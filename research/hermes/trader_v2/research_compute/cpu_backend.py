# -*- coding: utf-8 -*-
"""research_compute.cpu_backend — CPU 参考后端（转发 gpu_accelerator.core.cpu_backend）。

CPU 是**参考实现**：所有研究结论以 CPU 路径为准；GPU 结果须经其独立校验。
"""
from __future__ import annotations

import time

from ._bridge import ga

CPU = ga().core.cpu_backend


def has(op: str) -> bool:
    return hasattr(CPU, op)


def run(op: str, *args, **kw):
    """执行并返回 (result, elapsed_ms)。"""
    fn = getattr(CPU, op)
    t0 = time.perf_counter()
    r = fn(*args, **kw)
    return r, (time.perf_counter() - t0) * 1000.0
