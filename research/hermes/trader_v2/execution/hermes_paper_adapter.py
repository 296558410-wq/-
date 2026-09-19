# -*- coding: utf-8 -*-
"""V2 Module 4/5 — Hermes → Paper → Ledger 接线（Decision Contract + Adapter + 闭环）。

职责: 把 Hermes Decision 规范化/冻结 → 翻译成 Execution Request → 交 PaperExecutor →
将 DECISION/EXECUTION/FILL/POSITION/COST/PNL/ACCOUNT 完整写入 Module3 Ledger（因果链 parent_event_id）。
**纯 translation, 不改信号/方向/阈值/SL/TP/仓位/confidence**。只允许 PAPER。
Module 5 增补: 事件可打 run_id / decision_window 戳记（向后兼容, 默认 None）。
"""
from __future__ import annotations
import copy, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "ledger"))
import paper_executor as PE  # noqa: E402
import ledger as L  # noqa: E402
try:
    import price_space as PS  # noqa: E402
    _PS_FIELDS = tuple(PS.EVENT_FIELDS)
except Exception:  # noqa: BLE001
    PS = None
    _PS_FIELDS = ()

STRATEGY_ID = "hermes_v2"


def _ps_event_fields(plan):
    """价格空间记录字段（additive）。plan 为空(未启用/未换算) → 空 dict（保持账本逐字节不变）。"""
    if not plan or PS is None:
        return {}
    return {k: plan.get(k) for k in _PS_FIELDS if k in plan}
CONTRACT_FIELDS = ["decision_id", "decision", "timestamp_utc", "symbol", "side", "order_type", "volume",
                   "entry_reference", "stop_loss", "take_profit", "reason", "confidence",
                   "context_hash", "input_hash", "strategy_version"]


class RefuseToStart(Exception):
    pass


def load_config():
    return json.loads((ROOT / "config" / "v2_config.json").read_text(encoding="utf-8"))


def assert_paper_only(config=None):
    """启动安全门: 仅 PAPER。任一不满足 → REFUSE_TO_START。不可被参数/环境变量绕过。"""
    cfg = config or load_config()
    ex = cfg.get("execution", {})
    br = cfg.get("broker", {})
    bad = []
    if ex.get("execution_mode") != "PAPER":
        bad.append(f"execution_mode={ex.get('execution_mode')}")
    if ex.get("live_trading") is not False:
        bad.append(f"live_trading={ex.get('live_trading')}")
    if br.get("enabled") is not False:
        bad.append(f"broker.enabled={br.get('enabled')}")
    if ex.get("broker_demo_enabled") is not False:
        bad.append(f"broker_demo_enabled={ex.get('broker_demo_enabled')}")
    if bad:
        raise RefuseToStart("REFUSE_TO_START: " + "; ".join(bad))
    return True


def execution_mode_of(config=None):
    ex = (config or load_config()).get("execution", {})
    return ex.get("execution_mode", "PAPER")


def assert_execution_allowed(config=None):
    """启动安全门（Module 6 起）: 允许 PAPER 或 BROKER_DEMO；**任何 LIVE 一律 REFUSE**。
    PAPER 仍需四条件全 false（与 assert_paper_only 一致）；BROKER_DEMO 要求 broker.enabled+broker_demo_enabled 均 true
    且 live_trading 必须 false。不可被参数/环境变量绕过。"""
    cfg = config or load_config()
    ex = cfg.get("execution", {})
    br = cfg.get("broker", {})
    mode = ex.get("execution_mode", "PAPER")
    bad = []
    if ex.get("live_trading") is not False:
        bad.append(f"live_trading={ex.get('live_trading')}")
    if mode == "PAPER":
        if br.get("enabled") is not False:
            bad.append(f"broker.enabled={br.get('enabled')}")
        if ex.get("broker_demo_enabled") is not False:
            bad.append(f"broker_demo_enabled={ex.get('broker_demo_enabled')}")
    elif mode == "BROKER_DEMO":
        if br.get("enabled") is not True:
            bad.append(f"broker.enabled={br.get('enabled')}(需 true)")
        if ex.get("broker_demo_enabled") is not True:
            bad.append(f"broker_demo_enabled={ex.get('broker_demo_enabled')}(需 true)")
    else:
        bad.append(f"execution_mode={mode}(仅允许 PAPER/BROKER_DEMO)")
    if bad:
        raise RefuseToStart("REFUSE_TO_START: " + "; ".join(bad))
    return True


