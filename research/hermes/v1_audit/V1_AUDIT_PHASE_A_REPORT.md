# V1 审计 · PHASE A — 数据盘点报告

- 生成：2026-09-17 · 目录：`C:\AIQuant\research\hermes\v1_audit\`
- 范围：**仅 PHASE A（数据盘点）**，不做任何分析；**零修改 V1/V2/V3**，无任何订单。
- 输入产物：`V1_AUDIT_DATA_REGISTRY.json`（每个源含 path/type/time_range/row_count/sha256/source/schema/timezone/timestamp_resolution/completeness/whether_used/reason_if_excluded + classification）
- 代码 SHA256：`tools/v1_audit_phaseA.py`（见 registry `code_sha256` 与提交）

## 0. 合规声明
- V1 代码/配置/账本**未改动**；V2/V3 未动；未发任何订单（真实/Demo/Paper）。
- 本阶段只读扫描 + 计算哈希 + 登记。

## 1. V1 数据源清单（分类 FROZEN / HISTORICAL / DUPLICATE / TRANSITIONAL / RUNTIME）
| 类别 | 源 | 关键量 |
|---|---|---|
| 交易账本 (RUNTIME) | `run_state/plan_ledger.jsonl` | **811 行**（registered/filled/cancelled），sha `d8898c80…` |
| 决策 (RUNTIME) | `run_state/decisions/*.json` | **794 文件**（2026-09-07T11:46Z → 2026-09-17T12:17Z） |
| 持仓 (RUNTIME) | `run_state/positions/POS-*.json` | **57 文件**（→ POS-20260917T1047Z） |
| 复盘 (HISTORICAL) | `memory/reviews/RV-*.json` | **56 文件** |
| 统计/摘要 (RUNTIME) | `run_state/statistics.json`(41KB) · `trader_summary.txt`(245KB) · `workflow_history.jsonl` · `workflow_latest.json` · `state_package_latest.json`(仅 latest 快照) | — |
| 契约 (FROZEN) | `contracts/*.yaml`（DECISION/MEMORY/REVIEW/TRADE_PLAN/TRIGGER） | 5 |
| 代码 (RUNTIME) | `engine.py/trader_core.py/position.py/ledger.py/review.py/…` | 15 文件 sha256 已记 |
| 文档 (HISTORICAL) | `00_TRADER_PROTOCOL.md` · `DESIGN_V11.md` · `AUDIT_REPORT_20260907.md` · `V12_FINAL_REPORT.md` · `E2E_REPLAY_20260907T1247.md` | — |
| 契约/缓存 (**EXCLUDED**) | `run_state/bars_cache.json` · `candle_latest.json` · `run_state/tmp/*` | 缓存非权威 |

- 重复组（identical sha256）：**0**（decisions/positions/reviews/contracts 内均无重复）。
- 版本/历史区分：`AUDIT_REPORT_20260907.md`、`V12_FINAL_REPORT.md`、`E2E_REPLAY_*` 标 **HISTORICAL**；`state_package_latest.json` 仅最新快照（**无逐笔历史**，PHASE C 需确认是否够用）。

## 2. 真实行情数据（PHASE B 用）
| 源 | 路径 | 内容 |
|---|---|---|
| **V1 本地 tick** | `C:\AIQuant\data\live_fxtm\` | `ticks_20260907..20260916.parquet`（8 日）+ `quote_latest.json` + `collect_runs.log`；**覆盖 V1 交易期 09-07→09-16** |
| MT5 staging | `data\staging_mt5\` | XAUUSD_M1/M5/H1_server.parquet |
| FXTM staging | `data\staging_fxtm\` | 27 文件 63MB |
| **V1 主 MT5 终端** | `C:\Program Files\ForexTime (FXTM) MT5\` | 579 文件 / 310MB；terminal64.exe sha 已记（**只读**；PHASE B 决定是否用于行情恢复） |

## 3. 配置 / 版本（不写敏感值）
- `.env.mt5_demo` 存在；键：见 registry `v1_config.env_keys`（值 **redacted**）。
- V1 magic 约定 = **90002**（据 `fxtm_demo_adapter` 注释，PHASE C 需在代码中复核取号）。
- 策略/代码版本：以 `code_sha256`（15 文件）为**唯一身份**（叙述/时间不作身份）。

## 4. 缺口（PHASE B/C 需回答，当前标 DATA_GAP/待核）
1. **逐笔 tick 覆盖 vs 交易时刻**：`live_fxtm` 自 09-07 起，是否覆盖全部交易时刻（尤其 09-11→09-13 空档）→ PHASE B 核对。
2. **T_signal/T_order/T_fill/T_exit** 的精确可用性 → PHASE C 从 `plan_ledger`+`decisions`+`positions` 复原并冻结信息边界。
3. **真实成本**（spread/slippage/commission/swap）逐笔 —— 待 PHASE B/C 确认，**不得假设为 0**。
4. **历史逐笔上下文**：`state_package` 仅 latest → 交易时刻的市场上下文可能只能从 `decisions/*.json` 重建，**可能 DATA_GAP**。

## 5. PHASE A 结论
- **V1 数据足以进入 PHASE B**：账本(811)/决策(794)/持仓(57)/复盘(56) 齐备且带 sha256；**V1 真实 tick 覆盖其交易期**（09-07→09-16）。
- 无数据补造；所有缺口显式登记。
- 未发现需要区分而未区分的多版本混用（重复组=0）。

## 6. 下一步（PHASE B）
1. 核对 `live_fxtm` tick 对 V1 交易时刻的**逐笔覆盖率**（缺口报告，不插值）。
2. 确认 V1 主 MT5 终端是否能提供同环境可验证行情（只读）；如用替代源，单列来源与时间差。
3. 产出 `V1_AUDIT_MARKET_*`（覆盖率/缺口/来源登记），再进 PHASE C（信息边界冻结）。

> 本阶段不进入 PHASE C 之前，**不做任何入场/退出 Alpha 分析**。
