# XAUUSD HIGH-FREQUENCY EDGE MAP — 系统级价值地图（v2, 2026-09-06）

> MASTER MISSION 交付物（修订版 2）: 机制宇宙 + 证据融合 + 可及性 + 可观测性 + 本地映射 +
> Hermes 映射 + Top Questions + 系统蓝图 + 瓶颈。
> v2 相对 v1（2026-09-05 23:14）的触发: **HERMES-10 反证于 2026-09-06 08:06 入库**
> （vol/成本择时盈利 WEAKENED）。本文件是叙述层；机器可读细节见同目录 YAML
> （证据层 = EVIDENCE_CONVERGENCE.yaml）。**这不是策略清单，不是 alpha 证明，不假设任何机制有效。**

---

## 0. v2 第一修正（HERMES-10 特别修正，全图适用）

**不要再把 "risk/cost timing" 写成 "当前最可接近盈利 edge"。**

正确状态（CONTRA-09，来自 JFE limits-to-arbitrage + Elsevier disappearing profitability）：
- `ACTIVITY → FUTURE VOLATILITY` = **CONFIRMED INFORMATION**（本地 E5，双源双期，未被动摇）
- `VOLATILITY INFORMATION → PROFITABLE TIMING` = **UNPROVEN / WEAKENED**（成本后归零 + 2000 年后消失 + R1'-B 本地负证据）

推论：Risk/cost 信息保留为 **POSSIBLE INFORMATION LAYER**（风险管理/执行调度输入），
**不得提前升级为 PROFITABLE EDGE**。v1 中 M07/M18 等条目的 "唯一 ACCESSIBLE 簇/有肉" 表述已全部改写；
TIER 1 研究问题全部按信息层声称边界重写（TOP_RESEARCH_QUESTIONS.yaml）。

---

## 1. 核心问题一图流（25 机制，经济簇去重后 22 条独立线）

| 位置 | 机制 | 判定口径 | 证据 |
|---|---|---|---|
| **理论价值高但拿不到** | M01 信息延迟 · M04/M05/M06 做市簇 · M03/M22 订单流/队列 | INACCESSIBLE（INFRA_UNLOCK 前勿投入；TIER 3） | E2/E3 他市场；本地不可观测 |
| **机制真实但缺数据** | M11 VRP · M13 basis · M14 期权 · M19 RV · M20 多腿 · M25 跨资产 · M12 真套利链 | DATA GAP（≠ REJECTED；解锁即重评） | E2/E3 他市场/CONFLICTED |
| **可及但已证伪（已测空间）** | M08/M09 动量/反转（无条件）· M20 单腿 | CLOSED-REJECTED（重开需新信息维度或 ≤3m 补测） | E5-负 本地双源双期 |
| **可及、非方向、E5 确认** | M10 vol 聚集/activity→vol | SUPPORTED-NON_DIRECTIONAL（风险/成本输入） | E5 本地双源（唯一 E5 信息层） |
| **可及、中间层、未研究 ★** | M17 成本预测 · M02/M15 事件结构 · M18 切换先行 · M23 冲击窗 · M24 fix 窗 | OPEN（→ Top Questions；信息层定位） | 输入 E4/E5；可预测性本身 E0-E3 |
| **外部反证削弱** | M14 期权 IV（借券费代理）· M25 DXY lead-lag（OOS 负）· 无条件 vol-timing 盈利 | CONTRADICTED / WEAKENED（期待降级） | Muravyev 2025 / rahulsp 2026 / HERMES-10 |

**结构性事实（本图最重要的单一洞察，v2 不变）**：价值与可观测性**负相关**——理论上最肥的层
（订单流、簿深度、做市、队列）恰好完全不可观测；完全可观测的方向层（M08/M09）已被证伪。
v2 新增第二洞察：**信息可预测 ≠ 盈利可接近**（HERMES-10）——可验证价值的分布偏向中间层的
**信息/成本/风险输入**，且任何盈利声称必须过成本瓶颈。

## 2. 证据融合总则（HARD RULE #2；详见 EVIDENCE_CONVERGENCE.yaml）

- 每条机制挂: PRIMARY_SOURCES / INDEPENDENT_REPLICATIONS / COUNTER_EVIDENCE / LOCAL_EVIDENCE /
  HERMES_EVIDENCE / EVIDENCE_GRADE + **INDEPENDENT_EVIDENCE_COUNT**。
- 计数纪律：10 篇互引同一原始论文 = 1 条独立线；同团队双源双期 = 1 条本地线；
  外部文献多为他市场且成引用链 → 独立计数保守偏低（见文件 meta.counting_rule）。
