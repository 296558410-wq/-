# 交易系统 V1 — 架构总设计（2026-09-07 初版）
> 状态: DESIGN · 阶段: Research/Simulation（V1 不允许自动实盘）
> 目标: 一个能持续运行的 XAUUSD 自动交易系统, 从市场数据到执行反馈到记忆改进的完整闭环。
> 不是一次性策略回测; 不是继续找论文 alpha; 是系统工程。

---
## 0. 总览与核心思想

**不是预测每一根 K 线**。核心循环:

```
观察市场 → 判断市场状态 → 判断赔率何时有利 → 制定交易计划 → 等待 M15 触发
→ 执行 → 独立风控 → 反馈/成交记录 → 交易记忆 → 按真实结果持续改进
```

决策哲学（与 CONSUMER 需求一一对应）:
- LLM 回答的是"当前什么状态 / 什么条件出现后赔率有利 / 何时取消 / 是否值得承担成本 / 为何 WAIT", 不是"涨还是跌"。
- LONG / SHORT / WAIT 都是合法输出, WAIT 不是失败。
- "高频"≠ 强加交易次数; = 高概率 + 非对称 + 成本后正 EV + 可重复 + 可执行, 机会频率由真实市场测量, 不预设。

---
## 1. 硬约束（CONSTITUTION 级, 不可绕过）

| # | 约束 | 状态(2026-09-07 核验) |
|---|---|---|
| H1 | **执行不以 MT5 为中间层**; 须为经纪商原生直接交易 API (REST/FIX/WS 级, 非 MT5 Server 名/登录接口/网页 API) | **FXTM = EXECUTION DATA GAP**（见 §2 与 01_EXECUTION_DATA_GAP.md, 证据完整） |
| H2 | 500× 是账户可用杠杆, 非系统风险杠杆; **Risk Engine 独立于 LLM**, 可否决 LLM | 设计约束, 立即生效 |
| H3 | V1 不允许自动实盘; 顺序: Research→Simulation→Paper→Demo→Execution Validation→(未来明确授权才实盘) | 设计约束, 立即生效 |
| H4 | 禁止为证明有效而改数据/过滤失败/挑选区间/事后调规则; 所有结果真实记录 | 设计约束, 立即生效 |

H2 细则: LLM 无权决定 max position / max account risk / max margin / max daily loss /
max consecutive loss / max drawdown / 突破硬风控。Risk Engine 为独立进程/独立代码路径, 参数来自
Risk Policy 文件（人工/审计可改）, 非 LLM 输出。LLM 输出含期望仓位 → Risk Engine 校验/否决/降级。

H3 细则: 本设计文档的后续一切实现都在 Simulation/Demo 边界内;
EXECUTION_GATE 解锁条件 = (a) 目标经纪商原生 API 存在且经小单实测, (b) 用户明确书面授权。

---
## 2. EXECUTION DATA GAP — 目标经纪商 API 核验（2026-09-07, 证据）

**判定: FXTM (ForexTime/Exinity, 当前账户 212070422, 服务器 ForexTimeFXTM-Live01) 无可靠原生直接交易 API → EXECUTION DATA GAP。不假装可直接交易。**

### 2.1 核验证据（E2 = web 实证核验; 2026-09-07, web_search 无 provider, 用 web_fetch + Bing/DDG）
1. [E2] FXTM 官网 (fxtm.com / forextime.com) 全站抓取 + Bing "FXTM API trading REST FIX official":
   结果全部为 登录/平台/帮助中心/投资产品/加盟页; **无任何 API trading 产品页**。
2. [E2] 对比组: FXCM 官方提供 3 个免费 API (FIX / Java / ForexConnect), 有专门页面
   (fxcm.com/markets/algorithmic-trading/api-trading) → FXTM 无对等物。
3. [E2] 第三方桥 (MetaApi / API2Trade 等) 存在, 但本质 = 在 MT5 终端/协议之上包 REST/WS,
   仍以 MT5 为中间层 + 第三方托管 + 付费订阅 → 违反 H1, 不采用。
