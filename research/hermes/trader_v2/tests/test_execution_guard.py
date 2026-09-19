# -*- coding: utf-8 -*-
"""REPAIR-007 回归：执行幂等 + 状态机 + ledger 幂等（真实模块/文件系统；fake executor；零 broker）。
覆盖 R6B-001/003/004/005(跨进程)/007/009/010/011/012 + SAME_DECISION_X100 + DIFFERENT_DECISION。
用法: python tests/test_execution_guard.py
"""
from __future__ import annotations
import importlib.util, json, multiprocessing as mp, os, pathlib, sys, tempfile, threading

V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(V2, "execution")); sys.path.insert(0, os.path.join(V2, "runtime"))
_spec = importlib.util.spec_from_file_location("execution_guard", os.path.join(V2, "execution", "execution_guard.py"))
EG = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(EG)

R = []
def check(name, ok, detail=""):
    R.append(bool(ok)); print(f"{'PASS' if ok else 'FAIL'} | {name} | {detail}")

def _mp_worker(base, did, q):
    g = EG.ExecutionGuard(base); q.put(g.claim(did))

def _mp_transition(base, did, target, q):
    try:
        q.put(EG.ExecutionGuard(base).transition(did, target))
    except Exception:  # noqa: BLE001
        q.put(False)

def main():
    B = tempfile.mkdtemp(prefix="eg1_")
    g = EG.ExecutionGuard(B)
    ok, st = g.claim("DEC-001"); g.transition("DEC-001", "EXECUTING")
    wrote = g.ledger_append_once(pathlib.Path(B) / "ledger.jsonl", "DEC-001", {"status": "FILLED"})
    filled = g.transition("DEC-001", "FILLED", result={"qty": 0.01})
    n = len((pathlib.Path(B) / "ledger.jsonl").read_text(encoding="utf-8").strip().splitlines())
    check("R6B-001 single decision", ok and wrote and filled and g._read_state("DEC-001")["status"] == "FILLED" and n == 1, f"ledger={n}")

    for label, cnt in (("R6B-003 duplicate x10", 10), ("R6B-004 TOCTOU(threads)", 20), ("SAME_DECISION_X100", 100)):
        Bn = tempfile.mkdtemp(prefix="egn_"); gg = EG.ExecutionGuard(Bn); out = []; bar = threading.Barrier(cnt)
        def w(i, gg=gg, out=out, bar=bar):
            bar.wait(); out.append(gg.claim("DEC-X")[0])
        ts = [threading.Thread(target=w, args=(i,)) for i in range(cnt)]
        [t.start() for t in ts]; [t.join() for t in ts]
        check(f"{label} -> exactly 1 claim", sum(1 for o in out if o) == 1, f"claimed={sum(1 for o in out if o)}/{cnt}")

    try:
        B5 = tempfile.mkdtemp(prefix="eg5_"); q = mp.Queue(); ps = [mp.Process(target=_mp_worker, args=(B5, "DEC-MP", q)) for _ in range(8)]
        [p.start() for p in ps]; [p.join() for p in ps]
        res = [q.get() for _ in ps]
        check("R6B-005 cross-process -> exactly 1 claim", sum(1 for ok, _ in res if ok) == 1, f"claimed={sum(1 for ok, _ in res if ok)}/{len(ps)}")
    except Exception as e:  # noqa: BLE001
        check("R6B-005 cross-process -> exactly 1 claim", False, f"{type(e).__name__}:{e}")

    B7 = tempfile.mkdtemp(prefix="eg7_"); EG.ExecutionGuard(B7).claim("DEC-C7")
    check("R6B-007 crash-before-executor (no re-execute)", EG.ExecutionGuard(B7).can_execute("DEC-C7") is False, "can_execute=False")

    B9 = tempfile.mkdtemp(prefix="eg9_"); g9 = EG.ExecutionGuard(B9)
    g9.claim("DEC-U"); g9.transition("DEC-U", "EXECUTING")
    ok_u = g9.transition("DEC-U", "UNKNOWN"); bad = g9.transition("DEC-U", "FILLED")
    check("R6B-009/010 UNKNOWN + no auto-retry", ok_u and bad is False and g9.can_execute("DEC-U") is False, f"unknown={ok_u} retry_rejected={bad is False}")

    B11 = tempfile.mkdtemp(prefix="eg11_"); g11 = EG.ExecutionGuard(B11)
    g11.claim("DEC-R"); g11.transition("DEC-R", "EXECUTING"); g11.transition("DEC-R", "UNKNOWN")
    check("R6B-011 reconciliation", g11.transition("DEC-R", "RECONCILIATION") and g11.transition("DEC-R", "FILLED"), "")

    B12 = tempfile.mkdtemp(prefix="eg12_"); g12 = EG.ExecutionGuard(B12); L = pathlib.Path(B12) / "ledger.jsonl"
    w = sum(1 for _ in range(10) if g12.ledger_append_once(L, "DEC-L", {"status": "FILLED"}))
    check("R6B-012 ledger idempotency", w == 1 and len(L.read_text(encoding="utf-8").strip().splitlines()) == 1, f"writes={w}")

    # R6B-008 ledger crash-consistency：账本已有记录但 marker 缺失（模拟 append 后 crash）→ 不得重复
    B8 = tempfile.mkdtemp(prefix="eg8_"); g8 = EG.ExecutionGuard(B8); L8 = pathlib.Path(B8) / "ledger.jsonl"
    L8.write_text(json.dumps({"decision_id": "DEC-C8", "status": "FILLED"}) + "\n", encoding="utf-8")
    dup = g8.ledger_append_once(L8, "DEC-C8", {"status": "FILLED"})
    n8 = len(L8.read_text(encoding="utf-8").strip().splitlines())
    check("R6B-008 ledger crash-consistency (no dup after crash)", dup is False and n8 == 1, f"wrote={dup} lines={n8}")

    # R6B-004b 跨进程状态迁移（防后写覆盖）：两进程从 EXECUTING 迁移不同目标 → 仅 1 成功
    try:
        Bc = tempfile.mkdtemp(prefix="egc_"); g0 = EG.ExecutionGuard(Bc); g0.claim("DEC-C4"); g0.transition("DEC-C4", "EXECUTING")
        q2 = mp.Queue()
        p1 = mp.Process(target=_mp_transition, args=(Bc, "DEC-C4", "UNKNOWN", q2))
        p2 = mp.Process(target=_mp_transition, args=(Bc, "DEC-C4", "FAILED", q2))
        [p.start() for p in (p1, p2)]; [p.join() for p in (p1, p2)]
        res2 = [q2.get() for _ in (p1, p2)]
        check("R6B-004b cross-process transition (single winner)", sum(1 for r in res2 if r) == 1, f"succeeded={sum(1 for r in res2 if r)}/2")
    except Exception as e:  # noqa: BLE001
        check("R6B-004b cross-process transition (single winner)", False, f"{type(e).__name__}:{e}")

    Bd = tempfile.mkdtemp(prefix="egd_"); gd = EG.ExecutionGuard(Bd)
    check("DIFFERENT decisions independent", all(gd.claim(f"DEC-{i:03d}")[0] for i in range(5)), "")

    good = sum(1 for x in R if x); n = len(R)
    print(f"=== RESULT: {good}/{n} PASS ===")
    return 0 if good == n else 1

if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())
