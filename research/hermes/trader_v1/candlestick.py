# -*- coding: utf-8 -*-
"""candlestick.py — 日本蜡烛图形态识别(L3)

支持: Doji/Spinning Top/Marubozu/Hammer/Hanging Man/Inverted Hammer/Shooting Star/
Engulfing/Harami/Piercing/Dark Cloud Cover/Morning Star/Evening Star/
Three White Soldiers/Three Black Crows/Long Wick Rejection/Failed Breakout/
Inside Bar/Outside Bar

铁律: 禁止 Pattern → BUY/SELL 机械映射。本模块只输出形态标签 + 结构特征,
上下文/状态/位置/确认/EV 的合成由 Hermes 决策层完成。
输入: bars(o,h,l,c) 或单根; 全部基于已收盘 bar(调用方保证, 无 look-ahead)。
"""
import numpy as np


def body(o, c):
    return c - o


def is_bull(o, c):
    return c > o


def _rng(x):
    return max(x, 1e-12)


def detect_single(bar, prev=None):
    """单根形态识别。bar={o,h,l,c}; prev 可选(供 engulfing 等需前根者)。
    返回 {patterns: [..], bull: bool, body_frac, upper_wick, lower_wick}"""
    o, h, l, c = float(bar["o"]), float(bar["h"]), float(bar["l"]), float(bar["c"])
    rng = _rng(h - l)
    bod = abs(c - o)
    body_frac = bod / rng
    up_wick = h - max(o, c)
    lo_wick = min(o, c) - l
    up_frac = up_wick / rng
    lo_frac = lo_wick / rng
    bull = is_bull(o, c)
    pats = []
    # Doji: 实体极小(影线长短不限, 长腿十字亦属 doji)
    if body_frac < 0.08:
        pats.append("doji")
    # Spinning Top: 小实体 + 上下影
    if 0.08 <= body_frac < 0.3 and up_frac > 0.2 and lo_frac > 0.2:
        pats.append("spinning_top")
    # Marubozu: 无/极短影线
    if body_frac > 0.8 and up_frac < 0.05 and lo_frac < 0.05:
        pats.append("marubozu_bull" if bull else "marubozu_bear")
    # Hammer / Hanging Man: 长下影 + 小实体(上端)
    if lo_frac > 0.55 and body_frac < 0.35 and up_frac < 0.25:
        # 需位置上下文才能区分 hammer/hanging → 交给上层; 此处标 "long_lower_wick"
        pats.append("long_lower_wick")
    # Inverted Hammer / Shooting Star: 长上影 + 小实体(下端)
    if up_frac > 0.55 and body_frac < 0.35 and lo_frac < 0.25:
        pats.append("long_upper_wick")
    # Long Wick Rejection(总影长 > 2×实体, 明确方向拒绝)
    if (up_frac + lo_frac) > 0.7 and body_frac < 0.2:
        pats.append("rejection_" + ("bull" if lo_frac >= up_frac else "bear"))
    return {"patterns": pats, "bull": bull, "body_frac": round(body_frac, 3),
            "upper_wick_frac": round(up_frac, 3), "lower_wick_frac": round(lo_frac, 3),
            "range": round(rng, 2)}


def detect_pair(bar, prev):
    """双根形态(engulfing/harami/piercing/dark cloud/inside/outside)。"""
    o, h, l, c = (float(bar[k]) for k in ("o", "h", "l", "c"))
    po, ph, pl, pc = (float(prev[k]) for k in ("o", "h", "l", "c"))
    pats = []
    p_bull, c_bull = pc > po, c > o
    # Engulfing(看涨/看跌吞没): 当前实体包住前实体
    if abs(c - o) > abs(pc - po) and \
            min(o, c) < min(po, pc) and max(o, c) > max(po, pc):
        pats.append("engulfing_bull" if c_bull else "engulfing_bear")
    # Harami: 当前实体被前实体包住
    if abs(c - o) < abs(pc - po) and \
            min(po, pc) < min(o, c) and max(o, c) < max(po, pc):
        pats.append("harami")
    # Piercing: 跌势后阳线收于前阴线中点上方
    if not p_bull and c_bull and c > po and c < (po + pc) / 2 and o < po:
        pats.append("piercing")
    # Dark Cloud Cover: 涨势后阴线开于前阳线高点上方、收于中点下方
    if p_bull and not c_bull and o > ph and c < (po + pc) / 2:
        pats.append("dark_cloud_cover")
    # Inside Bar: 当前高低都在前根内
    if h <= ph and l >= pl:
        pats.append("inside_bar")
    # Outside Bar: 当前高低包住前根
    if h > ph and l < pl:
        pats.append("outside_bar")
    return pats


