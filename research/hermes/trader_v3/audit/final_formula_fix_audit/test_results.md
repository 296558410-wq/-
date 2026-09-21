# Test Results — V3-HFT-CALIBRATION-FORMULA-FIX-001

所有结果均由**实际执行**得到（只读回放，未修改测试以追求"好看"）。

## 1. 公式修复回归测试

```text
文件   : research/hermes/trader_v3/foundation/tests/test_v3_formula_fix.py
命令   : C:\AIQuant\.venv\Scripts\python.exe -m pytest foundation\tests\test_v3_formula_fix.py -q
原始输出(末行): 9 passed, 9 warnings in 0.07s
结果   : formula_fix_tests = 9/9 PASS   FAIL = 0
```

| ID | 测试 | 结果 |
|---|---|---|
| A | `test_a_spread_not_double_charged` | PASS |
| B | `test_b_favourable_slippage_stays_favourable` | PASS |
| C | `test_c_negative_commission_decreases_net` | PASS |
| D | `test_d_zero_commission` | PASS |
| E | `test_e_zero_swap` | PASS |
| F | `test_f_long_and_short_symmetric` | PASS |
| G | `test_g_contract_size_and_volume_scale` | PASS |
| H | `test_h_frozen_20_offline_recompute` | PASS |
| I | `test_i_broker_realized_reconciliation` | PASS |

> Test H = 用冻结历史 20 笔离线重算可复现；Test I = corrected 与 broker 事实对平。

## 2. 既有 V3 foundation 套件（未修改）

```text
文件   : research/hermes/trader_v3/foundation/tests/run_all.py
命令   : C:\AIQuant\.venv\Scripts\python.exe foundation\tests\run_all.py
原始输出: === TEST_COUNT=28 PASS=28 FAIL=0 ===
结果   : foundation_tests = 28 PASS   FAIL = 0
```

覆盖（节选）：tick_engine / tick_schema / tick_recorder / execution_calibration / cost_model /
gpu_engine / feature_engine / label_engine / pit_guard / ledger / registry / agent_interface /
entry_exit_interface / model_pipeline。其中与本次最相关：

```text
[PASS] ledger_append_only_hash_chain
[PASS] ledger_tamper_detected
[PASS] pit_no_future_enforced
[PASS] pit_purged_split_no_overlap
[PASS] entry_exit_interface_order_send_false
[PASS] agent_interface_no_auto_decision
```

## 3. 离线重算可复现性

```text
脚本: research/hermes/trader_v3/audit/v3_formula_fix_recompute.py
输入: 冻结 ledger + broker deal 导出
输出: audit/v3_formula_fix_summary.json / audit/v3_formula_fix_comparison.csv
```

## 4. 汇总

```text
formula_fix_tests = 9/9 PASS
foundation_tests  = 28 PASS
FAIL = 0
```
