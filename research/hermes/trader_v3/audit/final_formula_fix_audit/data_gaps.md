# DATA_GAP 完整披露 — V3-HFT-CALIBRATION-FORMULA-FIX-001/002

> 原则：**无法证明为真实 Observed 的字段，一律标注为 DERIVED / NOT_RECOVERABLE，绝不伪装成 Observed。**
> 每项含：`DATA_GAP` / `DESCRIPTION` / `IMPACT` / `CAN_RECONSTRUCT` / `USED_IN_CORRECTED_PNL`。

---

## DG-1 · TICK_VALUE_INCONSISTENT

```text
DATA_GAP            : TICK_VALUE_INCONSISTENT
DESCRIPTION         : Broker symbol spec 自相矛盾：symbol_info("XAUUSD").trade_tick_value = 0.1，
                      而 trade_contract_size = 100.0、trade_tick_size = 0.01。
                      按 tick_size × contract_size 应为 1.0（1 手 100oz，0.01 价格变动 = 1 USD），
                      报出的 0.1 与之相差 10×。
                      → 这不是"数据缺失"，而是"Broker 报出字段之间不自洽"。
IMPACT              : 若用 tick_value 计算 P&L 会产生 10× 误差。
                      本次 corrected 公式**不使用 tick_value**（改用 contract_size × volume），
                      因此 corrected P&L 不受影响。
CAN_RECONSTRUCT     : 否（冻结数据无法判定谁对；需 broker 侧确认或后续样本交叉验证）
USED_IN_CORRECTED_PNL : 否
```

## DG-2 · EXIT_SIDE_QUOTE_NOT_FULLY_RECOVERABLE

```text
DATA_GAP            : EXIT_SIDE_QUOTE_NOT_FULLY_RECOVERABLE
DESCRIPTION         : 冻结的历史 execution ledger 只落了 entry 侧 bid/ask；
                      exit 侧 bid/ask 未落盘。20/20 笔的 exit_quote_source 均为
                      AUDIT_CSV_SUPPLEMENTARY（即借用上一版审计 CSV 的派生值）。
IMPACT              : exit 侧 spread / friction 的**分解**不完整（仅影响诊断性分解）；
                      corrected P&L 只依赖 **exit_fill_price**（实际成交价，已落盘），故不受影响。
CAN_RECONSTRUCT     : 否（历史 20 笔不可回溯）；**仅对后续新 run 生效**（代码已补落盘 exit_bid/exit_ask）
USED_IN_CORRECTED_PNL : 否
```

## DG-3 · NO_INDEPENDENT_TICK_ARCHIVE_FOR_WINDOW

```text
DATA_GAP            : NO_INDEPENDENT_TICK_ARCHIVE_FOR_WINDOW
DESCRIPTION         : 该窗口无独立 tick/quote 归档可比对：
                      MT5 copy_ticks_range 返回 0，本地 tick 归档亦无该日文件。
                      因此 observed_spread 唯一来源是 pilot 在**入场瞬间**捕获的 quote。
IMPACT              : 无法用第二源独立复核点差/滑点；spread 仅能标注为"入场时实测（单源）"。
CAN_RECONSTRUCT     : 否（窗口已过）
USED_IN_CORRECTED_PNL : 否
```

## DG-4 · HOLD_ACTUAL_MS_NOT_PERSISTED_BY_OLD_PILOT

```text
DATA_GAP            : HOLD_ACTUAL_MS_NOT_PERSISTED_BY_OLD_PILOT
DESCRIPTION         : 旧 pilot 的 hold_actual_ms 由整秒 tick 时间戳计算，精度被量化到 1000ms
                      （无法反映 100/250/500ms 的持仓目标）。
                      本材料包中的 hold_actual_ms 用 ledger 的 ENTRY_FILL/EXIT_FILL **成交时间戳**
                      重新推导（毫秒级），属 DERIVED 而非原始持久化字段。
IMPACT              : 不影响 P&L；影响"持仓时长"类分析的精度。
CAN_RECONSTRUCT     : 部分（可由 ledger 成交时间戳推导至 ms 级；原始 tick 级精度不可恢复）
USED_IN_CORRECTED_PNL : 否
```

## DG-5 · ENTRY_SIDE_SPREAD_ONLY

```text
DATA_GAP            : ENTRY_SIDE_SPREAD_ONLY
DESCRIPTION         : CSV 的 observed_spread 为**入场侧**实测点差（entry quote ask-bid）。
                      exit 侧 spread 为派生值（部分由 bps 反推，见 comparison CSV 的
                      exit_spread_derived_from_bps）。
IMPACT              : 成本分解的 exit 侧部分为估计值，不能视作双向完全实测。
CAN_RECONSTRUCT     : 否
USED_IN_CORRECTED_PNL : 否
```

## DG-6 · REGISTRY_ENTRY_FILL_PRICE_NULL_HISTORICAL

```text
DATA_GAP            : REGISTRY_ENTRY_FILL_PRICE_NULL_HISTORICAL
DESCRIPTION         : 冻结期的 data/calibration/registry.jsonl 中 entry_fill_price 为 null
                      （字段名与写入端不匹配的历史缺陷）。本材料包的价格取自 ledger 的
                      ENTRY_FILL/EXIT_FILL 事件（已落盘），未使用 registry 的该字段。
IMPACT              : 历史 registry 不可作为成交价来源；已被 ledger 替代。
CAN_RECONSTRUCT     : 是（ledger ENTRY_FILL/EXIT_FILL 提供真实成交价）
USED_IN_CORRECTED_PNL : 否（改用 ledger fill price）
```

---

## 汇总表

| ID | DATA_GAP | CAN_RECONSTRUCT | USED_IN_CORRECTED_PNL | 影响 corrected P&L |
|---|---|---|---|---|
| DG-1 | TICK_VALUE_INCONSISTENT | 否 | 否 | 无（不用 tick_value） |
| DG-2 | EXIT_SIDE_QUOTE_NOT_FULLY_RECOVERABLE | 否（仅新 run） | 否 | 无（用 exit_fill_price） |
| DG-3 | NO_INDEPENDENT_TICK_ARCHIVE_FOR_WINDOW | 否 | 否 | 无 |
| DG-4 | HOLD_ACTUAL_MS_NOT_PERSISTED_BY_OLD_PILOT | 部分 | 否 | 无 |
| DG-5 | ENTRY_SIDE_SPREAD_ONLY | 否 | 否 | 无 |
| DG-6 | REGISTRY_ENTRY_FILL_PRICE_NULL_HISTORICAL | 是 | 否 | 无 |

## 与 corrected P&L 的关系（重要）

corrected_net_pnl 的输入**只有**：`entry_fill_price`、`exit_fill_price`、`volume`、
`contract_size`、`commission`、`swap`。上述 6 项 DATA_GAP **均不进入该公式**，
因此 corrected 结果的可信度**不依赖**这些缺口；它们影响的是"成本分解/诊断"与"未来 run 的完备性"。

## 诚实性声明

- 逐笔 CSV 的 `evidence_status` 列对每条记录标注了 `OBSERVED / DERIVED / NOT_RECOVERABLE` 来源。
- 未将任何 DERIVED 或 NOT_RECOVERABLE 字段标记为 Observed。
- 未删除任何失败/异常/DATA_GAP 记录（20/20 原样保留）。
