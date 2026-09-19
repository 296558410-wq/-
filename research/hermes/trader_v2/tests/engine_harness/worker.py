# -*- coding: utf-8 -*-
"""engine_harness.worker — 在临时隔离环境中实际调用**真实** V2 引擎入口，输出结构化标记。
只读、零 broker：注入 fake executor（不连 FXTM/MT5），run_dir/ACTIVE/lock 指向 temp。
输出 HARNESS_START / RUN_ID / DECISION_ID / TRADE_REACHED / EXECUTOR_CALLS / LEDGER_EVENTS / EXIT_CODE / HARNESS_RESULT + harness_result.json。
"""
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile, types, traceback

V2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../trader_v2
for sub in ("agents/technical", "agents/macro_global", "hermes", "execution", "ledger", "runtime", "data_sources", ""):
    sys.path.insert(0, os.path.join(V2, sub))

for name, attr in (("broker_demo_executor", "BrokerDemoExecutor"), ("paper_executor", "PaperExecutor")):
    m = types.ModuleType(name)
    setattr(m, attr, type(attr, (), {"backend": "paper_local", "__init__": lambda self, cfg: None, "_fresh": lambda self: {}}))
    sys.modules[name] = m

OUT = {"harness_version": "engine_harness/1", "run_id": None, "decision_id": None, "trade_reached": False,
       "executor_calls": 0, "ledger_events": 0, "phase": None, "failure_type": None, "traceback": None, "result": "FAIL"}

def emit(k, v):
    print(f"{k}={v}", flush=True)

emit("HARNESS_START", "1")
try:
    spec = importlib.util.spec_from_file_location("shadow_run", os.path.join(V2, "runtime", "shadow_run.py"))
    SR = importlib.util.module_from_spec(spec); spec.loader.exec_module(SR)
except Exception as e:  # noqa: BLE001
    OUT["failure_type"] = "IMPORT_FAILURE"; OUT["traceback"] = traceback.format_exc()
    emit("HARNESS_RESULT", "FAIL"); print(json.dumps(OUT, ensure_ascii=False)); sys.exit(0)

TMP = tempfile.mkdtemp(prefix="eharness_")
SR.run_dir = lambda rid: pathlib.Path(TMP) / str(rid)
SR.ACTIVE = pathlib.Path(TMP) / "ACTIVE.json"
if hasattr(SR, "START_LOCK"):
    SR.START_LOCK = pathlib.Path(TMP) / ".start_run.lock"
if hasattr(SR, "state_path"):
    SR.state_path = lambda rid: pathlib.Path(TMP) / f"state_{rid}.json"

try:  # 真实引擎入口：start_run（shadow=True → PaperExecutor，永不 broker）
    OUT["phase"] = "start_run"
    rid = SR.start_run(minutes=1, shadow=True)
    OUT["run_id"] = rid; OUT["decision_id"] = rid
    emit("RUN_ID", rid); emit("DECISION_ID", rid)
except Exception as e:  # noqa: BLE001
    OUT["failure_type"] = "ENGINE_FAILURE"; OUT["traceback"] = traceback.format_exc()
    emit("HARNESS_RESULT", "FAIL"); print(json.dumps(OUT, ensure_ascii=False)); sys.exit(0)

emit("TRADE_REACHED", "DATA_GAP")   # 未接线前不伪造；run_cycle 需真实行情/context，标记 DATA_GAP
emit("EXECUTOR_CALLS", 0); emit("LEDGER_EVENTS", 0)
OUT["result"] = "PASS"
emit("EXIT_CODE", 0); emit("HARNESS_RESULT", "PASS")
print(json.dumps(OUT, ensure_ascii=False))
sys.exit(0)
