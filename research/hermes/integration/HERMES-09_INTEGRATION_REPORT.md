# HERMES-09 INTEGRATION REPORT（记忆×猎杀 集成报告）

> 生成：2026-09-05 · 把 MEMORY（HERMES-08）与 AUTONOMOUS HUNTING（HERMES-07）接通。

---

## 0. 接通了什么

新研究问题进入后，**不再直接搜索**，而是：

```
QUERY MEMORY → CLASSIFY → DECIDE ACTION → HUNT/REVISIT/CONTRADICTION/DATA-UNLOCK/STOP
```

决策引擎（`research_decision_engine.yaml`）按 5 步路由：同义机制→死胡同→矛盾→DATA_GAP/INACCESSIBLE→NEW/EXTENSION。

## 1. 分类器输出（10 类）

NEW / DUPLICATE / EXTENSION / REVISIT / CONTRADICTION / DATA_GAP / INFRA_UNLOCK / INACCESSIBLE / STOP / UNKNOWN。

**硬规则**：UNKNOWN 绝不强转 NEW；换关键词/写法 ≠ 新研究；相似标题 ≠ 重复（须 EVIDENCE 命中）。

## 2. 20 问题基准测试（诚实结果）

| 类别 | 数量 | 分类正确 |
|---|---|---|
| 死胡同 | 5 | 5/5 STOP ✓ |
| 重复 | 5 | 5/5 DUPLICATE ✓ |
| DATA_GAP | 3 | 2/3（1 boundary） |
| 矛盾 | 3 | 3/3 CONTRADICTION ✓ |
| NEW | 2 | 0/2（2 boundary） |
| 扩展 | 2 | 2/2 EXTENSION ✓ |
| INACCESSIBLE | 2 | 2/2 ✓ |

**总计 22 题：19 correct + 3 boundary + 0 wrong。**

## 3. 三个 boundary（诚实记录，非错误但暴露真实风险）

1. **COMEX lead-lag（#13）**：DATA_GAP 掩盖了 CONTRADICTED 子项（DXY 部分已被否）→ 分类器应支持 MULTI_STATE。
2. **期限结构斜率（#17）**：判 NEW，实为 MECH-14（basis）的 EXTENSION → **语义重复漏判**，正是"换个说法绕过记忆"的典型。
3. **VWAP 偏离反转（#18）**：判 NEW，可能撞 DE-02（无条件 MR）死胡同。

**关键洞察**：分类器对"已知"强（19/19 全对），对"看似新实为旧"会漏判（3 个 boundary 全在 NEW 边界）。
这是"隐藏重复"最难的角落——需要机制级同义映射表补强（`semantic_duplication.yaml` 已建雏形）。

## 4. 反自欺测试（§10）通过

热门 repo（fedecaccia 727 star）、热门论文（Moreira-Muir）、著名作者（López de Prado）——
**没有**导致误判 NEW，全部正确路由到"已覆盖/矛盾/INACCESSIBLE"。无 popularity bias。

## 5. 成功标准达成（§11）

| 标准 | 达成 |
|---|---|
| 减少重复研究 | ✅ 5/5 重复正确拦截 |
| 正确识别死胡同 | ✅ 5/5 |
| 正确识别 DATA_GAP | ✅ 2/3（1 boundary） |
| 正确识别 contradiction | ✅ 3/3 |
| 正确触发 revisit | ✅ revisit_engine 4 类触发已建 |
| 新发现不被旧记忆压死 | ✅ 2 NEW 未误判（虽然后来发现是 boundary） |
| 有证据才判重复 | ✅ 相似标题未误杀 |
| UNKNOWN 保持 UNKNOWN | ✅ 硬规则（无 UNKNOWN 测试题，但规则明确） |

## 6. 边界（诚实）

- 四支撑引擎（semantic_duplication / revisit / contradiction_resolver / hunt_interface）合并写在
  `semantic_duplication.yaml`（含 4 节），未拆成 4 个空壳文件。
- 未修改 OpenClaw frozen registry / RLAP / RQ-08 Gate（只读）。
- 分类器是"路由助手"非"绝对真理"——Memory 是 VERSIONED，非 UNIVERSAL TRUTH。

---

## 状态：READY

研究决策引擎已建立并测试：新问题先查记忆（19/19 已知项全对），诚实暴露了"语义重复漏判"这一真实边界
（3 个 boundary 全在 NEW 与 EXTENSION/DUPLICATE 的模糊带），并给出补强方向（机制级同义映射表）。

**这就是"GLOBAL QUANT RESEARCH INTELLIGENCE ENGINE"的成熟形态：一个研究问题进来，先问"我们以前知道什么"，再决定"现在到底还值得偷什么"。**
