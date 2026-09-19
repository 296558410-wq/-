# -*- coding: utf-8 -*-
"""V2 回归测试 — GC=F / XAUUSD spot 标尺审计（离线；只读；不改策略）。

断言：
  1) 标尺数学正确（basis / spot-equivalent / planned_R vs actual_R / 风险美元）
  2) 历史数据上确实存在系统性价空间错配（100% 成交命中）→ 支撑 ISSUE CONFIRMED
  3) 产物存在（PRICE_SPACE_AUDIT.md + ISSUE 文档）

日志: logs/test_price_space_audit.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import price_space_audit as PSA  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_price_space_audit.log"
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
    # ---- 1) 数学 ----
    r = PSA.compute(4305.52, 4322.74, 4277.97, 4292.60, volume=0.01)
    check("basis = planned − exec", r["basis"] == 12.92, str(r["basis"]))
    check("spot_equivalent_entry == execution_entry", r["spot_equivalent_entry"] == 4292.6,
          str(r["spot_equivalent_entry"]))
    check("spot_equivalent_sl 换算正确", r["spot_equivalent_sl"] == 4309.82, str(r["spot_equivalent_sl"]))
    check("spot_equivalent_tp 换算正确", r["spot_equivalent_tp"] == 4265.05, str(r["spot_equivalent_tp"]))
    check("planned_risk 17.22 / actual_risk 30.14",
          (r["planned_risk"], r["actual_risk"]) == (17.22, 30.14), f"{r['planned_risk']}/{r['actual_risk']}")
    check("planned_R 1.6 / actual_R 0.485",
          (r["planned_R"], r["actual_R"]) == (1.6, 0.485), f"{r['planned_R']}/{r['actual_R']}")
    check("实际风险美元放大(>设计)", r["actual_risk_usd"] > r["planned_risk_usd"],
          f"{r['planned_risk_usd']} -> {r['actual_risk_usd']}")
    check("判为 MISMATCH", r["status"] == "MISMATCH", r["status"])
    check("无价空间换算（设计缺口）", r["price_space_conversion_in_code"] is False)

    # ---- 2) 历史系统性 ----
    rows, filled, mism, systematic = PSA.audit_and_write()
    check("存在历史 TRADE 记录", len(rows) >= 1, f"n={len(rows)}")
    check("已成交记录存在", len(filled) >= 1, f"n={len(filled)}")
    check("成交 100% 命中 MISMATCH（系统性）", systematic and len(mism) == len(filled),
          f"mismatch={len(mism)}/{len(filled)}")
    for x in filled:
        check(f"  {x['decision_id']}: actual_R != planned_R",
              x.get("actual_R") is not None and x["actual_R"] != x["planned_R"],
              f"plan_R={x['planned_R']} actual_R={x['actual_R']} basis={x['basis']}")

    # ---- 3) 产物 ----
    check("PRICE_SPACE_AUDIT.md 已生成", PSA.OUT_MD.exists(), str(PSA.OUT_MD))
    check("ISSUE 文档存在", PSA.ISSUE_MD.exists(), str(PSA.ISSUE_MD))

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
