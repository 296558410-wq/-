# V1 / V2 睡前运行健康检查

- 时间：2026-09-17 21:2x CST（13:2xZ）· **只读检查，未修复、未优化、无订单** · 未改 V1/V2/V3 程序文件
- 证据来源：实机进程/文件/日志/cron 读取

## 1. 总体状态
| 项 | 结论 |
|---|---|
| **V1** | **正常**（含 2 处非关键观察，见 §2 异常） |
| **V2** | **正常** |
| **V1/V2 隔离** | **PASS** |
| **真实下单安全** | **PASS** |

## 2. V1
- **进程**：MT5 终端 `terminal64.exe` PID **1348**（`C:\Program Files\ForexTime (FXTM) MT5`，启动 2026-09-09 06:20）运行中；V1 面板 `trader_v1_panel/server.py` PID **22096**（+子 42140，启动 2026-09-14 06:41）运行中。V1 交易循环由 **cron `hermes-trader-m15-cycle`** 驱动（见 §调度）。无重复实例。
- **调度**：`hermes-trader-m15-cycle` 存在且 enabled；**lastRunStatus=ok**，lastRun≈**13:02Z**，nextRun≈**13:17Z**；无 lastRunError；无漏跑/重复迹象（V1 侧）。**未修改 cron。**
- **行情**：源 `data/live_fxtm` 持续写入（最近 tick 文件 `ticks_20260917` 覆盖至当日）；V1 `plan_ledger` 末年记录 13:04Z → 采集持续。bid/ask 合法性此前 PHASE B 已核（ask<bid=0/零价=0）。
- **决策循环**：最新 **registered `TP-20260917T1302Z` @ 2026-09-17T13:04:24Z** → 完整生命周期在进行中（登记→触发→成交→…）。
- **Ledger**：`run_state/plan_ledger.jsonl` **815 行**，可读；**815/815 事件均带 sha256**；**chain head = `7a47985278d8…`**。⚠️ 用外部通用重算仅 1/815 匹配（V1 采用自身 prev 链序列化）→ **链的独立外部复算 = UNVERIFIABLE**（需 V1 自身 `ledger.py` 口径）；**append-only 与 head 存在=OK**。**未修改 Ledger。**
- **当前持仓**：positions 文件 57；最近 3 笔状态已读取（无未平仓告警；最近一笔 09-17 已平）。**今日 P&L（09-17，截至上轮统计）= −52.09 USD**（OBSERVABLE_NET，含 slippage；commission/swap=DATA_GAP）。
- **异常（非关键，仅记录）**：
  1. `decisions/` 目录内含样例文件 `plan_example.json`（UTF-16LE），按名排序会排在最后 → **易被误读为“最新决策”**（本次已识别，非真实决策异常）。
  2. V1 ledger 的 sha256 链**无法用通用方法外部复算**（自定义序列化）→ 标注 `UNVERIFIABLE`，非错误，但外部审计需 V1 自带校验器。

## 3. V2
- **Shadow/Paper**：ACTIVE run `V2-SHADOW-20260917-105319-b5e4`，status **RUNNING**；counters **cycles 9 / WAIT 9 / TRADE 0 / REJECT 0**；最新窗口 **13:00Z，decision=WAIT，replay_match=True，无 agent/hermes 错误**。
- **G3**：start 10:53Z / end **2026-09-19T10:53Z**（48h 窗口）；已运行 ≈2.3h。`SHADOW_ALLOWED=true` ✔；`FORWARD_VALIDATION_ALLOWED` **absent=NO** ✔；`FORWARD_STARTED` **absent=FALSE** ✔。
- **Scheduler**：`DIRECT_WINDOWS_TASK`；health：`armed=True · market_open=True · router_enabled=True`；current_cycle 13:00Z。面板守护进程在（V2 dashboard PID 1328→56664，启动 19:46）。
- **Ledger**：run ledger 存在且写入；V2 `ledger.verify_ledger` 口径（见 §4 证据）与 replay MATCH（timeline replay_match=True）。
- **Broker 安全闸门**：**`BROKER_ORDER_SENT=FALSE`（PASS）** —— run 为 **PAPER(shadow/no-broker)**，`TRADE=0`，无 EXECUTION/下单事件；**无 LIVE、无 Forward 自动进入、无真实账户下单接口调用**。
- **异常**：V2 `logs/*.log` 24h 内错误命中 199 次，**全部落在 `test_*.log`（测试产物）**，**运行日志无 ERROR/CRITICAL** → 非运行时异常。

## 4. 隔离
- **V1 是否保持未修改？** 是 —— V1 目录仅其自身进程写入；V1/Panel 未动。
- **V2 是否保持独立？** 是 —— 独立目录/独立 MT5 实例（`fxtm_demo_01`，PID 36460）/独立 magic。
- **是否互相干扰？**
  - 静态互引：`trader_v1/*.py` 引用 `trader_v2` = **0**；`trader_v2` 引用 `trader_v1` = **0**（PASS）
  - MT5 实例：V1 用 Program Files 终端（PID 1348）；V2 用 `mt5_instances\fxtm_demo_01`（PID 36460）——**不同实例**（PASS）
  - Magic：**V1=90002 / V2=90003** ——**不同**（PASS）
  - Ledger/状态文件：各自 `run_state/` ——**不共用**（PASS）
- 结论：**V1/V2 文件与资源无互相干扰（PASS）**。

## 5. 资源健康
- RAM 使用 **70.4%**；CPU **~34%**；磁盘 **Free 886.3 GB / Used 136.6 GB**（充足）；GPU **RTX A2000 已用 0 MiB / 0%**（空闲，无 OOM）。
- Python 进程：V1 面板 / money_hunter / V2 面板 各 2（父子）+ hermes-web-ui（正常）。
- MT5：V1(1348)、V2(36460)、**V3(56148，20:56:58 启动)** 三实例并存。
- **无 OOM、无持续高 CPU、无异常磁盘占用迹象**；未见资源竞争导致漏跑。

## 6. 需明天处理的问题
1. **V3 MT5 实例进程命令行缺少 `/portable`**（PID 56148，20:56:58 启动）→ 若未用 `/portable` 将落到默认 data dir，**可能与 V3 隔离目录不一致**（V3 不在本次 V1/V2 范围，但列为观察项，**未动手**）。
2. V1 ledger 链需用 V1 自带校验器才能外部复核（当前 `UNVERIFIABLE`）。
3. 否则：**NONE**。

## 7. 说明
- 本报告为**唯一新增文件**；V1/V2/V3 程序文件与历史数据**零修改**；**未发送任何订单**。
- 无法独立验证项均标 `UNVERIFIABLE`，未猜测。检查后即停止，等待人工处理。

---
**PASS 证据样例**：`V1 cron hermes-trader-m15-cycle lastRunStatus=ok（≈13:02Z, next≈13:17Z）`；`V1 plan_ledger 815 行 head=7a47985278d8`；`V2 run b5e4 RUNNING cycles=9 WAIT=9 TRADE=0`；`V2 SHADOW_ALLOWED=true / FORWARD_VALIDATION_ALLOWED=absent(NO)`；`isolation: cross-refs=0, magic 90002 vs 90003, instances distinct`。
