# MODULE_4_PRE_AUDIT — Hermes → Paper → Ledger 接线（前置审计）

> BASE_COMMIT: `3b91a74`（含 M1 Hermes引擎 d91fc2b / M2 Paper执行 b761d53 / M3 Ledger&Replay 3b91a74）
> 本轮只做接线；不改 V1、不下 broker 单、不改 Hermes/Agent/Paper 参数。

## 1. Hermes 输出 schema（`hermes/hermes.py: decide()`，实测）
```
{ decision: "TRADE"|"WAIT"|"REJECT",
  reason, chosen_opportunity, regime_tags, plan|null, no_trade_reason,
  context_id, context_hash, decision_source, ts, instrument:"GC_F", proxy_for:"XAUUSD",
  live_trading:false, signal_from_agents:false }
plan(仅 TRADE) = { direction, entry, stop_loss, take_profit, risk_per_trade_pct,
                   expected_holding_time, trigger_condition, invalidation_condition,
                   thesis, counter_thesis, evidence_ids, confidence, expected_R }
```
无 `decision_id` 字段（用 context_id 派生）；无 `volume/qty_lots`。

## 2. Paper Executor 输入 schema（`execution/paper_executor.py`）
`open(direction, mid, sl, tp, plan_id, context_id=None, decision_ref=None, symbol="XAUUSD", spread_bps=None, slippage_bps=None, latency_ms=None, qty_lots=None, decision_price=None, exec_price=None, invalidation=None, bid=None, ask=None)`
成本来源：config `execution.cost_model`(spread 0.35/slip 0.30/lat 250/comm 0)；contract(min/max lot, contract_size)；risk(per_trade_pct, single_position, max_notional)。返回 `{ok,status,failure_code,position,record}`。

## 3. Ledger 输入 schema（`ledger/ledger.py`）
`new_event(type, **fields)` → `append_event(event, path)`；44 语义字段 + `previous_event_hash/event_hash`；事件类型含 DECISION/EXECUTION_REQUEST/RESPONSE/ORDER_ACCEPTED/REJECTED/FILL/POSITION_OPEN/CLOSE_REQUEST/CLOSED/COST/PNL/ACCOUNT_SNAPSHOT/ACCOUNT_INIT。

## 4. 当前三者之间的断点
- Hermes decision 与 PaperExecutor 的入参**字段名/结构不匹配**（direction↔side, entry↔mid, 无 volume/decision_id）。
- **无 Decision Contract / 冻结快照**；decision 对象可被后续修改。
- Paper 执行结果**未写 ledger**；无 decision→execution→position 因果链。
- Paper 账户状态与 ledger replay **未对账**。

## 5. 最小接线方案
1. **Decision Contract** + `freeze_decision()`（深拷贝冻结）。
2. `execution/hermes_paper_adapter.py`：`normalize()/freeze()/to_execution_request()/process()`（纯 translation）。
3. `process()`：DECISION 事件（TRADE/WAIT/REJECT 都写）→ 若 TRADE：EXECUTION_REQUEST →（执行）→ EXECUTION_RESPONSE/ORDER_ACCEPTED|REJECTED → FILL → POSITION_OPEN →（可选 close）→ POSITION_CLOSE_REQUEST/CLOSED/COST/PNL → ACCOUNT_SNAPSHOT。因果用 `parent_event_id`。
4. `hermes_paper_loop.py`：PAPER-only 启动入口（safety gate，`REFUSE_TO_START`）。
5. 测试 `tests/test_module4_loop.py`：T1–T12（frozen fixtures + 临时 ledger）。

## 6. 无需修改
- Agent1/Agent2、Hermes 决策逻辑/阈值、PaperExecutor 成本与规则、config 成本参数、V1。

## 7. 需要修改
- 仅新增文件（adapter/loop/tests/pre-audit/report）；不改既有模块源码。

## 8. 需要新增的测试
T1–T12（TRADE/WAIT/REJECT/exec-reject/immutability/causal/account-conservation/replay-equality/determinism/integrity/env-isolation/V1-isolation）。
