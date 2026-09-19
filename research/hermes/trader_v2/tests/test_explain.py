# -*- coding: utf-8 -*-
"""V2 explain taxonomy — 测试（离线；不触 broker；不改策略）。
校验 gate() 既有 reason 字符串能被归类为 §6 要求的机器可读类别。
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import explain as EX  # noqa: E402

OUT = []; N = {"p": 0, "f": 0}


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    N["p" if cond else "f"] += 1
    ln = f"{tag} | {name} {detail}"; OUT.append(ln); print(ln)


CASES = [
    ("证据通过门禁", "TRADE", "TRADE_OK"),
    ("数据不新鲜(a1=expired, a2=ok) → 等刷新", "WAIT", "DATA_STALE"),
    ("data health DEGRADED → 等恢复", "WAIT", "DATA_DEGRADED"),
    ("data health FAIL → 不交易", "REJECT", "DATA_FAIL"),
    ("宏观核心数据不可用(macro_status=DEGRADED) → 等数据恢复", "WAIT", "MACRO_UNAVAILABLE"),
    ("未发现机会", "WAIT", "NO_OPPORTUNITY"),
    ("机会方向未定(如背离类) → 等价格选择方向", "WAIT", "DIRECTION_UNDECIDED"),
    ("技术(LONG) 与宏观(BEARISH) 冲突 → 证据冲突, 等确认", "WAIT", "TECH_MACRO_CONFLICT"),
    ("机会可能已被定价(price already extended) → 等回撤/确认", "WAIT", "PRICED_IN"),
    ("该机会需市场确认(follow-through 未验) → 先观察", "WAIT", "NO_FOLLOW_THROUGH"),
    ("风险回报不足/追高(LONG 但处区间高位 pos=91)", "REJECT", "EXTREME_POSITION"),
    ("风险回报不足/追空(SHORT 但处区间低位 pos=8)", "REJECT", "EXTREME_POSITION"),
    ("风险回报不足 expected_R=0.3 < 1.0", "REJECT", "RISK_REWARD"),
    ("缺少反证(counter_thesis)", "REJECT", "COUNTER_THESIS"),
    ("某个未知新 gate 文案", "WAIT", "OTHER_GATE"),
]
for reason, dec, want in CASES:
    got = EX.classify({"decision": dec, "reason": reason})["code"]
    check(f"{want} <= {reason[:34]}", got == want, f"got={got}")
check("TAXONOMY complete (§6 11类)", set(EX.CATEGORIES) >= {"DATA_STALE", "DATA_DEGRADED", "MACRO_UNAVAILABLE",
      "NO_OPPORTUNITY", "TECH_MACRO_CONFLICT", "PRICED_IN", "NO_FOLLOW_THROUGH", "EXTREME_POSITION",
      "RISK_REWARD", "COUNTER_THESIS", "OTHER_GATE"})
check("decision_hash stable", EX.decision_hash({"a": 1, "decision_id": "x"}) == EX.decision_hash({"a": 1, "decision_id": "y"}))

tot = N["p"] + N["f"]
print(f"\n=== RESULT: {N['p']}/{tot} PASS ===")
sys.exit(1 if N["f"] else 0)