- 独立证据最强的条目：**M10 activity→vol = E5 CONFIRMED（独立线 4）**；
  其次 M17/M18 信息层输入（E4/E5，独立线 2-3）。
- 诚实结论：**无任何机制在当前可及性下达到 E6**（XAUUSD OOS+成本+执行后）。
  对 "盈利 edge" 层，"无当前可及机制有足够证据进入立即研究" **成立**；
  对 "信息/风险/成本输入" 层不成立——那正是 Top Questions 的研究对象（研究候选 ≠ 盈利证明）。

## 3. 可观测性（任务最重要维度；详见 OBSERVABILITY_MATRIX.yaml）

- DIRECTLY_OBSERVABLE: M08/M09/M10；PROXY_OBSERVABLE: M02/M15/M17/M18/M24；
  WEAK_PROXY: M06/M07/M12/M16/M21/M23；NOT_OBSERVABLE: 其余 11。
- v2 proxy 纪律（HERMES-10 硬化）：activity ≠ order flow；volume ≠ signed flow；
  spread ≠ full liquidity；毛量≠净流（HBS）；volume 归一化破坏信号（arxiv 2512.18648）；
  raw OBI 被 flicker 污染（arxiv 2507.22712）；VPIN 增量弱（Andersen-Bondarenko）。
  → 一切 activity/volume 派生 proxy = "加标签的噪声代理候选"，报告一律 proxy 语言。
- 对 E5 activity→vol：代理风险 = 加标签警示，非推翻（双源双期仍立）。

## 4. 可及性（详见 ACCESSIBILITY_MATRIX.yaml）

- POSSIBLY/PARTIALLY_ACCESSIBLE = M02/M07/M08/M09/M10/M12/M15/M16/M17/M18/M21/M23/M24；
- 但 v2 关键限定：中间层（M07/M17/M18/M21/M23）只开放 INFORMATION/PROXY 层，
  **不开放 "盈利 edge" 声称**（盈利须预注册实验 + 成本建模 + 执行模拟）。
- INACCESSIBLE（12）= 结构性/数据性封锁；INACCESSIBLE ≠ NO VALUE（理解价值保留）。

## 5. 本地研究映射结论（详见 LOCAL_RESEARCH_MAPPING.yaml）

- **已浪费/死路（勿再投入）**：无条件方向族 M1+ 15-240m（F-R1..R17 + Phase9 27/27）；
  vol 当方向信号（DE-06）；蜡烛增量预测（F-R16）；无条件日级降险 gate（R1'-B）；
  DXY lead-lag（外部反证）。dead ends 全部带 reopen condition（dead_end_index DE-01..09）。
- **没真正研究**：M17 成本状态可预测性、M18 切换先行、M24 fix 窗、M02 事件反应形态、M07 AS 条件描述。
- **只是缺数据**：≤3m tick 层终审、R1'-A-DUKA（D2）、事件日历、期权/期货/跨资产、执行模拟器校准。
- **值得投入**：TIER 1 四项信息层研究 + TIER 2 数据解锁项。

## 6. Hermes 情报映射（CONFLICT 记录，不自动消解）

- 与本地高度一致：方向层关闭（CL-03）、vol 信息非方向（CL-01/02）、做市/订单流不可及（CL-08/09）、
  无条件 gate 负（CL-15）、期权 IV 期待降级（CL-07）、DXY lead-lag 反证（CL-10）。
- CONF-1（Hermes "R1 唯一有肉" vs 本地 R1' EDGE UNCERTAIN/FEED-LIMITED）：v2 由 HERMES-10 部分裁决——
  双源都承认的是 **非方向信息层**；"盈利有肉"主张被外部反证削弱 → 记录为
  "信息层开放、盈利层 WEAKENED"，不做任何一侧的自动胜出。
- CONF-2（spread→vol 历史 IC vs REP "表示≠预测"）：记录；预测层未测 → RQ-H1 正是其检验。
- Hermes = INTELLIGENCE SOURCE，非 FINAL AUTHORITY；独立外部证据多为 E2-E4 级（计数纪律见 §2）。

## 7. Top Research Questions（5/5 合格；上限不是配额；完整字段见 TOP_RESEARCH_QUESTIONS.yaml）

