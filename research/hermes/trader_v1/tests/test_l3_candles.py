# -*- coding: utf-8 -*-
"""L3 测试: 蜡烛图形态识别(已收盘 bar; 无 look-ahead; 标签非信号)。
运行: .venv\\Scripts\\python.exe -m pytest research/hermes/trader_v1/tests/test_l3_candles.py -q
"""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import candlestick as C


def bar(o, h, l, c, ts="2026-09-07 11:00:00"):
    return {"o": o, "h": h, "l": l, "c": c, "ts_utc": ts}


def test_doji():
    # 真十字: 实体≈0, 上下影对称短
    b = bar(4400, 4401, 4399, 4400.02)
    r = C.detect_single(b)
    assert "doji" in r["patterns"]


def test_doji_long_wick_is_still_doji():
    # 长腿十字(影线长但实体≈0)按教科书仍属 doji
    b = bar(4400, 4406, 4394, 4400.05)
    r = C.detect_single(b)
    assert "doji" in r["patterns"]


def test_marubozu_bull():
    b = bar(4390, 4400, 4390.01, 4399.99)
    r = C.detect_single(b)
    assert "marubozu_bull" in r["patterns"]


def test_long_lower_wick_hammer_shape():
    # 长下影(hammer 形态特征; 标签非买卖信号)
    b = bar(4400, 4401, 4390, 4400.5)
    r = C.detect_single(b)
    assert "long_lower_wick" in r["patterns"]


def test_long_upper_wick_shooting_shape():
    b = bar(4400, 4410, 4399, 4400.3)
    r = C.detect_single(b)
    assert "long_upper_wick" in r["patterns"]


def test_engulfing_bull():
    prev = bar(4400, 4402, 4398, 4399)     # 阴线
    cur = bar(4398, 4405, 4397, 4404)      # 阳线包住
    pats = C.detect_pair(cur, prev)
    assert "engulfing_bull" in pats


def test_inside_bar():
    prev = bar(4400, 4410, 4390, 4405)
    cur = bar(4396, 4404, 4394, 4402)
    pats = C.detect_pair(cur, prev)
    assert "inside_bar" in pats


def test_morning_star():
    b2 = bar(4400, 4402, 4395, 4396)       # 阴(第一根)
    b1 = bar(4395, 4400, 4390, 4393)       # 小实体下探(中间)
    b0 = bar(4390, 4410, 4389, 4408)       # 阳, 收于 b2 中点上方(当前)
    pats = C.detect_star(b2, b1, b0)       # 顺序 = (bar2, bar1, bar0)
    assert "morning_star" in pats


def test_evening_star():
    b2 = bar(4390, 4400, 4388, 4399)       # 阳(第一根)
    b1 = bar(4399, 4405, 4395, 4398)       # 小实体(中间)
    b0 = bar(4405, 4406, 4380, 4385)       # 阴, 收于 b2 中点下方(当前)
    pats = C.detect_star(b2, b1, b0)
    assert "evening_star" in pats


def test_three_white_soldiers():
    bars = [bar(4390, 4395, 4388, 4394), bar(4394, 4399, 4392, 4398),
            bar(4398, 4404, 4396, 4403)]
    pats = C.detect_three(bars[0], bars[1], bars[2])
    assert "three_white_soldiers" in pats


def test_failed_breakout_up():
    bars = [bar(4380, 4400, 4378, 4390)] * 3 + [bar(4390, 4408, 4389, 4395)]
    r = C.failed_breakout(bars, "h")
    assert r and r["pattern"] == "failed_breakout_up"


def test_no_mechanical_signal():
    """形态输出是标签, 不含买卖建议字段。"""
    b = bar(4400, 4410, 4390, 4405)
    r = C.detect_single(b)
    assert not any(k in r for k in ("signal", "action", "direction"))


def test_analyze_returns_ts_labels():
    bars = [bar(4380 + i, 4385 + i, 4375 + i, 4383 + i, f"2026-09-07 1{i}:00:00")
            for i in range(10)]
    out = C.analyze(bars)
    assert out["last"] is not None and out["recent"]
    assert isinstance(out["last"]["patterns"], list)
