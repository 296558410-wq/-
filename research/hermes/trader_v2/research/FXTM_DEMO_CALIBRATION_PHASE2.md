# FXTM Demo Execution Calibration — Phase 2 报告

> 日期: 2026-09-11 · 目标: 用**一次最小 XAUUSD Demo 市价单**测真实执行参数（fixed BUY, 非策略）。
> 账户: FXTM Demo `16*****84`（=******，用户当前登录）；测试终端 `C:\AIQuant\mt5_instances\fxtm_demo_01`（PID 36460）。
> 结论: **第 1 次尝试被终端拒绝(Algo Trading 关闭)；开启后第 2 次尝试成交并立即平仓。全程 V1 零影响、未重试、未加仓。**

## 两次尝试
| | attempt 1 | attempt 2 |
|---|---|---|
| 时间(UTC) | 12:55:12 | 12:56:32 |
| 结果 | **REJECTED** | **EXECUTED** |
| retcode / comment | `10027` / "AutoTrading disabled by client" | `10009` / "Request executed" |
| 原因 | 终端 Algo Trading 关闭 | Algo Trading 已开 |
| 成交 | 无 | 有 |

## A. Order (attempt 2)
```
order_sent: 1        order_id: ******    deal_id: 2362491534    position_id: (已即时平仓)
status: EXECUTED (retcode 10009)
```

## B. Entry (attempt 2)
```
request_time(utc):  2026-09-11T12:56:32.18Z
response_time(utc): 2026-09-11T12:56:33.02Z
RTT_ms:             649.218   (单次 order_send 端到端; 含终端IPC+broker, 不可再拆分)
Bid: 4391.60  Ask: 4391.73  Mid: 4391.67  Spread: 0.13 (≈0.296 bps)
requested_price:    4391.73
actual_fill:        4392.15
slippage_price:     +0.42     (BUY: fill - Ask_at_request; 正=更差)
slippage_bps:       +0.9563
```

## C. Exit (attempt 2)
```
close_RTT_ms:       583.525
requested_exit:     4392.24   (exit reference = Bid)
actual_exit:        4392.24
close_retcode:      10009 "Request executed"   close_order ****** / deal 2362491537
```

## D. Costs (attempt 2)
```
entry_spread:  0.13 (0.296 bps)     exit_spread: 0.14
entry_slippage:+0.42 (0.9563 bps)   exit_slippage: +0.09 (≈0.20 bps)
commission: -0.22 USD (0.01 手往返) swap: 0     other: 0
gross_pnl: +0.09 USD (price-based)
net_pnl: +0.09 USD (broker deals sum(profit); 未含 commission)
net_pnl_corrected: +0.09 - 0.22 = -0.13 USD (gross + commission + swap)
```

## E. Broker behavior
```
retcode: 10009 "Request executed"  (attempt1: 10027 AutoTrading disabled)
execution_mode: market FOK; 未拒单(成交)
```

## F. Safety 证明
```
V1 PID 1348 unchanged = PASS
V1 data directory untouched = PASS
test account = DEMO (trade_mode=0, server ForexTimeFXTM-Demo01) = PASS
orders_sent = 1 (成交) ; attempt1 rejected 未重试 = PASS
open_positions_after_test = 0 = PASS
credentials_not_logged = PASS (仅环境变量; 记录已扫描 0 泄露)
```

## G. Paper Engine 校准对比（n=1，仅观察，不得据此定长期参数）
```
                Paper 默认        FXTM Demo 实测(本次)
spread          0.35 bps          0.296–0.32 bps   (同量级, Paper 略保守)
slippage        0.30 bps          0.96 bps(入) / 0.20 bps(出)  ← 入方向明显更大
latency/RTT     250 ms            649 ms(下单) / 584 ms(平仓)   ← 实测远大于假设
commission      —                 0.22 USD / 0.01 手往返
```
- ⚠️ **n=1**：不得声称已证明长期平均 slippage/latency。本次仅说明 **Paper 的 250ms 延迟假设偏乐观**、**入场滑点可能远大于 0.30bps**（含 RTT 期间的价格漂移）。
- **未修改 Paper Engine。**

## 原始记录
`state/demo_calibration/phase2/`: `order_request.json` · `order_response.json` · `close_request.json` · `close_response.json` · `summary.json`（attempt 2 成交）；`attempt1_rejected.json`（attempt 1 拒绝）。

## 备注
- 环境变量 `FXTM_DEMO_LOGIN` 仍是 `16*****24`(******)，与当前使用的 `******` **不一致** → 需要更新时请示下（本实验采用"只附加不登录"，故未受影响）。
- 交易模块保持 disabled；未进入任何后续模块/自动执行/Live。

## 最终状态
`FXTM_DEMO_CALIBRATION_PHASE2_COMPLETE`（1 单成交 + 立即平仓；orders_sent=1, open=0；V1 零影响）。