| ID | 问题 | 机制 | 定位 | 反证 |
|---|---|---|---|---|
| RQ-H1 | 交易成本状态是否可预测 | M17 | 成本/执行信息层 | 完整（成本纪律内置） |
| RQ-H2 | 宏观日程窗反应结构 | M02/M15 | 事件时间结构/成本层 | 完整（双期对照内置） |
| RQ-H3 | 状态切换先行统计 | M18 | 风险管理输入 | 完整（声称边界 = 非盈利） |
| RQ-H4 | tick 冲击后流动性风险窗 | M07 | 风险层描述 | 条件（W1 审计先行） |
| RQ-H5 | fix 定盘窗 autopsy | M24 | 日历型风险/成本窗 | 完整（零成本） |

共同点：非重复、机制明确、至少 PROXY_OBSERVABLE、成本可建模、非收益 re-encoding、
当前/可获数据可验证、声称边界 = 信息/风险/成本输入（HERMES-10）。
反证汇总：0 降级 / 1 条件 / 4 完整——不构成 "有肉" 证据，只构成 "值得一问"。

## 8. 组合与分配（详见 HFT_RESEARCH_PORTFOLIO.yaml）

- TIER 0 不再研究（已测/已封/外部反证）· TIER 1 当前投入（RQ-H1/H3/H2/H5，信息层）·
  TIER 2 数据解锁即升（tick/D2/日历/期权）· TIER 3 有 barrier 不投入（做市簇/basis/套利/VRP/延迟）·
  TIER 4 低值饱和（含无条件 vol-timing 盈利——外部反证）。
- 分配原则：算力/工程 → TIER 1 实验 + TIER 2 数据解锁；**TIER 3 理论价值高不构成投入理由**。

## 9. 系统蓝图与瓶颈（详见 HFT_SYSTEM_BLUEPRINT.md / SYSTEM_BOTTLENECKS.yaml）

- 八类瓶颈显式识别（HARD RULE #3）：KNOWLEDGE / DATA / OBSERVABILITY / LATENCY / EXECUTION /
  COST / INFRASTRUCTURE / RESEARCH_METHODOLOGY——全部映射到 BN-1..BN-9。
- 排序：**OBSERVABILITY（BN-1）> COST（BN-9）> DATA（BN-2/3/4/6）> EXECUTION（BN-5）>
  LATENCY（BN-7）> METHODOLOGY/KNOWLEDGE（BN-8）**。
- 机会 vs 瓶颈：最大价值池（微观结构）被最硬瓶颈（观测面，结构性不可逆）封锁；
  当前唯一可推进的是被 DATA/EXECUTION 部分封锁的中间层信息研究。
  **瓶颈战略价值 > 机会数量**——不因 TIER 3 池子肥而分流资源。

## 10. 最终回答（任务十八的 12 问）

1. **世界上的钱可能在哪里？** ① 微观结构层（订单流/做市/队列/延迟——最大池，机构侧）；
   ② 中间层信息（成本状态/vol 风险状态/事件时间/流动性窗——小而未被认真开采）；
   ③ 跨资产/期权/期货结构（basis/VRP/IV/相对价值——机制真实但需数据与通道）。
   已测空间的方向层：无成本后价值（已排除，不是钱所在）。
2. **哪些钱我们当前拿不到？** ① 全部微观结构/做市簇（无 L2/maker/共址/延迟）；② 期权/期货/实物链
   （无数据无通道）；③ 事件抢跑（延迟 100ms+）。→ 12 条 INACCESSIBLE。
3. **哪些钱我们能观察？** M08/M09/M10（直接）+ M02/M15/M17/M18/M24（proxy）+ M07/M23 等（弱 proxy）。
   观察 ≠ 价值（M08/M09 已证伪）。
4. **哪些钱我们能验证？** 中间层信息：成本状态可预测性（RQ-H1）、切换先行统计（RQ-H3）、
   事件窗结构（RQ-H2）、fix 窗痕迹（RQ-H5）——大部分现有数据可测；≤3m/跨源验证等 DUKA tick/D2。
5. **哪些钱理论上有价值但当前无法接近？** TIER 3 全簇 + DATA GAP 簇（见 §1 前两行）。
6. **哪些方向已经死了？** 无条件方向族（M1+ 15-240m）、vol 当方向信号、蜡烛增量预测、
   无条件日级降险 gate、DXY lead-lag、≥5m 聚合微观方向、做市策略优化论（环境驱动，arxiv 2606.05882）
   ——带 reopen condition 的 dead ends（DE-01..09），非永久禁，但无新维度不重开。
7. **哪些只是 DATA_GAP？** ≤3m tick 层终审、R1'-A-DUKA、事件日历因果、期权/期货/跨资产、
   执行模拟器校准（≠ REJECTED；解锁即重评，dead_end_index reopen_conditions）。
