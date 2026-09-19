# PHASE 9 RESEARCH FRAMEWORK — XAUUSD Short-Horizon Price Imbalance Alpha Hunt

> 生成：2026-09-05 01:10 (Asia/Shanghai) · 阶段：FRAMEWORK（本文件先于一切搜索性计算）
> 配套：phase9_data_audit.md（数据审计，只盘点不搜索）

## 1. Research Question
XAUUSD 在 10s–15m 尺度是否存在**可识别的暂时性价格失衡**，其后续方向性行为
(i) 相对强基线（动量/均值回复/波动-时段条件）有 **incremental 预测信息**；
(ii) 机会频率足够（目标 ≥10 次/交易日）；(iii) 扣真实成本后正期望；
(iv) 跨时期（2023-24 vs 2026）与跨 feed（DUKA vs FXTM）可重复。
若不存在 → 如实证明在当前可交易数据与约束下为何不存在。

## 2. Short-Horizon Price Imbalance 的定义
**工作定义**：mid-price 相对"近期局部均衡"的异常位移 + 其后续路径特征——
须同时记录 位移幅度(相对近期波动归一)、速度(单位时间位移)、恢复/延伸行为、以及事后 10s-15m 路径。
它不是单一公式；是七族探测器的总称（§7 各层），每族有**可复核的预登记探测器规格**
（参数在 DISCOVERY 前固定，之后禁止为结果调参）。

## 3. 候选机制（仅作为先验；每项证据等级 Observed/Supported/Suggestive/Unknown 后标）
M1 流动性吃单连续冲击（inventory/queue 反应）；M2 止损/触发级联（趋势中加速后衰竭）；
M3 信息缓慢吸收（机构拆单）；M4 做市商失衡反应（quote 调整节奏）；M5 压缩-释放
（consolidation 后方向性释放）；M6 情绪/行为过度反应后的修正（rejection 族）。
**禁止机制自证**：机制标签只能由"顺序+条件统计+反例"支持，永远标记证据等级，不做因果断言。

## 4. 与既有概念的区别（必须可分离）
- vs 普通 momentum：失衡 = **条件于结构/活动的异常**（如 3σ 位移），须证明"失衡尾"比
  "同幅过去收益"基线提供额外信息（嵌套模型 ΔIC/ΔAUC 检验）；
- vs mean reversion：须证明失衡后回复**快于/强于**无条件短周期回复基线（同窗口 z 基线）；
- vs volatility clustering：失衡族的胜率/期望须**条件于波动状态**后仍存在（vol-conditioned baseline）；
- vs session effect：逐 session 分层，禁止跨 session 混合归因；
- vs spread/bid-ask artifact：所有研究用 **mid**；异常价差时段剔除/单独分析；
- vs 机械自相关：tick 级采样/报价刷新机制产生的伪延续 → 用**事件时间抽样 + 成交价交叉验证**（last vs mid）。
以上六条是任何候选进入统计漏斗前的**前置过滤**，不是可选项。

## 5. 数据要求与审计结论（详见 phase9_data_audit.md）
| 层 | 数据 | 状态 |
|---|---|---|
| 10s-3m 主战场 | FXTM tick 23 交易日（4.996M ticks，2026-08/09）；DUKA tick（补全中，553/1343 天蜡烛） | DISCOVERY 可用；**PASS 必须等 DUKA tick 独立验证** |
| 1-15m | FXTM M1 100k（2026）· DUKA M1 229k（2023-24，M5/H1 派生） | 双期双源可用 |
约束声明：FXTM tick 点差近固定（$0.14-0.23）→ spread 动态研究仅 DUKA；10-30s 统计仅在 tick 窗；
单窗独立日数 FXTM=23、DUKA M1≈130 → 日级稳定性门槛分别 ≥15/≥60 正天数才有意义。

## 6. 时间尺度
主：10s/30s/1m/2m/3m/5m/10m/15m。分辨率纪律：tick 窗才允许 ≤1m 结论；
M1 数据不产出亚分钟声明。Edge 衰减曲线按全部尺度报告（signal → fwd path 10s..15m）。

## 7. 七族探测器（预登记单元，DISCOVERY 前冻结规格）
P1 Price dynamics（3σ 位移/加速度/jerk/回撤速度）
P2 Impulse & Failed move（快移后 30-120s 内恢复比例/保持比例）
P3 Acceptance/Rejection（进入新价位区后 1-3m 保持 vs 拒绝；自定 level 定义=过去 swing/波动包络）
P4 Momentum decay（impulse 序列的 body/range/加速度衰减 → 衰竭 vs 延续）
P5 Compression→release（波动压缩后释放的方向性条件统计）
P6 Vol/activity×structure → direction（严格限制组合 ≤12，来自 Phase 6/7 状态特征）
P7 Tick/micro（quote 压力/到达爆发/impact 衰减的先后顺序 → 条件方向）
每族 DISCOVERY 阶段探测器数有上限（P1-6 合计 ≤36 规格），超限即停。

## 8. 基线（候选必须战胜的强基线，按序比较）
B0 random；B1 zero；B2 naive direction(符号漂移)；B3 momentum(5/15/30/60bar)；
B4 MR(zscore)；B5 vol-conditioned（同波动桶内的无条件方向均值）；B6 session-conditioned；
B7 Phase-6 state-conditioned；B8 Phase-7 activity-state conditioned。
**判定**：新探测器必须在嵌套意义下优于"同族最优简单基线"（ΔIC 或 ΔAUC 的 block bootstrap CI>0，
或 WF 折内稳定），仅优于 random 者 REJECT。§3 的"重新包装 momentum"防线由此执行。

