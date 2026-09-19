# V1.1 交易生命周期架构设计（重构蓝图, 2026-09-07）
> 依据: AUDIT_REPORT_20260907.md 审计结论 + 用户重构任务书
> 原则: 状态唯一可恢复可验证不可非法跳转 / 决策优先级唯一 / 不变量 FAIL CLOSED /
>        正确性优先于复杂度 / 无证据不声称赚钱 / 不破坏已工作基础设施

---
## 1. Hermes 核心职责升级
分析 → LONG/SHORT → SL/TP
升级为:
Observe → Understand → Opportunity → Tactics → Enter → Manage → Adapt → Exit → Review → Learn

- **Tactics(本次重构核心)**: 不仅决定方向, 还要决定怎么打这笔交易:
  立即进入 / 等回撤 / 等突破 / 突破后追入 / 突破失败反向 / 分批进入 / 小仓试探→确认加仓 / 不值得交易
- 市场理解: D1/H4/H1/M15 窗口是**输入候选非真理**; 状态包特征仅作状态信息, 不作机械策略组合。

---
## 2. Position State Machine(唯一状态模型)

```
FLAT ──(plan trigger+risk pass+fill)──► ENTRY_PENDING ──(fill ack)──► OPEN
OPEN ──(部分成交/试探仓确认)──► CONFIRMING ──(逻辑成立/加仓)──► PROFIT_EXPANSION
PROFIT_EXPANSION ──(逻辑成熟)──► MATURE ──(逻辑衰竭)──► EXHAUSTION
EXHAUSTION / 任何态 ──(退出决策)──► EXIT_PENDING ──(exit ack)──► CLOSED
任何态 ──(hard risk/invalidation)──► EXIT_PENDING(强制) ──► CLOSED
```

- 状态唯一: position_id 有且仅有一个当前状态(存 position snapshot, 幂等更新)。
- 合法迁移表(非法跳转 → FAIL CLOSED):
  | from | to | 触发 |
  |---|---|---|
  | FLAT | ENTRY_PENDING | trigger+risk pass |
  | ENTRY_PENDING | OPEN | fill ack(全部或部分>0) |
  | ENTRY_PENDING | FLAT | reject / cancel / 全部未成交 |
  | OPEN | CONFIRMING | 试探仓成交, 等待确认 |
  | CONFIRMING | OPEN | 确认后统一(或加仓) |
  | OPEN/CONFIRMING | PROFIT_EXPANSION | 逻辑成立+浮盈达状态阈值 |
  | PROFIT_EXPANSION | MATURE | 逻辑成熟(结构推进/趋势延续) |
  | MATURE | EXHAUSTION | 逻辑衰竭信号 |
  | 任意 | EXIT_PENDING | 退出决策(见优先级) |
  | EXIT_PENDING | CLOSED | exit fill ack |
  | CLOSED | (终态) | 不可再迁移 |

---
## 3. 决策优先级(唯一, 低优先级不得覆盖高优先级)

```
1. HARD RISK          (日亏上限/连亏熔断/杠杆上限/账户级硬风控 → 无条件执行)
2. POSITION INVALIDATION (原交易逻辑失效 → 退出)
3. EXECUTION SAFETY   (拒单/网络断/部分成交异常 → 状态修复优先)
4. EXTREME MARKET     (极端波动/spread 爆炸/事件窗 → 保护优先)
5. OPPORTUNITY CHANGE (新机会 vs 当前持仓的边际 EV 比较 → HOLD/REDUCE/EXIT/SWITCH)
6. PROFIT PROTECTION  (保本/利润保护, 状态转换而非固定价格)
7. TRAILING           (结构/波动/利润跟随, 单一 Stop Authority)
8. NORMAL MANAGEMENT  (常规复评/时间止损/仓位微调)
```

---
## 4. 止损/保本/Trailing/止盈 设计

### 4.1 初始 SL(回答"价格走到哪我的逻辑就错了")
- 基于: 初始风险 / 市场结构 / 波动率 / 当前价格位置 / 逻辑失效位置 / 正常噪声 / spread+成本
- 公式化检查(非固定美元):
  - 结构失效位(break structure) 为锚
  - SL 距离 ≥ max(噪声带宽(如 ATR_M15×k), 最小执行安全距离(含 spread))
  - 若结构失效位距 entry < 噪声带宽 → 该机会本不值得交易(拒绝, 不硬凑 SL)

### 4.2 保本 = 状态转换, 非固定规则
- 仅在满足以下才允许移保本: ① 交易逻辑已确认(有确认信号) ② 浮盈 ≥ 保本距离+噪声带宽
  ③ 移到 entry 不被正常噪声扫到 ④ 继续持有 EV ≥ 保护利润 EV
- 保本后即进入 PROFIT_PROTECTION 状态, 由 Stop Authority 统一管理

### 4.3 Trailing(三种逻辑, 由 Stop Authority 选一, 不打架)
- A. Structure trailing: 按价格结构(swing HL/LH)移动
- B. Volatility trailing: 距离 = k×ATR(当前), 随 vol 自适应
- C. Profit protection: 利润状态分级(如 1R/2R/3R), 每级对应最小保护距离
- **Stop Authority**: 任何时刻 SL 的唯一权威来源; 多规则触发时按 4.4 仲裁

