# -*- coding: utf-8 -*-
"""trigger.py — Trade Plan 触发/失效/取消 机械判定(TRIGGER_CONTRACT, 无 LLM)。

支持条件语法: price_cross_up/price_cross_down/close_above/close_below/zone_touch/
m15_close_in_zone/spread_under_bps/vol_under_bps/and/or。
判定时点: M15 收盘(engine 每轮调用) + quote 检查(最新 mid/spread)。
输出: {result: PENDING|TRIGGERED|CANCELLED, reason, matched, quote_at_check}
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _num(x):
    return float(x)


def eval_cond(cond, ctx):
    """ctx: {last_close, last_mid, spread_bps, vol_bps, cycle_high, cycle_low}"""
    if not isinstance(cond, dict):
        return False, f"bad_cond:{cond}"
    for k in ("and", "or"):
        if k in cond:
            subs = cond[k] or []
            res = [eval_cond(c, ctx)[0] for c in subs]
            ok = all(res) if k == "and" else any(res)
            return ok, f"{k}({res})"
    kv = [(k, v) for k, v in cond.items() if k != "note"]
    if len(kv) != 1:
        return False, f"cond_needs_single_key:{list(cond.keys())}"
    key, val = kv[0]
    mid = ctx.get("last_mid") or ctx.get("last_close")
    close = ctx.get("last_close")
    try:
        if key == "price_cross_up" and mid is not None:
            return mid >= _num(val), f"mid {mid} >= {val}"
        if key == "price_cross_down" and mid is not None:
            return mid <= _num(val), f"mid {mid} <= {val}"
        if key == "close_above" and close is not None:
            return close > _num(val), f"close {close} > {val}"
        if key == "close_below" and close is not None:
            return close < _num(val), f"close {close} < {val}"
        if key == "zone_touch" and mid is not None:
            lo, hi = _num(val[0]), _num(val[1])
            return lo <= mid <= hi, f"mid {mid} in [{lo},{hi}]"
        if key == "m15_close_in_zone" and close is not None:
            lo, hi = _num(val[0]), _num(val[1])
            return lo <= close <= hi, f"close {close} in [{lo},{hi}]"
        if key == "spread_under_bps":
            sp = ctx.get("spread_bps")
            return sp is not None and sp < _num(val), f"spread {sp} < {val}"
        if key == "vol_under_bps":
            vv = ctx.get("vol_bps")
            return vv is not None and vv < _num(val), f"vol {vv} < {val}"
    except Exception as e:  # noqa: BLE001
        return False, f"eval_error:{e}"
    return False, f"unknown_cond:{key}"


def check_trigger(plan, ctx):
    """触发判定: trigger_condition 满足 → TRIGGERED; 否则 PENDING。
    invalidation_condition 先查: 满足 → CANCELLED(invalidated)。"""
    inv = plan.get("invalidation_condition")
    if inv:
        hit, why = eval_cond(inv, ctx)
        if hit:
            return {"result": "CANCELLED", "reason": "invalidated", "matched": why}
    tr = plan.get("trigger_condition")
    if not tr:
        return {"result": "PENDING", "reason": "no_trigger_cond", "matched": ""}
    hit, why = eval_cond(tr, ctx)
    if hit:
        return {"result": "TRIGGERED", "reason": "trigger_met", "matched": why}
    return {"result": "PENDING", "reason": "not_yet", "matched": why}


if __name__ == "__main__":
    # 冒烟自检
    plan = {"trigger_condition": {"and": [{"close_below": 4405.0}, {"spread_under_bps": 0.6}]},
            "invalidation_condition": {"close_below": 4390.0}}
    for ctx in ({"last_close": 4403.0, "last_mid": 4403.5, "spread_bps": 0.4},
                {"last_close": 4407.0, "last_mid": 4407.2, "spread_bps": 0.4},
                {"last_close": 4388.0, "last_mid": 4388.5, "spread_bps": 0.4}):
        print(ctx["last_close"], "→", check_trigger(plan, ctx))
