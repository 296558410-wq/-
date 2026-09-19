# HERMES KNOWLEDGE UPGRADE — 00_ROUTE（2026-09-07）

> 任务性质：知识升级任务（非策略开发、非回测扩张、非 Money Hunter 主系统修改）。
> 主控 = OpenClaw（本会话）。执行体 = Hermes 侦察会话（subagent, 每次一个精确研究授权）。
> 产出目录：`research/hermes/knowledge_upgrade/`（本任务全部产物集中于此，不扩散新模块）。

## 绝对边界（任务书 §一）
不开发策略 / 不制造回测任务 / 不改 Constitution(除非真实结构缺陷) / 不改 Dashboard /
不反复增加模块 / 不购买付费数据-API-论文-服务 / 不真实交易 / 理论论文结果≠XAUUSD alpha /
预测能力≠赚钱能力 / 新指标≠新机制 / 不人为制造"成功发现"。无法验证 → 标 UNKNOWN, 不猜。

## 升级目标（§二~§六）：五层知识
L1 Market Microstructure（价格为何在瞬间移动：参与者行为→订单流→流动性→冲击→持续/反转→可观察→机会）
L2 Execution Knowledge（signal→execution→fill→cost→realized P&L；edge 为何死于成本）
L3 Behavioral Finance → Trading Mechanism（行为→可观察→结构变化→条件概率/收益分布→净 EV）
L4 Conditional Opportunity（无条件预测 → 状态条件机会：Net EV = P(win)×AvgWin − P(loss)×AvgLoss − Cost）
L5 Information→Alpha→Money 层级（DATA→INFORMATION→PREDICTIVE→ALPHA→STRATEGY→EXECUTION→NET EV→REPEATABLE MONEY）

## 本轮侦察授权（六个并行 Hermes 任务，各一精确授权，禁止广谱搜索）
| Scout | 授权 | 交付 |
|---|---|---|
| S1-MS | L1 微观结构核心机制 + 反例 | 机制卡 ≤12 + 反例卡 ≤5 |
| S2-EX | L2 执行知识 + 成本致死机制 | 机制卡 ≤10 + 反例卡 ≤5 |
| S3-BH | L3 行为→机制可观察链 | 机制卡 ≤10 + 反例卡 ≤5 |
| S4-CO | L4 条件机会/EV/regime | 机制卡 ≤10 + 反例卡 ≤5 |
| S5-GX | 黄金结构 + HFT/做市真赚钱机制 | 机制卡 ≤10 + 反例卡 ≤5 |
| S6-AD | 全局对抗扫描（最大反证/失败模式/可迁移性） | 反例卡 ≤10 + UNKNOWN 清单 |

## 统一 Claim 卡格式（§十）
Claim / Mechanism / Why / Observable / Required data / Timescale / Payoff / Execution dependency /
Cost sensitivity / Evidence / Counter-evidence / Applicable markets / XAUUSD relevance /
Direct|Proxy|Inferred|Unknown / Status(UNVERIFIED|SUPPORTED_EXT|CONTRADICTED_EXT|DATA_GAP)

纪律：外部证据最多 E3（他市场实证），E1 不得冒充 E4；XAUUSD 迁移必须回答"为什么适用/为什么不适用"；
依赖 L2/queue/signed flow/期权/做市商头寸的机制必须标注"当前 XAUUSD feed 是否可观察"。
只保存机制，不保存论文摘要。禁止只收集支持证据。

## 输出文件规划（本目录）
- `01_L1_microstructure.md`（S1 审核后）
- `02_L2_execution.md`（S2 审核后）
- `03_L3_behavioral.md`（S3 审核后）
- `04_L4_conditional_opportunity.md`（S4 审核后）
- `05_gold_structure_hft.md`（S5 审核后）
- `06_adversarial_sweep.md`（S6 审核后）
- `07_CORE_CLAIMS.yaml`（全部核心 Claim 结构化落库）
- `08_CORRECTIONS.md`（原有认知中被纠正的部分）
- `09_UNKNOWNS.md`（仍 UNKNOWN 的关键问题）
- `10_TOP10_XAUUSD_MECHANISMS.md`（对 XAUUSD Money Hunter 最重要的 10 个机制）
- `11_DATA_WATCHLIST.md`（最值得等待的数据/观测量）
- `12_NOT_TRADEABLE.md`（当前不能交易的清单）
- `13_KNOWLEDGE_UPGRADE_REPORT.md`（最终交付 1-10 项 + "Hermes 比升级前多学会了什么"）
- `raw/`（scout 原始返回，保留供审计）
