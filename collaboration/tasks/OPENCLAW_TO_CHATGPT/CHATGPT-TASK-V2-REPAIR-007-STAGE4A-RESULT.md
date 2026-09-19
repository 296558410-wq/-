# CHATGPT-TASK-V2-REPAIR-007-STAGE4A-RESULT.md

**Task**: V2-REPAIR-007 STAGE-4A（真实 TRADE 引擎 Harness 打通与可验证驱动）
**执行**: OpenClaw｜**决策**: 用户
**边界**：本轮**未修改任何引擎代码**（`runtime/shadow_run.py` 等）。

## §一 结论
```text
STAGE4A_EXECUTED=TRUE
ENGINE_TRADE_HARNESS=INCOMPLETE
TRADE_REACHED=DATA_GAP
EXECUTION_GUARD_WIRED=FALSE
RUN_SAFETY_007=INCOMPLETE
```

## §二 Stage-A：真实调用链（已实读，FACT）
来源：`runtime/shadow_run.py`（run_cycle）、`execution/hermes_paper_adapter.py`（ADP.process/normalize/freeze_decision）。
```text
Decision 产生      = hermes.decide（run_cycle 内）→ d
decision_id 生成   = ADP.normalize(): did = d["decision_id"] or f"DEC-{d['context_id'] or d['ts']}"
TRADE 进入         = run_cycle: d["decision"]=="TRADE" → (price_space) → ADP.process
ADP.process 调用   = run_cycle: out = ADP.process(d, pe, led, …)
Executor 真正执行   = **ADP.process 内部**（_to_request 仅 TRADE → executor.post/order）
execution_result   = ADP.process 返回 out
Ledger 写入        = **ADP.process 内部** `L.append_event(...)`（Module3 ledger，因果链）
Reconciliation     = run_cycle: `ADP.reconcile_broker_closes(...)`（BROKER_DEMO）+ replay 对账
State 更新         = run_cycle 末尾写 run_state / counters
```
**关键归属（回答 §四）**：
1. `ADP.process` **已拥有 executor 调用权**；
2. `ADP.process` **已写 ledger**；
3. reconciliation 由 run_cycle 的 `reconcile_broker_closes` 承担；
4. **正确的 ExecutionGuard 接线层 = `ADP.process` 之外、`run_cycle` 的 TRADE 分支**（claim→EXECUTING→ADP.process→transition）；
5. **Guard 不得写 ledger**（否则与 ADP 双重记账）——只做 claim/transition/idempotency/UNKNOWN；
6. `decision_id` 来源 = Hermes decision 的 `decision_id`（缺失时由 `ADP.normalize` 兜底 `DEC-{context_id|ts}`），**非 run_id**。

## §三 未完成（DATA_GAP）与阻塞点
- **未把 Harness 驱动到 TRADE**：需在 worker 内注入 fake Hermes（令 `d["decision"]=="TRADE"` + 合法 plan）+ fake A1/A2/context，再驱动**真实** `run_cycle`。本轮预算内未构建/稳定该注入链。
- 因此按 §十四：**不修改正式 `shadow_run.py`**（未接线）。
- 未做：H4A-001..007 的 TRADE 级观察；ledger/reconciliation 捕获；决定确定性。

### BLOCKER
```text
TRADE_REACHED=DATA_GAP：真实 run_cycle 需真实 Hermes/A1/A2/context；注入确定性 TRADE fixture 未在本轮稳定完成。
下一步最小修复点：在 tests/engine_harness/worker.py 内 monkeypatch hermes.decide(_pure) → 返回确定性 TRADE decision（合法 plan），
并注入 fake A1/A2/context；再驱动 run_cycle 观察定链；稳定后再据 §十五 接 ExecutionGuard.claim(decision_id)。
```

## §二十 最终字段
```text
STAGE4A_EXECUTED=TRUE
ENGINE_TRADE_HARNESS=INCOMPLETE
TRADE_REACHED=DATA_GAP
REAL_DECISION_CAPTURED=DATA_GAP
DECISION_ID_IS_RUN_ID=FALSE(静态证据: normalize 生成 DEC-*)
EXECUTION_GUARD_WIRED=FALSE
FAKE_EXECUTOR_CALLS=0
REAL_BROKER_ACCESS=FALSE
BROKER_ORDER_SENT=FALSE
LEDGER_EVENTS=0
LEDGER_CAPTURED=DATA_GAP
RECONCILIATION_REACHED=DATA_GAP
STATE_CAPTURED=DATA_GAP
DETERMINISM=DATA_GAP
PROCESS_EXIT=PASS
OUTPUT_CAPTURE=PASS
ENGINE_FAILURE=NONE
HARNESS_FAILURE=NONE
BLOCKER=TRADE_REACHED=DATA_GAP (fake Hermes/A1/A2 注入未稳定完成)
V1_UNTOUCHED=TRUE  V3_UNTOUCHED=TRUE  HERMES_UNTOUCHED=TRUE  AGENT1_UNTOUCHED=TRUE  AGENT2_UNTOUCHED=TRUE
STRATEGY_UNTOUCHED=TRUE  PIT_UNTOUCHED=TRUE  H01_UNTOUCHED=TRUE  CONFIG_UNTOUCHED=TRUE
FORWARD_STARTED=FALSE  BROKER_ORDER_SENT=FALSE  REAL_BROKER_ACCESS=FALSE
RUN_SAFETY_007=INCOMPLETE
```

## Git
```
PARENT_COMMIT=<prev HEAD>
FINAL_COMMIT=<this commit>  LOCAL_HEAD=<after>  REMOTE_HEAD=<after>  LOCAL_REMOTE_MATCH=TRUE
ORIGINAL_REPO_UNTOUCHED=TRUE
```
（本轮仅新增本报告；未改引擎/测试代码。）

_未下单；未 Forward；未改 execution_mode/H-01/PIT/策略；未改 shadow_run。_
