# -*- coding: utf-8 -*-
"""V2 标尺审计 — GC=F（信号价空间） vs XAUUSD spot（执行价空间）。

背景（事故 2026-09-16）：Hermes 计划用 GC=F 价位，执行在 XAUUSD spot 上；
       成交单（0.01 手）实际入场 4292.60，而计划入场 4305.52 → basis ≈ 12.92。
       后果：实际止损距离 30.14（设计 17.22）、实际止盈距离 14.63（设计 27.55）
             → 实际 R:R ≈ 0.49（设计 1.60）；实际风险 ≈ 账户 2.9%（目标 2%）。

本模块**只做审计/报告**，绝不修改策略（不改 entry/SL/TP/confidence/expected_R/sizing）。
用法: python tools/price_space_audit.py            # 写 research/PRICE_SPACE_AUDIT.md + ISSUE
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RUNS = ROOT / "research" / "runs"
CTX = ROOT / "state" / "decision_contexts"
OUT_MD = ROOT / "research" / "PRICE_SPACE_AUDIT.md"
ISSUE_MD = ROOT / "research" / "ISSUE_GC_SPOT_PRICE_SPACE_MISMATCH.md"
SIGNAL_SPACE = "GC_F (COMEX futures, Yahoo GC=F)"
EXEC_SYMBOL = "XAUUSD (spot, FXTM)"
CONTRACT_OZ = 100.0


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _reads(path):
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except Exception:  # noqa: BLE001
                pass
    return out


def _fills_by_decision(ledger_path):
    """decision_id -> (position_id, fill_price, side, volume)（取首笔成交）。"""
    res = {}
    for e in _reads(ledger_path):
        if e.get("event_type") in ("FILL", "POSITION_OPEN") and e.get("decision_id") and e.get("fill_price"):
            res.setdefault(e["decision_id"], {"position_id": e.get("position_id"),
                                              "fill_price": float(e["fill_price"]),
                                              "side": e.get("side"), "volume": e.get("volume")})
    return res


def _ctx_market(context_id):
    j = _load(CTX / f"{context_id}.json")
    if not j:
        return {}
    return j.get("market") or {}


def compute(planned_entry, planned_sl, planned_tp, execution_entry, volume=None):
    """纯函数：给定计划（信号价空间）与实际成交（执行价空间）→ 标尺审计衍生量。

    basis = planned_entry − execution_entry（带符号；动态，不可用常数修正）
    spot_equivalent_* = 计划价位 − basis（换算到执行价空间）
    planned_risk/reward = 计划价空间中的距离；actual_* = 成交价到【未换算】计划 SL/TP 的距离
    """
    out = {}
    if execution_entry is None:
        out["status"] = "NO_FILL(计划未成交/未执行)"
        return out
    basis = round(float(planned_entry) - float(execution_entry), 4)
    out["basis"] = basis
    out["spot_equivalent_entry"] = round(float(planned_entry) - basis, 4)
    out["spot_equivalent_sl"] = round(float(planned_sl) - basis, 4)
    out["spot_equivalent_tp"] = round(float(planned_tp) - basis, 4)
    out["planned_risk"] = round(abs(float(planned_entry) - float(planned_sl)), 4)
    out["actual_risk"] = round(abs(float(execution_entry) - float(planned_sl)), 4)
    out["planned_reward"] = round(abs(float(planned_entry) - float(planned_tp)), 4)
    out["actual_reward"] = round(abs(float(execution_entry) - float(planned_tp)), 4)
    out["planned_R"] = round(out["planned_reward"] / out["planned_risk"], 3) if out["planned_risk"] else None
    out["actual_R"] = round(out["actual_reward"] / out["actual_risk"], 3) if out["actual_risk"] else None
    if volume:
        out["actual_risk_usd"] = round(float(volume) * CONTRACT_OZ * out["actual_risk"], 2)
        out["planned_risk_usd"] = round(float(volume) * CONTRACT_OZ * out["planned_risk"], 2)
    out["price_space_conversion_in_code"] = False
    out["status"] = "MISMATCH" if abs(basis) > 0.5 else "OK"
    return out


def collect_trades():
    """返回所有 run 的 TRADE 决策审计行（信号价空间 vs 执行价空间）。"""
    rows = []
    for rd in sorted(RUNS.glob("*")):
        if not rd.is_dir():
            continue
        decdir = rd / "decisions"
        if not decdir.exists():
            continue
        fills = _fills_by_decision(rd / "ledger.jsonl")
        for f in sorted(decdir.glob("*.raw.json")):
            d = _load(f)
            if not isinstance(d, dict) or d.get("decision") != "TRADE":
                continue
            plan = d.get("plan") or {}
            pe, psl, ptp = plan.get("entry"), plan.get("stop_loss"), plan.get("take_profit")
            if pe is None or psl is None or ptp is None:
                continue
            did = d.get("decision_id") or f.name.split(".")[0]
            fl = fills.get(did, {})
            ex_entry = fl.get("fill_price")
            mkt = _ctx_market(d.get("context_id") or "")
            basis_ctx = mkt.get("basis_usd")
            row = {
                "run_id": rd.name, "decision_id": did, "timestamp": d.get("ts"),
                "instrument_signal": SIGNAL_SPACE, "execution_symbol": EXEC_SYMBOL,
                "side": (plan.get("direction") or "").upper(),
                "planned_entry": pe, "planned_sl": psl, "planned_tp": ptp,
                "execution_entry": ex_entry, "position_id": fl.get("position_id"),
                "volume": fl.get("volume"),
                "ctx_primary_last": mkt.get("primary_last"), "ctx_basis_usd": basis_ctx,
            }
            row.update(compute(pe, psl, ptp, ex_entry, fl.get("volume")))
            rows.append(row)
    return rows


def audit_and_write():
    rows = collect_trades()
    filled = [r for r in rows if r.get("execution_entry") is not None]
    mism = [r for r in filled if r.get("status") == "MISMATCH"]
    systematic = bool(filled) and len(mism) == len(filled)
    lines = ["# PRICE_SPACE_AUDIT — GC=F(信号) vs XAUUSD spot(执行)\n",
             f"- 生成: {datetime.now(timezone.utc).isoformat()}",
             f"- 信号价空间: {SIGNAL_SPACE}", f"- 执行标的: {EXEC_SYMBOL}",
             f"- TRADE 决策总数: {len(rows)}；已成交: {len(filled)}；判为 MISMATCH: {len(mism)}",
             f"- **结论: {'系统性 instrument mismatch（设计层面）' if systematic else '无系统性偏差'}**\n",
             "## 审计表\n"]
    hdr = ["decision_id", "timestamp", "instrument_signal", "execution_symbol", "side",
           "planned_entry", "planned_sl", "planned_tp", "execution_entry", "basis",
           "spot_equivalent_entry", "spot_equivalent_sl", "spot_equivalent_tp",
           "planned_risk", "actual_risk", "planned_reward", "actual_reward",
           "planned_R", "actual_R"]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "-")) for k in hdr) + " |")
    lines.append("\n## 附：上下文 basis（同轮 Agent1 记录）\n")
    lines.append("| decision_id | ctx_primary_last(GC) | ctx_basis_usd | execution_entry | observed_basis |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['decision_id']} | {r.get('ctx_primary_last','-')} | {r.get('ctx_basis_usd','-')} | "
                     f"{r.get('execution_entry','-')} | {r.get('basis','-')} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, filled, mism, systematic


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rows, filled, mism, systematic = audit_and_write()
    print(f"TRADE={len(rows)} filled={len(filled)} mismatch={len(mism)} systematic={systematic}")
    for r in rows:
        print(json.dumps({k: r.get(k) for k in ("decision_id", "planned_entry", "execution_entry",
                                                "basis", "planned_R", "actual_R")}, ensure_ascii=False))
    print("wrote:", OUT_MD)
