# V1 全生命周期审计报告（可交外部复核）

- 生成：2026-09-17 · 目录 `research/hermes/v1_audit/` · **V1/V2/V3 零修改** · **无任何订单** · 源 = **A（live_fxtm，V1 当时保存）**
- 数据范围：**V1 首个决策 2026-09-07 → 最新 2026-09-17**（8 个交易日）
- 产物：`V1_LIFECYCLE_DATA_REGISTRY.json` · `V1_TRADE_MASTER.jsonl` · `V1_LIFECYCLE_TIMELINE.json` · `V1_PNL_SERIES.json` · `V1_DIRECTIONAL_PERIODS.json` · `V1_MARKET_REGIME.json` · `V1_LOSS_STREAK.json` · `V1_AUDIT_PHASE_D_SHA256.json` · `V1_FULL_LIFECYCLE_SHA256.json`
- 脚本：`tools/v1_audit_lifecycle.py`（seed 固定 20260917）

---

## 1. Executive Summary（白话）
V1 从 **2026-09-07** 开始运行，到 **09-17** 共产生 **321 次计划登记**、**117 次触发**（115 通过风控、2 被风控拒）、**57 笔成交、57 笔已平仓**。**累计实现盈亏 +28.22 USD**（**OBSERVABLE_NET**；真实净额因 commission/swap 未记录 = `DATA_GAP`）。
按日：**09-08 +58.10；09-09 −50.29；09-10 +45.84；09-11 +39.82；09-14 +33.70；09-15 −5.75；09-16 −41.11；09-17 −52.09**。
即：**09-08~09-14 累计 +127.17（其中 09-09 单日为负），09-15~09-17 累计 −98.95**。用户“早期不错、最近亏”的印象**在日级 P&L 上可见（PARTIALLY_SUPPORTED）**；但**样本极小（57 笔 / 8 日）**，多数结论只能到 `INSUFFICIENT_EVIDENCE`。
**关键反证**：用真实 tick 重建的**入场方向**在“近期”**并未变差**（近期 +1s 方向胜率 0.714，甚至高于整体 0.617）。因此**近期亏损不能归因于“打不到方向”**——`DIRECTIONAL deterioration = NOT_SUPPORTED`。

## 2. Data Inventory
- V1 runtime：`plan_ledger.jsonl`(321 reg/117 trig/57 fill/57 close/262 cancel)、`decisions/`(794)、`positions/`(57)、`memory/reviews/`(56)、`statistics.json`、`workflow_history.jsonl`、`state_package_latest.json`。
- **无历史 state snapshot**（仅 latest）→ 历史决策**完整输入**不可复原 = `DATA_GAP`（class E，禁用于历史证明）。
- 行情：**A = `data/live_fxtm/ticks_*.parquet`（9 文件 / 1,756,702 tick / 09-07 01:05→09-17 12:24）**；D = staging_mt5 / staging_fxtm（**未使用**）。
- class：A(当时可见行情)、B(决策记录)、C(结果)、D(外部行情)、E(无法确认当时可见——含 state_package latest)。

## 3. Trading Timeline
- 首笔成交/平仓：2026-09-08；末笔：2026-09-17。**方向结构：LONG 8 / SHORT 49**。
- 触发被风控拒：**2**；取消（多为早期测试残留 `test_artifact_cleanup`）：262。

## 4. Performance Timeline
| 指标 | 值 |
|---|---|
| 已平仓 | 57（未平仓 0，含 09-17 一笔已平） |
| 累计（OBSERVABLE_NET） | **+28.22 USD** |
| 胜率 | **0.526** (30/57) |
| Profit Factor | **1.092** |
| 平均盈 / 亏 | +9.71 / −8.50（近似，见 JSON） |
| 期望值 | +0.495 USD/笔 |
| 最大回撤 | **−130.94 USD** |
| 最大连亏 / 连盈 | **7** / 见 JSON |
| 最近连亏 | 1 |
| TRUE_NET | `DATA_GAP`（commission/swap 未记录） |

## 5. Early vs Middle vs Recent（按平仓序三分位；**保留时间序**）
- 期间定义：early=09-08~09-09、mid=09-10~09-14、recent=09-14~09-17（**三分位按笔数**，recent 与 mid 在 09-14 边界相接——已在 JSON 标注）。
- `USER_DEFINED_RECENT_PERIOD`（描述性，非失效日）：**>=09-10**（近 7 日）。

## 6. Directional Performance（源 A，方向归一化）
| 期间 | +1s (win) | +5s (win) | +30s (win) | +300s (win) | +900s (win) |
|---|---|---|---|---|---|
| early | +0.158 (.688) | +0.300 (.75) | −0.096 (.375) | −1.44 (.188) | −3.47 (.188) |
| mid | −0.010 (.471) | +0.126 (.647) | +0.020 (.471) | +0.288 (.588) | −0.026 (.471) |
| **recent** | **+0.113 (.714)** | +0.197 (.50) | +0.387 (.429) | +0.989 (.571) | +1.494 (.60) |
| 7日(>=09-10) | +0.046 (.581) | +0.158 (.581) | +0.186 (.452) | +0.605 (.581) | +0.687 (.531) |

- **短窗方向：近期并未变差**（+1s 胜率更高）。early 在长窗(300/900s)反而**方向为负**。

## 7. Entry vs Exit
- early：**方向长窗为负，但 P&L 为正** → 早期正收益更可能来自**快速退出/TP**（描述性假设，非结论）。
- recent：**方向长窗为正，但 P&L 为负** → 近期亏损更可能与**退出/管理或个别大逆行**相关。
- ⇒ **Entry Direction 与 Final Outcome 明显分离**（`ENTRY_DIRECTION_POSITIVE_BUT_FINAL_OUTCOME_NEGATIVE` 与反向都出现）。

