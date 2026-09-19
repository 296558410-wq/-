# OPENCLAW HANDOFF（HERMES-11 对抗情报提交）

> 生成：2026-09-05 · 独立反情报部门。BELIEF_ATTACKED + 证据 + 影响等级。

---

## 唯一 ROUTE_CHANGING 级别的发现：无

诚实说明：本轮没有找到"会推翻半年研究路线"的证据。找到的是 3 个 MEDIUM 级 refinement + 多个 CONFIRM。

## MEDIUM 级（改变具体做法，不改变大方向）

### 1. 机构持仓是"隐藏的可及性"（REC-01）★ 最重要的挑战
- **BELIEF_ATTACKED**：D（机构 order flow / market making 不可及）
- **CURRENT_VIEW**：INACCESSIBLE
- **NEW_EVIDENCE**：CFTC COT 报告公开、每周、免费（含 disaggregated CSV + API），提供黄金期货投机 vs 商业净持仓。
- **WHAT_CHANGED**：**持仓层（positioning）是 PARTIALLY_ACCESSIBLE**，不是全 INACCESSIBLE。
- **WHAT_DID_NOT_CHANGE**：高频 signed order flow 仍 INACCESSIBLE；COT 是周频+滞后3天的情绪层，非流层。
- **WHAT_THIS_DOES_NOT_PROVE**：COT 极端持仓 ≠ 预测反转（cotdata.net 明示"不是交易信号"）。
- **IMPACT**：MEDIUM —— 为 XAUUSD 增加一个此前漏掉的"机构持仓/情绪"非方向输入，契合 E5 信息层。
- **OPENCLAW_ACTION**：CONSIDER（纳入 R1 形态/状态变量）

### 2. "执行层"应拆成两个具体机制（REC-02）
- **NEW_EVIDENCE**：Liquidity Provision as Alpha（bryanvine，24M snapshots, causal, strict forward）
- **WHAT_CHANGED**："execution alpha"从模糊方向拆成：(1) 执行 overlay（micro-price 门控降滑点 ~13%）；(2) vol-条件反转溢价（Sharpe 0.42→1.16）。
- **WHAT_THIS_DOES_NOT_PROVE**：做市本身可及（sub-0.1bp 游戏，仍 INACCESSIBLE）。
- **IMPACT**：MEDIUM —— RQ-02 应聚焦这两个具体形式。
- **OPENCLAW_ACTION**：REVIEW

### 3. "L2 是硬瓶颈"被削弱（REC-03）
- **NEW_EVIDENCE**：执行 overlay 只需 micro-price（bid/ask），不需 L2；L2 仅做市必需。
- **IMPACT**：LOW-MEDIUM —— 削弱"无 L2 无法研究执行"的隐含假设。

## CONFIRM 级（强化既有判断，不改变）

- **方向已死**：2607.20093（零售信号族 REFUTED）+ 2605.04004（MNQ 14 族无一存活）。
- **代理风险**：volume 归一化破坏信号、毛量≠净流、raw OBI 被 HFT 闪烁污染。
- **做市 INACCESSIBLE**：sub-0.1bp 游戏，queue/rebate/colocation 主导。

## 一个 MARKET-SPECIFIC EXCEPTION（提醒，不转移）

equities 日内 TTSM 成本后仍优于（S0927539823000245）——但这是 equities，**不转移到 XAUUSD spot**（§7 纪律）。

---

## 底线

作为反情报部门，本轮诚实的产出是：**没有 route-changing 的反证**（这本身是信息——说明 OpenClaw 的大方向
经过攻击后仍站得住），但有 1 个"隐藏可及性"（CFTC COT 持仓层）和 2 个执行层的具体化 refinement。

**最重要的一个词：POSITIONING ≠ FLOW。** 我把"机构流不可及"错误地扩展成了"机构持仓不可及"，
COT 报告纠正了这个过度概括——这是对抗性情报真正该抓的东西。
