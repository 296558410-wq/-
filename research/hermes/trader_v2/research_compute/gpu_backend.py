# -*- coding: utf-8 -*-
"""research_compute.gpu_backend — GPU 后端（转发 gpu_accelerator.core.gpu_backend）。

不复制实现；OOM 由 dispatcher/chunking 处理并回退 CPU。GPU 绝不进入执行/风控链。
"""
from __future__ import annotations

import time

from ._bridge import ga
from .chunking import MemoryManager

GPU = ga().core.gpu_backend


def available() -> bool:
    return ga().core.common.gpu_available()


def device_name() -> str:
    return ga().core.common.gpu_name()


def has(op: str) -> bool:
    return hasattr(GPU, op)


def run(op: str, *args, **kw):
    """执行并返回 (result, elapsed_ms, gpu_peak_mb)。OOM 会抛 RuntimeError（上层处理）。"""
    fn = getattr(GPU, op)
    mm = MemoryManager()
    mm.reset_peak()
    t0 = time.perf_counter()
    r = fn(*args, **kw)
    dt = (time.perf_counter() - t0) * 1000.0
    peak = mm.peak_mb()
    mm.free()
    return r, dt, peak
