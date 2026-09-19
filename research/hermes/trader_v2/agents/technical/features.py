# -*- coding: utf-8 -*-
"""V2 Agent1 特征层 —— 由单源 OHLC bars 计算结构化技术特征（纯确定性, 无 LLM）。

覆盖任务书 §四: 多周期趋势/高低点结构/趋势强度/突破/假突破/回撤/支撑阻力/VWAP/EMA,
波动(ATR/realized vol/expansion-contraction/异常), 市场状态(趋势|震荡|突破|回撤|高波动|流动性异常)。
全部基于已收盘 bar(由 market_data 保证)。
"""
from __future__ import annotations
import math


def _c(bars): return [b["c"] for b in bars]


def sma(xs, n):
    if len(xs) < n: return None
    return sum(xs[-n:]) / n


def ema_series(xs, n):
    if len(xs) < n: return []
    k = 2 / (n + 1)
    e = sum(xs[:n]) / n
    out = [e]
    for x in xs[n:]:
        e = x * k + e * (1 - k)
        out.append(e)
    return out


def ema(xs, n):
    s = ema_series(xs, n)
    return s[-1] if s else None


def rsi(xs, n=14):
    if len(xs) < n + 1: return None
    gains, losses = [], []
    for i in range(1, len(xs)):
        d = xs[i] - xs[i - 1]
        gains.append(max(d, 0.0)); losses.append(max(-d, 0.0))
    ag = sum(gains[:n]) / n; al = sum(losses[:n]) / n
    for i in range(n, len(gains)):
        ag = (ag * (n - 1) + gains[i]) / n
        al = (al * (n - 1) + losses[i]) / n
    if al == 0: return 100.0
    rs = ag / al
    return 100 - 100 / (1 + rs)


def atr(bars, n=14):
    if len(bars) < n + 1: return None
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    a = sum(trs[:n]) / n
    for i in range(n, len(trs)):
        a = (a * (n - 1) + trs[i]) / n
    return a


def realized_vol(close, n=20):
    if len(close) < n + 1: return None
    rets = [math.log(close[i] / close[i - 1]) for i in range(1, len(close)) if close[i - 1] > 0]
    tail = rets[-n:]
    if len(tail) < 2: return None
    mu = sum(tail) / len(tail)
    var = sum((x - mu) ** 2 for x in tail) / (len(tail) - 1)
    return math.sqrt(var * 252 * 96)  # 年化(近似, 15m 尺度)


def vwap(bars, day_anchor=True):
    """成交量加权均价。day_anchor: 仅用最新 UTC 日的 bar。"""
    if not bars: return None
    import datetime as _dt
    def _d(ts):
        return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).date()
    if day_anchor:
        last_day = _d(bars[-1]["t"])
        use = [b for b in bars if _d(b["t"]) == last_day]
    else:
        use = bars
    sv = sum(b["v"] for b in use)
    if sv <= 0:
        # 无成交量数据 → 退化为典型价均值
        return sum((b["h"] + b["l"] + b["c"]) / 3 for b in use) / len(use) if use else None
    return sum(((b["h"] + b["l"] + b["c"]) / 3) * b["v"] for b in use) / sv


def swings(bars, k=2):
    """swing 高/低点(左右各 k 根)。返回最近若干 {type, price, i}。"""
    out = []
    for i in range(k, len(bars) - k):
        hi = bars[i]["h"]; lo = bars[i]["l"]
        if all(hi >= bars[j]["h"] for j in range(i - k, i + k + 1) if j != i):
            out.append({"type": "H", "price": hi, "i": i})
        if all(lo <= bars[j]["l"] for j in range(i - k, i + k + 1) if j != i):
            out.append({"type": "L", "price": lo, "i": i})
    return out[-8:]


def structure(bars):
    """高低点结构: HH/HL/LH/LL 计数 + 最近 swing 序列 + 一致性。"""
    sw = swings(bars)
    hs = [s for s in sw if s["type"] == "H"]
    ls = [s for s in sw if s["type"] == "L"]
    hh = sum(1 for a, b in zip(hs, hs[1:]) if b["price"] > a["price"])
    lh = sum(1 for a, b in zip(hs, hs[1:]) if b["price"] < a["price"])
    hl = sum(1 for a, b in zip(ls, ls[1:]) if b["price"] > a["price"])
    ll = sum(1 for a, b in zip(ls, ls[1:]) if b["price"] < a["price"])
    bias = "up" if (hh + hl) > (lh + ll) else ("down" if (lh + ll) > (hh + hl) else "neutral")
    return {"hh": hh, "lh": lh, "hl": hl, "ll": ll, "swing_bias": bias,
            "last_swings": sw[-4:]}


def trend_range(close, n=20):
    """效率比 ER 分类: trend / range / mixed。"""
    if len(close) < n + 1: return {"cat": "unknown", "er": None}
    tail = close[-(n + 1):]
    net = abs(tail[-1] - tail[0])
    path = sum(abs(tail[i] - tail[i - 1]) for i in range(1, len(tail)))
    er = net / path if path > 0 else 0.0
    cat = "trend" if er > 0.35 else ("range" if er < 0.15 else "mixed")
    return {"cat": cat, "er": round(er, 3)}


def expand_contract(bars, n=10):
    if len(bars) < 2 * n + 2: return {"state": "unknown", "ratio": None}
    atrs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i - 1]["c"]
        atrs.append(max(h - l, abs(h - pc), abs(l - pc)))
    recent = sum(atrs[-n:]) / n
    prior = sum(atrs[-2 * n:-n]) / n
    if prior <= 0: return {"state": "unknown", "ratio": None}
    r = recent / prior
    state = "expanding" if r > 1.3 else ("contracting" if r < 0.75 else "neutral")
    return {"state": state, "ratio": round(r, 2)}


