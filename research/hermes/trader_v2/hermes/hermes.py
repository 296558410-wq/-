# -*- coding: utf-8 -*-
"""Hermes V2 决策引擎（Opportunity Discovery → Decision）。

流程(每次运行): 冻结 decision_context → discovery(候选机会) → 决策(Trade/Wait/Reject)
→ 契约门禁(新鲜度/定价/反证/风险回报/证据冲突) → 写 opportunity_ledger + hermes_memory + state。

决策来源:
- 生产: decision_source="llm"(由编排层把冻结 context + 候选喂给 Hermes LLM, 回填 decision)。
- Phase-1 基线/测试: decision_source="reference_rules"(确定性参照器, 用于打通链路与回归测试)。
铁律: 不投票; WAIT 是正常结果; LIVE_TRADING=false; 只产决策, 执行由 Paper Engine 负责。
用法: python hermes.py [--source reference_rules|llm] [--cycle X]
"""
from __future__ import annotations
import argparse, copy, json, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # hermes/ → trader_v2 (修正: 原 HERE.parents[1] 多算一级)
sys.path.insert(0, str(HERE))
import context as CTX  # noqa: E402
import discovery as DISC  # noqa: E402

STATE = ROOT / "state"
OPP_LEDGER = STATE / "opportunity_ledger.jsonl"
MEM = STATE / "hermes_memory.jsonl"
HSTATE = STATE / "hermes_state.json"
DEC_LATEST = STATE / "hermes_decision_latest.json"
LIVE_TRADING = False  # 硬门: Phase-1 永不开

