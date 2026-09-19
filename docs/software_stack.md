# AIQuant 软件栈方案 v0.1（待审批）

> 硬件基线：Intel i7-11370H (4C/8T) · 32GB RAM · NVIDIA RTX A2000 Laptop 4GB (CC 8.6, GA107, Ampere) · 驱动 591.55 (支持 CUDA ≤13.1) · 1TB NVMe (剩余 873GB)
> Python 基线：系统 3.14.7 保留（OpenClaw 专用）；AIQuant 用独立 **Python 3.12.x** venv
> 日期：2026-09-03 · 状态：**待审批，未安装任何新组件**

---

## 1. 分类总表

图例：GPU=是否使用 GPU · TK=是否需要 CUDA Toolkit · 磁盘=预估安装体积

### CORE（第一阶段，一次装齐但分相验证）

| 包 | 版本锚点 | 为什么装 | 依赖 | GPU | TK | 磁盘 | 潜在冲突 | 未来用途 |
|---|---|---|---|---|---|---|---|---|
| python 3.12.x | ≥3.12.8 | 生态全兼容点（numpy 2.5/scipy 1.18 要求 ≥3.12；sktime/vectorbt 等明确 <3.15） | — | 否 | 否 | ~120MB | 与 3.14 并存，py launcher 区分 | venv 基底 |
| numpy | 2.5.x | 数组计算地基 | — | 否 | 否 | ~40MB | 需 ≥3.12 | 一切数值 |
| pandas | 3.0.x | 表格/时序主数据结构 | numpy | 否 | 否 | ~60MB | pandas 3 有 API 变化，需读迁移说明 | 研究主数据框 |
| scipy | 1.18.x | 统计/优化/信号 | numpy | 否 | 否 | ~50MB | — | 假设检验、插值 |
| numba | 0.67.x | CPU JIT 加速自定义循环/rolling | numpy | 否(CPU) | 否 | ~50MB | 与 numpy 版本强绑定，须同批安装 | 自研快速指标、去重逻辑 |
| pyarrow | 25.x | Parquet/Feather 列存、零拷贝 | numpy | 否 | 否 | ~60MB | — | 全数据落地格式 |
| polars | 1.44.x | 大数据/并行/流式处理、SQL 上下文 | pyarrow | 否(CPU) | 否 | ~40MB | 1.44 起 PyPI 为 shim 分发，装时验证原生轮 | 大规模 tick 清洗 |
| duckdb | 1.5.x | 本地 SQL 分析、parquet 直查、聚合/校验 | — | 否 | 否 | ~30MB | — | 数据质量抽查、快速聚合 |
| statsmodels | 0.15.x | 回归/诊断/协整/时序统计 | pandas | 否 | 否 | ~60MB | — | 研究统计主力 |
| arch | 8.0.x | GARCH/波动率建模（XAUUSD 核心） | pandas | 否 | 否 | ~5MB | 2025-10 后节奏放缓但 8.0 稳定 | 波动率 regime 研究 |
| scikit-learn | 最新 | 基线 ML、CV、Pipeline、指标 | numpy/scipy | 否 | 否 | ~30MB | — | 基线模型对照 |
| torch | 2.14.0 | GPU 主引擎（见 §3 专用设计） | — | **是** | **否** | ~3GB | 见 §3 | DL/MC/GPU 数值 |
| xgboost | 3.4.x | 表格 ML 主力（GPU 可选） | numpy/scipy | 可选 | 否 | ~200MB | py≥3.12 | 特征模型、集成 |
| lightgbm | 4.7.x | 表格 ML 备选（CPU 路线） | numpy | 否(CPU) | 否 | ~10MB | Windows GPU 需 OpenCL，不稳 → CPU | 与 xgboost 对照 |
| pandera | 0.33.x | DataFrame 校验（研究数据质量门禁） | pandas | 否 | 否 | ~10MB | — | 数据进入研究前的 schema 校验 |
| mlflow | 3.15.x | 实验记录/指标/artifact（本地 sqlite） | — | 否 | 否 | ~100MB | 重依赖，用最小安装 | 实验元数据中枢 |
| matplotlib | 最新 | 基础绘图 | numpy | 否 | 否 | ~20MB | — | 报告图表 |
| pytest | 最新 | 研究代码测试 | — | 否 | 否 | ~5MB | — | 数据/逻辑回归测试 |

CORE 小计 ≈ **4–4.5GB**（torch 占大头）

### OPTIONAL（明确用途后才装）

