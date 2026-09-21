# CHATGPT-TASK-V3-HFT-COST-BRIDGE-AUDIT-001 — RESULT

TASK_ID= V3-HFT-COST-BRIDGE-AUDIT-001
STATUS= VALID
MODE= AUDIT_ONLY / READ_ONLY
STARTED_AT= 2026-09-21T13:25:00+08:00
FINISHED_AT= 2026-09-21T13:5x+08:00

LOCAL_HEAD= 6170050dcd6397f29193effc4f0baaed9036e2ab
LOCAL_BASE= 98ef9a74221427d5ef1e3eaa365cdd6d893ccbc1
REMOTE_HEAD= (see CHATGPT-TASK-V3-HFT-COST-BRIDGE-AUDIT-001.json -> staging_commit, verified == origin/main)

FILES_CREATED=
  research/hermes/trader_v3/audit/v3_cost_bridge_audit.py
  research/hermes/trader_v3/audit/v3_cost_bridge_20trades.csv
  research/hermes/trader_v3/audit/v3_cost_bridge_summary.json
  research/hermes/trader_v3/audit/v3_cost_bridge_manifest.json
  research/hermes/trader_v3/audit/_probe_broker.py
  research/hermes/trader_v3/audit/_probe_broker_out.json
FILES_CHANGED= (none — no existing file modified)
FILES_DELETED= (none)

V1_UNTOUCHED= TRUE
V2_UNTOUCHED= TRUE
V3_ALPHA_UNTOUCHED= TRUE (no alpha/model/strategy/prompt/threshold edit; calibration ledger + 20/20 raw results unmodified)
V3_DATA_UNTOUCHED= TRUE (ledger hash chain verified OK, 131 events)
BROKER_ORDER_SENT= FALSE (0 order_send; 0 order_check; read-only MT5 calls only)
CALIBRATION_AUTO_STOP= TRUE
EXPANSION= LOCKED

---

## 最终结构块

```text
V3-HFT-COST-BRIDGE-AUDIT-001

STATUS: VALID

MODEL_NET_MEAN: -0.137500 USD / round-trip   (state/V3_COST_PROFILE.json round_trip_net_pnl.mean)
BROKER_NET_MEAN: -0.372000 USD / round-trip  (balance 5000.00 -> 4992.56 over 20 RT)
MEAN_DIFFERENCE: +0.234500 USD / round-trip  (MODEL_NET - BROKER_NET, like-for-like)

EXPLAINED_DIFFERENCE: +0.234500 USD / round-trip (100.0%)
UNEXPLAINED_DIFFERENCE: -5.55e-17 USD / round-trip (floating-point residual, i.e. 0)
EXPLAINED_RATIO: 1.000000

SPREAD_EFFECT: -0.180000   (model charges the spread again although it is already inside the fills)
ENTRY_SLIPPAGE_EFFECT: -0.007500   (double count + abs() on already-realised fill difference)
EXIT_SLIPPAGE_EFFECT: -0.018000   (double count + abs() flips a +0.30 favourable fill into a -0.30 charge)
COMMISSION_EFFECT: +0.440000   (SIGN INVERTED: code adds +0.22 instead of charging -0.22; error = 2x|comm|)
SWAP_EFFECT: 0.000000   (broker swap = 0.0 on all 40 deals — broker fact)
CONVERSION_EFFECT: 0.000000   (price x contract_size 100 x volume 0.01 = x1.0 oz; 20/20 model gross == broker deal profit)
ROUNDING_EFFECT: 0.000000   (float residual < 1e-15)
OTHER_EFFECT: 0.000000   (no unmodelled execution cost found)

FOK_EFFECT: 0.000000 USD / round-trip (all 40 orders fully filled, no partial, no reject; deviation already inside fills)
TIME_ALIGNMENT_STATUS: PASS_WITH_DEFECT (server UTC+3 offset constant 10800 s; hold_actual_ms granularity defect - see DATA_GAPS)
UNIT_CONVERSION_STATUS: PASS

DATA_GAPS:
  - no independent tick/quote source covers the window (copy_ticks_range=0; local archive has no 2026-09-20 file)
  - ledger stores no exit-time bid/ask (exit spread reconstructed, 5/20 from bps, 15/20 assumed = entry spread)
  - registry entry_fill_price = null and cost-profile entry_slippage = null (key-name mismatch in code)
  - hold_actual_ms quantised to 1000 ms by integer-second tick stamps
  - tick.age / STALE_TICK_AT_REQUEST computed but never persisted
  - broker symbol_info trade_tick_value (0.1) does not reconcile with contract_size (100.0) — unused by bridge
  - calibration_pilot.py dead `gross` variable multiplies by an unset s["volume"] (latent, no effect this run)

EXPANSION_ALLOWED: NO

V1_UNTOUCHED: TRUE
V2_UNTOUCHED: TRUE
V3_ALPHA_UNTOUCHED: TRUE
ORDER_SENT: FALSE
LIVE: FALSE

GIT_COMMIT: 6170050dcd6397f29193effc4f0baaed9036e2ab (C:\AIQuant, path-limited, 6 audit files)
REMOTE_SYNC: staging repo pushed, local HEAD == origin/main (see JSON staging_commit)
```