4. [E1] MT5 Python API (现有采集器所用) = 终端自动化接口, 依赖本地 MT5 终端运行 + 登录,
   是"MT5 作为执行中间层" → 违反 H1 执行层要求; 仅可用于研究数据 (现状, 合规)。
5. [UNKNOWN] FXTM 集团旗下其它实体 (Forextime UK Ltd / Exinity Ltd 等) 是否对机构/白标提供 FIX,
   未经核验; 即便存在也非当前零售账户可达通道。不猜, 标 UNKNOWN。

### 2.2 EXECUTION DATA GAP 的含义（不是停滞, 是并行）
- 执行层研发**不依赖 FXTM API** 即可推进: Simulation → Paper 全在本地(见 §7 阶段门)。
- Demo/Execution Validation 阶段需要**另找有原生 API 的经纪商**（候选需核验: 原生 REST/FIX、
  XAUUSD CFD 或 GC 期货、零预算或小额、监管合规）→ 列为 DATA GATE 待用户批准项（预算相关, 按宪章 C 类）。
- 候选方向(仅清单, 不承诺, 需逐一核验): 有官方 API 的零售/ECN 经纪商(类 FXCM/OANDA/IG 模式)、
  或 CME GC 期货路径(IBKR 类, 与 hf_money_access_lab T2 同轨)。**禁止把 MT5 gateway/第三方桥当直接 API。**

---
## 3. 目标架构（数据流）

```
┌─────────────────────────────────────────────────────────────────────┐
│  Broker / Trading Server  (目标: 原生 API; 当前: EXECUTION DATA GAP)  │
└───────────────┬─────────────────────────────────────────────────────┘
                │ Market Data API (tick/bar, quote)
                ▼
        ┌───────────────┐     历史研究数据 (已有: staging_fxtm/duka/live_fxtm)
        │  DATA LAYER   │ ────► parquet/时间序列库 (bar+quote+trade+exec 统一 schema)
        └───────────────┘
                │ 标准化 bars: D1(20) / H4(48) / H1(24) / M15(执行层)
                ▼
        ┌───────────────────┐
        │  DECISION ENGINE  │  LLM 决策层 (见 §4)
        │  (D1+H4+H1 状态)   │  输入: 多周期市场状态包(数值化, 非裸K线直觉)
        └─────────┬─────────┘
                  │ 结构化 Trade Plan (见 §5)
                  ▼
        ┌───────────────────┐
        │  RISK ENGINE      │  独立于 LLM; 校验/否决/降级 (见 §6)
        │  (硬风控 + 参数)   │
        └─────────┬─────────┘
                  │ 通过后的 Plan (可执行约束内)
                  ▼
        ┌───────────────────┐      ┌──────────────────────┐
        │  M15 EXECUTION     │◄────►│  EXECUTION ENGINE     │
        │  TRIGGER MONITOR   │      │  (原生 Broker API)    │
        │  (等触发, 不预测)   │      └──────────┬───────────┘
        └───────────────────┘                 │ Fill/Reject/Slippage/Latency
                                              ▼
                                     ┌─────────────────┐
                                     │ RISK 实时回路    │ (止损/熔断/日亏上限独立执行)
                                     └─────────────────┘
                                              │
                                              ▼
        ┌──────────────────────────────────────────────────────┐
        │  RECORD LAYER: 订单/成交/拒单/滑点 → 交易记忆 → 复盘  │
        │  (真实结果, 无过滤; 失败交易也完整入库)                │
        └──────────────────────────────────────────────────────┘
```

架构原则:
- 各层**单向依赖**: Data → Decision → Risk → Execution → Record → Memory → (改进) → Decision。
- Risk 是独立旁路: Execution 受 Risk 实时控制, 不经过 LLM。
- 全部决策/成交/风控事件带 UTC 时间戳落盘; 回放可审计。

---
## 4. DECISION ENGINE — LLM 决策层（D1/H4/H1 状态机）

