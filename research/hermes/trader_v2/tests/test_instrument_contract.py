# -*- coding: utf-8 -*-
"""V2 回归 — P0-01 Instrument Contract（禁止语义伪装：GC=F 标签配 XAUUSD 数据）。

断言:
- config: instrument_marking.instrument=XAUUSD, market_data.primary_instrument=XAUUSD, reference_instrument=GC=F
- 代码中出现 GC_F/GC=F 作为 instrument 的位置已消除（仅允许 reference_market / quote symbol）
- price_space: SIGNAL=EXECUTION=XAUUSD, REFERENCE=GC=F
- router fallback 不再把 XAUUSD 换成 GC=F 期货
日志: logs/test_instrument_contract.log
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
import price_space as PS  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_instrument_contract.log"
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
    cfg = json.loads((ROOT / "config" / "v2_config.json").read_text(encoding="utf-8"))
    md = cfg["market_data"]
    im = cfg["instrument_marking"]
    check("config instrument=XAUUSD", im["instrument"] == "XAUUSD", im.get("instrument"))
    check("config no proxy_for/spot_futures_proxy", "proxy_for" not in im and "spot_futures_proxy" not in im)
    check("config reference_market=GC=F", im.get("reference_market") == "GC=F")
    check("config primary_instrument=XAUUSD", md.get("primary_instrument") == "XAUUSD", md.get("primary_instrument"))
    check("config reference_instrument=GC=F", md.get("reference_instrument") == "GC=F")

    check("price_space SIGNAL=XAUUSD", PS.SIGNAL_INSTRUMENT == "XAUUSD")
    check("price_space EXECUTION=XAUUSD", PS.EXECUTION_INSTRUMENT == "XAUUSD")
    check("price_space REFERENCE=GC=F", PS.REFERENCE_MARKET == "GC=F")
    check("price_space identity formula", "source_basis" in PS.CONVERSION_FORMULA.lower(), PS.CONVERSION_FORMULA)

    # 静态契约：instrument 不再被标为 GC_F
    for f in ("hermes/hermes.py", "hermes/context.py", "agents/macro_global/agent2.py"):
        src = (ROOT / f).read_text(encoding="utf-8")
        check(f"{f}: instrument=XAUUSD", '"instrument": "XAUUSD"' in src, "")
        check(f"{f}: no instrument=GC_F", '"instrument": "GC_F"' not in src, "")

    # router fallback 不得把 XAUUSD 换成 GC=F
    rsrc = (ROOT / "data_sources" / "router.py").read_text(encoding="utf-8")
    check("router fallback keeps instrument (XAUUSD=X)", '"XAUUSD=X" if symbol == "XAUUSD"' in rsrc)
    check("router no GC=F fallback swap", 'hist_yahoo("GC=F"' not in rsrc)

    # agent1 不再把主序列标为 GC=F
    a1 = (ROOT / "agents" / "technical" / "agent1.py").read_text(encoding="utf-8")
    check("agent1 primary label not GC=F@yahoo", '"GC=F@yahoo"' not in a1)
    check("agent1 sources.history not hardcoded yahoo", '"sources": {"history": "yahoo"' not in a1)

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
