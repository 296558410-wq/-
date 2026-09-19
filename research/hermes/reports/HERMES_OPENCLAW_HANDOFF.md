# HERMES OPENCLAW HANDOFF（向 OpenClaw 提交的研究机会）

> 生成：2026-09-05 · HERMES-03 · TOP RESEARCH OPPORTUNITIES。
> 每个：ID/Mechanism/Evidence/Why/Known/Unknown/Data/Overlap/Risk/Priority/Next step。
> **Recommended next step 只能是 REVIEW / PREREGISTER / DATA_GAP / ARCHIVE / CONTRADICTION_REVIEW。**
> 不得要求 "RUN STRATEGY"。Hermes 不自行实验、不自行宣布成功。

---

## 三个值得 OpenClaw 优先审查的机会（按价值排序）

### OP-1 · 形态条件化的 Adaptive Risk Edge —— REVIEW（最高优先）

- **Mechanism**：交易成本/波动 regime 依赖 + vol-timing 争议链（MECH-03/04 + CONTRA-01）
- **Evidence**：NBER w24222（成本择时>收益择时）+ arxiv:2212.07288（vol-target 成本幻觉）+ 本地 E5（activity→vol 0.60-0.89 非方向）
- **Why relevant**：外部证据与本地 R1' 结论**互相印证**——"无条件日级 vol 降险为负（机会成本>保护）"不是孤例，而是 vol-timing 的普遍失败模式；存活路径是"形态条件化 + 成本感知"。
- **Known**：R1'-B-N2 REJECT、C REDUNDANT、A feed-limited；E5 vol 信息成立但非方向。
- **Unknown**：哪种风险"形态"值得事前门控（R1' NEXT QUESTION 的 autopsy 尚未做）。
- **Data needed**：已有（FXTM H1/M1 + DUKA M1）。
- **Overlap**：与 R1' 直接衔接，非重复。
- **Risk**：重蹈"无条件 gate"覆辙 → 必须先 autopsy 定形态，再预注册。
- **Priority**：HOT
- **Next step**：**REVIEW**（先完成 R1' 遗留的 Market Autopsy 形态刻画，再决定是否预注册）

### OP-2 · 执行层真实成本模型（last look + 流毒性）—— DATA_GAP

- **Mechanism**：MECH-05（last look 非对称期权 + 流毒性）
- **Evidence**：BIS 2025 Triennial（E3 权威结构）+ FX 执行文献
- **Why relevant**：直接解释 Phase 5 成本幻觉；决定 ≤1m 候选的"真实可交易性"。
- **Known**：FXTM 固定点差无择时空间；DUKA 可变点差有薄 alpha。
- **Unknown**：XAUUSD 零售 feed 的 last look 参数、拒单率、流毒性。
- **Data needed**：成交级 tick + 拒单/流毒性标记（**缺失**）。
- **Overlap**：扩展 RID-005/KD-O02。
- **Risk**：数据缺口 → 只能理论+理想化假设。
- **Priority**：HOT（但被 DATA GAP 阻塞）
- **Next step**：**DATA_GAP**

### OP-3 · 研究协议升级：LLM search-intensity 泄漏的结构性防护 —— REVIEW

- **Mechanism**：MECH-11（LLM 隐式多回测 = 偏差放大器）
- **Evidence**：arxiv:2608.27734（2026）+ 独立审计
- **Why relevant**：OpenClaw/Hermes 都是 LLM 驱动研究；FL-20。
- **Known**：Phase 9A 已有 freeze/Gate/redundancy 守卫。
- **Unknown**：如何把 lookahead 修正 + search 缩减从"程序性"升级为"结构性"（执行环境级）。
- **Data needed**：无（方法论）。
- **Overlap**：扩展 FL-16/17/20。
- **Risk**：无。
- **Priority**：HOT
- **Next step**：**REVIEW**

---

## 次要机会

### OP-4 · LBMA 定盘窗 autopsy —— WARM（REVIEW）
描述性研究（RID-009 延伸）：定盘窗（10:30/15:00 伦敦）在 FXTM tick 上是否有可辨识微观结构特征。数据已有。价值 D/B。

### OP-5 · COMEX→现货 lead-lag —— DATA_GAP
跨资产价格发现（KD-U05）：需 COMEX/GLD 数据，当前未接入。

---

## 一个明确的 CONTRADICTION_REVIEW 建议

CONTRA-01（volatility-managed portfolios 争议）值得 OpenClaw 以"矛盾审查"视角重读：它的结论
（单因子 OOS+净成本失败；多因子+净额+成本优化+平滑才存活）**几乎逐条对应我们的 R1' 结论**。
建议把它作为 R1 方向继续与否的**外部基准线**，而非新的研究假设。

---

## 底线声明

本轮没有发现任何"值得立即预注册的方向 alpha"——这与 Phase 1-9A + R1' 的结论一致：
价值在**风险/执行/方法论层**，不在方向层。上面 3 个 HOT 机会全部落在这些层。
