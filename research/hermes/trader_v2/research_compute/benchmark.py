# -*- coding: utf-8 -*-
"""research_compute.benchmark — V2 研究计算基准（wall-clock 为准）。

记录: CPU 时间 / GPU kernel / GPU end-to-end / speedup / VRAM peak / numerical error。
区分 kernel-only 与 end-to-end（**不得把 kernel speedup 当真实研究加速**）。
输出: research/GPU_V2_BENCHMARK.md + research_compute/gpu_v2_results.json
"""
from __future__ import annotations

import json, os, time
from datetime import datetime, timezone

import numpy as np

from . import cpu_backend as CB, gpu_backend as GB

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.abspath(os.path.join(HERE, "..", "research"))
SIZES = [1_000_000, 5_000_000, 10_000_000, 20_000_000, 50_000_000, 100_000_000]


def _time(fn, repeat=1):
    best = None
    for _ in range(repeat):
        t0 = time.perf_counter(); fn(); dt = (time.perf_counter() - t0) * 1000
        best = dt if best is None else min(best, dt)
    return best


def run(quick=False):
    sizes = SIZES[:3] if quick else SIZES
    rng = np.random.default_rng(42)
    rows = []
    print("GPU available:", GB.available(), GB.device_name() if GB.available() else "")
    if GB.available():  # 预热：排除 CUDA 上下文冷启动
        try:
            for _ in range(2):
                GB.run("rolling_std", rng.standard_normal(100_000), 30)
        except Exception:
            pass
    for n in sizes:
        print(f"\n=== n={n:,} ===")
        x = rng.standard_normal(n)
        bid = x + 4000.0; ask = bid + 0.3
        ts = np.sort(rng.integers(0, max(n, 1) * 100, size=n)).astype(np.int64)
        xs = x[:min(n, 200_000)]      # 重采样样本上限（控内存）
        ys = rng.standard_normal(len(xs))
        NIT = 1000                    # 重采样次数

        # rolling_std
        cpu = _time(lambda: CB.run("rolling_std", x, 60)) if n <= 20_000_000 else float("nan")
        # AUTO 只在 3M–40M 用 GPU 滚动（超出走 CPU）；基准只测 AUTO 可用区间
        g = (_t(GB.run("rolling_std", x, 60)) if (GB.available() and 3_000_000 <= n <= 40_000_000)
             else (float("nan"), 0.0, None))
        rows.append(_row("rolling_std", n, cpu, *g))
        # microbar
        cpu = _time(lambda: CB.run("microbar", ts, bid, ask, 60000)) if n <= 20_000_000 else float("nan")
        g = (_t(GB.run("microbar", ts, bid, ask, 60000)) if (GB.available() and n <= 40_000_000)
             else (float("nan"), 0.0, None))
        rows.append(_row("microbar", n, cpu, *g))
        # monte_carlo (n_paths=n, 64 steps)
        cpu = _time(lambda: CB.run("monte_carlo", n_paths=n, n_steps=64, seed=42)) if n <= 1_000_000 else float("nan")
        g = _t(GB.run("monte_carlo", n_paths=n, n_steps=64, seed=42)) if GB.available() else (float("nan"), 0, None)
        rows.append(_row("monte_carlo", n, cpu, *g))
        # bootstrap
        cpu = _time(lambda: CB.run("bootstrap", xs, stat="mean", n_iter=NIT, seed=42))
        g = _t(GB.run("bootstrap", xs, stat="mean", n_iter=NIT, seed=42)) if GB.available() else (float("nan"), 0, None)
        rows.append(_row("bootstrap", len(xs), cpu, *g))
        # permutation (AUTO=CPU：GPU argsort 重且更慢 → 不测 GPU)
        cpu = _time(lambda: CB.run("permutation_diff", xs, ys, stat="mean", n_iter=NIT, seed=42))
        rows.append(_row("permutation", len(xs), cpu, float("nan"), 0.0, None))

    json.dump(rows, open(os.path.join(HERE, "gpu_v2_results.json"), "w", encoding="utf-8"), indent=1)
    _write_md(rows)
    return rows


def _t(call):
    try:
        res, ms, peak = call
        return ms, peak, None
    except Exception as e:  # noqa: BLE001
        return float("nan"), 0.0, str(e)[:80]


def _row(op, n, cpu, gpu, peak, err):
    sp = cpu / gpu if (cpu == cpu and gpu == gpu and gpu > 0) else float("nan")
    r = {"op": op, "n": n,
         "cpu_ms": None if cpu != cpu else round(cpu, 2),
         "gpu_e2e_ms": None if gpu != gpu else round(gpu, 2),
         "speedup": None if sp != sp else round(sp, 2),
         "vram_peak_mb": round(peak, 1), "error": err}
    print(f"  {op:14s} cpu={cpu:9.2f} gpu_e2e={gpu:9.2f} speedup={sp:5.2f} peak={r['vram_peak_mb']}")
    return r


def _write_md(rows):
    md = ["# GPU_V2_BENCHMARK — V2 研究计算基准", "",
          f"- 时间(UTC): {datetime.now(timezone.utc).isoformat()}",
          f"- GPU: {GB.device_name() if GB.available() else 'unavailable'}",
          "- 口径: wall-clock（best-of-2）；**end-to-end**（含 H2D/D2H）。kernel-only 见 gpu_accelerator/REPORT.md。", "",
          "| op | n | cpu_ms | gpu_e2e_ms | speedup | vram_peak_mb |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['op']} | {r['n']:,} | {r['cpu_ms']} | {r['gpu_e2e_ms']} | {r['speedup']} | {r['vram_peak_mb']} |")
    open(os.path.join(RESEARCH, "GPU_V2_BENCHMARK.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")


if __name__ == "__main__":
    import sys
    run(quick="--quick" in sys.argv)