### 4.4 止盈分类
- Fixed target(机会空间有限) / Runner(趋势扩张继续持有) / Partial TP(锁部分利润, 余仓正 EV) /
  Full exit(逻辑失效/机会耗尽/状态改变/反向证据/风险收益恶化/更好机会)
- **允许利润回撤**: 不因"保住胜率"过早杀盈利仓; 区分正常回撤 vs 反转
  (反转 = 结构失效或 Stop Authority 被触发; 回撤 = 仍在逻辑内)

---
## 5. 加仓/减仓(同一决策体系)
- 持仓中选项: HOLD / REDUCE / PARTIAL EXIT / ADD / FULL EXIT / PROTECT
- **ADD 铁律**: 禁止摊平亏损加仓; 加仓仅当新增信息使剩余机会 EV 上升;
  加仓后总仓位 ≤ max_position; 加仓是独立决策(重新过 risk_check)
- 机会成本: 持仓中遇新机会 → 比较 持有边际 EV vs 释放资本新机会 EV → HOLD/REDUCE/EXIT/SWITCH
- 单仓方向一致性: 同一 position_id 不允许方向翻转; 新方向 = 先 CLOSED 再新 position

---
## 6. Position Decision Contract(每次持仓管理结构化输出)
```
position_id, timestamp, current_position{qty,avg_entry,side,state},
market_state, original_thesis, thesis_status{valid|weakened|invalidated},
current_pnl{R,usd}, current_risk{to_stop_R}, current_volatility,
opportunity_remaining{high|medium|low|none}, expected_value_if_hold,
expected_value_if_reduce, expected_value_if_exit, opportunity_cost,
action{HOLD|REDUCE|PARTIAL_EXIT|ADD|FULL_EXIT|PROTECT|TRAIL},
action_reason, new_stop{level,authority}, new_take_profit{levels},
partial_exit_size, add_size, invalidation, next_review_condition, confidence
```
LLM 提出策略; Risk Engine 独立检查; Stop Authority 仲裁 SL。

---
## 7. 不变量(任何失败 → FAIL CLOSED)
```
I1 不允许未知仓位状态
I2 不允许重复订单(同 plan/position 的同一意图只发一次)
I3 不允许重复平仓(CLOSED 后不再 exit)
I4 不允许 SL 向风险更大方向移动(仅可收紧或保持)
I5 不允许 TP/SL 越过非法价格(LONG: SL<entry<TP; 边界含 spread 安全距离)
I6 不允许本地状态与 broker 状态永久不一致(不一致 → 停止新单 + 告警修复)
I7 不允许 Risk Engine 被 LLM 绕过(执行路径必经 risk_check)
I8 不允许未经授权进入真实交易(allow_trade=False 硬门)
I9 不允许旧 Trade Plan 再次触发(已触发/已取消计划不可复活)
I10 不允许未来数据进入决策(只消费已收盘 bar)
I11 不允许交易结束后状态仍 OPEN(CLOSED 终态)
I12 同一账户不允许存在方向冲突的持仓
```

---
## 8. 500× 杠杆与仓位分离
- Account Leverage(500×, 固定不可改) ≠ Position Size ≠ Risk Per Trade
- 仓位计算: risk_budget = equity × risk_per_trade_pct; lots = risk_budget / (SL_dist × contract)
- 检查链: SL 距离合理 → lots ≥ min_lot & ≤ max_lot → notional ≤ max → margin ≤ 可用(paper 模拟)
- 三者彻底分离, 禁止通过调 leverage 解决风险问题

---
## 9. 测试矩阵(重构实现时落地)
- 状态机: OPEN→CLOSE / PARTIAL→CLOSE / SL MOVE / TP MOVE / 非法跳转
- 失败注入: SL MOVE FAILED / ORDER REJECTED / NETWORK LOST / PROCESS RESTART /
  DUPLICATE EVENT / DUPLICATE ORDER / STALE QUOTE / SPREAD EXPANSION /
  EXTREME VOL / PARTIAL FILL / SIZE ROUNDING / MIN/MAX LOT / PRICE PRECISION /
  SL/TP DISTANCE / 500× / INSUFFICIENT MARGIN / 反向信号持仓中 / 新机会持仓中 / 多规则同时
- 类型: unit + integration + state-machine + restart/recovery + invariant + deterministic replay

---
## 10. 验证口径(正确性 vs 赚钱分开)
- Gross P&L − Spread − Slippage − Commission − Financing − Execution failure = Net P&L
- 统计: expectancy / profit factor / max DD / MAE / MFE / holding time / profit giveback /
  stop efficiency / TP efficiency / trailing efficiency / opportunity capture /
  missed opportunity / trade frequency / cost per trade
- 历史 replay + paper forward 双通道; 无证据不声称赚钱

---
## 11. 实施顺序(不破坏现有)
1. L0: H1/H2 幂等修复(现有 engine 上最小改动) ← 先做, 立即生效
2. L1: position.py 状态机 + position_decision.py + stop_authority.py(新模块)
3. L2: H3 未收盘 bar 修复 + risk 熔断落地 + review 接入
4. L3: 精度/min-max lot/方向约束/不变量引擎 + 测试矩阵(全部自动化)
5. replay: 用现有 staging+live 数据回放验证; 报告"哪些证明正确/哪些仍假设/数据缺口"
