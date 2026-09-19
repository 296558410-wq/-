# -*- coding: utf-8 -*-
"""R7 引擎级执行安全回归套件（REPAIR-007 STAGE4B-REMAINDER）。
真实 run_cycle + 真实 ExecutionGuard + 真实 ADP.process + FakeExec + 真实 ledger。
零 broker；temp 隔离；跨进程/崩溃用真实 subprocess。
用法：python r7_suite.py                  # 父：跑全部
      python r7_suite.py --child TMP RID DEC WIN   # 子：单次 run_cycle
"""
from __future__ import annotations
import importlib.util, json, os, pathlib, subprocess, sys, tempfile, threading, types, traceback

HERE = pathlib.Path(__file__).resolve()
V2 = HERE.parents[2]

def load_shadow():
    for sub in ("agents/technical", "agents/macro_global", "hermes", "execution", "ledger", "runtime", "data_sources", ""):
        sys.path.insert(0, str(V2 / sub))
    for name, attr in (("broker_demo_executor", "BrokerDemoExecutor"), ("paper_executor", "PaperExecutor")):
        m = types.ModuleType(name); setattr(m, attr, type(attr, (), {"backend": "fake", "__init__": lambda self, cfg: None}))
        sys.modules[name] = m
    SR = importlib.util.module_from_spec(importlib.util.spec_from_file_location("shadow_run", str(V2 / "runtime" / "shadow_run.py")))
    importlib.util.spec_from_file_location("shadow_run", str(V2 / "runtime" / "shadow_run.py")).loader.exec_module(SR)
    return SR

def set_fakes(SR, tmp, exec_log, dec_id):
    SR.run_dir = lambda rid: pathlib.Path(tmp) / str(rid)
    SR.ACTIVE = pathlib.Path(tmp) / "ACTIVE.json"
    if hasattr(SR, "START_LOCK"): SR.START_LOCK = pathlib.Path(tmp) / ".start_run.lock"
    if hasattr(SR, "state_path"): SR.state_path = lambda rid: pathlib.Path(tmp) / f"state_{rid}.json"
    SR.PS = None
    class FakeExec:
        backend = "paper_local"; acc = {"initial_balance": 10000.0, "currency": "USD"}
        def __init__(self): self.calls = []
        def account(self): return {"balance": 10000.0, "equity": 10000.0, "positions": [], "closed_trades": [], "margin_free": 10000.0, "realized_pnl": 0.0}
        def _log(self, kind):
            with open(exec_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"kind": kind, "dec": dec_id, "pid": os.getpid()}) + "\n"); f.flush(); os.fsync(f.fileno())
        def open(self, side, mid, sl, tp, **kw):
            self.calls.append({"side": side, "mid": mid, **kw}); self._log("open")
            return {"ok": True, "position": {"position_id": "POS-TEST-1", "entry": mid, "qty_lots": kw.get("qty_lots", 0.01), "latency_ms": 1}}
        def close(self, *a, **k): self._log("close"); return {"ok": True, "trade": {}}
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
            return ({"decision": "TRADE", "decision_id": dec_id, "ts": "2026-09-19T00:00:00+00:00",
                     "plan": {"direction": "LONG", "qty_lots": 0.01, "entry": 4300.0, "stop_loss": 4290.0, "take_profit": 4320.0, "confidence": 0.6}, "reason": "fixture"},
                    {"context_id": "ctx-test", "context_hash": "HASH-TEST", "market": {"primary_last": 4300.0, "retrieval_ts": "2026-09-19T00:00:00+00:00"}}, [], [])
    SR.A1 = FA1; SR.A2 = FA2; SR.HERMES = FH
    if hasattr(SR, "hermes"): SR.hermes = FH
    return FE

def count_log(p):
    p = pathlib.Path(p); return sum(1 for _ in p.open(encoding="utf-8")) if p.exists() else 0

def child_main(tmp, rid, dec, win):
    SR = load_shadow(); set_fakes(SR, tmp, str(pathlib.Path(tmp) / "exec.log"), dec)
    try: SR.run_cycle(rid, window=win)
    except Exception: pass
    return 0

