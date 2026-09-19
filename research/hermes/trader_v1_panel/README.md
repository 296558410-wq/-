# Hermes V1 · 控制面板（升级版 Control Center）

> 只读 · localhost:8790 · **绝不修改 V1 任何东西**（不改 V1 代码/数据/进程/cron，不用 V1 的 8787）

## 铁律（本面板的硬边界）
- **不修改 V1 任何文件**；不 import V1 交易/策略代码；不写任何东西。
- **不打开自己的 MT5 终端**（避免与 V1 的 MT5 用法冲突）。
- 账户信息通过 **V1 自带的 fail-closed demo-only 守卫**（`trader_v1/broker_mt5_demo.get_account`）在**一次性子进程**里只读拉取，30s 缓存；只读、不落盘、不写凭据。
- 端口 8790，与 V1(8787)/V2(8788) 完全隔离。

## 比 V2 面板更强 / 更全
- 顶部**实时报价条**（bid/ask/spread + 变动闪烁）+ **会话环**（OPEN/PRE-OPEN/CLOSED，来自 `trading_hours`）
- **M15 K线图**（由实盘 tick 重建，含 MA20 + 现价线 + 辉光）
- **工作流步进条**（OBSERVE→…→MEMORY 实时状态）
- **账户卡**（login/server/demo/balance/equity/margin/leverage）— 一眼看出跑的是 V1
- **持仓 + 实时浮盈**、**已实现 PnL / 胜率 / PF**（从 position events 汇总）
- **在册计划**（zone/trigger/SL/TP/EV）、**决策流**、**trader_summary 终端**、**WAIT 归因 Top**、**完整性/不变量**
- SSE 实时推送（2s 心跳）

## 运行
```
C:\AIQuant\.venv\Scripts\python.exe C:\AIQuant\research\hermes\trader_v1_panel\server.py
# 或双击 run_v1_panel.cmd  → http://127.0.0.1:8790
```
端口可用 `V1_PANEL_PORT` 覆盖（8787/8788 会被拒绝）。

## 数据来源（全部只读）
```
research/hermes/trader_v1/run_state/state_package_latest.json  行情包/多周期状态
research/hermes/trader_v1/run_state/workflow_latest.json       工作流步骤
research/hermes/trader_v1/run_state/statistics.json            counters/waits/invariants/integrity
research/hermes/trader_v1/run_state/plan_ledger.jsonl           在册/取消计划
research/hermes/trader_v1/run_state/decisions/*.json            决策
research/hermes/trader_v1/run_state/positions/*.json            持仓与成交events(realized)
research/hermes/trader_v1/run_state/trader_summary.txt          运行摘要
data/live_fxtm/quote_latest.json                                实时报价(V1 dashboard 写)
data/live_fxtm/ticks_*.parquet                                  tick → M15 K线
trader_v1/broker_mt5_demo.get_account() (子进程, 只读)          账户
```