# ---------------- Decision Contract ----------------
def normalize(decision, symbol="XAUUSD", strategy_version=None, input_hash=None):
    """Hermes decision → Decision Contract dict（不修改入参; 深拷贝 plan）。"""
    d = copy.deepcopy(decision) if isinstance(decision, dict) else {}
    plan = d.get("plan") or {}
    dec = d.get("decision")
    did = d.get("decision_id") or f"DEC-{d.get('context_id') or d.get('ts') or 'UNKNOWN'}"
    side = (plan.get("direction") or "").upper() or None
    return {
        "decision_id": did, "decision": dec, "timestamp_utc": d.get("ts"),
        "symbol": symbol, "side": side, "order_type": "MARKET",
        "volume": plan.get("qty_lots"),
        "entry_reference": plan.get("entry"), "stop_loss": plan.get("stop_loss"),
        "take_profit": plan.get("take_profit"),
        "reason": d.get("reason") or d.get("no_trade_reason"),
        "confidence": plan.get("confidence"),
        "context_hash": d.get("context_hash"), "input_hash": input_hash,
        "strategy_version": strategy_version or "hermes2/0.1.0",
    }


def freeze_decision(decision, symbol="XAUUSD", strategy_version=None, input_hash=None):
    """冻结快照（含 canonical json 摘要, 供不可变性证明）。"""
    snap = normalize(decision, symbol, strategy_version, input_hash)
    snap["_frozen_json"] = json.dumps(snap, sort_keys=True, ensure_ascii=False)
    return snap


def to_execution_request(snap):
    """Decision Snapshot → Execution Request（纯翻译; 不改字段值）。"""
    if snap.get("decision") != "TRADE":
        return None
    return {"symbol": snap["symbol"], "side": snap["side"], "order_type": "MARKET",
            "volume": snap["volume"], "entry_reference": snap["entry_reference"],
            "stop_loss": snap["stop_loss"], "take_profit": snap["take_profit"],
            "decision_id": snap["decision_id"]}


