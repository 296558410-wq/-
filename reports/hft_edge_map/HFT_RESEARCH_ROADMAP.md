# HFT RESEARCH ROADMAP — 未来 3–6 个月执行路线（裁决后 v1, 2026-09-06）

> 依据: 人工裁决 2026-09-06 11:37（HFT EDGE MAP v2 = PASS · KD-HFT-MAP v2 = APPROVED）。
> 并入: HERMES-10（CONTRA-09）+ HERMES-11（REC-01/02/03, b9f251d）全部有效修正。
> 本文件是**计划**，不是实验授权。任何一项进入实验前必须逐个过 ENTRY GATES + 人工裁决。
> 不并行启动 Top 5——研究池上限，不是并行配额。

---

## 0. 裁决固化（8 条修正全部写入本路线）

| # | 修正 | 落地位置 |
|---|---|---|
| 1 | activity → future volatility = CONFIRMED INFORMATION | 只作风险/成本输入（RQ-H1/H3 前提），禁止当方向 |
| 2 | volatility information → profitable timing = UNPROVEN / WEAKENED | 无任何 "vol-timing 盈利" 实验立项；TIER 4 |
| 3 | risk/cost information = POSSIBLE INFORMATION LAYER | RQ-H1/H3 声称边界 = 信息/风险/成本输入 |
| 4 | POSITIONING ≠ FLOW | CFTC COT（周频持仓）= PARTIALLY_ACCESSIBLE 低频输入；高频流仍 INACCESSIBLE |
| 5 | execution layer 必须拆分 | execution overlay（micro-price 门控）+ vol-条件反转（他市场证据, 不转移）分开立项 |
| 6 | L2 不是所有 execution research 的绝对前置 | RQ-07 只需 bid/ask tick；L2 仅做市族（TIER 3）需要 |
| 7 | INACCESSIBLE ≠ NO VALUE | 词汇纪律, 全路线沿用 |
| 8 | DATA GAP ≠ REJECTED | 数据缺口进 TIER 1B/2, 不判死 |

新 TIER 定义（裁决版, 取代 v2 组合的 TIER 0-4 用途）:
- **TIER 1A** = 当前可观察、可验证、成本可建模 → 现在就能预注册研究
- **TIER 1B** = 需要数据/工程解锁后才能研究
- **TIER 2** = 潜在价值存在, 但证据或能力不足
- **TIER 3** = 基础设施/数据壁垒过高
- **TIER 4** = 明确停止研究

## 1. 研究池映射（Top 5 是池, 非并行任务）

| 池成员 | 机制 | TIER | 解锁依赖 | 状态 |
|---|---|---|---|---|
| RQ-H1 成本状态可预测性 | M17 | **1A** | 无（DUKA M1/H1 在手） | 待预注册 |
| RQ-H3 状态切换先行统计（风险输入） | M18 | **1A** | 无（FXTM/DUKA M1/H1 在手） | 待预注册 |
| RQ-H5 fix 定盘窗 autopsy（描述） | M24 | **1A** | 无（FXTM tick W1 在手） | 待描述性注册 |
| RQ-H2 事件窗反应结构 | M02/M15 | **1B** | 事件日历（数据优先级 #2） | 待日历 |
| RQ-H4 tick 冲击后流动性风险窗 | M07 | **1B** | W1 数据审计 → DUKA tick（#1） | 待审计 |
| ≤3m 层方向族终审 + N1 事前识别 | M03/M09 补测 | 1B | DUKA tick（KD-U01/U09） | 待数据 |
| R1'-A-DUKA 跨源补测（预注册完成） | M21 邻域 | 1B | D2 252 日（数据优先级 #3） | 待数据 |
| Execution overlay 验证（REC-02 分支 1） | M21 | 1B | RQ-07 Engine v1 | 待 Build |
| vol-条件反转溢价（REC-02 分支 2） | M09 条件化 | 2 | 他市场证据不转移; 需 XAUUSD tick + 预注册（P2/P4 族已有冻结物） | 待数据 |
| COT 持仓极端作状态变量（REC-01） | 非方向输入 | 2 | 公开数据, 无解锁; 证据弱（"不是交易信号"） | 可选, 低优先 |
| 影响曲线/AS 描述（KD-O08） | M16 | 2 | tick + Engine | 待两者 |
| 期权 IV / 黄金 VRP / basis 信息用法 | M11/M13/M14 | 2→3 | 机构级数据+通道 | 不排队 |
| 做市簇/队列/订单流/跨场所/延迟 | M03-M06/M22/M01/M12 | **3** | INFRA_UNLOCK（L2/maker/共址/资本） | 不投入 |
| 无条件方向族/vol 当方向/蜡烛增量/无条件 vol gate/无条件 vol-timing/DXY lead-lag/≥5m 微观方向/零售信号族/LLM 直接交易输出 | 多 | **4** | — | 禁止 |