8. **哪些方向值得投入研究资源？** TIER 1 四项（RQ-H1/H3/H2/H5，信息/风险/成本输入层）+ TIER 2 解锁项。
9. **哪些方向应该投入工程/数据，而不是实验？** DUKA tick 下载与 W1 审计（BN-2）、D2 扩展（BN-3）、
   事件日历接入（BN-4）、执行模拟器 RQ-07（BN-5）、RLAP/RQ-08 门禁实现（BN-8）。
10. **当前最大 SYSTEM BOTTLENECK 是什么？** **观测面（OBSERVABILITY, BN-1）**——价值最高层结构性
    不可观测；次之 **成本经济性（COST, BN-9）**——任何薄盈利声称的终极过滤器（HERMES-10 确认）；
    再次 DATA（BN-2/3）与 EXECUTION（BN-5）。
11. **未来半年最值得投入什么？** ① RQ-H1/H3（信息层，现有 DUKA 数据即可预注册实验）；
    ② 事件日历接入 → RQ-H2；③ DUKA tick + D2 下载（解锁 ≤3m 终审/R1'-A-DUKA/RQ-H4）；
    ④ RQ-07 执行模拟器（工程）。全部走 kickoff→manifest→research_gate→rlap_audit。
12. **什么事情现在绝对不要做？** ① TIER 0/3/4 研究重开与投入；② 无条件 vol-timing 盈利策略
    （HERMES-10）；③ 把信息层结果升级为盈利声称；④ 任何 MT5 非只读操作/自动交易/push；
    ⑤ 修改 frozen registries；⑥ 在 DUKA tick 到位前宣布 ≤1m 结论 PASS；
    ⑦ 自动启动 Top 1——**等待人工裁决**。

## 11. 最终建议（五桶，HARD RULE #6）

**WHAT WE SHOULD RESEARCH（研究）**
- RQ-H1 成本状态可预测性（信息层；DUKA 现有数据）
- RQ-H3 状态切换先行统计（风险管理输入；REP 冻结公式复用）
- RQ-H2 事件窗反应结构（日历接入后；结构/成本层）
- RQ-H5 fix 窗 autopsy（零成本描述）
- RQ-H4 tick 流动性风险窗（W1 审计通过后；条件项）

**WHAT WE SHOULD BUILD（工程）**
- RQ-07 tick 级执行模拟器（maker/taker/fill/queue/adverse-selection；开源参考 ordersim/hftbacktest）
- 事件日历采集/清洗组件（分钟级时间戳 + 等级）
- RLAP C10b / RQ-08 模型时间资格门禁实现（research_gate 接线）
- Autopsy 引擎（G13）落地（RQ-H2/H5 复用）

**WHAT DATA WE SHOULD ACQUIRE（数据）**
- DUKA tick（KD-U01——最高优先解锁项）
- D2：DUKA 252 日同源历史（R1'-A-DUKA / 跨源终审）
- 公开宏观/央行事件日历（分钟级）
- （机会性）期权 IV / COMEX 期货 / 跨资产——授权可得才入，优先级中低（KD-U05）

**WHAT WE SHOULD NOT RESEARCH AGAIN（不再研究）**
- 无条件方向族（动量/MR/突破/趋势/形态，M1+ 15-240m）及其换名变体
- vol/activity 当方向信号；蜡烛增量预测；≥5m 聚合微观方向
- 无条件日级 vol gate（R1'-B 已否）；无条件 vol-timing 盈利（外部反证 WEAKENED）
- DXY lead-lag；做市策略优化（无 maker 通道）；IV 预测收益（无数据 + 借券费代理反证）

**WHAT WE CANNOT CURRENTLY DO（当前不能做）**
- 真订单流/簿深度/队列/做市任何研究（无 L2/maker，结构性不可观测）
- 微秒/事件抢跑（延迟 100ms+ retail 链路）
- 期权 VRP/黄金 IV/basis 套利/跨场所套利链（无数据无通道）
- 真实执行验证与任何实盘交易（只读 MT5；模拟器未建）
- 宣布任何 ≤1m 候选 PASS（DUKA tick 未到位）
- 把 "vol 信息可预测" 升级为 "可盈利择时"（HERMES-10 修正）

---

*纪律：INACCESSIBLE ≠ NO VALUE；DATA GAP ≠ REJECTED；KEEP/稳定 ≠ 正确状态表示；
CONFIRMED INFORMATION ≠ PROFITABLE TIMING；本图任何条目不构成交易许可。
v1 → v2 变更仅此一图族；frozen registries（hypothesis_registry / phase9_detector_registry /
REPRESENTATION_REGISTRY）未触碰。*