def process(decision, executor, ledger_path, *, symbol="XAUUSD", market_mid=None,
            close_after=False, close_price=None, strategy_version=None, input_hash=None,
            run_id=None, decision_window=None, execution_mode=None,
            execution_plan=None, execution_reject=None):
    """把一个 Hermes Decision 走完 (Paper|BrokerDemo) → Ledger。返回摘要。

    execution_plan / execution_reject（价格空间转换层）: 均为可选；**默认 None**
    → 行为与历史实现逐字节一致（用于保证不启用时对运行中的 run 零影响）。
    - execution_plan: price_space.prepare() 的 valid=True 记录 → 用 execution_* 下单，并写入 additive 字段。
    - execution_reject: valid=False 记录 → 执行层 fail-closed（不下单，记 REJECT）。
    """
    snap = freeze_decision(decision, symbol, strategy_version, input_hash)
    mode = execution_mode or ("BROKER_DEMO" if getattr(executor, "backend", "paper_local") == "fxtm_demo" else "PAPER")

    def emit(**kw):
        kw.setdefault("environment", mode); kw.setdefault("execution_mode", mode)
        if run_id is not None:
            kw["run_id"] = run_id
        if decision_window is not None:
            kw["decision_window"] = decision_window
        return L.append_event(L.new_event(**kw), ledger_path)

    if not L.load_events(ledger_path):
        emit(event_type="ACCOUNT_INIT", account_balance=executor.acc.get("initial_balance"),
             currency=executor.acc.get("currency"))

    ev_dec = emit(event_type="DECISION", strategy_id=STRATEGY_ID,
                  strategy_version=snap["strategy_version"], decision_id=snap["decision_id"],
                  status=snap["decision"], symbol=snap["symbol"], side=snap["side"], order_type="MARKET",
                  volume=snap["volume"], requested_price=snap["entry_reference"],
                  context_hash=snap["context_hash"], input_hash=snap["input_hash"],
                  message=snap["reason"], confidence=snap["confidence"],
                  stop_loss=snap["stop_loss"], take_profit=snap["take_profit"],
                  **_ps_event_fields(execution_plan))
    events = [ev_dec["event_id"]]
    out = {"decision": snap["decision"], "decision_id": snap["decision_id"], "run_id": run_id,
           "decision_window": decision_window, "paper_orders": 0, "position_id": None,
           "execution_result": None, "events": events, "snapshot": snap}

    if snap["decision"] != "TRADE" or snap["side"] not in ("LONG", "SHORT"):
        acc = executor.account()
        emit(event_type="ACCOUNT_SNAPSHOT", account_balance=acc.get("balance"), account_equity=acc.get("equity"),
             free_margin=acc.get("balance"), message=f"no-op decision={snap['decision']}")
        return out

    # ---- 价格空间转换层（可选）: execution space 的 entry/SL/TP - 未启用则等于 signal 值（逐字节不变）----
    ps = execution_plan if (isinstance(execution_plan, dict) and execution_plan.get("valid")) else None
    eff_entry = ps["execution_entry"] if ps else snap["entry_reference"]
    eff_sl = ps["execution_stop_loss"] if ps else snap["stop_loss"]
    eff_tp = ps["execution_take_profit"] if ps else snap["take_profit"]

    req = to_execution_request(snap)
    ev_req = emit(event_type="EXECUTION_REQUEST", strategy_id=STRATEGY_ID, decision_id=snap["decision_id"],
                  parent_event_id=ev_dec["event_id"], symbol=req["symbol"], side=req["side"],
                  order_type="MARKET", volume=req["volume"], requested_price=eff_entry,
                  reference_mid=(eff_entry if ps else market_mid), status="REQUESTED", stop_loss=eff_sl,
                  take_profit=eff_tp, **_ps_event_fields(ps))
    events.append(ev_req["event_id"])

    # fail-closed: 价格空间不可用/异常 → 不下单（不猜测、不送无效价格给 broker）
    if ps is None and execution_reject:
        _code = execution_reject.get("reject_code") or "PRICE_SPACE_ERROR"
        _msg = f"price_space fail-closed: {execution_reject.get('reject_detail')}"
        emit(event_type="EXECUTION_RESPONSE", decision_id=snap["decision_id"],
             parent_event_id=ev_req["event_id"], status="REJECTED", retcode=_code, message=_msg,
             symbol=req["symbol"], side=req["side"], **_ps_event_fields(execution_reject))
        emit(event_type="ORDER_REJECTED", decision_id=snap["decision_id"],
             parent_event_id=ev_req["event_id"], status="REJECTED", retcode=_code, message=_msg)
        out["execution_result"] = f"REJECTED:{_code}"
        acc = executor.account()
        emit(event_type="ACCOUNT_SNAPSHOT", account_balance=acc.get("balance"), account_equity=acc.get("equity"),
             free_margin=acc.get("balance"), message=f"price_space_reject code={_code}")
        return out

    mid = eff_entry if ps else (market_mid if market_mid is not None else snap["entry_reference"])
    res = executor.open(snap["side"], mid, eff_sl, eff_tp,
                        plan_id=snap["decision_id"], context_id=snap["context_hash"],
                        decision_ref=snap["decision_id"], symbol=symbol, qty_lots=snap["volume"])
    if not res.get("ok"):
        emit(event_type="EXECUTION_RESPONSE", decision_id=snap["decision_id"], parent_event_id=ev_req["event_id"],
             status="REJECTED", retcode=res.get("failure_code"), message=res.get("reason"),
             symbol=req["symbol"], side=req["side"])
        emit(event_type="ORDER_REJECTED", decision_id=snap["decision_id"], parent_event_id=ev_req["event_id"],
             status="REJECTED", retcode=res.get("failure_code"), message=res.get("reason"))
        out["execution_result"] = f"REJECTED:{res.get('failure_code')}"
        return out

    pos = res["position"]
    out["paper_orders"] = 1; out["position_id"] = pos["position_id"]; out["execution_result"] = "EXECUTED"
    emit(event_type="EXECUTION_RESPONSE", decision_id=snap["decision_id"], parent_event_id=ev_req["event_id"],
         status="EXECUTED", symbol=req["symbol"], side=req["side"], fill_price=pos["entry"],
         fill_volume=pos["qty_lots"], latency_ms=pos.get("latency_ms"))
    emit(event_type="ORDER_ACCEPTED", decision_id=snap["decision_id"], parent_event_id=ev_req["event_id"],
         status="ACCEPTED", symbol=req["symbol"], side=req["side"], order_id=pos["position_id"])
    ev_fill = emit(event_type="FILL", decision_id=snap["decision_id"], parent_event_id=ev_req["event_id"],
                   position_id=pos["position_id"], symbol=req["symbol"], side=req["side"],
                   fill_price=pos["entry"], fill_volume=pos["qty_lots"], requested_price=mid, status="FILLED")
    ev_open = emit(event_type="POSITION_OPEN", decision_id=snap["decision_id"], parent_event_id=ev_fill["event_id"],
                   position_id=pos["position_id"], symbol=req["symbol"], side=req["side"],
                   volume=pos["qty_lots"], fill_price=pos["entry"], status="OPEN")
    events.append(ev_open["event_id"])

    if close_after:
        px = close_price if close_price is not None else mid
        emit(event_type="POSITION_CLOSE_REQUEST", decision_id=snap["decision_id"],
             parent_event_id=ev_open["event_id"], position_id=pos["position_id"],
             requested_price=px, status="CLOSE_REQUESTED")
        cres = executor.close(pos["position_id"], px, reason="module4_close")
        tr = cres["trade"]
        if "commission_usd" in tr:  # BROKER_DEMO: 以 broker deals 的成本/盈亏为准（带符号）
            comm = round(float(tr.get("commission_usd") or 0.0), 6)
            swap = round(float(tr.get("swap_usd") or 0.0), 6)
            gross = float(tr.get("gross_usd") or 0.0)
            net = float(tr.get("net_usd") or 0.0)
            cmsg = "commission/swap = broker deal 实际值; net = profit+commission+swap"
        else:  # PAPER: commission 折成总执行成本
            total_cost = tr["entry_cost_usd"] + tr["exit_cost_usd"]
            comm = round(-total_cost, 6); swap = 0.0
            gross = tr["gross_usd"]; net = tr["net_usd"]
            cmsg = "commission = 总执行成本(spread+slip+commission), 与 Paper 账户口径一致"
        ev_closed = emit(event_type="POSITION_CLOSED", decision_id=snap["decision_id"],
                         parent_event_id=ev_open["event_id"], position_id=pos["position_id"],
                         symbol=req["symbol"], side=req["side"], volume=tr["qty_lots"],
                         fill_price=tr["exit"], status="CLOSED", gross_pnl=gross,
                         commission=comm, swap=swap, net_pnl=net, message=cmsg)
        emit(event_type="COST", decision_id=snap["decision_id"], parent_event_id=ev_closed["event_id"],
             position_id=pos["position_id"], commission=comm, swap=swap, message="total_exec_cost")
        emit(event_type="PNL", decision_id=snap["decision_id"], parent_event_id=ev_closed["event_id"],
             position_id=pos["position_id"], gross_pnl=gross, net_pnl=net,
             commission=comm, swap=swap)
        events.append(ev_closed["event_id"])

    acc = executor.account()
    emit(event_type="ACCOUNT_SNAPSHOT", account_balance=acc.get("balance"), account_equity=acc.get("equity"),
         free_margin=acc.get("balance"),
         message=f"open={len(acc['positions'])} closed={len(acc['closed_trades'])}")
    return out


