# MODULE 4 报告 — Hermes → Paper → Ledger 闭环接线

## 1. 状态
```
MODULE_4_COMPLETE
```

## 2. Pre-Audit（`research/MODULE_4_PRE_AUDIT.md`）
- **Hermes 输出**：`{decision:TRADE|WAIT|REJECT, reason, plan{方向/entry/SL/TP/...}, context_id, context_hash, ...}`（无 decision_id/volume）。
- **Paper 输入**：`PaperExecutor.open(direction, mid, sl, tp, plan_id, context_id, ..., qty_lots)`。
- **Ledger 输入**：`new_event(type,**fields)` + `append_event(ev, path)`。
- **断点**：字段不匹配、无冻结快照、执行结果未入账、账户↔账本未对账。

## 3. Decision Contract（最终 schema）
```
decision_id, decision(TRADE|WAIT|REJECT), timestamp_utc, symbol, side, order_type,
volume, entry_reference, stop_loss, take_profit, reason, confidence,
context_hash, input_hash, strategy_version
```
`normalize()` 从 Hermes decision 映射（direction→side, entry→entry_reference, …）；**不改写任何值**，仅翻译。

## 4. Adapter（`execution/hermes_paper_adapter.py`）
```
Hermes decision
  → normalize()            (translation only)
  → freeze_decision()      (深拷贝冻结 + _frozen_json 摘要)
  → to_execution_request() (只读快照 → 请求)
  → PaperExecutor.open()   (Module2 规则不变)
  → Ledger events
```
不得修改 signal/方向/阈值/SL/TP/仓位/confidence（代码仅做字段映射）。

## 5. Ledger 事件链（冒烟实例, PAPER）
```
ACCOUNT_INIT → DECISION(TRADE) → EXECUTION_REQUEST → EXECUTION_RESPONSE(EXECUTED)
→ ORDER_ACCEPTED → FILL → POSITION_OPEN → POSITION_CLOSE_REQUEST
→ POSITION_CLOSED(gross/net/commission) → COST → PNL → ACCOUNT_SNAPSHOT
因果: 每事件 parent_event_id 指向上一环; decision_id 贯穿全链 (T6 校验)。
WAIT/REJECT: 仅 DECISION(status)。
Execution 拒绝: DECISION(TRADE) → EXECUTION_REQUEST → EXECUTION_RESPONSE(REJECTED) → ORDER_REJECTED。
```

## 6. Replay / 账户一致性
Paper Account 与 Ledger Replay 逐字段一致（T8）：
`balance / equity / realized_pnl==net_pnl / trade_count / gross_pnl / commission / open_positions` 全 PASS。
守恒（T7）：`initial + gross + commission + swap == balance` ✅。

## 7. Tests（`logs/test_module4_loop.log`）
```
total 12 / passed 12 / failed 0 / skipped 0
T1 TRADE 全链 PASS · T2 WAIT 保留 PASS · T3 REJECT 保留 PASS · T4 Hermes TRADE vs Execution REJECT 区分 PASS
T5 冻结不可变 PASS · T6 因果链 PASS · T7 账户守恒 PASS · T8 Paper==Replay PASS
T9 确定性 replay PASS · T10 verify_ledger PASS · T11 环境隔离(PAPER only) PASS · T12 V1 隔离+启动门 PASS
```
运行入口冒烟：`hermes_paper_loop.py`（单轮）→ 账户 10000 → 9998.32（成本 −1.68）。

## 8. Safety
```
execution_mode=PAPER           (config + 启动门 assert_paper_only)
BROKER_DEMO orders=0           LIVE orders=0
启动门: 非 PAPER / broker.enabled / broker_demo_enabled 任一不符 → REFUSE_TO_START (T12 验证)
V1 untouched=PASS              (代码 0 处 V1 引用; V1 PID 1348 未变)
Paper 成本参数未改             (spread 0.35 / slip 0.30 / lat 250 / comm 0 维持基线)
```

## 9. Git
```
BASE_COMMIT: 3b91a74dced14d8e852c3a5d3f31f2c545142566
NEW_COMMIT : (提交后填)
CHANGED_FILES:
  research/hermes/trader_v2/execution/hermes_paper_adapter.py
  research/hermes/trader_v2/execution/hermes_paper_loop.py
  research/hermes/trader_v2/tests/test_module4_loop.py
  research/hermes/trader_v2/research/MODULE_4_PRE_AUDIT.md
  research/hermes/trader_v2/research/MODULE_4_REPORT.md
  research/hermes/trader_v2/logs/test_module4_loop.log
```

## 10. 未解决问题
- **commission 口径**：Paper 把 spread+slip+commission 合并在 entry/exit_cost；为与账户一致，ledger `POSITION_CLOSED.commission` = −(entry_cost+exit_cost)，已注明。未改 Paper Engine。
- **Hermes decision 无 volume/take_profit 细分**：adapter 原样翻译（volume 缺省由 executor 按风险定档；未改阈值）。
- 未启用真实 Hermes 长跑（仅受控 fixture/单轮冒烟）；如需长跑另行授权。
- 未进入 Module 5 / Broker Demo / Live / 策略优化。