---

## 1. 核心问题：这两个数字的差从哪来

任务头给出的 "-0.5095" 与 "+0.1375" 存在**符号口径混用**：

- `state/V3_COST_PROFILE.json` 同时含两个字段：
  - `round_trip_net_pnl.mean = -0.1375`  → 这是**净盈亏**（NET P&L）
  - `NET_ROUND_TRIP_COST.mean = +0.1375` → 这只是上面那个数的**取负**，即**成本**（COST）
- 任务头把 **成本 (+0.1375)** 与 **broker 净盈亏 (-0.372)** 相减，得到 `-0.372 - 0.1375 = -0.5095`（口径不同类）。
- **同口径比较**：MODEL_NET `-0.1375` vs BROKER_NET `-0.372` → 差 **+0.2345 USD/RT**（模型比现实“乐观”0.2345）。
- 无论用哪种口径，差都不是执行/行情造成的，而是**计账公式错误**造成的。

### 1.1 根因（逐项量化，USD / round-trip）

bridge 恒等式（每笔）：`MODEL_NET + Σ(修正项) = BROKER_NET`

| # | 项 | 值 (USD/RT) | 性质 |
|---|---|---|---|
| 1 | spread | **-0.1800** | 重复计提：成交价已含买卖价差（买@ask/卖@bid），代码又减一次 spread |
| 2 | entry slippage | **-0.0075** | 重复计提 + `abs()` 把已实现的价差当成本 |
| 3 | exit slippage | **-0.0180** | 重复计提 + `abs()` 把 V3CAL-00 的 +0.30 **有利**成交记成 -0.30 成本 |
| 4 | commission | **+0.4400** | **符号反转**：MT5 返回 commission=-0.22/RT（成本），代码写 `net = ... - comm`，等于 +0.22，只记了一半且方向错 |
| 5 | swap | 0.0000 | broker 40 笔 deal 全为 0.0 |
| 6 | price-P&L conversion | 0.0000 | 见 §3 |
| 7 | position size | 0.0000 | 固定 0.01 手，前后一致 |
| 8/9 | 理论/实际成交价定义 | 0.0000 | request=可成交边(ask/bid)；fill=r.price == broker deal.price 20/20 |
| 10 | FOK | 0.0000 | 见 §4 |
| 11 | timestamp-quote 对齐 | 0.0000（状态 PASS_WITH_DEFECT） | 见 §5 |
| 12 | holding-duration 对齐 | 0.0000 | ledger ns 时间戳给可用持仓时长；registry 的 hold_actual_ms 不可用 |
| 13 | rounding-contract | 0.0000 | 残差 < 1e-15 |
| 14 | 其它未建模成本 | 0.0000 | 未发现 |
| 15 | **代码/账务口径错误** | **（即 1-4 项，共 +0.2345）** | 根因类别 |

**Σ = -0.18 - 0.0075 - 0.018 + 0.44 = +0.2345 = MEAN_DIFFERENCE**，残差 ≈ 0。

### 1.2 每笔桥接要点（节选；完整 20/20 见 CSV）

- 残差列 `unexplained_difference` 20/20 均 ≤ 5.6e-17（浮点）。
- 典型 V3CAL-00 (LONG)：gross +0.12；model_net -0.16（含 spread 0.18、|exit_slip| 0.30 的重复计提、comm +0.22）；broker_net -0.10；差 +0.06 → 由 +0.18 +0.02 +0.30 -0.44 修正回 broker。
- 典型 V3CAL-12 (LONG)：entry 滑点 0.08（唯一较大真实滑点）；model_net -0.12 vs broker_net -0.30。
- 20/20 `broker_net` 之和 = **-7.44** = 账户余额差；broker profit 合计 **-3.04**、commission **-4.40**、swap **0.00**。

## 2. 核心公式审计（§六）

- **gross pnl**：LONG `(exit_fill - entry_fill)`，SHORT `(entry_fill - exit_fill)`，单位 price = USD（见 §3）。
- **spread cost**：代码用 entry 时刻 `ask-bid` 并再次从已含价差的 gross 中扣除 → **错误（重复计提）**。可成交价口径（long 买 ask / short 卖 bid）本身**正确**。
- **slippage**：`expected executable price` = 请求前最后一次 `symbol_info_tick()` 的可成交边；`actual` = `order_send().price`。二者之差已体现在成交价中，**不应再作为成本重复扣减**；且 `abs()` 使负滑点（有利）被当成成本。
- **commission**：MT5 每笔 deal 返回 **-0.11**，两笔共 **-0.22/RT**；代码 `- comm` 造成**符号反转**。且 `_cost_profile` 用 `commission_source = "MT5 history_deals_get (UNKNOWN if absent)"`，但数值实际存在（**非 DATA_GAP**）。
- **swap**：broker 事实 = 0.0（40/40 deal），窗口仅 31 秒、无隔夜/滚存 → **§五 swap 未发生，broker fact 支撑成立**。

## 3. 单位审计（§七）

