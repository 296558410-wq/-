# AIQuant — AI 量化研究工作站

面向 **XAUUSD 黄金**的高频/短周期（Tick / M1 / M5 / H1）量化研究工作站。
长期目标：机器学习 + GPU 加速统计 + 严格回测 + 可复现研究 + 未来 LLM/Agent 研究自动化。

> 硬件：Surface Laptop Studio · i7-11370H 4C/8T · 32GB RAM · RTX A2000 4GB (CC 8.6)
> 详见 `reports/machine_baseline.md`、`environment/environment.md`、`docs/software_stack.md`

## 目录结构（含用途）

```
C:\AIQuant\
├── .venv\              研究专用 Python 3.12 虚拟环境（所有项目默认解释器）
├── environment\        requirements.in / requirements.txt / environment.md / install.log
├── architecture\       compute_architecture.md（CPU/GPU分工） data_architecture.md（数据层）
├── data\
│   ├── raw\            原始数据（只读，不原地修改）
│   ├── processed\      标准化数据（Parquet）
│   ├── parquet\        Parquet 统一存储层
│   └── cache\          中间缓存 / DuckDB 文件 / 可重建内容
├── datasets\           整理后的数据集（按主题）
├── research\
│   ├── experiments\    研究实验（假设→实验→结论）
│   ├── hypotheses\     假设登记
│   ├── features\       特征定义与验证
│   ├── signals\        信号定义
│   └── strategies\     策略定义与迭代
├── models\             训练模型权重（不入 Git）
├── checkpoints\        训练中间状态（不入 Git）
├── backtests\          回测结果与报告
├── research_engine\    CPU/GPU 统一计算后端雏形（run_monte_carlo / bootstrap / permutation…）
├── notebooks\          探索性分析
├── scripts\            数据管线/一次性脚本
├── configs\            配置模板（.env 不入 Git）
├── tests\              测试套件 + 结果记录
├── benchmarks\         GPU/CPU 基准脚本
├── experiments\        通用实验目录（mlflow 相关/早期布局，research\experiments 为研究实验主目录）
├── reports\            报告（machine_baseline / gpu_benchmark / overnight_report…）
├── logs\               运行日志（install.log 等）
├── projects\           实际研究项目（与 research\ 配合；大项目独立成库时用此目录）
├── tools\              可复用工具脚本
├── artifacts\          mlflow artifact 存储
├── cache\              全局缓存（自清理）
├── automation\         长期任务运行器与设计（checkpoint/resumable）
├── docker\             未来容器占位（当前不用）
└── docs\               设计文档（software_stack.md / architecture.md）
```

## 数据流（统一数据层）

```
Raw Tick → Normalize → Parquet → DuckDB → Feature Layer → Research → Backtest
```

## 铁律

1. 代码进 Git；数据/模型/secret 永不进 Git
2. 研究结论必须可复现：commit + lock + seed + 数据 manifest + 硬件快照
3. Sharpe 高 ≠ Alpha；噪声控制机制从第一天启用
4. GPU 只做有实测优势的任务；4GB VRAM 预算纪律
5. 系统 Python 3.14 不动；一切量化工作用 `.venv`
6. `C:\AIResearch` 保留不动

详见 `docs/software_stack.md` 与 `docs/architecture.md`。
