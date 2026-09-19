# HIGH-FREQUENCY SYSTEM BLUEPRINT — 分层蓝图（非策略，非实现规格）

> 任务十三：INFORMATION → OBSERVATION → STATE → OPPORTUNITY → DECISION → EXECUTION → RISK → FEEDBACK。
> 每层回答：现在有什么 / 缺什么 / 是否成为瓶颈。
> 版本: v1 = 2026-09-05 · v2 = 2026-09-06（并入 HERMES-10: 延迟是根本成本确认; 风险层定位 = 信息输入非盈利 edge; 成本 = 显式瓶颈）

## 层 1 — INFORMATION（信息源）
- 现在有：FXTM bid/ask/last（tick 23 日 + M1/M5/H1 2026）；DUKA M1/M5/H1（2023-09..2024-03，可变 spread）；固定日程时间（Phase 7 已用）。
- 缺：事件日历语义标注；期货/期权/跨资产；成交流；DUKA tick；对齐的跨场所并发样本。
- v2 注：HERMES-10 确认延迟为 HFT 根本成本 → 信息层内任何需要速度优势的源（M01）整体不可达；信息层的价值在"存在性"（事件时间/日历锚）而非"速度"。
- 瓶颈度：中（信息面窄但非空）。

## 层 2 — OBSERVATION（观测/特征）
- 现在有：P1-P7 探测器工程（27/27 已注册）；REP Phase2 冻结成员（B0-B4/C1-C12 中 13 KEEP 冻结公式）；quote-pressure/burst、vol/activity/spread 状态特征族。
- 缺：真实簿/队列观测（不可得）；FXTM 固定点差 → spread 动态不可观测（KD-U01）；事件时间层特征（tick 缺）。
- 瓶颈度：**高（第一瓶颈）**——价值最高处（M03/M04/M22）的观测面永久缺失；我们只能做"activity proxy"，不能做"order flow"。

## 层 3 — STATE（状态）
- 现在有：REP Phase1 框架 + Phase2 描述性稳定性（13 KEEP；注意 KEEP ≠ 正确状态表示）；High-Vol taxonomy（regime 依赖）；Autopsy 风险形态。
- 缺：状态切换动力学（预测层从未测）；跨尺度-跨 feed 语义稳定性（Phase 1 结论：无稳定跨窗表示，KD-U10 前身）；可移植性判据（Phase 3 计划项）。
- 瓶颈度：中（描述层就绪，预测层是 TIER 1 主战场 RQ-H3）。

## 层 4 — OPPORTUNITY（机会识别）
- 现在有：NBQ-T1 机制定义/标签规格（OOS REVERSAL n=0 NOT EVALUABLE，搁置）；条件 MR 预注册（P2/P4）；事件窗想法（RQ-H2）。
- 缺：一个通过门禁链验证的机会识别器（目前为零——这是诚实状态）；日历标注。
- 瓶颈度：高（但这是研究目标本身，不是基础设施瓶颈）。

## 层 5 — DECISION（决策）
- 现在有：R1' state machine 规范（A Trade/Wait · B Reduce/Stop · C Scaling）+ gate 化实现；research_gate/RLAP 决策链（防泄漏是决策层一部分）。
- 缺：任何获得 KEEP/EDGE 判定可进入决策层的信号（方向族全 REJECTED；中间层未测）。
- 瓶颈度：取决于层 4；决策架构本身已冻结可用。

## 层 6 — EXECUTION（执行）
- 现在有：MT5 只读（fail-closed，无 order_send）；R1'-A FXTM 对照研究（声称边界已声明：不宣称 execution alpha）。
- 缺：执行模拟器（RQ-07 未建）；真实/paper 通道；fill/滑点/queue 假设的 tick 校准基础（DUKA tick 缺）。
- 瓶颈度：**高（第三瓶颈）**——中间层研究目前只能输出"成本/风险输入"，无法闭环验证"执行后价值"。

## 层 7 — RISK（风险）
- 现在有：成本模型锚（R1'：机会成本 116.5bp / 保护 60.6bp 级）；无条件 vol gate 教训（REJECTED）；vol/activity 非方向关系（CL-01/02）。
- 缺：条件化风险 gate 的验证（RQ-H3 正是此层）；taxonomy 的"风险-机会分离"后半程。
- v2 注：HERMES-10 修正——本层输出是风险管理输入（何时成本高/风险高的提前量），不是"可盈利择时"；无条件 vol-timing 盈利主张已由外部反证削弱（CONTRA-09）；本层研究与盈利声称之间隔着一个成本瓶颈（BN-9）。
- 瓶颈度：低-中（概念与纪律就绪，等层 3 预测层；成本纪律已内置）。

## 层 8 — FEEDBACK（反馈回路）
- 现在有：每阶段报告+证据+审计+本地提交+人工裁决（强制 STOP）；window-role/first-use/PML/SI/模型时间门禁（C01-C10b）。
- 缺：实时/在线反馈（研究阶段不需要）；Hermes 定期情报回写（只读使用中）。
- 瓶颈度：低（这是本项目最强的一层）。

## 结论（任务十三要求：真正的系统瓶颈）
1. **观测面（层 2）**——结构性、不可逆（无 L2/成交流/maker）。对策：接受 proxy 上限；把研究面收敛到 proxy 足够的问题（成本/vol/事件时间），并在一切报告中用 proxy 语言。
2. **数据解锁（层 2/6）**——DUKA tick、D2 252 日历史、事件日历、对齐并发样本。对策：列为 TIER 2 解锁优先级，先做 W1 tick 数据审计（RQ-H4 kill 前置）。
3. **执行验证（层 6）**——模拟器缺失使所有中间层研究停在"输入"而非"闭环"。对策：RQ-07 执行模拟器立项（工程，非 alpha），放在 TIER 1 实验之后。
4. **成本经济性（层 6/7, v2 新增显式）**——单边 0.5-2.4bp 与薄信号毛收益的差距 + 外部 vol-timing 成本归零证据（HERMES-10）→ 盈利声称的终极过滤器。对策：信息层与研究层分开声称；1x/2x/3x 成本压力内置；只研究信息/风险输入或足够厚的 edge。
5. **非瓶颈警示**：决策纪律/防泄漏链（层 5/8）已成熟，无需再加官僚层；层 4 的零候选是研究现状的诚实反映，不是流程失败。
