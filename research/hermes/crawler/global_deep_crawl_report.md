# GLOBAL DEEP CRAWL REPORT（全球深挖报告）

> 生成：2026-09-05 · HERMES-05 · 目标问题：
> **"全球公开研究生态中，市场参与者究竟通过什么机制持续获得经济价值？"**
> 框架：WHO KNOWS WHAT / WHEN / THROUGH WHICH CHANNEL / AT WHAT COST / WITH WHAT INFRASTRUCTURE。
> 综合 HERMES-01..05 全部已挖实体，非单次搜索。

---

## 0. 一句话结论

持续经济价值**不在"方向预测"**，而集中在两类：**(A) 信息基础设施优势**（先于别人知道、以更低成本执行——
我们 INACCESSIBLE），和 **(B) 风险/成本的时间择时**（波动率与交易成本的 regime 依赖——我们部分 ACCESSIBLE）。
这解释了为什么我们自己的 XAUUSD 研究里方向 alpha 是空的、而 vol/activity 信息（非方向）是硬的。

---

## 1. WHO KNOWS WHAT FIRST —— 信息速度层（INACCESSIBLE）

| 机制 | 谁获利 | 通过什么渠道 | 基础设施 | 我们可否 |
|---|---|---|---|---|
| 订单流信息（Evans-Lyons） | dealer/银行 | 专有客户订单流（6.5 年 Citibank 数据） | dealer 客户关系 | ❌ 数据不可得 |
| 极低延迟/last look | 非银行做市商 | 50-200ms 可拒单的非对称期权 | 主机托管+低延迟 | ❌ 无 maker 通道 |
| 队列位置/L2 深度 | HFT | 盘口深度+队列 | 交易所 co-location | ❌ 无 L2 数据 |

**结论**：市场里"先知道"的利润，被有基础设施的机构拿走。我们（零售 feed、无深度、无 maker）
在这一层 **INACCESSIBLE**。任何"订单流/微观结构方向预测"的外部漂亮结果，都依赖我们拿不到的数据。

## 2. WHO PROVIDES LIQUIDITY —— 做市层（INACCESSIBLE，且被高估）

| 机制 | 真实经济学 | 关键证据 |
|---|---|---|
| spread capture | spread/2 > 逆向选择 + 库存成本 | A-S 框架 |
| 做市盈利来源 | **环境驱动，非策略**（informedness regime） | arxiv:2606.05882（R²<0.05） |

**结论**：做市盈利是"环境特征"不是"策略优化"——即使有 maker 通道，优化报价的边际贡献也 < 市场环境。
这条**双重**不可及：既无通道，且机制本身也被高估。

## 3. WHO TIMES COST & RISK —— 风险/成本择时层（部分 ACCESSIBLE）★ 我们的价值所在

| 机制 | 证据 | 我们可否 |
|---|---|---|
| 交易成本 regime 依赖（成本择时 > 收益择时） | NBER w24222（Collin-Dufresne） | ✅ 可研究（E5 vol 信息 + spread 成本代理已有） |
| 波动率择时的成本幻觉 | arxiv:2212.07288 + CONTRA-01 | ✅ 已印证 R1'（机会成本>保护） |
| activity→vol / spread→vol（非方向信息） | 本地 E5（IC 0.60-0.89 / -0.24） | ✅ 已证（硬） |

**结论**：这是唯一一个我们能真正参与的层——**波动率与交易成本的时间结构**。全球证据（Collin-Dufresne、
Moreira-Muir 争议链）与我们的本地结论（R1' 无条件降险被否 → 应走向"形态条件化"）互相印证。
这是 R1 adaptive 方向的外部机制级支撑，也是 RQ-01 的核心。

## 4. WHERE DIRECTIONAL ALPHA LIVES —— 方向层（基本不存在于高效市场）

- 外部：LLM agent 的"alpha"在泄漏控制下大部分是被动暴露（FL-24）；子基点 edge 死于费用（FL-25）。
- 本地：两期双源 0 SUPPORTED；Phase 9 27/27 探测器零候选。
- **收敛**：方向 alpha 在流动性好的市场里是稀缺的、被成本/泄漏/搜索强度系统性侵蚀的。

## 5. 方法论层：研究本身的"假 alpha"风险（本轮最大新增）

| 风险 | 证据 |
|---|---|
| 搜索强度泄漏 | arxiv:2608.27734 |
| 参数化 look-ahead（权重级） | FINCAD（arxiv:2605.24564）—— 现有守卫抓不到 |
| 被动暴露幻觉 | arxiv:2605.28359 |
| 诱导零审计 | arxiv:2604.15531（可执行的 Audit） |

**结论**：我们作为 LLM 驱动研究，最大的风险不是"找不到 alpha"，而是"制造假 alpha"（FL-20/23/24）。
这指向 RQ-05（泄漏审计升级）——这是本轮最重要的、可执行的方法论增量。

---

## 6. 藏宝图（综合后的价值地图）

```
市场持续经济价值
├── 信息速度层（订单流/延迟/队列）—— INACCESSIBLE，机构独占
├── 做市层（spread capture）—— INACCESSIBLE，且被环境驱动高估
├── 风险/成本择时层（vol/cost regime）—— ★ ACCESSIBLE，我们的 R1 方向
├── 方向层（directional alpha）—— 基本不存在（本地+外部收敛）
└── 方法论层（研究假 alpha 风险）—— ★ 可执行，RQ-05 泄漏审计
```

**最终答案**：我们能持续获得价值的地方，不是"预测价格方向"，而是"更准确地理解并择时波动率与
交易成本的时间结构"——同时用严格的方法论保证自己不制造假 alpha。
