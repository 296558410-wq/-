# MODULE_3_PRE_AUDIT — Ledger & Replay（前置审计）

> BASE_COMMIT: `339c408`（V2 已含 Agent1/Agent2/Phase-1.5/Hermes引擎/Paper执行/Demo校准 P1+P2）
> 本轮**只做 Module 3**；未改 V1、未下单、未启用 broker、未改 Hermes/Paper 参数。

## 1. 当前已有数据结构（审计所见）
| 来源 | 文件 | 关键字段 |
|---|---|---|
| Hermes 决策上下文 | `state/decision_contexts/<ctx>.json` | context_id, context_hash, cycle, agent1/agent2 refs, evidence_ids, config_hash, versions |
| Hermes 决策 | `state/hermes_decision_latest.json` | decision(TRADE/WAIT/REJECT), reason, chosen_opportunity, regime_tags, plan, context_id/hash |
| 机会账本 | `state/opportunity_ledger.jsonl` | opportunity_id, thesis, direction, trigger, invalidation, priced_in, counter_thesis, evidence_ids, status |
| Hermes 记忆 | `state/hermes_memory.jsonl` | context_id, decision, reason, counter_thesis, outcome(null), why_wrong(null) |
| Paper 执行 | `state/paper_account.json` + `paper_executions.jsonl` | account{initial_balance,balance,equity,realized_pnl,unrealized_pnl,positions,closed_trades}; exec rec{status,failure_code,fill_price,qty_lots,entry_cost_usd,...} |
| Paper 成交 | `state/paper_account.json#closed_trades` | position_id,plan_id,direction,qty_lots,entry,exit,reason,gross_usd,entry_cost_usd,exit_cost_usd,net_usd,sl,tp,latency_ms,spread_source |
| Demo 校准 | `state/demo_calibration/phase2/*.json` | order_request/order_response(retcode,order_id,deal_id,requested_price,actual_fill_price,response_latency_ms) / close_request/close_response / attempt1_rejected(10027) / summary |
| 证据 | `state/evidence_registry.jsonl` + `data_cache/evidence_raw/` | evidence_id, sha256 链 |

## 2. 当前缺失字段（Module 3 需补）
- 无**统一事件账本**（DECISION→REQUEST→RESPONSE→FILL→POSITION→CLOSE→PNL→ACCOUNT）；现为分散文件。
- 无 `previous_event_hash/event_hash`（无防篡改）。
- 无统一 `execution_mode/environment` 标记（Paper 与 Broker Demo 未在同一账本内可区分）。
- 无 `event_id/source_timestamp/retcode/order_id/deal_id/position_id` 的统一语义。
- **无 Replay**（从账本重建状态）。
- Demo 校准数据为**旧 schema**，无 `source_record_hash` 迁移锚点。

## 3. 可复用
- Hermes 的 `context_id/context_hash`（作为 ledger 的 context_hash 关联）。
- evidence 的 sha256 固化模式（沿用其 hash 思路）。
- demo phase2 的 order/close 记录（迁移为 BROKER_DEMO 事件）。
- paper `closed_trades` 结构（迁移为 PAPER 事件）。

## 4. 重复/冲突
- 三处各自维护"时间戳/价格/成本"，**口径不一**（Paper 把 commission 折进 entry/exit_cost；demo 有独立 commission 字段）。→ 统一进 event schema，保留原始值 + 明确 `cost_model_note`。
- `unrealized_pnl` 在 Paper 账户存在但非事件化 → 只入 `ACCOUNT_SNAPSHOT`。

## 5. Module 3 最小实现方案
1. `ledger/ledger.py`：统一 event schema + `append_event()` + `verify_ledger()`（sha256 链，GENESIS 起始）。
2. `ledger/replay.py`：`replay()` 从账本重建 account/open/closed/pnl；`state_hash()`。
3. `ledger/migrate_demo_calibration.py`：把 phase2 原始记录（只读）转成 BROKER_DEMO 事件，附 `source_record_hash`。
4. `tests/test_ledger_replay.py`：Test1–10（append/tamper/delete/reorder/determinism/empty/WAIT/REJECT/partial-schema/cost-conservation）+ 环境隔离 + 迁移兼容。
5. 账本文件：`ledger/hermes_v2_ledger.jsonl`（config `paths.ledger` 同步）。

## 6. 不需要修改的部分
- 不改 Agent1/Agent2、Hermes 引擎逻辑、Paper Engine 参数、FXTM adapter（保持 disabled）、V1。
- 不改 demo phase2 原始记录（**只读迁移**）。

## 7. 需要新增的文件
```
ledger/ledger.py
ledger/replay.py
ledger/migrate_demo_calibration.py
tests/test_ledger_replay.py
research/MODULE_3_PRE_AUDIT.md (本文件)
research/MODULE_3_REPORT.md
state/ledger/ (运行产物) + ledger/hermes_v2_ledger.jsonl
```
