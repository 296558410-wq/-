# -*- coding: utf-8 -*-
"""L3 测试: 不变量引擎 + 机会漏斗 + 蜡烛图 Context 纪律。
运行: .venv\\Scripts\\python.exe -m pytest research/hermes/trader_v1/tests/test_l3_invariants.py -q
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import position as P  # noqa: E402
import ledger as L  # noqa: E402
import invariants as INV  # noqa: E402
import opportunity as OPP  # noqa: E402
from position import Position  # noqa: E402


@pytest.fixture(autouse=True)
def iso(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "STATE_DIR", tmp_path / "positions")
    monkeypatch.setattr(L, "LEDGER_P", tmp_path / "plan_ledger.jsonl")
    monkeypatch.setattr(OPP, "LEDGER_P", tmp_path / "plan_ledger.jsonl")
    monkeypatch.setattr(OPP, "RUN", tmp_path)


def test_invariant_conflicting_positions():
    a = Position("PA", "TA", "LONG", stop_level=4390.0)
    a.enter(); a.fill(4400.0, 0.1)
    b = Position("PB", "TB", "SHORT", stop_level=4410.0)
    b.enter(); b.fill(4400.0, 0.1)
    snaps = [a.to_dict(), b.to_dict()]
    ok, _ = INV.check_no_position_conflict(snaps)
    assert not ok
    # 只留一个 → pass
    ok2, _ = INV.check_no_position_conflict([a.to_dict()])
    assert ok2


def test_invariant_illegal_sl_tp():
    a = Position("PA", "TA", "LONG", stop_level=4405.0)  # SL > 未来 entry → 非法
    a.enter(); a.fill(4400.0, 0.1)
    ok, detail = INV.check_sl_tp_legal([a.to_dict()])
    assert not ok and "4405" in detail


def test_invariant_closed_with_qty():
    a = Position("PA", "TA", "LONG", stop_level=4390.0)
    a.enter(); a.fill(4400.0, 0.1)
    a.request_exit("x")
    # 模拟异常: CLOSED 但 qty 残留(篡改)
    snap = a.to_dict()
    snap["state"] = "CLOSED"
    snap["qty_lots"] = 0.1
    ok, detail = INV.check_no_duplicate_close()
    # 先持久化被篡改快照
    P.STATE_DIR.mkdir(parents=True, exist_ok=True)
    (P.STATE_DIR / "PA.json").write_text(json.dumps(snap), encoding="utf-8")
    ok, detail = INV.check_no_duplicate_close()
    assert not ok


def test_invariant_ledger_chain():
    # 空 ledger → pass
    ok, _ = INV.check_ledger_chain()
    assert ok
    # 写入 + 篡改 → fail(直接测 ledger.verify)
    L.register_plan("T1", "D1", "LONG", {"direction": "LONG"})
    assert L.verify()
    lines = (L.LEDGER_P.read_text(encoding="utf-8")).splitlines()
    e = json.loads(lines[0])
    e["decision"] = "SHORT"
    lines[0] = json.dumps(e, ensure_ascii=False)
    L.LEDGER_P.write_text("\n".join(lines), encoding="utf-8")
    assert not L.verify()


def test_invariant_no_future_data():
    # 未来 bar → fail
    pkg = {"market_state": {"m15": {"last_bar": "2026-09-09T00:00:00+00:00"}}}
    ok, _ = INV.check_no_future_data(pkg)
    assert not ok
    ok2, _ = INV.check_no_future_data(None)
    assert ok2


def test_check_all_aggregate():
    res = INV.check_all()
    assert "pass" in res and "failed" in res and "results" in res


def test_funnel_empty_is_honest():
    f = OPP.funnel(24)
    assert f["m15_windows"] >= 0
    assert f["executed_trades"] >= 0


def test_frequency_study_insufficient_data():
    """无/极少样本 → INSUFFICIENT_DATA(诚实, 不硬凑 NOT_SUPPORTED)。"""
    s = OPP.daily_frequency_study()
    assert s["verdict"] == "INSUFFICIENT_DATA"


def test_frequency_study_computes_from_samples():
    # 模拟 12 笔 closed: 55% 胜率, 平均赢 1.2R 输 0.8R → 支持频率判定逻辑运行
    evs = []
    for i in range(12):
        won = i % 2 == 0 or i == 1
        evs.append({"type": "closed", "plan_id": f"T{i}", "payload": {
            "realized_R": 1.2 if (i % 3 != 0) else -0.8}})
    s = OPP.daily_frequency_study(plans_log=evs)
    assert s["verdict"] in ("SUPPORTED", "NOT_SUPPORTED")
    assert s["n_samples"] == 12
    assert 3 in s["frequencies"]
