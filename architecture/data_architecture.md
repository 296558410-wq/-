# Data Architecture — 统一数据层设计

> 目标：任何实验不再自造 CSV。一条数据流水线：Raw → Normalize → Parquet → DuckDB → Feature → Research → Backtest。
> 当前阶段只用 **synthetic 数据**验证管线；真实数据源（MT5 等）待数据策略审批。

## 1. 分层管线

```
┌─ Raw (原始, 只读) ── data/raw/
│   Tick:  timestamp(UTC), symbol, bid, ask, volume, source
│   Bar:   timestamp(UTC), symbol, open, high, low, close, volume, source
├─ Normalize (标准化, 幂等可重跑) ── scripts/
│   - 统一 UTC、去重、缺失标记、spread 计算、session 标注
├─ Parquet 存储层 ── data/parquet/ (schema 版本化)
│   命名: <symbol>_<granularity>_<start>_<end>.parquet
├─ DuckDB 查询层 ── data/cache/aiq_meta.duckdb (视图/索引/聚合)
├─ Feature Layer ── research/features/ (schema 版本化)
├─ Research / Backtest ── research/ + backtests/
└─ 报告 ── reports/
```

## 2. 统一 Schema（约定）

### Tick（示例，XAUUSD）
| 字段 | 类型 | 说明 |
|---|---|---|
| ts_utc | datetime64[ns, UTC] | 主键部分，事件时间 |
| symbol | str | 如 XAUUSD |
| bid / ask | float64 | 报价 |
| spread | float64 | ask-bid（归一化层计算） |
| volume | float64 | 该 tick 量（如可获取） |
| source | str | 数据源标识（mt5/dukascopy/synthetic…） |
| quality | uint8 | 0=正常 1=可疑 2=缺失填充（质量层） |

### Bar（M1/M5/H1 通用）
ts_utc, symbol, open, high, low, close, volume, spread_mean, tick_count, source

### Feature / Label Schema
每个 feature/label 定义必须记录：名称、计算函数版本、输入数据版本、参数、窗口、是否前视（lookahead=否）、seed。

## 3. 质量规则（必须处理）

| 问题 | 处理 |
|---|---|
| 时区 | 存储一律 UTC；本地时区仅在展示层转换 |
| 重复 tick | 按 (ts_utc,bid,ask) 去重并计数记录 |
| 缺失 | 显式标记（NaN + quality 字段），不静默填充 |
| spread 异常 | 负 spread/极端值 → quality=1，过滤策略参数化 |
| 市场 session | 标注字段：asia/london/newyork/offhours（可配置） |
| 停盘缺口 | 保留时间戳（不重采样跨缺口），策略显式处理 |
| 数据版本 | 目录级 MANIFEST.json（文件清单+SHA256+生成脚本 commit） |

## 4. Synthetic 数据（当前验证用）

- 生成器：`scripts/gen_synthetic.py`（几何布朗运动 + 跳跃 + 日内波动 U 型 + bid/ask spread）
- 粒度：tick（稀疏模拟）→ 聚合成 M1/M5/H1
- 输出：`data/synthetic/` 下 parquet + manifest
- 用途：管线联调、测试、pipeline 端到端验证。**不代表真实市场行为，禁止用于结论性研究**

## 5. 目录-格式对应

| 内容 | 位置 | 格式 |
|---|---|---|
| 原始数据 | data/raw/<source>/ | 源格式或 parquet |
| 标准 bar/tick | data/parquet/<symbol>/<gran>/ | parquet (zstd) |
| 特征 | research/features/ | parquet + schema.yaml |
| 标签 | research/features/labels/ | parquet |
| 元数据库 | data/cache/aiq_meta.duckdb | duckdb |
| 实验元数据 | research/experiments/<exp>/meta/ | yaml/json（进 Git） |

## 6. 待办（后续阶段）

- [ ] MT5 导出管线（真实数据源策略审批后）
- [ ] MANIFEST 自动生成脚本
- [ ] pandera schema 注册表
- [ ] ArcticDB 评估（tick 量大后）
- [ ] DVC 数据版本化（多版本迭代后）
