# V3_ALPHA_MAP.md（draft v0 · 骨架 + 已证实状态回填）

- 产出：`@default`（Hermes Agent，组G 守门/反方）· 2026-09-17 · 房间：v3新项目的开发
- 依据：`TEAM_PLAN_V3_20260917.md §22`（赵先生《V3 总任务书》受理）+ 研究真相源 `C:\AIQuant\research\hermes\memory\{claim_registry,dead_end_index,contradiction_registry}.yaml`
- **本节零市场数字**。表中每个状态都是**指针**（指向已落证据或已登记裁定），不含任何新的市场结论。
- 状态词表：对外用任务书三值 `KEEP / REJECT / UNCERTAIN`；括号内为 registry 细分（`SUPPORTED / DATA_GAP / INACCESSIBLE / CONTRADICTED / METHODOLOGY_RISK`）。
- **本表唯一权威版仍在房间方案文档**；本文件是 §十八 Alpha Map 的第一版骨架，后续只追加、不改判。
- 纪律：`REJECT` 行**不得**在无重开条件命中时重跑（任务书 §十二「防止重复测试相同假设」）；`UNCERTAIN` 行必须**先登记再跑**（§22.5 组G 契约）。

## 一、Alpha 族 × 状态 × 数据层档

数据层档：`A` = L1 报价可算（DUKA tick 现有列）；`B` = 仅代理可算（须标 `proxy=true`）；`C` = 现在结构性不可算（DATA_GAP / 禁用代理冒充）。

| # | Alpha 族 | 状态 | 依据（指针） | 档 | 下一步 / 归属 |
|---|---|---|---|---|---|
| 1 | 无条件方向动量（M1+ 15–240m） | **REJECT** | `DE-01`（F-R1/F-R17，两期双源 0 SUPPORTED） | A | **补测**（非重开）：≤3m tick 事件时间层，须登记 |
| 2 | 无条件均值回复（M1+ zscore/dist） | **REJECT** | `DE-02`（F-R2） | A | 仅「条件于结构/事件的 MR」可作新实验 |
| 3 | session / 小时条件方向 | **REJECT** | `DE-03`（F-R6） | A | 仅允许作**分层变量** |
| 4 | K 线/蜡烛形态增量预测 | **REJECT** | `DE-04`（ΔIC −0.0047，CI 含 0） | A | 仅描述性；蜡烛代理速度=自动 REJECT |
| 5 | ≥5m 聚合微观方向（OFI / imbalance） | **REJECT** | `DE-05`（F-R11 / KD-C07） | A | **重开条件已命中**：≤3m tick 事件时间层（DUKA tick 到位）⇒ 见 #6 |
| 6 | **tick 层（秒~≤3m）微观方向族**（quote imbalance / quote-OFI / micro-price 偏离） | **UNCERTAIN（有依据重开，KD-U01）** | `DE-05` 重开条件 + §22.3-2 | A | `@待指派`：事前登记 + 多重检验按族内**累计 n** + 跨期两独立时段 + 成本后净额 |
| 7 | 短周期 momentum / reversal（tick 事件时间层） | **UNCERTAIN** | `DE-01`/`DE-02` 重开条款 | A | 同上；必须**事前**定义入场/出场与 hold |
| 8 | Spread shock（点差突变 → 后续路径） | **UNCERTAIN** | `R`/§14.6 未登记项 | A | 先登记（阈值/样本窗/多重比较矫正/hold-out 锁定） |
| 9 | volatility clustering / acceleration | **REJECT（作方向信号）** | `DE-06`（重开条件=禁止） | A | 只进 risk / execution 层 |
| 10 | activity → 未来波动（非方向） | **KEEP**（SUPPORTED，E5） | `CL-01`（双源双期 IC 0.60–0.89） | A | 已有；作**风险/成本层输入**，禁当方向 |
| 11 | spread → 未来波动（非方向，负相关） | **KEEP**（SUPPORTED，E5） | `CL-02`（DUKA −0.55~−0.59 / FXTM −0.22~−0.29） | A | 同上 |
| 12 | 做市 spread capture | **REJECT**（INACCESSIBLE） | `DE-08` + `CL-09` CONTRADICTED | C | 重开=INFRA_UNLOCK（maker 通道 + L2）；短期不可能 |
| 13 | liquidity withdrawal / replenishment | **UNCERTAIN（B 档代理）** | §22.2 B 类 | **B** | 只能由 L1 挂量代理；产物必须写明代理失效模式 |
| 14 | signed trade flow / aggressor / buy-sell pressure | **DATA_GAP**（INACCESSIBLE） | §22.2 C 类（DUKA 为报价源） | **C** | 须新数据源（成交流）；**禁**用 quote-OFI 冒充 |
| 15 | 真 order book imbalance / 深度 / 队列位置 | **DATA_GAP** | `DE-08`；`33333` 已决定「队列位置不建模」 | **C** | 重开=INFRA_UNLOCK（L2） |
| 16 | 跨市场 lead-lag：DXY → 黄金 | **REJECT**（CONTRADICTED） | `CL-10` / `CONTRA-08`（rahulsp 2026：同时性非预测性，OOS R² 全负） | C | **原样重跑=自动 REJECT** |
| 17 | 跨市场 lead-lag：XAG / GC / COMEX | **DATA_GAP** | `DE` 重开条件 `DATA_UNLOCK`：COMEX/GLD 接入（**非** DXY 链） | **C** | 组D **暂缓**；且 Δt=100ms/500ms/1s 档在零售可得数据上判 `UNRESOLVABLE`（**禁填 0**） |
| 18 | 事件 / 新闻冲击（宏观日程） | **KEEP（非方向）** | `CL-04`（宏观日程驱动 activity 簇聚，E4） | A/B | 起点可用；只是 activity 分层 |
| 19 | 事件后几秒~分钟可执行模式 | **UNCERTAIN** | `CL-12`（快反应 INACCESSIBLE，慢反应未验证） | B | 需事件时间戳源 + 同精度 tick；须登记 |
| 20 | 订单流 → 汇率（Evans-Lyons 型客户流） | **REJECT / 永久 dead end** | `DE-09` + `CL-08` INACCESSIBLE | C | 重开条件=无（数据根本不可公开获取） |
| 21 | 黄金 VRP（卖 vol） | **DATA_GAP** | `CL-11`（无期权数据） | C | 重开=期权数据接入 |
| 22 | 风险/成本择时（R1 形态条件化） | **UNCERTAIN** | `DE-07` 重开条款「形态条件化」；`CL-15` REJECTED（无条件 gate） | A/B | 需先 autopsy 定风险形态；成本 regime 对 XAUUSD `CL-06` 仅 E3 且未验证 |
| 23 | ML 组合（特征组合/分类/回归/序列） | **未到（不评分）** | 任务书 §十F「ML 最后进入」；`CL-14` 提醒 LLM/passive 暴露 | — | 前置=**至少 1 个 KEEP 特征**；当前**已测特征上 0 个方向 KEEP** |
| 24 | 参数化 look-ahead / 泄漏审计（守门工具） | **METHODOLOGY_RISK（常设）** | `CL-13`（deepseek cutoff 与 XAUUSD 历史重叠） | — | 组G 常设审计项；任何 KEEP 必过 |

