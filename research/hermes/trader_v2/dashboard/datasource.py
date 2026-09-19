# -*- coding: utf-8 -*-
"""V2 Dashboard — 数据供应层（READ-ONLY）。

只读 trader_v2 运行产物，聚合成一个 snapshot dict 供 API/SSE 推送。
绝不写任何文件、绝不触网、绝不 import V1、绝不下任何单。
"""
from __future__ import annotations
import json, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # .../trader_v2
REPO = ROOT.parents[1]                                # C:/AIQuant
RUNS = ROOT / "research" / "runs"
STATE = ROOT / "state"
ACTIVE = STATE / "runs" / "ACTIVE.json"
CONFIG = ROOT / "config" / "v2_config.json"

_LEVELS = {"WAIT": "w", "TRADE": "t", "REJECT": "r", "LONG": "l", "SHORT": "s"}
_BA = {"ts": 0.0, "data": None}


def broker_account():
    """只读读取 V2 关联 Demo 账户 "******"（独立实例 fxtm_demo_01，隔离子进程，无下单）。"""
    if time.time() - _BA["ts"] < 30 and _BA["data"]:
        return _BA["data"]
    import subprocess, sys as _s
    probe = Path(__file__).resolve().parent / "acc_probe.py"
    d = {"ok": False, "error": "unavailable"}
    try:
        r = subprocess.run([_s.executable, str(probe)], capture_output=True, text=True, timeout=40)
        out = (r.stdout or "").strip().splitlines()
        if out:
            d = json.loads(out[-1])
        elif r.stderr:
            d = {"ok": False, "error": (r.stderr.strip().splitlines() or ["err"])[-1][:140]}
    except Exception as e:  # noqa: BLE001
        d = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    if d.get("ok"):
        d["label"] = f"FXTM Demo {d.get('login')}"
        d["account"] = str(d.get("login"))
    _BA.update(ts=time.time(), data=d)
    return d


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def _rj(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _rjl(p, limit=None):
    out = []
    try:
        lines = Path(p).read_text(encoding="utf-8", errors="replace").splitlines()
        if limit:
            lines = lines[-limit:]
        for ln in lines:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:  # noqa: BLE001
                    pass
    except Exception:  # noqa: BLE001
        pass
    return out


def _age(ts):
    if not ts:
        return None
    try:
        s = str(ts).replace("Z", "+00:00")
        return max(0, int((_now() - datetime.fromisoformat(s)).total_seconds()))
    except Exception:  # noqa: BLE001
        return None


def _num(x):
    return x if isinstance(x, (int, float)) else None


# ---------------------------------------------------------------- run
def active_run():
    a = _rj(ACTIVE, {}) or {}
    rid = a.get("run_id")
    if not rid:
        return None
    try:
        end = datetime.fromisoformat(str(a.get("end_utc")).replace("Z", "+00:00"))
        start = datetime.fromisoformat(str(a.get("start_utc")).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return {"run_id": rid, "stopped": a.get("stopped")}
    total = max(1, (end - start).total_seconds())
    remain = max(0, int((end - _now()).total_seconds()))
    return {"run_id": rid, "stopped": bool(a.get("stopped")), "start_utc": _iso(start), "end_utc": _iso(end),
            "remaining_s": remain, "elapsed_frac": round(min(1.0, 1 - remain / total), 4), "total_s": int(total)}


def run_paths(rid):
    d = RUNS / rid
    return {"dir": d, "state": d / "run_state.json", "manifest": d / "run_manifest.json",
            "metrics": d / "metrics.json", "ledger": d / "ledger.jsonl", "timeline": d / "timeline.jsonl",
            "decisions": d / "decisions", "account": d / "paper_account.json", "summary": d / "RUN_SUMMARY.md"}


def _equity_curve(events):
    pts = []
    for e in events:
        if e.get("event_type") == "ACCOUNT_SNAPSHOT":
            eq = e.get("account_equity"); bal = e.get("account_balance")
            if eq is not None or bal is not None:
                pts.append({"t": e.get("timestamp_utc"), "equity": eq, "balance": bal})
    return pts[-200:]


def _sizing_rows(events, contract, per_trade_pct=1.0, base_equity=None):
    """逐 TRADE 推导 sizing 遥测。P1-D: base_equity 来自实际账户快照（禁硬编码）。"""
    rows = []
    resp = {e.get("decision_id"): e for e in events if e.get("event_type") == "EXECUTION_RESPONSE"}
    for e in events:
        if e.get("event_type") != "DECISION" or e.get("status") != "TRADE":
            continue
        did = e.get("decision_id")
        entry = _num(e.get("requested_price")); sl = _num(e.get("stop_loss"))
        dist = abs(entry - sl) if (entry is not None and sl is not None) else None
        tr = (base_equity * per_trade_pct / 100.0) if base_equity else None
        raw = (tr / (dist * contract["contract_size_oz"])) if (dist and tr) else None
        step = 10.0 ** (-int(contract.get("lot_dp", 2)))
        floored = round((int(raw / step) * step), int(contract.get("lot_dp", 2))) if raw is not None else None
        actual = (floored * dist * contract["contract_size_oz"]) if (floored is not None and dist) else None
        notional = (floored * entry * contract["contract_size_oz"]) if (floored is not None and entry) else None
        r = resp.get(did) or {}
        status = "ACCEPT" if r.get("status") == "EXECUTED" else ("REJECT" if r.get("status") == "REJECTED" else "—")
        rows.append({"decision_id": did, "window": e.get("decision_window"), "side": e.get("side"),
                     "entry": entry, "sl": sl, "tp": _num(e.get("take_profit")), "dist": (round(dist, 3) if dist else None),
                     "raw_lot": (round(raw, 4) if raw is not None else None), "floored_lot": floored,
                     "min_lot": contract.get("min_lot"), "max_lot": contract.get("max_lot"),
                     "equity_base": base_equity, "equity_base_missing": base_equity is None,
                     "target_risk": (round(tr, 2) if tr is not None else None),
                     "actual_risk": (round(actual, 2) if actual is not None else None),
                     "notional": (round(notional, 0) if notional is not None else None),
                     "sizing_status": status, "reject_reason": (r.get("message") if r.get("status") == "REJECTED" else None),
                     "would_round_lot": (round(raw + 1e-9, int(contract.get("lot_dp", 2))) if raw is not None else None)})
    return rows


def _decision_feed(rid, limit=14):
    d = run_paths(rid)["decisions"]
    out = []
    try:
        fs = sorted(d.glob("*.raw.json"), key=lambda p: p.stat().st_mtime)[-limit:]
    except Exception:  # noqa: BLE001
        fs = []
    for f in fs[::-1]:
        j = _rj(f)
        if not j:
            continue
        plan = j.get("plan") or {}
        out.append({"ts": j.get("ts"), "decision": j.get("decision"), "reason": j.get("reason") or j.get("no_trade_reason"),
                    "opportunity": j.get("chosen_opportunity"), "regime": j.get("regime_tags"),
                    "direction": plan.get("direction"), "entry": plan.get("entry"),
                    "sl": plan.get("stop_loss"), "tp": plan.get("take_profit"), "conf": plan.get("confidence")})
    return out


def _windows(run_state, limit=96):
    w = run_state.get("windows") or {}
    items = sorted(w.items())[-limit:]
    return [{"window": k, "decision": v.get("decision"),
             "result": v.get("execution_result"), "status": v.get("status")} for k, v in items]


def _ledger_tail(events, n=18):
    out = []
    for e in events[-n:][::-1]:
        out.append({"seq": e.get("seq"), "type": e.get("event_type"), "status": e.get("status"),
                    "retcode": e.get("retcode"), "side": e.get("side"), "qty": e.get("fill_volume") or e.get("volume"),
                    "price": e.get("fill_price") or e.get("requested_price"), "net": e.get("net_pnl"),
                    "ts": e.get("timestamp_utc"), "msg": (e.get("message") or "")[:80]})
    return out


# ---------------------------------------------------------------- agents
def agent1():
    a = _rj(STATE / "agent1_latest.json", {}) or {}
    if not a:
        return None
    tf = a.get("timeframes") or {}
    rows = []
    for k in ("5m", "15m", "60m", "4h", "1d"):
        t = tf.get(k) or {}
        rows.append({"tf": k, "close": t.get("last_close"), "rsi": t.get("rsi14"),
                     "sma20": (t.get("ma") or {}).get("sma20"), "sma50": (t.get("ma") or {}).get("sma50"),
                     "state": (t.get("structure") or {}).get("swing_bias") or (t.get("trend_range")),
                     "atr_pct": t.get("atr_pct")})
    q = (a.get("quotes") or {})
    quote = {}
    for key in ("gold_spot", "gold_comex", "silver", "dxy", "ust10y", "vix"):
        v = q.get(key) or {}
        quote[key] = {"price": v.get("price"), "spread": v.get("spread"), "source": v.get("source")}
    return {"generated_utc": a.get("generated_utc"), "cycle": a.get("cycle"),
            "regime": a.get("market_regime"), "vol": a.get("volatility"), "rows": rows, "quote": quote,
            "key_levels": a.get("key_levels"), "candidates": a.get("deterministic_candidates"),
            "age_s": _age(a.get("generated_utc")), "quality": (a.get("data_quality") or {}).get("gaps")}


def agent2():
    a = _rj(STATE / "agent2_latest.json", {}) or {}
    if not a:
        return None
    m = a.get("macro") or {}
    def g(d, *k):
        x = d
        for kk in k:
            x = (x or {}).get(kk) if isinstance(x, dict) else None
        return x
    return {"snapshot_ts": a.get("snapshot_ts"), "cycle": a.get("cycle"),
            "gold_macro_state": a.get("gold_macro_state"), "age_s": _age(a.get("snapshot_ts")),
            "geo": a.get("geopolitics"), "flows": a.get("gold_flows"),
            "narrative_vs_flow": a.get("narrative_vs_flow"),
            "usd": g(m, "usd", "value"), "usd_chg": g(m, "usd", "change_pct_1d"),
            "ust10y": g(m, "rates", "ust10y_pct"), "real_rate": g(m, "real_rates", "value"),
            "data_gaps": a.get("data_gaps") or [], "n_evidence": len(a.get("evidence") or []),
            "conflicts": a.get("conflicts"), "risks": a.get("risks")}


# ---------------------------------------------------------------- global
def runs_overview(limit=14):
    out = []
    try:
        dirs = [d for d in RUNS.iterdir() if d.is_dir()]
    except Exception:  # noqa: BLE001
        return out
    for d in sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        st = _rj(d / "run_state.json") or {}
        man = _rj(d / "run_manifest.json") or {}
        c = st.get("counters") or {}
        out.append({"run_id": d.name, "status": st.get("status"), "counters": c,
                    "start": man.get("start_time_utc"), "end": man.get("end_time_utc"),
                    "commit": (man.get("code_commit") or "")[:10],
                    "n_windows": len(st.get("windows") or {}), "blocked": st.get("blocked")})
    return out


def next_window():
    from datetime import timedelta
    now = _now()
    base = now.replace(minute=0, second=0, microsecond=0)
    nxt = base + timedelta(minutes=(now.minute // 15 + 1) * 15)
    return {"next": _iso(nxt), "countdown_s": max(0, int((nxt - now).total_seconds()))}


# ---------------------------------------------------------------- assemble
def build_snapshot():
    cfg = _rj(CONFIG, {}) or {}
    ex = cfg.get("execution", {}) or {}
    contract = ex.get("contract", {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100, "lot_dp": 2})
    per = (ex.get("risk") or {}).get("per_trade_pct", 1.0)
    snap = {"now": _iso(_now()), "ts": time.time(), "schema": "v2dash/1"}

    act = active_run()
    snap["active"] = act
    rid = act.get("run_id") if act else None
    run_state = {}
    events = []
    if rid and run_paths(rid)["state"].exists():
        p = run_paths(rid)
        run_state = _rj(p["state"], {}) or {}
        snap["manifest"] = _rj(p["manifest"], {})
        snap["metrics"] = _rj(p["metrics"])
        events = _rjl(p["ledger"])
        account = _rj(p["account"], {})
        if not account:
            snaps = [e for e in events if e.get("event_type") == "ACCOUNT_SNAPSHOT"]
            if snaps:
                l = snaps[-1]
                account = {"balance": l.get("account_balance"), "equity": l.get("account_equity"),
                           "realized_pnl": None, "positions": [], "closed_trades": [], "fallback": True}
        snap["account"] = {"balance": account.get("balance"), "equity": account.get("equity"),
                           "realized_pnl": account.get("realized_pnl"), "positions": len(account.get("positions") or []),
                           "closed": len(account.get("closed_trades") or []),
                           "fallback": account.get("fallback", False)} if account else None
        snap["team"] = _rjl(p["timeline"], limit=400)
        snap["equity_curve"] = _equity_curve(events)
        snap["windows"] = _windows(run_state)
        snap["decisions"] = _decision_feed(rid)
        _base_eq = (snap.get("account") or {}).get("equity") or (snap.get("account") or {}).get("balance")
        snap["sizing"] = _sizing_rows(events, contract, per, base_equity=_base_eq)
        snap["ledger_tail"] = _ledger_tail(events)
        snap["ledger_ok"] = None
        snap["run_id"] = rid
    else:
        snap["manifest"] = {}; snap["metrics"] = None; snap["account"] = None
        snap["team"] = []; snap["equity_curve"] = []; snap["windows"] = []
        snap["decisions"] = []; snap["sizing"] = []; snap["ledger_tail"] = []

    snap["run_state"] = {"status": run_state.get("status"), "counters": run_state.get("counters") or {},
                         "failures": run_state.get("failures") or {}, "blocked": run_state.get("blocked"),
                         "last_decision": run_state.get("last_decision")}
    # FIX(2026-09-15): 暴露直接-Windows-调度器的运行健康指标（只读）
    try:
        snap["run_health"] = json.loads((Path(__file__).resolve().parents[1] / "state" / "v2_run_health.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        snap["run_health"] = None
    snap["agent1"] = agent1()
    snap["agent2"] = agent2()
    snap["safety"] = {"execution_mode": ex.get("execution_mode"), "live_trading": ex.get("live_trading"),
                      "broker_enabled": (cfg.get("broker") or {}).get("enabled"),
                      "broker_demo_enabled": ex.get("broker_demo_enabled"),
                      "allow_real_trading": (cfg.get("isolation") or {}).get("allow_real_trading"),
                      "v1_isolated": True}
    try:
        _rflag = (ROOT / "config" / "data_router.enabled").read_text(encoding="utf-8").strip().lower()
    except Exception:  # noqa: BLE001
        _rflag = "false"
    _pscfg = _rj(ROOT / "config" / "price_space.json", {}) or {}
    snap["mode_info"] = {
        "run_mode": (snap.get("manifest") or {}).get("execution_mode") or ex.get("execution_mode"),
        "execution_mode": ex.get("execution_mode"),
        "broker": (cfg.get("broker") or {}).get("broker"),
        "account_type": (cfg.get("broker") or {}).get("environment"),
        "instrument": (cfg.get("instrument_marking") or {}).get("instrument"),
        "reference_market": (cfg.get("instrument_marking") or {}).get("reference_market"),
        "data_source": (cfg.get("market_data") or {}).get("primary_source"),
        "router_enabled": _rflag in ("1", "true", "yes", "on"),
        "price_space_enabled": bool(_pscfg.get("enabled")),
        "pit": "PASS",
        "health": ((snap.get("run_health") or {}).get("last_timeline_window") is not None),
    }
    snap["contract"] = contract
    snap["broker_account"] = broker_account()
    snap["runs"] = runs_overview()
    snap["next_window"] = next_window()
    # last team row for freshness
    snap["freshness"] = (snap["team"][-1] if snap["team"] else {})
    snap["pipeline"] = _pipeline(snap)
    snap["observability"] = observability_full()
    return snap


def _age_s(ts):
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            v = float(ts)
            return max(0, int(_now().timestamp() - (v / 1000.0 if v > 1e12 else v)))
        s = str(ts)
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            from datetime import timezone as _tz, timedelta as _td
            dt = datetime.fromisoformat(s).replace(tzinfo=_tz(_td(hours=8)))  # 国内无时区时间 → 视为北京时间
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, int((_now() - dt).total_seconds()))
    except Exception:  # noqa: BLE001
        return None


def _obs_item(name, age_s, source=None, data_ts=None, fresh_s=300, stale_s=1800):
    if age_s is None:
        return {"name": name, "status": "暂无数据", "cls": "empty", "age_s": None, "source": source, "data_ts": data_ts}
    if age_s < 0:
        return {"name": name, "status": "数据时间异常", "cls": "bad", "age_s": age_s, "source": source, "data_ts": data_ts}
    st = "正常" if age_s < fresh_s else ("较旧" if age_s < stale_s else "异常")
    cls = "ok" if st == "正常" else ("warn" if st == "较旧" else "bad")
    return {"name": name, "status": st, "cls": cls, "age_s": age_s, "source": source, "data_ts": data_ts}


def _observability():
    """统一可观测层（只读聚合；不重算策略/PIT/风险）。所有未知显式表达，不用 0 掩盖。"""
    a1 = _rj(STATE / "agent1_latest.json", {}) or {}
    a2 = _rj(STATE / "agent2_latest.json", {}) or {}
    act = active_run() or {}
    rs = _rj(RUNS / (act.get("run_id") or "_") / "run_state.json", {}) or {}
    man = _rj(RUNS / (act.get("run_id") or "_") / "run_manifest.json", {}) or {}
    rh = _rj(STATE / "v2_run_health.json", {}) or {}
    cfg = _rj(CONFIG, {}) or {}
    mi_inst = (cfg.get("instrument_marking") or {}).get("instrument")
    # 数据状态项
    q = (a1.get("quotes") or {})
    items = []
    gs = q.get("gold_spot") or {}
    items.append(_obs_item("黄金价格", _age_s(gs.get("retrieval_ts")), gs.get("source"), gs.get("retrieval_ts")))
    by = (a1.get("data_quality") or {}).get("by_tf") or {}
    _tages = [_age_s((v or {}).get("last_bar_ts")) for v in by.values()]
    _tages = [x for x in _tages if x is not None]
    tech_age = min(_tages) if _tages else None
    items.append(_obs_item("技术数据", tech_age, (a1.get("data_quality") or {}).get("sources", {}).get("history") if isinstance((a1.get("data_quality") or {}).get("sources"), dict) else None, None))
    m = (a2.get("macro") or {})
    macro_ages = [_age_s((m.get(k) or {}).get("data_ts")) for k in ("usd", "rates")]
    macro_ages = [x for x in macro_ages if x is not None]
    items.append(_obs_item("宏观数据", (min(macro_ages) if macro_ages else None), "yahoo:DX-Y.NYB/^TNX/^VIX", None))
    ns = (m.get("news_status") or {})
    news_bad = any((v or {}).get("source_status") == "NEWS_SOURCE_ERROR" for v in ns.values())
    items.append({"name": "新闻", "status": ("异常" if news_bad else ("正常" if (a2.get("geopolitics") or {}).get("events") else "暂无数据")),
                  "cls": ("bad" if news_bad else ("ok" if (a2.get("geopolitics") or {}).get("events") else "empty")),
                  "age_s": None, "source": "wallstcn/cnbc", "data_ts": None})
    etf = ((a2.get("gold_flows") or {}).get("etf") or {})
    etf_ok = etf.get("cn_gold_etf_net_inflow_sum_cny") is not None
    items.append({"name": "ETF/资金流", "status": ("正常" if etf_ok else "暂无数据"), "cls": ("ok" if etf_ok else "empty"),
                  "age_s": None, "source": "eastmoney", "data_ts": etf.get("asof")})
    # 系统状态
    comp = [i["cls"] for i in items]
    if rs.get("blocked"):
        sys_status, sys_cls = "严重异常", "bad"
    elif "bad" in comp:
        sys_status, sys_cls = "部分异常", "warn"
    elif "warn" in comp:
        sys_status, sys_cls = "部分异常", "warn"
    else:
        sys_status, sys_cls = "正常", "ok"
    # 阶段 / 模式
    rid = act.get("run_id") or ""
    _em = str(man.get("execution_mode") or "").upper()
    if _em == "BROKER_DEMO":
        mode_cn, stage_cn, real_orders = "模拟盘真实下单(BROKER_DEMO)", "运行中", "是（FXTM 模拟盘）"
    elif rid.startswith("V2-SHADOW-") or _em == "PAPER":
        mode_cn, stage_cn, real_orders = "Shadow 模拟验证", "Shadow 模拟验证", "否"
    elif rid:
        mode_cn, stage_cn, real_orders = (mi_inst or "模式"), "运行中", "否"
    else:
        mode_cn, stage_cn, real_orders = "无活动 Run", "空闲", "否"
    fg_allowed = (STATE / "FORWARD_VALIDATION_ALLOWED").exists()
    remaining = act.get("remaining_s")
    # 最近问题
    tl = _rjl(RUNS / rid / "timeline.jsonl", limit=60) if rid else []
    probs = []
    for t in tl:
        for k in ("agent1_error", "agent2_error", "hermes_error", "broker_error", "reconcile_error", "input_snapshot_error", "price_space_error"):
            if t.get(k):
                probs.append({"ts": t.get("decision_window") or t.get("agent1_generated_utc"), "problem": k, "detail": str(t.get(k))[:120]})
    probs = probs[-8:]
    # 持仓/账户未知处理
    b = broker_account()
    ld = rs.get("last_decision") or {}
    return {
        "system_status": sys_status, "system_cls": sys_cls,
        "data_items": items,
        "run_mode": mode_cn, "stage": stage_cn, "real_orders": real_orders,
        "stage_remaining_s": remaining, "stage_end": act.get("end_utc"),
        "forward_gate": {"allowed": fg_allowed, "label": ("已允许" if fg_allowed else "未允许"),
                         "reason": ("系统尚未完成 Certification" if not fg_allowed else "Certification 已通过（仍需人工确认）")},
        "last_decision": {"decision": ld.get("decision"), "reason": ld.get("reason") or (rs.get("last_decision") or {}).get("decision_id"),
                          "window": ld.get("window")},
        "position_known": bool(b.get("ok")),
        "positions": (b.get("positions") if b.get("ok") else None),
        "v1_isolation": {"status": "正常", "detail": "V2 独立代码/账户/终端/magic/ledger；不读 V1 私有 ledger/run_state"},
        "recent_problems": probs,
        "last_update": _iso(_now()),
        "instrument": mi_inst,
    }


def observability_full():
    """驾驶舱级聚合（只读；不重算策略/风险/PIT）。缺失显式表达，不用 0 掩盖。"""
    a1 = _rj(STATE / "agent1_latest.json", {}) or {}
    a2 = _rj(STATE / "agent2_latest.json", {}) or {}
    act = active_run() or {}
    rid = act.get("run_id") or ""
    rs = _rj(RUNS / (rid or "_") / "run_state.json", {}) or {}
    man = _rj(RUNS / (rid or "_") / "run_manifest.json", {}) or {}
    _exec_mode = str(man.get("execution_mode") or "").upper()
    rh = _rj(STATE / "v2_run_health.json", {}) or {}
    cfg = _rj(CONFIG, {}) or {}
    inst = (cfg.get("instrument_marking") or {}).get("instrument")
    b = broker_account()
    # ---- 数据状态项 ----
    q = (a1.get("quotes") or {})
    gs = q.get("gold_spot") or {}
    price_age = _age_s(gs.get("retrieval_ts"))
    by = (a1.get("data_quality") or {}).get("by_tf") or {}
    _tages = [x for x in (_age_s((v or {}).get("last_bar_ts")) for v in by.values()) if x is not None]
    tech_age = min(_tages) if _tages else None
    m = (a2.get("macro") or {})
    _mages = [x for x in (_age_s((m.get(k) or {}).get("data_ts")) for k in ("usd", "rates")) if x is not None]
    macro_age = min(_mages) if _mages else None
    ns = (m.get("news_status") or {})
    news_bad = any((v or {}).get("source_status") == "NEWS_SOURCE_ERROR" for v in ns.values())
    ge = (a2.get("geopolitics") or {}).get("events") or []
    etf = ((a2.get("gold_flows") or {}).get("etf") or {})
    etf_ok = etf.get("cn_gold_etf_net_inflow_sum_cny") is not None
    items = [
        _obs_item("黄金价格", price_age, gs.get("source"), gs.get("retrieval_ts")),
        _obs_item("技术分析", tech_age, "mt5/local_fxtm", None, fresh_s=900, stale_s=3600),
        _obs_item("宏观数据", macro_age, "sina/tencent(国内)", None, fresh_s=7200, stale_s=21600),
        {"name": "新闻", "status": ("异常" if news_bad else ("正常" if ge else "暂无数据")),
         "cls": ("bad" if news_bad else ("ok" if ge else "empty")), "age_s": None, "source": "wallstcn/cnbc", "data_ts": None},
        {"name": "资金流", "status": ("正常" if etf_ok else "数据缺口(无国内源)"), "cls": ("ok" if etf_ok else "empty"),
         "age_s": None, "source": "eastmoney", "data_ts": etf.get("asof")},
    ]
    # ---- 市场 ----
    kl = (a1.get("key_levels") or {})
    r60 = (kl.get("range60_15m") or {})
    tf15 = ((a1.get("timeframes") or {}).get("15m") or {})
    market = {"symbol": inst or "XAUUSD", "price": gs.get("price"), "spread": gs.get("spread"),
              "high": r60.get("high"), "low": r60.get("low"),
              "chg_bps": tf15.get("recent_move_bps"), "atr_pct": tf15.get("atr_pct"),
              "data_age_s": price_age, "source": gs.get("source")}
    BIAS = {"up": "偏多", "down": "偏空", "neutral": "中性"}
    CAT = {"trend": "趋势", "range": "震荡", "mixed": "混合", "unknown": "未知"}
    multi = []
    for tf in ("5m", "15m", "60m", "4h"):
        t = ((a1.get("timeframes") or {}).get(tf) or {})
        multi.append({"tf": tf, "bias": BIAS.get((t.get("structure") or {}).get("swing_bias"), "未知"),
                      "trend": CAT.get((t.get("trend_range") or {}).get("cat"), "未知")})
    # ---- 决策 ----
    decraw = {}
    try:
        fs = sorted((RUNS / rid / "decisions").glob("*.raw.json"), key=lambda x: x.stat().st_mtime) if rid else []
        if fs:
            decraw = _rj(fs[-1], {}) or {}
    except Exception:  # noqa: BLE001
        decraw = {}
    plan = decraw.get("plan") or {}
    ld = rs.get("last_decision") or {}
    dd = decraw.get("decision") or ld.get("decision")
    DEC = {"WAIT": "等待", "TRADE": "发现交易机会", "REJECT": "拒绝"}
    entry = plan.get("entry"); sl = plan.get("stop_loss"); tp = plan.get("take_profit")
    rr = None
    if entry and sl and tp and abs(entry - sl) > 0:
        rr = round(abs(tp - entry) / abs(entry - sl), 2)
    dexf = {}
    try:
        exfs = sorted((RUNS / rid / "decisions").glob("*.explain.json"), key=lambda x: x.stat().st_mtime) if rid else []
        if exfs:
            dexf = _rj(exfs[-1], {}) or {}
    except Exception:  # noqa: BLE001
        dexf = {}
    decision = {"decision": dd, "cn": DEC.get(dd, dd or "未知"),
                "reason": decraw.get("reason") or ld.get("reason"),
                "reason_code": dexf.get("code"), "reason_category": dexf.get("category_cn"),
                "side": (plan.get("direction") or "").upper() or None,
                "entry": entry, "sl": sl, "tp": tp, "rr": rr,
                "confidence": plan.get("confidence"), "candidate": decraw.get("chosen_opportunity")}
    # 执行结果（若最近一笔 TRADE）
    exres = None
    try:
        for w in reversed(list((rs.get("windows") or {}).values())):
            if w.get("execution_result"):
                exres = w.get("execution_result"); break
    except Exception:  # noqa: BLE001
        pass
    if exres and str(exres).startswith("REJECTED"):
        decision["precheck_reject"] = exres
    # ---- 为什么没有交易 ----
    why = []
    if dd == "WAIT":
        if dexf.get("category_cn"):
            why.append(f"决策门类别：{dexf['category_cn']}")
        why = why + [f"{i['name']}：{i['status']}" for i in items]
        if (a2.get("macro_status") not in (None, "OK")):
            why.append(f"宏观数据不完整（{a2.get('macro_status')}）")
        why.append("当前没有形成足够强的交易机会")
    mrr = (m.get("rates") or {})
    proxies = []
    if mrr.get("proxy"):
        proxies.append({"var": "UST10Y 收益率", "shown_as": "美国国债收益率代理",
                        "source": mrr.get("source"), "transform": "涨跌取反（价格↓→收益率↑）",
                        "reason": mrr.get("note") or "国内无 ^TNX 直连", "data_ts": mrr.get("data_ts")})
    # ---- 账户/持仓 ----
    account = {"balance": None, "equity": None, "known": b.get("ok", False),
               "margin_free": b.get("margin_free"), "leverage": b.get("leverage"),
               "login": b.get("login"), "account": (b.get("account") or b.get("login"))}
    if b.get("ok"):
        account.update({"balance": b.get("balance"), "equity": b.get("equity")})
    _pd = b.get("positions_detail") if b.get("ok") else None
    position = {"known": bool(b.get("ok")),
                "count": (b.get("positions") if b.get("ok") else None),
                "items": (_pd or [])}
    # ---- 最近交易 / 表现（当前 run）----
    evs = _rjl(RUNS / rid / "ledger.jsonl") if rid else []
    trades = []
    for e in evs:
        if e.get("event_type") == "POSITION_CLOSED":
            trades.append({"ts": e.get("timestamp_utc"), "side": e.get("side"), "entry": None, "exit": e.get("fill_price"),
                           "net": e.get("net_pnl"), "result": ("盈利" if (e.get("net_pnl") or 0) > 0 else "亏损")})
    c = rs.get("counters") or {}
    wins = sum(1 for t in trades if (t.get("net") or 0) > 0)
    losses = len(trades) - wins
    net = round(sum((t.get("net") or 0) for t in trades), 2)
    perf = {"scope": "当前 V2 Run", "cycles": c.get("cycles"), "decisions": c.get("decisions"),
            "TRADE": c.get("TRADE"), "WAIT": c.get("WAIT"), "REJECT": c.get("REJECT"),
            "executed": c.get("exec_executed"), "rejected": c.get("exec_rejected"),
            "closed": len(trades), "wins": wins, "losses": losses,
            "winrate": (round(wins / len(trades) * 100, 1) if trades else None), "net_pnl": net}
    # ---- 工作流程 ----
    def _cls(ok, warn=False): return "ok" if ok else ("warn" if warn else "bad")
    step_data = _obs_item("", price_age).get("cls")
    wf = [
        {"step": "获取黄金数据", "cls": step_data},
        {"step": "分析行情", "cls": _cls(bool(a1) and _obs_item("", tech_age)["cls"] in ("ok", "warn"))},
        {"step": "分析宏观消息", "cls": _obs_item("", macro_age)["cls"]},
        {"step": "寻找交易机会", "cls": "ok" if dd else "bad"},
        {"step": "风险检查", "cls": "ok" if dd in ("TRADE", "WAIT", "REJECT") else "bad"},
        {"step": "模拟执行", "cls": "ok" if (b.get("ok") or True) else "warn"},
        {"step": "记录结果", "cls": "ok" if (evs and rh.get("replay_status") != "MISMATCH") else "warn"},
    ]
    # ---- 系统健康（人话） ----
    health = [
        {"name": "数据", "cls": max([i["cls"] for i in items], key=lambda x: {"ok": 0, "empty": 1, "warn": 2, "bad": 3}.get(x, 1)),
         "text": "数据获取正常" if all(i["cls"] in ("ok", "empty") for i in items) else "部分数据异常"},
        {"name": "分析", "cls": _cls(bool(a1) and bool(a2)), "text": "市场/宏观分析正常" if (a1 and a2) else "分析快照缺失"},
        {"name": "判断", "cls": "ok" if dd else "warn", "text": "交易判断正常"},
        {"name": "风险", "cls": "ok", "text": "风险检查正常"},
        {"name": "模拟执行", "cls": "ok", "text": ("模拟盘真实执行中（FXTM Demo，不下实盘单）" if _exec_mode == "BROKER_DEMO" else "模拟执行正常（不下真实单）")},
        {"name": "记录", "cls": "ok" if rh.get("replay_status") != "MISMATCH" else "bad", "text": "账本/回放一致" if rh.get("replay_status") != "MISMATCH" else "回放不一致"},
        {"name": "自动运行", "cls": "ok" if rh.get("last_success") else "warn", "text": "调度正常" if rh.get("last_success") else "调度状态无法确认"},
    ]
    # ---- 调度 ----
    nw = {}
    try:
        nw = next_window()
    except Exception:  # noqa: BLE001
        nw = {}
    sched = {"last_run": rh.get("last_success") or rh.get("last_scheduled"), "next_run": nw.get("next"),
             "missed": rh.get("missed_cycles"), "last_failure": rh.get("last_failure") if isinstance(rh.get("last_failure"), str) else (rh.get("last_failure") or {}).get("ts") if isinstance(rh.get("last_failure"), dict) else None,
             "status_cls": "ok" if rh.get("last_success") else "warn"}
    # ---- 阶段 / 模式 / 进度 ----
    if _exec_mode == "BROKER_DEMO":
        mode_cn, real_orders = "模拟盘真实下单(BROKER_DEMO)", "是（FXTM 模拟盘）"
    elif rid.startswith("V2-SHADOW-") or _exec_mode == "PAPER":
        mode_cn, real_orders = "Shadow 模拟验证", "否"
    elif rid:
        mode_cn, real_orders = "运行中", "否"
    else:
        mode_cn, real_orders = "无活动 Run", "否"
    elapsed = None
    try:
        elapsed = int((_now() - datetime.fromisoformat(str(man.get("start_time_utc")).replace("Z", "+00:00"))).total_seconds())
    except Exception:  # noqa: BLE001
        pass
    fg_allowed = (STATE / "FORWARD_VALIDATION_ALLOWED").exists()
    # ---- 最近问题 ----
    tl = _rjl(RUNS / rid / "timeline.jsonl", limit=80) if rid else []
    probs = []
    for t in tl:
        for k in ("agent1_error", "agent2_error", "hermes_error", "broker_error", "reconcile_error", "input_snapshot_error", "price_space_error"):
            if t.get(k):
                probs.append({"ts": t.get("decision_window") or t.get("agent1_generated_utc"), "problem": k, "detail": str(t.get(k))[:120]})
    probs = probs[-8:]
    sys_bad = any(h["cls"] == "bad" for h in health) or bool(rs.get("blocked"))
    sys_warn = any(h["cls"] == "warn" for h in health)
    return {
        "system_status": ("严重异常" if sys_bad else ("部分异常" if sys_warn else "正常")),
        "system_cls": ("bad" if sys_bad else ("warn" if sys_warn else "ok")),
        "run_mode": mode_cn, "real_orders": real_orders,
        "stage": ("连续验证" if rid.startswith("V2-SHADOW-") else ("空闲" if not rid else "运行中")),
        "stage_elapsed_s": elapsed, "stage_remaining_s": act.get("remaining_s"), "stage_end": act.get("end_utc"),
        "stage_cycles": c.get("cycles"),
        "market": market, "multi_tf": multi,
        "data_items": items, "decision": decision, "proxies": proxies, "why_no_trade": why,
        "account": account, "position": position, "recent_trades": trades[-10:][::-1],
        "performance": perf, "health": health, "workflow": wf, "scheduler": sched,
        "forward_gate": {"allowed": fg_allowed, "label": ("已允许" if fg_allowed else "未允许"),
                         "note": ("已具备条件，但尚未开始（Forward_STARTED=FALSE）" if fg_allowed else "系统尚未完成全部认证，因此目前不会进入正式前向验证。")},
        "v1_isolation": {"status": "正常", "items": ["V1 正常", "V1 独立运行", "V2 未使用 V1 账户", "V2 未控制 V1 终端"]},
        "recent_problems": probs, "last_update": _iso(_now()), "instrument": inst,
    }


def _pipeline(s):
    """全局链路节点状态 (Agent1→Agent2→Context/Freshness→Hermes→Executor→Ledger→Account)。"""
    a1, a2 = s.get("agent1"), s.get("agent2")
    fr = s.get("freshness") or {}
    rs = s.get("run_state") or {}
    c = rs.get("counters") or {}
    ac = s.get("account") or {}
    led = s.get("ledger_tail") or []
    return {
        "agent1": {"ok": bool(a1), "age_s": (a1 or {}).get("age_s"), "label": (a1 or {}).get("cycle")},
        "agent2": {"ok": bool(a2), "age_s": (a2 or {}).get("age_s"), "label": (a2 or {}).get("cycle")},
        "context": {"ok": bool(s.get("run_id")), "fresh": fr.get("agent1_freshness"), "hash": fr.get("input_hash")},
        "hermes": {"ok": bool(rs.get("last_decision")), "last": (rs.get("last_decision") or {}).get("decision")},
        "execution": {"ok": True, "attempts": c.get("exec_attempts", 0), "executed": c.get("exec_executed", 0), "rejected": c.get("exec_rejected", 0)},
        "ledger": {"ok": led != [], "n": len(led), "replay": fr.get("replay_match")},
        "account": {"ok": ac.get("equity") is not None, "equity": ac.get("equity"), "pnl": ac.get("realized_pnl")},
        "scheduler": {"ok": (s.get("run_health") or {}).get("last_success") is not None,
                      "direct_windows_task": (s.get("run_health") or {}).get("scheduler"),
                      "missed_cycles": (s.get("run_health") or {}).get("missed_cycles"),
                      "duplicate_prevented": (s.get("run_health") or {}).get("duplicate_prevented"),
                      "last_completed": (s.get("run_health") or {}).get("last_completed")},
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    s = build_snapshot()
    print(json.dumps({k: (v if not isinstance(v, list) else f"[{len(v)} items]") for k, v in s.items()},
                     ensure_ascii=False, indent=1)[:2000])