| 包 | 为什么候选 | GPU | TK | 磁盘 | 启用条件 |
|---|---|---|---|---|---|
| vectorbt 1.1.x | 快速向量化研究/大规模参数扫描（纯 py 活跃） | 有限 | 否 | ~20MB | 需要批量策略扫描时（第二阶段评估） |
| nautilus_trader | tick/事件驱动/microstructure 级回测（Rust 核） | 否 | 否 | ~80MB | 进入 tick 级验证阶段时（第三阶段） |
| arcticdb | tick 级列存数据库 | 否 | 否 | ~150MB | 数据量 > 数百 GB 或需要高频切片查询时 |
| MetaTrader5 官方包 | XAUUSD 数据源通道 | 否 | 否 | ~20MB | 确认使用 MT5 终端 + 数据策略后 |
| cupy-cuda12x | GPU 数组/通用数值 | 是 | 否 | ~1GB | GPU benchmark 证明 >2× 收益且 CPU 内存瓶颈明显时 |
| quantstats | 绩效报告 | 否 | 否 | ~5MB | 有回测结果需要标准报告时 |
| statsforecast | 快速统计预测基线 | 否 | 否 | ~10MB | 需要 naive/ETS/ARIMA 基线对照时 |
| dvc | 数据版本化 | 否 | 否 | ~50MB | 数据集开始多版本迭代时 |
| hydra-core | 实验配置管理 | 否 | 否 | ~5MB | 配置矩阵复杂度上升时 |

### LATER（观察/路线图，当前明确不装）

| 项目 | 原因 | 触发条件 |
|---|---|---|
| sentence-transformers / embedding | 4GB VRAM 可跑小模型，但需 HF 下载源方案 | 本地 LLM 策略定稿（GPU 环境建成后单独设计） |
| llama.cpp / 本地量化 LLM | ≤4B Q4 可行，但模型源/工具链未定 | LLM 策略文档审批后 |
| pyqlib | 发版放缓、Windows 支持弱 | 仅借鉴其数据/回测思想 |
| sktime / darts / neuralforecast | 重框架，与自研管线重叠 | 明确需要某类模型（如 N-BEATS）时按需评估 |
| Docker / WSL / RAPIDS | 用户决策 #11 排除 | 后续评估，不属 Core |
| Chroma/向量库 | 依赖 embedding 方案 | 随 LLM 策略 |
| JAX | Windows 生态仍弱于 torch | 无明确不可替代场景 |

### REJECT（不装，记录理由）

| 项目 | 理由 |
|---|---|
| backtrader | 3 年+ 未发版，单线程慢 |
| zipline-reloaded / pyfolio-reloaded | 生态老旧，非 tick/MT5 路线 |
| great-expectations | 重框架，pandera 覆盖 |
| mlfinlab | 商业化付费化 |
| freqtrade 等 crypto-only | 方向不符（XAUUSD） |
| airflow/kedro/luigi | 现阶段脚本+mlflow 足够 |
| CUDA Toolkit / cuDNN 独立安装 | torch pip 轮子自带 runtime（见 §3） |
| 各类"一键安装脚本"工具 | 安全原则禁止 |

---

## 2. CPU / GPU / RAM / Disk 工作负载分工

### 判定原则
- **GPU 只用于**：大规模并行数值（MC/Bootstrap/Permutation/Shuffle）、参数扫描、矩阵/张量运算、ML/DL 训练推理、embedding
- **CPU 保留**：I/O、数据清洗、逻辑判断、高精度统计（FP64）、小数据、数据库、控制流、调度
- **4GB VRAM 预算规则**：任何单任务显存预留 ≤2.5GB（留 ~1.5GB 余量防 OOM）；批量大小动态调；溢出自动回退 CPU（代码层 try/except 设计）
- FP64 注意：Ampere 消费级 FP64 极弱（1:64）→ 高精度统计走 CPU

### 研究任务 × 执行单元矩阵

