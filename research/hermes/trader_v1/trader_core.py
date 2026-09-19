# -*- coding: utf-8 -*-
"""trader_core.py — 执行与持仓管理确定性核心(Full Integration)

职责: 把 L0-L3 组件接成完整链路:
  trigger(计划触发) → risk → position 建仓(fill) → 每轮 mark/manage(决策优先级)
  → 硬止损/硬止盈检查 → exit → review 归档 → ledger 事件同步 → 不变量每轮检查

所有函数确定性、无 LLM(LLM=Hermes 在决策层)。paper fill 模型(无真实 broker)。
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ledger  # noqa: E402
import position as P  # noqa: E402
import invariants as INV  # noqa: E402
import review as RV  # noqa: E402
from position import Position, PositionInvariantError, CONTRACT_SPEC  # noqa: E402
import position_decision as PD  # noqa: E402

RUN = HERE / "run_state"
EXEC_MODE = "paper"  # paper | demo(由 engine --exec 切换; demo=真实 FXTM demo 账户 FOK)

def set_exec_mode(mode):
    global EXEC_MODE
    assert mode in ("paper", "demo"), f"bad exec mode {mode}"
    EXEC_MODE = mode


def broker_account():
    """账户信息(paper→本地模拟; demo→真实 broker)。"""
    if EXEC_MODE == "demo":
        import broker_mt5_demo as B  # noqa: PLC0415
        acc = B.get_account()
        if acc.get("ok"):
            return {"mode": "demo", "balance": acc["balance"], "equity": acc["equity"],
                    "margin_free": acc["margin_free"], "margin_level": acc["margin_level"],
                    "leverage": acc["leverage"], "currency": acc["currency"],
                    "login": acc["login"], "server": acc["server"]}
        return {"mode": "demo", "error": acc.get("error")}
    return {"mode": "paper", "balance": None, "equity": None, "note": "paper 无账户"}


def broker_sync_positions():
    """broker 状态对账(I6): demo 模式从 broker 拉真实持仓与本地 position 快照比对。
    返回 (本地未平, broker 未平, 不一致列表)。"""
    local = [s for s in P.open_positions() if s.get("state") not in ("CLOSED",)]
    if EXEC_MODE == "paper":
        return local, [], []
    import broker_mt5_demo as B  # noqa: PLC0415
    bp = B.get_positions()
    if not bp.get("ok"):
        return local, [], [f"broker_unreachable:{bp.get('error')}"]
    bpos = bp.get("positions", [])
    # demo 模式: 本地 position_id ↔ broker ticket 映射存 snapshot 字段 broker_ticket
    mism = []
    for s in local:
        ticket = s.get("broker_ticket")
        if ticket and not any(b["ticket"] == ticket for b in bpos):
            mism.append(f"local_open_but_broker_closed:{s['position_id']}(ticket {ticket})")
    for b in bpos:
        if not any(s.get("broker_ticket") == b["ticket"] for s in local):
            mism.append(f"broker_open_but_no_local:{b['ticket']}")
    return local, bpos, mism


def _now():
    return datetime.now(timezone.utc).isoformat()


def load_json(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default if default is not None else {}


def next_position_id(plan_id):
    return f"POS-{plan_id.replace('TP-', '')}"


def open_position_from_plan(plan_id, price, spread_bps):
    """触发通过 Risk 后建仓。EXEC_MODE=paper → 本地模拟; =demo → broker FOK 真实下单。
    返回 position 对象。"""
    regs = [e for e in ledger.all_events() if e.get("type") == "registered"
            and e.get("plan_id") == plan_id]
    if not regs:
        return None, "no_registered_plan"
    plan = regs[-1].get("plan") or {}
    side = plan.get("direction")
    stop = (plan.get("stop_logic") or {}).get("level_price")
    tgt = plan.get("target_logic") or {}
    tp_levels = [{"price": x["price"], "frac": x.get("frac", 1.0)}
                 for x in (tgt.get("levels") or [])]
    pos_id = next_position_id(plan_id)
    if P.load_position(pos_id) is not None:
        return None, "position_exists"          # 幂等: 已建仓
    # 单仓约束(防 I12 方向冲突): 已有未平仓 → 拒绝新开, 等管理平仓后新轮重建
    if any(s.get("qty_lots", 0) > 0 for s in P.open_positions()):
        return None, "position_busy"
    # 手数: 计划自带为准; 此处只做合约级防御(政策区间 0.01-0.05 由 engine.risk_check 把关)
    qty = plan.get("qty_lots")
    try:
        qty = float(qty) if qty is not None else 0.01
    except (TypeError, ValueError):
        qty = 0.0
    spec = P.CONTRACT_SPEC
    if qty < spec["min_lot"] - 1e-9 or qty > spec["max_lot"] + 1e-9:
        return None, f"qty_out_of_contract:{plan.get('qty_lots')}"
    broker_ticket = None
    if EXEC_MODE == "demo":
        import broker_mt5_demo as B  # noqa: PLC0415
        r = B.market_order(side, qty, sl=stop, tp=(tp_levels[0]["price"] if tp_levels else None))
        if not r.get("ok"):
            return None, f"broker_reject:{r.get('error')}"
        price = r["fill_price"]
        broker_ticket = r.get("ticket")
        # 若 broker 侧带 SL/TP 则本地同步
    pos = Position(pos_id, plan_id, side, stop_level=stop, tp_levels=tp_levels)
    pos.enter()
    pos.fill(price, qty)
    if broker_ticket:
        pos.broker_ticket = broker_ticket
        pos._persist()
    ledger.transition(plan_id, "filled", price=price, qty=qty, position_id=pos_id,
                      exec_mode=EXEC_MODE, broker_ticket=broker_ticket)
    return pos, "ok"


def check_hard_stops(pos, price, spread_bps=0.0):
    """硬止损/硬止盈/时间止损(优先级 1/2 的机械部分)。返回 exit 事件或 None。
    使用当前价(ask/bid touch 判定由调用方给触发价)。"""
    if pos.state == "CLOSED":
        return None
    if pos.stop_level is not None:
        if pos.side == "LONG" and price <= pos.stop_level:
            pos.hard_stop_hit(price)
            return {"reason": "hard_stop", "price": price}
        if pos.side == "SHORT" and price >= pos.stop_level:
            pos.hard_stop_hit(price)
            return {"reason": "hard_stop", "price": price}
    for tp in pos.tp_levels or []:
        tpx = tp.get("price")
        # 2026-09-08 fix: TP 命中只做检测不迁移状态(partial 需在 OPEN 态执行;
        # 旧代码先 hard_tp_hit→EXIT_PENDING 再 partial_exit→非法迁移卡死)
        if pos.side == "LONG" and tpx and price >= tpx:
            return {"reason": "hard_tp", "price": price, "frac": tp.get("frac", 1.0),
                    "tp_price": tpx}
        if pos.side == "SHORT" and tpx and price <= tpx:
            return {"reason": "hard_tp", "price": price, "frac": tp.get("frac", 1.0),
                    "tp_price": tpx}
    return None


def manage_positions(price, spread_bps, hermes_decision=None):
    """每轮: 所有未平仓位的 mark + 硬止检查 + (若 Hermes 给持仓决策) 决策引擎。"""
    out = []
    for snap in P.open_positions():
        pos = P.load_position(snap["position_id"])
        if pos is None:
            continue
        pos.mark(price)
        # 崩溃恢复(2026-09-08): 上轮已 HARD_STOP_HIT/EXIT_REQUEST 但未 exit_fill → 回补成交,
        # 否则 EXIT_PENDING 卡死(旧代码下轮 hard_stop_hit 重复调用非法被吞)
        if pos.state == "EXIT_PENDING":
            last = (pos.events or [])[-1] if pos.events else None
            ev_name = (last or {}).get("event", "")
            reason_tag = {"HARD_STOP_HIT": "hard_stop", "HARD_TP_HIT": "hard_tp",
                          "EXIT_REQUEST": "decision", "INVALIDATE": "decision"}.get(ev_name, "recovered_exit")
            if EXEC_MODE == "demo" and getattr(pos, "broker_ticket", None):
                import broker_mt5_demo as B  # noqa: PLC0415
                br = B.close_position(pos.broker_ticket)
                if br.get("ok"):
                    price = br.get("close_price") or price
            realized = pos.exit_fill(price, reason=reason_tag)
            ledger.transition(pos.plan_id, "closed", exit_price=price,
                              reason=reason_tag, realized_usd=realized,
                              exec_mode=EXEC_MODE)
            _gen_review(pos, {"reason": reason_tag})
            out.append({"position_id": pos.position_id, "action": "EXIT",
                        "reason": f"recovered_from_{ev_name}", "realized_usd": realized})
            continue
        # 硬止损/止盈优先(机械, 独立于 LLM)
        hit = check_hard_stops(pos, price, spread_bps)
        if hit:
            if hit["reason"] == "hard_stop":
                # demo 模式: 先 broker 平仓(真实成交); 成功后更新本地
                if EXEC_MODE == "demo" and getattr(pos, "broker_ticket", None):
                    import broker_mt5_demo as B  # noqa: PLC0415
                    br = B.close_position(pos.broker_ticket)
                    if br.get("ok"):
                        price = br.get("close_price") or price
                realized = pos.exit_fill(price, reason="hard_stop")
                ledger.transition(pos.plan_id, "closed", exit_price=price,
                                  reason="hard_stop", realized_usd=realized,
                                  exec_mode=EXEC_MODE)
                out.append({"position_id": pos.position_id, "action": "EXIT",
                            "reason": "hard_stop", "realized_usd": realized})
            elif hit["reason"] == "hard_tp":
                frac = hit.get("frac", 1.0)
                remaining = pos.qty_lots
                qty = round(remaining * frac, 2)
                min_lot = P.CONTRACT_SPEC["min_lot"]
                # 手数粒度: 余量不足最小手 / 部分量舍入归零 → 全平;
                # demo 无部分平仓能力(broker 侧对账 I6 要求本地=broker) → 全平
                full = (frac >= 1.0 - 1e-9 or qty >= remaining - 1e-9
                        or remaining - qty < min_lot - 1e-9 or qty <= 0
                        or EXEC_MODE == "demo")
                if full:
                    if EXEC_MODE == "demo" and getattr(pos, "broker_ticket", None):
                        import broker_mt5_demo as B  # noqa: PLC0415
                        br = B.close_position(pos.broker_ticket)
                        if br.get("ok"):
                            price = br.get("close_price") or price
                    pos.hard_tp_hit(price, frac=frac)
                    realized = pos.exit_fill(price, reason="hard_tp")
                    ledger.transition(pos.plan_id, "closed", exit_price=price,
                                      reason="hard_tp", realized_usd=realized,
                                      exec_mode=EXEC_MODE)
                else:
                    pos.partial_exit(price, qty, reason="tp_partial")
                    # 消耗该 TP 档(防重复命中同档)
                    hit_px = hit.get("tp_price")
                    pos.tp_levels = [x for x in pos.tp_levels
                                     if abs(x.get("price", 0) - hit_px) > 1e-9]
                    pos._persist()
                out.append({"position_id": pos.position_id,
                            "action": "PARTIAL_EXIT" if not full else "EXIT",
                            "reason": "hard_tp"})
            # 平仓后立即生成 review(接入 M8)
            _gen_review(pos, hit)
            continue
        # Hermes 持仓决策(若有)
        if hermes_decision and hermes_decision.get("position_id") == pos.position_id:
            d = PD.decide(hermes_decision, pos, price, spread_bps)
            if d["action"] in ("EXIT",):
                pos.request_exit(f"decision_p{d['priority']}")
                realized = pos.exit_fill(price, reason=d["action_reason"][0])
                ledger.transition(pos.plan_id, "closed", exit_price=price,
                                  reason="decision", realized_usd=realized)
                _gen_review(pos, {"reason": "decision"})
                out.append({"position_id": pos.position_id, "action": "EXIT",
                            "reason": d["action_reason"][0], "realized_usd": realized})
            else:
                res = PD.apply_action(pos, d, price, spread_bps)
                out.append({"position_id": pos.position_id, "action": d["action"],
                            "priority": d.get("priority"), "applied": res})
        else:
            out.append({"position_id": pos.position_id, "action": "MANAGE_SCAN",
                        "state": pos.state})
    return out


def _gen_review(pos, hit):
    """平仓后生成 review(M8 接入)。从 ledger 取 fill 事件。"""
    try:
        evs = ledger.plan_events(pos.plan_id)
        fill = next((e for e in evs if e.get("type") == "filled"), None)
        closed = next((e for e in evs if e.get("type") == "closed"), None)
        if fill and closed:
            RV.build_review(pos.plan_id,
                            {"entry_price": fill.get("price"),
                             "utc_ts": fill.get("utc_ts"),
                             "qty": fill.get("qty"),
                             "spread_bps_at_entry": fill.get("spread_bps"),
                             "slippage_bps": 0.02, "latency_ms": 0},
                            {"exit_price": closed.get("exit_price"),
                             "utc_ts": closed.get("utc_ts"),
                             "reason": closed.get("reason")})
    except Exception:  # noqa: BLE001
        pass


def run_invariants(state_pkg=None):
    """每轮不变量检查。失败 → 返回报告(由调用方 FAIL CLOSED: 冻结新开仓)。"""
    res = INV.check_all(state_pkg)
    return res


def reconcile_broker_auto_closed():
    """I6 执行(2026-09-08): demo 模式以 broker 为真相。
    本地 OPEN 且带 broker_ticket 的仓位, 若 broker 已无该持仓(随单 SL/TP 自动平仓/
    手工平), 从 deals 历史取真实平仓价 → 本地 exit_fill + ledger closed + review。
    —— 修复: 此前 broker 侧平仓后本地 15min 阈值判定可能永不触发 → 幻影持仓。
    找不到离场成交(ok:False)时不动(不臆断平仓价)。paper 模式: 本地即真相, 直接返回。"""
    if EXEC_MODE != "demo":
        return []
    import broker_mt5_demo as B  # noqa: PLC0415
    local = [s for s in P.open_positions()
             if s.get("state") != "CLOSED" and s.get("broker_ticket")]
    if not local:
        return []
    bp = B.get_positions()
    if not bp.get("ok"):
        return [{"action": "RECONCILE_SKIP",
                 "reason": f"broker_unreachable:{bp.get('error')}"}]
    broker_tickets = {p["ticket"] for p in bp.get("positions", [])}
    out = []
    for s in local:
        t = s.get("broker_ticket")
        if t in broker_tickets:
            continue
        pos = P.load_position(s["position_id"])
        if pos is None or pos.state == "CLOSED":
            continue
        deal = B.get_closing_deal(t)
        if not deal.get("ok"):
            out.append({"position_id": s["position_id"], "action": "RECONCILE_PENDING",
                        "reason": f"no_closing_deal:{deal.get('error')}"})
            continue
        px = deal["price"]
        stop = pos.stop_level
        tps = [x["price"] for x in (pos.tp_levels or [])]
        eps = 0.15  # SL/TP 位容差(成交价可差 1-2 tick)
        if pos.side == "LONG" and stop and px <= stop + eps:
            reason = "broker_sl"
        elif pos.side == "SHORT" and stop and px >= stop - eps:
            reason = "broker_sl"
        elif tps and pos.side == "LONG" and px >= min(tps) - eps:
            reason = "broker_tp"
        elif tps and pos.side == "SHORT" and px <= max(tps) + eps:
            reason = "broker_tp"
        else:
            reason = "broker_close"
        # 状态机: OPEN → EXIT_REQUEST → EXIT_PENDING → EXIT_FILL(直接 exit_fill 非法)
        pos.request_exit(reason)
        realized = pos.exit_fill(px, reason=reason)
        ledger.transition(pos.plan_id, "closed", exit_price=px, reason=reason,
                          realized_usd=realized, exec_mode="demo", broker_auto=True)
        _gen_review(pos, {"reason": reason})
        out.append({"position_id": pos.position_id, "action": "RECONCILE_CLOSE",
                    "reason": reason, "price": px, "realized_usd": realized})
    return out


if __name__ == "__main__":
    print(json.dumps(run_invariants(), ensure_ascii=False, indent=1))
