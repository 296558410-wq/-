# -*- coding: utf-8 -*-
"""research_compute.rng — 随机数政策与统计摘要工具。

政策：GPU/CPU **不做逐元素一致**要求；但必须 **same seed / same distribution / same sample size**，
统计量（mean/std/quantile/tail）落在预定义 tolerance 内即通过。
所有派生种子必须确定性（sha256），保证可复现。
"""
from __future__ import annotations

import hashlib

import numpy as np


def child_seed(base_seed: int, *tags) -> int:
    """确定性派生种子：same (base, tags) → same int。"""
    h = hashlib.sha256(f"{int(base_seed)}|{'|'.join(map(str, tags))}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def stat_summary(x) -> dict:
    a = np.asarray(x, dtype=np.float64)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"n": 0}
    q = np.quantile(a, [0.01, 0.25, 0.5, 0.75, 0.99])
    return {"n": int(a.size), "mean": float(a.mean()), "std": float(a.std(ddof=1)) if a.size > 1 else 0.0,
            "median": float(np.median(a)), "q01": float(q[0]), "q25": float(q[1]), "q50": float(q[2]),
            "q75": float(q[3]), "q99": float(q[4])}


def reps(n_iter: int, seed: int) -> np.random.Generator:
    """参考实现用 numpy Generator（CPU 与 GPU 各自独立流，仅要求统计一致）。"""
    return np.random.default_rng(int(seed))
