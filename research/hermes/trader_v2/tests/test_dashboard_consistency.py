# -*- coding: utf-8 -*-
"""V2 回归 — P1-D Dashboard 一致性（模式真实 + sizing 不硬编码 + 标签）。

断言:
- _sizing_rows base_equity 来自参数（账户），None 时显式 equity_base_missing（不伪造）
- datasource 暴露 mode_info（run_mode/execution_mode/broker/account_type/instrument/router/price_space）
- 代码无 base_equity=10000.0 硬编码；app.js 无 '虚拟账户'/'Paper 账户'/'Paper Equity'
日志: logs/test_dashboard_consistency.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "dashboard"))
import datasource as DS  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_dashboard_consistency.log"
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
    contract = {"contract_size_oz": 100, "lot_dp": 2, "min_lot": 0.01, "max_lot": 0.05}
    ev = [{"event_type": "DECISION", "status": "TRADE", "decision_id": "D1", "requested_price": 4300.0,
           "stop_loss": 4282.0, "take_profit": 4327.0, "decision_window": "w", "side": "LONG"}]
    r = DS._sizing_rows(ev, contract, 2.0, base_equity=1024.0)
    check("sizing uses account equity base", r[0]["equity_base"] == 1024.0, str(r[0]["equity_base"]))
    check("target_risk from base (1024*2%)", r[0]["target_risk"] == 20.48, str(r[0]["target_risk"]))
    check("floored lot 0.01", r[0]["floored_lot"] == 0.01, str(r[0]["floored_lot"]))
    r2 = DS._sizing_rows(ev, contract, 2.0, base_equity=None)
    check("no base -> equity_base_missing, no fake risk", r2[0]["equity_base_missing"] is True and r2[0]["target_risk"] is None)

    dsrc = (ROOT / "dashboard" / "datasource.py").read_text(encoding="utf-8")
    check("datasource exposes mode_info", '"mode_info"' in dsrc)
    check("no hardcoded base_equity=10000", "base_equity=10000.0" not in dsrc)
    check("account fallback not fake-zero", '"realized_pnl": None, "positions": [], "closed_trades": [], "fallback": True' in dsrc)

    app = (ROOT / "dashboard" / "static" / "app.js").read_text(encoding="utf-8")
    check("app.js no 虚拟账户", "虚拟账户" not in app)
    check("app.js no 'Paper 账户'", "Paper 账户" not in app)
    check("app.js no 'Paper Equity'", "Paper Equity" not in app)
    check("app.js uses mode_info", "mode_info" in app)

    import json
    cfg = json.loads((ROOT / "config" / "v2_config.json").read_text(encoding="utf-8"))
    check("dashboard/account instrument consistent XAUUSD",
          (cfg.get("instrument_marking") or {}).get("instrument") == "XAUUSD")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