## 二、计数（本版骨架，仅结构统计，不含市场数字）

- `KEEP` = **3**（#10 #11 #18；**全部非方向 / 全部只进 risk·execution 层**）
- `REJECT` = **9**（#1 #2 #3 #4 #5 #9 #12 #16 #20）
- `UNCERTAIN` = **6**（#6 #7 #8 #13 #19 #22）
- `DATA_GAP / INACCESSIBLE` = **4**（#14 #15 #17 #21）；另外 #12 同时计入 `REJECT`，其不可及属性为 `INACCESSIBLE`（同一行两类标注，不重复计一格）
- **未评分** = **1**（#23，前置未满足）
- **方向类 KEEP = 0**。这是当前 Alpha Map 最重要的一格。

## 三、阻塞与前置（决定本表能否从"骨架"变成"证据表"）

1. **真实 tick 未进房间**（唯一硬阻塞）：`@1` 读不到 `C:\AIQuant\data\staging_duka\assembled\`。缺真实两段 tick ⇒ `--ticks2` 只能 `INSUFFICIENT_DATA` ⇒ 本表**一个真实数字也填不了**。三条解法见房间方案文档 §22.6。
2. 组G 契约（不登记不跑 / 事前锁定 / 族内累计 n / 只认盘上 sha256 / KEEP 须过成本后净额+压力表+跨期+placebo）已生效，见 §22.5。
3. 未登记即跑出的任何结果**不得**进入本表（可复跑，但不受理）。

*本文件由 AI Agent（`@default`）产出，只给工程与统计口径，不构成投资建议，不承诺任何收益。*
