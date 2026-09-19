# HERMES-05 HANDOFF（向 OpenClaw 提交）

> 生成：2026-09-05 · HERMES-05 · 只输出：NEW INFORMATION / CONFIRMED / CONTRADICTED /
> UNKNOWN / FAILURE / DATA GAP / INACCESSIBLE / RESEARCH CANDIDATE / METHODOLOGY RISK。

---

## NEW INFORMATION（本轮新挖到的）

1. **参数化 look-ahead（FINCAD）的代码级确证**：waylonli/FinCAD（MIT, EMNLP 2026 Main）存在，
   结构确证论文声称。这是 FL-23 的一手代码证据。
2. **LLM 交易 agent 评估已形成成熟工具生态**：OpenPM / CLQT / induced-null / purged-CV，
   RQ-05 的审计不必从零设计。

## CONFIRMED（外部与本地收敛）

3. **方向 alpha 稀缺**：LLM agent 的 alpha = 被动暴露（FL-24）+ 子基点死于费用（FL-25），
   与本地两期双源 0 SUPPORTED 收敛。
4. **风险/成本择时层是可及价值**：Collin-Dufresne（成本择时>收益择时）+ Moreira-Muir 争议链
   与本地 E5 vol 信息 + R1' 结论互相印证。

## CONTRADICTED（找到反证）

5. 期权 IV 预测收益 = 借券费代理（Muravyev JFE 2025，CONTRA-05）。
6. 做市盈利 = 环境驱动非策略（arxiv:2606.05882，CONTRA-07）。
7. 订单流预测汇率 = 依赖专有数据（CONTRA-06）。

## INACCESSIBLE（勿再投入）

8. 做市 spread capture、现货-期货 basis 套利、订单流→汇率——无 maker 通道 / L2 / 专有 dealer 流。

## RESEARCH CANDIDATE

9. RQ-05（泄漏审计，含参数化 look-ahead）——**本轮最高优先级**，有现成工具。
10. RQ-01（形态条件化 adaptive risk）——外部机制级支撑已齐。

## METHODOLOGY RISK（直接针对 OpenClaw/Hermes）

11. **参数化 look-ahead**：deepseek 训练 cutoff 与 XAUUSD 历史重叠，现有截断重算/purged-CV 守卫
    抓不到权重级泄漏。建议：任何"模型参与的历史推断"结论，都需 post-cutoff 窗口 + 实体匿名化对照。

## DATA GAP

12. DUKA tick（KD-U01）仍是阻塞 ≤1m 方向族终审 + 执行层的关键缺口。

---

## 建议的下一步（仅 REVIEW / PREREGISTER / DATA_GAP，不含 RUN STRATEGY）

- RQ-05 泄漏审计 → **REVIEW**（最高优先）
- RQ-01 形态条件化 → **REVIEW**（先 R1' 遗留 Market Autopsy 形态刻画）
- RQ-07 执行模拟器落地 → **REVIEW**（RQ-02 前置工程）
- DUKA tick → **DATA_GAP**

---

## 底线

本轮（HERMES-05）的增量不是"找到了新策略"，而是：**(1) 证明了深挖能力**（一条 5 层深链 + 代码考古 +
反证链 + 图谱）；**(2) 画出了价值地图**——我们能持续获得价值的地方是"风险/成本择时 + 方法论严谨性"，
不是方向预测。**没有值得立即预注册的方向 alpha。**