def range_pos(bars, n=60):
    if len(bars) < 2: return {}
    use = bars[-n:]
    hi = max(b["h"] for b in use); lo = min(b["l"] for b in use)
    c = use[-1]["c"]
    pos = (c - lo) / (hi - lo) * 100 if hi > lo else None
    return {"high": round(hi, 2), "low": round(lo, 2),
            "pos_pct": round(pos, 1) if pos is not None else None}


def recent_move_bps(close, n=6):
    if len(close) < n + 1: return None
    a, b = close[-(n + 1)], close[-1]
    return round((b / a - 1) * 1e4, 1) if a else None


def bar_behavior(bars, n=6):
    """价格行为: 连续方向/实体/影线/收盘位置(最近 n 根)。"""
    use = bars[-n:]
    res = []
    for b in use:
        rng = b["h"] - b["l"]
        body = b["c"] - b["o"]
        res.append({"dir": "up" if body > 0 else ("down" if body < 0 else "flat"),
                    "body_ratio": round(abs(body) / rng, 2) if rng > 0 else None,
                    "close_pos": round((b["c"] - b["l"]) / rng, 2) if rng > 0 else None,
                    "upper_wick": round((b["h"] - max(b["o"], b["c"])) / rng, 2) if rng > 0 else None,
                    "lower_wick": round((min(b["o"], b["c"]) - b["l"]) / rng, 2) if rng > 0 else None})
    return res


def breakout_state(bars, lookback=20):
    """突破/假突破/回撤检测(相对前 lookback 区间)。"""
    if len(bars) < lookback + 3: return {"state": "unknown"}
    hist = bars[-(lookback + 1):-1]
    hi = max(b["h"] for b in hist); lo = min(b["l"] for b in hist)
    last = bars[-1]
    up_break = last["c"] > hi
    dn_break = last["c"] < lo
    up_wick_fail = last["h"] > hi and last["c"] <= hi
    dn_wick_fail = last["l"] < lo and last["c"] >= lo
    state = "breakout_up" if up_break else ("breakout_down" if dn_break else
            ("false_breakout_up" if up_wick_fail else ("false_breakout_down" if dn_wick_fail else "inside")))
    return {"state": state, "range_hi": round(hi, 2), "range_lo": round(lo, 2)}


def tf_features(bars, tf):
    """单个周期的完整特征块。"""
    close = _c(bars)
    f = {"tf": tf, "n_bars": len(bars)}
    if len(bars) < 5:
        f["state"] = "DATA_GAP"
        return f
    f["state"] = "ok"
    f["last_close"] = round(close[-1], 2)
    f["ma"] = {"sma20": _r(sma(close, 20)), "sma50": _r(sma(close, 50)), "sma200": _r(sma(close, 200))}
    f["ema"] = {"ema20": _r(ema(close, 20)), "ema50": _r(ema(close, 50)), "ema200": _r(ema(close, 200))}
    f["rsi14"] = _r(rsi(close, 14))
    a = atr(bars, 14)
    f["atr14"] = _r(a)
    f["atr_pct"] = round(a / close[-1] * 100, 3) if a and close[-1] else None
    f["realized_vol_ann"] = _r(realized_vol(close, 20), 4)
    f["vwap"] = _r(vwap(bars))
    f["structure"] = structure(bars)
    f["trend_range"] = trend_range(close)
    f["exp_cont"] = expand_contract(bars)
    f["range60"] = range_pos(bars, 60)
    f["recent_move_bps"] = recent_move_bps(close, 6)
    f["price_vs_sma20_bps"] = round((close[-1] / f["ma"]["sma20"] - 1) * 1e4, 1) if f["ma"]["sma20"] else None
    f["breakout"] = breakout_state(bars)
    f["bar_behavior"] = bar_behavior(bars)
    return f


def _r(x, n=2):
    return None if x is None else round(float(x) + 0.0, n)


def market_regime(tfs: dict, live: dict = None) -> dict:
    """综合多周期 → 市场状态标签 + 流动性/波动提示。"""
    cats = {tf: tfs.get(tf, {}).get("trend_range", {}).get("cat") for tf in ("5m", "15m", "60m", "4h", "1d")}
    vol = tfs.get("15m", {}).get("exp_cont", {}).get("state")
    regime = "mixed"
    trend_ct = sum(1 for c in cats.values() if c == "trend")
    if trend_ct >= 3: regime = "trend"
    elif sum(1 for c in cats.values() if c == "range") >= 3: regime = "range"
    flags = []
    if vol == "expanding": flags.append("vol_expansion")
    if vol == "contracting": flags.append("vol_contraction")
    if live and live.get("spread") is not None and live.get("spread") > 0.6:
        flags.append("wide_spread")
    return {"regime": regime, "trend_range_by_tf": cats, "vol_state_15m": vol, "flags": flags}


if __name__ == "__main__":
    import sys, json
    sys.stdout.reconfigure(encoding="utf-8")
    from market_data import snapshot_history
    h = snapshot_history("GC=F")
    for tf in ("15m", "60m"):
        print(tf, json.dumps({k: v for k, v in tf_features(h[tf]["bars"], tf).items()
                              if k in ("last_close", "rsi14", "atr_pct", "vwap", "trend_range", "range60", "breakout")},
                             ensure_ascii=False))