启动纪律: 同一时刻最多 **1 个 1A 实验在 Discovery→OOS 流水线内运行**（RLAP 程序级多重性 +
search-intensity 纪律）; 其余 1A 成员只做预注册冻结, 不计算。建议首个实验 = RQ-H1（数据最全、
成本纪律最清晰）; RQ-H3 预注册与其并行准备, 顺序执行。

## 2. WHAT TO RESEARCH（研究什么, 按序）

**阶段 S1（裁决后立即, 只做协议不做计算）**
1. RQ-H1 预注册冻结: 目标 = 未来 h∈{15m,1h,4h} DUKA spread 分位/成本 regime; 特征 = REP KEEP 冻结公式;
   基线 = 无条件分布; 3 块 OOS; kill 内置（见 §8）。声称边界 = 成本信息层。
2. RQ-H3 预注册冻结: REP 状态路径 → 未来 vol 放大事件的先行统计; 风险层指标（提前量/命中率/成本规避差）;
   无收益声称。声称边界 = 风险管理输入。
3. RQ-H5 描述性协议注册（KD-TAX1 同型: REGISTERED_DESCRIPTIVE）: fix 窗 ±30m vol/activity/spread vs 24h 基线。

**阶段 S2（RQ-H1 完成一个完整证据链后裁决）**: 依结果决定 RQ-H3 启动或调整;
RQ-H2 仅在日历入库后进入预注册（事件窗结构, 双期对照 FXTM 2026 vs DUKA 2023-24）。

**阶段 S3（DUKA tick 到位后裁决）**: RQ-H4（W1 审计先行）、≤3m 终审补测、vol-条件反转的 XAUUSD 版
（只能以 P2/P4 冻结规格的扩展形式, 禁新阈值搜索）。

不研究（TIER 4 全清单见 §5）; 不研究任何无条件 vol-timing 盈利形式。

## 3. WHAT TO BUILD（工程什么, 已批准）

**RQ-07 Execution Reality Engine（批准立项, 最高工程优先）**
- 定位: 真实高频执行现实层, 非理想化 backtester。任何未来 HFT candidate 必须先过本引擎评估,
  才可进入更高层研究（新 ENTRY GATE, §7）。
- 至少实现（裁决清单逐项）:
  Bid/Ask 状态 · spread（可变点差 feed 驱动）· slippage · latency（retail ~100ms+ 假设, 参数化）·
  fill probability（taker marketable 简化 + 限价排队近似）· adverse selection（成交后 markout 模拟）·
  market impact（事件冲击响应）· partial fill · missed/rejected fill（含 last-look 拒绝模型, RQ-02）·
  exposure（未成交暴露跟踪）。
- 输入数据: DUKA 可变 spread（主）+ FXTM tick W1（结构验证）; **不需要 L2**（REC-03 确认, micro-price 级即可）。
- 参考: ordersim / hftbacktest / MicroExchange（开源审计后选型）。
- 产出: `execution_reality` 评估包 + candidate 评分报告模板（成本后/2x/3x + 拒绝率灵敏度）。
- 里程碑: v0（taker marketable + spread/slippage/latency + fill/missed）→ v1（+限价排队 + partial +
  last-look 拒绝 + adverse-selection markout）→ v2（impact + exposure 接入研究管线）。
- 本引擎是工程, 非 alpha 研究; 不产生收益声称。

**其他 Build（排 RQ-07 之后）**
- 事件日历采集/清洗组件（分钟级时间戳 + 等级 + 源冗余; RQ-H2 前置）——数据优先级 #2 的配套工程。
- Autopsy Engine（G13）落地（RQ-H2/H5 复用; Phase 7 事件链框架扩展）。
- COT 拉取/入库小工具（cftc.gov disaggregated CSV; 可选, 半天级工作量）。
- 门禁链已存在（research_gate / rlap_audit C01-C10b / RQ-08）——**只接线不重建**; 新增 execution-reality gate 接入。

## 4. WHAT DATA TO ACQUIRE（获取什么数据, 裁决版优先级）

1. **DUKA tick（KD-U01）— 最高优先**: 解锁 ≤3m 终审、RQ-H4 主测场、spread 动态描述、N1 事前识别、
   执行层 tick 校准、vol-条件反转 XAUUSD 版。已有断点续传工具链; 阻塞 = 网络/时间, 非方法。
2. **宏观/央行事件日历**: 分钟级时间戳 + 等级; 公开源; RQ-H2 唯一前置。
3. **只获取存在明确 REOPEN 条件的数据缺口**（dead_end_index 规则）:
   - D2（DUKA 252 日同源历史）→ 重开 R1'-A-DUKA（预注册已完成, KD-R1A）;
   - 其余缺口（期权/期货/跨资产/COMEX）无 REOPEN 触发前不获取。
