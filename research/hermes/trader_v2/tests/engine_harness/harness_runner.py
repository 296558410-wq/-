# -*- coding: utf-8 -*-
"""engine_harness.harness_runner — 稳定、可重复、可诊断的引擎级 Harness。
- 以**子进程**运行 worker.py，捕获 stdout/stderr/exit/timeout（解决“空输出不可诊断”）。
- 结构化：harness_result.json；失败分类 IMPORT/ENGINE/HARNESS/TIMEOUT/ASSERTION/UNEXPECTED。
- 支持 --mode single|concurrent --workers N --runs N（确定性）。
零 broker：worker 内 fake executor + temp 隔离。
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, "worker.py")
PY = sys.executable
MARKERS = ("HARNESS_START", "RUN_ID", "DECISION_ID", "TRADE_REACHED", "EXECUTOR_CALLS", "LEDGER_EVENTS", "EXIT_CODE", "HARNESS_RESULT")


def parse_markers(out):
    d = {}
    for ln in out.splitlines():
        for m in MARKERS:
            if ln.startswith(m + "="):
                d[m] = ln.split("=", 1)[1].strip()
    return d


def run_one(idx):
    art = tempfile.mkdtemp(prefix=f"eharness_{idx}_")
    t0 = time.time()
    try:
        p = subprocess.run([PY, WORKER], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, cwd=art)
        rc, out, err, timeout = p.returncode, p.stdout or "", p.stderr or "", False
    except subprocess.TimeoutExpired as e:
        rc, out, err, timeout = None, (e.stdout or ""), (e.stderr or ""), True
    dur = round(time.time() - t0, 2)
    mk = parse_markers(out or "")
    failure_type = None
    if timeout:
        failure_type = "TIMEOUT"
    elif not (out or "").strip() and not (err or "").strip():
        failure_type = "ENVIRONMENT_FAILURE"
    elif "Traceback" in (err or "") and not mk.get("RUN_ID"):
        failure_type = "UNEXPECTED_EXCEPTION"
    elif rc not in (0, None):
        failure_type = "ENGINE_FAILURE"
    res = {"idx": idx, "rc": rc, "timeout": timeout, "duration_s": dur, "markers": mk,
           "failure_type": failure_type, "stdout_tail": (out or "")[-500:], "stderr_tail": (err or "")[-500:],
           "artifact_dir": art}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--mode", choices=["single", "concurrent"], default="single")
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    if a.mode == "concurrent":
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            results = list(ex.map(run_one, range(a.workers)))
    else:
        results = [run_one(i) for i in range(a.runs)]
    stable = all(r["failure_type"] is None and r["markers"].get("RUN_ID") for r in results)
    determinism = len({(r["markers"].get("RUN_ID") is not None, r["rc"], r["failure_type"]) for r in results}) <= 1 if a.mode == "single" else None
    summary = {"harness_version": "engine_harness/1", "mode": a.mode, "workers_or_runs": a.workers if a.mode == "concurrent" else a.runs,
               "results": results, "all_reached_run_id": stable, "determinism_stable": determinism,
               "result": "PASS" if stable else "FAIL"}
    out_path = os.path.join(HERE, "harness_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(f"HARNESS_RUNNER mode={a.mode} n={summary['workers_or_runs']} all_reached_run_id={stable} determinism={determinism} result={summary['result']}")
    for r in results:
        print(f"  #{r['idx']} rc={r['rc']} dur={r['duration_s']}s run_id={r['markers'].get('RUN_ID')} trade={r['markers'].get('TRADE_REACHED')} failure={r['failure_type']}")
    print("WROTE", out_path)
    return 0 if stable else 1


if __name__ == "__main__":
    sys.exit(main())