# ---------------- parent suite ----------------
def main():
    TMP = tempfile.mkdtemp(prefix="r7_")
    EXEC = pathlib.Path(TMP) / "exec.log"
    SR = load_shadow(); FE = set_fakes(SR, TMP, str(EXEC), "TEST-DECISION-0001")
    _orig_start = SR.start_run
    def _new_run(*a, **k):
        try: (pathlib.Path(TMP) / "ACTIVE.json").unlink()
        except FileNotFoundError: pass
        return _orig_start(*a, **k)
    SR.start_run = _new_run
    R = {}
    def n(): return count_log(EXEC)
    # R7-001 single
    try:
        rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        o = SR.run_cycle(rid, window="W1")
        R["R7-001_single"] = "PASS" if (o.get("execution_result") == "EXECUTED" and n() == 1) else "FAIL"
        R["single_dec_id"] = o.get("decision_id"); R["single_ledger"] = sum(1 for _ in SR.run_ledger(rid).open(encoding="utf-8"))
    except Exception:
        R["R7-001_single"] = "FAIL"; R["single_tb"] = traceback.format_exc()
    # R7-002 x10 / R7-003 x100 (same dec_id, distinct windows)
    for k, m in (("R7-002_x10", 10), ("R7-003_x100", 100)):
        try:
            rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
            for i in range(m): SR.run_cycle(rid, window=f"{k}-{i}")
            R[k] = "PASS" if n() == 1 else "FAIL"
        except Exception:
            R[k] = "FAIL"; R[k + "_tb"] = traceback.format_exc()
    # R7-004 TOCTOU 20 threads same dec_id
    try:
        rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        ts = [threading.Thread(target=lambda i=i: SR.run_cycle(rid, window=f"T{i}")) for i in range(20)]
        [t.start() for t in ts]; [t.join() for t in ts]
        R["R7-004_toctou20"] = "PASS" if n() == 1 else "FAIL"
    except Exception:
        R["R7-004_toctou20"] = "FAIL"; R["R7-004_tb"] = traceback.format_exc()
    # R7-007 different decisions A/B/C
    try:
        rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        for j, dec in enumerate(["DEC-A", "DEC-B", "DEC-C"]):
            set_fakes(SR, TMP, str(EXEC), dec); SR.run_cycle(rid, window=f"DIFF-{j}")
        R["R7-007_diff_dec"] = "PASS" if n() == 3 else "FAIL"
    except Exception:
        R["R7-007_diff_dec"] = "FAIL"; R["R7-007_tb"] = traceback.format_exc()
    # R7-005/006 cross-process 8 / 10 (shared run, distinct windows)
    for k, m in (("R7-005_cross8", 8), ("R7-006_cross10", 10)):
        try:
            set_fakes(SR, TMP, str(EXEC), "TEST-DECISION-CROSSPROC")
            rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
            ps = [subprocess.Popen([sys.executable, str(HERE), "--child", TMP, rid, "TEST-DECISION-CROSSPROC", f"{k}-{i}"]) for i in range(m)]
            [p.wait(timeout=120) for p in ps]
            R[k] = "PASS" if n() == 1 else "FAIL"
        except Exception:
            R[k] = "FAIL"; R[k + "_tb"] = traceback.format_exc()
    # R7-008 crash BEFORE executor (child dies at ADP.process entry, after claim+EXECUTING)
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-CRASHB"); SR_orig = SR.ADP.process
        def boom(*a, **k): os._exit(3)
        rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        # child: patch ADP.process -> exit; guard claims+EXECUTING first
        code = ("import sys;sys.argv=['x','--child-crashb','%s','%s','DEC-CRASHB','WB'];" % (TMP, rid))
        subprocess.run([sys.executable, str(HERE), "--child-crashb", TMP, rid, "DEC-CRASHB", "WB"], timeout=120)
        n_before = n()
        SR.ADP.process = SR_orig
        o = SR.run_cycle(rid, window="WB2")   # restart: must NOT execute
        R["R7-008_crash_before"] = "PASS" if (n_before == 0 and n() == 0 and o.get("duplicate_skipped")) else "FAIL"
        R["R7-008_guard_status"] = o.get("guard_status")
    except Exception:
        R["R7-008_crash_before"] = "FAIL"; R["R7-008_tb"] = traceback.format_exc()
    # R7-009 crash AFTER executor (child executes then dies before returning)
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-CRASHA")
        rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        subprocess.run([sys.executable, str(HERE), "--child-crasha", TMP, rid, "DEC-CRASHA", "WA"], timeout=120)
        n_after_crash = n()
        o = SR.run_cycle(rid, window="WA2")   # restart: must NOT execute again
        R["R7-009_crash_after"] = "PASS" if (n_after_crash == 1 and n() == 1 and o.get("duplicate_skipped")) else "FAIL"
        R["R7-009_exec_total"] = n()
    except Exception:
        R["R7-009_crash_after"] = "FAIL"; R["R7-009_tb"] = traceback.format_exc()
    # R7-011 scheduler re-entry (two overlapping cycles, same dec, distinct windows, via threads already covered; explicit 2)
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-REENTRY")
        rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        t1 = threading.Thread(target=lambda: SR.run_cycle(rid, window="RE-a")); t2 = threading.Thread(target=lambda: SR.run_cycle(rid, window="RE-b"))
        t1.start(); t2.start(); t1.join(); t2.join()
        R["R7-011_sched_reentry"] = "PASS" if n() == 1 else "FAIL"
    except Exception:
        R["R7-011_sched_reentry"] = "FAIL"; R["R7-011_tb"] = traceback.format_exc()
    # R7-013 ledger idempotency (guard.ledger_append_once: same dec+event → 1; different event → 2)
    try:
        from execution_guard import ExecutionGuard
        lp = pathlib.Path(TMP) / "idem.jsonl"; g = ExecutionGuard(pathlib.Path(TMP) / "g_idem")
        for _ in range(100): g.ledger_append_once(lp, "DEC-IDEM", {"event_type": "POSITION_OPEN", "position_id": "P1"})
        first = sum(1 for _ in lp.open(encoding="utf-8"))
        g.ledger_append_once(lp, "DEC-IDEM", {"event_type": "POSITION_CLOSE", "position_id": "P1"})
        second = sum(1 for _ in lp.open(encoding="utf-8"))
        R["R7-013_ledger_idem"] = "PASS" if (first == 1 and second == 2) else "FAIL"
    except Exception:
        R["R7-013_ledger_idem"] = "FAIL"; R["R7-013_tb"] = traceback.format_exc()
    # R7-014 UNKNOWN no auto-retry
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-UNK")
        rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        from execution_guard import ExecutionGuard
        g = ExecutionGuard(SR.run_dir(rid) / "exec_guard"); g.claim("DEC-UNK"); g.transition("DEC-UNK", "EXECUTING"); g.transition("DEC-UNK", "UNKNOWN", result="t")
        o = SR.run_cycle(rid, window="UNK1")
        R["R7-014_unknown_safe"] = "PASS" if (n() == 0 and o.get("duplicate_skipped")) else "FAIL"
    except Exception:
        R["R7-014_unknown_safe"] = "FAIL"; R["R7-014_tb"] = traceback.format_exc()
    # R7-021 decision_id scope: same dec_id in two different runs
    try:
        EXEC.write_text("")
        set_fakes(SR, TMP, str(EXEC), "DEC-SCOPE")
        r1 = SR.start_run(minutes=1, shadow=True); SR.run_cycle(r1, window="S1")
        r2 = SR.start_run(minutes=1, shadow=True); SR.run_cycle(r2, window="S2")
        R["R7-021_scope"] = "PER_RUN" if n() == 2 else ("GLOBAL" if n() == 1 else "DATA_GAP")
    except Exception:
        R["R7-021_scope"] = "DATA_GAP"; R["R7-021_tb"] = traceback.format_exc()
    R["REAL_BROKER_ACCESS"] = "FALSE"; R["BROKER_ORDER_SENT"] = "FALSE"
    for k in sorted(R):
        if k.endswith(("_tb", "_dec_id", "_ledger", "_status", "_total", "_scope")):
            continue
        print(f"{k}={R[k]}")
    print("DECISION_ID_SCOPE=" + str(R.get("R7-021_scope", "DATA_GAP")))
    print(json.dumps(R, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    import multiprocessing; multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        sys.exit(child_main(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
    if len(sys.argv) > 1 and sys.argv[1] == "--child-crashb":
        SR = load_shadow(); set_fakes(SR, sys.argv[2], str(pathlib.Path(sys.argv[2]) / "exec.log"), sys.argv[4])
        SR.ADP.process = lambda *a, **k: os._exit(3)     # crash before executor
        try: SR.run_cycle(sys.argv[3], window=sys.argv[5])
        except Exception: pass
        os._exit(3)
    if len(sys.argv) > 1 and sys.argv[1] == "--child-crasha":
        SR = load_shadow(); FE2 = set_fakes(SR, sys.argv[2], str(pathlib.Path(sys.argv[2]) / "exec.log"), sys.argv[4])
        _orig = SR.ADP.process
        def after(*a, **k):
            r = _orig(*a, **k)      # real execute + ledger
            os._exit(4)             # crash after executor, before return
        SR.ADP.process = after
        try: SR.run_cycle(sys.argv[3], window=sys.argv[5])
        except Exception: pass
        os._exit(4)
    sys.exit(main())