MIN_EXPECTED_R = 1.0
CATEGORY_PRIORITY = ["false_breakout", "breakout", "trend", "macro_repricing", "geopolitical", "narrative_flow"]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _append(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def gate(cand, ctx, a2, a1=None):
    """契约门禁: 返回 (verdict, reason)。verdict ∈ TRADE/WAIT/REJECT。"""
    f1 = ctx["agent1"]["freshness"]; f2 = ctx["agent2"]["freshness"]
    if f1 in ("expired", "unknown") or f2 in ("expired", "unknown"):
        return "WAIT", f"数据不新鲜(a1={f1}, a2={f2}) → 等刷新"
    # P0-04: 数据健康度进入决策链（FAIL→不交易；DEGRADED→等）
    _ov = (ctx.get("health") or {}).get("overall_status")
    if _ov == "FAIL":
        return "REJECT", f"data health FAIL → 不交易"
    if _ov == "DEGRADED":
        return "WAIT", "data health DEGRADED → 等恢复"
    # P0-03/P0-04: 宏观核心数据不可用 → fail-closed（禁止以 NEUTRAL 绕过）。
    # 注意：属数据质量门（非策略）；旧快照无 macro_status 字段时向后兼容。
    _ms = (a2 or {}).get("macro_status")
    if _ms is not None and _ms != "OK":
        return "WAIT", f"宏观核心数据不可用(macro_status={_ms}) → 等数据恢复"
    if cand is None:
        return "WAIT", "未发现机会"
    macro_state = a2.get("gold_macro_state", "UNCERTAIN")
    dirn = cand.get("dir_hint")
    if dirn is None:
        return "WAIT", "机会方向未定(如背离类) → 等价格选择方向"
    if (dirn == "LONG" and macro_state == "BEARISH") or (dirn == "SHORT" and macro_state == "BULLISH"):
        return "WAIT", f"技术({dirn}) 与宏观({macro_state}) 冲突 → 证据冲突, 等确认"
    if cand.get("priced_in") == "HIGH":
        return "WAIT", "机会可能已被定价(price already extended) → 等回撤/确认"
    if cand.get("requires_confirmation"):
        return "WAIT", "该机会需市场确认(follow-through 未验) → 先观察"
    pos_pct = (((a1 or {}).get("timeframes", {}).get("15m", {}) or {}).get("range60") or {}).get("pos_pct")
    if pos_pct is not None:
        if dirn == "LONG" and pos_pct >= 88:
            return "REJECT", f"风险回报不足/追高(LONG 但处区间高位 pos={pos_pct})"
        if dirn == "SHORT" and pos_pct <= 12:
            return "REJECT", f"风险回报不足/追空(SHORT 但处区间低位 pos={pos_pct})"
    if (cand.get("expected_R_est") or 0) < MIN_EXPECTED_R:
        return "REJECT", f"风险回报不足 expected_R={cand.get('expected_R_est')} < {MIN_EXPECTED_R}"
    if not cand.get("counter_thesis"):
        return "REJECT", "缺少反证(counter_thesis)"
    return "TRADE", "证据通过门禁"


def build_plan(cand, price):
    if not price:
        return None
    d = cand["dir_hint"]
    est_r = cand.get("expected_R_est") or 1.5
    risk = round(price * 0.004, 2)  # 默认 0.4% 结构风险(占位; 具体入场后由规则细化)
    if d == "LONG":
        sl = round(price - risk, 2); tp = round(price + risk * est_r, 2)
    else:
        sl = round(price + risk, 2); tp = round(price - risk * est_r, 2)
    return {"direction": d, "entry": round(price, 2), "stop_loss": sl, "take_profit": tp,
            "risk_per_trade_pct": 1.0, "expected_holding_time": "M15*8",
            "trigger_condition": cand.get("trigger"), "invalidation_condition": cand.get("invalidation"),
            "thesis": cand.get("thesis"), "counter_thesis": cand.get("counter_thesis"),
            "evidence_ids": cand.get("evidence_ids", []), "confidence": 0.55,
            "expected_R": est_r}


def decide_pure(ctx, a1, a2, source="reference_rules", llm_decision=None):
    """确定性决策（**无副作用**）——live 与离线 replay 共用同一代码路径。
    返回 (d, cands, tags)。不做任何文件写入。"""
    cands = DISC.discover(ctx, a1, a2)
    tags = DISC.regime_tags(ctx, a1, a2)
    if source == "llm" and llm_decision:
        d = copy.deepcopy(llm_decision)
    else:
        # 参照器: 选优先级最高候选 → 门禁
        chosen = None
        for cat in CATEGORY_PRIORITY:
            hit = [c for c in cands if c["category"] == cat]
            if hit:
                chosen = hit[0]; break
        verdict, reason = gate(chosen, ctx, a2, a1)
        price = (ctx.get("market") or {}).get("primary_last")
        plan = build_plan(chosen, price) if verdict == "TRADE" else None
        d = {"decision": verdict, "reason": reason, "chosen_opportunity": (chosen or {}).get("id"),
             "regime_tags": tags, "plan": plan,
             "no_trade_reason": None if verdict == "TRADE" else reason}
    d.update({"context_id": ctx["context_id"], "context_hash": ctx["context_hash"],
              "decision_source": source, "ts": _now(), "instrument": "XAUUSD", "reference_market": "GC_F",
              "live_trading": LIVE_TRADING, "signal_from_agents": False})
    return d, cands, tags


def decide(ctx, a1, a2, source="reference_rules", llm_decision=None):
    """返回 (decision, cands, tags)。决策来自 decide_pure（同一确定性路径）；此处仅做候选留痕（写 OPP_LEDGER）。"""
    d, cands, tags = decide_pure(ctx, a1, a2, source, llm_decision)
    # 记录所有候选机会(即便不交易)
    for c in cands:
        _append(OPP_LEDGER, {"opportunity_id": f"{ctx['context_id']}_{c['id']}",
                             "detected_at": _now(), "context_id": ctx["context_id"],
                             "thesis": c.get("thesis"), "direction": c.get("dir_hint"),
                             "trigger": c.get("trigger"), "invalidation": c.get("invalidation"),
                             "expected_edge": c.get("expected_R_est"), "priced_in": c.get("priced_in"),
                             "counter_thesis": c.get("counter_thesis"), "evidence_ids": c.get("evidence_ids"),
                             "status": "detected"})
    return d, cands, tags


def run(cycle=None, source="reference_rules", llm_decision=None, agent1_path=None, agent2_path=None):
    ctx, ctxp = CTX.build_context(cycle, agent1_path, agent2_path)
    a1 = _load(agent1_path or STATE / "agent1_latest.json") or {}
    a2 = _load(agent2_path or STATE / "agent2_latest.json") or {}
    d, cands, tags = decide(ctx, a1, a2, source, llm_decision)
    STATE.mkdir(parents=True, exist_ok=True)
    DEC_LATEST.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    _append(MEM, {"ts": _now(), "context_id": ctx["context_id"], "regime_tags": tags,
                  "n_candidates": len(cands), "decision": d["decision"], "reason": d.get("reason"),
                  "chosen": d.get("chosen_opportunity"), "counter_thesis": (d.get("plan") or {}).get("counter_thesis"),
                  "outcome": None, "why_wrong": None})
    _append(OPP_LEDGER, {"opportunity_id": f"{ctx['context_id']}_DECISION", "detected_at": _now(),
                         "context_id": ctx["context_id"], "decision": d["decision"],
                         "decision_reason": d.get("reason"), "status": "decided"})
    # hermes_state 汇总
    st = _load(HSTATE, {"regime_tags": [], "n_runs": 0, "last_decision": None,
                        "recent_opportunities": [], "recent_rejections": [], "current_hypotheses": [],
                        "invalidated_hypotheses": []}) or {}
    st["n_runs"] = st.get("n_runs", 0) + 1
    st["regime_tags"] = tags
    st["last_decision"] = {"ts": d["ts"], "decision": d["decision"], "reason": d.get("reason"),
                           "context_id": ctx["context_id"]}
    st["recent_opportunities"] = ((st.get("recent_opportunities") or []) + [c["id"] for c in cands])[-20:]
    if d["decision"] in ("WAIT", "REJECT"):
        st["recent_rejections"] = ((st.get("recent_rejections") or []) + [{"dec": d["decision"], "reason": d.get("reason")}])[-20:]
    HSTATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    return d, ctx, cands, tags


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="reference_rules", choices=["reference_rules", "llm"])
    ap.add_argument("--cycle", default=None)
    a = ap.parse_args()
    d, ctx, cands, tags = run(a.cycle, a.source)
    print("HERMES_DECISION:", d["decision"], "|", d.get("reason"))
    print("  regime_tags:", tags, "| candidates:", [c["id"] for c in cands])
    print("  plan:", json.dumps(d.get("plan"), ensure_ascii=False) if d.get("plan") else None)
