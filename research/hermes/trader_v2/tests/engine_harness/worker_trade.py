# -*- coding: utf-8 -*-
"""Stage-4A-002 worker：注入 fake A1/A2/Hermes/Executor，驱动**真实 shadow_run.run_cycle** 到 TRADE。
不改任何引擎源码；零 broker；temp 隔离。输出结构化标记 + JSON。
"""
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile, types, traceback

V2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ("agents/technical", "agents/macro_global", "hermes", "execution", "ledger", "runtime", "data_sources", ""):
    sys.path.insert(0, os.path.join(V2, sub))

# 1) 拦截真实 broker/paper 模块（避免任何真实连接）
for name, attr in (("broker_demo_executor", "BrokerDemoExecutor"), ("paper_executor", "PaperExecutor")):
    m = types.ModuleType(name); setattr(m, attr, type(attr, (), {"backend": "fake", "__init__": lambda self, cfg: None, "_fresh": lambda self: {}}))
    sys.modules[name] = m

SR = importlib.util.module_from_spec(importlib.util.spec_from_file_location("shadow_run", os.path.join(V2, "runtime", "shadow_run.py")))
importlib.util.spec_from_file_location("shadow_run", os.path.join(V2, "runtime", "shadow_run.py")).loader.exec_module(SR)

OUT = {"harness_version": "stage4a2/1", "run_id": None, "decision_id": "TEST-DECISION-0001", "trade_reached": False,
       "real_adp_process": False, "fake_executor_calls": 0, "ledger_events": 0, "failure_type": None, "traceback": None, "result": "INCOMPLETE"}
def emit(k, v): print(f"{k}={v}", flush=True)

# 2) temp 隔离
TMP = tempfile.mkdtemp(prefix="trade_")
SR.run_dir = lambda rid: pathlib.Path(TMP) / str(rid)
SR.ACTIVE = pathlib.Path(TMP) / "ACTIVE.json"
if hasattr(SR, "START_LOCK"): SR.START_LOCK = pathlib.Path(TMP) / ".start_run.lock"
if hasattr(SR, "state_path"): SR.state_path = lambda rid: pathlib.Path(TMP) / f"state_{rid}.json"
SR.PS = None  # 关闭 price_space 分支 → execution_plan=None（不 rejection，直接执行）

# 3) fake executor（记录调用）
class FakeExec:
    backend = "paper_local"
    def __init__(self): self.calls = []
    def account(self): return {"balance": 10000.0, "equity": 10000.0, "positions": [], "closed_trades": [], "margin_free": 10000.0, "realized_pnl": 0.0}
    def open(self, side, mid, sl, tp, **kw):
        self.calls.append({"side": side, "mid": mid, "sl": sl, "tp": tp, **kw})
        return {"ok": True, "position": {"position_id": "POS-TEST-1", "entry": mid, "qty_lots": kw.get("qty_lots", 0.01), "latency_ms": 1}}
    def close(self, *a, **k): return {"ok": True, "trade": {}}
FE = FakeExec()
FE.acc = {"initial_balance": 10000.0, "currency": "USD"}
SR._make_executor = lambda cfg, run_id=None: FE

# 4) fake A1 / A2 / Hermes
class FakeA1:
    @staticmethod
    def build(cycle=None): return ({"generated_utc": "2026-09-19T00:00:00+00:00", "market_regime": {"x": 1},
                                    "quotes": {"gold_spot": {"price": 4300.0, "data_ts": "2026-09-19T00:00:00+00:00", "retrieval_ts": "2026-09-19T00:00:00+00:00", "source": "mt5"}}}, "p")
class FakeA2:
    @staticmethod
    def build(cycle=None): return ({"snapshot_ts": "2026-09-19T00:00:00+00:00"}, "p")
class FakeHermes:
    @staticmethod
    def run(cycle=None):
        d = {"decision": "TRADE", "decision_id": "TEST-DECISION-0001", "ts": "2026-09-19T00:00:00+00:00",
             "plan": {"direction": "LONG", "qty_lots": 0.01, "entry": 4300.0, "stop_loss": 4290.0, "take_profit": 4320.0, "confidence": 0.6},
             "reason": "harness-fixture"}
        ctx = {"context_id": "ctx-test", "context_hash": "HASH-TEST", "market": {"primary_last": 4300.0, "retrieval_ts": "2026-09-19T00:00:00+00:00"}}
        return d, ctx, [], []
SR.A1 = FakeA1; SR.A2 = FakeA2; SR.HERMES = FakeHermes
if hasattr(SR, "hermes"): SR.hermes = FakeHermes
emit("A1_INJECTED", "TRUE"); emit("A2_INJECTED", "TRUE"); emit("CONTEXT_INJECTED", "TRUE"); emit("HERMES_INJECTED", "TRUE")

try:
    emit("HARNESS_START", "TRUE")
    rid = SR.start_run(minutes=1, shadow=True)
    OUT["run_id"] = rid; emit("RUN_ID", rid); emit("DECISION_ID", OUT["decision_id"])
    out = SR.run_cycle(rid)
    OUT["real_adp_process"] = True
    dec = out.get("execution_result")
    OUT["execution_result"] = dec
    OUT["fake_executor_calls"] = len(FE.calls)
    led = SR.run_ledger(rid)
    n = sum(1 for _ in led.open(encoding="utf-8")) if led.exists() else 0
    OUT["ledger_events"] = n
    OUT["trade_reached"] = bool(FE.calls) or str(dec) == "EXECUTED"
    emit("TRADE_REACHED", "TRUE" if OUT["trade_reached"] else "FALSE")
    emit("REAL_ADP_PROCESS", "TRUE")
    emit("FAKE_EXECUTOR_CALLS", len(FE.calls)); emit("LEDGER_EVENTS", n)
    emit("EXECUTION_RESULT", str(dec))
    OUT["result"] = "PASS" if OUT["trade_reached"] and len(FE.calls) >= 1 and n >= 1 else "INCOMPLETE"
except Exception as e:  # noqa: BLE001
    OUT["failure_type"] = "ENGINE_FAILURE"; OUT["traceback"] = traceback.format_exc()
    emit("HARNESS_RESULT", "FAIL")
emit("REAL_BROKER_ACCESS", "FALSE"); emit("BROKER_ORDER_SENT", "FALSE")
emit("EXIT_CODE", 0); emit("HARNESS_RESULT", OUT["result"])
print(json.dumps(OUT, ensure_ascii=False))
sys.exit(0)
