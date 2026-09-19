# ISSUE — Broker 自动平仓导致 run BLOCKED（reconcile 状态不同步）

- **ID**: ISSUE_BROKER_AUTO_CLOSE_RECONCILE_STATE
- **STATUS**: **FIXED**（commit `5955ede`）
- **发生**: run `V2-PAPER-20260915-112856-d341`，2026-09-16 01:08:07Z（本地 09:08）起 `BLOCKED`
- **类型**: 工程 bug（状态一致性）

## 症状
`PAPER_REPLAY_MISMATCH`，detail = `{net_pnl: false, trade_count: false, commission: false}`（`balance: true`）。
触发点：该 run 首笔真实成交被 **broker 侧 TP 自动平仓**（`POSITION_OPEN` seq 95，SHORT 0.01 XAUUSD
@4292.60 → broker deals 平仓 @4277.75，gross +14.85 / commission −0.22 / **net +14.63**）。
此后 run 冻结，9.5 小时无新周期。

## 根因
`shadow_run._account_match()`（BROKER_DEMO 分支）比较「账本 replay 的已实现量」与 `executor.acc["closed_trades"]`：

1. `closed_trades` **只在 `BrokerDemoExecutor.close()` 里 append**；
2. broker 侧（SL/TP）自动平仓走 `reconcile_broker_closes()` —— **只写账本，不更新 executor 状态**；
3. 每个周期 `pe.connect()` → `_fresh()` 会**清空** `closed_trades`。

⇒ 只要 broker 先于账本平仓，对比必然 `net_pnl/trade_count/commission` 三项 fail → 必然 BLOCK。

## 修复（5955ede）
- `BrokerDemoExecutor.register_closed_trade()`：幂等（按 `position_id`），与 `close()` **同一状态语义**。
- `BrokerDemoExecutor.rebuild_closed_trades()`：从 **broker deals** 重建 run 范围内的已实现成交视图
  （跨 reconnect / 进程重启持久）。
- `reconcile_broker_closes()`：Phase A（broker 平仓 → 账本 + executor 双写）；Phase B（账本已平仓 →
  重建 executor 视图）；**重复对账不重复记账**（账本 POSITION_CLOSED 为权威）；`reconcile_report`。
- `_account_match()`：新增显式 `history_unavailable`（broker deal 历史不可用 → **fail-closed**）。
- 新增可观测计数器：`broker_reconcile_count` / `broker_auto_close_count` /
  `reconcile_duplicate_prevented` / `account_match_failures`。

## 验证
- `tests/test_broker_reconcile.py`：T1–T8（25/25）——
  broker 自动 TP、自动 SL、引擎主动 close、重复 reconcile（不重复记账本）、
  restart recovery（崩溃后重建）、partial state（fail-closed，不下新单）、
  Broker==Executor==Ledger==Replay、conservation PASS。
- `tests/test_v2_repair.py` R12/R12b（21/21）。
- 全量回归 18/18 文件 PASS（`tools/run_v2_tests.py`）。

## 历史 run 处置
`V2-PAPER-20260915-112856-d341` finalize 为 **BLOCKED（immutable）**：账本/决策/时间线**未改动**
（verify=True、conservation=True）；运行以新 continuation run 承接（`PREVIOUS_RUN=d341`）。
**不**通过改历史账本让旧 run「看起来正常」。

> 该笔 `+14.63 USD` 保留为有效 Broker Demo 执行证据 + GC/spot 标尺异常案例
> （见 `ISSUE_GC_SPOT_PRICE_SPACE_MISMATCH.md`）；未删、未改、未重算。
