# -*- coding: utf-8 -*-
"""engine.py — Hermes 15 分钟交易员闭环编排器(P0: paper/forward observation)。

每 M15 收盘后运行一轮(调度: cron 15min / 手动)。无真实执行 API(P0) → paper fill 模型。
环节: OBSERVE(状态包) → DECIDE(Hermes 判断, LLM 由外部调用; 引擎支持 offline/echo 模式)
      → PLAN 注册(若 LONG/SHORT) → WAIT(触发判定, 机械) → RISK(检查) → EXECUTE(paper)
      → MANAGE(持仓复评) → EXIT → REVIEW → MEMORY(statistics) 。

Hermes 是唯一交易智能体: 本引擎只做确定性编排/记录/风控执行, 决策方向完全来自 Hermes 输出。
用法:
  python engine.py --decide             # 完整一轮: 状态包+决策+计划+触发+持仓管理
  python engine.py --trigger-only       # 仅触发/持仓管理(决策由已注册计划驱动)
  python engine.py --paper-fill ID      # 手动触发一次 paper 成交(测试)
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent.parent.parent))

import ledger  # noqa: E402
from state_package import load_ticks, resample  # noqa: E402

RUN = HERE / "run_state"
DEC_DIR = RUN / "decisions"
POS_P = RUN / "paper_positions.json"
STATS_P = RUN / "statistics.json"
WF_LATEST = RUN / "workflow_latest.json"
WF_HIST = RUN / "workflow_history.jsonl"
MEM_DIR = HERE / "memory"
STATE_PKG_P = RUN / "state_package_latest.json"


def load_json(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default if default is not None else {}


def save_json(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


# ---------------- WORKFLOW TRACE(每轮步骤链, Dashboard 可视化) ----------------
def write_workflow(cycle, pkg, decision, steps_extra=None, meta=None):
    """组装并写 workflow_latest.json + 追加 workflow_history.jsonl(限 96 条=24h)。
    steps: OBSERVE→STATE→THINK→DECIDE→PLAN/WAIT→TRIGGER→RISK→EXECUTE→MANAGE→REVIEW→MEMORY
    每步: {status: done|running|pending|wait|none|skip, start, end, ms, result}"""
    eng_start = meta.get("engine_start_iso") if meta else None
    t0 = _parse_ts(eng_start) or datetime.now(timezone.utc)
    pkg_ts = _parse_ts((pkg or {}).get("generated_utc"))
    dec_ts = _parse_ts((decision or {}).get("utc_ts")) if decision else None
    now = datetime.now(timezone.utc)

    def step(name, status, start, end, result):
        s, e = _parse_ts(start), _parse_ts(end)
        ms = round((e - s).total_seconds() * 1000) if (s and e and e >= s) else None
        return {"step": name, "status": status,
                "start": start.isoformat() if hasattr(start, "isoformat") else start,
                "end": end.isoformat() if hasattr(end, "isoformat") else end,
                "ms": ms, "result": result}

    dq = (pkg or {}).get("data_quality", {})
    ms_ = (pkg or {}).get("market_state", {})
    ms_text = (f"D1 {ms_.get('d1',{}).get('trend_range',{}).get('cat','?')} / "
               f"H4 {ms_.get('h4',{}).get('trend_range',{}).get('cat','?')} / "
               f"H1 {ms_.get('h1',{}).get('trend_range',{}).get('cat','?')}")
    steps = [
        step("OBSERVE", "done", eng_start or pkg_ts, pkg_ts or now,
             f"live_days={dq.get('live_days')} context_days={dq.get('context_days')}"),
        step("STATE", "done", pkg_ts or now, pkg_ts or now, ms_text),
    ]
    if decision is None:
        steps.append(step("THINK", "running" if pkg_ts and (now - pkg_ts).total_seconds() < 600 else "pending",
                          pkg_ts or now, None, "Hermes 决策未到(等待/超时)"))
        steps.append(step("DECIDE", "waiting", None, None, "—"))
    else:
        steps.append(step("THINK", "done", pkg_ts or now, dec_ts or now,
                          f"→ {decision.get('decision')}"))
        steps.append(step("DECIDE", "done", dec_ts or now, dec_ts or now,
                          decision.get("decision")))
    plan_out = (steps_extra or {}).get("plan_out")
    trig_out = (steps_extra or {}).get("trigger_out")
    risk_out = (steps_extra or {}).get("risk_out")
    exec_out = (steps_extra or {}).get("exec_out")
    if plan_out is None and decision and decision.get("decision") == "WAIT":
        plan_out = {"status": "wait", "result": "WAIT(合法)"}
    steps.append(step("PLAN", (plan_out or {}).get("status", "pending"),
                      (plan_out or {}).get("ts"), None, (plan_out or {}).get("result", "—")))
    if trig_out is None:
        steps.append(step("TRIGGER", "pending", None, None, "等待计划触发"))
    else:
        steps.append(step("TRIGGER", trig_out.get("status", "done"),
                          trig_out.get("ts"), trig_out.get("end"), trig_out.get("result")))
    steps.append(step("RISK", (risk_out or {}).get("status", "pending"),
                      (risk_out or {}).get("ts"), None, (risk_out or {}).get("result", "待触发后检查")))
    steps.append(step("EXECUTE", (exec_out or {}).get("status", "pending"),
                      (exec_out or {}).get("ts"), None,
                      (exec_out or {}).get("result", "P0 paper; 未触发不成交")))
    pos = load_json(POS_P)
    mgmt = "持仓中(paper)" if pos and pos.get("open") else "无持仓"
    steps.append(step("MANAGE", "open" if pos and pos.get("open") else "idle", None, None, mgmt))
    steps.append(step("REVIEW", "pending", None, None, "平仓后生成"))
    steps.append(step("MEMORY", "done", now.isoformat(), now.isoformat(), "statistics/ledger 已更新"))

    wf = {"cycle": cycle, "generated_utc": now.isoformat(), "steps": steps}
    RUN.mkdir(parents=True, exist_ok=True)
    WF_LATEST.write_text(json.dumps(wf, indent=1, ensure_ascii=False), encoding="utf-8")
    # 历史(24h 窗口)
    rec = {"cycle": cycle, "utc_ts": now.isoformat(),
           "decision": (decision or {}).get("decision"),
           "plan_id": (plan_out or {}).get("plan_id"),
           "wait_reason": ((decision or {}).get("answers_14") or {}).get("14") if decision and decision.get("decision") == "WAIT" else None,
           "triggered": bool(trig_out) if trig_out else False,
           "traded": bool(exec_out) if exec_out else False}
    lines = []
    if WF_HIST.exists():
        lines = [l for l in WF_HIST.read_text(encoding="utf-8").splitlines() if l.strip()]
    lines.append(json.dumps(rec, ensure_ascii=False))
    WF_HIST.write_text("\n".join(lines[-96:]) + "\n", encoding="utf-8")
    return wf


# ---------------- OBSERVE ----------------
def observe():
    pkg = load_json(STATE_PKG_P)
    if not pkg:
        print("NO_STATE_PACKAGE run state_package.py first", flush=True)
        return None
    return pkg


# ---------------- RISK(独立于 Hermes 的确定性检查) ----------------
RISK_POLICY = {  # P0 默认; 独立文件可覆盖(人工可改, Hermes 无权改)
    # 仓位权威 = 计划自带 qty_lots(LLM 提议); 本层只校验区间(2026-09-08 用户定案 0.01-0.05 手)
    "min_lots": 0.01,
    "max_lots": 0.05,
    "default_lots": 0.01,
    # notional 上限随 max_lots 上浮: 0.05 手 = 5 oz; @$5,000 ≈ $25,000
    "max_position_notional_usd": 25000,
    "max_account_risk_per_trade_pct": 1.0,  # 预留: 接账户余额后启用(paper 无账户)
    "max_daily_loss_pct": 3.0,
    "max_consecutive_losses": 4,
    "max_spread_bps_entry": 1.0,
    "allow_trade": True,  # paper 阶段恒真; 真实执行阶段须用户授权才置 True 且连 broker
}


def validate_plan(plan):
    """TRADE_PLAN_CONTRACT 机械校验: 返回 (ok, issues[])。不修改计划。"""
    issues = []
    d = plan.get("direction")
    zone = plan.get("entry_zone") or {}
    lo, hi = zone.get("low"), zone.get("high")
    stop = (plan.get("stop_logic") or {}).get("level_price")
    tgt = ((plan.get("target_logic") or {}).get("levels") or [{}])[0].get("price")
    if lo is None or hi is None or stop is None or tgt is None:
        issues.append("missing zone/stop/target prices")
        return False, issues
    if d == "LONG" and not (stop < lo <= hi < tgt):
        issues.append(f"geometry LONG violated: stop={stop} zone=[{lo},{hi}] target={tgt}")
    if d == "SHORT" and not (tgt < lo <= hi < stop):
        issues.append(f"geometry SHORT violated: target={tgt} zone=[{lo},{hi}] stop={stop}")
    ev = (plan.get("expected_net_EV") or {}).get("value")
    if ev is not None and isinstance(ev, (int, float)) and ev <= 0:
        issues.append(f"WEAK_EV_PLAN ev={ev} <= 0 (registered but flagged for Risk/review)")
    return (len(issues) == 0), issues


def risk_check(plan, stats):
    """确定性风险检查: 返回 (pass, list of violations)。Hermes 建议可被否决。
    2026-09-08 定案: qty_lots 为仓位唯一权威(计划提议, 区间校验 0.01-0.05),
    不再用硬编码 risk_budget 反推幻影仓位(旧模型曾致所有 M15 计划必然超名义上限)。"""
    v = []
    notional = None
    if plan:
        zone = plan.get("entry_zone") or {}
        lo = zone.get("low") or 0
        hi = zone.get("high") or 0
        ref = (lo + hi) / 2 if (lo or hi) else None
        lots = plan.get("qty_lots")
        if lots is None:
            lots = RISK_POLICY["default_lots"]  # 计划缺省 → 默认档
        try:
            lots = float(lots)
        except (TypeError, ValueError):
            lots = 0.0
            v.append(f"qty_lots_not_number:{plan.get('qty_lots')!r}")
        if lots < RISK_POLICY["min_lots"] or lots > RISK_POLICY["max_lots"]:
            v.append(f"qty_lots {lots} 超出允许区间 [{RISK_POLICY['min_lots']}, {RISK_POLICY['max_lots']}]")
        if ref and lots > 0:
            notional = lots * ref * 100  # 1 lot XAUUSD = 100 oz
            if notional > RISK_POLICY["max_position_notional_usd"]:
                v.append(f"notional {notional:.0f} > max {RISK_POLICY['max_position_notional_usd']}")
    cost = (plan or {}).get("estimated_cost") or {}
    # fix(2026-09-07): estimated_cost 曾允许 float(总bps) -> risk_check 崩溃; 仅 dict 提供 spread_bps 明细
    spread_bps = cost.get("spread_bps") if isinstance(cost, dict) else None
    if (spread_bps or 0) > RISK_POLICY["max_spread_bps_entry"]:
        v.append(f"spread {cost.get('spread_bps')}bps > ceiling {RISK_POLICY['max_spread_bps_entry']}")
    if not RISK_POLICY["allow_trade"]:
        v.append("allow_trade=False (尚未授权真实执行)")
    return (len(v) == 0), v, notional


# ---------------- EXECUTE(paper) ----------------
def paper_execute(plan_id, quote_mid, spread_bps):
    """Paper fill: 市价单在触发时以 touch 成交 + 固定滑点模型(与 execution_reality 保守一致)。
    返回 fill 事件; 标注 paper:true。"""
    sl = 0.02  # paper 滑点 bps(占 spread 的保守比例, 可配)
    slip = quote_mid * sl * 1e-4 * (1 if spread_bps > 0 else 0.5)
    pos = load_json(POS_P)
    fill = {"type": "filled", "utc_ts": now_iso(), "plan_id": plan_id,
            "paper": True, "side": None, "qty_lots": None,
            "entry_price": None, "slippage_bps": round(sl, 4),
            "spread_bps_at_entry": spread_bps, "latency_ms": 0}
    # 简化: 数量与价位由 plan 计算
    return fill


# ---------------- MEMORY/STATS ----------------
def update_stats(**kw):
    st = load_json(STATS_P, {"counters": {}, "waits": {}, "pnl": {}, "frequency": {},
                             "execution_quality": {}, "integrity": {}})
    c = st["counters"]
    for k, v in kw.items():
        if k.startswith("counter_"):
            c[k[8:]] = c.get(k[8:], 0) + v
    st["integrity"] = {"ledger_head": ledger.head(), "last_cycle": kw.get("cycle"),
                       "updated_utc": now_iso()}
    save_json(STATS_P, st)
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decide", action="store_true", help="完整一轮(观察+决策+计划+触发管理)")
    ap.add_argument("--trigger-only", action="store_true")
    ap.add_argument("--echo", default="", help="模拟 Hermes 决策 JSON; 支持 @file 读文件(测试/离线; 生产由 Hermes 输出)")
    ap.add_argument("--exec", default="paper", choices=["paper", "demo"],
                    help="执行后端: paper=本地模拟(默认) / demo=FXTM demo FOK 真实下单")
    ap.add_argument("--cycle", default=None)
    a = ap.parse_args()

    import trader_core as TC  # noqa: PLC0415
    TC.set_exec_mode(a.exec)
    if a.exec == "demo":
        # demo 模式先验账户可达 + 对账
        acc = TC.broker_account()
        if acc.get("error"):
            print(f"DEMO_ACCOUNT_ERROR {acc['error']} — FAIL CLOSED 不发单", flush=True)
            return 4

    t_start = datetime.now(timezone.utc)
    pkg = observe()
    if not pkg:
        return 2
    cycle = a.cycle or pkg.get("cycle") or now_iso()
    st = load_json(STATS_P, {})
    st.setdefault("counters", {})
    st["counters"]["observations"] = st["counters"].get("observations", 0) + 1

    # 每轮不变量检查(Full Integration; 失败 → FAIL CLOSED 冻结新开仓)
    inv = TC.run_invariants(pkg)
    st["last_invariants"] = {"pass": inv["pass"], "failed": inv["failed"],
                             "checked_utc": inv.get("checked_utc")}
    if not inv["pass"]:
        print(f"FAIL_CLOSED invariants={inv['failed']}", flush=True)
        st["counters"]["fail_closed_events"] = st["counters"].get("fail_closed_events", 0) + 1
        save_json(STATS_P, st)
        return 3  # 不变量失败: 本轮不做任何交易动作

    # I6 对账(2026-09-08): demo 模式以 broker 为真相 — 每轮先回收 broker 已自动
    # 平仓(SL/TP 随单)的仓位, 防本地幻影持仓(此前 15min 阈值判定可永久漏判)
    if TC.EXEC_MODE == "demo":
        try:
            rec_out = TC.reconcile_broker_auto_closed()
        except Exception as e:  # noqa: BLE001
            rec_out = []
            print(f"RECONCILE_ERROR {e}", flush=True)
        for o in rec_out:
            if o.get("action") == "RECONCILE_CLOSE":
                st["counters"]["trades_closed"] = st["counters"].get("trades_closed", 0) + 1
                st["counters"]["reconcile_closed"] = st["counters"].get("reconcile_closed", 0) + 1
                print(f"RECONCILE_CLOSE {o['position_id']} {o['reason']} @{o['price']} "
                      f"realized={o['realized_usd']}", flush=True)
            else:
                print(f"RECONCILE {o.get('action')} {o.get('position_id', '')} "
                      f"{o.get('reason', '')}", flush=True)

    # 持仓管理(每轮: mark + 硬止 + 决策) — L1/L2 集成
    m15l = (pkg.get("market_state") or {}).get("m15_live") or {}
    live_mid = m15l.get("last_mid")
    live_spr = m15l.get("spread_bps_now")
    mgmt_out = []
    if live_mid is not None:
        try:
            mgmt_out = TC.manage_positions(live_mid, live_spr or 0.0)
        except Exception as e:  # noqa: BLE001
            print(f"MANAGE_ERROR {e}", flush=True)
            st["counters"]["manage_errors"] = st["counters"].get("manage_errors", 0) + 1
        for o in mgmt_out:
            if o.get("action") == "EXIT":
                st["counters"]["trades_closed"] = st["counters"].get("trades_closed", 0) + 1
            print(f"MANAGE {o.get('position_id')} action={o.get('action')} "
                  f"reason={o.get('reason', o.get('applied', ''))}", flush=True)

    steps_extra = {}
    decision = None
    if a.decide:
        # L0 幂等: 决策文件只消费一次(consumed 标记在统计层; 计划注册幂等由 ledger.register_plan 保证)
        dp = DEC_DIR / f"{cycle.replace(':', '').replace('-', '')}.json"
        if a.echo:
            src = a.echo
            if src.startswith("@"):
                decision = json.loads(Path(src[1:]).read_text(encoding="utf-8"))
            else:
                decision = json.loads(src)
        else:
            # 生产模式: 等待 Hermes 决策
            decision = load_json(dp)
            if not decision:
                print(f"WAITING_HERMES_DECISION {dp} (Hermes 每 M15 收盘后写入; 当前无 → 本轮静默)", flush=True)
                update_stats(cycle=cycle)
                write_workflow(cycle, pkg, None, steps_extra,
                               meta={"engine_start_iso": t_start.isoformat()})
                return 0
        DEC_DIR.mkdir(parents=True, exist_ok=True)
        (DEC_DIR / f"{cycle.replace(':', '').replace('-', '')}.json").write_text(
            json.dumps(decision, indent=1, ensure_ascii=False), encoding="utf-8")
        st["counters"]["decisions"] = st["counters"].get("decisions", 0) + 1
        decision_id = decision.get("decision_id") or f"DEC-{cycle}"
        # 防重复: 该 cycle 已在本轮处理过(进程内)
        if decision_id in getattr(main, "_processed", set()):
            print(f"SKIP_DUPLICATE_DECISION {decision_id} (已处理, L0 幂等)", flush=True)
            update_stats(cycle=cycle)
            return 0
        main._processed = getattr(main, "_processed", set())
        main._processed.add(decision_id)
        if decision.get("decision") == "WAIT":
            w = st.setdefault("waits", {})
            w["consecutive_waits"] = w.get("consecutive_waits", 0) + 1
            w["last_wait_ts"] = now_iso()
            w["last_reason"] = (decision.get("answers_14") or {}).get("14", "")
            w.setdefault("wait_reasons", {})
            r = decision.get("answers_14") or {}
            reason = str(r.get("14", ""))[:60]
            w["wait_reasons"][reason] = w["wait_reasons"].get(reason, 0) + 1
            steps_extra["plan_out"] = {"status": "wait", "ts": now_iso(),
                                       "result": "WAIT(合法)", "plan_id": None}
            print("DECISION WAIT (合法)", flush=True)
        else:
            st["waits"]["consecutive_waits"] = 0
            plan = decision.get("plan") or {}
            if plan:
                plan_id = plan.get("plan_id") or f"TP-{now_iso().replace(':', '').replace('-', '').split('.')[0]}"
                plan["plan_id"] = plan_id
                ok, issues = validate_plan(plan)
                # L0-H1: 幂等注册(同 decision_id / plan_id 只一次)
                ev, ok_reg, reason = ledger.register_plan(
                    plan_id, decision_id, decision.get("decision"), plan,
                    validation={"ok": ok, "issues": issues})
                if ok_reg:
                    st["counters"]["plans_registered"] = st["counters"].get("plans_registered", 0) + 1
                    tag = "OK" if ok else "ISSUES:" + ";".join(issues)
                    steps_extra["plan_out"] = {"status": "registered", "ts": now_iso(),
                                                "result": f"{plan_id} {decision.get('decision')} [{tag}]",
                                                "plan_id": plan_id}
                    print(f"PLAN REGISTERED {plan_id} decision_id={decision_id} valid={tag} "
                          f"ledger_sha={ev['sha256'][:12]}", flush=True)
                else:
                    print(f"PLAN REGISTER SKIPPED {plan_id} ({reason})", flush=True)
        update_stats(cycle=cycle)

    # TRIGGER 判定(L0-H2): 只评估 active(registered)计划; 触发/取消走原子 transition
    pkg_ms = (pkg.get("market_state") or {})
    m15l = pkg_ms.get("m15_live") or {}
    m15t = pkg_ms.get("m15") or {}
    ctx = {"last_close": m15t.get("last_close"), "last_mid": m15l.get("last_mid"),
           "spread_bps": m15l.get("spread_bps_now")}
    trig_msgs, risk_msgs, exec_msgs = [], [], []
    for e in ledger.active_plans()[-10:]:
        pid = e["plan_id"]
        plan = e.get("plan") or {}
        # —— 主动模式: 计划生命周期管理(防僵尸计划) ——
        # 1) 年龄超限取消(maximum_holding_time 默认 M15*8=2h)
        # 2) 价格已远离触发意图: LONG 计划现价已远高于触发带上沿且未触发 → 机会错过, 取消
        #    (旧计划基于注册瞬间价格; 快速行情下应让新轮重建而非干等) —— 2026-09-07 盯梢发现
        try:
            reg_ts = datetime.fromisoformat(e.get("utc_ts", "").replace("Z", "+00:00"))
            age_min = (datetime.now(timezone.utc) - reg_ts).total_seconds() / 60
        except Exception:  # noqa: BLE001
            age_min = 0
        max_hold = 120.0  # 默认 2h; 计划可指定
        mht = (plan.get("maximum_holding_time") or "")
        if mht.startswith("M15*") and mht[4:].isdigit():
            max_hold = float(mht[4:]) * 15
        ez = plan.get("entry_zone") or {}
        ez_hi = ez.get("high")
        ez_lo = ez.get("low")
        mid_now = ctx.get("last_mid")
        direction = plan.get("direction")
        stale = False
        stale_reason = ""
        if age_min > max_hold:
            stale, stale_reason = True, f"plan_expired age={age_min:.0f}min>{max_hold:.0f}min"
        elif mid_now is not None and ez_hi is not None and ez_lo is not None:
            # 价格已完全离开触发意图带(超出 2× 带宽), 且方向已不可达
            band = max(ez_hi - ez_lo, 1.0)
            if direction == "LONG" and mid_now > ez_hi + 2 * band:
                stale, stale_reason = True, f"price_left_setup mid={mid_now} > zone_hi+2band={ez_hi + 2 * band:.1f}(机会已走, 由新轮重建)"
            elif direction == "SHORT" and mid_now < ez_lo - 2 * band:
                stale, stale_reason = True, f"price_left_setup mid={mid_now} < zone_lo-2band={ez_lo - 2 * band:.1f}(机会已走, 由新轮重建)"
        if stale:
            ev, ok_t, reason = ledger.transition(pid, "cancelled", reason=stale_reason)
            if ok_t:
                st["counters"]["plans_cancelled"] = st["counters"].get("plans_cancelled", 0) + 1
                trig_msgs.append(f"CANCELLED {pid} ({stale_reason})")
                print(f"PLAN CANCELLED {pid} ({stale_reason})", flush=True)
            continue
        import trigger as trig  # noqa: PLC0415
        res = trig.check_trigger(plan, ctx)
        if res["result"] == "TRIGGERED":
            # Risk 检查(独立于 Hermes)
            ok, viol, notional = risk_check(plan, st)
            if ok:
                ev, ok_t, reason = ledger.transition(pid, "triggered", matched=res["matched"],
                                                     risk_pass=True, notional_est=notional)
                if ok_t:
                    st["counters"]["triggers"] = st["counters"].get("triggers", 0) + 1
                    trig_msgs.append(f"TRIGGERED {pid} matched={res['matched']}")
                    risk_msgs.append("PASS")
                    # —— EXECUTE(2026-09-08 接线: 此前 risk 通过后停在 triggered 无任何成交) ——
                    fill_px = ctx.get("last_mid")
                    if fill_px is None:
                        fill_px = ctx.get("last_close")
                    pos, ecode = TC.open_position_from_plan(pid, fill_px, ctx.get("spread_bps") or 0.0)
                    if pos is not None:
                        st["counters"]["trades_opened"] = st["counters"].get("trades_opened", 0) + 1
                        exec_msgs.append(f"FILLED {pid} {pos.side} {pos.qty_lots}手 @{pos.avg_entry} "
                                         f"mode={TC.EXEC_MODE}")
                        print(f"EXEC FILLED {pid} {pos.side} {pos.qty_lots}手 @{pos.avg_entry} "
                              f"mode={TC.EXEC_MODE}", flush=True)
                    else:
                        # 成交失败(仓位忙/幂等/broker 拒) → 计划立即终态, 不留僵尸
                        ledger.transition(pid, "cancelled", reason=f"exec_fail:{ecode}")
                        st["counters"]["plans_cancelled"] = st["counters"].get("plans_cancelled", 0) + 1
                        trig_msgs.append(f"CANCELLED {pid} (exec_fail:{ecode})")
                        print(f"EXEC FAIL {pid} {ecode}", flush=True)
                else:
                    trig_msgs.append(f"TRIGGER {pid} SKIP ({reason})")
            else:
                ev, ok_t, reason = ledger.transition(pid, "triggered", matched=res["matched"],
                                                     risk_pass=False, violations=viol)
                if ok_t:
                    # 否决即终态(2026-09-08): 不留 triggered 僵尸等 age 清扫
                    ledger.transition(pid, "cancelled",
                                      reason="risk_block:" + ";".join(viol))
                    st["counters"]["plans_cancelled"] = st["counters"].get("plans_cancelled", 0) + 1
                trig_msgs.append(f"TRIGGERED {pid}(RISK BLOCK)")
                risk_msgs.append("BLOCK:" + ";".join(viol))
                print(f"TRIGGERED {pid} BUT RISK BLOCK: {viol}", flush=True)
        elif res["result"] == "CANCELLED":
            ev, ok_t, reason = ledger.transition(pid, "cancelled",
                                                 reason=res["reason"], matched=res["matched"])
            if ok_t:
                st["counters"]["plans_cancelled"] = st["counters"].get("plans_cancelled", 0) + 1
                trig_msgs.append(f"CANCELLED {pid} ({res['reason']})")
                print(f"PLAN CANCELLED {pid} ({res['reason']})", flush=True)
        else:
            trig_msgs.append(f"PENDING {pid} ({res['matched']})")
            print(f"TRIGGER_CHECK {pid} → PENDING ({res['matched']})", flush=True)
    if trig_msgs:
        steps_extra["trigger_out"] = {"status": "done", "ts": now_iso(), "end": now_iso(),
                                      "result": "; ".join(trig_msgs[-4:])}
    if risk_msgs:
        steps_extra["risk_out"] = {"status": "checked", "ts": now_iso(),
                                    "result": "; ".join(risk_msgs[-4:])}
    if exec_msgs:
        steps_extra["exec_out"] = {"status": "paper", "ts": now_iso(),
                                    "result": "; ".join(exec_msgs[-4:])}

    save_json(STATS_P, st)
    write_workflow(cycle, pkg, decision, steps_extra,
                   meta={"engine_start_iso": t_start.isoformat()})
    print("CYCLE_DONE", cycle, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
