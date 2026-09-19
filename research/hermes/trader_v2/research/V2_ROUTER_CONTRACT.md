# V2 ROUTER CONTRACT (P0-02)

## 定位
```
V2 Scheduler → V2 Data Router → Agent1 / Agent2 → Hermes
```
Router 是 V2 **唯一数据源决策层**：source discovery / priority / fallback / timestamp / freshness / PIT / quality / failure / audit。
Agent1/Agent2 **不得自行换源绕过 Router**。

## 开关（唯一）
- 唯一来源：`config/data_router.enabled` 标记文件。
- 环境变量 `V2_DATA_ROUTER_ENABLED` 仅作**显式覆盖**；scheduler **不再隐式 setdefault**（已移除 hidden override，见 `runtime/v2_scheduled_cycle.py`）。
- 生产要求 enabled=true。

## Audit（每次 source 选择）
记录：`request_id(隐含 logged_at)`、`field`、`requested_symbol`、`selected_source`、`candidate_sources`、
`selection_reason`、`data_timestamp`、`received_at`、`pit`、`freshness`、`quality`、`fallback_level`、`error`
（写 `data_cache/router_audit.jsonl`；限速聚合见 `audit.py`）。

## V2 / V1 数据隔离
- V2 **不读取** V1 的 run_state / ledger / decision state / cache（代码级断言见 `tests/test_router_contract.py`）。
- V2 的技术 bars 来自 `local_fxtm`（`C:\AIQuant\data\live_fxtm` tick）。按任务书 §10：**共享底层 tick feed 允许**，
  只要 V2 不依赖 V1 的状态性运行结果——当前满足；V2 独立 ledger/state/account/terminal。
- 遗留（记录）：如未来要求 V2 完全自有采集，可加 `market_data.tick_dir` 指向 V2 专属目录 + 独立采集器（本阶段未做）。

## 校验
`tests/test_router_contract.py`。
