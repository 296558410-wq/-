# V2 研究计算层 (research_compute)

V2 的 **Research Compute Backend**：把已验证的 `C:\AIQuant\research\gpu_accelerator`（独立 GPU 加速层）作为
V2 的大规模统计验证 / 特征计算 / 反事实实验计算后端。**单一 GPU 实现**（转发，不复制第二套）。

## 边界（硬）
- **不是 Decision Engine**：Hermes 仍是唯一交易决策者；GPU 绝不产生 TRADE、不改 Decision Contract、不绕 Risk Gate。
- **与执行系统完全隔离**：不 import / 不调用 `PaperExecutor`、`BrokerDemoExecutor`、`FXTMDemoAdapter`、`Ledger`、`Replay`、`Risk Gate`；GPU **不写 Ledger**、不下单/改单/平仓/改 SL/TP/volume/risk。
- **不碰 V1**：不 import、不读写 V1 账户/ledger/state/memory。
- **不改时间语义**：feature[t]→signal[t]→execution[t+1]；所有 rolling/resample/feature 只用已冻结数据范围，无未来泄漏。
- 只读原始数据；不改任何交易阈值 / 风险参数 / `max_lot=0.05` / FLOOR_TO_STEP / 成本模型 / Broker Demo 执行逻辑 / cron。

## 用法
```python
import sys; sys.path.insert(0, r"C:\AIQuant\research\hermes\trader_v2")
from research_compute import compute, decide

r = compute("bootstrap", x, stat="mean", n_iter=10000, seed=7, n_iter=10000)
r["result"]        # 结果（GPU 时已经 CPU 独立验证通过）
r["backend_used"]  # "cpu" | "gpu"
r["fallback_reason"]# GPU OOM/不可用时的回退原因
```
模式：`backend="auto" | "cpu" | "gpu"`（默认 auto）。

## AUTO 规则（阈值来自 benchmark，可更新）
- CUDA 不可用 / 无算子 → CPU；
- 重采样(bootstrap/permutation/MC)：`n_iter×n ≥ 1e8` → GPU，否则 CPU；
- 滚动(rolling_std/mean)：`3M ≤ n ≤ 40M` → GPU（区间外 CPU；未分块大 n 不做，避免越界显存）；
- elementwise(microbar/spread/returns/rv/features)：`n ≥ 2M` → GPU。
- GPU OOM → 释放→缩块重试→仍失败 → **CPU fallback**（记录原因）。

## 验证（硬门）
GPU 结果进入研究结论前必须经 **CPU 独立验证**：`compare()`（elementwise / statistical），
不一致 → `COMPUTE_VALIDATION_FAILED`（不得继续交给 Hermes）。

## 文件
`dispatcher.py` 调度 · `cpu_backend.py`/`gpu_backend.py` 转发 · `validation.py` 一致性门 ·
`chunking.py` 4GB 显存安全 · `rng.py` 随机数政策 · `benchmark.py` 基准 · `_bridge.py` 桥接。