### 4.1 周期与输入
- D1: 最近 20 根 · H4: 最近 48 根 · H1: 最近 24 根（根数=用户指定, 默认值）
- 输入不是裸 K 线, 是**每周期数值化状态包**（Deterministic 预计算, 无 LLM）:
  - price structure（HH/HL/LH/LL 结构标注、区间高低点）
  - MA（如 20/50/200 的 slope/位置/交叉关系, 值可配）
  - RSI（14, 值 + 背离检测标记）
  - current volatility（ATR、RV、近 N 根极值）
  - support / resistance（摆点+整数位+前高前低）
  - trend / range 分类（ADX 类 + 结构判定, 输出类别与置信）
  - expansion / contraction（range 收缩/扩张状态机）
  - recent abnormal movement（跳空、脉冲、量异动标记; 与本地已证 E5 认知一致: activity→vol 是信息, 方向需谨慎）
  - MTF agreement / conflict（D1/H4/H1 状态是否同向/冲突/中性）

### 4.2 LLM 任务（禁止事项与必须事项）
**不回答** "现在涨还是跌?"; **不把指标机械组合成策略**; 指标只是状态信息。
**必须回答**:
1. 当前市场属于什么状态?（含 D1/H4/H1 各自状态 + 组合判定）
2. 当前最值得等待的机会是什么?（机会类型: 趋势延续/区间反转/突破/回踩等, 若无可写 NONE→WAIT）
3. 什么条件出现后赔率才开始有利?（可验证的触发条件, 非模糊描述）
4. 什么条件出现后必须取消计划?（失效/反证条件）
5. 若触发, 预期收益/风险结构?（R 倍数、目标位、止损位逻辑）
6. 当前是否值得承担交易成本?（成本敏感显式化: 入场 spread/slippage 预算 vs 预期 EV）
7. 若无优势, 为什么 WAIT?（WAIT 是合法决策; 必须有理由, 不空转）

### 4.3 决策输出契约（JSON schema, 全部字段强制）
```
decision: {
  utc_ts, symbol, decision_id,
  market_state: {d1:{...}, h4:{...}, h1:{...}, composite:"trend_up|trend_down|range|transition|unknown"},
  bias: "LONG|SHORT|NEUTRAL|WAIT",
  confidence: 0..1,
  opportunity_type: "breakout|pullback|range_reversal|exhaustion|none",
  plan: null | TradePlan(§5),
  rationale: 简短文本(供复盘, 非决策输入),
  model, prompt_version, llm_meta
}
```
- 所有 market_state 字段必须来自 deterministic 预计算层（可复算/可审计）, LLM 只做综合判断。
- LLM 输出必须能**完全复现回溯**: 同一状态包 → 同一输入的 prompt 可重放。

---
## 5. Trade Plan（结构化交易计划）

每次输出不是 BUY/SELL, 是结构化计划。字段（用户指定全集, 均有定义与取值规则）:
```
trade_plan: {
  plan_id, utc_ts, decision_id_ref,
  market_state: 摘要(指向 §4.3 market_state),
  bias, confidence,
  opportunity_type,
  entry_zone: {price_low, price_high, entry_style:"limit|stop|market_if_touch"},
  trigger_condition: 可机械判定条件(如 "M15 收盘价 > X 且 spread < Y bps"),
  invalidation_condition: 可机械判定条件(触发即取消, 无二义),
  stop_logic: {type:"structure|atr|percent", level, 理由},
  target_logic: {type:"structure|R_multiple|partial", levels:[...]},
  expected_R: 正数(R 倍数),
  expected_win_probability: 0..1(估计, 标注来源: 历史同类统计/主观→须降权),
  expected_loss: 金额或账户%(=风险预算, 受 Risk Engine 约束),
  estimated_cost: {spread_bps, slippage_bps, expected_total_bps, cost_in_R},
  expected_net_EV: 数值(以 R 计或账户%计) + EV 计算式,
  pre_registered: bool(计划是否在触发前注册/可审计)
}
```
- EV 判据（与宪章一致）: P(win)×AvgWin − P(loss)×AvgLoss − cost > 0。
- **触发前注册**: Trade Plan 在触发条件满足**之前**写入计划库(plan registry) → 防止事后挑选。
- expected_win_probability 默认被 Risk 按 0.5 保守处理, 除非来自 ≥N 次历史同类样本统计(防 LLM 幻觉概率)。

