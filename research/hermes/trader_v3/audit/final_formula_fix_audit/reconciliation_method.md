# Reconciliation Method — 如何证明 corrected P&L 不是"自证循环"

本文件说明 **corrected net P&L 的独立计算路径**，以及与 **Broker 事实**的比较方式。

## 1. 两个完全独立的输入源

| 侧 | 来源 | 性质 |
|---|---|---|
| **A. corrected（计算侧）** | 成交价 + 手数 + 合约规格 + commission + swap | 用公式**独立算出** |
| **B. broker（事实侧）** | MT5 `history_deals_get` 导出的 40 笔 deal（`broker_facts_20trades.json`） | 券商**不可变事实** |

两侧**没有任何数据拷贝关系**：A 不读取 B 的 `profit`/`net`；B 不参与 A 的公式。

## 2. corrected 公式（计算侧，公式版本 `v3-calibration-netpnl-2`）

```text
gross_pnl_usd = (exit_fill_price - entry_fill_price) * direction_sign * contract_size * volume
                direction_sign = +1 (LONG) / -1 (SHORT)

corrected_net_pnl = gross_pnl_usd + commission + swap
```

- `entry_fill_price` / `exit_fill_price`：来自 execution ledger 的 ENTRY_FILL / EXIT_FILL（实际成交价）
- `contract_size` = 100.0（`symbol_info("XAUUSD").trade_contract_size`，实测）
- `volume` = 0.01（固定）
- `commission`：MT5 deal 的 commission 字段（负值 = 成本，**不反号**）
- `swap`：MT5 deal 的 swap 字段

**关键点**：spread 与 slippage **不单独扣减**——它们已经体现在实际成交价里（`entry_fill` 是买在 ask、卖在 bid 的实际价）。旧公式的错就在于又扣了一遍，并叠加了 `abs()` 符号错误与 commission 反号。

## 3. broker（事实侧，与上面无关）

```text
broker_net_pnl(per round-trip) = Σ deal.profit + Σ deal.commission + Σ deal.swap
                                  （该 position 的 entry deal + exit deal）
broker_total = -7.44 USD        broker_mean = -0.372 USD/RT
```

`broker_facts_20trades.json` 保留原始字段：`ticket / order / position_id / symbol / magic / volume / price / time / profit / commission / swap`。

## 4. 比较（不是复制）

```text
reconciliation_error(per trade) = corrected_net_pnl - broker_net_pnl
matched_count = |error| < 1e-9 的笔数
```

结果：**matched_count = 20 / unmatched_count = 0**，
`total_error = 3.7e-14 USD`、`max_abs_residual = 8.0e-13 USD`（浮点级）。

## 5. 为什么这排除了自证循环

1. corrected 只用 fill price / volume / spec / commission / swap —— 全是**原始观测量**。
2. broker 侧只读 deal 导出 —— 券商账务事实。
3. 若 corrected 是"抄" broker，则二者的 **per-trade 差值**不会呈现出随价格方向/手数/规格变化的浮点特征；实测残差集中在 1e-13 量级（纯浮点），且 20/20 逐笔成立。
4. 复核者可用 `v3_formula_fix_recompute.py` 在 `broker_facts_20trades.json` + ledger 上**离线复算**同一结果（见 `test_results.md` 的 Test H）。

## 6. 已知限制（见 DATA_GAP）

- 历史 20 笔的 **exit 侧 bid/ask 未落盘** → friction 分解借用上一版审计 CSV，逐行标注 `AUDIT_CSV_SUPPLEMENTARY`。
- `observed_spread` 为**入场时实测**（entry quote）；exit 侧 spread 为派生值，已标注。
- `tick_value(0.1)` 与 `contract_size(100)` 不自洽 → `DATA_GAP_TICK_VALUE_INCONSISTENT`（不影响本公式：本公式用 contract_size × volume，不用 tick_value）。
