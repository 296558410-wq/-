# -*- coding: utf-8 -*-
"""L1 测试: Position State Machine — 合法/非法迁移, partial fill/exit, ADD 铁律,
SL/TP 不变量, 重启恢复, 重复平仓拒绝。
运行: .venv\\Scripts\\python.exe -m pytest research/hermes/trader_v1/tests/test_l1_position.py -q
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import position as P
from position import Position, PositionInvariantError, CONTRACT_SPEC

# 隔离状态目录
@pytest.fixture(autouse=True)
def iso_state(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "STATE_DIR", tmp_path / "positions")
    return tmp_path


def mkpos(side="LONG", stop=4390.0):
    pos = Position("POS-1", "TP-1", side, stop_level=stop, tp_levels=[{"price": 4430.0, "frac": 1.0}])
    return pos


def test_full_lifecycle_long():
    pos = mkpos()
    assert pos.state == "FLAT"
    pos.enter()
    assert pos.state == "ENTRY_PENDING"
    pos.fill(4400.0, 0.1)
    assert pos.state == "OPEN" and pos.avg_entry == 4400.0 and pos.qty_lots == 0.1
    pos.set_stop(4395.0)          # 收紧 SL(合法)
    assert pos.stop_level == 4395.0
    pos.set_tp([{"price": 4430.0, "frac": 1.0}])
    pos.mark(4420.0)              # MFE 更新
    assert pos.mfe == 20.0
    pos.hard_tp_hit(4430.0)
    assert pos.state == "EXIT_PENDING"
    r = pos.exit_fill(4430.0)
    assert pos.state == "CLOSED"
    assert r == pytest.approx((4430 - 4400) * 100 * 0.1, abs=0.02)
    assert pos.qty_lots == 0.0


def test_partial_fill_and_add():
    pos = mkpos()
    pos.enter()
    pos.partial_entry(4400.0, 0.05)       # 试探仓
    assert pos.state == "PARTIALLY_FILLED"
    pos.fill(4401.0, 0.05)                # 剩余成交
    assert pos.state == "OPEN"
    assert pos.qty_lots == 0.1
    assert pos.avg_entry == pytest.approx(4400.5)
    # ADD 合法(高于均价, 有理由)
    pos.add(4402.0, 0.1, "EV up after breakout confirm")
    assert pos.qty_lots == 0.2


def test_add_averaging_down_forbidden():
    pos = mkpos()
    pos.enter()
    pos.fill(4400.0, 0.1)
    with pytest.raises(PositionInvariantError):
        pos.add(4390.0, 0.1, "averaging down")   # 摊平 → 拒绝
    assert pos.qty_lots == 0.1


def test_stop_cannot_widen():
    pos = mkpos()
    pos.enter()
    pos.fill(4400.0, 0.1)
    pos.set_stop(4395.0)
    with pytest.raises(PositionInvariantError):
        pos.set_stop(4385.0)    # LONG SL 下移 = 扩大风险 → 拒绝
    assert pos.stop_level == 4395.0


def test_stop_illegal_cross_entry():
    pos = mkpos()
    pos.enter()
    pos.fill(4400.0, 0.1)
    with pytest.raises(PositionInvariantError):
        pos.set_stop(4405.0)    # LONG SL >= entry → 非法
    with pytest.raises(PositionInvariantError):
        pos.set_stop(4400.0)    # SL == entry → 非法


def test_illegal_transitions():
    pos = mkpos()
    # FLAT 直接 fill 非法
    with pytest.raises(PositionInvariantError):
        pos.fill(4400.0, 0.1)
    # CLOSED 后再 exit 拒绝(I3 重复平仓)
    pos.enter(); pos.fill(4400.0, 0.1)
    pos.request_exit("manual")
    pos.exit_fill(4390.0)
    assert pos.state == "CLOSED"
    with pytest.raises(PositionInvariantError):
        pos.exit_fill(4390.0)


def test_short_side():
    pos = mkpos(side="SHORT", stop=4410.0)
    pos.enter(); pos.fill(4400.0, 0.1)
    assert pos.side == "SHORT"
    pos.set_stop(4405.0)   # SHORT 下移 = 收紧(合法)
    with pytest.raises(PositionInvariantError):
        pos.set_stop(4415.0)  # 上移扩大风险 → 拒绝
    pos.mark(4390.0)
    assert pos.mfe == 10.0
    r = pos.hard_stop_hit(4390.0) if False else None
    pos.request_exit("tp")
    assert pos.exit_fill(4390.0) == pytest.approx((4400 - 4390) * 100 * 0.1, abs=0.02)


def test_partial_exit_reduces_qty():
    pos = mkpos()
    pos.enter(); pos.fill(4400.0, 0.2)
    pos.partial_exit(4410.0, 0.1, reason="partial_tp")
    assert pos.qty_lots == 0.1
    with pytest.raises(PositionInvariantError):
        pos.partial_exit(4415.0, 0.1)   # qty == total → 应 full exit
    pos.request_exit("rest")
    pos.exit_fill(4415.0, 0.1)
    assert pos.state == "CLOSED"


def test_restart_recovery(tmp_path, monkeypatch):
    """写快照后重新 load_position → 状态完整恢复(进程重启模拟)。"""
    pos = mkpos()
    pos.enter(); pos.fill(4400.0, 0.1); pos.set_stop(4395.0); pos.mark(4410.0)
    pos._persist()
    # 模拟重启: 新实例从磁盘恢复
    p2 = P.load_position("POS-1")
    assert p2 is not None
    assert p2.state == "OPEN"
    assert p2.qty_lots == 0.1 and p2.avg_entry == 4400.0
    assert p2.stop_level == 4395.0 and p2.mfe == 10.0
    # 恢复后可继续操作
    pos2 = p2
    pos2.request_exit("manual")
    assert pos2.exit_fill(4405.0) == pytest.approx(5.0 * 100 * 0.1, abs=0.02)


def test_open_positions_lists_non_closed():
    a = Position("POS-A", "TP-A", "LONG", stop_level=4390.0)
    a.enter(); a.fill(4400.0, 0.1)          # OPEN
    b = Position("POS-B", "TP-B", "LONG", stop_level=4389.0)
    b.enter(); b.fill(4401.0, 0.2)
    b.request_exit("x"); b.exit_fill(4399.0)  # CLOSED
    c = Position("POS-C", "TP-C", "LONG", stop_level=4390.0)
    c.enter()                                 # ENTRY_PENDING 未成交
    ops = P.open_positions()
    ids = [o["position_id"] for o in ops]
    assert "POS-A" in ids and "POS-B" not in ids
    assert all(o["state"] != "CLOSED" for o in ops)


def test_fail_closed_freezes():
    pos = mkpos()
    pos.fail_closed = True
    with pytest.raises(PositionInvariantError):
        pos.enter()
    with pytest.raises(PositionInvariantError):
        pos.mark(4410.0)
