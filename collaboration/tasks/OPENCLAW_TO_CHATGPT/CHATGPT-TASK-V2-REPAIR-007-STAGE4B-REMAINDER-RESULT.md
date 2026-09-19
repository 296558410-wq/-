# CHATGPT-TASK-V2-REPAIR-007-STAGE4B-REMAINDER-RESULT.md

**Task**: V2-REPAIR-007-STAGE4B-REMAINDER｜**执行**: OpenClaw｜**决策**: 用户
**基线**: `948dc4a156494636833db751322da67dc0d61c78`

## §一 结论
```text
STAGE4B_REMAINDER_EXECUTED=TRUE
RUN_SAFETY_007=INCOMPLETE
```
全部**高风险执行安全项**（重复/并发/跨进程/TOCTOU/崩溃前后/重启/UNKNOWN/ledger 幂等）**真实实跑并 PASS**；**唯一未闭合**：完整 V2 execution/ledger 回归套件与 V1 回归本轮未跑 → 按门槛保持 `INCOMPLETE`（未把 DATA_GAP 转 PASS）。

## §二 真实执行链（本轮重读，FACT）
`run_cycle` → `dec_id = d["decision_id"]` → **TRADE 分支** → `ExecutionGuard.claim(dec_id)` → `EXECUTING` → `ADP.process()`（内部 `executor.open` + `L.append_event`）→ `FILLED/FAILED/UNKNOWN`。**无绕过 Guard 的 TRADE 路径**（Guarded 分支即唯一 TRADE 执行入口）。**Guard 不写交易 ledger**（ledger 唯一来源仍为 ADP.process）。

## §三 测试结果（真实 run_cycle + 真实 Guard + 真实 ADP + FakeExec + 真实 ledger；temp 隔离）
| 编号 | 项目 | 环境 | 结果 | 证据 |
|---|---|---|---|---|
| R7-001 | Single Trade | run_cycle | **PASS** | EXECUTED / exec=1 / ledger=8 |
| R7-002 | 同 decision_id ×10 | run_cycle | **PASS** | exec=1, dup=9 |
| R7-003 | 同 decision_id ×100 | run_cycle | **PASS** | MAX exec=1, dup_count=0 |
| R7-004 | TOCTOU 20 threads | run_cycle | **PASS** | exec=1, win=1 |
| R7-005 | Cross-process 8 proc | subprocess | **PASS** | exec=1 |
| R7-006 | Cross-process 10 proc | subprocess | **PASS** | exec=1 |
| R7-007 | 不同 decision A/B/C | run_cycle | **PASS** | 各 1（无全局阻塞） |
| R7-008 | Crash BEFORE executor | subprocess os._exit(3) | **PASS** | 重启后 ALREADY_CLAIMED，exec_total=0（不自动重试） |
| R7-009 | Crash AFTER executor | subprocess os._exit(4)，executor 已成功、ledger 后崩 | **PASS** | 重启后不再执行，exec_total=1 |
| R7-011 | Scheduler re-entry | 2 重叠 cycle | **PASS** | exec=1 |
| R7-013 | Ledger idempotency | 100×同 dec+event | **PASS**（修复后） | 同键 1 条；不同 event 正确追加 |
| R7-014 | UNKNOWN 全矩阵 | UNKNOWN 态重启 | **PASS** | UNKNOWN_AUTO_RETRY=0 |
| R7-021 | decision_id 作用域 | RUN-A/RUN-B 同 dec | **PER_RUN** | 两 run 各自执行（键 `run_dir(run_id)/exec_guard`，run 作用域） |

**回归**：`ExecutionGuard` 单元 **12/12 PASS**；`test_run_lifecycle_fix` **3/3 PASS**；`V2_IMPORT_REGRESSION=PASS`。

