# -*- coding: utf-8 -*-
"""research_compute.validation — CPU 独立验证（GPU 结果进入研究结论前的硬门）。

流程: GPU result → CPU independent verification → tolerance check → PASS / FAIL。
不一致 → 抛 ComputeValidationError（COMPUTE_VALIDATION_FAILED），**不得继续交给 Hermes**。
tolerance 预定义，禁止为通过而放宽。
"""
from __future__ import annotations

import numpy as np

from .rng import stat_summary

# 预定义 tolerance（fp32 GPU vs fp64 CPU 参考）
TOL_ELEMENTWISE = {"atol": 1e-4, "rtol": 1e-4}
TOL_STATISTICAL = {"rtol": 0.05, "atol": 1e-6}   # 重采样类：统计量一致（非逐元素）


class ComputeValidationError(Exception):
    code = "COMPUTE_VALIDATION_FAILED"


def compare_elementwise(cpu, gpu, tol=None) -> dict:
    tol = tol or TOL_ELEMENTWISE
    a = np.asarray(cpu, dtype=np.float64); b = np.asarray(gpu, dtype=np.float64)
    if a.shape != b.shape:
        return {"ok": False, "kind": "elementwise", "reason": f"shape {a.shape}!={b.shape}", "tol": tol}
    m = np.isfinite(a) | np.isfinite(b)
    diff = np.abs(a[m] - b[m]) if m.any() else np.array([0.0])
    lim = tol["atol"] + tol["rtol"] * np.abs(b[m] if m.any() else np.array([0.0]))
    ok = bool(np.all(diff <= lim))
    return {"ok": ok, "kind": "elementwise", "max_abs": float(diff.max()) if diff.size else 0.0,
            "n": int(m.sum()), "tol": tol}


def compare_statistical(cpu, gpu, tol=None) -> dict:
    tol = tol or TOL_STATISTICAL
    sc, sg = stat_summary(cpu), stat_summary(gpu)
    if sc.get("n", 0) == 0 or sg.get("n", 0) == 0:
        return {"ok": False, "kind": "statistical", "reason": "empty sample"}
    worst = {"key": None, "rel": 0.0}
    ok = True
    for k in ("mean", "std", "median", "q01", "q25", "q50", "q75", "q99"):
        denom = max(abs(sc[k]), 1e-12)
        rel = abs(sc[k] - sg[k]) / denom
        if rel > worst["rel"]:
            worst = {"key": k, "rel": rel, "cpu": sc[k], "gpu": sg[k]}
        if rel > tol["rtol"] and abs(sc[k] - sg[k]) > tol["atol"]:
            ok = False
    return {"ok": ok, "kind": "statistical", "worst": worst, "cpu_n": sc["n"], "gpu_n": sg["n"], "tol": tol}


def compare(cpu, gpu, kind="elementwise", tol=None) -> dict:
    return compare_statistical(cpu, gpu, tol) if kind == "statistical" else compare_elementwise(cpu, gpu, tol)


def assert_valid(report: dict):
    if not report.get("ok"):
        raise ComputeValidationError(f"{report}")
    return True
