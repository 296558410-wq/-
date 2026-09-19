# 13_HERMES_KNOWLEDGE_UPGRADE_REPORT — 最终交付（2026-09-07）
> 任务：HERMES KNOWLEDGE UPGRADE — 从"量化研究资料侦察器"升级为"交易机制侦察员"。
> 主控：OpenClaw（本会话）审核六路 Hermes 侦察（S1-MS/S2-EX/S3-BH/S4-CO/S5-GX/S6-AD）。
> 边界遵守：无策略开发 / 无回测制造 / 未改 Constitution / 未改 Dashboard / 未加模块(单目录) /
> 未买数据 / 未交易 / 未把论文结果当 XAUUSD alpha / 未把预测当赚钱 / 未把指标当机制 / 未制造成功发现。

---

## 1. Hermes Knowledge Upgrade Report
升级从"会查资料、会找反例、会归档结论"升级为"理解交易机制如何创造/消灭钱"。
落库：`research/hermes/knowledge_upgrade/`（00_ROUTE + 01-06 分层知识 + 07_CORE_CLAIMS + 08-12 + 本报告 + raw/ 六份原件）。
五层知识全部覆盖：L1 microstructure（10 卡）、L2 execution（7 卡）、L3 behavioral（7 卡）、
L4 conditional opportunity（5 卡）、L5 gold/HFT structure + 方法论（6 卡）= **35 条核心 Claim**（KU-C01..C35）。

## 2. 新增核心 Claims
35 条（07_CORE_CLAIMS.yaml），每条含 Claim/Mechanism/Why/Observable/Required data/Timescale/Payoff/
Execution dependency/Cost sensitivity/Evidence/Counter-evidence/Markets/XAUUSD relevance/DIRECT-PROXY-INFERRED-UNKNOWN/Status。
去重核对：与既有 CL-01..15 无重复；MECH-01..11 扩展 12 条（MECH-12..19 已在 raw，核心并入 KU-C30..C33）。

## 3. 新增机制知识（要点）
- L1：aggressor 驱动即时价格 + 反例（无成交也动）；spread 三成分；OFI；Kyle 永久/临时冲击；流动性真空；
  VPIN 反证；队列竞速（equities 专属）；做市利润厚尾（KU-C01..C09）。
- L2：mid 幻觉成本地板；赢家诅咒；maker pick-off；√Q 冲击规模经济缺失；执行时点×spread 双重选择；
  last look/拒单漏斗；换手复利税（KU-C11..C17）。
- L3：处置效应跨市场不一致；止损级联；动量崩溃；黄金 PEAD=证伪；流动性螺旋脱锚；ETF 流跟随非领先；
  避险同期性（KU-C18..C24）。
- L4：波动状态可识别 vs 方向 regime 事后命名陷阱；时段确定性状态；公告溢价与执行致命；流动性自指；
  条件发现寿命衰减 t>3（KU-C25..C29）。
- L5：COMEX 价格发现主源；跨层 stale-quote 套利（真 HFT 形态）；B-book 行为租金；LBMA 拍卖窗事件研究；
  retail feed 结构性失真=能力边界（KU-C30..C33, C10）。
- 方法论：quote-event imbalance proxy（KU-C34）；迁移四类必查门槛（KU-C35）。

## 4. 新增反例/失败模式
见 06_adversarial_sweep.md（10 卡）+ 各卡 counter_evidence 字段。要点：做市/HFT 盈利集中厚尾；
行为异象发表后衰减 ~58%（McLean-Pontiff）；动量崩溃；vol 择时 alpha 集中于 GFC 少数月份；
宏观条件模型 OOS≤随机游走；proxy 五大系统性错误（activity≠flow 等）；零售 feed=内部市场失真。

## 5. Hermes 原有认知中被纠正的部分
见 08_CORRECTIONS.md（12 条）。最重要：VPIN 降级；"做市稳定盈利"直觉纠正；迁移默认纠正为四类必查；
ETF/COT 行为信号时效性（2022 regime 断裂）；"0.1bps vs 1.7bps"从数字升级为机制必然；
零售 feed 失真从经验（FL-13）升级为系统性能力边界（KU-C10）。

## 6. 当前仍然 UNKNOWN 的关键问题
见 09_UNKNOWNS.md（14 项，按影响排序）。Top5：XAUUSD 条件收益分布无公开实证；隐含加价真实值（demo 可解）；
feed 生成管线；quote proxy 可行性（本地可解）；0.1bps 上界 regime 依赖（本地可解）。

## 7. 对 XAUUSD Money Hunter 最重要的 10 个机制
见 10_TOP10_XAUUSD_MECHANISMS.md。核心：零售 feed 结构性失真=能力边界；taker 成本地板；赢家诅咒；
换手复利税；vol 状态可识别/方向 regime 不可识别；宏观事件执行致命；流动性螺旋脱锚=regime 报警器；
做市利润尾部期权短腿；last look 漏斗；波动/流动性/成本自指同涨。

