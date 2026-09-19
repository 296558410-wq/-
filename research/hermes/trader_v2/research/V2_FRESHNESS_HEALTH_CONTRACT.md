# V2 FRESHNESS & HEALTH CONTRACT (P0-04)

## Freshness
- **定义**: `age = now - data_ts`（**data_ts = 数据自身时刻**）；禁止 `now - snapshot_ts`。
- 字段: Agent1 data_ts = max(各 tf `last_bar_ts`)；Agent2 data_ts = max(核心宏观字段 `data_ts`)。
- 状态: `FRESH / STALE / MISSING / INVALID / SOURCE_ERROR / PIT_INVALID`（阈值 `FRESH_RULES`，与策略阈值分离）。
- 未来时间戳（age<-5s）→ `unknown`（不可信）；缺失 → `unknown`。
- 接口: `context._fresh_from_data_ts(epoch, kind)`；`context._a1_data_ts/_a2_data_ts`。

## Health
- `context.build_health(a1,a2,a1_fr,a2_fr,router_enabled)` →
  `{overall_status, technical_status, macro_status, router_status, pit_status, freshness_status, price_space_status, broker_status}`
  取值 `PASS/DEGRADED/FAIL`（price_space 当前 DISABLED）。
- 写入 `ctx["health"]` 与 `ctx["freshness"]`（含 data_ts/status/age）。

## Health → Gate（fail-closed）
```
overall FAIL     → REJECT (不交易)
overall DEGRADED → WAIT
overall PASS     → 继续
macro_status != OK → WAIT  (P0-03)
```

## 禁止（健康伪装）
`source failed→default` / `timestamp missing→now()` / `missing→NEUTRAL` / `stale→current` / `snapshot fresh→data fresh`。
`agent2.macro_status=DEGRADED` 不再退化为 NEUTRAL（见 P0-03）。

## 校验
`tests/test_freshness_health.py`、`tests/test_macro_failclosed.py`。
