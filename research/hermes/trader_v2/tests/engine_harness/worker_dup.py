# -*- coding: utf-8 -*-
"""Stage-4B dup 验证：同一 decision_id、不同 window，两次真实 run_cycle → 真实 Guard 去重。
不改引擎；temp 隔离；FakeExecutor 计数。"""
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile, types, traceback
V2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("agents/technical", "agents/macro_global", "hermes", "execution", "ledger", "runtime", "data_sources", ""):
    sys.path.insert(0, os.path.join(V2, sub))
for name, attr in (("broker_demo_executor", "BrokerDemoExecutor"), ("paper_executor", "PaperExecutor")):
    m = types.ModuleType(name); setattr(m, attr, type(attr, (), {"backend": "fake", "__init__": lambda self, cfg: None}))
    sys.modules[name] = m
SR = importlib.util.module_from_spec(importlib.util.spec_from_file_location("shadow_run", os.path.join(V2, "runtime", "shadow_run.py")))
importlib.util.spec_from_file_location("shadow_run", os.path.join(V2, "runtime", "shadow_run.py")).loader.exec_module(SR)
TMP = tempfile.mkdtemp(prefix="dup_")
SR.run_dir = lambda rid: pathlib.Path(TMP) / str(rid)
SR.ACTIVE = pathlib.Path(TMP) / "ACTIVE.json"
if hasattr(SR, "START_LOCK"): SR.START_LOCK = pathlib.Path(TMP) / ".start_run.lock"
if hasattr(SR, "state_path"): SR.state_path = lambda rid: pathlib.Path(TMP) / f"state_{rid}.json"
SR.PS = None
class FakeExec:
    backend = "paper_local"
    acc = {"initial_balance": 10000.0, "currency": "USD"}
    def __init__(self): self.calls = []
    def account(self): return {"balance": 10000.0, "equity": 10000.0, "positions": [], "closed_trades": [], "margin_free": 10000.0, "realized_pnl": 0.0}
    def open(self, side, mid, sl, tp, **kw):
        self.calls.append({"side": side, "mid": mid, **kw})
        return {"ok": True, "position": {"position_id": "POS-TEST-1", "entry": mid, "qty_lots": kw.get("qty_lots", 0.01), "latency_ms": 1}}
    def close(self, *a, **k): return {"ok": True, "trade": {}}
FE = FakeExec(); SR._make_executor = lambda cfg, run_id=None: FE
class FA1:
    @staticmethod
    def build(cycle=None): return ({"generated_utc": "2026-09-19T00:00:00+00:00", "market_regime": {"x": 1}, "quotes": {"gold_spot": {"price": 4300.0, "data_ts": "2026-09-19T00:00:00+00:00", "retrieval_ts": "2026-09-19T00:00:00+00:00", "source": "mt5"}}}, "p")
class FA2:
    @staticmethod
    def build(cycle=None): return ({"snapshot_ts": "2026-09-19T00:00:00+00:00"}, "p")
class FH:
    @staticmethod
    def run(cycle=None):
        return ({"decision": "TRADE", "decision_id": "TEST-DECISION-0001", "ts": "2026-09-19T00:00:00+00:00",
                 "plan": {"direction": "LONG", "qty_lots": 0.01, "entry": 4300.0, "stop_loss": 4290.0, "take_profit": 4320.0, "confidence": 0.6}, "reason": "fixture"},
                {"context_id": "ctx-test", "context_hash": "HASH-TEST", "market": {"primary_last": 4300.0, "retrieval_ts": "2026-09-19T00:00:00+00:00"}}, [], [])
SR.A1 = FA1; SR.A2 = FA2; SR.HERMES = FH
if hasattr(SR, "hermes"): SR.hermes = FH
R = {}
try:
    rid = SR.start_run(minutes=1, shadow=True)
    o1 = SR.run_cycle(rid, window="WIN-A")
    c1 = len(FE.calls)
    o2 = SR.run_cycle(rid, window="WIN-B")   # 同 decision_id，不同 window → 绕引擎去重，走 Guard
    c2 = len(FE.calls)
    R = {"run_id": rid, "cycle1": o1.get("execution_result"), "dup_skipped": bool(o2.get("duplicate_skipped")),
         "guard_status": o2.get("guard_status"), "executor_calls_after1": c1, "executor_calls_after2": c2,
         "result": "PASS" if (c1 == 1 and c2 == 1 and o2.get("duplicate_skipped")) else "FAIL"}
except Exception:
    R = {"result": "FAIL", "traceback": traceback.format_exc()}
print("DUP_EXECUTOR_CALLS_AFTER_1=" + str(R.get("executor_calls_after1")))
print("DUP_EXECUTOR_CALLS_AFTER_2=" + str(R.get("executor_calls_after2")))
print("DUPLICATE_SKIPPED=" + str(R.get("dup_skipped")))
print("GUARD_STATUS=" + str(R.get("guard_status")))
print("DUP_TEST_RESULT=" + str(R.get("result")))
print("REAL_BROKER_ACCESS=FALSE"); print("BROKER_ORDER_SENT=FALSE")
print(json.dumps(R, ensure_ascii=False))
sys.exit(0)
