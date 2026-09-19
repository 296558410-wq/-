# V2 FAILURE INJECTION REPORT — 20260917 (P1-F)

真实注入（隔离/离线），断言 fail-closed。`tests/test_failure_injection.py` **13/13 PASS**。

| 注入 | 期望 | 实测 |
|---|---|---|
| DXY/UST10Y/VIX 缺失 | DEGRADED（非 NEUTRAL） | PASS |
| health FAIL | REJECT（不交易） | PASS |
| health DEGRADED | WAIT | PASS |
| macro_status DEGRADED | WAIT | PASS |
| freshness unknown | WAIT | PASS |
| price_space basis 缺失 | BASIS_UNAVAILABLE（reject） | PASS |
| price_space basis stale | BASIS_STALE（reject） | PASS |
| broker 无效 stops | PRECHECK_REJECT（不下单） | PASS |
| pit_cache 未来记录 | 不可见（as-of 排除） | PASS |
| replay snapshot 缺失 | SNAPSHOT_MISSING（fail-closed，不联网） | PASS |
| ledger 截断行 | LedgerMalformed（verify 失败→BLOCK） | PASS |
| forward gate 未认证 | start_run 拒绝 | PASS |
| router env 显式 disable | 生效（router_enabled=False） | PASS |

## 已由既有回归覆盖（未重复注入）
- Broker 三路径 reconcile、重启恢复：`test_broker_reconcile` 25/25。
- Ledger 重复/篡改/顺序：`test_module5_shadow`、`test_v2_repair`。
- Scheduler 去重/漏周期：`test_module5_paths`、scheduler 窗口去重。
- 数据源 fallback/超时：`test_data_sources` 37/37、`test_dxy_recursion` 15/15。

## 结论
所有注入场景均 **fail-closed**（NO FALSE FRESH / NO FALSE NEUTRAL / NO TRADE on bad data）。

## 局限
- Broker 侧真实故障（MT5 断连/auto-close）以既有测试 + reconcile 计数覆盖；未在 live 实例上强制断连（避免影响实例）。
- Windows sleep/kill 无法在本阶段实测（不修改任务计划）；由 `StartWhenAvailable=false` + 窗口去重静态保证。
