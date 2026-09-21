# V3-HFT-CALIBRATION-FORMULA-FIX-001 — 校准账务公式修复（V3-only）

- **Task**: V3-HFT-CALIBRATION-FORMULA-FIX-001
- **Authority**: 用户 GO（V3-only 最小修复；用户发现的是**会计公式问题**，不是市场判断错误）
- **Date**: 2026-09-21（修复/测试/离线重算 15:13–15:17 GMT+8；本报告为任务书正式归档版）
- **Repo commit**: `4f6bd54c4a4963fb2885921fee1d7adb510c940a`（C:\AIQuant，path-limited）
- **Mode**: V3-only 修复 + 只读验证；**未重发任何订单**（全程 `order_send` = 0）
- **STATUS**: `PASS`
- **Next**: `WAIT_FOR_CHATGPT_AUDIT`

---

## 十五、最终报告结构

### A. bugs_fixed
| # | BUG | 位置 | 修法 |
|---|---|---|---|
| 1 | **spread 重复计提** —— 成交价已含 bid/ask，账务又扣一次 spread | `foundation/calibration_pilot.py::_round_trip` → net_pnl | 不再扣；spread 仅作诊断量上报（标注 `EMBEDDED_IN_FILL_PRICE_NOT_DEDUCTED`） |
| 2 | **entry/exit slippage 重复计提** —— 滑点已在成交价内 | 同上 | 不再扣；仅诊断上报 |
| 3 | **`abs()` 把有利滑点成本化** | 同上 | 删除 `abs()`，保留符号（有利即有利） |
| 4 | **MT5 commission 符号反转** —— `commission<0` 为成本，代码 `-comm` 反号（误差 2×\|comm\|） | 同上 | 直接取 `commission`，不反号 |
| 5 | **broker realized 与 execution cost 混淆** —— 未分离三者 | 同上 | 分离为：broker realized P&L / execution cost（诊断）/ model theoretical P&L |
| 6 | **单位未以 broker symbol spec 为准** | `_round_trip` | 统一 `signed(exit_fill−entry_fill) × contract_size × volume + commission + swap`；symbol spec 现随样本落盘 |

新账务为独立纯函数模块 `foundation/pnl_accounting.py`（公式版本 `v3-calibration-netpnl-2`），并在账务对平失败时 **fail-closed → HALT**。

### B. files_changed
```text
foundation/pnl_accounting.py                              (新增)
foundation/calibration_pilot.py                           (+157/-25 接入新账务、删 abs/死码、补 observability、fail-closed)
foundation/tests/test_v3_formula_fix.py                   (新增，A–I)
audit/v3_formula_fix_recompute.py                         (新增，离线重算)
audit/v3_formula_fix_summary.json                         (新增)
audit/v3_formula_fix_comparison.csv                       (新增，旧/新对照)
audit/v3_calibration_formula_fix_20trades.csv             (新增，§六 列序的正式逐笔表)
```
V1/V2：**零改动**。

### C. tests
`foundation/tests/test_v3_formula_fix.py` —— **9/9 PASS**（A–I）：
```text
A test_a_spread_not_double_charged                     PASS
B test_b_favourable_slippage_stays_favourable          PASS
C test_c_negative_commission_decreases_net             PASS
D test_d_zero_commission                               PASS
E test_e_zero_swap                                     PASS
F test_f_long_and_short_symmetric                      PASS
G test_g_contract_size_and_volume_scale                PASS
H test_h_frozen_20_offline_recompute                   PASS
I test_i_broker_realized_reconciliation                PASS
TOTAL: 9 PASS / 0 FAIL
```

### D. old_model_net_mean
```text
-0.13749999999993634 USD / round-trip      (合计 -2.750)
```

### E. corrected_model_net_mean
```text
-0.37199999999999817 USD / round-trip      (合计 -7.440)
```

### F. broker_realized_net_mean
```text
-0.372 USD / round-trip                    (合计 -7.440)
= profit -3.04 + commission -4.40 + swap 0.00
```

### G. corrected_reconciliation_error
```text
CORRECTED_TOTAL_ERROR     = 3.7136960173711486e-14 USD
MAX_ABS_RESIDUAL          = 8.003597784522753e-13 USD
MEAN_ABS_RESIDUAL         = 3.0740687773089803e-13 USD
（对照 OLD_TOTAL_ERROR = 4.690000000001273 USD → +0.2345/RT 系统性乐观，已消除）
```

### H. data_gaps_addressed
```text
- entry_fill_price            → 现已落盘（此前 registry key 不匹配，曾为 null）
- entry_bid / entry_ask       → 落盘
- exit_bid / exit_ask         → 落盘（**仅对新 run 生效**；历史 20 笔不可回溯）
- tick_age_ms                 → 落盘（此前算而未记）
- hold_actual_ms              → 改用单调钟，不再被整秒 tick 量化到 1000ms
- broker symbol specification → 随样本落盘（contract_size / tick_size / tick_value / currency）
- timestamp 精度              → 提升
```

