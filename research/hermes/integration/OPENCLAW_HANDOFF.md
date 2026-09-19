# OPENCLAW HANDOFF（HERMES-09 提交）

> 生成：2026-09-05 · Handoff 现在含 MEMORY_STATE，不只"找到一个研究"。

---

## 现在 OpenClaw 提交研究问题给 Hermes 的流程

```
问题 → Hermes 查 Memory → 分类 → 返回：
  MEMORY_STATE + WHAT_WAS_KNOWN + WHAT_IS_NEW + WHAT_FAILED + WHAT_CONTRADICTS
  + WHAT_DATA_UNLOCKED + WHY_DESERVES_RESEARCH / WHY_NOT
  → OPENCLAW_ACTION: NEW_RESEARCH / REVISIT / CONTRADICTION_REVIEW / DATA_ACQUISITION / STOP
```

## 本轮交付给 OpenClaw 的核心能力

1. **研究决策引擎**（`research_decision_engine.yaml`）：10 类输出 + 5 步路由 + 硬规则（UNKNOWN≠NEW）。
2. **语义去重**（`semantic_duplication.yaml`）：机制级同义映射表（动量/RSI/MACD→DE-01 等）。
3. **Revisit 引擎**：DUKA tick / 期权 / COMEX / maker 通道 / 审计工具 五类触发 → REVISIT_CANDIDATE。
4. **矛盾解析器**：CLAIM_A vs CLAIM_B 不选边，按 7 维对比 → 5 类输出。

## 诚实暴露的边界（供 OpenClaw 知悉）

**分类器在 NEW 边界会漏判语义重复**（3 个 boundary 案例）——"期限结构斜率"实为 basis 的改名、
"VWAP 偏离反转"可能撞均值回归死胡同。这是"隐藏重复"最难的角落，需要机制级同义映射表持续补强。

## 建议 OpenClaw 的动作

- 无需新研究启动（本轮是集成 + 测试，非新发现）。
- 若接入决策引擎，建议把 `semantic_duplication.yaml` 的同义映射表纳入 Registry V2 的冗余守卫。

## 底线

HERMES-09 的价值：**让"先查记忆再决定偷什么"成为硬流程，而非靠模型记忆的直觉。**
分类器 19/22 正确（含 3 个诚实记录的 boundary），证明"已知项"的路由可靠，同时诚实暴露了
"语义重复"这一真实弱点。这正是成熟研究引擎该有的样子：可靠的部分可靠，薄弱的部分明确标注。
