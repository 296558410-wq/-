# -*- coding: utf-8 -*-
"""V2 回归 — P0-04 Freshness(data_ts) + Health(gate)。

断言:
- freshness 基于 data_ts（age=now-data_ts），非 snapshot 生成时刻
- 未来时间戳 → unknown；缺失 → unknown
- build_health: PASS/DEGRADED/FAIL 聚合
- hermes.gate: health FAIL→REJECT, DEGRADED→WAIT, 缺失字段→向后兼容
日志: logs/test_freshness_health.log
"""
from __future__ import annotations
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "hermes"))
import context as CTX  # noqa: E402
import hermes as H  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_freshness_health.log"
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
    now = time.time()
    check("fresh (age 60s)", CTX._fresh_from_data_ts(now - 60, "agent1")[0] == "fresh")
    check("stale (age 2000s)", CTX._fresh_from_data_ts(now - 2000, "agent1")[0] == "stale")
    check("expired (age 5000s)", CTX._fresh_from_data_ts(now - 5000, "agent1")[0] == "expired")
    check("future ts -> unknown", CTX._fresh_from_data_ts(now + 100, "agent1")[0] == "unknown")
    check("missing ts -> unknown", CTX._fresh_from_data_ts(None, "agent1")[0] == "unknown")

    check("_to_epoch iso", CTX._to_epoch("2026-09-17T00:00:00+00:00") == 1789603200.0)
    check("_to_epoch secs", CTX._to_epoch(1789606800) == 1789606800.0)
    check("_to_epoch ms", CTX._to_epoch(1789606800000) == 1789606800.0)

    a1_ok = {"data_quality": {"gaps": [], "by_tf": {"15m": {"last_bar_ts": int(now - 60)}}}}
    a1_gap = {"data_quality": {"gaps": ["5m"], "by_tf": {"15m": {"last_bar_ts": int(now - 60)}}}}
    a2_ok = {"macro_status": "OK", "macro": {"usd": {"data_ts": int(now - 60)}}}
    a2_deg = {"macro_status": "DEGRADED", "macro": {"usd": {"data_ts": int(now - 60)}}}
    check("health PASS", CTX.build_health(a1_ok, a2_ok, "fresh", "fresh", True)["overall_status"] == "PASS")
    check("health DEGRADED (a1 gaps)", CTX.build_health(a1_gap, a2_ok, "fresh", "fresh", True)["overall_status"] == "DEGRADED")
    check("health DEGRADED (macro)", CTX.build_health(a1_ok, a2_deg, "fresh", "fresh", True)["overall_status"] == "DEGRADED")
    check("health FAIL (no a1)", CTX.build_health(None, a2_ok, "unknown", "fresh", True)["overall_status"] == "FAIL")
    check("health FAIL (freshness expired)", CTX.build_health(a1_ok, a2_ok, "expired", "fresh", True)["overall_status"] == "FAIL")

    ctx_fail = {"agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"}, "health": {"overall_status": "FAIL"}}
    ctx_deg = {"agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"}, "health": {"overall_status": "DEGRADED"}}
    ctx_pass = {"agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"}, "health": {"overall_status": "PASS"}}
    vF, rF = H.gate(None, ctx_fail, {})
    check("gate health FAIL -> REJECT", vF == "REJECT", f"{vF}:{rF}")
    vD, rD = H.gate(None, ctx_deg, {})
    check("gate health DEGRADED -> WAIT", vD == "WAIT", f"{vD}:{rD}")
    vP, rP = H.gate(None, ctx_pass, {})
    check("gate health PASS -> falls through", vP == "WAIT" and "未发现机会" in rP, f"{vP}:{rP}")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