## 8. LONG vs SHORT
- LONG n=8 / SHORT n=49（**极不平衡**）。LONG 太少 → 任何 LONG 结论 = `INSUFFICIENT_EVIDENCE`。
- SHORT 贡献绝大多数交易；SHORT 近期方向（+1s 等）与整体相近 → `SHORT deterioration = NOT_SUPPORTED`。

## 9. Market Regime（源 A）
| 期间 | spread_bp p50 | tick_rate/h | 实现波动(bp/tick) | range(USD) |
|---|---|---|---|---|
| early | 0.319 | 8649 | 0.404 | 99.5 |
| mid | 0.345 | 4828 | 0.455 | 142.3 |
| recent | 0.349 | 8622 | 0.426 | 132.9 |
- **市场环境无实质变化**（spread 微升 ~0.03bp；活跃度/波动/波幅同量级）→ `market_regime_change = NOT_SUPPORTED`。

## 10. Cost
- `OBSERVABLE_NET` = review.realized.pnl_usd（含已记录 **slippage**）。
- spread@entry：**未记录**（可由源A推导，~0.32–0.35bp）。
- commission / swap：**未记录 → DATA_GAP**（**禁默认 0**）。`TRUE_NET = DATA_GAP`。

## 11. Loss Streak
- 观测最大连亏 **7**；随机基线（winrate=0.526，seed 固定，5000 次）p50=5、p95=8；观测**百分位 93.4%** → **`WITHIN_RANDOM_RANGE`**（未超随机）。
- 最近连亏 = 1。⇒ **近期亏损串不显著异常**。

## 12. Contradictory Evidence（专门列与“最近失效”相矛盾）
1. **入场方向近期未恶化**（+1s 胜率 0.714 > 整体 0.617）。
2. **近期长窗方向为正**（+900s 均值 +1.49），**亏损更可能来自退出/管理**。
3. **连亏在随机范围内**（93.4% < 95%）。
4. **市场环境基本未变**（spread/波动/活跃同量级）。
5. **09-14 仍为盈利日**（+33.70）→ “上周起持续亏”不精确。
6. 样本 **57 笔 / 8 日** → 任何“恶化”都可能是小样本波动。

## 13. Data Gaps（无法回答的问题）
- 历史**决策完整输入**不可复原（无 state history）→ 不能解释“V1 为什么这么决策”。
- **commission/swap** 缺失 → 真实净额无法给。
- 入场时刻 **spread 未记录**（只能推导）。
- 样本极小 → 变化点、方向恶化、连亏显著性均 `INSUFFICIENT_EVIDENCE`。
- 周末 49.2h + 盘中/日切缺口 → 部分 horizon 不可算。

## 14. Final Diagnosis（状态词表）
| 层 | 状态 |
|---|---|
| 早期表现较好 | **PARTIALLY_SUPPORTED**（5/6 早期日为 +，但 09-09 为 −；样本小） |
| 最近明显恶化 | **PARTIALLY_SUPPORTED**（09-15~17 连续负；统计 `INSUFFICIENT_EVIDENCE`） |
| 入场方向恶化 | **NOT_SUPPORTED** |
| LONG 恶化 | **INSUFFICIENT_EVIDENCE**（n=8） |
| SHORT 恶化 | **NOT_SUPPORTED** |
| EXIT/管理贡献恶化 | **PARTIALLY_SUPPORTED**（近期方向正、P&L 负） |
| 市场环境变化 | **NOT_SUPPORTED** |
| 成本变化 | **NOT_SUPPORTED**（spread 微升） |
| 连续亏损异常 | **NOT_SUPPORTED**（within random） |
| **根本原因** | **UNRESOLVED**（最可能：退出/管理 + 小样本随机；**证据不足**） |
| 变化点 | **CHANGE_POINT_UNRESOLVED**（描述上“09-15 起转负”，但无可靠统计变化点） |

## 15. 问题地图（§二十）
| 调查问题 | 当前证据 | 状态 |
|---|---|---|
| 早期是否表现较好 | 09-08~09-14 多为正（09-09 除外） | PARTIALLY_SUPPORTED |
| 最近是否明显恶化 | 09-15~17 连负（−98.95） | PARTIALLY_SUPPORTED |
| 入场方向是否恶化 | 近期 +1s 胜率 0.714 ≥ 整体 | NOT_SUPPORTED |
| LONG 是否恶化 | n=8 | INSUFFICIENT_EVIDENCE |
| SHORT 是否恶化 | 与整体相近 | NOT_SUPPORTED |
| EXIT 是否贡献恶化 | 近期方向正/结果负 | PARTIALLY_SUPPORTED |
| 市场环境是否变化 | spread/波动/活跃同量级 | NOT_SUPPORTED |
| 成本是否变化 | spread 微升 0.03bp | NOT_SUPPORTED |
| 连续亏损是否异常 | 93.4 百分位 | NOT_SUPPORTED |
| 根本原因 | 无可靠归因 | UNRESOLVED |

## 16. 边界声明
- 本报告**不做交易决定**、不提参数建议；未改 V1/V2/V3；未发单。
- **不得**写成 `V1_HAS_ALPHA` / `V1_HAS_NO_ALPHA` / `V1_IS_BROKEN`。
- 用户观察若缺统计支持已直书（见 §12/§14）。
- 引用任何数字须带对应 JSON + 源A sha256。