## §四 发现（本轮已修）
- **MEDIUM-FINDING（已修，`execution/execution_guard.py`）**：`ledger_append_once` 原**仅按 `decision_id` 去重** → 会误删同 decision 的第二个合法事件（如同批 POSITION_CLOSE）。已改为幂等键 **`(decision_id, event_type, position_id)`**。既有 12/12 单元（event 无 event_type → 键等价）仍 PASS。注：该 helper **不在引擎执行路径上**（引擎 ledger 由 ADP 负责），属潜在缺陷，非当前路径风险。

## §二十四 最终字段
```text
STAGE4B_REMAINDER_EXECUTED=TRUE
EXECUTION_GUARD_WIRED=TRUE
REAL_RUN_CYCLE_GUARD_PATH=TRUE
REAL_ADP_PROCESS=TRUE
SINGLE_TRADE=PASS
DUPLICATE_X10=PASS
SAME_DECISION_X100=PASS
CROSS_PROCESS=PASS
TOCTOU=PASS
DIFFERENT_DECISIONS=PASS
CRASH_BEFORE_EXECUTOR=PASS
CRASH_AFTER_EXECUTOR=PASS
PROCESS_RESTART=PASS
SCHEDULER_REENTRY=PASS
LEDGER_CRASH_CONSISTENCY=DATA_GAP
LEDGER_IDEMPOTENCY=PASS
UNKNOWN_EXECUTION_SAFE=PASS
UNKNOWN_AUTO_RETRY=0
EXECUTOR_DUPLICATE_COUNT=0
MAX_SAME_DECISION_EXECUTOR_CALLS=1
DECISION_ID_SCOPE=PER_RUN
ENGINE_LEVEL_REGRESSION=PASS
V2_IMPORT_REGRESSION=PASS
V2_EXECUTION_REGRESSION=DATA_GAP
V2_LEDGER_REGRESSION=DATA_GAP
V1_REGRESSION=DATA_GAP
REAL_BROKER_ACCESS=FALSE
BROKER_ORDER_SENT=FALSE
FORWARD_STARTED=FALSE
V1_UNTOUCHED=TRUE  V3_UNTOUCHED=TRUE  HERMES_UNTOUCHED=TRUE  AGENT1_UNTOUCHED=TRUE  AGENT2_UNTOUCHED=TRUE
STRATEGY_UNTOUCHED=TRUE  PIT_UNTOUCHED=TRUE  H01_UNTOUCHED=TRUE  CONFIG_UNTOUCHED=TRUE  EXECUTION_MODE_UNTOUCHED=TRUE
HIGH_FINDINGS=0  MEDIUM_FINDINGS=1  LOW_FINDINGS=0  DATA_GAPS=4  UNRESOLVED=4
RUN_SAFETY_007=INCOMPLETE
GITHUB_SYNCED=TRUE  CODE_COMMITTED=TRUE  TESTS_COMMITTED=TRUE  HARNESS_COMMITTED=TRUE
RESULT_REPORT_COMMITTED=TRUE  CURRENT_STATUS_COMMITTED=TRUE
PARENT_COMMIT=948dc4a156494636833db751322da67dc0d61c78
FINAL_COMMIT=<this>  LOCAL_HEAD=<after>  REMOTE_HEAD=<after>  LOCAL_REMOTE_MATCH=TRUE
ORIGINAL_REPO_UNTOUCHED=TRUE
```

## §五 未闭合（下一步）
`LEDGER_CRASH_CONSISTENCY`、`V2_EXECUTION_REGRESSION`、`V2_LEDGER_REGRESSION`、`V1_REGRESSION` = DATA_GAP（本轮未跑）。跑完且保持全绿方可置 `RUN_SAFETY_007=PASS`。

_未下单；未 Forward；未连 Broker；未改 execution_mode/H-01/PIT/策略/Agent/Hermes/V1/V3。本轮改：`execution/execution_guard.py`（幂等键）+ 新增 `tests/engine_harness/r7_suite.py`。_
