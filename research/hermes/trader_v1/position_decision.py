# -*- coding: utf-8 -*-
"""position_decision.py — Position Decision Engine(L2/DESIGN_V11 §6)

每个持仓管理周期产生结构化决策(Position Decision Contract 24 字段)。
Hermes(LLM) 提出策略 → 本引擎做确定性计算 + Risk 独立检查 → 唯一动作。
决策优先级(DESIGN §3): HARD RISK > INVALIDATION > EXECUTION SAFETY > EXTREME >
OPPORTUNITY CHANGE > PROFIT PROTECTION > TRAILING > NORMAL MANAGEMENT。

本模块是确定性骨架(计算 EV/风险/优先级); Hermes 的意图通过持仓决策 JSON 注入
(由外部 Hermes 会话生成, engine 消费后交给本引擎裁决)。
"""
from datetime import datetime, timezone

from position import Position, PositionInvariantError, CONTRACT_SPEC


def _now():
    return datetime.now(timezone.utc).isoformat()


def _r_dist(entry, price):
    """以 R 计的价格距离(entry→price 的 R 倍数; 需带 stop 距离上下文)。"""
    return None


def pos_metrics(pos, price):
    """当前持仓指标(pnl/risk/距离, 单位统一)。"""
    if pos.avg_entry is None or pos.qty_lots <= 0:
        return {"pnl_usd": 0.0, "pnl_R": 0.0, "dist_to_stop_R": None,
                "risk_usd": 0.0, "unrealized_pct": 0.0}
    d = (price - pos.avg_entry) if pos.side == "LONG" else (pos.avg_entry - price)
    pnl_usd = d * CONTRACT_SPEC["contract_size_oz"] * pos.qty_lots
    stop_dist = abs(pos.avg_entry - pos.stop_level) if pos.stop_level else None
    risk_usd = stop_dist * CONTRACT_SPEC["contract_size_oz"] * pos.qty_lots \
        if stop_dist else None
    pnl_R = (pnl_usd / risk_usd) if risk_usd else None
    return {"pnl_usd": round(pnl_usd, 2), "pnl_R": round(pnl_R, 2) if pnl_R else None,
            "risk_usd": round(risk_usd, 2) if risk_usd else None}


