# -*- coding: utf-8 -*-
"""L2 测试: H3 未收盘 bar / Stop Authority / Position Decision Engine 优先级。
运行: .venv\\Scripts\\python.exe -m pytest research/hermes/trader_v1/tests/test_l2_decision.py -q
"""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from position import Position, PositionInvariantError  # noqa: E402
import position as P  # noqa: E402
import stop_authority as SA  # noqa: E402
import position_decision as PD  # noqa: E402


@pytest.fixture(autouse=True)
def iso(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "STATE_DIR", tmp_path / "positions")


def mk_long_open(entry=4400.0, stop=4390.0, qty=0.1):
    pos = Position("POS-D1", "TP-D1", "LONG", stop_level=stop)
    pos.enter()
    pos.fill(entry, qty)
    return pos


def test_H3_state_package_drops_forming_bar():
    """未收盘 M15 bar 不应进入正式状态。"""
    from state_package import resample
    import pandas as pd
    # 构造: tick 到 12:13(12:00 bar 未收盘)
    idx = pd.date_range("2026-09-07 11:00:00", "2026-09-07 12:13:00", freq="1min")
    df = pd.DataFrame({"ts_utc": idx, "mid": 4400.0, "bid": 4399.9, "ask": 4400.1})
    bars = resample(df, "15min", drop_forming=True)
    last = str(bars["ts_utc"].iloc[-1])
    assert last == "2026-09-07 11:45:00"  # 12:00 bar 未收盘(12:13<12:15) → 剔除, 最后=11:45
    bars2 = resample(df, "15min", drop_forming=False)
    assert len(bars2) == len(bars) + 1
    assert str(bars2["ts_utc"].iloc[-1]) == "2026-09-07 12:00:00"


def test_breakeven_eligibility():
    pos = mk_long_open(entry=4400.0, stop=4390.0)
    ok, _ = SA.breakeven_eligible(pos, 4400.5, atr_value=0.5)
    assert not ok                      # 浮盈不足
    ok, _ = SA.breakeven_eligible(pos, 4405.0, atr_value=0.5)
    assert ok                          # 浮盈 5.0 ≥ 噪声 0.75+


def test_stop_authority_no_overwrite():
    """多个 authority 按优先级取首个可用; 结构 trailing 不越过均价。"""
    pos = mk_long_open(entry=4400.0, stop=4390.0)
    res = SA.select_authority(pos, 4405.0, [
        ("structure", {"swing_level": 4396.0}),          # 结构
        ("volatility", {"atr_value": 1.0, "k": 1.5}),    # vol(不应被用)
    ])
    assert res["authority"] == "structure" and res["level"] == 4396.0
    # 结构位越过均价 → 该 authority 不可用, 落到 vol
    res2 = SA.select_authority(pos, 4405.0, [
        ("structure", {"swing_level": 4405.0}),          # 非法(>avg)
        ("volatility", {"atr_value": 1.0, "k": 1.5}),
    ])
    assert res2["authority"] == "volatility"
    assert res2["level"] == pytest.approx(4400.0 - 1.5, abs=0.01)


def test_decision_priority_hard_risk_first():
    pos = mk_long_open()
    d = PD.decide({"action": "HOLD"}, pos, 4405.0,
                  hard_risk={"daily_loss_breached": True})
    assert d["action"] == "EXIT" and d["priority"] == 1


def test_decision_invalidation_second():
    pos = mk_long_open()
    d = PD.decide({"action": "HOLD", "thesis_status": "invalidated"}, pos, 4405.0)
    assert d["action"] == "EXIT" and d["priority"] == 2


def test_decision_add_averaging_down_rejected():
    pos = mk_long_open(entry=4400.0)
    # 现价 4395 < avg → 摊平 → 拒绝
    d = PD.decide({"action": "ADD", "add_ev_justification": "x", "add_size": 0.1},
                  pos, 4395.0)
    assert d["action"] == "HOLD" and "averaging_down" in d["action_reason"][0]
    # 现价 4402 > avg + 有 EV 理由 → 允许
    d2 = PD.decide({"action": "ADD", "add_ev_justification": "breakout", "add_size": 0.1},
                   pos, 4402.0)
    assert d2["action"] == "ADD"


def test_decision_switch_when_new_ev_much_higher():
    pos = mk_long_open()
    d = PD.decide({"action": "HOLD", "ev_hold": 0.5}, pos, 4402.0,
                  new_opportunity_ev=1.5)
    assert d["action"] == "EXIT" and d["priority"] == 5


def test_decision_reduce_invalid_size():
    pos = mk_long_open(qty=0.1)
    d = PD.decide({"action": "REDUCE", "partial_exit_size": 0.5}, pos, 4402.0)
    assert d["action"] == "HOLD"          # size > qty → 拒绝


def test_apply_partial_reduce():
    pos = mk_long_open(qty=0.2)
    d = PD.decide({"action": "REDUCE", "partial_exit_size": 0.1}, pos, 4402.0)
    assert d["action"] == "REDUCE"
    out = PD.apply_action(pos, d, 4402.0)
    assert pos.qty_lots == 0.1


def test_apply_protect_moves_stop():
    pos = mk_long_open(entry=4400.0, stop=4390.0)
    d = PD.decide({"action": "PROTECT",
                   "new_stop": {"level": 4400.0, "authority": "breakeven"}},
                  pos, 4405.0)
    assert d["action"] == "PROTECT"
    PD.apply_action(pos, d, 4405.0)
    assert pos.stop_level == 4400.0
