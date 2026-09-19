# AIQuant 架构设计 v0.1（待审批）

> 配套文档：`software_stack.md`（软件栈与安装计划）
> 硬件：Surface Laptop Studio · i7-11370H 4C/8T · 32GB RAM · RTX A2000 4GB (CC 8.6) · 驱动 591.55 · 1TB NVMe

## 1. 目录语义（STEP 6 已创建，19 目录）

```
C:\AIQuant\
├── projects\        实际研究项目（每个项目一个子目录，独立子仓库或根仓库子目录）
├── data\
│   ├── raw\         原始数据（MT5 导出等，只读，禁止原地修改）
│   └── processed\   清洗后标准化数据（Parquet）
├── datasets\        整理好的公开/研究数据集（按主题分子目录）
├── models\          训练完成的模型权重（不入 Git）
├── checkpoints\     训练中间 checkpoint（不入 Git）
├── experiments\     实验目录：<日期>_<主题>_<序号>\（meta 入 Git，产物本地）
│   └── benchmarks\  GPU/性能基准
├── notebooks\       探索性分析（产出结论后迁入 projects 固化为脚本）
├── scripts\         一次性/运维/数据管线脚本
├── tools\           可复用工具（snapshot_env.py、seed 工具、回测辅助）
├── reports\         Markdown 研究报告（入 Git）
├── logs\            研究日志（不入 Git，保留 .gitkeep）
├── configs\         配置模板（入 Git；含 .env.example 不含 .env）
├── cache\           临时缓存（自清理，不入 Git）
├── artifacts\       mlflow artifact 本地存储根
├── docker\          未来容器方案占位（当前不使用）
└── docs\            架构/规范文档（本文件与 software_stack.md）
```

**边界原则**：代码进 Git；数据进 data/datasets；权重进 models/checkpoints；实验证据进 experiments+mlflow；secret 永不落盘于本项目。

## 2. Python 环境

- 系统 Python 3.14.7：**仅 OpenClaw 运行时使用，不安装任何量化包**
- `C:\AIQuant\.venv`：Python **3.12.x** 独立虚拟环境，所有 AI Quant 工作默认解释器
- venv 内 pip.ini → 清华 TUNA 镜像（记录于 software_stack.md §6）
- 环境锁：`requirements.in`（顶层）+ `requirements.lock`（pip freeze，P1 起每相更新）

## 3. 计算分工（详见 software_stack.md §2）

- **GPU 专属**：MC / Bootstrap / Permutation / Shuffle / 参数扫描批量 / DL 训练 / 大特征分块 / 未来 embedding
- **CPU 专属**：I/O 清洗、rolling、GARCH 类 MLE、高精度 FP64 统计、回测调度、GBDT（默认）
- **RAM 规则**：研究进程 ≤12GB；>8GB 数据强制流式/分块
- **VRAM 规则**：单批 ≤2.5GB，OOM 自动降批回退 CPU

## 4. 可复现五元组（每个实验必须可回答）

| 维度 | 记录方式 |
|---|---|
| 代码版本 | git commit hash（实验 runner 自动注入 tags） |
| 依赖版本 | requirements.lock + Python 版本 |
| 数据版本 | 输入文件 manifest（路径+大小+SHA256） |
| 硬件 | tools/snapshot_env.py 输出（GPU 名/驱动/CUDA/torch 版本） |
| 随机性 | seed 三件套 + 参数文件（configs/） |

## 5. 实验纪律（研究协议要点，细化版待研究阶段审批）

1. 先写假设 → 设计实验 → 固定 seed 与数据版本 → 运行 → 记录
2. 任何"发现"必须附带对照：placebo/shuffle/时序交叉验证
3. 多重比较意识：FDR 控制从第一批实验开始记账（n_trials 字段）
4. 结果只认实验目录 + mlflow 记录，不认口头结论
5. 代码评审制：tools/scripts 的可复用代码进 Git 前过 pytest

## 6. Git 管理（审批后执行）

- `git init` 于 C:\AIQuant 根；默认分支 main
- .gitignore 分层规则（根 + 子目录补充），核心忽略：
  data/ datasets/ models/ checkpoints/ cache/ artifacts/ .venv/ .env *.pt *.pth *.ckpt *.safetensors *.key
- 身份已配置（296558410-wq / 296558410@qq.com）；SSH 密钥已生成并登记 GitHub（待用户网页添加）
- 首次 commit：docs/ + .gitignore + requirements.in + 目录骨架

## 7. 安全边界

- 不执行 curl|iex / 陌生一键脚本 / 未审查 README 命令
- 所有安装来自官方源或登记镜像（清单见 software_stack.md）
- 涉及管理员权限、防火墙、系统配置修改 → 先报告
- API key/凭据只放环境变量或 OpenClaw 凭据库，不落项目文件