---
## 6. RISK ENGINE（独立于 LLM）

### 6.1 边界（LLM 无权决定, Risk 可否决）
max_position_lots / max_notional / max_account_risk_per_trade(% 或 R) /
max_margin_usage / max_daily_loss / max_consecutive_losses / max_drawdown /
硬风控开关(熔断)。来源 = Risk Policy 文件(versioned, 人工可改, 系统只读应用)。

### 6.2 实时回路（独立于决策回路执行）
- 订单级: 否决超限仓位/保证金; 拒绝在禁止时段/禁止事件窗(如重大公告 N 秒内)的市价入场。
- 持仓级: 止损单在经纪商侧(原生 API 挂单) + 本地监控双保险; 日亏上限触发 → 全平+当日禁开。
- 连续亏损上限 → 冷却期(次数×时长, 可配)。
- 杠杆: 即使账户 500×, Risk 层有效杠杆上限默认远低(如 ≤10-20× 级, 值在 Risk Policy, 人工确认)。

### 6.3 与现有资产的衔接
- Risk Engine 是**新独立组件**(无现有对应); 设计沿用宪章纪律 + DoD(先真跑后宣布/产出断言)。
- 回测/模拟期 Risk Engine 即启用（防止"模拟期无风控"导致统计失真）。

---
## 7. M15 EXECUTION LAYER

### 7.1 职责
- 在 M15 周期等待 Trade Plan 的 trigger_condition（等触发, 不预测, 不提前）。
- 触发判定机械化为确定性代码（无 LLM 参与触发; LLM 只建计划）。
- 需研究/实现的执行质量要素(用户清单): entry trigger / invalidation / stop / take profit /
  trailing / partial exit / time stop / spread filter / volatility filter / execution quality /
  slippage / fill latency / reject / opportunity frequency。
- **先测机会频率**: 不预设每日交易次数; 统计真实市场每天出现多少个符合计划质量门槛的机会。

### 7.2 过滤器（确定性, 执行前最后检查）
- spread filter: 入场时 spread ≤ plan.spread_budget（超限 → 等待/跳过, 记录为 skipped_spread）。
- volatility filter: 当前 vol 在 plan 假设的 vol 范围内（超限 → 跳过, 记录 skipped_vol）。
- time/event filter: 重大公告窗口、周末持仓规则等（记录 skipped_event）。
- 所有 skip 有原因落盘 → 复盘"机会被成本/环境吃掉的频率"（对应知识升级 L2/L4: 成本-状态自指）。

### 7.3 执行质量记录（Execution Report）
每单记录: request_ts / quote_asof / fill_ts / fill_price / fill_side / spread_at_fill /
slippage(bps) / latency(ms) / reject(若有, 含原因) / partial fill。全部真实入库(DoD 产出断言)。

---
## 8. RECORD / MEMORY / IMPROVEMENT（记忆闭环）

- 交易记忆库: 每笔(含 WAIT/计划取消/skip/失败)结构化入库:
  market_state / plan / trigger_evals / fill / pnl / outcome / review_notes。
- 复盘点: 定期(周)统计: 计划质量(触发率/胜率/EV 实现 vs 预估)、执行质量(滑点/拒单率)、
  WAIT 质量(等待是否避免亏损)。**无过滤**: 失败交易完整保留, 禁止事后剔除(硬约束 H4)。
- 改进回路: 复盘输出 → 状态包/计划模板/过滤器参数的建议修改 → 走预注册/回测验证才生效
  （防过拟合: 修改必须先在历史/模拟上验证, 不许直接上线"感觉更好"的规则）。
- 与现有资产衔接: 结果记忆落 research/money_hunter 同类结构(SCOREBOARD/STATE 纪律沿用);
  新知识进 hermes 知识库时遵循 KU-C 格式与迁移四类必查(KU-C35)。

