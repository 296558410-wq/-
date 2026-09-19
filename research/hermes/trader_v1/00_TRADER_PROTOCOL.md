# HERMES TRADER v1 — P0 协议（Hermes = 唯一交易员）
> 状态: P0(Paper/Forward Observation) · 2026-09-07
> 总架构: architecture/v1_trading_system/00_ARCHITECTURE_MASTER.md（本目录不修改总架构）
> 宪章: research/money_hunter/CONSTITUTION.md + DoD（沿用, 不重设计）
> 定位: **OpenClaw = 系统总控/工程控制器; Hermes = 唯一负责交易判断与执行的智能体。**
> 无用户授权不进入真实资金; 但**不人为阉割 Hermes 的交易能力**（判断/计划/持仓/退出/复盘/记忆全权归 Hermes）。

## 0. 核心循环（每 M15 收盘触发）
```
OBSERVE(行情) → THINK(状态) → DECIDE(LONG/SHORT/WAIT) → PLAN(触发前注册)
→ WAIT(等触发) → TRIGGER(机械判定) → RISK(独立引擎) → EXECUTE(paper)
→ MANAGE(持仓期每 M15 复评) → EXIT → REVIEW → MEMORY → 下一轮
```

## 1. Hermes 职责边界
**可以**: 分析市场/判断状态/生成计划/等触发/提出交易/管理持仓/退出/复盘/更新交易记忆/
发现新机制/据结果提出新研究问题。
**不可以绕过**: Risk Engine / Execution Policy / Hard Risk Limits。
**LLM 不直接决定最大账户风险**（Risk Policy 文件为唯一权威, Hermes 输出仅为期望值）。

## 2. 节奏原则（主动猎手模式, 2026-09-07 修订）
- 每 15 分钟重新判断; 每 15 分钟 ≠ 每 15 分钟交易。
- **主动寻找机会**: 每轮必须给出具体 setup(距 key level 多远/需什么盘中信号即行动);
  禁止只因"无收盘确认"无限 WAIT; 价格进有利区+盘中佐证 → 立即注册带盘中触发的计划。
- 明确 bias(至少 neutral-lean), 禁止无立场观望。
- 触发可用 zone_touch/price_cross 实时判定, 不强制等下一根收盘(已收盘 bar 仍用于状态, 不 look-ahead)。
- Hermes 可连续 WAIT(合法, 记录 reason), 但 WAIT 必须说明"等什么价触发"。
- 无每日最低交易次数; 不为凑数降门槛; EV 为正仍为开仓前提。
- 测量对象 = Opportunity Frequency + Net EV + Execution Quality(真实记录)。

## 3. 每次思考必答 14 问（决策 JSON 必含）
1 当前市场状态 2 D1/H4/H1 是否一致 3 当前 M15 变化 4 有无可交易机会 5 机会机制来源
6 什么条件触发 7 什么条件使计划失效 8 预期收益 9 预期损失 10 交易成本
11 成本后 EV 是否仍为正 12 机会预计多久再现 13 交易 or WAIT 14 为什么

## 4. Trade Plan 先注册（不可篡改）
Trigger 之前必须写入 ledger（append-only, 带 sha256 链）。禁止看到结果后补计划。
字段全集见 contracts/TRADE_PLAN_CONTRACT.yaml。注册后任何人(含 Hermes 自己)不得修改;
取消 = 追加 cancel 记录(带原因), 不是改写。

## 5. 数据纪律
- 用真实数据(现有 parquet/tick): staging_fxtm(历史背景 D1/H4/H1) + live_fxtm(当前 M15/forward)。
- 发现缺失 → 记 DATA GAP; 不用假数据填补; 不停止 live 采集器。
- P0 = paper/forward observation; 无真实 API 时 fill 用 paper 模型(见 09_PAPER_LOOP), 明确标注 paper。

## 6. 执行纪律（P0 版）
- 本阶段不连接真实 broker; EXECUTION DATA GAP 维持(见 architecture/v1_trading_system/01_...)。
- 系统输出的一切 P&L 若为 paper → 处处标注; 无真实交易时 Dashboard 禁止显示虚假盈利。

## 7. 文件布局
```
research/hermes/trader_v1/
├── 00_TRADER_PROTOCOL.md        ← 本文件
├── contracts/                   ← 机器可读契约(JSON Schema 参考 + 字段说明)
│   ├── DECISION_CONTRACT.yaml
│   ├── TRADE_PLAN_CONTRACT.yaml
│   ├── TRIGGER_CONTRACT.yaml
│   ├── REVIEW_CONTRACT.yaml
│   └── MEMORY_CONTRACT.yaml
├── state_package.py             ← B: 确定性市场状态包生成器(无 LLM)
├── engine.py                    ← 闭环编排器: OBSERVE→…→MEMORY 单轮
├── review.py                    ← G: Trade Review 生成(确定性统计 + 待 Hermes 评注)
├── ledger.py                    ← 计划注册/不可篡改 ledger(sha256 链)
├── run_state/                   ← 运行时状态(decision/plan/waits/stats/paper positions)
├── memory/                      ← H: 交易记忆(决策/计划/结果/复盘归档)
└── logs/                        ← 每轮原始输出
```