## 9. 统计协议（全部强制）
预登记；non-overlap entries（每 horizon 块）；block permutation/bootstrap；BH-FDR（按层+整轮）；
四段式：DISCOVERY(拟合/选择) → VALIDATION(单次确认) → OOS(锁定，最终一次性) → CROSS-PERIOD(另一窗/feed)；
walk-forward（时间顺序折）；subperiod（月/日）；参数扰动（±1 邻域）；**延迟信号**（+1 bar 再入场）与
**反号信号**（对称性检验：若反号同样"有效"→ 机械结构/artifact，REJECT）；placebo 事件。
K 线/tick 强自相关 → 一切推断以 effective n 为准。

## 10. 成本与执行模型
per-feed 动态：FXTM 用实测 tick half-spread（~$0.08-0.12）+ 滑点 $0.10 + 延迟 1 tick；DUKA 用实测 spread。
压力 ×1/2/3。tick 窗内做 execution simulation（taker 假设为主；maker 需队列假设，标记为理想化）。
**禁止用 mid 理论 PnL 宣布成功**：净期望 = 方向收益 − half-spread@入场 − 出场成本 − 滑点。

## 11. 机会频率与路径指标（每个候选必报）
日均/小时/session 次数；信号平均持续；signal→MFE/MAE 时间分布；最优 holding（edge 衰减曲线argmax）；
信号重叠率（>30% 重叠降权）；win/loss 结构（胜率/均赢/均亏/中位/期望/payoff/最大连亏/MFE-MAE）。
**高胜率审查**：若高胜率由小赢大亏构成（期望被尾部拖累）→ REJECT 或按 payoff 重新判定。

## 12. Candidate Alpha Registry
alpha_registry/phase9/ 每候选全字段（§21 列表 + 本节 §11 指标 + 证据等级）。
Status ∈ {PASS, REJECT, EDGE UNCERTAIN}；禁用 Promising 等。

## 13. Kill Criteria（阶段性关闭）
层内：该族预登记探测器全部耗尽且无 VALIDATION 级增量信号 → 关闭该层（记录证据）。
全局 kill（任选其一）：(a) 七层全关；(b) 进入 COST 关的候选 ≥80% 死于成本且剩余无一过机会频率；
(c) 任何候选在 CROSS-PERIOD 失败且失败无法用机制解释。Kill 后只写终审报告，不回头加参数。

## 14. PASS Criteria
§22 十六条全满足（OOS+/统计可信/多重检验/依赖感知/WF/参数扰动/子段/跨期/跨feed/成本后正期望/
频率/回撤/无artifact/无session伪影/无前视/非单阈值依赖），且 HIGH-FREQUENCY STRATEGY GATE 通过
（机会存在、方向概率、payoff、期望、成本吸收、执行可行、OOS/WF/跨期稳）。

## 15. 执行计划（阶段闸门，每闸门记录后放行）
1 FRAMEWORK（本文件）→ 2 DATA AUDIT（已完成：phase9_data_audit.md）→ 3 DISCOVERY（P1-7 预登记规格）
→ 4 STATISTICAL SCREEN（VALIDATION 段）→ 5 OOS（一次性）→ 6 COST+EXECUTION → 7 CROSS-PERIOD（DUKA）
→ 8 FINAL AUDIT + 终审报告。每阶段产出 registry/JSON；失败层即时关闭。

## 16. 设计可行性自审（诚实回答："这个设计有没有机会？"）
有机会的支柱：(a) 双 feed 双期独立样本可做真 cross-validation；(b) 10s-3m 分辨率是前 8 阶段
未系统覆盖的层——若 edge 存在，最可能在此；(c) tick 数据同时允许 execution simulation（成本侧真实）。
主要威胁（如实）：(1) 单边成本 ~0.5-1bp vs 1-5m 典型位移 1-4bp → 需要 edge 在 2-3m 内
显著大于成本；(2) FXTM 23 独立日限制日级结论；(3) feed artifact（FXTM 报价节奏、DUKA 合成性质）
可能伪造短期"延续/回复"；(4) 高频领域众所周知的 baseline 陷阱——多数"失衡"会死于 B3/B4。
设计修正（已内建）：mid-only、四段式、延迟/反号/条件基线三重防线、PASS 必须跨 feed。
结论：**设计有机会发现真高频 edge，但先验概率不高；七层中 P2/P3/P5/P7（failed move、
acceptance、compression-release、tick 顺序）理论上有机制理由，是攻击重点；P1/P4/P6 多数会
死于基线或成本——预登记预算向 P2/P3/P5/P7 倾斜。** 若全灭，终审将给出结构性解释。

## 17. 对 Phase 1-8 的主动挑战（§29，简版，详细入终审）
- Phase 4 的"微观方向 REJECTED"基于 M1 聚合 + 15-60m 持期 → 不覆盖 10s-3m 层（本 Phase 补测，非推翻）；
- Phase 6/7 的"波动/活动状态信息"是本 Phase P5/P6 的输入但**禁止直接当方向**（状态条件基线已内建）；
- Phase 8 蜡烛结论与 P4（动量衰减）部分重叠——P4 探测器必须用 tick 精度的速度/加速度，
  不是蜡烛代理；若 P4 亦死 → 与 Phase 8 互证方向层在 XAUUSD 极弱。
- 诚实提醒：此前所有"方向弱"的结论都基于 M1+ 与 ≤4 个月独立样本；Phase 9 若在 tick 层失败，
  应视为"当前可交易数据与约束下方向高频 edge 缺失"的**最强证据**（多方法互证），而非孤立否定。
