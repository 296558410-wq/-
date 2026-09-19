# -*- coding: utf-8 -*-
"""Full Integration 测试: trader_core 端到端 — 触发→建仓→硬止→管理→平仓→review→invariant。
运行: .venv\\Scripts\\python.exe -m pytest research/hermes/trader_v1/tests/test_integration.py -q
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
from position import Position  # noqa: E402


@pytest.fixture(autouse=True)
def iso(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "LEDGER_P", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(P, "STATE_DIR", tmp_path / "positions")
    monkeypatch.setattr(TC, "RUN", tmp_path)
    # review 目录隔离
    monkeypatch.setattr(RV, "REVIEW_DIR", tmp_path / "reviews")
    return tmp_path


def seed_plan(pid="TP-1", side="LONG", stop=4390.0, tp=4430.0, decision_id="D1"):
    plan = {"direction": side,
            "entry_zone": {"low": 4400.0, "high": 4405.0},
            "stop_logic": {"level_price": stop},
            "target_logic": {"levels": [{"price": tp, "frac": 1.0}]},
            "qty_lots": 0.1}
    L.register_plan(pid, decision_id, side, plan)
    L.transition(pid, "triggered", matched="test")
    return pid


def test_full_trade_flow_open_to_hard_stop():
    pid = seed_plan()
    # 触发后建仓
    pos, msg = TC.open_position_from_plan(pid, 4400.0, 0.3)
    assert msg == "ok" and pos.state == "OPEN"
    assert pos.qty_lots == 0.1
    # ledger 已迁移 filled
    assert L.plan_state(pid)["state"] == "filled"
    # 重复建仓幂等
    pos2, msg2 = TC.open_position_from_plan(pid, 4400.0, 0.3)
    assert msg2 == "position_exists"
    # 价格触止损 → 平仓 + review
    out = TC.manage_positions(4390.0, 0.3)
    assert out and out[0]["action"] == "EXIT" and out[0]["reason"] == "hard_stop"
    assert L.plan_state(pid)["state"] == "closed"
    # review 已生成
    rvs = list((RV.REVIEW_DIR).glob("RV-*.json"))
    assert len(rvs) == 1


def test_hard_tp_full_exit():
    pid = seed_plan()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    out = TC.manage_positions(4430.0, 0.3)
    assert out[0]["reason"] == "hard_tp"
    assert L.plan_state(pid)["state"] == "closed"


def test_position_marked_each_cycle():
    pid = seed_plan()
    pos, _ = TC.open_position_from_plan(pid, 4400.0, 0.3)
    TC.manage_positions(4410.0, 0.3)   # 浮盈, 无触发
    p2 = P.load_position(pos.position_id)
    assert p2.mfe == 10.0
    assert p2.state == "OPEN"


def test_hermes_decision_exit_via_core():
    pid = seed_plan()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    dec = {"position_id": f"POS-{pid.replace('TP-','')}", "action": "EXIT",
           "thesis_status": "invalidated", "market_state": {}, "confidence": 0.9}
    out = TC.manage_positions(4402.0, 0.3, hermes_decision=dec)
    assert any(o["action"] == "EXIT" for o in out)
    assert L.plan_state(pid)["state"] == "closed"


def test_invariant_run_each_cycle():
    res = TC.run_invariants()
    assert "pass" in res and isinstance(res["failed"], list)


def test_restart_recovery_position_still_managed():
    """模拟: 建仓 → '重启'(重新 load) → 硬止仍触发。"""
    pid = seed_plan()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    # 重启: 新进程从磁盘恢复
    pos2 = P.load_position(TC.next_position_id(pid))
    assert pos2 is not None and pos2.state == "OPEN"
    out = TC.manage_positions(4389.0, 0.3)
    assert any(o["reason"] == "hard_stop" for o in out)


def test_no_duplicate_close_across_cycles():
    pid = seed_plan()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    TC.manage_positions(4390.0, 0.3)   # 触硬止 → closed
    # 下一轮: 该仓位不再被管理(CLOSED 排除)
    out = TC.manage_positions(4380.0, 0.3)
    assert out == []
    # ledger: closed 后不再有事件
    assert L.plan_state(pid)["state"] == "closed"


def test_ledger_chain_intact_after_full_flow():
    pid = seed_plan()
    TC.open_position_from_plan(pid, 4400.0, 0.3)
    TC.manage_positions(4390.0, 0.3)
    assert L.verify()
