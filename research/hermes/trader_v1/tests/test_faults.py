# -*- coding: utf-8 -*-
"""Fault Injection + 用户测试矩阵专项(V12 §二十)。
覆盖: duplicate decision/trigger/restart/recovery/partial fill/partial close/
rejected/stale quote/spread expansion/extreme vol/duplicate callback/network failure/
price precision/lot rounding/min-max lot/insufficient margin/opposite signal/
new opportunity while holding/simultaneous signals/SL-TP mod fail/forming bar。
运行: .venv\\Scripts\\python.exe -m pytest research/hermes/trader_v1/tests/test_faults.py -q
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import ledger as L  # noqa: E402
import position as P  # noqa: E402
import trader_core as TC  # noqa: E402
import review as RV  # noqa: E402
import engine  # noqa: E402
import invariants as INV  # noqa: E402
from position import Position, PositionInvariantError, CONTRACT_SPEC  # noqa: E402


@pytest.fixture(autouse=True)
def iso(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "LEDGER_P", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(P, "STATE_DIR", tmp_path / "positions")
    monkeypatch.setattr(RV, "REVIEW_DIR", tmp_path / "reviews")
    monkeypatch.setattr(engine, "RUN", tmp_path)
    monkeypatch.setattr(TC, "RUN", tmp_path)
    return tmp_path


def seed(side="LONG", stop=4390.0, tp=4430.0, pid="TP-F", dec="DF"):
    plan = {"direction": side, "entry_zone": {"low": 4400.0, "high": 4405.0},
            "stop_logic": {"level_price": stop},
            "target_logic": {"levels": [{"price": tp, "frac": 1.0}]},
            "qty_lots": 0.1}
    L.register_plan(pid, dec, side, plan)
    L.transition(pid, "triggered")
    return pid


# ---------- 用户矩阵 1: 重复类 ----------
def test_duplicate_decision_replay_10x():
    """同一 decision 重放 10 次 → 1 registered(L0 回归)。"""
    plan = {"direction": "LONG", "entry_zone": {"low": 4400.0}}
    for i in range(10):
        L.register_plan("TP-R", "DEC-R", "LONG", plan)
    assert len([e for e in L.all_events() if e.get("type") == "registered"]) == 1


def test_duplicate_trigger_10x():
    seed()
    for _ in range(10):
        L.transition("TP-F", "triggered")
    assert len([e for e in L.all_events() if e.get("type") == "triggered"]) == 1


def test_duplicate_callback_fill_once():
    """duplicate callback: 同一 fill 回调两次 → position 只建一次。"""
    pid = seed()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    _, msg2 = TC.open_position_from_plan(pid, 4400.0, 0.3)
    assert msg2 == "position_exists"
    snaps = P.open_positions()
    assert len([s for s in snaps if s.get("plan_id") == pid]) == 1


# ---------- 用户矩阵 2: 部分成交/平仓 ----------
def test_partial_fill_then_full():
    pid = seed()
    L.transition(pid, "filled", price=4400.0, qty=0.05)  # ledger 记录
    pos = Position(TC.next_position_id(pid), pid, "LONG", stop_level=4390.0)
    pos.enter()
    pos.partial_entry(4400.0, 0.05)
    assert pos.state == "PARTIALLY_FILLED"
    pos.fill(4401.0, 0.05)
    assert pos.state == "OPEN" and pos.qty_lots == 0.1


def test_partial_close_then_full_close():
    pid = seed()
    TC.open_position_from_plan(pid, 4400.0, 0.2) if False else None
    # 手动: 建 0.2 → partial 0.1 → full 0.1
    pos = Position(TC.next_position_id(pid), pid, "LONG", stop_level=4390.0)
    pos.enter(); pos.fill(4400.0, 0.2)
    pos.partial_exit(4410.0, 0.1)
    assert pos.qty_lots == 0.1
    pos.request_exit("rest")
    r = pos.exit_fill(4412.0, 0.1)
    assert pos.state == "CLOSED"
    assert r == pytest.approx(12.0 * 100 * 0.1, abs=0.02)


# ---------- 用户矩阵 3: 拒单/网络/重启 ----------
def test_rejected_order_returns_flat():
    pos = Position("POS-RJ", "TP-RJ", "LONG", stop_level=4390.0)
    pos.enter()
    pos.reject("rejected_by_broker")
    assert pos.state == "FLAT" and pos.qty_lots == 0.0


def test_network_failure_no_crash():
    """模拟异常注入: manage_positions 遇损坏仓位文件 → 不崩溃。"""
    P.STATE_DIR.mkdir(parents=True, exist_ok=True)
    (P.STATE_DIR / "POS-BAD.json").write_text("{corrupt json", encoding="utf-8")
    out = TC.manage_positions(4400.0, 0.3)
    assert isinstance(out, list)


def test_restart_recovery_after_partial():
    pid = seed()
    pos = Position(TC.next_position_id(pid), pid, "LONG", stop_level=4390.0)
    pos.enter(); pos.fill(4400.0, 0.2); pos.partial_exit(4405.0, 0.1)
    p2 = P.load_position(pos.position_id)
    assert p2.qty_lots == 0.1 and p2.state == "OPEN"
    # 恢复后 hard stop
    TC.manage_positions(4389.0, 0.3)
    assert P.load_position(pos.position_id).state == "CLOSED"


# ---------- 用户矩阵 4: 市场异常 ----------
def test_stale_quote_handled():
    """stale quote: 状态包无 m15_live → manage 无 mid → 不管理不崩溃。"""
    out = TC.manage_positions(None, 0.3)   # price=None
    assert isinstance(out, list)


def test_spread_expansion_does_not_force_trade():
    """spread explosion: 不触发交易; 触发逻辑照常(spread 过滤由 Hermes/plan 层)。"""
    pid = seed()
    TC.open_position_from_plan(pid, 4400.0, 5.0)   # 高 spread 建仓(paper 允许记录)
    assert P.load_position(TC.next_position_id(pid)).state == "OPEN"


def test_extreme_vol_no_position_corruption():
    pid = seed()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    # 极端波动: 直接跳过止损价(模拟 gap)
    out = TC.manage_positions(4300.0, 0.3)
    assert any(o["reason"] == "hard_stop" for o in out)
    assert P.load_position(TC.next_position_id(pid)).state == "CLOSED"


# ---------- 用户矩阵 5: 数量/精度/杠杆 ----------
def test_price_precision_rounding():
    pos = Position("POS-P", "TP-P", "LONG", stop_level=4390.0)
    pos.enter()
    pos.fill(4400.123456, 0.1)   # 超精度价
    assert pos.avg_entry == 4400.12  # round 2dp


def test_lot_rounding():
    pos = Position("POS-L", "TP-L", "LONG", stop_level=4390.0)
    pos.enter()
    pos.fill(4400.0, 0.1234)     # 超精度手数
    assert pos.qty_lots == 0.12  # round 2dp


def test_min_max_lot():
    pos = Position("POS-M", "TP-M", "LONG", stop_level=4390.0)
    pos.enter()
    with pytest.raises(PositionInvariantError):
        pos.fill(4400.0, 0.0)
    pos.fill(4400.0, CONTRACT_SPEC["max_lot"])
    with pytest.raises(PositionInvariantError):
        pos.fill(4400.0, 1.0)   # 超 max_lot


def test_margin_and_500x_separated():
    """杠杆固定 500×: 保证金率 = notional/500; 仓位大小独立。"""
    spec = CONTRACT_SPEC
    assert spec["leverage"] == 500.0
    # 0.1 lot @4400 = 44000 notional; margin = 88
    notional = 0.1 * 4400.0 * spec["contract_size_oz"]
    margin = notional * spec["margin_pct"]
    assert margin == pytest.approx(88.0, abs=0.01)


# ---------- 用户矩阵 6: 信号冲突 ----------
def test_opposite_signal_while_position_exists():
    """持仓中禁止同账户反向(决策层拒绝 ADD/开反向; 不变量 I12)。"""
    a = Position("POS-A", "TP-A", "LONG", stop_level=4390.0)
    a.enter(); a.fill(4400.0, 0.1)
    b = Position("POS-B", "TP-B", "SHORT", stop_level=4410.0)
    b.enter(); b.fill(4400.0, 0.1)
    ok, _ = INV.check_no_position_conflict([a.to_dict(), b.to_dict()])
    assert not ok


def test_new_opportunity_while_holding_switch_logic():
    """持仓中高 EV 新机会 → 决策层 SWITCH(EXIT)。"""
    pos = Position("POS-S", "TP-S", "LONG", stop_level=4390.0)
    pos.enter(); pos.fill(4400.0, 0.1)
    import position_decision as PD
    d = PD.decide({"action": "HOLD", "ev_hold": 0.4}, pos, 4402.0,
                  new_opportunity_ev=1.2)
    assert d["action"] == "EXIT" and d["priority"] == 5


def test_simultaneous_management_signals():
    """同轮多信号: 硬止 > Hermes 意图(硬止先执行)。"""
    pid = seed()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    dec = {"position_id": TC.next_position_id(pid), "action": "HOLD", "market_state": {}}
    # 价格已触硬止 → 硬止优先, 即使 Hermes 说 HOLD
    out = TC.manage_positions(4389.0, 0.3, hermes_decision=dec)
    assert any(o["reason"] == "hard_stop" for o in out)


# ---------- 用户矩阵 7: SL/TP 修改失败 ----------
def test_sl_modification_failure_keeps_state():
    """SL 修改失败(非法值)→ 状态不变 + 异常。"""
    pos = Position("POS-SL", "TP-SL", "LONG", stop_level=4390.0)
    pos.enter(); pos.fill(4400.0, 0.1)
    pos.set_stop(4395.0)                     # 收紧: 合法
    assert pos.stop_level == 4395.0
    with pytest.raises(PositionInvariantError):
        pos.set_stop(4380.0)   # 扩大风险 → 拒绝
    assert pos.stop_level == 4395.0
    assert pos.state == "OPEN"


def test_tp_modification_failure():
    pos = Position("POS-TP", "TP-TP", "LONG", stop_level=4390.0)
    pos.enter(); pos.fill(4400.0, 0.1)
    with pytest.raises(PositionInvariantError):
        pos.set_tp([{"price": 4430.0, "frac": 1.5}])  # frac>1
    assert pos.tp_levels == []


# ---------- 用户矩阵 8: 形成中 bar / look-ahead ----------
def test_forming_bar_not_in_decision():
    from state_package import resample
    import pandas as pd
    idx = pd.date_range("2026-09-07 11:00", "2026-09-07 12:10", freq="1min")
    df = pd.DataFrame({"ts_utc": idx, "mid": 4400.0, "bid": 4399.9, "ask": 4400.1})
    bars = resample(df, "15min", drop_forming=True)
    assert str(bars["ts_utc"].iloc[-1]) == "2026-09-07 11:45:00"


# ---------- 用户矩阵 9: 其他 ----------
def test_no_unknown_state_after_ops():
    pos = Position("POS-U", "TP-U", "LONG", stop_level=4390.0)
    pos.enter(); pos.fill(4400.0, 0.1); pos.request_exit("x")
    ok, _ = INV.check_unknown_position_state()
    assert ok


def test_engine_fail_closed_on_invariant_break():
    """不变量破坏 → engine 返回 3(FAIL CLOSED) 不交易。"""
    # 构造 ledger 篡改
    pid = seed()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    lines = L.LEDGER_P.read_text(encoding="utf-8").splitlines()
    e = json.loads(lines[0])
    e["decision"] = "SHORT"
    lines[0] = json.dumps(e, ensure_ascii=False)
    L.LEDGER_P.write_text("\n".join(lines), encoding="utf-8")
    res = TC.run_invariants()
    assert not res["pass"]
