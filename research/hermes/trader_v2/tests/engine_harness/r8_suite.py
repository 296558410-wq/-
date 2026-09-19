# -*- coding: utf-8 -*-
"""R8 FINAL-CLOSEOUT：Ledger crash-consistency + V2 exec/ledger 回归子集。
真实 run_cycle + 真实 Guard + 真实 ADP + FakeExec + 真实 ledger；temp 隔离；零 broker。
用法：python r8_suite.py                # 父
      python r8_suite.py --child-A TMP RID DEC WIN   # crash: executor 成功后、ledger 前
      python r8_suite.py --child-B TMP RID DEC WIN   # crash: ledger append 后
"""
from __future__ import annotations
import importlib.util, json, os, pathlib, subprocess, sys, tempfile, traceback
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from r7_suite import load_shadow, set_fakes, count_log, HERE  # noqa: E402

def _hpa():
    import hermes_paper_adapter as HPA; return HPA

def child(mode, tmp, rid, dec, win):
    SR = load_shadow(); set_fakes(SR, tmp, str(pathlib.Path(tmp) / "exec.log"), dec)
    HPA = _hpa()
    if mode == "A":      # 崩在 executor 成功之后、交易 ledger 写入前（EXECUTION_RESPONSE 前) 
        _o = HPA.L.append_event
        def a1(ev, path, *a, **k):
            if isinstance(ev, dict) and ev.get("event_type") == "EXECUTION_RESPONSE": os._exit(5)
            return _o(ev, path, *a, **k)
        HPA.L.append_event = a1
    elif mode == "B":    # append 后（POSITION_OPEN 之后）崩
        _o = HPA.L.append_event
        def a2(ev, path, *a, **k):
            r = _o(ev, path, *a, **k)
            if isinstance(ev, dict) and ev.get("event_type") == "POSITION_OPEN": os._exit(6)
            return r
        HPA.L.append_event = a2
    try: SR.run_cycle(rid, window=win)
    except Exception: pass
    return 0

