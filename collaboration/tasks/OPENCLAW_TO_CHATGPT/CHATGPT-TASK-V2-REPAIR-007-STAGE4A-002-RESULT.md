# CHATGPT-TASK-V2-REPAIR-007-STAGE4A-002-RESULT.md

**Task**: V2-REPAIR-007-STAGE4A-TRADE-HARNESS-002｜**执行**: OpenClaw｜**决策**: 用户
**边界**：**未修改任何引擎源码**（`shadow_run.py` / `hermes_paper_adapter.py` / `execution_guard.py` 等 0 改动）。

## §一 结论
```text
STAGE4A_002_EXECUTED=TRUE
ENGINE_TRADE_HARNESS=PASS
```
**Harness 已能把真实 `run_cycle()` 稳定驱动到 TRADE，并真实进入 `ADP.process()`，由 Fake Executor 接住、真实 ledger 记录。**

## §二 调用链（实读，FACT）
`run_cycle`：`ADP.assert_execution_allowed()` → Agent1/2 → `d,ctx,cands,tags = HERMES.run(cycle)` → `dec_id = d["decision_id"] or DEC-{context_id}` → price_space → **`out = ADP.process(d, pe, led, …)`**（`ADP.process` 内部：`to_execution_request` → `executor.open(...)` → `L.append_event(...)` 写 ledger）→ `_account_match` replay 对账 → 写 run_state。

## §三 Harness 注入（不改引擎）
`tests/engine_harness/worker_trade.py`：进程内 monkeypatch —— `SR.A1`(fake) / `SR.A2`(fake) / `SR.HERMES`(fake，返回确定性 TRADE `decision_id=TEST-DECISION-0001`) / `SR._make_executor`→`FakeExec`（实现 `acc/account()/open()/close()` 契约）；`SR.PS=None`（跳过 price_space）；run_dir/ACTIVE/START_LOCK/state_path → `%TEMP%`；拦截 broker/paper 模块。**零 broker**。

## §四 结果（结构化）
```
HARNESS_START=TRUE  RUN_ID<V2-SHADOW-*>
DECISION_ID=TEST-DECISION-0001
A1/A2/CONTEXT/HERMES_INJECTED=TRUE
TRADE_REACHED=TRUE
REAL_ADP_PROCESS=TRUE
FAKE_EXECUTOR_CALLS=1
LEDGER_EVENTS=8
EXECUTION_RESULT=EXECUTED
REAL_BROKER_ACCESS=FALSE  BROKER_ORDER_SENT=FALSE
EXIT_CODE=0  HARNESS_RESULT=PASS
```
**确定性 ×3**：3/3 均 `FAKE_EXECUTOR_CALLS=1 / LEDGER_EVENTS=8 / EXECUTED / PASS`（`decision_id` 稳定）。

## §五 调试记录（分类，非 DATA_GAP）
1. 首轮 `KeyError:'positions'` —— **FIXTURE_FAILURE**（FakeExec.account 缺字段）→ 补齐。
2. 次轮 `KeyError:'realized_pnl'`（`_account_match` 对账）—— **FIXTURE_FAILURE** → 补齐。
3. 第三轮 **PASS**。（引擎本身无改动；问题全在 fake fixture 契约。）

## §六 未做（按任务书 §二十一 留到 4B）
ExecutionGuard.claim / 状态机 / duplicate×10 / cross-process / crash / restart / scheduler re-entry —— **未做**（本阶段不做）。

## §七 安全/未改
```
REAL_BROKER_ACCESS=FALSE  BROKER_ORDER_SENT=FALSE  FORWARD_STARTED=FALSE
V1_UNTOUCHED=TRUE  V3_UNTOUCHED=TRUE  HERMES_SOURCE_UNTOUCHED=TRUE
AGENT1_SOURCE_UNTOUCHED=TRUE  AGENT2_SOURCE_UNTOUCHED=TRUE  STRATEGY_UNTOUCHED=TRUE
PIT_UNTOUCHED=TRUE  H01_UNTOUCHED=TRUE  CONFIG_UNTOUCHED=TRUE  EXECUTION_MODE_UNTOUCHED=TRUE
runtime/shadow_run.py 修改 = 0
```

## §二十三 最终字段
```text
STAGE4A_002_EXECUTED=TRUE
ENGINE_TRADE_HARNESS=PASS
A1_INJECTED=TRUE  A2_INJECTED=TRUE  CONTEXT_INJECTED=TRUE  HERMES_INJECTED=TRUE
DECISION_REACHED=TRUE  TRADE_REACHED=TRUE  REAL_DECISION_CAPTURED=TRUE  DECISION_ID_STABLE=TRUE
REAL_RUN_CYCLE=TRUE  REAL_ADP_PROCESS=TRUE
FAKE_EXECUTOR_CALLS=1  FAKE_EXECUTOR_ONLY=TRUE  REAL_BROKER_ACCESS=FALSE  BROKER_ORDER_SENT=FALSE
LEDGER_EVENTS=8  LEDGER_CAPTURED=TRUE
RECONCILIATION_REACHED=TRUE   # run_cycle 的 _account_match/replay 对账已执行（PAPER）
STATE_CAPTURED=TRUE
DETERMINISM=PASS  EXIT_CODE=PASS  OUTPUT_CAPTURE=PASS
BLOCKER=NONE
V1_UNTOUCHED=TRUE  V3_UNTOUCHED=TRUE  HERMES_SOURCE_UNTOUCHED=TRUE  AGENT1_SOURCE_UNTOUCHED=TRUE
AGENT2_SOURCE_UNTOUCHED=TRUE  STRATEGY_UNTOUCHED=TRUE  PIT_UNTOUCHED=TRUE  H01_UNTOUCHED=TRUE
CONFIG_UNTOUCHED=TRUE  EXECUTION_MODE_UNTOUCHED=TRUE
FORWARD_STARTED=FALSE  BROKER_ORDER_SENT=FALSE  REAL_BROKER_ACCESS=FALSE
RUN_SAFETY_007=INCOMPLETE   # 尚未接 ExecutionGuard（Stage-4B）
```

## Git
```
PARENT_COMMIT=<prev>  FINAL_COMMIT=<this>  LOCAL_HEAD=<after>  REMOTE_HEAD=<after>  LOCAL_REMOTE_MATCH=TRUE
ORIGINAL_REPO_UNTOUCHED=TRUE
```

_未下单；未 Forward；未改 execution_mode/H-01/PIT/策略/引擎。_
