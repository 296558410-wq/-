# Compute Architecture — CPU / GPU / RAM / Disk 分工设计

> 硬件事实：i7-11370H 4C/8T（无 AVX-512）· 32GB RAM · RTX A2000 4GB (sm_86) · 1TB NVMe
> 实测基准见 `reports/gpu_benchmark.md`（真实数字，非估算）

## 1. 分工总原则

- GPU 只承接**大规模并行数值任务**，且必须通过实测确认有收益（benchmark 记录在案）
- 4GB VRAM 纪律：单批显存 ≤2.5GB；OOM → 自动降批 → 仍不行回退 CPU（代码层处理）
- FP64 高精度统计（协整、GARCH MLE、t/F 检验细节）→ CPU
- 调度/编排永远在 CPU；GPU 是"计算单元"不是"大脑"

## 2. CPU 负责

| 任务 | 工具 | 理由 |
|---|---|---|
| 文件 I/O / Parquet 读写 | pyarrow / polars | 磁盘与格式逻辑 |
| DuckDB 查询/聚合 | duckdb | 数据库引擎 |
| 数据清洗/ETL | pandas / polars | 控制流密集 |
| 复杂控制逻辑/调度 | python | — |
| Rolling 计算 | numpy / numba JIT | 串行依赖，numba 已足够快 |
| GARCH/波动率 MLE | arch | 串行优化，FP64 |
| 回归/诊断统计 | statsmodels / scipy | FP64 精度 |
| 回测引擎（事件/向量） | backtesting.py / vectorbt | 引擎本身 CPU |
| GBDT（默认） | xgboost CPU / lightgbm | 表格数据量级 CPU 足够且稳定 |

## 3. GPU 负责

| 任务 | 方式 | 备注 |
|---|---|---|
| Monte Carlo 路径模拟 | torch 批量矩阵 | 收益最大场景（实测见报告） |
| Bootstrap / Permutation / Shuffle | torch 批量重采样+统计 | 万次级迭代 |
| 大规模矩阵/张量运算 | torch | FP32/FP16 |
| DL 模型训练 | torch（小网络 ≤50M 参数） | 动态 batch |
| 大规模特征分块计算 | torch 分块 | 单批 ≤2.5GB |
| 参数网格扫描（数值型） | torch 批量评估 | 策略级扫描仍 CPU |
| Embedding（未来） | 小模型 | LATER |

## 4. 工具级 GPU 结论（实测/决策，2026-09-03）

| 工具 | GPU 路线 | 结论 |
|---|---|---|
| **PyTorch** | pip CUDA runtime 轮子 | ✅ 主 GPU 引擎；无需 Toolkit/cuDNN |
| **Numba** | CPU JIT 为主 | CUDA target 需 CUDA Toolkit → **暂不启用**（记录） |
| **CuPy** | cupy-cuda12x 轮子 | 评估：与 torch 重叠；若纯 numpy-API 场景无不可替代性 → 不装/移除 |
| **XGBoost** | device='cuda' | 实测（见 gpu_benchmark.md）；失败则 CPU |
| **LightGBM** | OpenCL GPU | Windows 下需 OpenCL ICD，不稳定 → CPU 路线（记录） |
| vectorbt/backtesting | CPU | 引擎 CPU 化 |
| RAPIDS | — | 已决策不装（无 Windows 轮子，需 WSL/Docker） |

## 5. RAM 规划（32GB）

| 用途 | 预算 | 规则 |
|---|---|---|
| 研究进程 | ≤12GB | 超限 → 分块/流式 |
| GPU 相关 CPU 侧 | ≤8GB | tensor 搬运缓冲 |
| DuckDB/parquet 查询 | ≤6GB | spill-to-disk 开启 |
| 系统+OpenClaw+杂项 | 余量 | 观察占用 |

> 8GB 以上数据禁止整载入内存：polars 惰性/流式、duckdb 直查 parquet、pyarrow 分块读。

## 6. SSD 空间策略（873GB 可用）

| 区域 | 预算 | 策略 |
|---|---|---|
| .venv | ≤6GB | 冻结即止，可重建 |
| data+datasets | ≤300GB | Parquet 压缩列存；raw 保留原始 |
| models+checkpoints+artifacts | ≤100GB | 权重不进 Git；用 manifest 管理 |
| research/experiments+backtests+benchmarks | ≤50GB | 元数据进 Git，大产物本地 |
| reports/logs/cache | ≤20GB | 日志轮转，cache 自清理 |
| 系统余量 | 400GB+ | 保持充足 |

## 7. 决策记录

- 2026-09-03：Numba CUDA / LightGBM GPU / CuPy 需要 CUDA Toolkit 或 OpenCL → **当前阶段不装 Toolkit**，仅记录，待实际 workload 证明值得再评估。