def detect_star(bar2, bar1, bar0):
    """三根星形: Morning Star / Evening Star(中间实体小+跳空)。"""
    pats = []
    o2, c2 = bar2["o"], bar2["c"]  # 第一根
    o1, c1 = bar1["o"], bar1["c"]  # 中间
    o0, c0 = bar0["o"], bar0["c"]  # 当前
    rng1 = _rng(bar1["h"] - bar1["l"])
    small = abs(c1 - o1) / rng1 < 0.3
    # Morning: 阴 → 小实体(下探) → 阳收于第一根中点上方
    if c2 < o2 and small and c0 > o0 and c0 > (o2 + c2) / 2:
        pats.append("morning_star")
    # Evening: 阳 → 小实体(上探) → 阴收于第一根中点下方
    if c2 > o2 and small and c0 < o0 and c0 < (o2 + c2) / 2:
        pats.append("evening_star")
    return pats


def detect_three(bar2, bar1, bar0):
    """三白兵/三黑鸦。"""
    pats = []
    if all(b["c"] > b["o"] for b in (bar2, bar1, bar0)) and \
            bar1["c"] > bar2["c"] and bar0["c"] > bar1["c"]:
        pats.append("three_white_soldiers")
    if all(b["c"] < b["o"] for b in (bar2, bar1, bar0)) and \
            bar1["c"] < bar2["c"] and bar0["c"] < bar1["c"]:
        pats.append("three_black_crows")
    return pats


def failed_breakout(bars, level_key="h"):
    """Failed Breakout: 收盘突破 N 根高点后又收回(出现长上影/收于突破位下方)。"""
    if len(bars) < 3:
        return None
    last, prior = bars[-1], bars[:-1]
    hi = max(b["h"] for b in prior[-10:]) if len(prior) >= 3 else None
    if hi is None:
        return None
    if level_key == "h" and last["h"] > hi and last["c"] < hi:
        return {"pattern": "failed_breakout_up", "level": round(float(hi), 2)}
    if level_key == "l" and last["l"] < hi and last["c"] > hi:
        return {"pattern": "failed_breakout_down", "level": round(float(hi), 2)}
    return None


def analyze(bars, last_n=12):
    """完整分析最近 bars: 返回 {last: 单根+对根形态, history: [...]}。
    只读已收盘 bars; 输出标签供 Hermes 与 Context/State/Location/Confirmation/EV 合成。"""
    if len(bars) < 2:
        return {"error": "insufficient"}
    res = {"last": None, "recent": [], "failed_breakout": None}
    tail = list(bars[-last_n:])
    last = tail[-1]
    prev = tail[-2] if len(tail) >= 2 else None
    if prev is not None:
        single = detect_single(last)
        pairs = detect_pair(last, prev)
        stars = detect_star(tail[-3], tail[-2], tail[-1]) if len(tail) >= 3 else []
        threes = detect_three(tail[-3], tail[-2], tail[-1]) if len(tail) >= 3 else []
        res["last"] = {**single, "pair_patterns": pairs,
                       "multi_patterns": stars + threes,
                       "ts": str(last.get("ts_utc", ""))}
        res["failed_breakout"] = failed_breakout(tail)
    # 近期形态摘要(供 Hermes 快速参考)
    for i in range(1, min(6, len(tail))):
        b = tail[-i]
        s = detect_single(b)
        res["recent"].append({"ts": str(b.get("ts_utc", "")),
                              "patterns": s["patterns"], "bull": s["bull"]})
    return res


def label_map():
    """形态 → 中文标签(Dashboard/日志)。"""
    return {"doji": "十字星", "spinning_top": "陀螺线", "marubozu_bull": "光头光脚阳线",
            "marubozu_bear": "光头光脚阴线", "hammer": "锤子线", "hanging_man": "上吊线",
            "inverted_hammer": "倒锤子", "shooting_star": "射击之星",
            "engulfing_bull": "看涨吞没", "engulfing_bear": "看跌吞没", "harami": "孕线",
            "piercing": "刺透形态", "dark_cloud_cover": "乌云盖顶",
            "morning_star": "晨星", "evening_star": "暮星",
            "three_white_soldiers": "三白兵", "three_black_crows": "三黑鸦",
            "long_lower_wick": "长下影", "long_upper_wick": "长上影",
            "rejection_bull": "看涨拒绝", "rejection_bear": "看跌拒绝",
            "inside_bar": "内包线", "outside_bar": "外包线",
            "failed_breakout_up": "假突破向上", "failed_breakout_down": "假突破向下"}
