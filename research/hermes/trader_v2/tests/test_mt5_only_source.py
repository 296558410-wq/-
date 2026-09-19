# -*- coding: utf-8 -*-
"""V2 回归 — P0-06 MT5-only 交易行情源守卫。

断言:
- 交易行情（技术 K 线 history + XAUUSD 现货 gold_spot）非 mt5 → technical/overall DEGRADED
- 两者均 mt5 → PASS
- 缺失源字段（合成 fixture）→ 向后兼容，不触发
- hermes.gate: 该 DEGRADED → WAIT（不产生 TRADE）
日志: logs/test_mt5_only_source.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "hermes"))
import context as CTX  # noqa: E402
import hermes as H  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_mt5_only_source.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def _a1(hist, spot, gaps=None):
    return {"data_quality": {"gaps": gaps or [], "sources": {"history": hist, "quotes": [spot]}},
            "quotes": {"gold_spot": {"source": spot, "price": 4345.0}},
            "price_basis": {"primary_source": hist}}


def main():
    a2_ok = {"macro_status": "OK"}

    check("mt5+mt5 -> PASS", CTX.build_health(_a1("mt5", "mt5"), a2_ok, "fresh", "fresh", True)["overall_status"] == "PASS")
    h_fb = CTX.build_health(_a1("local_fxtm", "sina"), a2_ok, "fresh", "fresh", True)
    check("local_fxtm+sina -> DEGRADED", h_fb["overall_status"] == "DEGRADED", str(h_fb))
    check("local_fxtm+sina -> technical DEGRADED", h_fb["technical_status"] == "DEGRADED")
    check("local_fxtm+sina -> trading_source DEGRADED", h_fb["trading_source_status"] == "DEGRADED")
    check("history only fallback -> DEGRADED", CTX.build_health(_a1("local_fxtm", "mt5"), a2_ok, "fresh", "fresh", True)["overall_status"] == "DEGRADED")
    check("spot only fallback -> DEGRADED", CTX.build_health(_a1("mt5", "sina"), a2_ok, "fresh", "fresh", True)["overall_status"] == "DEGRADED")
    check("cache(mt5) history -> DEGRADED", CTX.build_health(_a1("cache(mt5)", "mt5"), a2_ok, "fresh", "fresh", True)["overall_status"] == "DEGRADED")

    # 向后兼容: 无源字段（合成 fixture）不触发
    a1_nosrc = {"data_quality": {"gaps": []}}
    check("missing source fields -> PASS (back-compat)",
          CTX.build_health(a1_nosrc, a2_ok, "fresh", "fresh", True)["overall_status"] == "PASS")

    # gate: DEGRADED -> WAIT
    ctx_deg = {"agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"},
               "health": {"overall_status": "DEGRADED"}}
    v, r = H.gate(None, ctx_deg, {})
    check("gate fallback-DEGRADED -> WAIT", v == "WAIT", f"{v}:{r}")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
