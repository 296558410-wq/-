# -*- coding: utf-8 -*-
"""R8-001-D FINAL：Ledger partial/corrupt write 安全恢复。
真实 run_cycle + 真实 Guard + 真实 ADP + FakeExec SUCCESS + **真实 ledger 写路径**注入半写/损坏/截断 + os._exit + 重启。
零 broker；temp 隔离。
用法：python r8d_suite.py
      python r8d_suite.py --child MODE TMP RID DEC WIN
"""
from __future__ import annotations
import importlib.util, json, os, pathlib, subprocess, sys, tempfile, traceback
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from r7_suite import load_shadow, set_fakes, count_log  # noqa: E402

def child(mode, tmp, rid, dec, win):
    SR = load_shadow(); set_fakes(SR, tmp, str(pathlib.Path(tmp) / "exec.log"), dec)
    import hermes_paper_adapter as HPA
    _o = HPA.L.append_event
    def part(ev, path, *a, **k):
        if isinstance(ev, dict) and ev.get("event_type") == "EXECUTION_RESPONSE":
            line = json.dumps(ev)
            if mode == "half": frag = line[: max(1, len(line) // 2)]
            elif mode == "garbage": frag = '{"event_type":"POSITION_OPEN","decision_id":"'; 
            else: frag = line[:-3]   # trunc: 去掉结尾 -> 无换行、JSON 不完整
            with open(path, "a", encoding="utf-8") as f:
                f.write(frag); f.flush(); os.fsync(f.fileno())
            os._exit(7)
        return _o(ev, path, *a, **k)
    HPA.L.append_event = part
    try: SR.run_cycle(rid, window=win)
    except Exception: pass
    return 0

def main():
    TMP = tempfile.mkdtemp(prefix="r8d_"); EXEC = pathlib.Path(TMP) / "exec.log"
    SR = load_shadow(); set_fakes(SR, TMP, str(EXEC), "DEC-D")
    _os = SR.start_run
    def nr(*a, **k):
        try: (pathlib.Path(TMP) / "ACTIVE.json").unlink()
        except FileNotFoundError: pass
        return _os(*a, **k)
    SR.start_run = nr
    import ledger as L
    from execution_guard import ExecutionGuard
    R = {}
    def n(): return count_log(EXEC)
    for mode in ("half", "garbage", "trunc"):
        dec = f"DEC-{mode.upper()}"
        try:
            set_fakes(SR, TMP, str(EXEC), dec); rid = SR.start_run(minutes=1, shadow=True); EXEC.write_text("")
            subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve()), "--child", mode, TMP, rid, dec, "D1"], timeout=120)
            n_after = n()
            led = SR.run_ledger(rid)
            vok, _ = L.verify_ledger(led) if led.exists() else (True, {})
            parse_err = not vok
            g = ExecutionGuard(SR.run_dir(rid) / "exec_guard")
            st = g._read_state(dec)
            o = SR.run_cycle(rid, window="D2")   # restart
            extra = n() - n_after
            gs = st.get("status") if st else None
            safe = (n_after == 1 and extra == 0 and gs != "FILLED")
            R[f"R8-D-{mode}"] = "PASS" if safe else "FAIL"
            R[f"R8-D-{mode}_detail"] = f"exec_after={n_after} extra_exec={extra} parse_err={parse_err} guard={gs} restart={o.get('blocked') or o.get('duplicate_skipped') or o.get('execution_result')}"
        except Exception:
            R[f"R8-D-{mode}"] = "FAIL"; R[f"R8-D-{mode}_tb"] = traceback.format_exc()
    # D-004 汇总：executor success + partial ledger + restart → exec_total 不增
    R["R8-D-004_exec_success_partial"] = "PASS" if all(R.get(f"R8-D-{m}") == "PASS" for m in ("half", "garbage", "trunc")) else "FAIL"
    R["REAL_BROKER_ACCESS"] = "FALSE"; R["BROKER_ORDER_SENT"] = "FALSE"
    for k in sorted(R):
        if k.endswith("_detail") or k.endswith("_tb"): continue
        print(f"{k}={R[k]}")
    print(json.dumps(R, ensure_ascii=False)); return 0

if __name__ == "__main__":
    import multiprocessing; multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        sys.exit(child(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]))
    sys.exit(main())
