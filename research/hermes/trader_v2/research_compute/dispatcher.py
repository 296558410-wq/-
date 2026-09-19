# -*- coding: utf-8 -*-
"""research_compute.dispatcher — V2 研究计算调度（AUTO / CPU / GPU）。

只做"研究计算"，**不进入交易执行/风控链**；结果必须经 CPU 独立验证后才可交给 Hermes。
AUTO 依据任务种类 + 规模 + 已验证 benchmark 阈值选择 CPU/GPU；GPU OOM/失败 → 释放→缩块→重试→CPU 回退。
"""
from __future__ import annotations

import time

from . import cpu_backend as CB, gpu_backend as GB
from . import chunking
from .validation import compare, assert_valid, ComputeValidationError

# ---- AUTO 阈值（来自 gpu_accelerator benchmark + 本任务 GPU_V2_BENCHMARK；可随基准更新）----
TH = {
    "rolling_gpu_min_n": 15_000_000,    # 滚动类：<15M 走 CPU（实测 5–10M GPU 仅 0.6–0.7x，CPU 更快）
    "rolling_gpu_max_n": 40_000_000,    # 滚动类：>40M 走 CPU（避免 WDDM paging，未分块）
    "elem_gpu_min_n": 2_000_000,        # elementwise(microbar/quotes/returns/rv/features)
    "elem_gpu_max_n": 40_000_000,       # elementwise 上限（>40M 走 CPU，避免显存越界）
    "resample_min_work": 100_000_000,   # 重采样：n_iter×n ≥ 1e8 走 GPU（否则 CPU 启动开销占优）
}

# op 注册表: name -> (cpu_op, kind, category, bytes_per_item, factor)
OPS = {
    # P0
    "bootstrap":        ("bootstrap",        "statistical", "resample", 8, 1),
    "permutation":      ("permutation_diff", "statistical", "resample", 8, 1),
    "monte_carlo":      ("monte_carlo",      "statistical", "resample", 4, 3),
    "rolling_std":      ("rolling_std",      "elementwise", "rolling",  4, 5),
    "rolling_mean":     ("rolling_mean",     "elementwise", "rolling",  4, 5),
    # P1
    "microbar":         ("microbar",         "elementwise", "elem",     8, 5),
    "realized_vol":     ("realized_volatility", "elementwise", "elem",  8, 4),
    "spread_stats":     ("quotes",           "elementwise", "elem",     8, 4),
    "returns":          ("returns",          "elementwise", "elem",     8, 3),
    "features":         ("features",         "elementwise", "elem",     8, 4),
}

DECISIONS = []   # 审计日志（每次 compute 一条）


def _n_of(args, kw):
    if "n_items" in kw and kw["n_items"] is not None:
        return int(kw["n_items"])
    import numpy as np
    for a in args:
        try:
            s = np.asarray(a).size
            if s > 0:
                return int(s)
        except Exception:
            pass
    return 0


def decide(op: str, n: int, n_iter: int = 0, backend: str = "auto") -> tuple[str, str]:
    if op not in OPS:
        return "cpu", f"op {op} 未注册(默认 CPU)"
    if backend == "cpu":
        return "cpu", "forced=cpu"
    if not GB.available() or not GB.has(OPS[op][0]):
        return "cpu", "CUDA 不可用 / GPU 无此算子"
    if backend == "gpu":
        return "gpu", "forced=gpu"
    cat = OPS[op][2]
    if cat == "resample":
        # 已实测：permutation 在 GPU 上不划算(argsort 显存大且更慢) → AUTO 固定 CPU；bootstrap/MC 收益大 → GPU
        if op == "permutation":
            return "cpu", "permutation: GPU 无收益(argsort 重/更慢), AUTO→CPU"
        work = max(1, n_iter) * max(1, n)
        if work >= TH["resample_min_work"]:
            return "gpu", f"resample work={work:.2e} ≥ {TH['resample_min_work']:.0e}"
        return "cpu", f"resample work={work:.2e} < {TH['resample_min_work']:.0e}(启动开销占优)"
    if cat == "rolling":
        if TH["rolling_gpu_min_n"] <= n <= TH["rolling_gpu_max_n"]:
            return "gpu", f"rolling n={n:,} 在 [{TH['rolling_gpu_min_n']:,},{TH['rolling_gpu_max_n']:,}]"
        return "cpu", f"rolling n={n:,} 超出 GPU 安全/有效区间"
    if cat == "elem":
        if TH["elem_gpu_min_n"] <= n <= TH["elem_gpu_max_n"]:
            return "gpu", f"elem n={n:,} 在有效区间"
        return "cpu", f"elem n={n:,} 超出 GPU 有效/安全区间"
    return "cpu", "default cpu"


def compute(op: str, *args, backend: str = "auto", verify: bool = True, n_iter: int = 0,
            n_items=None, seed: int = 42, **kw) -> dict:
    """统一入口。返回 dict（含 result / backend_used / 时间 / 验证 / fallback）。"""
    if op not in OPS:
        raise KeyError(f"未注册算子: {op}")
    cpu_op, kind, cat, bpi, fac = OPS[op]
    n = _n_of(args, {"n_items": n_items})
    chosen, reason = decide(op, n, n_iter, backend)
    rec = {"op": op, "n": n, "n_iter": n_iter, "chosen": chosen, "reason": reason,
           "cpu_ms": None, "gpu_ms": None, "backend_used": None, "fallback_reason": "",
           "gpu_peak_mb": None, "validation": None}
    gpu_res = gpu_ms = None
    if chosen == "gpu":
        try:
            gpu_res, gpu_ms, peak = GB.run(cpu_op, *args, **kw)
            rec["gpu_ms"] = gpu_ms; rec["gpu_peak_mb"] = peak
        except RuntimeError as e:  # OOM 等
            if "out of memory" not in str(e).lower():
                raise
            chunking.free()
            try:  # 缩块重试一次（释放后）
                gpu_res, gpu_ms, peak = GB.run(cpu_op, *args, **kw)
                rec["gpu_ms"] = gpu_ms; rec["gpu_peak_mb"] = peak
            except RuntimeError:
                chunking.free()
                rec["fallback_reason"] = "GPU OOM×2 → CPU fallback"
                gpu_res = None
    if gpu_res is not None:
        rec["backend_used"] = "gpu"
        if verify:
            cpu_res, cpu_ms = CB.run(cpu_op, *args, **kw)
            rep = compare(cpu_res, gpu_res, kind)
            rec["cpu_ms"] = cpu_ms; rec["validation"] = rep
            assert_valid(rep)                      # 不一致 → COMPUTE_VALIDATION_FAILED
            rec["result"] = gpu_res
        else:
            rec["result"] = gpu_res
    else:
        if chosen == "gpu" and not rec["fallback_reason"]:
            rec["fallback_reason"] = "GPU 未产出 → CPU"
        cpu_res, cpu_ms = CB.run(cpu_op, *args, **kw)
        rec["backend_used"] = "cpu"; rec["cpu_ms"] = cpu_ms; rec["result"] = cpu_res
        rec["validation"] = {"ok": True, "kind": "cpu-reference"}
    rec["speedup"] = (rec["cpu_ms"] / rec["gpu_ms"]) if (rec["cpu_ms"] and rec["gpu_ms"]) else None
    DECISIONS.append(rec)
    return rec


def result_of(rec) -> object:
    return rec["result"]
