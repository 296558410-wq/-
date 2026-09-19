# ISSUE_NOTE — run V2-PAPER-20260914-231126-5fe2 (archived)

## 事故
- 2026-09-15 **04:53:31Z（本地 12:53）** 起 `BLOCKED`：`PAPER_REPLAY_MISMATCH (equity, net_pnl)`，此后无新周期。
- 触发点：run 首笔真实成交（04:45Z，TRADE SHORT XAUUSD 0.01 @4305.53，SL4314/TP4269.31，pos ******）。

## 根因（2 个工程 bug，已修 commit 3113801）
1. **对账闸门对"持仓中"天然不成立**：`_account_match`(BROKER_DEMO) 拿 replay 已实现量去比 broker **实时浮动 equity / 浮盈**（`realized_pnl=balance-initial`）→ 有持仓/价格一动必超容差 → 误判 BLOCK。
2. **经纪商侧平仓不回账**：引擎不轮询 broker SL/TP 平仓 → 仓位被 TP 平掉后账本无 `POSITION_CLOSED` → 账本与账户脱节。

## 实际发生的经纪商事件（demo ******，非策略成绩）
- 该 SHORT 最终被 broker 按 **TP 平仓**：账户 999.87 → **1035.96（+36.09）**，现 0 持仓。
- 本 run 的 append-only 账本**未记录**这次平仓（引擎已 blocked）→ 账本停在 `1 open / balance 999.76`。

## 处置（本文件所在 run）
- run 已 **finalize 归档**（保留其历史，**未删改账本**）。
- 修复后：`reconcile_broker_closes` 会在每周期自动回写此类 broker 平仓；`_account_match` 不再比浮动值。
- 新 run 以 broker 当前余额（1035.96）为新初始基准，继续运行。
