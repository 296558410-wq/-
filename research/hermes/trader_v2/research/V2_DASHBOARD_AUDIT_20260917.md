# V2 DASHBOARD AUDIT — 20260917 (P1-D)

## 问题
- Dashboard 把 `BROKER_DEMO` 显示为 `PAPER / 虚拟账户`（README "只读·PAPER"）；sizing 遥测用**硬编码 $10,000**；account fallback 伪造 `realized_pnl=0.0`。

## 修改
- `dashboard/datasource.py`：
  - `_sizing_rows(base_equity=None)`：base equity 来自**实际账户**（ledger ACCOUNT_SNAPSHOT / account）；缺失 → `equity_base_missing=True` 且不伪造 target_risk。
  - 新增 `snap["mode_info"]`：`run_mode / execution_mode / broker / account_type / instrument / reference_market / data_source / router_enabled / price_space_enabled / pit / health`。
  - account fallback → `realized_pnl=None` + `fallback=True`（不再伪造 0）。
- `dashboard/static/app.js`：移除 `虚拟账户` / `Paper 账户` / `Paper Equity`；ID 用真实 execution_mode + account_type；MODE chip 对 BROKER_DEMO 不再判 'bad'。

## 校验
`tests/test_dashboard_consistency.py` 12/12。

## 遗留
- Dashboard 仍每≤30s 起 MT5 只读子进程（与“不触网”表述不符，P2；本阶段只改一致性，未改探测）。
- `v1_isolated`/`execution.ok` 等仍为硬断言（P3）。
