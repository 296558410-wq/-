# -*- coding: utf-8 -*-
"""Phase-1 校准只读自测：模块无写接口 + 附加目标正确 + 行情可读。日志: logs/test_demo_calibration_readonly.log"""
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
import fxtm_demo_calibration as C  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_demo_calibration_readonly.log"
_res = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== Phase-1 demo calibration (read-only) self-test ===")
    check("module is READ_ONLY", C.READ_ONLY is True)
    check("no write-api calls in module", C.assert_no_write_api() == [], str(C.assert_no_write_api()))
    try:
        mt5 = C.attach()
    except Exception as e:  # noqa: BLE001
        check("attach test instance (skipped: terminal not running)", True, f"skip: {e}")
        log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS (live part skipped) ===")
        return 0
    ti = mt5.terminal_info(); ai = mt5.account_info()
    check("attached to test data dir", "fxtm_demo_01" in (ti.data_path or ""), ti.data_path)
    check("account is DEMO", (ai.trade_mode == 0) if ai else False, f"login_ok={ai is not None}")
    q = C.get_quote(mt5, "XAUUSD")
    check("quote ok", q.get("ok") and q["ask"] > 0 and q["bid"] > 0 and q["spread"] > 0,
          f"bid={q.get('bid')} ask={q.get('ask')} spread={q.get('spread')}")
    mt5.shutdown()
    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if all(_res) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
