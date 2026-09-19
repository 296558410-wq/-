# -*- coding: utf-8 -*-
"""V1 审计 PHASE C — 信息可见性边界 + 分析资格矩阵 + 交易重建状态（只读；不做 Alpha）。

产出:
  V1_TRADE_RECONSTRUCTION_STATUS.json
  V1_INFORMATION_BOUNDARY.json
  V1_ANALYSIS_ELIGIBILITY.json
  V1_AUDIT_PHASE_C_SHA256.json
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

V1 = Path(r"C:\AIQuant\research\hermes\trader_v1")
AUDIT = Path(r"C:\AIQuant\research\hermes\v1_audit")
NOW = datetime.now(timezone.utc).isoformat()


def sha(p):
    try:
        h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
    except Exception:  # noqa: BLE001
        return None


def load_jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    replay = {r["trade_id"]: r for r in load_jsonl(AUDIT / "V1_TRADE_REPLAY.jsonl")}
    # T_order from positions ENTER events
    recon = []
    for f in (V1 / "run_state" / "positions").glob("POS-*.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        pid = p.get("position_id")
        ev = {e.get("event"): e.get("ts") for e in p.get("events", [])}
        recon.append((pid, ev.get("ENTER"), ev.get("FILL"), ev.get("EXIT_FILL"), ev.get("EXIT_REQUEST")))
    pos = {x[0]: x for x in recon}

    rec_status = []
    elig = []
    for tid, r in replay.items():
        po = pos.get(tid)
        t_sig = r.get("t_signal"); t_fill = r.get("t_fill"); t_exit = r.get("t_exit")
        t_order = po[1] if po else None
        src = "positions.ENTER" if t_order else ("plan_id_parse(PARTIAL)" if t_sig else None)
        conf = "HIGH" if t_order else ("LOW" if t_sig else "NONE")
        if t_order and t_fill and t_order > t_fill:
            conf = "MEDIUM(order>fill, 时钟异常)"
        rec_status.append({"trade_id": tid, "plan_id": r.get("plan_id"), "T_signal": t_sig, "T_order": t_order,
                           "T_fill": t_fill, "T_exit": t_exit,
                           "reconstruction_source": src, "confidence": conf,
                           "T_order_status": "RECOVERED" if t_order else "DATA_GAP"})
        cpre = (r.get("coverage_before_signal") or {}).get("covered")
        csf = (r.get("coverage_signal_to_fill") or {}).get("covered")
        cfe = (r.get("coverage_fill_to_exit") or {}).get("covered")
        # 资格
        if t_exit is None:
            out = "UNRESOLVABLE"
        elif cfe:
            out = "ELIGIBLE"
        elif csf:
            out = "PARTIAL"
        else:
            out = "DATA_GAP"
        entry = "PARTIAL" if (cpre and csf) else ("DATA_GAP" if not cpre else "PARTIAL")
        # 完整输入快照缺失 → 永不 ELIGIBLE
        entry = "DATA_GAP" if entry == "ELIGIBLE" else entry
        cost = "PARTIAL" if (cfe or csf) else "DATA_GAP"   # spread 可推导/slippage 已记录；commission/swap DATA_GAP
        cf = "ELIGIBLE" if (cpre and csf and cfe) else ("PARTIAL" if (csf or cfe) else "DATA_GAP")
        # 集合
        if entry == "ELIGIBLE" and out == "ELIGIBLE":
            grp = "A_FULLY_RECONSTRUCTABLE"
        elif out == "ELIGIBLE":
            grp = "B_OUTCOME_RECONSTRUCTABLE"
        else:
            grp = "C_DATA_GAP_UNRESOLVABLE"
        elig.append({"trade_id": tid, "ENTRY_RECONSTRUCTION": entry, "OUTCOME_RECONSTRUCTION": out,
                     "COST_RECONSTRUCTION": cost, "COUNTERFACTUAL_ELIGIBILITY": cf, "set": grp,
                     "status_phaseB": r.get("status")})

    (AUDIT / "V1_TRADE_RECONSTRUCTION_STATUS.json").write_text(
        json.dumps({"schema": "v1_trade_reconstruction/1", "ts_utc": NOW,
                    "T_order_rule": "positions.ENTER ts；缺失→DATA_GAP（不得用 T_fill 永久替代）",
                    "trades": rec_status}, ensure_ascii=False, indent=1), encoding="utf-8")
    (AUDIT / "V1_ANALYSIS_ELIGIBILITY.json").write_text(
        json.dumps({"schema": "v1_analysis_eligibility/1", "ts_utc": NOW,
                    "dims": ["ENTRY_RECONSTRUCTION", "OUTCOME_RECONSTRUCTION", "COST_RECONSTRUCTION",
                             "COUNTERFACTUAL_ELIGIBILITY"],
                    "rules": {"ENTRY": "决策 JSON 仅 state_summary，无完整输入快照 → 最高只能 PARTIAL，永不 ELIGIBLE",
                              "OUTCOME": "fill→exit 有 tick 覆盖→ELIGIBLE；否则 PARTIAL/DATA_GAP；未平仓→UNRESOLVABLE",
                              "COST": "spread 可由源A推、slippage 已记录；commission/swap 未记录→DATA_GAP ⇒ 最高 PARTIAL",
                              "COUNTERFACTUAL": "signal→horizon 有 tick 覆盖→ELIGIBLE"},
                    "trades": elig}, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    sets = Counter(e["set"] for e in elig)
    entryc = Counter(e["ENTRY_RECONSTRUCTION"] for e in elig)
    outc = Counter(e["OUTCOME_RECONSTRUCTION"] for e in elig)
    boundary = {"schema": "v1_information_boundary/1", "ts_utc": NOW,
                "classes": {
                    "A_visible_and_saved_before_signal": {"desc": "T_signal 前实际保存且可确认存在的信息",
                                                          "examples": ["live_fxtm tick(源A, T_signal 前)", "plan_ledger 该 plan 的 registered 事件"],
                                                          "allowed_for": ["ENTRY_DECISION_ANALYSIS"], "status": "部分存在(逐笔覆盖见矩阵)"},
                    "B_decision_state_summary": {"desc": "decisions/*.json 的 state_summary(文本摘要)",
                                                 "allowed_for": ["描述 V1 记录了哪些字段"], "not_equal_to": "完整可见输入",
                                                 "status": "存在(摘要)"},
                    "C_latest_state_package_only": {"desc": "仅 latest state_package 可见的信息",
                                                    "allowed_for": [], "forbidden_for": ["ENTRY_DECISION_ANALYSIS", "历史解释"],
                                                    "status": "禁止用于历史"},
                    "D_post_signal_observable": {"desc": "T_signal 之后才能观察到的信息（价格/spread/新闻/宏观/结果）",
                                                 "allowed_for": ["POST_ENTRY_OUTCOME_ANALYSIS"], "forbidden_for": ["ENTRY_DECISION_ANALYSIS"]}},
                "hard_rule": "只有 A 可作为『V1 当时实际可见输入』的证据；C 禁止用于历史决策解释；D 只用于 outcome 分析。",
                "unprovable_statement": "无法从历史保存数据证明『V1 在 T_signal 时完整看到了哪些原始市场输入』。",
                "costs": {"spread_at_entry_recorded": False, "slippage_recorded": True,
                          "commission_recorded": False, "swap_recorded": False,
                          "note": "spread/slippage 可部分重建(源A+review)；commission/swap=DATA_GAP，禁默认0"}}
    (AUDIT / "V1_INFORMATION_BOUNDARY.json").write_text(json.dumps(boundary, ensure_ascii=False, indent=1), encoding="utf-8")

    files = ["V1_TRADE_RECONSTRUCTION_STATUS.json", "V1_INFORMATION_BOUNDARY.json", "V1_ANALYSIS_ELIGIBILITY.json",
             "tools/v1_audit_phaseC.py"]
    reg = {"ts_utc": NOW, "sha256": {f: sha(AUDIT / f) for f in files}}
    (AUDIT / "V1_AUDIT_PHASE_C_SHA256.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"n": len(elig), "sets": dict(sets), "entry": dict(entryc), "outcome": dict(outc),
                      "T_order_recovered": sum(1 for x in rec_status if x["T_order_status"] == "RECOVERED")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
