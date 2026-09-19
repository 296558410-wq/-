# -*- coding: utf-8 -*-
"""V2 回归 — P1-C Broker 订单预校验（发送前 fail-closed，杜绝 10016）。

断言（纯函数 broker_validate.precheck_order）:
- valid BUY / valid SELL → ok
- wrong side SL/TP → PRECHECK_REJECT
- too-close SL/TP (< stops_level) → reject
- SL/TP 落在市价错误一侧 → reject
- off-tick → reject
日志: logs/test_broker_validate.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
import broker_validate as BV  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_broker_validate.log"
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
    # valid SELL
    ok, c, det = BV.precheck_order("SHORT", 4300.0, 4317.0, 4273.0, market_bid=4299.8, market_ask=4300.0, stops_level=0.5)
    check("valid SELL ok", ok, f"{c}:{det}")
    # valid BUY
    ok, c, det = BV.precheck_order("LONG", 4300.0, 4283.0, 4327.0, market_bid=4299.8, market_ask=4300.0, stops_level=0.5)
    check("valid BUY ok", ok, f"{c}:{det}")

    # wrong side (SELL SL below entry)
    ok, c, det = BV.precheck_order("SHORT", 4300.0, 4283.0, 4327.0, market_bid=4299.8, market_ask=4300.0)
    check("SELL wrong side reject", (not ok) and c == "PRECHECK_REJECT", f"{det}")
    # wrong side (BUY TP below entry)
    ok, c, det = BV.precheck_order("LONG", 4300.0, 4283.0, 4270.0, market_bid=4299.8, market_ask=4300.0)
    check("BUY wrong TP reject", not ok, f"{det}")

    # SL at/below market for SELL (the historical 10016 scenario)
    ok, c, det = BV.precheck_order("SHORT", 4300.0, 4300.5, 4273.0, market_bid=4310.0, market_ask=4310.2)
    check("SELL SL below market reject", (not ok) and det.get("reason") == "short_sl_at_or_below_market", f"{det}")
    # TP at/above market for SELL (market collapsed below TP)
    ok, c, det = BV.precheck_order("SHORT", 4300.0, 4317.0, 4273.0, market_bid=4260.0, market_ask=4260.2)
    check("SELL TP at/above market reject", (not ok) and det.get("reason") == "short_tp_at_or_above_market", f"{det}")

    # too-close (stops_level)
    ok, c, det = BV.precheck_order("SHORT", 4300.0, 4300.3, 4273.0, market_bid=4299.8, market_ask=4300.0, stops_level=1.0)
    check("too-close SL reject", (not ok) and "stops_level" in det.get("reason", ""), f"{det}")

    # off-tick
    ok, c, det = BV.precheck_order("SHORT", 4300.005, 4317.0, 4273.0, market_bid=4299.8, market_ask=4300.0)
    check("off-tick reject", (not ok) and det.get("reason") == "entry_off_tick", f"{det}")

    # missing price
    ok, c, det = BV.precheck_order("SHORT", 4300.0, None, 4273.0)
    check("missing sl reject", (not ok) and det.get("reason") == "missing_price", f"{det}")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