| 任务 | 单元 | 说明 |
|---|---|---|
| 大规模特征计算（tick→bar） | **GPU**（torch 分块）或 CPU(polars 并行) | 数据量超 RAM 用 polars 流式；超 2.5GB 单批用 GPU |
| Rolling 计算 | CPU（numba 自研/numpy 分块） | 串行依赖不适合 GPU，numba 足够快 |
| Monte Carlo | **GPU**（torch 批量路径） | 天然并行，收益最大场景 |
| Bootstrap | **GPU**（torch 重采样+统计） | 万次以上重采样收益显著 |
| Permutation/Shuffle Test | **GPU**（批量打乱+统计） | 同上 |
| 参数网格搜索 | CPU 调度 + GPU 批量评估 | 策略级搜索 CPU/vectorbt；模型级搜索 GPU |
| 多策略回测 | CPU（vectorbt/nautilus） | 回测引擎本身 CPU；瓶颈在特征→GPU |
| Walk-forward | CPU 编排，段内计算按需 GPU | 串行滚动窗口，调度在 CPU |
| 超参数搜索（ML/DL） | **GPU**（小批量并行）+ mlflow 记录 | 4GB 显存 → 小 batch、单卡串行为主 |
| 统计检验（t/卡方/协整） | CPU（scipy/statsmodels） | FP64 精度要求 |
| 波动率建模 GARCH | CPU（arch） | 串行 MLE |
| ML（GBDT） | CPU（lightgbm/xgboost CPU） | 金融表格数据量级 CPU 足够；xgboost GPU 可选测 |
| DL 时序模型 | **GPU**（torch 小网络） | 显存约束见 §4 |
| Embedding | **GPU**（小模型） | 未来 LLM 阶段 |
| LLM 推理 | **GPU 4GB 限制**：≤4B Q4 或 API | LATER |
| 数据 I/O/清洗 | CPU + 磁盘 | duckdb/polars |

### RAM 预算（32GB）
- 单进程 pandas/研究脚本预算：**≤12GB**
- torch GPU 相关 CPU 侧：≤8GB
- 数据分块规则：>8GB 的 parquet 不整载入内存 → polars/duckdb 流式或 GPU 分块
- mlflow/pytest 等常驻服务开销忽略不计

### Disk 布局（873GB 可用）
| 区域 | 路径 | 预算 | 内容 |
|---|---|---|---|
| 环境 | C:\AIQuant\.venv | ~5GB | Python 3.12 + CORE 包 |
| 代码 | C:\AIQuant\projects + scripts/tools/configs/docs | ~1GB | 进 Git |
| 数据 | C:\AIQuant\data + datasets | 弹性（≤300GB 建议） | Parquet；不入 Git；**数据源为 MT5/未来 broker，非旧电脑迁移** |
| 模型 | models + checkpoints + artifacts | ≤100GB | 不入 Git |
| 实验 | experiments + reports + logs | ≤50GB | 元数据进 Git，大 artifact 用 mlflow 本地存储 |
| 缓存 | cache | 自清 | pip/模型缓存 |

---

## 3. PyTorch + pip CUDA runtime 路线（专项设计）

### 已核实事实（2026-09-03 实测）
1. torch **2.14.0** 提供 `cp312 win_amd64` 官方轮子 ✅
2. torch 2.14 Linux 依赖标记为 **cu13** 系列（nvidia-cudnn-cu13 等）→ Windows 轮子内部捆绑 CUDA runtime
3. 本机驱动 **591.55（CUDA 13.1）** ≥ CUDA 13.x 要求 → **驱动兼容 ✅**
4. RTX A2000 = sm_86 → torch 官方轮子包含 sm_86 内核 ✅

### 安装与验证协议（执行时）
```powershell
C:\AIQuant\.venv\Scripts\python -m pip install torch --index-url 清华镜像(如镜像缺 torch 则回退官方 PyPI)
# 验证脚本（tools/verify_gpu.py，安装阶段落地）:
#   torch.__version__ / torch.version.cuda / torch.cuda.is_available()
#   torch.cuda.get_device_properties(0)  # 名称、CC、显存
#   sm_86 内核实际跑通: 矩阵乘 + 小 MC
#   nvidia-smi 记录 driver/CUDA
```
- **不需要**：CUDA Toolkit、cuDNN、CUDA_PATH、系统 PATH 改动（全部随 wheel）
- **不装**：torch 的 CPU-only 变体、+cuXXX 特殊 index（默认 PyPI 轮子即 CUDA 版）
- 失败回退路径：若默认轮子有问题 → 仅换 pytorch.org cu12x index（不改驱动）；再失败 → 报告，不盲试

---

## 4. GPU 显存与模型规模边界（4GB VRAM 约束）

| 负载类型 | 可行规模 | 说明 |
|---|---|---|
| MC/Bootstrap/统计批量 | 任意（分块） | 每块 < 2.5GB |
| MLP/CNN/小 Transformer | 参数量 ≤ 50M（fp32） | 时序特征模型足够 |
| 训练 batch | 动态 32→8 | OOM 自动减半回退 |
| 本地 LLM | ≤4B Q4（≈2.5–3GB） | LATER，需量化工具链 |
| Embedding 模型 | 0.1–0.5B 任意 | 未来阶段 |
| 大模型微调 | **不可行**（需 LoRA+量化且仍紧张） | 结论：不走这条路，用 API 或小模型 |

---

## 5. 目录结构与数据/模型/实验/Git 管理设计

（目录树已于 STEP 6 创建，19 个目录）