def decide(decision_json, pos: Position, price, spread_bps=0.0,
           hard_risk=None, invalidation_hit=False, extreme_event=False,
           new_opportunity_ev=None):
    """主裁决函数。返回结构化决策(dict) + 建议动作。
    decision_json: Hermes 持仓决策(含 original_thesis 评估/意图)。硬风控参数来自 risk_policy,
    不来自 Hermes(此处 hard_risk 由调用方从 RISK_POLICY 注入)。"""
    m = pos_metrics(pos, price)
    d = {
        "position_id": pos.position_id,
        "timestamp": _now(),
        "current_position": {"side": pos.side, "qty_lots": pos.qty_lots,
                             "avg_entry": pos.avg_entry, "state": pos.state},
        "market_state": decision_json.get("market_state", {}),
        "original_thesis": decision_json.get("original_thesis", ""),
        "thesis_status": decision_json.get("thesis_status", "active"),
        "current_pnl": m,
        "current_volatility": decision_json.get("volatility"),
        "opportunity_remaining": decision_json.get("opportunity_remaining", "unknown"),
        "expected_value_if_hold": decision_json.get("ev_hold"),
        "expected_value_if_reduce": decision_json.get("ev_reduce"),
        "expected_value_if_exit": decision_json.get("ev_exit"),
        "opportunity_cost": new_opportunity_ev,
        "action": None, "action_reason": [], "priority": None,
        "new_stop": None, "new_take_profit": None,
        "partial_exit_size": None, "add_size": None,
        "invalidation": decision_json.get("invalidation"),
        "next_review_condition": None, "confidence": decision_json.get("confidence"),
        "risk_verdict": "pass",
    }
    # —— 优先级 1: HARD RISK(独立于 Hermes 的硬参数) ——
    if hard_risk:
        if hard_risk.get("daily_loss_breached"):
            d.update(action="EXIT", priority=1,
                     action_reason=["HARD_RISK daily_loss_breached"])
            d["risk_verdict"] = "hard_exit"
            return d
        if hard_risk.get("consecutive_loss_breached"):
            d.update(action="EXIT", priority=1,
                     action_reason=["HARD_RISK consecutive_loss_breached"])
            return d
        if hard_risk.get("max_notional_breached"):
            d.update(action="REDUCE", priority=1,
                     action_reason=["HARD_RISK max_notional_breached"],
                     partial_exit_size="risk_computed")
            return d
    # —— 优先级 2: POSITION INVALIDATION ——
    if invalidation_hit or decision_json.get("thesis_status") == "invalidated":
        d.update(action="EXIT", priority=2, action_reason=["INVALIDATION thesis_failed"])
        return d
    # —— 优先级 3/4: 执行安全与极端事件 ——
    if extreme_event:
        d.update(action="PROTECT", priority=4,
                 action_reason=["EXTREME_MARKET protect"])
        return d
    # —— 优先级 5: OPPORTUNITY CHANGE(SWITCH 判断) ——
    hold_ev = d["expected_value_if_hold"]
    new_ev = new_opportunity_ev
    if hold_ev is not None and new_ev is not None and new_ev > hold_ev * 1.5 \
            and new_ev > 0:
        d.update(action="EXIT", priority=5,
                 action_reason=[f"SWITCH new_ev {new_ev} > hold {hold_ev}*1.5"])
        return d
    # —— 优先级 6/7: Hermes 意图经 Risk 校验 ——
    intent = decision_json.get("action", "HOLD")
    if intent in ("EXIT", "FULL_EXIT"):
        d.update(action="EXIT", priority=6, action_reason=["hermes_intent_exit"])
    elif intent == "REDUCE":
        size = decision_json.get("partial_exit_size")
        if size and 0 < size < pos.qty_lots:
            d.update(action="REDUCE", priority=6, partial_exit_size=size,
                     action_reason=["hermes_intent_reduce"])
        else:
            d.update(action="HOLD", priority=8,
                     action_reason=["reduce_size_invalid"])
    elif intent == "PARTIAL_EXIT":
        size = decision_json.get("partial_exit_size")
        if size and 0 < size < pos.qty_lots:
            d.update(action="PARTIAL_EXIT", priority=6, partial_exit_size=size,
                     action_reason=["hermes_intent_partial"])
        else:
            d.update(action="HOLD", priority=8, action_reason=["partial_size_invalid"])
    elif intent == "ADD":
        # ADD 铁律: Risk 层拒绝亏损摊平意图(浮亏时 Hermes 不能 ADD)
        if (pos.side == "LONG" and price < pos.avg_entry) or \
           (pos.side == "SHORT" and price > pos.avg_entry):
            d.update(action="HOLD", priority=6,
                     action_reason=["ADD_REJECTED averaging_down_forbidden"])
        elif decision_json.get("add_ev_justification"):
            d.update(action="ADD", priority=6, add_size=decision_json.get("add_size"),
                     action_reason=["hermes_intent_add_ev_justified"])
        else:
            d.update(action="HOLD", priority=8,
                     action_reason=["ADD_REJECTED no_ev_justification"])
    elif intent == "PROTECT":
        # 保本: 须通过资格检查(调用方已在 stop_authority 验), 此处只透传
        d.update(action="PROTECT", priority=7,
                 new_stop=decision_json.get("new_stop"),
                 action_reason=["hermes_intent_protect"])
    else:
        # HOLD / 默认
        d.update(action="HOLD", priority=8, action_reason=["hold_default"])
    d["next_review_condition"] = "next_m15_close"
    return d


def apply_action(pos: Position, action: dict, price, spread_bps=0.0):
    """执行已裁决动作(确定性)。返回结果摘要。动作与 position 层不变量一致。"""
    a = action.get("action")
    if a == "EXIT":
        r = pos.request_exit(f"decision:{action.get('priority')}")
        return {"applied": "EXIT_REQUEST", "note": action["action_reason"]}
    if a == "REDUCE" or a == "PARTIAL_EXIT":
        size = action.get("partial_exit_size")
        if size is None and a == "REDUCE":
            size = round(pos.qty_lots * 0.5, 2)
        pos.partial_exit(price, size, reason=a.lower())
        return {"applied": a, "qty_out": size}
    if a == "ADD":
        size = action.get("add_size")
        pos.add(price, size, ev_justification="engine_approved")
        return {"applied": "ADD", "qty": size}
    if a == "PROTECT":
        ns = action.get("new_stop")
        if ns and isinstance(ns, dict) and ns.get("level"):
            be = ns.get("authority") in ("breakeven", "profit")
            pos.set_stop(ns["level"], authority=ns.get("authority", "profit"),
                         allow_breakeven=be)
            return {"applied": "PROTECT", "new_stop": ns["level"]}
        return {"applied": "PROTECT_NONE"}
    return {"applied": "HOLD"}
