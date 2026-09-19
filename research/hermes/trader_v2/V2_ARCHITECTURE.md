# Hermes V2 — 架构设计（第一阶段）

> 状态：Phase-1 设计冻结候选 · 2026-09-11 · 目录 `C:\AIQuant\research\hermes\trader_v2`
> 依据：用户《XAUUSD V2 第一阶段建设任务书》
> 铁律：**V1 完全不动**（`research/hermes/trader_v1` 只读，不 import、不改、不共用状态/账户/ledger/记忆）。

---

## 0. 一句话
Agent1（技术/市场情报）+ Agent2（宏观/地缘/资金流情报）持续产出结构化情报 → **Hermes V2 不投票、自主寻找正期望机会** → 独立模拟账户执行 → 完整可审计 ledger → 自动复盘。

---

## 1. 与 V1 的隔离契约（硬性）
| 维度 | V1 | V2 |
|---|---|---|
| 目录 | `research/hermes/trader_v1/` | `research/hermes/trader_v2/` |
| 代码 | 不 import V2 | **不 import V1**（拷贝必要逻辑，独立演进） |
| 账户/通道 | FXTM MT5 demo（MT5 终端，magic=90002） | 独立模拟账户（见 §8；默认本地 paper，可插 OANDA） |
| ledger | `trader_v1/run_state/plan_ledger.jsonl` | `trader_v2/ledger/v2_ledger.jsonl`（独立 sha256 链） |
| 记忆/状态 | `trader_v1/run_state`,`memory/` | `trader_v2/state`,`reviews/` |
| 调度 | cron `hermes-trader-m15-cycle` | 独立 cron（独立 session，不复用 V1 job） |
| 数据 | `data/live_fxtm`（MT5 采集，V1 拥有） | 见 §9：V2 自采（**只读** V1 的 live tick 或独立源，绝不写入/占用 V1 采集器） |

**V2 不得**：停止/修改/降级 V1、复用 V1 终端或账户、写 V1 任何文件、让 V2 结果影响 V1。

---

## 2. 组件架构
```
XAUUSD 实时市场（独立行情源）
        │
   ┌────┴─────┐
   ▼          ▼
 Agent1      Agent2                ← 情报采集 + 结构化（LLM 只做"情报综合"，不做交易）
 技术/市场    宏观/地缘/资金流
   │          │
   └────┬─────┘
        ▼
   Hermes V2                        ← 唯一的交易决策者：自主寻找机会（非投票）
        │  TRADE / WAIT / REJECT
        ▼
   Engine V2（确定性）               ← 风控 / 计划注册 / 触发 / 执行 / 持仓 / 对账 / 复盘
        ▼
   V2 模拟账户（独立余额/仓位/PnL）
        ▼
   V2 Ledger（含 provenance，可追溯"当时看到了什么"）
        ▼
   自动复盘（含"为什么没有交易"）
```
- **OpenClaw = 主控**：调度 Agent1/Agent2/Hermes/Engine、管任务队列、异常监控与自恢复、每日复盘、版本与 git 记录。用户不手工搬数据。

---

## 3. 目录结构（已建）
```
trader_v2/
├── README.md
├── V2_ARCHITECTURE.md          ← 本文件
├── V2_PHASE1_PLAN.md           ← 建设计划 + 开放决策
├── config/v2_config.json       ← V2 独立配置（路径/节奏/账户参数/因子开关）
├── contracts/                  ← 机器可读契约（decision/plan/ledger/agent1/agent2）
├── agents/
│   ├── technical/              ← Agent1: 采集器 + 情报生成
│   └── macro_global/           ← Agent2: 宏观/地缘/资金流采集 + 情报生成
├── hermes/                     ← Hermes V2 决策（prompt/契约/机会发现流程）
├── runtime/                    ← 编排/定时/任务队列
├── ledger/                     ← 独立 append-only + sha256 链
├── reviews/                    ← 自动复盘
├── state/                      ← 运行时状态（快照/持仓/统计）
├── research/                   ← 研究产出（报告/分析）
└── logs/                       ← 每轮原始输出
```

---

## 4. Agent1 — 技术/市场情报（规格）
**输入**：V2 独立行情（M5/M15/H1/H4/D1 已收盘 bar）。**禁止**单根 K 线机械预测。
**输出（结构化，落盘 `state/agent1_latest.json` + 版本化快照）**：
```
时间 / 市场状态(趋势|震荡|突破|回撤|高波动|流动性异常)
1H / 15M / 5M：趋势 / 结构(HH-HL-LH-LL) / 波动(ATR, RV, expansion|contraction)
VWAP / EMA(20/50/200) / 支撑阻力 / 突破 / 假突破 / 回撤反应 / 突破跟随
多周期结构一致性(领先周期/冲突周期)
关键价格 / 潜在机会 / 机会成立条件 / 机会失效条件 / 证据强度 / 不确定性
```
Agent1 绝不输出裸 `LONG/SHORT`；只给证据与状态。

