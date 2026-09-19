# V2 — 启用「模拟盘真实下单」(BROKER_DEMO) — 2026-09-18

- 触发: 用户指令「现在给我开起来」（此前确认要把 V2 从 Shadow/Paper 切到 模拟盘真实下单）。
- 性质: **显式放宽安全姿态**（撤销 2026-09-18 早间的 BROKER_DEMO disarm）。**仍然 demo、非实盘**（`live_trading=false` 硬锁）。
- 目标场所: FXTM 模拟盘 `fxtm_demo_01`（终端 tag 校验），账号 ********** / server `ForexTimeFXTM-Demo01`，magic **90003**。

## 1. 变更前后
| 项 | before | after |
|---|---|---|
| config SHA256 | `01bc3b8b4585b8fb2f824de83a98530c5f493411378d02b85fb0f1c3088af6b3` | `b0cc254b809da52844778bbbb8a298df77dd2d031a8353fec3f982dac26be0e5` |
| `execution.backend` | `paper_local` | `fxtm_demo` |
| `execution.execution_mode` | `PAPER` | `BROKER_DEMO` |
| `execution.broker_demo_enabled` | `false` | `true` |
| `broker.enabled` | `false` | `true` |
| `execution.live_trading` | `false` | `false`（不变） |
| `risk.per_trade_pct` | `1.0` | `1.0`（不变，保留 F3 修复） |
| `state/FORWARD_VALIDATION_ALLOWED` | 不存在 | `true`（开 forward 门） |

## 2. Run 编排
- 旧 shadow run `V2-SHADOW-20260917-105319-b5e4` → **finalize 存档**（status STOPPED；90 轮；TRADE 8 / exec_executed 5 / rejected 3；ledger 220 事件 verify=True）。**未删、未改历史**。
- 新 run：**`V2-PAPER-20260918-102531-8648`**（`RUN_META.shadow=false`，`execution_mode=BROKER_DEMO`，48h→2026-09-19T10:25Z）。
- ACTIVE 单槽已切到新 run；Windows 任务 `hermes-v2-cycle` 每 15m 驱动。

## 3. 验证（启用时，只读）
- `execution_mode=BROKER_DEMO`、`broker_demo_enabled=true`、`broker.enabled=true`、`live_trading=false`。
- `assert_execution_allowed()` = **PASS**。
- 适配器连接实测：`{"ok":true,"login":******,"server":"ForexTimeFXTM-Demo01","demo":true}`，余额 $1024.03。
- MT5 只读行情不受影响（F2 解耦）：`a1_src=mt5`。
- 硬门保留：适配器强制 `fxtm_demo_01` 终端 / DEMO 账户 / 指定 server；`BrokerDemoExecutor._guard` 要求 BROKER_DEMO 且 `live_trading=false`。

## 4. 首个 BROKER_DEMO 周期结果
- 10:45Z: TRADE → **EXECUTED** → `ORDER_ACCEPTED` order ********** → `POSITION_OPEN`。
  - FXTM Demo 真实持仓：**XAUUSD SELL 0.01 @4376.46, SL 4411.13, TP 4365.45, magic 90003**。
- 11:00Z: TRADE → `REJECTED:POSITION_BUSY`（单仓约束，正常）。
- 其后 WAIT。run 健康：RUNNING / blocked=null / replay MATCH / ledger verify=True。
- 注：broker 模式 sizing 以 broker 权益（~$1024）为基 → 1% 风险 ≈ 0.01 手（paper 模式是按 $10000 → 0.05 手）。

## 4b. 面板显示 BUG 修复（2026-09-18 晚）
现象：面板“当前持仓”显示“无”、“真实下单”显示“否”，但实际已有 demo 持仓。
- 根因: (1) `datasource` 的 `position.list` 是**整数计数**，而 `app.js` 用 `(p.list||[]).length` → 整数无 `.length` → 永远“无”；(2) `real_orders` 仅按 run-id 前缀判定（`V2-PAPER-` → “否”），未看 `execution_mode`。
- 修复（仅 dashboard 显示层，不动引擎/策略）:
  - `static/app.js`：持仓计数兼容 int/array；shadow 卡片文案按是否真实下单切换。
  - `datasource.py`：`real_orders`/`run_mode`/执行条文案改为按 `manifest.execution_mode`（BROKER_DEMO → “是（FXTM 模拟盘）”/“模拟盘真实下单(BROKER_DEMO)”）。
- 通过 supervisor（`v2_dashboard_supervisor.cmd`，自动重启）只重启 dashboard 子进程加载新代码；未动 V1。
- 修复后 `/api/snapshot`：`real_orders=是（FXTM 模拟盘）`、`run_mode=模拟盘真实下单(BROKER_DEMO)`、`position.list=1`。

## 5. 如何回退（一键）
1. `config/v2_config.json`：`execution_mode=PAPER`、`broker_demo_enabled=false`、`broker.enabled=false`、`backend=paper_local`；
2. 删除 `state/FORWARD_VALIDATION_ALLOWED`；
3. finalize 当前 run，`shadow_run.py shadow-start` 开新的 shadow run。

## 6. 监控
- 只读 observer cron `v2-longrun-observer`（15m）已更新：现按 `BROKER_DEMO` 期望值巡检；若 `live_trading!=false`、模式漂移、ledger 异常、或出现 TRADE → 告警。
- 日志：`memory/v2_audit_2026-09-18.jsonl`。
