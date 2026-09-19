# HERMES GLOBAL SCAN REPORT（全球扫描报告）

> 生成：2026-09-05 · HERMES-03 · 本轮真实全球扫描的 10 个高质量发现（完整分析链）。
> 全部来自真实检索/抓取（web_search + web_extract），非记忆、非虚构；去重后保留。
> 证据等级：外部资料最多 E2/E3，一律未在 XAUUSD 验证。机器可读版见 global_intelligence/*.yaml。

---

## 发现总览（去重后 10 条，覆盖 8 类来源）

| # | 发现 | 机制 | XAUUSD 相关 | 价值 |
|---|---|---|---|---|
| F1 | LBMA 定盘 = IBA 电子轮次拍卖 | MECH-01 | MEDIUM | 理解+潜在微观结构 |
| F2 | COMEX 期货领先现货（EFP 套利） | MECH-02 | MEDIUM | 跨资产 lead-lag |
| F3 | vol-target 换手/成本幻觉 | MECH-03 | HIGH | 印证 R1' |
| F4 | 交易成本 regime 依赖（成本择时>收益择时） | MECH-04 | HIGH | R1 机制支撑 |
| F5 | last look + 流毒性 > 半价差 | MECH-05 | HIGH | 执行层 |
| F6 | OTC 内部化/碎片化 | MECH-06 | MEDIUM | 理解 |
| F7 | OFI 放大价格波动 | MECH-07 | LOW | 方向已否 |
| F8 | OTC 信息追逐 vs 逆向选择 | MECH-08 | LOW | 理解 |
| F9 | 回测过拟合/deflated Sharpe | MECH-10 | HIGH | 方法论红线 |
| F10 | LLM 搜索强度泄漏 | MECH-11 | HIGH | 直接针对我们 |

---

## F1 — LBMA 定盘 = 电子轮次拍卖

- **SOURCE**：WatchGold 微观结构拆解（IBA 官方机制）· E1-E2
- **CLAIM**：LBMA 金价由 IBA 以 30 秒/轮的电子拍卖产生，失衡 >10,000 盎司则朝失衡方向调价进入下一轮。
- **MECHANISM**：定盘是"真实订单撮合价"而非报价协商；10:30/15:00 伦敦两场是黄金 spot 最重权重的定价时刻。
- **EVIDENCE**：机制描述（可交叉验证于 IBA/LBMA 官方文档）。
- **LIMITATION**：XAUUSD 是经纪商 spot 报价（FXTM），非 LBMA 直接成员；传导需经 feed。
- **CONTRADICTION**：无（描述性，非可交易主张）。
- **XAUUSD RELEVANCE**：MEDIUM（理解价值 + 定盘窗 autopsy 候选）
- **DATA**：FXTM tick 覆盖 24h，事件时间已知（固定）
- **TESTABILITY**：可做描述性 autopsy（RID-009 延伸）
- **VALUE**：D（理解价值）+ 潜在 B

## F2 — COMEX 期货领先现货

- **SOURCE**：WatchGold + 多来源一致 · E3
- **CLAIM**：黄金价 = COMEX 期货/伦敦现货/GLD 三市场被套利钉成；COMEX 领先（尤其美国时段）。
- **MECHANISM**：EFP(cash-and-carry) 套利是纽带；2020-03 套利崩裂（EFP basis 爆裂）是压力测试实证。
- **LIMITATION**：XAUUSD 是 spot 报价，非 COMEX；价格发现源头在 COMEX。
- **CONTRADICTION**：双向传导（非单向因果）。
- **XAUUSD RELEVANCE**：MEDIUM（→ KD-U05 跨资产数据缺口）
- **DATA**：需 COMEX/GLD 数据（未接入）
- **VALUE**：D + 潜在跨资产 B

## F3 — vol-target 换手/成本幻觉 ★

- **SOURCE**：arXiv:2212.07288 "Smoothing volatility targeting" · E3
- **CLAIM**：标准 1/RV vol-target 产生极端换手与杠杆；成本后收益消失；平滑波动预测可正则化并恢复价值。
- **MECHANISM**：已实现方差的噪声导致预测抖动 → 极端换手 → 成本侵蚀（MECH-03）。
- **EVIDENCE**：158 美股策略，成本 14/50bp 两档。
- **CONTRADICTION**：见 CONTRA-01（Moreira-Muir 争议链）。
- **XAUUSD RELEVANCE**：HIGH —— 直接印证 R1'-B/C（机会成本>保护、C 冗余）与 FL-18（复杂度不产生价值）。
- **DATA**：已有（vol 特征管线）
- **VALUE**：B（非方向风险信息）+ 方法论

## F4 — 交易成本 regime 依赖 ★（本轮最高价值）

- **SOURCE**：NBER w24222（Collin-Dufresne/Daniel/Sağlam）· E3
- **CLAIM**：交易成本随波动 regime 显著变化（高波动期更高）；**OOS 最大收益来自择时"波动率+交易成本"，而非择时预期收益**。
- **MECHANISM**：regime-switching 下最优交易速度 state 依赖；二阶矩比一阶矩更可估（Merton 1980）。
- **EVIDENCE**：机构真实交易成本（implementation shortfall）+ regime 模型，OOS 验证。
- **CONTRADICTION**：无强反证。
- **XAUUSD RELEVANCE**：HIGH —— 这是 R1 adaptive 方向最强的一个外部机制级支撑：它说"风险/成本层的时间变化"比"收益层"更值得择时，与 XAUUSD 的 E5 结论（vol 信息非方向、方向无 edge）**高度一致**。
- **DATA**：已有（activity→vol + spread 成本代理）
- **VALUE**：B（风险层）+ 为 R1 提供机制论证

## F5 — last look + 流毒性 ★（执行层）

- **SOURCE**：BIS 2025 Triennial（E3 权威）+ divitae 执行层文献（E1）
- **CLAIM**：非银行流普遍带 last look（50-200ms 可拒）→ 公布价差是"非对称期权"；真实成本 = 成交单半价差 + 被拒单机会成本 > 半价差。
- **MECHANISM**：流毒性（系统早于不利 mid 移动到达）→ 流动性商针对性加宽/降级（MECH-05）。
- **EVIDENCE**：BIS 结构数据（内部化>80%、电子 59%、15+ 平台）。
- **CONTRADICTION**：无（结构事实）。
- **XAUUSD RELEVANCE**：HIGH —— 直接解释 Phase 5 成本幻觉 + FL-05/FL-21；≤1m 候选"真实可交易性"依赖此。
- **DATA**：需成交级 tick + 拒单记录（当前缺失 → DATA GAP）
- **VALUE**：C（执行/风险层）

## F6 — OTC 内部化/碎片化

- **SOURCE**：BIS 2025 Triennial · E3
- **CLAIM**：>80% 客户交易被 dealer 内部化，流不可见；多层级各自加延迟/点差。
- **MECHANISM**：碎片化 → "同信号在 sub-1ms vs sub-100ms 是不同策略"（MECH-06）。
- **XAUUSD RELEVANCE**：MEDIUM（理解 + 解释 FL-13 feed confusion）
- **VALUE**：D

## F7 — OFI 放大价格波动

- **SOURCE**：Fed FEDS Note 2025（美债）· E3
- **CLAIM**：OFI 放大价格波动 = 固有流动性风险的事后实现。
- **CONTRADICTION**：XAUUSD ≥5m imb 方向已 REJECTED（KD-C07）。
- **XAUUSD RELEVANCE**：LOW（方向已否；仅 vol/流动性风险层有意义）
- **VALUE**：D

## F8 — OTC 信息追逐 vs 逆向选择

- **SOURCE**：Zou（junyuanzou.com）· E2
- **CLAIM**：dealer 追 informed 订单的动机抵消逆向选择恐惧。
- **XAUUSD RELEVANCE**：LOW（无 dealer 身份数据）
- **VALUE**：D

## F9 — 回测过拟合 / deflated Sharpe ★

- **SOURCE**：Bailey-López de Prado SSRN 2606462 · E2
- **CLAIM**：试足够多变体必然"发现"盈利；随机序列也能优化出策略；必须按 trial 数缩减。
- **MECHANISM**：multiple-testing 下 E[max Sharpe] 随 trial 数增长（MECH-10）。
- **XAUUSD RELEVANCE**：HIGH（映射 FL-12/FL-03）
- **VALUE**：方法论红线

## F10 — LLM 搜索强度泄漏 ★（直接针对我们）

- **SOURCE**：arXiv:2608.27734（2026）· E2/E3
- **CLAIM**：LLM agent 循环提议/评估/精炼策略，在看到第一个数字前已做几十次隐式回测；不按搜索强度缩减 → agent 生产力变成偏差放大器；文本"避免 lookahead"是弱护栏。
- **MECHANISM**：search-intensity leakage（MECH-11）。
- **EVIDENCE**：leakage-safe/search-aware 评估框架，独立审计（Yao-Zheng 2026; Li et al 2025）。
- **XAUUSD RELEVANCE**：HIGH —— OpenClaw/Hermes 都是 LLM 驱动研究，此失败模式直接适用。
- **VALUE**：方法论（FL-20）

---

## 价值漏斗（VALUE DISCOVERY RATE）

- Total screened（本轮检索结果）≈ 30+ 条原始结果
- High-quality（去重后保留）10 条
- XAUUSD relevant（MEDIUM+）7 条
- Research candidates（进队列）5 条（RQ-01..05）
- 核心新机制（HIGH 价值）5 条（F3/F4/F5/F9/F10）

> 核心不是"抓了多少网页"，而是 30→10→7→5 的漏斗里，5 个 HIGH 价值发现全部落在**风险/执行/方法论层**，
> 与"方向 alpha 已死"的研究现状一致——这本身就是对研究方向的独立验证。
