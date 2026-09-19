# -*- coding: utf-8 -*-
"""V2 decision reason taxonomy + hashes (G3 observability).

**只读/旁路**: 不改变任何决策、评分、门禁。仅把 frozen 决策的 reason 归类为机器可读 code，
供 ledger/timeline/dashboard 区分显示；并计算 decision_hash / input_hash 便于对账。

分类来源 = hermes.hermes.gate() 的既有字符串（策略冻结，未改动）。
"""
from __future__ import annotations
import hashlib
import json

# §6 要求的 WAIT/REJECT 可解释类别
CATEGORIES = {
    "TRADE_OK": "证据通过门禁",
    "DATA_STALE": "数据不足/过期",
    "DATA_DEGRADED": "数据降级",
    "DATA_FAIL": "数据不可用(health FAIL)",
    "MACRO_UNAVAILABLE": "宏观数据不足/降级",
    "NO_OPPORTUNITY": "技术条件不足(未发现机会)",
    "DIRECTION_UNDECIDED": "方向未定(等价格选方向)",
    "TECH_MACRO_CONFLICT": "技术/宏观冲突",
    "PRICED_IN": "已 priced-in",
    "NO_FOLLOW_THROUGH": "缺乏 follow-through",
    "EXTREME_POSITION": "极端仓位过滤",
    "RISK_REWARD": "风险收益不足",
    "COUNTER_THESIS": "对手论点缺失(反证不足)",
    "OTHER_GATE": "其他明确 gate",
}


def _rules():
    # (code, 匹配子串) — 顺序敏感
    return [
        ("TRADE_OK", "证据通过门禁"),
        ("DATA_STALE", "数据不新鲜"),
        ("DATA_DEGRADED", "data health DEGRADED"),
        ("DATA_FAIL", "data health FAIL"),
        ("MACRO_UNAVAILABLE", "宏观核心数据不可用"),
        ("TECH_MACRO_CONFLICT", "与宏观"),
        ("PRICED_IN", "已被定价"),
        ("NO_FOLLOW_THROUGH", "需市场确认"),
        ("EXTREME_POSITION", "追高"),
        ("EXTREME_POSITION", "追空"),
        ("RISK_REWARD", "expected_R="),
        ("COUNTER_THESIS", "缺少反证"),
        ("DIRECTION_UNDECIDED", "方向未定"),
        ("NO_OPPORTUNITY", "未发现机会"),
    ]


def classify(d):
    """→ {code, category_cn, decision, detail}。永不抛。"""
    try:
        dec = (d or {}).get("decision")
        reason = (d or {}).get("reason") or (d or {}).get("no_trade_reason") or ""
        code = "OTHER_GATE"
        if dec == "TRADE":
            code = "TRADE_OK"
        else:
            for c, pat in _rules():
                if pat in reason:
                    code = c
                    break
        return {"code": code, "category_cn": CATEGORIES.get(code, code),
                "decision": dec, "detail": reason}
    except Exception:  # noqa: BLE001
        return {"code": "OTHER_GATE", "category_cn": CATEGORIES["OTHER_GATE"], "decision": None, "detail": ""}


def _canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decision_hash(d):
    try:
        return hashlib.sha256(_canon({k: v for k, v in (d or {}).items() if k != "decision_id"}).encode("utf-8")).hexdigest()
    except Exception:  # noqa: BLE001
        return None


def input_hash(ctx):
    return (ctx or {}).get("context_hash")


if __name__ == "__main__":
    import sys
    print(json.dumps(CATEGORIES, ensure_ascii=False, indent=1))
    if len(sys.argv) > 1:
        print(json.dumps(classify(json.load(open(sys.argv[1], encoding="utf-8"))), ensure_ascii=False))