def reconcile_broker_closes(executor, ledger_path, *, symbol="XAUUSD", run_id=None,
                            execution_mode=None, decision_window=None):
    """Broker 侧平仓 → 账本 + 执行器状态双向对齐（与 close() 同一状态语义）。

    Phase A: 账本仍 open、broker 已不存在的仓位 → 按 broker deals 补记 POSITION_CLOSED/COST/PNL。
    Phase B: 账本已平仓的全部 position → 从 broker deals 重建 executor.acc["closed_trades"]。
             （必须：connect() 每周期 _fresh() 清空内存态；不重建则「上周期/上进程平掉的仓」
              在下一周期对账时必然 trade_count/net_pnl/commission 不符 → 误判 BLOCK）

    identity/去重: position_id 为唯一键；账本已有 POSITION_CLOSED 的 position 绝不重复补记；
    register/rehydrate 幂等（已存在且数值一致 → no-op）。
    绝不新开/平仓。非 BROKER_DEMO → 0。
    返回：本轮新补记的平仓笔数（int，保持调用方向后兼容）；
         明细写入 executor.reconcile_report。
    """
    if getattr(executor, "backend", "") != "fxtm_demo":
        return 0
    evs = L.load_events(ledger_path)
    ledger_open = {}          # position_id -> POSITION_OPEN event（仍 open）
    ledger_closed = []        # position_id 已平仓（含引擎主动平仓与历史对账）
    for e in evs:
        if e.get("event_type") == "POSITION_OPEN" and e.get("position_id"):
            ledger_open[e["position_id"]] = e
        elif e.get("event_type") == "POSITION_CLOSED" and e.get("position_id"):
            pid = e["position_id"]
            ledger_open.pop(pid, None)
            if pid not in ledger_closed:
                ledger_closed.append(pid)
    mode = execution_mode or "BROKER_DEMO"

    def emit(**kw):
        kw.setdefault("environment", mode); kw.setdefault("execution_mode", mode)
        if run_id is not None:
            kw["run_id"] = run_id
        if decision_window is not None:
            kw["decision_window"] = decision_window
        return L.append_event(L.new_event(**kw), ledger_path)

    report = {"new_closes": [], "duplicate_prevented": [], "rebuilt": [],
              "history_missing": [], "broker_auto_close": []}
    broker_open = {str(p["ticket"]) for p in (executor.adapter.get_positions().get("positions") or [])}

    def _register(tr):
        """执行器状态同步（接口扩展；旧/桩执行器无此方法时不报错）。"""
        fn = getattr(executor, "register_closed_trade", None)
        if fn is None:
            return None
        try:
            return bool(fn(tr))
        except Exception:  # noqa: BLE001
            return None

    # ---- Phase A: broker 已平、账本未记 ----
    n = 0
    for pid, ev in ledger_open.items():
        if pid in broker_open:
            continue                       # 仍在 broker → 不动
        tr = executor.trade_from_deals(pid, reason="broker_sl_tp")
        if not tr:
            report["history_missing"].append(pid)   # broker 无 deal 明细 → 调用方 fail-closed
            continue
        ev_closed = emit(event_type="POSITION_CLOSED", parent_event_id=ev["event_id"], position_id=pid,
                         symbol=symbol, side=ev.get("side"), volume=tr["qty_lots"], fill_price=tr["exit"],
                         status="CLOSED", gross_pnl=tr["gross_usd"], commission=tr["commission_usd"],
                         swap=tr["swap_usd"], net_pnl=tr["net_usd"],
                         message="reconciled from broker deals (SL/TP close)")
        emit(event_type="COST", parent_event_id=ev_closed["event_id"], position_id=pid,
             commission=tr["commission_usd"], swap=tr["swap_usd"], message="total_exec_cost")
        emit(event_type="PNL", parent_event_id=ev_closed["event_id"], position_id=pid,
             gross_pnl=tr["gross_usd"], net_pnl=tr["net_usd"],
             commission=tr["commission_usd"], swap=tr["swap_usd"])
        reg = _register(tr)
        if reg is False:
            report["duplicate_prevented"].append(pid)
        else:
            report["new_closes"].append(pid)
        report["broker_auto_close"].append(pid)
        if pid not in ledger_closed:
            ledger_closed.append(pid)
        n += 1

    # ---- Phase B: 账本已平仓 → 重建执行器已实现视图（跨 reconnect/restart 一致） ----
    _rebuild = getattr(executor, "rebuild_closed_trades", None)
    if ledger_closed and _rebuild is not None:
        rb = _rebuild(ledger_closed)
        report["rebuilt"] = rb["rebuilt"]
        report["duplicate_prevented"] += rb["duplicate_prevented"]
        for pid in rb["missing"]:
            if pid not in report["history_missing"]:
                report["history_missing"].append(pid)

    if n:
        acc = executor.account()
        emit(event_type="ACCOUNT_SNAPSHOT", account_balance=acc.get("balance"), account_equity=acc.get("equity"),
             free_margin=acc.get("balance"), message=f"reconciled_closes={n}")
    try:
        executor.reconcile_report = report
    except Exception:  # noqa: BLE001
        pass
    return n


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("STRATEGY_ID:", STRATEGY_ID)
    assert_paper_only(); print("paper-only gate: PASS")
    print("fields:", CONTRACT_FIELDS)
