# OPENCLAW HANDOFF — HERMES-04（深挖后的研究机会）

> 生成：2026-09-05 · 相对 HERMES-03 handoff 的更新。Recommended next step 只能是
> REVIEW / PREREGISTER / DATA_GAP / ARCHIVE / CONTRADICTION_REVIEW。

---

## 优先提交的 3 个机会

### OP-1（升级）· 研究协议泄漏审计 —— REVIEW ★ 最高优先
- **变化**：从 HERMES-03 的"候选"升级为"有现成工具 + 已识别新盲区"。
- **机制**：MECH-12/13/17（参数化 look-ahead + induced-null + point-in-time）
- **关键新证据**：参数化 look-ahead（FINCAD）——LLM 权重记忆历史结果，**现有截断重算/purged-CV 守卫抓不到**。
- **Why relevant**：OpenClaw/Hermes 都是 LLM 驱动研究；deepseek 训练 cutoff 与 XAUUSD 历史重叠。
- **Known**：Phase 9 有 freeze/Gate/ts-leak 冒烟；FL-01/02 覆盖数据管线泄漏。
- **Unknown**：权重级泄漏是否影响我们的结论；诱导零审计能否在我们的引擎上跑通。
- **Data needed**：无（方法论）。
- **Risk**：无。
- **Next step**：**REVIEW**（评估是否引入 induced-null 审计 + post-cutoff 窗口 + 实体匿名化对照）

### OP-2（升级）· 执行层真实成本模型 —— DATA_GAP
- **变化**：新增可复用基础设施（ordersim/hftbacktest/MicroExchange），RQ-07 前置工程成熟。
- **Known**：Phase 5 执行模拟器未完成；FXTM 固定点差无空间。
- **Next step**：**DATA_GAP**（仍被 DUKA tick 阻塞，但可先自建执行模拟器 RQ-07）

### OP-3（维持）· 形态条件化 adaptive risk —— REVIEW
- **变化**：无新反证；D1（执行成本负结果）进一步印证"成本是决定项"。
- **Next step**：**REVIEW**（R1' 遗留 Market Autopsy 形态刻画优先）

---

## 新增机会

### OP-4 · 黄金 basis/backwardation 压力信号 —— DATA_GAP
非方向压力信号（D/B），契合 E5 vol/activity 层。需 COMEX 期货 + LBMA 现货数据（KD-U05）。**Next step**：DATA_GAP。

### OP-5 · 执行模拟器落地 —— REVIEW
补齐 Phase 5 未完成工程（RQ-07），是 OP-2 的前置。**Next step**：REVIEW。

---

## 一个明确的 CONTRADICTION_REVIEW 建议

**期权 IV 预测收益 = 借券费代理（CONTRA-05）**：Muravyev JFE 2025 的强反证削弱了"期权信息领先价格"。
若未来考虑引入黄金 CVOL/implied 作为非方向信号，须先审查"它是真信息还是摩擦代理"（黄金无卖空约束，
机制可能不同）。**Next step**：CONTRADICTION_REVIEW。

---

## 明确标记 INACCESSIBLE（勿再投入研究精力）

做市 spread capture、现货-期货 basis 套利、订单流→汇率、做市盈利策略优化——这些都依赖我们拿不到的
数据/通道（maker 接入、L2 深度、专有 dealer 客户流、实物交割）。保留理解价值 D，不再作为研究候选。

---

## 底线声明

本轮没有发现任何"值得立即预注册的方向 alpha"（与 Phase 1-9A + R1' 一致）。真正的新增量是**方法论层**：
1. 参数化 look-ahead 是我们守卫体系的一个真实盲区（A4/FL-23）；
2. 一批机构/HFT edge 被明确标记 INACCESSIBLE，防止未来误投入；
3. 一个诚实负结果（子基点 edge 死于真实费用）印证了执行成本是决定项。