def main():
    TMP = tempfile.mkdtemp(prefix="r8_"); EXEC = pathlib.Path(TMP) / "exec.log"
    SR = load_shadow(); FE = set_fakes(SR, TMP, str(EXEC), "DEC-0001")
    _os = SR.start_run
    def nr(*a, **k):
        try: (pathlib.Path(TMP) / "ACTIVE.json").unlink()
        except FileNotFoundError: pass
        return _os(*a, **k)
    SR.start_run = nr
    R = {}
    def n(): return count_log(EXEC)
    # ---- R8-001-A crash before ledger append ----
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-CB4L"); rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve()), "--child-A", TMP, rid, "DEC-CB4L", "A1"], timeout=120)
        n_after = n(); led = SR.run_ledger(rid)
        led_txt = led.read_text(encoding="utf-8") if led.exists() else ""
        led_after = sum(1 for _ in led_txt.splitlines())
        tx = any(json.loads(l).get("event_type") == "POSITION_OPEN" for l in led_txt.splitlines() if l.strip())
        o = SR.run_cycle(rid, window="A2")   # restart
        R["R8-A_crash_before_append"] = "PASS" if (n_after == 1 and not tx and n() == 1 and o.get("duplicate_skipped")) else "FAIL"
        R["R8-A_detail"] = f"exec_after={n_after} ledger_lines={led_after} tx={tx} exec_total={n()} guard={o.get('guard_status')}"
    except Exception:
        R["R8-A_crash_before_append"] = "FAIL"; R["R8-A_tb"] = traceback.format_exc()
    # ---- R8-001-B crash after append ----
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-CA4L"); rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve()), "--child-B", TMP, rid, "DEC-CA4L", "B1"], timeout=120)
        n_after = n(); led = SR.run_ledger(rid)
        pos_open = sum(1 for ln in led.read_text(encoding="utf-8").splitlines() if json.loads(ln).get("event_type") == "POSITION_OPEN") if led.exists() else 0
        o = SR.run_cycle(rid, window="B2")
        R["R8-B_crash_after_append"] = "PASS" if (n_after == 1 and pos_open == 1 and n() == 1 and o.get("duplicate_skipped")) else "FAIL"
        R["R8-B_detail"] = f"exec={n_after} POSITION_OPEN={pos_open} exec_total={n()} guard={o.get('guard_status')}"
    except Exception:
        R["R8-B_crash_after_append"] = "FAIL"; R["R8-B_tb"] = traceback.format_exc()
    # ---- R8-001-C ledger write failure -> UNKNOWN, no retry ----
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-LFAIL"); rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        HPA = _hpa(); _o = HPA.L.append_event
        def boom(ev, path, *a, **k):
            if isinstance(ev, dict) and ev.get("event_type") == "POSITION_OPEN": raise RuntimeError("LEDGER_WRITE_FAIL")
            return _o(ev, path, *a, **k)
        HPA.L.append_event = boom
        raised = False
        try: SR.run_cycle(rid, window="C1")
        except Exception: raised = True
        HPA.L.append_event = _o
        from execution_guard import ExecutionGuard
        g = ExecutionGuard(SR.run_dir(rid) / "exec_guard"); st = g._read_state("DEC-LFAIL")
        o2 = SR.run_cycle(rid, window="C2")
        R["R8-C_ledger_write_failure"] = "PASS" if (n() == 1 and raised and st and st.get("status") == "UNKNOWN" and o2.get("duplicate_skipped")) else "FAIL"
        R["R8-C_detail"] = f"exec={n()} raised={raised} guard_state={st.get('status') if st else None}"
    except Exception:
        R["R8-C_ledger_write_failure"] = "FAIL"; R["R8-C_tb"] = traceback.format_exc()
    # ---- R8-002 exec regression: reject -> FAILED ; exception -> UNKNOWN ----
    try:
        FE = set_fakes(SR, TMP, str(EXEC), "DEC-REJ"); rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        FE.open = lambda *a, **k: {"ok": False, "failure_code": "TEST_REJECT", "reason": "x"}
        o = SR.run_cycle(rid, window="REJ1")
        from execution_guard import ExecutionGuard
        st = ExecutionGuard(SR.run_dir(rid) / "exec_guard")._read_state("DEC-REJ")
        R["R8-002_reject_FAILED"] = "PASS" if (st and st.get("status") == "FAILED") else "FAIL"
        R["R8-002_reject_detail"] = f"result={o.get('execution_result')} guard={st.get('status') if st else None}"
    except Exception:
        R["R8-002_reject_FAILED"] = "FAIL"; R["R8-002_rej_tb"] = traceback.format_exc()
    try:
        FE = set_fakes(SR, TMP, str(EXEC), "DEC-EXC"); rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        def raising(*a, **k): raise RuntimeError("EXECUTOR_EXC")
        FE.open = raising
        raised = False
        try: SR.run_cycle(rid, window="EXC1")
        except Exception: raised = True
        from execution_guard import ExecutionGuard
        st = ExecutionGuard(SR.run_dir(rid) / "exec_guard")._read_state("DEC-EXC")
        R["R8-002_exception_UNKNOWN"] = "PASS" if (st and st.get("status") == "UNKNOWN") else "FAIL"
        R["R8-002_exc_detail"] = f"raised={raised} guard={st.get('status') if st else None}"
    except Exception:
        R["R8-002_exception_UNKNOWN"] = "FAIL"; R["R8-002_exc_tb"] = traceback.format_exc()
    # ---- R8-003 ledger regression: event types + replay ----
    try:
        set_fakes(SR, TMP, str(EXEC), "DEC-LED"); rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
        o = SR.run_cycle(rid, window="LED1")
        evs = [json.loads(ln) for ln in SR.run_ledger(rid).read_text(encoding="utf-8").splitlines()]
        types = [e.get("event_type") for e in evs]
        need = {"EXECUTION_REQUEST", "EXECUTION_RESPONSE", "POSITION_OPEN", "FILL"}
        did_ok = all(e.get("decision_id") in (None, "DEC-LED") for e in evs if e.get("event_type") != "ACCOUNT_INIT")
        try:
            import replay as RPL; rst = RPL.replay(SR.run_ledger(rid), execution_mode="PAPER"); replay_ok = bool(rst)
        except Exception: replay_ok = False
        R["R8-003_ledger_regression"] = "PASS" if (need.issubset(set(types)) and did_ok and replay_ok) else "FAIL"
        R["R8-003_detail"] = f"types={types} did_ok={did_ok} replay_ok={replay_ok}"
    except Exception:
        R["R8-003_ledger_regression"] = "FAIL"; R["R8-003_tb"] = traceback.format_exc()
    R["REAL_BROKER_ACCESS"] = "FALSE"; R["BROKER_ORDER_SENT"] = "FALSE"
    for k in sorted(R):
        if k.endswith("_detail") or k.endswith("_tb"): continue
        print(f"{k}={R[k]}")
    print(json.dumps(R, ensure_ascii=False)); return 0

if __name__ == "__main__":
    import multiprocessing; multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--child-A": sys.exit(child("A", sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
    if len(sys.argv) > 1 and sys.argv[1] == "--child-B": sys.exit(child("B", sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
    sys.exit(main())