4. 可选（公开免费, 非缺口）: CFTC COT 黄金持仓（REC-01）——作低频状态变量候选, 不阻塞任何路线。
不获取: L2/深度/成交流/maker 数据（无通道, 买不到）; 任何需要机构身份的源。

## 5. WHAT NOT TO RESEARCH（不研究什么）

- 无条件方向族（动量/MR/突破/趋势/形态, M1+ 15-240m）及换名变体（F-R1..R17; DE-01..07）
- vol/activity 直接当方向信号（DE-06）; 蜡烛形态增量预测（F-R16）; ≥5m 聚合微观方向（KD-C07）
- 无条件日级 vol gate（R1'-B）; 无条件 vol-timing 盈利（HERMES-10: JFE 成本归零 + Elsevier 消失）
- DXY→黄金 lead-lag（CL-10）; 零售信号族通用复刻（2607.20093 REFUTED + 2605.04004 MNQ 14 族无一存活——
  他市场佐证, 与本地方向层关闭一致）
- LLM 直接交易 agent 方向输出（CL-14/FL-23, 参数化泄漏未解前）
- 做市/队列/订单流/跨场所套利/延迟抢跑（TIER 3, 见 §6）
- 任何 "等 L2 就能做 execution" 的隐性等待（REC-03 已否: overlay 不需要 L2）——该动工就动工

## 6. WHAT REQUIRES UNLOCK（什么需要解锁, 以及解锁后进哪）

| 项 | 解锁条件 | 解锁后去向 | 解锁责任人 |
|---|---|---|---|
| RQ-H2 | 事件日历入库（数据 #2 + 采集组件） | TIER 1A | 数据/工程 |
| RQ-H4 | W1 tick 数据审计 PASS → DUKA tick（#1） | TIER 1A | 数据（审计先行） |
| ≤3m 终审 / N1 | DUKA tick（#1） | TIER 1A（补测协议已冻结） | 数据 |
| R1'-A-DUKA | D2 252 日（#3, 有 REOPEN 条件） | TIER 1A（预注册已冻结） | 数据 |
| Execution overlay 验证 | RQ-07 v1 | TIER 1A | 工程 |
| vol-条件反转（XAUUSD 版） | DUKA tick + 扩展预注册（P2/P4 冻结物为基） | TIER 1B | 数据 + 研究 |
| 期权 IV / VRP / basis 信息用法 | 机构级期权/期货数据+通道 | TIER 2（届时重评） | 外部授权（不排队） |
| 做市簇 / 队列 / 订单流 / 跨场所 / 延迟 | INFRA_UNLOCK（maker+L2+共址+资本, 短期不可能） | TIER 3（保持不投入） | — |
| COT 持仓状态变量 | 无（公开）; 仅需人工点头纳入状态向量 | TIER 2 可选 | 研究（低优先） |

## 7. ENTRY GATES（入口门禁, 每个实验必经）

1. **注册与冗余检查**: 新假设登记 → hypothesis_registry 冗余比对（REDUNDANT_WITH_EXISTING_RESEARCH 自动拒）;
   换名不构成差异化（reentry_rules）。
2. **预注册冻结**: 阈值/窗口/成本/基线/统计协议在计算前锁定; 禁 post-hoc 放宽。
3. **research_gate**: kickoff → manifest（含 model_temporal 块, RQ-08）→ research_gate → rlap_audit
   （C01-C10b: window-role / first-use HARD-BLOCK / SI / PML / registry-sha / model 资格）; 无 skip/force。
4. **人工裁决点**（每阶段）: DISCOVERY → VALIDATION → OOS → CROSS-PERIOD → CROSS-FEED 各段结束须人工放行;
   无人自动推进。**不自动启动 Top 1。**
5. **Execution Reality Gate（新增, 裁决要求）**: 任何未来 HFT candidate 必须先通过 RQ-07 引擎评估
   （成本后 + 2x/3x + 拒绝率/滑点/AS 灵敏度）, 才可进入更高层研究; 未过引擎 = 停在信息层声称。
6. **数据资格门**: ≤1m 候选的 PASS 需要 DUKA tick 跨 feed 验证（KD-U09）; FXTM 单窗结论不外推。
7. **词汇门**: 报告只能用 registry 判定词汇; CONFIRMED INFORMATION ≠ PROFITABLE TIMING;
   activity ≠ order flow; positioning ≠ flow; INACCESSIBLE ≠ NO VALUE; DATA GAP ≠ REJECTED。

## 8. KILL CONDITIONS（终止条件）