### Git 管理（C:\AIQuant 根仓库，审批后 init）
- **进 Git**：projects/ scripts/ tools/(源码) configs/ docs/ notebooks/ experiments/*/meta、reports/ logs/(保留 .gitkeep 或摘要)、requirements 锁文件、.gitignore、.env.example
- **不进 Git**：data/ datasets/ models/ checkpoints/ cache/ artifacts/ .venv/ secrets/ *.pt *.pth *.ckpt *.safetensors .env *.key 私有数据
- .gitignore 规则分级：全局忽略 + 各子目录局部规则（不粗暴一刀切；parquet 若未来需要样例文件则用例外规则）
- 流程：main 主分支 + 研究分支；提交信息规范；**commit hash 自动写入实验元数据**

### 数据管理
- 落地格式：Parquet（列存、压缩、schema 自带）；命名：`<symbol>_<granularity>_<date_range>.parquet`
- 查询/校验层：duckdb + pandera schema 注册
- 版本：文件清单 hash 清单（manifest.json）→ 未来 dvc
- 来源：MT5 导出管线（待数据策略审批）；**不迁移旧电脑数据**

### 模型管理
- models/（权重）+ checkpoints/（训练中间态）+ artifacts/（mlflow artifact 根）
- 每个模型记录：代码 commit、数据版本(manifest hash)、超参、seed、训练时间、GPU 快照 → mlflow run

### 实验管理（mlflow sqlite 本地）
- experiments/<日期>_<主题>_<序号>/：config.yaml + seed + 结果 + 图表
- mlflow 记录：params/metrics/artifacts/tags(commit hash, data hash, gpu, env)
- 统计严谨性内置：结果表附带 n_trials、多重检验标记（FDR 阶段再做）

### 日志/报告
- logs/：分项目日志（研究日志与系统日志分离）
- reports/：markdown 报告模板（GPU benchmark、实验结论、bootstrap_report）

### 可复现机制（env lock）
- `requirements.in`（顶层声明）+ `requirements.lock`（pip freeze 全量锁定，安装后生成）
- 版本五元组记录：**Python 版本 / package lock / git commit / 数据 manifest / GPU+驱动快照**
- seed 三件套：`random` + `numpy.random` + `torch.manual_seed`（tools 提供统一函数）
- `tools/snapshot_env.py`：一键输出环境 JSON（CPU/GPU/driver/torch/cuda/packages/commit）——安装阶段实现

---

## 6. 安装计划（分相，每相验证后才进下一相）

| 相 | 内容 | 验证门 | 回滚 |
|---|---|---|---|
| P0 | Python 3.12.x 官方安装器（与 3.14 并存，py launcher 可见） | `py -3.12 --version` | 卸载器（不动 3.14） |
| P1 | venv + 基础数值栈（numpy/pandas/scipy/numba/pyarrow/polars/duckdb/bottleneck + pip freeze 基线） | import 冒烟 + 简单计算 | 删 venv 重建 |
| P2 | torch 2.14.0（默认 PyPI 轮子） | tools/verify_gpu.py 全绿 | 同上 |
| P3 | sklearn/xgboost/lightgbm/statsmodels/arch/matplotlib | 冒烟测试 | 同上 |
| P4 | pandera/mlflow/pytest + 目录 .gitignore + git init + 首次 commit | git 状态干净 | git reset |
| P5 | GPU benchmark（CPU vs GPU：矩阵/MC/Bootstrap/Permutation/Rolling）→ reports/gpu_benchmark.md | 报告产出 | — |

镜像策略（记录在案）：venv 内 pip.ini 指向**清华 TUNA 镜像**（官方机构维护的 PyPI 镜像，https://pypi.tuna.tsinghua.edu.cn/simple）；torch 大轮子若镜像缺失回退官方 PyPI；不使用任何第三方加速器。

---

## 7. 已知风险与对策
| 风险 | 对策 |
|---|---|
| polars 1.44 shim 分发异常 | P1 装时实测 import + 跑 1M 行运算 |
| torch 2.14 Windows 轮子捆绑 CUDA 版本与 591.55 不兼容 | P2 验证门强制；失败换 cu12x index |
| 4GB VRAM OOM | §2 预算规则 + 动态 batch + CPU 回退 |
| numba 与 numpy 版本锁定 | 同批安装，lock 文件固定 |
| 国内网络（PyPI 慢） | 清华镜像 + 失败重试策略，不装代理 |
| pandas 3.0 API 迁移 | 读迁移指南，实验代码从第一天按 3.0 写 |

**审批点：以上方案（分类/分工/安装计划/镜像/风险）确认后，进入 P0 执行。**
