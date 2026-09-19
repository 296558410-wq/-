# -*- coding: utf-8 -*-
"""L0 测试: 幂等(H1/H2) + 计划状态机合法迁移 + 链完整性。
运行: cd C:\\AIQuant && .venv\\Scripts\\python.exe -m pytest research/hermes/trader_v1/tests/test_l0_idempotency.py -q
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import ledger as L

SAMPLE_PLAN = {"direction": "LONG", "entry_zone": {"low": 4400.0, "high": 4405.0},
               "stop_logic": {"level_price": 4392.0},
               "target_logic": {"levels": [{"price": 4435.0}]},
               "expected_net_EV": {"value": 0.5}}


@pytest.fixture()
def iso_ledger(tmp_path, monkeypatch):
    """每个测试用独立 ledger 文件(隔离)。"""
    p = tmp_path / "plan_ledger.jsonl"
    monkeypatch.setattr(L, "LEDGER_P", p)
    return p


def test_H1_duplicate_decision_replay(iso_ledger):
    """同一 decision 重放 10 次 → 只产生一个 registered。"""
    ev = None
    for i in range(10):
        ev, ok, reason = L.register_plan("TP-1", "DEC-A", "LONG", SAMPLE_PLAN)
        if i == 0:
            assert ok and reason == "ok"
        else:
            assert not ok and "dup_decision" in reason
    regs = [e for e in L.all_events() if e.get("type") == "registered"]
    assert len(regs) == 1
    assert L.verify()


def test_H1_same_plan_id_replay(iso_ledger):
    """同 plan_id 重试 → 拒绝。"""
    ev, ok, _ = L.register_plan("TP-9", "DEC-9", "LONG", SAMPLE_PLAN)
    assert ok
    ev2, ok2, reason2 = L.register_plan("TP-9", "DEC-10", "LONG", SAMPLE_PLAN)
    assert not ok2 and "dup_plan" in reason2
    assert len(L.all_events()) == 1


def test_H2_duplicate_trigger(iso_ledger):
    """触发条件保持满足, triggered 只能发生一次(终态前唯一)。"""
    L.register_plan("TP-2", "DEC-2", "LONG", SAMPLE_PLAN)
    ev1, ok1, _ = L.transition("TP-2", "triggered", risk_pass=True)
    assert ok1
    ev2, ok2, reason2 = L.transition("TP-2", "triggered", risk_pass=True)
    assert not ok2 and "illegal_transition" in reason2
    trigs = [e for e in L.all_events() if e.get("type") == "triggered"]
    assert len(trigs) == 1


def test_state_machine_full_flow(iso_ledger):
    """registered→triggered→filled→closed 合法链。"""
    L.register_plan("TP-3", "DEC-3", "LONG", SAMPLE_PLAN)
    assert L.plan_state("TP-3")["state"] == "registered"
    assert L.transition("TP-3", "triggered")[1]
    assert L.plan_state("TP-3")["state"] == "triggered"
    assert L.transition("TP-3", "filled", price=4402.0)[1]
    assert L.plan_state("TP-3")["state"] == "filled"
    assert L.transition("TP-3", "closed", exit_price=4430.0)[1]
    assert L.plan_state("TP-3")["state"] == "closed"
    assert L.verify()


def test_illegal_transitions(iso_ledger):
    """非法迁移全部拒绝: 未注册触发/直接 close/终态后迁移/跳过中间态。"""
    # 未注册就触发
    assert not L.transition("TP-X", "triggered")[1]
    L.register_plan("TP-4", "DEC-4", "LONG", SAMPLE_PLAN)
    # registered 直接 → closed 非法
    assert not L.transition("TP-4", "closed")[1]
    # registered → filled(跳过 triggered)非法
    assert not L.transition("TP-4", "filled")[1]
    # 合法 triggered → cancelled
    assert L.transition("TP-4", "triggered")[1]
    assert L.transition("TP-4", "cancelled", reason="test")[1]
    # cancelled 后再 closed 非法
    assert not L.transition("TP-4", "closed")[1]
    assert L.plan_state("TP-4")["state"] == "cancelled"
    assert L.verify()


def test_chain_integrity_detect_tamper(iso_ledger):
    """篡改中间事件 → verify False。"""
    L.register_plan("TP-5", "DEC-5", "LONG", SAMPLE_PLAN)
    L.transition("TP-5", "triggered")
    assert L.verify()
    # 篡改第一行
    lines = iso_ledger.read_text(encoding="utf-8").splitlines()
    e = json.loads(lines[0])
    e["plan"] = {"hacked": True}
    lines[0] = json.dumps(e, ensure_ascii=False)
    iso_ledger.write_text("\n".join(lines), encoding="utf-8")
    assert not L.verify()


def test_active_plans_excludes_terminated(iso_ledger):
    L.register_plan("TP-6", "DEC-6", "LONG", SAMPLE_PLAN)
    L.register_plan("TP-7", "DEC-7", "SHORT", SAMPLE_PLAN)
    L.transition("TP-6", "cancelled", reason="expired")
    act = [e["plan_id"] for e in L.active_plans()]
    assert act == ["TP-7"]
