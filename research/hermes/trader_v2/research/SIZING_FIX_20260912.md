# V2 SIZING FIX — design ruling & landing (2026-09-12)

> 状态：**APPLIED**。范围仅限 sizing 取整；未改策略/阈值/成本/风控/账户/数据。
> 记录时间：2026-09-12T23:20Z（本地 2026-09-12 07:20 GMT+8）

## 0. 审计结论（前置）
- 上一轮只读审计判定：**DESIGN_DECISION_REQUIRED**。
- 关键事实：sizing 使用 round-nearest，可向上取整；max_lot 为硬拒绝（不 clamp）；
  风险保证由事后 risk 校验以"拒绝"达成，而非由 sizing 保证；round-up 造成死区与系统性拒单。

## 1. 正式裁定（本次落地）
```
max_lot   = HARD_REJECT     # qty > max_lot -> REJECT:RISK_LIMIT, 禁止 clamp
rounding  = FLOOR_TO_STEP   # floor(raw / step) * step,  step = 0.01 (lot_dp=2)
```
校验顺序：`raw → floor-to-step → min_lot → max_lot → notional → risk`。

## 2. 修复
- 文件：`execution/paper_executor.py`
  - 仅改 `_lots()`：`round()`（最近邻）→ `math.floor()`（向下到 step）
  - 新增 `import math`
  - `size_position_raw()` 调用点不变（两处：显式 qty 透传、equity 计算）
- 未改：min_lot/max_lot/notional/risk 语义、cost model、账户、ledger、replay、hermes、agents、context、freshness、config。

### 版本链
```
base_commit   e4c9ba2ec2ee6b3325033a0c225a8a4f5b22adeb
fix_commit    e1a3517ab725985417c75a08968ac6675517aced
changed       execution/paper_executor.py (+6/-1)
              tests/test_sizing_floor.py (new, 209 行)
config_hash   eec4330cbf6c1a826340e1859adeafef183663a8ab3233c3077d22e16dabfd81 (未变)
```

## 3. 语义证明
- `qty = floor(raw)` ⇒ `qty ≤ raw` ⇒ `actual_risk = qty·dist·contract = qty·dist·100 ≤ raw·dist·100 = target_risk`。
- 因此 **ACCEPT ⇒ actual_risk ≤ max_risk_usd (+tol)**；且 `max_lot` 仍为硬拒绝，绝不放宽到 0.05。
- 单调性：dist↑ ⇒ raw↓ ⇒ floor(raw) 非增；无反向跳变。
- 方向对称：sizing 只用 `abs(entry−sl)`，与方向无关。

## 4. 测试
### 4.1 sizing 专项（`tests/test_sizing_floor.py`）22/22 PASS
```
C01 dist=20.00 raw=0.05  -> 0.05 ACCEPT risk=100.00
C02 dist=17.74 raw≈0.0564 -> 0.05 ACCEPT risk=88.70   (历史信号)
C03 dist=17.73 raw≈0.0564 -> 0.05 ACCEPT risk=88.65
C04 raw=0.049 -> 0.04 ACCEPT
C08 raw=0.045 -> 0.04 ACCEPT
C11 raw=0.025 -> 0.02 ACCEPT
C12 raw=0.015 -> 0.01 ACCEPT
C14 dist=101 raw=0.0099 -> 0.00 -> REJECT:RISK_LIMIT(min_lot)
C15 dist=250 -> REJECT:RISK_LIMIT(min_lot)
MAXLOT raw=0.0625 -> 0.06 -> REJECT:RISK_LIMIT(max_lot)  # 不 clamp 到 0.05
PASSTHRU qty=0.06 -> REJECT(max_lot) ; qty=0.05 -> ACCEPT
§六 1200 随机案例: ACCEPT=209 REJECT=991, 全部 actual_risk<=target (worst_excess=0)
§六 对照: round-nearest 存在 133 个超风险点 (证明修复必要)
§七 单调性 dist↑=>qty 非增 (1..400 step .01) + 4 窗口
§八 LONG sizing == SHORT sizing
```
### 4.2 全量回归
```
module2 execution            12/12 PASS
module4 loop                 12/12 PASS
module5 shadow               15/15 PASS
module5 paths                13/13 PASS
ledger_replay                12/12 PASS
opportunity_engine           10/10 PASS
sizing_floor                 22/22 PASS
```
**既有失败（与本次无关，HEAD 基线同样失败，已核验）：**
```
test_paper_final_validation  [E v1 isolation]  (fxtm_demo_calibration.py / fxtm_demo_one_shot.py 含 trader_v1/live_fxtm 关键字) — 预先存在
test_pit_integrity           PIT value_asof (T0 sees pre-revision) — 预先存在（数据/PIT）
test_event_trigger           url content update -> new version — 预先存在（网络/数据）
```
未删除/未弱化任何既有断言。

## 5. 历史 Run 保护（未触碰）
```
V2-PAPER-20260911-132414-2684   INVALID_FOR_DECISION_ALPHA / FRESHNESS_INPUT_PATH_DEFECT  (保持)
V2-PAPER-20260911-133224-a17b   运行中(24h 至 2026-09-12T13:32Z); ledger/历史事实未改; 两笔历史 TRADE 未补成交
```

## 6. 新 Run（隔离、修复后）
- 冻结（启动前记录）：`base_commit=e4c9ba2`，`code_commit=e1a3517`（HEAD，本文档 docs 提交延后到任务结束一并提交，故 HEAD 现即 e1a3517），`config_hash=eec4330c…fd81`。
- 受 ACTIVE 单槽 + "不得扰乱既有 Run" 约束：新 run 在既有 run 的 24h 窗口结束后自动启动
  （计划 2026-09-12T13:45:00Z；既有 run 于 13:32Z 到期、13:37Z 周期自动 finalize）。
- 启动前预检：HEAD==e1a3517 且 config_hash==eec4330c…fd81，否则 RUN_BLOCKED 不启动。
- 参数：`--minutes 1440`（24h）；execution_mode=PAPER；broker.enabled=false；broker_demo_enabled=false；live_trading=false。
- 冻结：code_commit(=fix commit)、config_hash、strategy/agent/hermes/paper/ledger versions、start/end。
- 自动 finalize + A/B/C 验收：计划 2026-09-13T14:05:00Z。
- **不自动进入 Broker Demo / Live；不自动开始下一模块。**
