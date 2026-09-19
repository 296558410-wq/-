# -*- coding: utf-8 -*-
"""research_compute._bridge — 桥接独立 GPU 加速层 (C:\\AIQuant\\research\\gpu_accelerator)。

单一 GPU 实现来源：不复制第二套 GPU 代码，全部转发到 gpu_accelerator。
"""
from __future__ import annotations

import os
import sys

_RESEARCH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _RESEARCH not in sys.path:
    sys.path.insert(0, _RESEARCH)

_CACHE = {}


def ga():
    """返回 gpu_accelerator 包（延迟导入）。"""
    if "ga" not in _CACHE:
        import gpu_accelerator as _ga  # noqa
        _CACHE["ga"] = _ga
    return _CACHE["ga"]


def research_path() -> str:
    return _RESEARCH
