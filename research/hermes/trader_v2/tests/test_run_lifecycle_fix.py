# -*- coding: utf-8 -*-
"""REPAIR-006 回归：run 生命周期/并发/原子写（纯 mock，临时目录，零 broker）。
覆盖 R6-001 单次 start_run、R6-002 并发 start_run、R6-012 原子写（防半写）。
用法: python tests/test_run_lifecycle_fix.py   （打印 RESULT n/n PASS，退出码 0/1）
"""
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile, threading, types

V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("agents/technical", "agents/macro_global", "hermes", "execution", "ledger", "runtime", "data_sources", ""):
    sys.path.insert(0, os.path.join(V2, sub))

# fake executors → 避免任何真实 broker/MT5 副作用
for name, attr in (("broker_demo_executor", "BrokerDemoExecutor"), ("paper_executor", "PaperExecutor")):
    m = types.ModuleType(name)
    setattr(m, attr, type(attr, (), {"backend": "x", "__init__": lambda self, cfg: None, "_fresh": lambda self: {}}))
    sys.modules[name] = m

SR = importlib.util.module_from_spec(importlib.util.spec_from_file_location("shadow_run", os.path.join(V2, "runtime", "shadow_run.py")))
importlib.util.spec_from_file_location("shadow_run", os.path.join(V2, "runtime", "shadow_run.py")).loader.exec_module(SR)

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} | {name} | {detail}")

TMP = tempfile.mkdtemp(prefix="r6_")
SR.run_dir = lambda rid: pathlib.Path(TMP) / str(rid)
SR.ACTIVE = pathlib.Path(TMP) / "ACTIVE.json"
SR.START_LOCK = pathlib.Path(TMP) / ".start_run.lock"
SR.state_path = lambda rid: pathlib.Path(TMP) / f"state_{rid}.json"

# R6-001 单次 start_run
try:
    rid = SR.start_run(minutes=1440, shadow=False)
    check("R6-001 single start_run", rid.startswith("V2-PAPER-") and (pathlib.Path(TMP) / str(rid)).exists(), rid)
except Exception as e:
    check("R6-001 single start_run", False, f"{type(e).__name__}:{e}")

# 清理 ACTIVE 以便并发测试从干净态开始
try: SR.ACTIVE.unlink()
except FileNotFoundError: pass
for d in os.listdir(TMP):
    p = os.path.join(TMP, d)
    if os.path.isdir(p):
        import shutil; shutil.rmtree(p, ignore_errors=True)

# R6-002 并发 start_run（应序列化：1 成功 + 1 REFUSE，或至少不产生两个有效 ACTIVE / 不损坏）
outcomes = []
bar = threading.Barrier(2)
def w(i):
    bar.wait()
    try:
        r = SR.start_run(minutes=1440, shadow=False); outcomes.append(("OK", r))
    except Exception as e:
        outcomes.append(("REFUSE" if "REFUSE" in str(e) else "ERR", f"{type(e).__name__}:{e}"))
t1 = threading.Thread(target=w, args=(1,)); t2 = threading.Thread(target=w, args=(2,))
t1.start(); t2.start(); t1.join(); t2.join()
ok_ct = sum(1 for o in outcomes if o[0] == "OK")
dirs = [d for d in os.listdir(TMP) if d.startswith("V2-")]
active_ok = False; active_rid = None
try:
    a = json.load(open(SR.ACTIVE, encoding="utf-8")); active_ok = True; active_rid = a.get("run_id")
except Exception:
    active_ok = False
check("R6-002 concurrent start_run: no 2 valid ACTIVE", ok_ct <= 1 and len(dirs) <= 1 and active_ok,
      f"ok={ok_ct} refuse={sum(1 for o in outcomes if o[0]=='REFUSE')} run_dirs={len(dirs)} json_ok={active_ok} active={active_rid}")

# R6-012 原子写：# 顺序高频写 + 每次读回校验 + 无 .tmp 残留（os.replace 原子性）
try:
    tgt = pathlib.Path(TMP) / "hammer.json"
    bad = 0
    for i in range(300):
        SR._write(tgt, {"n": i, "pad": "x" * 2000})
        try:
            json.load(open(tgt, encoding="utf-8"))
        except Exception:
            bad += 1
    leftovers = [p for p in os.listdir(TMP) if ".tmp." in p]
    check("R6-012 atomic write (no partial JSON)", bad == 0 and not leftovers,
          f"corrupt_reads={bad}/300 leftover_tmp={len(leftovers)}")
except Exception as e:
    check("R6-012 atomic write (no partial JSON)", False, f"{type(e).__name__}:{e}")

n = len(results); good = sum(1 for _, ok, _ in results if ok)
print(f"=== RESULT: {good}/{n} PASS ===")
sys.exit(0 if good == n else 1)