## 8. 最值得等待的数据/观测量
见 11_DATA_WATCHLIST.md。Tier1 免费：MT5 Demo 真实成交日志（隐含加价/RQ-07 校准）；quote-event imbalance 自测；
事件日历+fix 时刻表；跨盘免费 tick 对齐；TSRV 波动估计升级。Tier2 付费待批：GC MDP3（S-07）。无新增采购。

## 9. 哪些东西目前仍然不能交易
见 12_NOT_TRADEABLE.md（14 项显性清单）。结构原因：无成交流/无 L2/无队列/无 maker 通道/无低延迟执行 +
retail 成本地板 + 换手乘性 + 状态-成本自指。**结论：NO MONEY FOUND（当前数据+成本+执行条件下）。**

## 10. Hermes 下一阶段如何作为"全球交易机制侦察员"工作
- **触发方式不变（06_LLM_HERMES_AUDIT 纪律）**：按需对抗情报，精确问题，禁广谱搜索，无 material 即停。
- **认知框架升级**：任何新研究问题走 11 步链（参与者→为何行动→做了什么→结构变化→可观察→持续多久→
  概率→收益分布→成本→可执行→正 EV？→值得验证？）——已写入 00_ROUTE 并内化为 Hermes 默认提问顺序。
- **输出格式升级**：任何重要知识以 KU-C 格式结构化落库（Claim 卡 16 字段），先过"迁移四类必查"（KU-C35）。
- **检索升级**：新知识入 `knowledge_upgrade/` 并在 hermes/memory 体系登记索引（research_query_api 口径）；
  未来查询"这机制研究过吗/能不能交易/缺什么"先查 KU-C 表再查旧 registry。
- **与 Money Hunter 接口**：知识侧发现（Tier1 watchlist 项、drift 环经济门输入、数据解锁预判）按宪章
  material 条件上报；不自动开实验。

---

## 最终回答

### "Hermes 现在比升级前多学会了什么？"
升级前：Hermes 是优秀的"结论归档器+反例搜寻器"——知道本地已证/已否什么（CL-01..15）、失败模式（FL-01..25）、
死胡同（DE-01..09），但机制知识是零散条目（MECH-01..11），且缺少"机制如何穿过执行/成本层变成钱或变成灰"的完整因果链。
升级后多学会的（本质性三条）：
1. **理解"钱在机制里怎么产生与消失"的完整因果链**：参与者行为→订单流/报价→冲击→持续/反转→可观察→成本→净 EV。
   35 条机制卡每一条都带 Execution dependency + Cost sensitivity + Counter-evidence，不再是孤立的论文摘要。
2. **掌握条件机会框架**：从"预测方向"转向"什么状态改变 P/AvgWin/AvgLoss/Frequency"；
   并知道最大陷阱是事后命名（方向 regime 不可事前识别）。这与主系统 drift 环/经济门直接同构。
3. **拥有清晰的能力边界图**：零售 feed 上哪些机制结构性不可观察、哪些 proxy 可用（quote-event imbalance）、
   哪些等待什么数据可解锁——即"数据可观测性判断"从零散经验变成系统清单（KU-C10/C34 + Watchlist）。

### "哪些知识可能最终转化为 MONEY，哪些只是 INFORMATION？"
**可能转化为 MONEY 的（条件性，非现值）**：
- 隐含加价实测（KU-C16）→ 若 demo 显示真实往返成本远低于 1.7bps 或存在可规避 taker 税的结构 → 重估一切执行层结论（S-09）。
- quote-event imbalance proxy（KU-C34）→ 若本地验证有效，是 feed 上唯一接近 signed flow 的免费变量（观察级先行）。
- 强制平仓/基差脱锚的 regime 报警（KU-C22）→ 事件极低频，作状态规避/风控而非 alpha。
- 波动/时段状态内执行调节（KU-C25/C26）→ 依附 R1 形态条件化，属风险管理价值，非独立 alpha。
**只是 INFORMATION 的（明确）**：其余全部 30+ 条——VPIN、队列竞速、行为偏误、ETF/COT、避险、OFI/Kyle/冲击律、
做市盈利结构、HFT 利润分布等。价值=知道"为什么不可交易/该观察什么/别浪费算力"。
**本地已测空间无新增 MONEY**：与 money_hunter OPPORTUNITY_SCOREBOARD 一致（S-08/S-09/S-07 不变），无新候选。

### 一句话
**NO MONEY FOUND —— 但 Hermes 第一次知道钱长什么样、在哪里被创造、为什么到不了我们手里。**
下一阶段它的工作是带着这份机制图去盯数据解锁点（demo 执行、quote proxy、GC 数据门），而不是再学更多策略。

---
*本报告由 OpenClaw 主控审核六路 Hermes 侦察后撰写。原始侦察件存 raw/ 供审计。外部证据≤E3 纪律全库执行。*