## 5. Agent2 — 宏观 + 全球局势 + 黄金资金流（规格）
**三层**：
- A 全球宏观：Fed/ECB/BOJ/PBOC、利率与预期、CPI/PCE/PPI/NFP/失业/初请/GDP/PMI/ISM、美债收益率、实际利率、DXY、VIX。判断"宏观如何改变黄金定价环境"，不做"数据好=金跌"。
- B 全球局势：战争/冲突/中东/俄乌/中美/台海/制裁/贸易/政治/主权风险。**必须分级：事实 / 市场确认 / 新闻报道 / 推测**；未确认消息不得作为交易事实。
- C 黄金资金流：GLD/全球黄金 ETF 持仓与净流入流出、央行购金、COMEX/COT。重点：**叙事 vs 真实资金是否背离**（背离必须标记）。
**输出**：结构化（时间/宏观环境/事件/全球局势+可信度/ETF 持仓与变化+异常度/央行/COMEX-COT/综合 BULLISH|BEARISH|NEUTRAL|UNCERTAIN/核心依据/主要风险/**与技术面的潜在冲突**）。

## 6. Hermes V2 — 机会发现（核心，非投票）
**禁止** `A1=LONG + A2=LONG ⇒ LONG`。Hermes 可接受/反驳任一 Agent、可发现两者都未指出的机会、可等待、可放弃。
**每次新市场状态执行 20 步**（任务书 §八）：取情报→取实时状态→判 regime→找机会→查技术/宏观/资金流/风险事件→查是否已被定价→找证据冲突→判成立/失效条件→判风险收益比→决定 TRADE/WAIT/REJECT→(TRADE: 方向/入场/止损/止盈/风险/预期持有)→模拟执行→持续跟踪→平仓→自动复盘。
**必须记录"为什么没有交易"**（机会发现/未执行/放弃的原因）。
**目标**：不是预测每次价格变化，而是**主动寻找值得下注的机会**。

## 7. 决策契约（`contracts/DECISION_CONTRACT.json`，草案字段）
```
cycle, ts_utc, market_price,
decision: TRADE|WAIT|REJECT,
direction: LONG|SHORT|null,
opportunity_id, opportunity_thesis, discovered(vs A1/A2 关系: agree|refute|independent|none),
regime, priced_in_assessment, evidence_conflicts[],
entry_zone{low,high}, trigger_condition, invalidation_condition,
stop_logic{type,level_price}, target_logic{levels[{price,frac}]},
expected_R, expected_win_probability, cost{spread_bps,slippage_bps,latency_ms},
expected_net_ev, risk_lots, max_holding_time, expected_hold,
no_trade_reason (WAIT/REJECT 必填: 发现机会?为何未执行/放弃),
agent1_ref{snapshot_id}, agent2_ref{snapshot_id},
confidence, model, prompt_version
```

## 8. 模拟账户与执行（独立、可插拔）
- **Phase-1 默认：本地独立 paper 账户**（独立 balance/positions/orders/PnL，落 `state/account.json`），**不用理想成交价**：以真实 live mid/bid/ask 为基准，叠加 **spread + 滑点 + 延迟** 成本模型（参数在 config）。
- **执行通道适配器接口**（`execution_backend`）：`paper_local`（默认）｜`oanda_v20`（预留；用户注册 OANDA demo + token 后启用）。
- 真实资金：**硬门关闭**（`allow_real=false`）。
- 最小单位/精度/成本按 XAUUSD CFD 规格（0.01 手起）。

## 9. 数据与"无未来泄漏"纪律（最高级别）
- Agent 在时间 T 判断，**只能用 T 时刻已公开可得的信息**。
- 每个数据点记录：`data_source / data_timestamp(发布时刻) / retrieval_timestamp / source_version`；缓存落 `data_cache/`（带发布时刻）。
- 特别处理发布时点：宏观数据发布、新闻发布/更新、ETF 持仓发布、COT 发布（周五收盘后）、央行数据、经济数据修订、行情时间戳。禁止"数据库已更新=历史决策可见"。
- **可达数据源（已实测）**：Yahoo Finance（`GC=F`/`XAUUSD`、`DX-Y.NYB`、`^TNX`、`^VIX`、`GLD`）、US Treasury、ECB、CFTC（COT）、SPDR Gold Shares、iShares GLD、CNBC RSS 等新闻源。
  不可达：FRED（超时）→ 用 Yahoo/财政部替代。Stooq 需换 URL。

## 10. 节奏与调度（建议默认，可调）
| 任务 | 频率 | 形态 |
|---|---|---|
| Agent1 技术情报 | 每 15 分钟（M15 收盘后） | 采集器(确定性) + LLM 情报综合(隔离 session) |
| Agent2 宏观/资金流 | **每 1 小时 + 事件触发** | 采集器 + LLM 情报综合 |
| Hermes V2 决策 | 每 15 分钟 | LLM 决策（读最新 A1 + 最近 A2 + 实时行情） |
| Engine V2 执行/管理 | 每 15 分钟 | 确定性 |
| 每日复盘 | 每日（收盘后） | 确定性 + LLM 评注 |
> 注：每轮 3 次 LLM 调用（A1/A2/Hermes）会消耗 token；先按此跑，成本可再议。

## 11. Phase-1 完成标准（任务书 §十六）映射
A Agent1 稳定产出 ✅目标 / B Agent2 稳定产出宏观+地缘+资金流 ✅目标 / C Hermes 持续取双情报并主动找机会 ✅目标 / D 独立模拟账户执行 ✅目标 / E 完整 ledger（含 provenance 与"为什么没交易"）✅目标 / F V1 仍正常未被干扰 ✅必须核验 / G 可审计（4 问可回答）✅目标。
> 完成后：**先跑真实市场观察，不立即调参**；样本足够再进 Phase-2（机会质量分析与策略进化）；最终比较 **V1 vs V2 的增量价值**。

## 12. 明确不做（Phase-1）
不改 V1 / 不实盘 / 不为收益疯狂调参 / 不先训复杂模型 / 不先假设回测有效 / 不让 Agent 投票决定交易 / 不让宏观新闻或单根 K 线直接触发交易。
