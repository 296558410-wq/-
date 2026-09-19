# -*- coding: utf-8 -*-
"""V2 Module 4 — 受控 PAPER-only 运行入口（每次一个决策; 不自动长跑）。

启动安全检查: execution_mode==PAPER 且 live_trading==False 且 broker.enabled==False 且 broker_demo_enabled==False，
否则 REFUSE_TO_START。默认读 state/hermes_decision_latest.json（或 --fixture）；只跑一轮。
用法: python hermes_paper_loop.py [--fixture path.json] [--close]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "ledger"))
import hermes_paper_adapter as ADP  # noqa: E402
import paper_executor as PE  # noqa: E402

DEC = ROOT / "state" / "hermes_decision_latest.json"
LEDGER = ROOT / "ledger" / "hermes_v2_ledger.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", default=None, help="Hermes decision JSON 文件; 缺省读 state/hermes_decision_latest.json")
    ap.add_argument("--close", action="store_true", help="开仓后立即平仓(测试用)")
    ap.add_argument("--mid", type=float, default=None)
    ap.add_argument("--ledger", default=None, help="覆盖账本路径(测试用)")
    a = ap.parse_args()
    try:
        ADP.assert_paper_only()
    except ADP.RefuseToStart as e:
        print(e); return 3
    src = Path(a.fixture) if a.fixture else DEC
    if not src.exists():
        print(f"NO_DECISION_FILE {src}"); return 2
    decision = json.loads(src.read_text(encoding="utf-8-sig"))
    ex = PE.PaperExecutor(ADP.load_config())
    out = ADP.process(decision, ex, Path(a.ledger) if a.ledger else LEDGER, market_mid=a.mid, close_after=a.close)
    print("PAPER loop (single cycle):", json.dumps(out, ensure_ascii=False))
    print("account:", json.dumps({k: ex.acc[k] for k in ("balance", "equity", "realized_pnl")}, ensure_ascii=False),
          "open", len(ex.acc["positions"]), "closed", len(ex.acc["closed_trades"]))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
