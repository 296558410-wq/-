# HERMES-04 GLOBAL DEEP SCAN（全球深挖扫描报告）

> 生成：2026-09-05 · 对 HERMES-03 四条高价值线索的深挖。12 个发现，全部真实检索。
> 每个发现含完整字段链。分类：HOT / WARM / ARCHIVE / CONTRADICTION / DATA GAP / INACCESSIBLE。
> 机器可读见 global_intelligence/{mechanisms_deep,accessibility_matrix,contradiction_updates,failure_updates,research_queue_update,research_lineage_update}.yaml

---

## LINE A — Research Leakage / Agentic Quant（4 发现）

### A1 · 搜索强度泄漏（深挖）— HOT
- **SOURCE**：arxiv:2608.27734（HERMES-03 已记 MECH-11，本轮深挖其机制细节）
- **CLAIM**：LLM agent 循环提议/评估/精炼策略，在看到第一个数字前已做几十次隐式回测；不按搜索强度缩减，agent 生产力变成偏差放大器。
- **EVIDENCE**：deflated Sharpe/PBO 未在 LLM 策略发现文献应用（独立审计：Yao-Zheng 2026, Li et al 2025）。
- **INFERENCE**：文本"避免 lookahead"是弱护栏——不阻止生成的策略消费未来信息。
- **APPLICABILITY**：直接针对 OpenClaw/Hermes（LLM 驱动研究）。
- **COUNTER_EVIDENCE**：无（方法论共识）。
- **CONFIDENCE**：HIGH。**VALUE**：方法论。**STATUS**：HOT（RQ-05）。

### A2 · 诱导零环境审计 — HOT
- **SOURCE**：arxiv:2604.15531 "Spurious Predictability in Financial ML"
- **CLAIM**：在"诱导零"（保留金融数据特征、移除条件均值可预测性）环境上评估完整工作流，区分真可预测 vs 选择偏差/泄漏/时序违反造成的虚假可预测。
- **EVIDENCE**：随机 CV 破坏时序→lookahead；波动预测的验证选择在 null 下机械改善表现（可复现）。
- **INFERENCE**：这是**可执行的 Research Leakage Audit**——LINE A 要的"audit 候选"。
- **APPLICABILITY**：可直接在 XAUUSD 现有数据上构造诱导零，验证我们的引擎（呼应 Phase 1 已知答案实验，但更系统）。
- **DATA**：无需新数据。**CONFIDENCE**：HIGH。**VALUE**：方法论。**STATUS**：HOT。

### A3 · point-in-time 审计基准 — HOT
- **SOURCE**：arxiv:2608.09988 (OpenPM) + arxiv:2606.29771 (CLQT)
- **CLAIM**：LLM 交易 agent 评估须强制 point-in-time（availability time 非 event time）、成本感知、策略一致性；把 lookahead 当作失败前置条件（TimeGate），hash 链可重算审计。
- **INFERENCE**：现成的审计基准参考实现——我们不必从零设计 RQ05 审计。
- **APPLICABILITY**：OpenPM 的"row-gate + 认证"与 Phase 9 ts-leak 冒烟同源，可借鉴。
- **CONFIDENCE**：HIGH。**VALUE**：方法论。**STATUS**：HOT。

### A4 · 参数化 look-ahead（权重级泄漏）★ 本轮最重要新发现 — HOT
- **SOURCE**：arxiv:2605.24564 (FINCAD) + arxiv:2605.28359
- **CLAIM**：LLM 权重在训练时已记忆历史结果；回测窗口重叠训练 cutoff 时模型从记忆推理，偏差活在权重里，**数据管线审计看不见**。匿名化 ticker 后 agent 拒交易 → 证明信号来自 ticker 记忆而非数据。
- **EVIDENCE**：5 个 LLM(7B-14B)、5 只 mega-cap、5 个推理基准；11 个 LLM 上 Spearman 从 +0.779→+0.846。
- **INFERENCE**：**我们现有的 no-lookahead 守卫（截断重算、purged-CV）抓不到这种泄漏**——因为它在权重里，不在数据管线里。这是对"现有守卫是否覆盖"的直接回答：**没有完全覆盖**。
- **APPLICABILITY**：deepseek 模型训练 cutoff 与 XAUUSD 历史重叠 → 直接适用。
- **COUNTER_EVIDENCE**：无（新识别失败模式）。
- **CONFIDENCE**：HIGH。**VALUE**：方法论（FL-23）。**STATUS**：HOT。

---

## LINE B — Execution / Microstructure Value（3 发现）

### B1 · 做市盈利 = informedness 环境，非报价策略 — INACCESSIBLE
- **SOURCE**：arxiv:2606.05882
- **CLAIM**：做市商盈利主要由市场信息度环境驱动（spread 与 informedness R²<0.05），非报价策略优化。
- **INFERENCE**：做市盈利是环境/基础设施 edge，不是"学会 A-S 做市就能赚"。
- **APPLICABILITY**：XAUUSD 我们无 maker 通道、无 L2 → 只有理解价值。
- **DATA/INFRA**：做市接入（缺）。**COUNTER_EVIDENCE**：A-S 理论框架（CONTRA-07）。
- **CONFIDENCE**：MEDIUM。**VALUE**：D。**STATUS**：INACCESSIBLE。

### B2 · spread capture / 做市经济学 — INACCESSIBLE
- **SOURCE**：Avellaneda-Stoikov + Brenndoerfer/Menaldo（spread/2 > 逆向选择 + 库存成本）
- **CLAIM**：做市盈利 = 价差收益 − 逆向选择 − 库存风险。
- **INFERENCE**：这是"价差为何存在"的理论；对我们不可交易（无 maker 通道）。
- **STATUS**：INACCESSIBLE（D 类理解价值）。

