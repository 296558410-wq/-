# V1 审计 · PHASE B — 时间对齐 + 行情覆盖审计（只读）

- 生成：2026-09-17 · 目录 `C:\AIQuant\research\hermes\v1_audit\` · **零修改 V1/V2/V3**，**无任何订单**，不计算 Alpha。
- 产物：`V1_TRADE_REPLAY.jsonl`（逐笔时间对齐+覆盖）· `V1_COVERAGE_MATRIX.csv`（覆盖矩阵）· `V1_TICK_QUALITY.json` · `V1_AUDIT_PHASE_B_SUMMARY.json`
- 脚本：`tools/v1_audit_phaseB.py`（sha 见提交）

## 1. 数据来源身份（严格区分，不得混称）
| 类 | 来源 | 本阶段使用 |
|---|---|---|
| **A. V1 当时实际收到/保存的行情** | `C:\AIQuant\data\live_fxtm\ticks_*.parquet`（V1 collector 当时落盘） | ✅ **是（唯一行情源）** |
| B. V1 主 MT5 终端**后来**可读历史 | `C:\Program Files\ForexTime (FXTM) MT5\` | ❌ 未使用 |
| C. 其他替代源 | `data\staging_mt5`、`data\staging_fxtm` | ❌ 未使用 |

> 本阶段所有逐笔对齐与覆盖**只用 A**；B/C 未参与。**GAP_WEEKEND 等结论属 A 源事实**。

## 2. V1 交易总体
- **真实成交笔数 = 57**（`plan_ledger` filled=57 / closed=56；1 笔仍 OPEN）
- 每笔含：trade_id(=position_id) / plan_id / direction / T_signal / T_order(未单列→见下) / T_fill / T_exit / 成交价 / 出场价 / close_reason / realized_usd

## 3. 时间戳对齐结果（T_signal / T_fill / T_exit）
- `T_signal` = `plan_ledger.registered.utc_ts`（无 utc_ts 的旧登记行回退到 plan_id 解析，已在记录中标注 `signal_src`）。
- `T_order` **未单独持久化** → 目前以 `T_fill` 近似，**标记 PARTIAL/待补**（PHASE C 将从 positions/*.json 的 ENTER/FILL 事件补齐）。
- 对齐方式：对每个时间戳取**最近 tick**（`align_signal/align_fill/align_exit` 记录 tick_ms/delta_ms/side）。
- **未来信息风险**：`align_signal.side=after` 且 delta 大者标 `future_info_risk_at_signal`（本批未触发大 delta 情形；小 delta 属取样栅格）。

## 4. 真实行情覆盖率（源 A）
- tick 文件 **9** / 行数 **1,756,702**；覆盖 **09-07 01:05 → 09-17 12:24 UTC**（V1 交易期）。
- 质量（`V1_TICK_QUALITY.json`）：**dup_ts=0 · 非单调=0 · ask<bid=0 · 零价=0**；活跃 interval p50 ≈ **265~274ms**；单位=**UTC 毫秒**(`time_msc`/`ts_utc`)。
- **逐笔覆盖状态**：**PASS 45 · PARTIAL 9 · DATA_GAP 2 · UNRESOLVABLE 1**（合计 57）。
  - `coverage_before_signal` / `coverage_signal_to_fill` / `coverage_fill_to_exit` 已逐笔记录（段内 tick 数 + 最大间隔）。

## 5. 数据缺口（不插值、不补齐、不删除受影响交易）
| 缺口 | 时段(UTC) | 时长 | 影响 |
|---|---|---|---|
| **周末缺口** | 09-11 23:54 → 09-14 01:05 | **49.2 h** | **11 笔**受影响；`POS-20260913T2217Z` → **DATA_GAP** |
| 每日结算/日切 | 23:54 → 01:05（每日） | ~70 min | 多笔入场窗 ticks=0 → **PARTIAL** |
| 09-08 盘中 | 05:46 → 07:31 | 1.75 h | `POS-20260908T063856` PARTIAL |
| 09-15 盘中 | 05:54 → 09:01 | 3.1 h | `POS-20260915T0632Z` → **DATA_GAP** |
| 09-17 盘中 | 10:24 → 11:00 | 36 min | `POS-20260917T1047Z` 覆盖不全 |

- **特别检查 09-11→09-13**：该窗内有 233,817 tick，但其中是 **49.2h 周末空档**（09-11 23:54→09-14 01:05）→ **VERDICT = GAP_WEEKEND**（不是 NO_GAP）。受影响交易 **11 笔**，其中 1 笔落于缺口内判 **DATA_GAP**。**未插值、未用后续行情补齐、未删除任何交易。**

## 6. 逐笔覆盖矩阵
- `V1_COVERAGE_MATRIX.csv` 列：`trade_id | signal | order | fill | exit | tick_before | tick_at/after | max_delta_ms | status`
- status 取值域：`PASS / PARTIAL / DATA_GAP / UNRESOLVABLE`（无其它值）。

## 7. 决策输入可见性（关键 DATA_GAP）
- `run_state/decisions/*.json` **只保存 `state_summary`（文本摘要）**，**未保存决策时刻的完整可见输入快照**；
- `state_package` **仅最新**（`state_package_latest.json`），**无逐笔历史**。
- ⇒ **历史交易时刻的“实际可见输入”无法完整复原 → 标记 `DATA_GAP`**；**严禁用 latest state 解释历史交易**（PHASE C 的信息边界将据此设限：只能使用 `ts ≤ T_signal` 且**确实保存了的**字段）。

## 8. 是否满足进入 PHASE C 的条件
- **满足（有条件）**：源 A 逐笔行情覆盖 V1 交易期，57 笔均有 T_signal/T_fill（T_exit 56/57），覆盖矩阵与缺口已登记。
- **PHASE C 必须带着以下约束进入**：
  1. **T_order 缺失**（用 T_fill 近似，需从 positions 事件补齐或标 PARTIAL）；
  2. **决策输入快照缺失** → 入场分析的信息边界只能建立在“已保存字段”上，其余 **DATA_GAP**；
  3. **11 笔受周末缺口影响 / 2 笔 DATA_GAP / 1 笔 UNRESOLVABLE（未平仓）** → 统计与跨期须显式处理，**不得丢弃**。
- **本阶段结束，暂停，不进入 Alpha 分析**（依 §9）。

> 数据来源身份、缺口、对齐全部可复现（脚本 + 输入 sha256）。引用任何数字须带 `V1_AUDIT_PHASE_B_SUMMARY.json` + 源 A 路径。
