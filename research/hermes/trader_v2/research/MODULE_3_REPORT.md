# MODULE 3 报告 — Ledger & Replay

## 1. 状态
```
MODULE_3_COMPLETE
```

## 2. 实现摘要（新增文件）
```
ledger/ledger.py                  统一事件 schema + append_event() + verify_ledger()（sha256 链, GENESIS 起始）
ledger/replay.py                  确定性 replay() + state_hash() + conservation()
ledger/migrate_demo_calibration.py  phase2 旧记录 → BROKER_DEMO 事件（只读, 附 source_record_hash）
tests/test_ledger_replay.py       Test 1–10 + 环境隔离 + 迁移兼容
ledger/hermes_v2_ledger.jsonl     正式账本（迁移 12 事件: Demo 校准 attempt1 reject + attempt2 成交平仓）
research/MODULE_3_PRE_AUDIT.md    前置审计
config/v2_config.json             paths.ledger → ledger/hermes_v2_ledger.jsonl
```

## 3. Ledger Schema（§五 语义字段, `ledger.py:SCHEMA_FIELDS`）
```
event_id, event_type, event_version, seq,
timestamp_utc, source_timestamp_utc,
environment, execution_mode,
strategy_id, strategy_version, decision_id, parent_event_id,
symbol, side, order_type, volume,
requested_price, reference_bid, reference_ask, reference_mid,
fill_price, fill_volume, spread, slippage,
request_timestamp, response_timestamp, fill_timestamp, latency_ms,
order_id, deal_id, position_id,
commission, swap, gross_pnl, net_pnl,
account_balance, account_equity, free_margin,
broker, broker_server, status, retcode, message,
context_hash, input_hash,
previous_event_hash, event_hash
（+ 迁移追加 source_record_hash）
```
事件类型：`ACCOUNT_INIT, DECISION, EXECUTION_REQUEST, EXECUTION_RESPONSE, ORDER_ACCEPTED, ORDER_REJECTED, FILL, POSITION_OPEN, POSITION_CLOSE_REQUEST, POSITION_CLOSED, COST, PNL, ACCOUNT_SNAPSHOT, SYSTEM_EVENT`。
**WAIT/REJECT 以 DECISION(status) 保留**；不可变：`event[n].previous_event_hash == event[n-1].event_hash`，首条 = `GENESIS`。

## 4. Replay
```
input  : ledger(jsonl) [+ 可选 execution_mode 过滤]
recon  : ACCOUNT_INIT→初值; DECISION→计数(TRADE/WAIT/REJECT); POSITION_OPEN→持仓; POSITION_CLOSED→平仓+pnl; COST/SNAPSHOT→账户
output : {account, open_positions, closed_positions, trade_count, winning/losing_trades,
          gross_pnl, commission, swap, net_pnl, decisions, orders_rejected, events_consumed, state_hash}
```
不调用市场数据/Hermes/Broker/真实账户; 无副作用。同一账本两次 replay → 相同 `state_hash`。

## 5. 测试结果（`logs/test_ledger_replay.log`）
```
total 12 / passed 12 / failed 0 / skipped 0
T1 append+verify PASS · T2 tamper detected · T3 delete detected · T4 reorder detected
T5 replay determinism PASS · T6 empty ledger legal · T7 WAIT preserved(no trade)
T8 REJECT not counted as trade · T9 zero-fill no position · T10 cost conservation PASS
Env separation PAPER/BROKER_DEMO PASS · Migration compat + originals immutable PASS
```
（本轮以自建断言运行；亦可用 `pytest` 收集同名文件。）

## 6. Demo Calibration Compatibility（339c408 的 phase2）
- **兼容成功**：phase2 六个文件（order_request/response、close_request/response、summary、attempt1_rejected）→ 迁移为 12 条 BROKER_DEMO 事件。
- 保留：attempt1 rejected(10027)、attempt2 成交+平仓、entry/close fill、commission(-0.22)、spread、slippage、RTT、order_id/deal_id、retcode。
- 每条事件带 **source_record_hash**（源文件 sha256）→ 可追溯原文件；**原始文件未改（前后 sha256 一致）**。
- **未把 n=1 伪装成统计参数**（PNL 事件注明 "calibration observation"）。

## 7. Safety
```
V1 untouched = PASS
new broker order = 0
live trading = 0
```

## 8. Git
```
BASE_COMMIT: 339c40814e4cc2317efb2222b5be3e6aa90a2812
NEW_COMMIT : (见下, 提交后填)
CHANGED_FILES:
  research/hermes/trader_v2/ledger/ledger.py
  research/hermes/trader_v2/ledger/replay.py
  research/hermes/trader_v2/ledger/migrate_demo_calibration.py
  research/hermes/trader_v2/ledger/hermes_v2_ledger.jsonl
  research/hermes/trader_v2/tests/test_ledger_replay.py
  research/hermes/trader_v2/research/MODULE_3_PRE_AUDIT.md
  research/hermes/trader_v2/research/MODULE_3_REPORT.md
  research/hermes/trader_v2/config/v2_config.json
  research/hermes/trader_v2/logs/test_ledger_replay.log
```

## 9. 未解决问题 / 说明
- **PAPER 账户守恒**：`replay` 支持 `initial + gross + commission + swap == balance`；但 Paper 现有 execution 记录把 commission 折进 `entry/exit_cost`（无独立 commission 字段），待 Module 4 接线时统一——**本模块只定义口径，不改 Paper Engine**。
- **demo position_id** 为派生值 `DEMOPOS-<order_id>`（关闭太快未捕获 broker position ticket）——已如实记录。
- 本模块**未**：启用 broker adapter、Hermes 自动执行、Live、Module 4、Orchestration、策略优化。