### B3 · 订单流→汇率（Evans-Lyons）— INACCESSIBLE
- **SOURCE**：Evans-Lyons (NBER w7317/w13151/w11748)
- **CLAIM**：订单流解释 40-80% 日度汇率变动，预测宏观基本面优于汇率本身。
- **COUNTER_EVIDENCE**：依赖 Citibank 专有客户流（不可获取）；4 个月样本 OOS RMSE 改善 30-40% 但统计不显著。
- **INFERENCE**：机制真实但可及性 INACCESSIBLE——"订单流预测汇率"的可复现性依赖我们拿不到的数据。
- **STATUS**：INACCESSIBLE（CONTRA-06）。

---

## LINE C — Gold / FX Specific（3 发现）

### C1 · 黄金 basis/backwardation = 实物压力信号 — WARM
- **SOURCE**：derivativesjournal + goldify + metalcharts（机制一致）
- **CLAIM**：basis 由资金成本+实物需求+投机持仓+压力决定；backwardation=实物需求压力；2020 EFP 错位 >$100 是压力先兆；GOFO 是旧远期利率。
- **INFERENCE**：非方向压力信号（D/B 类）——契合 E5 vol/activity 层。
- **DATA**：COMEX 期货 + LBMA 现货（缺 → KD-U05）。
- **CONFIDENCE**：MEDIUM（机制描述一致，未在 XAUUSD 现货验证）。
- **VALUE**：D/B。**STATUS**：DATA GAP（RQ-06）。

### C2 · 期权 IV 预测收益 = 借券费代理 — CONTRADICTION
- **SOURCE**：Muravyev-Pearson-Pollet (JFE 2025)
- **CLAIM**：IV spread/skew 预测收益，剔除高借券费股票后预测力降 ≥2/3 → 大部分是借券费/卖空约束代理，非真信息缓慢扩散。
- **COUNTER_EVIDENCE**：经典"期权信息领先价格"文献（CONTRA-05）。
- **INFERENCE**：降级对黄金 CVOL/implied 的期待；黄金无卖空约束，机制可能不同，需独立检验。
- **DATA**：黄金期权 IV（缺）。
- **CONFIDENCE**：HIGH（JFE 同行评审）。**VALUE**：D/方法论。**STATUS**：CONTRADICTION。

### C3 · 三市场价格发现链（伦敦/纽约/上海）— DATA GAP
- **SOURCE**：goldify/metalcharts（SGE 量自 2014 三倍）
- **CLAIM**：价格发现在 LBMA 现货/COMEX 期货/SGE 之间连续转移；亚洲时段影响力上升。
- **INFERENCE**：跨市场 lead-lag 是信息，但需跨市场数据。
- **STATUS**：DATA GAP（KD-U05）。

---

## LINE D — Quant Community / Open-source（2 发现）

### D1 · 子基点 edge 死于真实费用（诚实负结果）— HOT（失败案例）
- **SOURCE**：H2nryHe/Microstructure_Alpha_Execution_Lab（GitHub）
- **CLAIM**：BTC-USDT 微观结构 alpha：0ms 下 breakeven fee ~0.687bp，0.5bp 费用下净正天数 2/6；QI+OFI 未稳健改善净经济。
- **INFERENCE**：**执行先于经济学**——信号是 desired state 非 fill；成本显式。子基点 edge 被真实费用抹平。
- **APPLICABILITY**：直接印证 FL-05/FL-21/Phase 5——执行成本是决定项。
- **CONFIDENCE**：HIGH（可复现仓库 + 明确负结果）。**VALUE**：方法论 + 失败案例。**STATUS**：HOT（FL-25）。

### D2 · 可复用研究基础设施 — WARM
- **SOURCE**：intrepidkarthi/orderbook (Go CLOB) + MicroExchange (C++ Hawkes) + ordersim/hftbacktest（执行模拟）
- **CLAIM**：生产级 CLOB 匹配引擎、Hawkes 仿真、purged-CV、因果重放、执行模拟器——开源成熟。
- **INFERENCE**：补齐 Phase 5 未完成的 tick 执行模拟器 + RQ-05 的 purged-CV 工具，有现成实现。
- **APPLICABILITY**：RQ-07 的前置工程。
- **CONFIDENCE**：HIGH（可审查开源）。**VALUE**：方法论。**STATUS**：WARM。

---

## 分类汇总

| 分类 | 发现 | 数量 |
|---|---|---|
| HOT | A1/A2/A3/A4（泄漏审计）+ D1（执行成本负结果） | 5 |
| WARM | C1（黄金 basis）+ D2（基础设施） | 2 |
| CONTRADICTION | C2（期权 IV 借券费代理） | 1 |
| DATA GAP | C3（跨市场） | 1 |
| INACCESSIBLE | B1/B2/B3（做市/订单流） | 3 |

## 本轮最重要的三个结论

1. **参数化 look-ahead（A4）是我们现有守卫抓不到的新盲区**——它直接回答了 LINE A 的核心问题：
   "现有 no-lookahead/preregistration/frozen registry 是否真的覆盖？" **答案是：没有，只覆盖了数据管线级，未覆盖权重级。**

2. **"别人能做"大部分是 INACCESSIBLE（B 线）**——做市、订单流、basis 套利都依赖我们拿不到的数据/通道。
   这轮把"机构 edge"与"我们可研究的 edge"明确切开了。

3. **执行成本是决定项，不是事后项（D1 + C2）**——一个诚实的开源负结果（子基点 edge 死于 0.5bp 费用）
   比十个"漂亮回测"更有价值，因为它印证了我们的 FL-05/Phase 5 判断。