---
## 9. 与现有资产映射（复用, 不重造; 缺什么标什么）

| V1 组件 | 现有资产 | 缺口/动作 |
|---|---|---|
| 历史/实时数据层 | data/staging_fxtm, staging_duka, live_fxtm + mt5 采集器(研究用) | 需统一 bar schema 构建器(D1/H4/H1/M15) |
| 成本/执行现实模型 | research/execution_reality (RQ-07 引擎, 无前视 fill 模拟) | 作为 Simulation 期 fill 层; 需 M15 触发接入 |
| 数据/通道解锁分析 | research/hf_money_access_lab (T0-T3 通道+成本) | 执行经纪商核验接续此表(见 §2.2) |
| 市场状态统计认知 | microstructure_drift 观察环 + hermes KU 库(E1-E3) | 状态包数值化需按本地已证认知校准(activity→vol 等) |
| 治理/宪章 | money_hunter CONSTITUTION + DoD(2026-09-07) | V1 继承; 阶段门按宪章上报规则 |
| Risk Engine | 无 | **新建**(独立组件, 见 §6) |
| LLM Decision Engine | 无(hermes 是研究侦察非决策) | **新建**(见 §4) |
| M15 Trigger/Execution | demo_exec_instrument.py(待 demo 注册) | **新建主执行路径**; 但 demo 注册仍值得做(测量执行环境) |
| 交易记忆/复盘 | failure_memory/claim_registry(研究侧) | **新建交易侧记忆**(见 §8) |
| Dashboard | money_hunter/dashboard(drift 观察) | V1 运行视图另设(不混入现有 drift dashboard) |

---
## 10. 阶段门（Roadmap; V1 不允许自动实盘）

| 阶段 | 内容 | 出口判据(DoD: 先真跑后宣布) | 依赖 |
|---|---|---|---|
| P0 Research | 状态包数值化定义+历史回放验证; M15 机会频率测量(历史) | 状态包在历史数据可复算; 机会频率统计出报告 | 现有数据 |
| P1 Simulation | Decision(LLM 状态综合)+TradePlan+RQ-07 fill 模拟闭环(历史) | 真实 tick 时间轴回放; 净 EV/分布报告; 无前视审计 | P0 |
| P2 Paper | 用 live_fxtm 前瞻 tick 跑实时 paper(决策-计划-触发-模拟成交) | 连续 N 日真实前瞻运行; 产出断言(文件/记录真实存在) | P1 + live 数据积累(14 天基线已在跑) |
| P3 Demo Exec | 目标经纪商原生 API 小单测量(EXECUTION_GATE 前置) | 见 §2.2: 经纪商原生 API 存在+用户批准; 小单实测 latency/slippage/reject | 用户批准 + 经纪商核验 |
| P4 Execution Validation | Demo 账户跑完整闭环(真实订单, 最小仓位) | 与 Paper 偏差报告; 执行质量达标 | P3 |
| (实盘) | **仅未来用户明确书面授权** | 另行设计(不在 V1) | — |

当前(2026-09-07): 处于 P0 入口。可立即推进: 状态包定义/历史复算 + M15 机会频率历史测量 +
live 数据继续积累(DoD 24h checkpoint 2026-09-08 核日增)。

---
## 11. 已知红线（写死, 不协商）
1. 不以 MT5 为执行中间层(§2 EXECUTION DATA GAP 明示, 不假装)。
2. LLM 不触碰风控参数(§6)。
3. V1 无自动实盘; 未经明确授权不进入真实资金(§1 H3)。
4. 数据/结果真实记录, 无过滤无挑选(§1 H4)。
5. 成本永远计入 EV; 预测能力≠赚钱能力; WAIT 合法。
6. 不购买付费服务推进架构(需预算项一律 DATA GATE 待批)。

---
*本文件为 V1 总设计主文档。子设计(状态包 schema/LLM prompt 契约/风控参数/执行引擎接口)在后续
子文档展开, 每份遵循: 先真跑后宣布, 产出断言, 根因证据确认。*
