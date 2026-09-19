# V3 C-31 FINALIZATION — 终裁 + §20.10 三读 + co-sign

生成：2026-09-17 · Owner：V3 总控 / 组G 终裁（自裁）

## 〇、结论（先说）
- **§3.1 判据终裁**：以 **换根率**（`frac_fill_tick_changed_vs_prev_rung`）为判据列；`same` 列保留作对照。
- **§3.2 生效基终裁**：`ladder-basis = signals`（策略实际信号集）为**生效基**；`ticks` 基保留作 feed 诊断。两基**不得互相顶替引用**。
- **§20.10 三读**：**未通过**（1/3 产物不可逐字节复现）。
- **co-sign**：**WITHHELD（拒签）**。
- **C-31 状态 = NOT_FROZEN**；**G1 = INSUFFICIENT_EVIDENCE**。
- 旧 `p2_net_edge_gate.py@5f51c5ba…` = **HISTORICAL**（保留，不冒充）。
- 冻结候选工具哈希 = `c364f060f7c6c6555c17f06c94ac42c173ae4a53b883f35e3e73a4542b2114d5`（位于 `.recheck_r32/`）——**但未签字**。

## 一、§3.1 终裁依据
- R-31.F 列名写 `frac_same_...`，但 R-31.C 阈值（≤0.50/0.50–0.90/≥0.90→可分辨）的括注"该档数字在多数交易上与上一档逐位相同"**只在"改变占比"上自洽**。
- 反证：R-31.D 公布 `1000 vs 500ms = 62.15%/69.45% → RESOLVABLE_WEAK`；若为"相同占比"，则改变率=37.85%/30.55%≤0.50 ⇒ 应判 UNRESOLVABLE，与公布裁定矛盾。
- **裁定**：公布数字是**换根率**。工具同时落 `changed`(判据) 与 `same`(对照) 两列；沿用 R-31.C 字样作 G-CONV-01 关闭。

## 二、§3.2 终裁依据
- R-31.C 原文对象 = "**交易**占比" ⇒ 默认 **signals 基**。
- 两基在真数据上给出**不同**裁定（signals: 250ms=WEAK；ticks: 250ms=UNRESOLVABLE）；二者度量不同对象（执行路径 vs feed 本身）。
- **裁定**：生效基 = `signals`；`ticks` 基仅作 feed 诊断；任何引用必须写明 basis。

## 三、§20.10 before/mid/after 三读（本机实跑）
| 读 | 对象 | p2_trades | p2_summary | p2_latency_ladder |
|---|---|---|---|---|
| before | 签字时产物（`R31_FIX_33333.md` 指纹） | `7c6154f8…` | `d5adab91…` | `8554aee2…` |
| mid | 工具确定性复跑（`determinism/`） | `7c6154f8…` ✅ | `d5adab91…` ✅ | `8554aee2…` ✅ |
| **after** | 总控独立复跑（冻结工具 `c364f060`） | `7c6154f8…` ✅ | **`3cd637e7…` ❌** | `8554aee2…` ✅ |

**判定**：`p2_trades` 与 `p2_latency_ladder` **逐字节可复现**；**`p2_summary_*.json` 不可复现**（同一冻结工具、同参数、同输入，输出哈希不同）→ **确定性缺陷**。

### 附带发现（治理）
- room 根目录 `p2_net_edge_gate.py` 当前哈希 = `c7e25c17…`（= **c364f060 之后的新版本**，新增 `experiment_id/outdir/period_trades` 字段），**不等于** C-31 冻结哈希。
- ⇒ **冻结哈希 c364f060 实际存在于 `.recheck_r32/p2_net_edge_gate.py`**；根目录版本系冻结后改动。
- 影响：任何"用根目录工具复现 C-31"的尝试都会得到新版本产物（≠冻结指纹），**不得**据此宣称 C-31 已复现。

## 四、影响与处置
- **C-31 不得签字冻结**：`p2_summary` 的非确定性使"唯一 artifact fingerprint + 逐字节一致"这一冻结前提不成立。
- **G1 维持 INSUFFICIENT_EVIDENCE**：C-31 未 FROZEN ⇒ **G2 不开放**（G2 开放条件之一 = C-31 FROZEN/PASS）。
- 已登记 G 审计 finding：`G-AUD-001`（summary 确定性缺陷）、`G-AUD-002`（冻结工件身份漂移：根目录 vs .recheck_r32）。
- 修复方向（不改判据、不重跑市场假设）：定位 `p2_summary` 中的非确定字段（疑似运行时元数据/浮点归约顺序/字典序），固定后重做 §20.10 三读；若纯元数据变量 → 可对该字段做规范化后重新冻结。

## 五、纪律声明
- 未改任何 V1/V2；未发任何 broker 单；`staging_duka` 只读；未删除历史快照 `5f51c5ba…`。
- 未为"通过验收"放宽判据；发现缺陷即**降级**，不保护结论。

## 六、ADDENDUM（根因定位后 → 已签字冻结）
- **根因**（`tools/v3_c31_diff.py`）：d5adab91 vs 3cd637e7 的差异 **只有 `/provenance/mtime`**（分类 F/G，运行时元数据）；**SEMANTIC_FIELD_DIFFS = 0**（trade count/fill tick/return/gross/cost/net/latency verdict/population/period/effective N/pass-fail 全部相同）。
- 因差异**仅属 metadata/serialization**（非 A/B/C/D），按新硬门禁**允许**建立 deterministic canonicalization。
- 规范化规范事前固定并落盘：`research/V3_CANONICALIZATION_SPEC.md`（key ordering / numeric / timestamp policy / path normalization / volatile exclusion / encoding / newline）。实现 `tools/v3_canonicalize.py`。
- **§20.10 三读（canonical）：PASS** —— 冻结工具跑 3 次，`p2_trades / p2_latency_ladder / p2_summary` 三份 canonical 产物**逐字节一致**。
- **co-sign 已给出 → C-31 = FROZEN**。Fingerprint: `research/c31_frozen/FINGERPRINT.json` + `state/C31_FROZEN.json`。
  - 工具 `p2_net_edge_gate.py@c364f060…`；canonical 产物哈希：trades `0ef81fad…` / summary `7fd5f4f0…` / ladder `6b222801…`。
- **G1 = PASS**；`G-AUD-001` = RESOLVED_BY_CANONICALIZATION（**历史 finding 保留**）；`G-AUD-002` = **OPEN**（身份漂移，独立保留）。
- **G2 仍 CLOSED**：开放条件 `VALID_DAY_FROZEN=NO`。
- 纪律：canonicalization **未**掩盖任何语义差异；若差异曾属 A/B/C/D，则保持 NOT_FROZEN（本次不适用）。
