# -*- coding: utf-8 -*-
"""V2 研究计算层（Research Compute Backend）。

只服务"研究计算"（大规模统计验证 / 特征计算 / 反事实实验）；
**不是** Decision Engine，绝不进入交易执行/风控链。
GPU 后端复用独立层 `C:\\AIQuant\\research\\gpu_accelerator`（单一实现）。
"""
from . import dispatcher, validation, chunking, rng  # noqa: F401
from .dispatcher import compute, decide, DECISIONS, OPS  # noqa: F401
from .validation import compare, assert_valid, ComputeValidationError  # noqa: F401
