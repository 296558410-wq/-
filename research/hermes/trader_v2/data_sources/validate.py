# -*- coding: utf-8 -*-
"""V2 Data Source Router — 数据质量验证（错误数据 → INVALID，禁止进入 Hermes）。"""
from __future__ import annotations
import math
from datetime import datetime, timezone


def _now_ts():
    return datetime.now(timezone.utc).timestamp()


def validate_bars(bars, tf: str, tf_seconds: int, now_ts=None, max_jump_pct=0.25) -> tuple[bool, list[str], list[dict]]:
    """校验 OHLC bars。返回 (ok, reasons, cleaned_bars)。"""
    reasons: list[str] = []
    now_ts = now_ts or _now_ts()
    if bars is None:
        return False, ["bars=None"], []
    clean = []
    last_t = None
    for b in bars:
        try:
            t = int(b["t"]); o = float(b["o"]); h = float(b["h"]); l = float(b["l"]); c = float(b["c"])
        except Exception:  # noqa: BLE001
            reasons.append("non_numeric_bar"); continue
        if any(math.isnan(x) or math.isinf(x) for x in (o, h, l, c)):
            reasons.append("nan_bar"); continue
        if min(o, h, l, c) <= 0:
            reasons.append("impossible_price(<=0)"); continue
        if not (l <= o <= h and l <= c <= h):
            reasons.append(f"ohlc_inconsistent@{t}"); continue
        if t + tf_seconds > now_ts:
            reasons.append(f"future_unclosed_bar@{t}"); continue     # PIT：剔除未收盘
        if last_t is not None and t <= last_t:
            reasons.append(f"non_monotonic_or_dup@{t}"); continue
        if last_t is not None and t - last_t > 4 * tf_seconds:
            reasons.append(f"gap>{4}x@{t}")                          # 记录但不丢（缺口可见）
        clean.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": float(b.get("v") or 0)})
        last_t = t
    # 极端跳变（相邻收盘 > max_jump）
    for i in range(1, len(clean)):
        prev, cur = clean[i - 1]["c"], clean[i]["c"]
        if prev and abs(cur - prev) / prev > max_jump_pct:
            reasons.append(f"extreme_jump@{clean[i]['t']}")
    hard = [r for r in reasons if r.startswith(("nan", "impossible", "ohlc", "future", "non_numeric", "non_monotonic"))]
    return (len(clean) > 0 and not hard), reasons, clean


def validate_quote(q) -> tuple[bool, list[str]]:
    reasons = []
    if q is None:
        return False, ["quote=None"]
    price = q.get("price")
    if price is None:
        return False, ["price=None"]
    try:
        price = float(price)
    except Exception:  # noqa: BLE001
        return False, ["price_not_float"]
    if math.isnan(price) or math.isinf(price) or price <= 0:
        return False, ["price_impossible"]
    bid, ask = q.get("bid"), q.get("ask")
    if bid is not None and ask is not None:
        try:
            if float(bid) > float(ask):
                reasons.append("bid>ask")
        except Exception:  # noqa: BLE001
            reasons.append("bidask_bad")
    return (len(reasons) == 0), reasons


def validate_scalar(v):
    if v is None:
        return False, ["null"]
    try:
        f = float(v)
    except Exception:  # noqa: BLE001
        return False, ["not_numeric"]
    if math.isnan(f) or math.isinf(f):
        return False, ["nan_inf"]
    return True, []
