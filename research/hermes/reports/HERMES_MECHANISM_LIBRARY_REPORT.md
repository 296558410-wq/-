# HERMES MECHANISM LIBRARY REPORT（机制库报告）

> 生成：2026-09-05 · 机器可读见 global_intelligence/mechanisms.yaml（MECH-01..11）。

## 11 个机制的 XAUUSD 价值分布

| 价值 | 机制 | 说明 |
|---|---|---|
| **HIGH** | MECH-03（vol-target 成本幻觉）、MECH-04（成本 regime 依赖）、MECH-05（last look/流毒性）、MECH-10（回测过拟合）、MECH-11（LLM 泄漏） | 全部落在风险/执行/方法论层 |
| MEDIUM | MECH-01（定盘拍卖）、MECH-02（COMEX 领先）、MECH-06（OTC 内部化）、MECH-09（逆向选择→加宽价差） | 理解/执行层背景 |
| LOW | MECH-07（OFI 放大）、MECH-08（信息追逐） | 方向层已否 / 无数据 |

## 三个"理解价值"最深的机制（D 类，不可交易但重要）

1. **MECH-02（COMEX 领先现货）**：解释 XAUUSD 价格发现的源头与跨市场传导——理解为什么"黄金价"是套利钉出来的，而非单一市场定价。
2. **MECH-06（OTC 内部化/碎片化）**：解释我们 feed 差异（FL-13）的根因——FXTM 零售 feed 是聚合层最末端，看不到 >80% 的内部化流。
3. **MECH-01（定盘拍卖）**：解释黄金 spot 最重权重的两个定价时刻（10:30/15:00 伦敦）。

## 三个"可操作"最强的机制（B/C 类）

1. **MECH-04（成本 regime 依赖）**：为 R1 adaptive 提供机制级外部支撑——"波动+成本择时 > 收益择时"。
2. **MECH-03（vol-target 成本幻觉）**：印证 R1' 的"成本侵蚀"发现，提示"平滑/形态条件化"是存活路径。
3. **MECH-05（last look/流毒性）**：执行层真实成本模型，决定 ≤1m 候选的真实可交易性。

## 去重结论

11 个机制中 2 个标 REDUNDANT（MECH-07 与 RID-001/P7 重叠）、5 个 EXTENSION（深化既有 RID/FL）、4 个 NEW。
无换名重复。
