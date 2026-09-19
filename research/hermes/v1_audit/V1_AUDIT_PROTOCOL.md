# V1 AUDIT PROTOCOL — 信息可见性边界与“不可证明事项”冻结（PHASE C）

- 生成：2026-09-17 · 目录 `research/hermes/v1_audit/` · **零修改 V1/V2/V3** · **无任何订单** · **本阶段不做 Alpha**。
- 产物：`V1_AUDIT_PROTOCOL.md` · `V1_INFORMATION_BOUNDARY.json` · `V1_ANALYSIS_ELIGIBILITY.json` · `V1_TRADE_RECONSTRUCTION_STATUS.json` · `V1_AUDIT_PHASE_C_SHA256.json`
- 脚本：`tools/v1_audit_phaseC.py`

## 0. 最重要：冻结“不可证明事项”
**无法从历史保存数据证明：“V1 在 T_signal 时完整看到了哪些原始市场输入”。**
- 因此后续报告**不得**写“V1 根据 X/Y/Z 做出了这个决定”，除非 X/Y/Z 在 **T_signal 前的已保存数据**中有直接证据。
- **可以**写：“V1 decision JSON 中记录了 `state_summary`，其中包含……”（**必须**与“实际完整输入”严格区分）。
- 该不可证明性对所有 57 笔交易**一致成立**。

## 1. T_order 恢复
- 规则：`T_order = positions/*.json` 的 **ENTER 事件 ts**；`T_exit = EXIT_FILL`（回退 review.exit.utc_ts）。
- 结果：**57/57 恢复成功**（reconstruction_source=`positions.ENTER`, confidence=HIGH）。
- 若缺失：标 **DATA_GAP**，**不得用 T_fill 永久替代**。

## 2. 信息可见性边界（A/B/C/D）
| 类 | 定义 | 允许用途 | 状态 |
|---|---|---|---|
| **A** | T_signal 前**实际保存且可确认存在**的信息（源A tick、registered 事件） | **ENTRY_DECISION_ANALYSIS** | 部分存在（逐笔覆盖见矩阵） |
| **B** | `decisions/*.json` 的 **state_summary（文本摘要）** | 描述“V1 当时记录了什么” | 存在（摘要）；**≠ 完整输入** |
| **C** | 仅 **latest state_package** 可见的信息 | 无 | **禁止用于历史决策解释** |
| **D** | T_signal 之后才能观察到（价格/spread/新闻/宏观/结果） | **POST_ENTRY_OUTCOME_ANALYSIS** | 可用（仅 outcome） |

**硬规则**：只有 **A** 可作为“V1 当时实际可见输入”的证据；**B 只是摘要**；**C 禁用于历史**；**D 只用于 outcome**。

## 3. 审计分析资格矩阵
每笔交易标注四维：`ENTRY_RECONSTRUCTION / OUTCOME_RECONSTRUCTION / COST_RECONSTRUCTION / COUNTERFACTUAL_ELIGIBILITY` ∈ {ELIGIBLE, PARTIAL, DATA_GAP, UNRESOLVABLE}（见 `V1_ANALYSIS_ELIGIBILITY.json`）。
- **ENTRY_RECONSTRUCTION：最高只能 PARTIAL（47 笔 PARTIAL / 10 笔 DATA_GAP），永不 ELIGIBLE**（因无完整输入快照）。
- **OUTCOME_RECONSTRUCTION：ELIGIBLE 53 / PARTIAL 1 / DATA_GAP 2 / UNRESOLVABLE 1**。
- **COST_RECONSTRUCTION：最高 PARTIAL**（spread 可由源A推导、slippage 已记录；commission/swap 未记录=DATA_GAP）。
- **COUNTERFACTUAL：依 signal→horizon 的 tick 覆盖**（ELIGIBLE/PARTIAL/DATA_GAP）。
- **缺口不静默删除**：全部 57 笔进入总体记录。

## 4. 周末缺口处理（冻结）
- 缺口 **09-11 23:54 → 09-14 01:05（49.2h）**；受影响 **11 笔**必须**保留**。
- **禁止**：删除 / 插值 / 用周末后第一笔 tick 填充 / 假设缺口期连续市场 / 把 GAP_WEEKEND 当普通数据。
- 跨该缺口的 forward return / MFE / MAE —— **无法严格定义 → DATA_GAP**。
- 具体：`POS-20260913T2217Z` = **DATA_GAP（OUTCOME）**；其余受影响交易按其窗口覆盖降级（PARTIAL）。

## 5. 盘中缺口处理（冻结）
- `09-08 05:46→07:31` · `09-15 05:54→09:01` · `09-17 10:24→11:00` + 每日日切 `23:54→01:05`。
- **禁止插值**。明确受影响的 horizon（缺口跨过的窗口不可计算 → **DATA_GAP**）：例 `POS-20260908T063856`、`POS-20260915T0632Z`。

## 6. 真实成本（逐项确认）
| 成本 | 状态 |
|---|---|
| spread（入场时刻） | V1 **未记录**（`spread_bps_at_entry=null`×57）；**可由源A推导** → PARTIAL |
| slippage | **已记录**（`execution.slippage_bps` ×57） |
| commission | **未记录 → DATA_GAP**（禁默认 0） |
| swap | **未记录 → DATA_GAP**（禁默认 0） |

## 7. 三个严格不同的分析集合
- **集合 A｜FULLY_RECONSTRUCTABLE**：可完整重建时间线**且**证明 V1 当时输入 → **本批 = 0 笔**（因无完整输入快照）。
- **集合 B｜OUTCOME_RECONSTRUCTABLE**：可研究交易后真实市场路径，但**不能**证明 V1 当时输入 → **53 笔**。
- **集合 C｜DATA_GAP / UNRESOLVABLE**：仅保留于总体记录，**不用于对应统计分析** → **4 笔**。
- **禁止把 B 当成 A。**

## 8. 本阶段禁止
胜率 / PF / Alpha / 最优参数 / Exit 优化 / 反事实优化 / 任何策略改进建议 —— 均**未做**。

## 9. 结论（回答五问）
1. **能真实重建**：T_signal/T_order/T_fill/T_exit；T_fill→T_exit 的真实价格路径（源A）；slippage；出场原因与实现盈亏（记录值）。
2. **不能真实重建**：V1 在 T_signal 时的**完整可见输入**；**入场时刻 spread**（未记录，仅可推导）；**commission/swap**（未记录）；仅 latest state_package 的历史上下文。
3. **可做什么分析**：集合 B 的 53 笔 → **OUTCOME 路径分析**；ENTRY 类分析**最高只能到“B 摘要级描述 + A 部分证据”，不得声称完整输入**。
4. **影响结论的缺口**：49.2h 周末缺口（11 笔）；3 处盘中缺口 + 每日日切；决策输入快照缺失；cost 缺失(commission/swap)；1 笔未平仓。
5. **下一阶段应允许**：仅 **OUTCOME_RECONSTRUCTABLE（集合 B）** 的**事后路径/成本(可重建项)**分析；ENTRY 方向归因须**限定在已保存证据**，并对“完整输入”类主张一律 DATA_GAP。**Alpha 结论仍须更后阶段且受限**。

> 引用任何结论须带本 Protocol + 对应 JSON + 源A sha256。