**逐 RQ（预注册即冻结）**
- RQ-H1: 3 块 OOS 中位 IC 无可辨正预测 且 最佳窗成本优势 < 0.2×点差, 或任一前向窗反转 → REJECT, 信息层关闭。
- RQ-H3: 先行特征区分度无显著提升（AUC vs 0.5）或提前量中位 < 2×执行延迟 → REJECT/UNCERTAIN; 结果禁作盈利声称。
- RQ-H5: fix 窗与对照无差异或 feed 密度不足 → CLOSED 描述条目（零成本结论）。
- RQ-H2: ≥80% 事件类别无显著放大或峰值反应中位 > 5m → 降纯描述, 出 TIER 1。
- RQ-H4: 冲击响应无差异或 W1 审计显示 feed 不承载 → 降 DATA_GAP 条目。

**程序级（任一触发 = 全路线暂停, 回报人工）**
- K1: ROUTE-CHANGING 反证入库（如 HERMES-10 型）→ 停当前实验, 先修订地图再继续。
- K2: RLAP/rlap_audit 违规（泄漏/首次使用/窗口角色/搜索强度/模型时间）→ 立即冻结, 审计后恢复。
- K3: Execution Reality 显示候选成本后净值为负且 2x/3x 全灭 → 该候选降级/关闭（不得以 mid-PnL 或理想化假设复活）。
- K4: 任何尝试把信息层结果升级为盈利声称 → 该输出作废（词汇门）。
- K5: DUKA tick 到位前宣布任何 ≤1m 候选 PASS → 无效（数据资格门）。

## 9. 未来 3–6 个月资源优先级（月历）

**M1（2026-09 下半）— 协议与数据并行**
- 研究: RQ-H1 + RQ-H3 预注册冻结 + RQ-H5 描述性注册（协议层, 零计算）;
  RQ-H1 过 research_gate + rlap_audit → 人工裁决放行后开始 Discovery。
- 工程: RQ-07 Engine v0 设计与骨架（bid/ask/spread/slippage/latency/fill/missed）; W1 tick 数据审计。
- 数据: DUKA tick 下载启动（持续, 最高优先）; 事件日历源评估。
- 出口: 裁决点 —— RQ-H1 是否进入 Discovery; RQ-07 v0 是否合标。

**M2-M3（2026-10~11）— 首个实验链 + 引擎 v1**
- 研究: RQ-H1 完整链（DISCOVERY→VALIDATION→OOS; 每段人工放行）; RQ-H3 依序启动（不并行计算）;
  RQ-H5 描述性 autopsy（零成本, 后台）。
- 工程: RQ-07 v1（+限价排队 + partial fill + last-look 拒绝 + AS markout）; 日历采集组件上线 → RQ-H2 预注册。
- 数据: DUKA tick 完成/部分完成 → 触发数据审计; 日历入库。
- 出口: RQ-H1 裁决（KEEP→进跨期/跨源; 负→按 kill 关闭并记录）; RQ-07 v1 合标 → execution reality gate 生效。

**M4-M6（2026-12~2027-02）— 解锁项与第二波**
- 研究: RQ-H2（日历齐）; RQ-H4 + ≤3m 补测（DUKA tick 齐, 数据审计过）; vol-条件反转 XAUUSD 版
  （P2/P4 扩展预注册, 若裁决同意）; 所有 candidate 过 Execution Reality Gate 后才许声称。
- 工程: RQ-07 v2（impact/exposure 接入）; Autopsy Engine; COT 状态变量（若裁决纳入）。
- 数据: D2（REOPEN 条件触发时）; 其余缺口不获取。
- 出口: 每季度末向人工提交 3 问——钱在哪/瓶颈变没变/下一季度最该做什么。

**资源纪律**: 同时只跑 1 个实验计算链; 算力/工程按此序分配:
RQ-07 Engine > RQ-H1 > DUKA tick 下载与审计 > RQ-H3 > 日历组件 > RQ-H5/RQ-H2 > COT。
TIER 3 不占任何资源; TIER 2 只在解锁条件满足时重评。

## 10. 下一步（本路线自身的 Gate）

本 ROADMAP 提交后 **STOP**, 等待人工裁决:
1. ROADMAP 是否批准; 2. 首个实验选择（建议 RQ-H1）与预注册授权;
3. RQ-07 v0 范围确认（裁决清单已含, 确认即可开工）; 4. DUKA tick 下载授权（数据 #1）。

---
*纪律重申: 本路线不授权任何计算/交易/参数搜索; 每个实验仍走 §7 全链门禁。
参考文献: reports/hft_edge_map/* (v2) · EVIDENCE_CONVERGENCE.yaml · HERMES-10_HFT_HANDOFF ·
HERMES-11_REPORT/RECLASSIFICATIONS（REC-01/02/03）· research/registry/knowledge_map.yaml KD-HFT-MAP v2。*