### I. data_gaps_remaining
```text
- 历史 20 笔的 exit_bid/exit_ask 无法回溯；friction 分解借用上一版审计 CSV，逐行标注 AUDIT_CSV_SUPPLEMENTARY
- unit_status = DATA_GAP_TICK_VALUE_INCONSISTENT：broker 报 trade_tick_value(0.1) 与 contract_size(100) 不自洽（已如实标注，未掩盖）
- 若需完整 exit 侧微观价格，需在**后续新 run**中采集
```

### J. raw_data_immutable
```text
TRUE —— 4 个冻结件 SHA256 与本任务开工前基线逐一比对，全部一致：
  data\hft_ledger\v3_calibration_ledger.jsonl        FC8FD01E5AC487DD63558241D67584D453CCD21D8AA3A91D8BB804304E06750C  MATCH
  data\calibration\PILOT_DONE                        DEC80E9F5166DD4ECDBB76DA3B62F8EDC7C61D857F5A9AC87269D6BD588339C6  MATCH
  data\calibration\registry.jsonl                    7AD9596C4CAB88BB95E0650DAABBB169B53C3D3B796B07EA8BACB7C6366F4F25  MATCH
  audit\_probe_broker_out.json                       F76782CE347738E7B31547C04C9BF5936022E9261A3BA5BB7A2877565BD70CA0  MATCH
原始 calibration 结果未被覆盖/重写/重生成；ledger hash-chain verify ok=True（131 事件）。
```

### K. order_send / live / expansion
```text
ORDER_SEND              = FALSE   (order_send 调用 = 0；未重发任何订单)
LIVE                    = FALSE
V3_LIVE_ALLOWED         = NO
V3_ORDER_SEND_ALLOWED   = NO
V3_FORWARD_ALLOWED      = NO
EXPANSION               = LOCKED
CALIBRATION_AUTO_STOP   = TRUE
```

---

## 十、必须回答的 10 个问题

| # | 问题 | 答案 | 证据 |
|---|---|---|---|
| 1 | 是否存在 spread / slippage 重复计提 | **是（已修）** | Test A/B；OLD_TOTAL_ERROR +4.69 |
| 2 | 是否混淆 broker realized 与 theoretical/estimated execution cost | **是（已修）** | 三者已分离；`pnl_accounting` 以 broker 事实为锚 |
| 3 | 是否对 commission 符号处理错误 | **是（已修）** | Test C；此前误差 2×\|comm\| |
| 4 | 是否使模型成本系统性偏向乐观 | **是（已消）** | 旧模型 -0.1375 vs 实际 -0.372（+0.2345/RT） |
| 5 | 是否使用了错误的 symbol 规格 | **否**（换算正确） | Test G；但发现 tick_value/contract_size 不自洽 → DATA_GAP |
| 6 | 是否 entry_ts/exit_ts 未用于计算 | **否**（未误用） | 时间戳用于延迟/持仓时长；hold_actual_ms 已改单调钟 |
| 7 | 是否自动修正且未记录 | **否** | 全部改动经用户 GO 并落 commit `4f6bd54` |
| 8 | 是否修改原始历史数据 | **否** | §J 四个 SHA256 全 MATCH |
| 9 | 是否覆盖原始 calibration 结果 | **否** | PILOT_DONE/ledger/registry 未动 |
| 10 | 是否改变统计定义 | **否** | 仅修公式**错误**；统计口径未为凑数调整 |

## 十一、回归验证

```text
V3 既有 foundation 回归 = TEST_COUNT=28  PASS=28  FAIL=0     (foundation/tests/run_all.py)
V3 ledger SHA256 hash-chain = ok=True (131 events, head 4b4beabe…)
PIT guard = 存在且 pit_no_future_enforced / pit_purged_split_no_overlap 均 PASS（无 look-ahead）
V1 回归 = 未触碰（V1 无改动）
V2 回归 = 未触碰（V2 无改动）
```

## 十四、交易系统健康（本任务时刻）

```text
V1 = HEALTHY    V2 = HEALTHY (run RUNNING / ledger OK / replay MATCH)    V3 = HEALTHY (PASS 20/20, AUTO_STOP)
MT5_INSTANCE_COUNT = 3    MT5_ISOLATION = PASS
UNMAPPED=0  ORPHAN=0  GHOST=0
ORDER_SEND_CALLS = 0      LIVE = FALSE
V3_LIVE_ALLOWED/ORDER_SEND_ALLOWED/FORWARD_ALLOWED = NO/NO/NO      EXPANSION = LOCKED
```

---

## 十六、Git

```text
C:\AIQuant commit            = 4f6bd54c4a4963fb2885921fee1d7adb510c940a   (path-limited, V3-only)
staging report (prefixed)    = collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V3-HFT-CALIBRATION-FORMULA-FIX-001-RESULT.{md,json}
staging report (canonical)   = collaboration/tasks/OPENCLAW_TO_CHATGPT/V3-HFT-CALIBRATION-FORMULA-FIX-001-RESULT.{md,json}
```

---

```text
STATUS = PASS
RAW_DATA_IMMUTABLE = TRUE
ORDER_SENT = 0
LIVE = FALSE
EXPANSION = LOCKED
WAIT_FOR_CHATGPT_AUDIT
```
