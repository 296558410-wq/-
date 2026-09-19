# -*- coding: utf-8 -*-
"""V2 Module 5 — Hermes V2 实时 Paper Shadow Run 运行器（PAPER ONLY）。

每个 run: 唯一 run_id; 冻结 manifest(版本/配置); Agent1(15m)+Agent2(60m)+Hermes(15m) → 决策
→ RAW+FROZEN 保存 → (仅 TRADE) Paper 执行 → Module3 Ledger(append-only, run_id 戳记)
→ checkpoint Replay 对账(Paper==Replay) → run_state/metrics → RUN_SUMMARY。

安全: 启动 assert_execution_allowed()（允许 PAPER / BROKER_DEMO, 任何 LIVE 一律拒）; ledger 不可用 → 不执行; 账户!=Replay → RUN_BLOCKED; 崩溃可恢复(去重)。
用法:
  python shadow_run.py cycle [--minutes 1440] [--close]      # cron 每15分钟调一次
  python shadow_run.py once --cycles 3 --interval-sec 5      # 受控短跑
  python shadow_run.py finalize | status | replay-check
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for sub in ("agents/technical", "agents/macro_global", "hermes", "execution", "ledger", "runtime", "data_sources"):
    sys.path.insert(0, str(ROOT / sub))
import hermes_paper_adapter as ADP  # noqa: E402
import hermes as HERMES  # noqa: E402
import agent1 as A1  # noqa: E402
import agent2 as A2  # noqa: E402
import paper_executor as PE  # noqa: E402
import broker_demo_executor as BDE  # noqa: E402
import ledger as L  # noqa: E402
import replay as R  # noqa: E402
try:
    import price_space as PS  # noqa: E402
except Exception:  # noqa: BLE001
    PS = None

RUNS = ROOT / "research" / "runs"
ACTIVE = ROOT / "state" / "runs" / "ACTIVE.json"
CERT = ROOT / "state" / "FORWARD_VALIDATION_ALLOWED"
SHADOW_FLAG = ROOT / "state" / "SHADOW_ALLOWED"
DEFAULT_MINUTES = 1440


def forward_allowed():
    """P1-G: 认证门（在**所有**入口生效：scheduler / CLI / direct python）。
    未认证前禁止启动任何新 run；不依赖 strategy config。env 仅作显式授权覆盖。"""
    v = str(os.environ.get("V2_FORWARD_VALIDATION_ALLOWED", "")).strip().lower()
    if v:
        return v in ("1", "true", "yes", "on")
    try:
        return CERT.read_text(encoding="utf-8").strip().lower() in ("1", "true", "yes", "on")
    except Exception:  # noqa: BLE001
        return False


def shadow_allowed():
    """Shadow 授权（与 forward 分开；shadow 永不发 broker 单）。"""
    v = str(os.environ.get("V2_SHADOW_ALLOWED", "")).strip().lower()
    if v:
        return v in ("1", "true", "yes", "on")
    try:
        return SHADOW_FLAG.read_text(encoding="utf-8").strip().lower() in ("1", "true", "yes", "on")
    except Exception:  # noqa: BLE001
        return False


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def window15(dt=None):
    dt = dt or utcnow()
    return dt.replace(minute=(dt.minute // 15) * 15, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%MZ")


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def code_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT.parents[1]),
                              capture_output=True, text=True, timeout=20).stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def _grep(path, key, default="unknown"):
    try:
        for ln in Path(path).read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith(key):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:  # noqa: BLE001
        pass
    return default


def versions():
    return {"strategy_version": ADP.load_config().get("hermes", {}).get("prompt_version", "hermes2-prompt/0.1.0"),
            "agent1_version": _grep(ROOT / "agents" / "technical" / "agent1.py", "AGENT_VERSION"),
            "agent2_version": _grep(ROOT / "agents" / "macro_global" / "agent2.py", "AGENT_VERSION"),
            "hermes_version": "hermes2/0.1.0",
            "paper_engine_version": _grep(ROOT / "execution" / "paper_executor.py", "ENGINE_VERSION", "paper/0.1.0"),
            "ledger_version": f"ledger/{L.EVENT_VERSION}"}


def run_dir(run_id):
    return RUNS / run_id


def run_ledger(run_id):
    return run_dir(run_id) / "ledger.jsonl"


def state_path(run_id):
    return run_dir(run_id) / "run_state.json"


def _load(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def _write(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def _append_jsonl(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ---------------- run lifecycle ----------------
def _make_executor(cfg, run_id=None):
    """按 execution_mode 选执行器: PAPER→PaperExecutor / BROKER_DEMO→BrokerDemoExecutor(真实 demo)。
    Shadow run (RUN_META.shadow=true) → 强制 PaperExecutor（**永不发 broker 单**）。"""
    mode = (cfg.get("execution") or {}).get("execution_mode", "PAPER")
    _shadow = bool(((_load(run_dir(run_id) / "RUN_META.json", {}) or {}).get("shadow")) if run_id else False)
    if mode == "BROKER_DEMO" and not _shadow:
        return BDE.BrokerDemoExecutor(cfg)
    pe = PE.PaperExecutor(cfg)
    if run_id is not None:
        PE.ACCOUNT_P = run_dir(run_id) / "paper_account.json"
        PE.EXECUTIONS_P = run_dir(run_id) / "paper_executions.jsonl"
    pe.acc = pe._fresh()
    return pe


def start_run(minutes=DEFAULT_MINUTES, market_data_source="XAUUSD (router: mt5→local_fxtm→yahoo) + quotes/macro sina/tencent(国内) + reference GC=F", shadow=False):
    if shadow:
        if not shadow_allowed():
            raise RuntimeError("REFUSE_TO_START: shadow not authorized (SHADOW_ALLOWED=false)")
    elif not forward_allowed():
        raise RuntimeError("REFUSE_TO_START: forward validation not certified (FORWARD_VALIDATION_ALLOWED=false)")
    ADP.assert_execution_allowed()
    rid = ("V2-SHADOW-" if shadow else "V2-PAPER-") + utcnow().strftime("%Y%m%d-%H%M%S") + "-" + hashlib.sha1(f"{time.time_ns()}".encode()).hexdigest()[:4]
    now = utcnow(); end = now + timedelta(minutes=minutes)
    man = {"run_id": rid, "start_time_utc": iso(now), "end_time_utc": iso(end),
           "execution_mode": ADP.execution_mode_of(), "symbol": "XAUUSD", "timezone": "UTC",
           "config_hash": sha_file(ROOT / "config" / "v2_config.json"), "code_commit": code_commit(),
           "market_data_source": market_data_source, "frozen": True, **versions()}
    run_dir(rid).mkdir(parents=True, exist_ok=True)
    _write(run_dir(rid) / "run_manifest.json", man)
    _write(run_dir(rid) / "RUN_META.json", {"shadow": bool(shadow), "execution_mode": ("PAPER" if shadow else ADP.execution_mode_of()),
                                             "created_utc": iso(now), "note": "shadow=PAPER/no-broker" if shadow else ""})
    _write(ACTIVE, {"run_id": rid, "start_utc": iso(now), "end_utc": iso(end), "stopped": False})
    _write(state_path(rid), {"run_id": rid, "status": "RUNNING", "windows": {}, "counters": _zero_counters(),
                             "failures": {"agent1": 0, "agent2": 0, "hermes": 0, "ledger": 0, "restarts": 0},
                             "last_decision": None, "blocked": None})
    return rid


def _zero_counters():
    return {"cycles": 0, "decisions": 0, "TRADE": 0, "WAIT": 0, "REJECT": 0,
            "exec_attempts": 0, "exec_executed": 0, "exec_rejected": 0, "duplicate_skips": 0,
            "broker_reconcile_count": 0, "broker_auto_close_count": 0,
            "reconcile_duplicate_prevented": 0, "account_match_failures": 0}


def ensure_run(minutes=DEFAULT_MINUTES, allow_new=False):
    """有界语义: 单一 active run; 窗口结束→finalize 并停止(不自动开新 run)。allow_new=True 才开新 run。
    P1-G: 未认证时不允许**新建** run；但**已有活动 run 不受影响**（否则会卡住 shadow）。"""
    act = _load(ACTIVE)
    if act and act.get("stopped"):
        act = None if allow_new else act
    if act and act.get("run_id") and run_dir(act["run_id"]).exists():
        if _parse(act["end_utc"]) <= utcnow():
            # 窗口已尽: 仅当 run 尚未终态时才 finalize（防止每周期重复 finalize 改写 end_time）
            st = _load(state_path(act["run_id"])) or {}
            if st.get("status") not in ("STOPPED", "COMPLETE", "BLOCKED"):
                finalize(act["run_id"])
            if not allow_new:
                return act["run_id"], False
        else:
            return act["run_id"], False
    if allow_new and not forward_allowed():
        return None, False
    return start_run(minutes), True


def _parse(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_state(run_id):
    st = _load(state_path(run_id))
    if not st:
        raise RuntimeError(f"no run_state for {run_id}")
    return st


# ---------------- one cycle ----------------
def run_cycle(run_id, cycle=None, market_mid=None, close_after=False, window=None, allow_new_run=False):
    """执行一个决策周期。返回摘要 dict。"""
    ADP.assert_execution_allowed()
    st = load_state(run_id)
    if st.get("blocked"):
        return {"run_id": run_id, "blocked": st["blocked"]}
    if st.get("status") == "STOPPED":
        return {"run_id": run_id, "status": "STOPPED"}

    led = run_ledger(run_id)
    ok, detail = L.verify_ledger(led) if led.exists() else (True, {"n": 0})
    if not ok:
        st["failures"]["ledger"] += 1
        st["blocked"] = {"reason": "LEDGER_UNVERIFIABLE", "detail": detail, "ts": iso(utcnow())}
        _write(state_path(run_id), st); _write(ACTIVE, {**_load(ACTIVE, {}), "stopped": True})
        return {"run_id": run_id, "blocked": "LEDGER_UNVERIFIABLE", "detail": detail}

    # 账本可用性探测(写失败 → NO EXECUTION)
    if not _ledger_writable(led):
        st["failures"]["ledger"] += 1
        st["blocked"] = {"reason": "LEDGER_UNAVAILABLE", "ts": iso(utcnow())}
        _write(state_path(run_id), st)
        return {"run_id": run_id, "blocked": "LEDGER_UNAVAILABLE"}

    win = window or window15()
    if win in st["windows"]:
        st["counters"]["duplicate_skips"] += 1
        _write(state_path(run_id), st)
        return {"run_id": run_id, "decision_window": win, "skipped_duplicate": True}

    # --- Agent1 / Agent2 (失败不得伪装成新数据) ---
    a1, a2 = None, None
    timeline = {"run_id": run_id, "decision_window": win}
    try:
        a1, _p1 = A1.build(cycle)
        timeline["agent1_generated_utc"] = a1.get("generated_utc")
        timeline["market_data_ts"] = (a1.get("quotes", {}).get("gold_spot") or {}).get("data_ts")
        timeline["market_retrieval_ts"] = (a1.get("quotes", {}).get("gold_spot") or {}).get("retrieval_ts")
    except Exception as e:  # noqa: BLE001
        st["failures"]["agent1"] += 1; timeline["agent1_error"] = f"{type(e).__name__}:{e}"
    try:
        a2, _p2 = A2.build(cycle)
        timeline["agent2_snapshot_ts"] = a2.get("snapshot_ts")
    except Exception as e:  # noqa: BLE001
        st["failures"]["agent2"] += 1; timeline["agent2_error"] = f"{type(e).__name__}:{e}"
    timeline["agent1_freshness"] = ((a1 or {}).get("market_regime") or {}) and "ok" if a1 else "missing"
    timeline["agent2_data_gaps"] = (a2 or {}).get("data_gaps")

    # --- Hermes ---
    try:
        d, ctx, cands, tags = HERMES.run(cycle)
    except Exception as e:  # noqa: BLE001
        st["failures"]["hermes"] += 1
        timeline["hermes_error"] = f"{type(e).__name__}:{e}"
        st["windows"][win] = {"status": "HERMES_FAILED", "ts": iso(utcnow())}
        st["counters"]["cycles"] += 1
        _write(state_path(run_id), st); _append_jsonl(run_dir(run_id) / "timeline.jsonl", timeline)
        return {"run_id": run_id, "decision_window": win, "hermes_error": timeline["hermes_error"]}

    input_hash = ctx.get("context_hash")
    dec_id = d.get("decision_id") or f"DEC-{ctx.get('context_id')}"
    d["decision_id"] = dec_id
    timeline.update({"hermes_input_ts": (ctx.get("market") or {}).get("retrieval_ts") or ctx.get("context_id"),
                     "hermes_decision_ts": d.get("ts"), "decision": d.get("decision"),
                     "decision_id": dec_id, "input_hash": input_hash})

    # --- RAW + FROZEN 保存 ---
    decdir = run_dir(run_id) / "decisions"; decdir.mkdir(parents=True, exist_ok=True)
    _write(decdir / f"{dec_id}.raw.json", d)
    # G3 §6 可观测: reason 分类 + decision_hash（旁路；不改变决策/快照/hash）
    try:
        import explain as EX
        _ex = EX.classify(d)
        timeline["reason_code"] = _ex["code"]
        timeline["reason_category"] = _ex["category_cn"]
        timeline["decision_hash"] = EX.decision_hash(d)
        _write(decdir / f"{dec_id}.explain.json", _ex)
    except Exception as e:  # noqa: BLE001
        timeline["explain_error"] = f"{type(e).__name__}:{e}"
    snap = ADP.freeze_decision(d, input_hash=input_hash)
    _write(decdir / f"{dec_id}.frozen.json", snap)

    # --- P1-B: Decision Input Snapshot（immutable; 离线 replay 用；不改变决策）---
    try:
        import replay_inputs as RI
        _prov = {}
        try:
            import pit_cache as _PC
            _dts = d.get("ts") or iso(utcnow())
            for _k in ("hist:XAUUSD:15m", "hist:XAUUSD:5m", "hist:XAUUSD:60m", "hist:XAUUSD:1d"):
                _rec = _PC.get_asof(_k, _dts, "XAUUSD")
                if _rec:
                    _prov[_k] = {"source": _rec.get("source"), "source_hash": _rec.get("source_hash"), "data_ts": _rec.get("data_ts")}
        except Exception:  # noqa: BLE001
            pass
        _sni = RI.build_snapshot(d, ctx, (a1 or {}), (a2 or {}), cands, tags, provenance=_prov)
        RI.write_snapshot(run_dir(run_id), _sni)
        timeline["input_snapshot"] = {"decision_id": _sni["decision_id"], "hash": _sni["snapshot_hash"]}
    except Exception as e:  # noqa: BLE001
        timeline["input_snapshot_error"] = f"{type(e).__name__}:{e}"

    # --- Paper 执行 (仅 TRADE) ---
    px = (ctx.get("market") or {}).get("primary_last")
    cfg = ADP.load_config()
    _shadow = bool((_load(run_dir(run_id) / "RUN_META.json", {}) or {}).get("shadow"))
    mode = "PAPER" if _shadow else (cfg.get("execution") or {}).get("execution_mode", "PAPER")
    pe = _make_executor(cfg, run_id=run_id)
    _ccc = {"broker_reconcile_count": 0, "broker_auto_close_count": 0, "reconcile_duplicate_prevented": 0}
    if mode == "BROKER_DEMO":
        try:
            pe.connect()
        except Exception as e:  # noqa: BLE001
            timeline["broker_error"] = f"{type(e).__name__}:{e}"
            st["windows"][win] = {"status": "BROKER_UNAVAILABLE", "ts": iso(utcnow())}
            st["counters"]["cycles"] += 1
            _write(state_path(run_id), st); _append_jsonl(run_dir(run_id) / "timeline.jsonl", timeline)
            return {"run_id": run_id, "decision_window": win, "broker_error": timeline["broker_error"]}
        # FIX(2026-09-15): 先把“broker 已 SL/TP 平仓但账本未记”的仓位回写，避免账本与账户脱节
        # FIX(2026-09-16): 同轮把执行器已实现成交视图与账本对齐（跨 reconnect/restart），
        #                 并记录 broker_reconcile 可观测计数器（任务书 §十六）。
        try:
            _rc = ADP.reconcile_broker_closes(pe, led, run_id=run_id, execution_mode=mode, decision_window=win)
            if _rc:
                timeline["reconciled_closes"] = _rc
            _rep = getattr(pe, "reconcile_report", None) or {}
            timeline["broker_reconcile"] = {
                "new_closes": _rep.get("new_closes"), "broker_auto_close": _rep.get("broker_auto_close"),
                "rebuilt": _rep.get("rebuilt"), "duplicate_prevented": _rep.get("duplicate_prevented"),
                "history_missing": _rep.get("history_missing")}
            if _rep.get("rebuilt") or _rep.get("new_closes"):
                _ccc["broker_reconcile_count"] += 1
            _ccc["broker_auto_close_count"] += len(_rep.get("broker_auto_close") or [])
            _ccc["reconcile_duplicate_prevented"] += len(_rep.get("duplicate_prevented") or [])
        except Exception as e:  # noqa: BLE001
            timeline["reconcile_error"] = f"{type(e).__name__}:{e}"
    # ---- 价格空间转换层（Execution Preparation；默认关闭 → 对历史行为零影响）----
    # P0-01: signal(XAUUSD) → source-basis → execution(XAUUSD) → 执行前校验。fail-closed 见 hermes_paper_adapter.process。
    execution_plan, execution_reject = None, None
    _ps_cfg = PS.load_config() if PS else {"enabled": False}
    if PS and _ps_cfg.get("enabled") and d.get("decision") == "TRADE" and (d.get("plan") or {}):
        try:
            a1q = ((a1 or {}).get("quotes") or {}).get("gold_spot") or {}
            gc_ts = (a1 or {}).get("generated_utc")
            spot_price, spot_ts = a1q.get("price"), a1q.get("retrieval_ts")
            spot_source = "agent1:gold_spot:" + str(a1q.get("source"))
            live_bid = live_ask = None
            if mode == "BROKER_DEMO":
                try:  # 优先用执行场所自身报价作为 execution space 锚
                    q = pe.adapter.get_quote("XAUUSD")
                    if q.get("ok") and q.get("bid") and q.get("ask"):
                        live_bid, live_ask = float(q["bid"]), float(q["ask"])
                        spot_price = (live_bid + live_ask) / 2.0
                        spot_ts = iso(utcnow())
                        spot_source = "broker:fxtm_demo:XAUUSD:tick"
                except Exception as e:  # noqa: BLE001
                    timeline["price_space_venue_error"] = f"{type(e).__name__}:{e}"
            now_ts = utcnow().timestamp()
            rb = PS.recent_basis(_ps_cfg.get("jump_window_hours", 6), now_ts=now_ts)
            if px and spot_price:
                PS.record_basis(float(spot_price) - float(px), ts=iso(utcnow()))
            rec = PS.prepare(d["plan"], gc_price=px, gc_ts=gc_ts, spot_price=spot_price,
                             spot_ts=spot_ts, spot_source=spot_source, now_ts=now_ts, cfg=_ps_cfg,
                             recent_basis=rb, live_bid=live_bid, live_ask=live_ask)
            timeline["price_space"] = {"valid": rec.get("valid"), "reject_code": rec.get("reject_code"),
                                       "basis": rec.get("basis"), "basis_age": rec.get("basis_age"),
                                       "basis_source": rec.get("basis_source"),
                                       "execution_entry": rec.get("execution_entry")}
            if rec.get("valid"):
                execution_plan = rec
            else:
                execution_reject = rec
        except Exception as e:  # noqa: BLE001
            timeline["price_space_error"] = f"{type(e).__name__}:{e}"
            execution_reject = {"valid": False, "reject_code": "PRICE_SPACE_ERROR",
                                "reject_detail": {"error": timeline["price_space_error"]}}
    out = ADP.process(d, pe, led, market_mid=(market_mid if market_mid is not None else px),
                      close_after=close_after, input_hash=input_hash, run_id=run_id,
                      decision_window=win, execution_mode=mode,
                      execution_plan=execution_plan, execution_reject=execution_reject)
    timeline["execution_backend"] = getattr(pe, "backend", None)
    timeline["paper_execution_ts"] = iso(utcnow())

    # --- checkpoint: Replay vs 执行账户 ---
    rst = R.replay(led, execution_mode=mode)
    acc = pe.account()
    match, mismatch = _account_match(pe, rst, acc)
    timeline["replay_match"] = match

    _fail = st.get("failures")  # FIX(2026-09-15): reload 会丢弃本轮 agent1/agent2 失败计数 → 先留存再恢复
    st = load_state(run_id)
    if _fail is not None:
        st["failures"] = _fail
    for _k, _v in _ccc.items():
        if _v:
            st["counters"][_k] = st["counters"].get(_k, 0) + _v
    if not match:
        st["counters"]["account_match_failures"] = st["counters"].get("account_match_failures", 0) + 1
    st["windows"][win] = {"status": "DONE", "decision_id": dec_id, "decision": d.get("decision"),
                          "execution_result": out.get("execution_result"), "ts": iso(utcnow())}
    st["counters"]["cycles"] += 1
    st["counters"]["decisions"] += 1
    for k in ("TRADE", "WAIT", "REJECT"):
        if d.get("decision") == k:
            st["counters"][k] += 1
    if d.get("decision") == "TRADE":
        st["counters"]["exec_attempts"] += 1
        if out.get("execution_result") == "EXECUTED":
            st["counters"]["exec_executed"] += 1
        elif str(out.get("execution_result", "")).startswith("REJECTED"):
            st["counters"]["exec_rejected"] += 1
    st["last_decision"] = {"ts": d.get("ts"), "decision": d.get("decision"), "decision_id": dec_id,
                           "window": win, "execution_result": out.get("execution_result")}
    if not match:
        st["blocked"] = {"reason": "PAPER_REPLAY_MISMATCH", "detail": mismatch, "ts": iso(utcnow())}
        st["status"] = "BLOCKED"
    _write(state_path(run_id), st)
    _append_jsonl(run_dir(run_id) / "timeline.jsonl", timeline)
    return {"run_id": run_id, "decision_window": win, "decision_id": dec_id, "decision": d.get("decision"),
            "execution_result": out.get("execution_result"), "paper_orders": out.get("paper_orders"),
            "replay_match": match, "blocked": st.get("blocked")}


def _ledger_writable(led):
    try:
        led.parent.mkdir(parents=True, exist_ok=True)
        probe = led.parent / ".write_probe"
        probe.write_text("x", encoding="utf-8"); probe.unlink()
        return True
    except Exception:  # noqa: BLE001
        return False


def _account_match(pe, rst, acc):
    closed = acc["closed_trades"]
    if getattr(pe, "backend", "") == "fxtm_demo":
        # FIX(2026-09-15): 只比“已实现”量(balance/平仓笔数/平仓净额/手续费)；不再比 live 浮动 equity。
        # 原实现拿 replay(snapshot) 去比 broker 实时 equity/浮盈 — 只要有持仓/价格一动必超容差 → 误判 BLOCK。
        tol = 0.05
        broker_net = round(sum(float(t.get("net_usd") or 0.0) for t in closed), 6)
        checks = {"balance": abs((rst["account"]["balance"] or 0) - acc["balance"]) < tol,
                  "net_pnl": abs(rst["net_pnl"] - broker_net) < tol,
                  "trade_count": rst["trade_count"] == len(closed),
                  "commission": abs(rst["commission"] - round(sum(float(t.get("commission_usd") or 0.0) for t in closed), 6)) < tol}
        if not acc.get("positions"):  # 空仓时 equity==balance 才有意义
            checks["equity"] = abs((rst["account"]["equity"] or 0) - acc["equity"]) < tol
        # FIX(2026-09-16): broker deal 历史不可用（无法重建已实现成交）→ fail-closed，
        # 显式标注 history_unavailable，避免与“账实不符”混淆（不静默放行）。
        rep = getattr(pe, "reconcile_report", None) or {}
        if rep.get("history_missing"):
            checks["history_unavailable"] = False
    else:
        sum_cost = round(sum(t["entry_cost_usd"] + t["exit_cost_usd"] for t in closed), 6)
        checks = {"balance": abs((rst["account"]["balance"] or 0) - acc["balance"]) < 1e-6,
                  "equity": abs((rst["account"]["equity"] or 0) - acc["equity"]) < 1e-6,
                  "net_pnl": abs(rst["net_pnl"] - acc["realized_pnl"]) < 1e-6,
                  "trade_count": rst["trade_count"] == len(closed),
                  "commission": abs(rst["commission"] - (-sum_cost)) < 1e-6}
    return all(checks.values()), {k: v for k, v in checks.items() if not v}


# ---------------- metrics / summary ----------------
def metrics(run_id):
    led = run_ledger(run_id)
    evs = L.load_events(led)
    # FIX(2026-09-15): 原硬编码 execution_mode="PAPER" → BROKER_DEMO run 的账本被整段过滤，
    # finalize 产出空 metrics(decisions=0/account=null/conservation=no_initial_balance)。改为取 run manifest 的模式。
    man = _load(run_dir(run_id) / "run_manifest.json", {}) or {}
    mode = man.get("execution_mode", "PAPER")
    st = R.replay(led, execution_mode=mode)
    opened = sum(1 for e in evs if e["event_type"] == "POSITION_OPEN")
    closed = sum(1 for e in evs if e["event_type"] == "POSITION_CLOSED")
    attempts = sum(1 for e in evs if e["event_type"] == "EXECUTION_REQUEST")
    rejected = sum(1 for e in evs if e["event_type"] == "EXECUTION_RESPONSE" and e.get("status") == "REJECTED")
    executed = sum(1 for e in evs if e["event_type"] == "EXECUTION_RESPONSE" and e.get("status") == "EXECUTED")
    # max open positions & drawdown
    mo, cur = 0, 0; eqs = []
    for e in evs:
        if e["event_type"] == "POSITION_OPEN": cur += 1; mo = max(mo, cur)
        elif e["event_type"] == "POSITION_CLOSED": cur -= 1
        if e["event_type"] == "ACCOUNT_SNAPSHOT" and e.get("account_equity") is not None:
            eqs.append(e["account_equity"])
    mdd = 0.0; peak = None
    for v in eqs:
        peak = v if peak is None else max(peak, v)
        if peak: mdd = max(mdd, (peak - v) / peak)
    ver_ok, ver_detail = L.verify_ledger(led)
    cons_ok, cons_detail = R.conservation(st)
    return {"events": len(evs), "verify_ledger": ver_ok, "verify_detail": ver_detail,
            "decisions": st["decisions"], "trade_decisions": st["decisions"]["TRADE"],
            "exec_attempts": attempts, "exec_executed": executed, "exec_rejected": rejected,
            "positions_opened": opened, "positions_closed": closed, "positions_still_open": opened - closed,
            "gross_pnl": st["gross_pnl"], "commission": st["commission"], "swap": st["swap"], "net_pnl": st["net_pnl"],
            "max_open_positions": mo, "max_drawdown_frac": round(mdd, 6),
            "conservation": cons_detail, "conservation_ok": cons_ok,
            "account": st["account"], "state_hash": st["state_hash"]}


def finalize(run_id, status="COMPLETE"):
    st = load_state(run_id)
    st["status"] = "STOPPED" if status == "COMPLETE" else status
    st["end_time_utc"] = iso(utcnow())
    _write(state_path(run_id), st)
    m = metrics(run_id)
    man = _load(run_dir(run_id) / "run_manifest.json", {}) or {}
    man["end_time_utc"] = iso(utcnow())
    man["status"] = status
    _write(run_dir(run_id) / "run_manifest.json", man)
    _write(run_dir(run_id) / "metrics.json", m)
    (run_dir(run_id) / "RUN_SUMMARY.md").write_text(_summary_md(run_id, man, st, m), encoding="utf-8")
    if _load(ACTIVE, {}).get("run_id") == run_id:
        _write(ACTIVE, {**_load(ACTIVE, {}), "stopped": True})
    return m


def _summary_md(run_id, man, st, m):
    c = st["counters"]; f = st["failures"]
    L_ = [f"# RUN SUMMARY — {run_id}", "",
          f"- status: **{man.get('status')}**", f"- start_utc: {man.get('start_time_utc')}",
          f"- end_utc: {man.get('end_time_utc')}", f"- execution_mode: {man.get('execution_mode')}",
          f"- code_commit: `{man.get('code_commit')}`", f"- config_hash: `{man.get('config_hash')}`",
          f"- versions: {json.dumps({k: man.get(k) for k in ('strategy_version','agent1_version','agent2_version','hermes_version','paper_engine_version','ledger_version')}, ensure_ascii=False)}",
          f"- market_data_source: {man.get('market_data_source')}", "",
          "## Decisions", f"- total: {c['decisions']} (TRADE {c['TRADE']} / WAIT {c['WAIT']} / REJECT {c['REJECT']})",
          "## Execution", f"- attempts: {m['exec_attempts']} / executed: {m['exec_executed']} / rejected: {m['exec_rejected']}",
          "## Positions / PnL", f"- opened: {m['positions_opened']} closed: {m['positions_closed']} open_remaining: {m['positions_still_open']}",
          f"- gross: {m['gross_pnl']} commission: {m['commission']} swap: {m['swap']} net: {m['net_pnl']}",
          f"- max_open_positions: {m['max_open_positions']} max_drawdown_frac: {m['max_drawdown_frac']}",
          "## Ledger", f"- events: {m['events']} verify_ledger: {m['verify_ledger']} conservation_ok: {m['conservation_ok']}",
          "## System", f"- agent1_failures: {f['agent1']} agent2_failures: {f['agent2']} hermes_failures: {f['hermes']} ledger_failures: {f['ledger']}",
          f"- duplicate_skips: {c['duplicate_skips']}", f"- blocked: {st.get('blocked')}",
          "", "## Integrity", f"- replay state_hash: `{m['state_hash']}`",
          "- Paper Account == Replay: " + ("PASS" if m["conservation_ok"] else "MISMATCH"),
          "", "## Data", f"- last_decision: {json.dumps(st.get('last_decision'), ensure_ascii=False)}", ""]
    return "\n".join(L_)


# ---------------- CLI ----------------
def _active_minutes(a):
    return a.minutes


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_c = sub.add_parser("cycle"); p_c.add_argument("--minutes", type=int, default=DEFAULT_MINUTES); p_c.add_argument("--close", action="store_true"); p_c.add_argument("--new", action="store_true")
    p_o = sub.add_parser("once"); p_o.add_argument("--cycles", type=int, default=3); p_o.add_argument("--interval-sec", type=float, default=0); p_o.add_argument("--minutes", type=int, default=DEFAULT_MINUTES); p_o.add_argument("--close", action="store_true")
    p_f = sub.add_parser("finalize")
    p_s = sub.add_parser("start"); p_s.add_argument("--minutes", type=int, default=DEFAULT_MINUTES)
    p_ss = sub.add_parser("shadow-start"); p_ss.add_argument("--minutes", type=int, default=DEFAULT_MINUTES)
    sub.add_parser("status"); sub.add_parser("replay-check")
    a = ap.parse_args()
    if a.cmd == "cycle":
        rid, started = ensure_run(a.minutes, allow_new=a.new)
        if rid is None:
            print(json.dumps({"skipped": "FORWARD_LOCKED", "reason": "not_certified"})); return 0
        r = run_cycle(rid, close_after=a.close)
        print(json.dumps({"run_id": rid, "started": started, **r}, ensure_ascii=False)); return 0
    if a.cmd == "once":
        rid, started = ensure_run(a.minutes, allow_new=True)
        for i in range(a.cycles):
            r = run_cycle(rid, close_after=a.close, window=None)
            print(json.dumps({"i": i, **r}, ensure_ascii=False))
            if r.get("blocked"):
                break
            if a.interval_sec and i < a.cycles - 1:
                time.sleep(a.interval_sec)
        finalize(rid)
        print("FINALIZED", rid); return 0
    if a.cmd == "start":
        try:
            rid = start_run(a.minutes)
        except RuntimeError as e:
            print(json.dumps({"refused": str(e)})); return 3
        print(json.dumps({"run_id": rid, "end_utc": _load(ACTIVE, {}).get("end_utc"), "started": True}, ensure_ascii=False)); return 0
    if a.cmd == "shadow-start":
        try:
            rid = start_run(a.minutes, shadow=True)
        except RuntimeError as e:
            print(json.dumps({"refused": str(e)})); return 3
        print(json.dumps({"run_id": rid, "shadow": True, "end_utc": _load(ACTIVE, {}).get("end_utc")}, ensure_ascii=False)); return 0
    if a.cmd == "finalize":
        act = _load(ACTIVE, {}); rid = act.get("run_id"); print("FINALIZED", rid, finalize(rid)); return 0
    if a.cmd == "status":
        act = _load(ACTIVE, {}) or {}
        rid = act.get("run_id")
        print(json.dumps({"active": act, "metrics": metrics(rid) if rid and run_dir(rid).exists() else None}, ensure_ascii=False, indent=1)); return 0
    if a.cmd == "replay-check":
        act = _load(ACTIVE, {}) or {}; rid = act.get("run_id")
        _mode = (_load(run_dir(rid) / "run_manifest.json", {}) or {}).get("execution_mode", "PAPER")
        ok, det = L.verify_ledger(run_ledger(rid)); st = R.replay(run_ledger(rid), _mode)
        print(json.dumps({"run_id": rid, "verify": ok, "detail": det, "state_hash": st["state_hash"],
                          "conservation": R.conservation(st)}, ensure_ascii=False)); return 0
    return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
