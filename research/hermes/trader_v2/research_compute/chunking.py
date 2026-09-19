# -*- coding: utf-8 -*-
"""research_compute.chunking — 4GB VRAM 安全（预算/分块/OOM 重试/回退），转发 gpu_accelerator。

安全准则：显存预算 = VRAM×0.75（默认 3.0GB）；**禁止**出现 rolling@100M → 6.4GB WDDM paging 这类越界执行。
凡可能大张量的操作必须经 plan_chunk 分块；OOM → 释放 → 缩块重试 → 仍失败 → CPU fallback。
"""
from __future__ import annotations

from ._bridge import ga

OOMFallback = ga().core.memory_manager.OOMFallback
MemoryManager = ga().core.memory_manager.MemoryManager


def budget_bytes() -> int:
    return MemoryManager().budget


def plan_chunk(n_items: int, bytes_per_item: int, factor: int = 3) -> int:
    return MemoryManager().plan_chunk(int(n_items), int(bytes_per_item), int(factor))


def free():
    MemoryManager().free()


def peak_mb() -> float:
    return MemoryManager().peak_mb()


class ChunkedRunner:
    """在有界显存内执行 fn(chunk)，OOM 自动缩块重试；超限抛 OOMFallback（上层回退 CPU）。"""

    def __init__(self, bytes_per_item: int = 4, factor: int = 3, max_shrink: int = 4):
        self.bytes_per_item = bytes_per_item
        self.factor = factor
        self.max_shrink = max_shrink
        self.mm = MemoryManager()

    def run(self, fn, chunk_items: int):
        return self.mm.safe_execute(fn, chunk_items=chunk_items, bytes_per_item=self.bytes_per_item,
                                    factor=self.factor, max_shrink=self.max_shrink)
