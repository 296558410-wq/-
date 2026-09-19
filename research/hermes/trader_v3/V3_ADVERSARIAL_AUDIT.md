# V3_ADVERSARIAL_AUDIT.md — 组G 反方审计框架（`@default`）

**性质**：组G 的工作框架与证伪台账。**不产出 Alpha**，只产 `REJECT / UNCERTAIN / DATA_GAP` 与攻击记录。
**权限依据**：任务书 §十四「任何成员报告 KEEP，组G 必须尝试证明这个 KEEP 是假的」+ 房间 §22.5 契约。

---

## 1. 核心原则

1. **KEEP 是控方主张，举证责任在提出方。** 组G 的攻击失败**不构成**支持证据。
2. **攻击失败 ≠ 结论成立**；只有在攻击被**至少一条独立路径**打过后仍存活，才可进 `KEEP`。
3. **一处不合规 ⇒ 整条降级**（不是「大体上没问题」）。
4. **组G 自家工具也要被审计**：本轮已发生 3 次「组G 探针自身缺陷被误报为闸门缺陷」（S-01/S-02/S-03），故**任何组G 报出的攻击结论，须附可复跑脚本 + 盘上哈希**，否则不受理。

---

## 2. 攻击清单（17 项，逐项须给出**可验证载体**，不接受口头回答）

| # | 攻击 | 必须交出的载体 |
|---|---|---|
| 1 | look-ahead | 特征计算所用数据的 `ts` 上界证明 ≤ 决策时刻；参数化 look-ahead 检查 |
| 2 | timestamp 可信性 | 时区/单位（ns/ms/us）举证；UTC vs broker server time 对照 |
| 3 | leakage | 训练/测试切分代码 + 切分点哈希；purge/embargo 宽度计算式 |
| 4 | 样本重叠 | 标签重叠矩阵或重叠率；非重叠版本复跑结果 |
| 5 | effective N | 有效样本数（含重叠折减 + 非空窗口上界，见 `V3_RESOLUTION_AUDIT.md` §4） |
| 6 | multiple testing | 族内**累计** n + 矫正方法 + 分母冻结时点（见 `V3_MULTIPLE_TESTING_LEDGER.yaml`） |
| 7 | regime selection | regime 划分**事前**定义 + trailing-only 证明；≥3 个 regime 同号 |
| 8 | transaction cost | 成本项 source 标注；未知项 fail-closed；`0x/0.5x/1x/1.5x/2x/3x` 全跑 |
| 9 | latency | 三段延迟（local/net/broker）必填；`UNRESOLVABLE` 不得填 0 |
| 10 | spread | 点差口径（crossed/round-trip/bp 换算基线名）；点差 ×1/1.2/1.5/2 全跑 |
| 11 | execution 可行性 | 被动成交双边界（`strict` / `nofill`）；`nofill` 必须 `fill_rate: null` |
| 12 | placebo | placebo 设计 + 结果 |
| 13 | permutation | 置换检验设计 + 结果 |
| 14 | block bootstrap | 块长选择依据 + 结果 |
| 15 | OOS | hold-out 单侧锁定证明；OOS mean / median 双正 |
| 16 | walk-forward | 窗口切分方案 + 每折结果 |
| 17 | 价格量级/连续性健全性 | 单位与量级检查（既有缺口：`p2` 无此检查，金价 727,761 USD/oz 仍 exit 0） |

**附加（本项目特有）**：
- **A/B/C 三类能力边界**（可算 / 只能代理 / 结构性不可算，见房间 §22.2）：**C 类被当 A 类跑出数字 ⇒ 该结论当场作废**（等同造数据）。
- **Quote OFI ≠ Trade OFI**：混称 / 混算 ⇒ 当场作废。
- **波动率族方向化**：`DE-06` 重开条件 = 禁止；把 vol 可预测性写成方向 Alpha ⇒ 当场作废。
- **UNRESOLVABLE 填 0 / 插值制造高频**：当场作废。
- **合规 ≠ 可引用**：产物按现行不变式不矛盾，**不等于**它出自被签字的版本；引用必须带完整相对路径 + 出处哈希。

---

## 3. 裁决梯度（本框架唯一出口）

```
提出方: KEEP
      │
      ├─ 17 项任一「载体缺失」 ─────────────► UNCERTAIN (原因: 举证不足, 非结论)
      ├─ 任一项「攻击成功」 ────────────────► REJECT
      ├─ 成本 ×3 后不存活 ─────────────────► REJECT (情况A, 任务书 §十六)
      ├─ 成本后存活但执行不可行 ────────────► REJECT (情况B)
      ├─ 跨期两独立时段不同号 / 仅单期 ─────► UNCERTAIN
      ├─ 依赖 UNRESOLVABLE 档位 ────────────► DATA_GAP
      └─ 全部通过 ─────────────────────────► KEEP_CANDIDATE (仍不得下单, 任务书 §十八)
```

**强制降级工具**：`KEEP → UNCERTAIN` 或 `REJECT`，**组G 行使时不需提出方同意**；提出方若有异议，须以**新 Experiment ID** 重新举证（不得改原登记）。

---

## 4. 台账（当前为空——这是诚实状态，不是遗漏）

| 审计 ID | 被审对象 | 攻击项 | 结果 | 证据 |
|---|---|---|---|---|
| — | 无 | — | — | 尚无任何 `KEEP` 主张被提交 |

**当前基准**：`directional KEEP = 0`（`V3_ALPHA_MAP.md` v0，24 族）。任务书 §十五 明示此基准可接受。
组G 现有 3 个 `KEEP` 全部为**非方向 / risk·execution 层**，**不构成方向 Alpha 证据**。

---

## 5. 数据可得性层面的既有裁决（组G 已下，延续有效）

| 项 | 裁决 | 依据 |
|---|---|---|
| 100ms / 50ms 延迟档在 DUKA 上 | **UNRESOLVABLE**（50ms 为 STRICT），**禁填 0** | `V3_RESOLUTION_AUDIT.md` §3 |
| 250ms / 500ms 延迟档 | `RESOLVABLE_WEAK`（仅少数窗口有信息） | 同上 |
| DXY→黄金 lead-lag | **CONTRADICTED**，原样重跑 = 自动 REJECT | `CL-10` / `CONTRA-08` |
| 跨资产 lead-lag Δt ≤1s | `UNRESOLVABLE`（无第二市场同精度 tick） | 房间 §22.3-3 |
| 做市吃点差 | `INACCESSIBLE`（`DE-08`）+ `CONTRADICTED`（`CL-09`） | 既有 |
| 波动率族方向化 | **禁止**（重开条件 = 禁止） | `DE-06` |
| 月 +100% / 加杠杆提频率 | **REJECT** | 房间 §0 三条 |
| 高周转 + 被动吃点差路线 | 需过 P2 七条，任一条不过 ⇒ **当场判死** | 房间 §15.8 |

---

## 6. 组G 自身可复跑产物（审计工具也须可审计）

| 产物 | 作用 |
|---|---|
| `.g_audit/g_resolution_audit_default.py` | 本框架 §5 的分辨率裁定实测器 |
| `V3_RESOLUTION_AUDIT.md` | 分辨率裁定 + 777ms 数字修正 |
| `V3_MULTIPLE_TESTING_LEDGER.yaml` | §2 第 6 项（多重检验）的冻结载体 |

*本文件由 AI Agent（`@default`）产出，只给工程与统计口径，不构成投资建议，不承诺任何收益。*
