# -*- coding: utf-8 -*-
"""V2 回归 — P1-A Macro PIT 完整性。

断言:
- macro_field_status: AVAILABLE/MISSING/ERROR
- news_source_status: OK / NEWS_SOURCE_ERROR / EMPTY（失败不静默为空）
- macro_completeness 输出显式标签
- agent2 输出含 macro_completeness / macro_pit_risk / news_status / cot.pit_status / etf.asof
- TRADE_CRITICAL_MACRO 界定
日志: logs/test_macro_pit.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
import agent2 as A2  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_macro_pit.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    check("field AVAILABLE", A2.macro_field_status({"last": 1.0}) == "AVAILABLE")
    check("field MISSING", A2.macro_field_status(None) == "MISSING")
    check("field ERROR", A2.macro_field_status({"__failed__": True}) == "ERROR")

    check("news OK", A2.news_source_status([{"x": 1}])["source_status"] == "OK")
    check("news ERROR", A2.news_source_status(None, "TimeoutError:x")["source_status"] == "NEWS_SOURCE_ERROR")
    check("news EMPTY", A2.news_source_status([])["source_status"] == "EMPTY")

    check("completeness passthrough", A2.macro_completeness({"DXY": "AVAILABLE"}) == {"DXY": "AVAILABLE"})
    check("TRADE_CRITICAL set", A2.TRADE_CRITICAL_MACRO == ("DXY", "UST10Y", "VIX"))
    check("CONTEXT_ONLY set", "COT" in A2.CONTEXT_ONLY_MACRO and "COT" not in A2.TRADE_CRITICAL_MACRO)

    src = (ROOT / "agents" / "macro_global" / "agent2.py").read_text(encoding="utf-8")
    for token in ('"macro_completeness": completeness', '"macro_pit_risk": macro_pit_risk',
                  '"news_status": news_status', '"pit_status"', '"asof"', '"publication_ts"'):
        check(f"agent2 emits {token}", token in src)

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
