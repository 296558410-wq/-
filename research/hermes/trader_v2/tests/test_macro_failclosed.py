# -*- coding: utf-8 -*-
"""V2 回归 — P0-03 宏观 fail-closed + P1-01 conflicts 反降级。

断言:
- core_macro_status: OK / SOURCE_ERROR / DATA_MISSING 三态
- macro_state: core_degraded → DEGRADED(不是 NEUTRAL)；conflicts 禁止方向升级
- hermes.gate: macro_status != OK → WAIT（数据质量门 fail-closed）
日志: logs/test_macro_failclosed.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
sys.path.insert(0, str(ROOT / "hermes"))
import agent2 as A2  # noqa: E402
import hermes as H  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_macro_failclosed.log"
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
    # ---- core_macro_status ----
    check("core OK", A2.core_macro_status({"last": 100.0, "change_pct": 0.5}) == "OK")
    check("core SOURCE_ERROR", A2.core_macro_status({"__failed__": True}) == "SOURCE_ERROR")
    check("core SOURCE_ERROR(None)", A2.core_macro_status(None) == "SOURCE_ERROR")
    check("core DATA_MISSING", A2.core_macro_status({"last": None, "change_pct": None}) == "DATA_MISSING")

    # ---- macro_state ----
    check("degraded -> DEGRADED (not NEUTRAL)", A2.macro_state(True, 0.9, []) == ("DEGRADED", "DEGRADED"))
    check("strong+no-conflict -> BULLISH", A2.macro_state(False, 0.7, []) == ("OK", "BULLISH"))
    check("strong+CONFLICT -> NOT upgraded (P1-01)", A2.macro_state(False, 0.7, ["c"]) == ("OK", "NEUTRAL"),
          str(A2.macro_state(False, 0.7, ["c"])))
    check("strong->BEARISH", A2.macro_state(False, -0.7, []) == ("OK", "BEARISH"))
    check("strong BEARISH+conflict -> NEUTRAL", A2.macro_state(False, -0.7, ["c"]) == ("OK", "NEUTRAL"))
    check("small+conflict -> UNCERTAIN", A2.macro_state(False, 0.0, ["c"]) == ("OK", "UNCERTAIN"))
    check("small no-conflict -> NEUTRAL", A2.macro_state(False, 0.0, []) == ("OK", "NEUTRAL"))

    # ---- hermes.gate: macro degrade → WAIT ----
    ctx = {"agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"}}
    v, r = H.gate(None, ctx, {"macro_status": "DEGRADED"})
    check("gate DEGRADED -> WAIT", v == "WAIT" and "macro_status" in r, f"{v}:{r}")
    v2, r2 = H.gate(None, ctx, {"macro_status": "OK"})
    check("gate OK -> falls through to 未发现机会", v2 == "WAIT" and "未发现机会" in r2, f"{v2}:{r2}")
    v3, r3 = H.gate(None, ctx, {})  # 旧快照无该字段 → 向后兼容
    check("gate legacy(no macro_status) -> 未发现机会", v3 == "WAIT" and "未发现机会" in r3, f"{v3}:{r3}")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