XAUUSD spec（broker 实读）：`digits 2, point 0.01, trade_tick_size 0.01, trade_contract_size 100.0, volume_min 0.01, currency_profit USD`。
`profit = price_move × contract_size(100) × volume(0.01) = price_move × 1.0 oz` → price_move 数值 == USD。
**20/20 broker deal.profit 与 (exit-entry)×1.0 完全一致**（合计 -3.04）→ **未假设 1 lot = 1 oz；是按 contract_size=100 × volume=0.01 得出的 1.0 oz 有效口径**。
DATA_GAP：broker 上报的 `trade_tick_value = 0.1` 与 contract_size 100 不自洽（按定义应为 1.0/lot/tick），本桥接**未使用**该字段，以 deal.profit 为准。

## 4. FOK 审计（§八）

- symbol `filling_mode = 1`（仅 FOK）；实际 40 笔 order `type_filling = 0`（FOK），`state = 4`（全部成交）。
- 无部分成交、无拒单；request 的 `deviation = 20` 点（0.20）从未被触发。
- fill 相对 request 的最大偏离：**+0.30（有利，V3CAL-00 出场）/ -0.02（不利）**。
- 该偏离**已包含在成交价内**，因此对 bridge 的独立贡献 = **0.00 USD/RT**。
- 该偏离主要由**订单 RTT ~270 ms 内的行情漂移**导致（窗口正好在**周日周开 23:05Z** 附近，波动大），非 FOK 机制本身。

## 5. 时间对齐审计（§九）

- ledger 时间戳 = UTC（与 pilot started/finished 一致）；**broker deal time = UTC + 10800 s（FXTM 服务器 UTC+3）**，40/40 完全恒等 → 无时区错配。
- **无 look-ahead**：每笔 request 时间戳先于其 fill；request 报价取自 send 前的 tick。
- **缺陷**：`registry.hold_actual_ms` 由 tick 的**整秒**时间戳相减得到，精度 1000 ms，出现 0/2000/3000 等噪声 → 不可用作持仓时长；可用持仓时长取自 ledger ns 时间戳（100–2000 ms 目标）。
- **DATA_GAP**：`tick.age`/`STALE_TICK_AT_REQUEST` 在代码里算了但**没写进 ledger**，故退出偏离无法在“报价陈旧 / 行情漂移 / 执行滑点”之间拆分；`ledger` 也未持久化退出时刻 bid/ask。

## 6. 20 笔汇总（§十）

见 `v3_cost_bridge_20trades.csv`（20 行 × 完整字段，含每笔 bridge 修正项与残差）。
- explained_ratio = **1.000000**（分母 = +0.2345，非近 0）。
- 真实结构性成本（实测）：**spread 0.18 + commission 0.22 = 0.40 USD/RT ≈ 0.914 bp**；
  而成本模型给的口径 = **0.1375 USD/RT ≈ 0.314 bp** → **成本被低估 ≈ 0.26 USD / 0.60 bp**。

## 7. §十二 门槛

- MODEL 与 BROKER 已逐项解释、残差≈0 才可建议扩张；但**本轮为纯记账错误，并非策略/执行 edge 证据**。
- 真实成本 0.40 USD/RT（0.914 bp）→ **EXPANSION = LOCKED**。
- 本次 calibration 方向序列非 alpha（校准用交替 LONG/SHORT），且实测 gross 均值 ≈ -0.152/Rt（≈ -spread 的机械结果 + 微小漂移）→ **ALPHA_NOT_PROVEN_AFTER_COST = TRUE**。
- **未修改任何成本模型“修回正收益”**；只报告口径与数值。

## 8. §十四 可复现性

脚本 `v3_cost_bridge_audit.py` 同输入同输出。
- ledger_sha256 = fc8fd01e5ac487dd63558241d67584d453ccd21d8aa3a91d8bb804304e06750c
- registry_sha256 = 7ad9596c4cab88bb95e0650daabbb169b53c3d3b796b07ea8bacb7c6366f4f25
- cost_profile_sha256 = 26b3f8d80a7ad4754d403ee2c03df1898cb2fb2bf19a04edc6d8fc515bd0a728
- broker_data_sha256 = bbd36b4680c4ca36737192f5a5a4ac127e6fa220be6816322c00efcfc7aeaaa4 (40 deals + 40 orders)
- tick_data_hash = **null (DATA_GAP)**
- input_hash = 0e58f297787790e9970c5d2d99355d6bbebdca25bb34405948d329ac05c6befd
- result_hash = 4d8c72a54ee02b10756845089e328207e61bccbffb61453b9297acaa0f99c9fe
- git_commit = 7351955e1b8e029eda84c20610862d03e1050492（冻结证据那次提交）
- BASE_COMMIT = 98ef9a74221427d5ef1e3eaa365cdd6d893ccbc1

## 9. HALT / 异常

**无 HALT。** 唯一异常为“§十二 扩张门槛不可通过”，按规则冻结 `EXPANSION = LOCKED`，未自动修复交易逻辑。

---

REPORT_COMMIT= (staging commit; 见 JSON staging_commit)
