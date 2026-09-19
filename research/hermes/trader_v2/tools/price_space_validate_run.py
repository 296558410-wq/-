# -*- coding: utf-8 -*-
"""V2 前向验证器 — 价格空间链路（**只读**）: plan(GC) -> execution(XAUUSD) -> 实际成交 -> 实际 R/R & risk。

直接读 run 账本里 Hermes/执行层写入的 signal_* / execution_* / basis / fill，逐笔核对：
  - signal_entry/sl/tp (GC 空间，Hermes 原计划)
  - execution_entry/sl/tp (XAUUSD 空间，本层换算)
  - basis / basis_age / basis_source / source_hash (PIT 溯源)
  - 实际 fill 与 execution SL/TP 的 距离 / R:R / 风险%  → 与 signal 计划对比
  - 是否正确一侧 / 是否 10016 / 是否 price-space fail-closed

用法:
  python tools/price_space_validate_run.py                 # 当前 ACTIVE run
  python tools/price_space_validate_run.py --run <run_id>
  python tools/price_space_validate_run.py --all           # 所有 run（legacy run 无 execution_* 则按 signal 对照）
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RUNS = ROOT / "research" / "runs"
ACTIVE = ROOT / "state" / "runs" / "ACTIVE.json"
CONTRACT_OZ = 100.0
RISK_TARGET_PCT = 2.0


def _load(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def _reads(p):
    p = Path(p)
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


def _active_run():
    return (_load(ACTIVE, {}) or {}).get("run_id")


def validate(run_id):
    led = RUNS / run_id / "ledger.jsonl"
    evs = _reads(led)
    decs = {e.get("decision_id"): e for e in evs if e.get("event_type") == "DECISION"}
    fills = {}
    rej = {}
    for e in evs:
        if e.get("event_type") in ("FILL", "POSITION_OPEN") and e.get("decision_id") and e.get("fill_price"):
            fills.setdefault(e["decision_id"], e["fill_price"])
        if e.get("event_type") in ("EXECUTION_RESPONSE", "ORDER_REJECTED") and e.get("status") == "REJECTED":
            rej.setdefault(e.get("decision_id"), e.get("retcode"))
    trades = [e for e in evs if e.get("event_type") == "DECISION" and e.get("status") == "TRADE"]
    print(f"\n=== run {run_id} : TRADE={len(trades)} ===")
    if not trades:
        print("  (尚无 TRADE 决策)")
        return
    hdr = ("decision_id", "side", "sig_entry", "exec_entry", "basis", "age", "src",
           "exec_sl", "exec_tp", "fill", "risk$", "risk%", "realR", "planR", "note")
    print("  " + " | ".join(hdr))
    for d in trades:
        did = d.get("decision_id")
        side = d.get("side")
        se, ssl, stp = d.get("signal_entry"), d.get("signal_stop_loss"), d.get("signal_take_profit")
        ee, esl, etp = d.get("execution_entry"), d.get("execution_stop_loss"), d.get("execution_take_profit")
        fill = fills.get(did)
        note = []
        if ee is None:  # legacy run (无换算记录)
            ee, esl, etp = se, ssl, stp
            note.append("NO_CONVERSION(legacy)")
        # 计划 R
        planR = None
        if se is not None and ssl is not None and stp is not None and abs(se - ssl) > 0:
            planR = round(abs(se - stp) / abs(se - ssl), 2)
        risk_usd = risk_pct = realR = None
        if fill is not None and esl is not None:
            rd = abs(fill - esl)
            risk_usd = round(rd * CONTRACT_OZ * 0.01, 2)  # 0.01 手
            realR = round(abs(fill - etp) / rd, 2) if rd else None
            eq = (d.get("account_equity") or 1024.0)
            risk_pct = round(risk_usd / eq * 100.0, 2)
        if rej.get(did):
            note.append(f"REJ:{rej[did]}")
        if rej.get(did) == "BROKER_REJECT_10016":
            note.append("INVALID_STOPS")
        if ee is not None and fill is not None and abs(fill - ee) > 1.0:
            note.append("FILL!=EXEC_ENTRY")
        print("  " + " | ".join(str(x) for x in (
            did, side, se, ee, d.get("basis"), d.get("basis_age"),
            (str(d.get("basis_source"))[:18] if d.get("basis_source") else None),
            esl, etp, fill, risk_usd, risk_pct, realR, planR, ",".join(note) or "ok")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.all:
        for rd in sorted(RUNS.glob("*")):
            if rd.is_dir() and (rd / "ledger.jsonl").exists():
                validate(rd.name)
    else:
        rid = a.run or _active_run()
        if not rid:
            print("no active run"); return 2
        validate(rid)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
