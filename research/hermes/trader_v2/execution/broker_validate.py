# -*- coding: utf-8 -*-
"""V2 Broker 订单预校验（P1-C / §19–20）—— 发送前 fail-closed，杜绝 10016。

在真正调用 broker 之前本地校验：
- 方向边: BUY: SL<entry, TP>entry ; SELL: SL>entry, TP<entry
- 相对市价: 有效一侧；距离 >= stops_level
- tick/digits
任何不满足 → 本地 PRECHECK_REJECT（**不下单**）。
"""
from __future__ import annotations


def _on_tick(v, tick):
    if not tick:
        return True
    return abs(round(float(v) / tick) * tick - float(v)) < 1e-6


def precheck_order(direction, entry, sl, tp, *, market_bid=None, market_ask=None,
                   stops_level=0.0, freeze_level=0.0, digits=2, tick=0.01):
    """返回 (ok, code, detail)。code=None 表示通过。"""
    d = (direction or "").upper()
    if d not in ("LONG", "SHORT"):
        return False, "PRECHECK_REJECT", {"reason": "bad_direction", "direction": direction}
    if entry is None or sl is None or tp is None:
        return False, "PRECHECK_REJECT", {"reason": "missing_price", "entry": entry, "sl": sl, "tp": tp}
    entry, sl, tp = float(entry), float(sl), float(tp)
    for nm, v in (("entry", entry), ("sl", sl), ("tp", tp)):
        if not _on_tick(v, tick):
            return False, "PRECHECK_REJECT", {"reason": f"{nm}_off_tick", nm: v, "tick": tick}

    if d == "LONG":
        if not (sl < entry):
            return False, "PRECHECK_REJECT", {"reason": "long_sl_not_below_entry"}
        if not (tp > entry):
            return False, "PRECHECK_REJECT", {"reason": "long_tp_not_above_entry"}
    else:
        if not (sl > entry):
            return False, "PRECHECK_REJECT", {"reason": "short_sl_not_above_entry"}
        if not (tp < entry):
            return False, "PRECHECK_REJECT", {"reason": "short_tp_not_below_entry"}

    if market_bid is not None and market_ask is not None:
        mb, ma = float(market_bid), float(market_ask)
        if d == "SHORT":
            if sl <= ma:
                return False, "PRECHECK_REJECT", {"reason": "short_sl_at_or_below_market", "market_ask": ma}
            if tp >= mb:
                return False, "PRECHECK_REJECT", {"reason": "short_tp_at_or_above_market", "market_bid": mb}
            if stops_level and (sl - ma) < stops_level:
                return False, "PRECHECK_REJECT", {"reason": "sl_below_stops_level", "sl": sl, "market_ask": ma,
                                                  "stops_level": stops_level}
            if stops_level and (mb - tp) < stops_level:
                return False, "PRECHECK_REJECT", {"reason": "tp_below_stops_level", "tp": tp, "market_bid": mb,
                                                  "stops_level": stops_level}
        else:
            if sl >= mb:
                return False, "PRECHECK_REJECT", {"reason": "long_sl_at_or_above_market", "market_bid": mb}
            if tp <= ma:
                return False, "PRECHECK_REJECT", {"reason": "long_tp_at_or_below_market", "market_ask": ma}
            if stops_level and (mb - sl) < stops_level:
                return False, "PRECHECK_REJECT", {"reason": "sl_below_stops_level", "sl": sl, "market_bid": mb,
                                                  "stops_level": stops_level}
            if stops_level and (tp - ma) < stops_level:
                return False, "PRECHECK_REJECT", {"reason": "tp_below_stops_level", "tp": tp, "market_ask": ma,
                                                  "stops_level": stops_level}
    return True, None, {}
