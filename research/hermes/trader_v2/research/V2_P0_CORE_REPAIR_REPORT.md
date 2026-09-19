# V2 P0 CORE REPAIR REPORT — 20260917

阶段: 仅 P0-01/02/04/05。**不进入 shadow/forward/alpha**。`FORWARD_VALIDATION_ALLOWED=NO`。

## 汇总
| P0 | 结论 | commits |
|---|---|---|
| P0-01 标的统一 | 完成（代码/配置/测试/契约） | `6f67f1f` |
| P0-02 Router 唯一入口 | 完成 | `359e495` (+`b002054` 认证门) |
| P0-04 Freshness+Health | 完成 | `8b6f064` |
| P0-05 Cache AS-OF | 完成 | (本 commit) |

## P0-01 — Instrument / Price Space
- **问题**: 配置/决策/manifest 声明 GC=F；router 实跑 `local_fxtm`(XAUUSD)。`agent1.price_basis.primary="GC=F@yahoo"`、`data_quality.sources.history="yahoo"` 为谎；`decision.instrument="GC_F"`；router fallback 会把 XAUUSD 换成 GC=F 期货。
- **根因**: 历史 Phase-1 以 GC=F 代理，后切 router 未同步语义。
- **修改**: `v2_config`(instrument_marking/market_data → XAUUSD, reference_instrument=GC=F)、`agent1`(primary=XAUUSD@{src}, 诚实 source)、`context/hermes/agent2`(instrument=XAUUSD, reference_market=GC=F)、`router`(fallback→XAUUSD=X)、`price_space`(重定义 XAUUSD source-basis, 仍 disabled)。
- **测试**: `test_instrument_contract` 19/19。
- **行为变化**: `BEHAVIOR_CHANGE=TRUE`（context_hash 因 market.instrument 变化；decision.instrument 值变化）。**非策略**。
- **遗留**: 旧 per-run 历史 manifest 仍写 "yahoo GC=F"（历史不重写）。

## P0-02 — Router 唯一数据入口
- **问题**: 文档称 router 默认 OFF/legacy，实跑 ON；`v2_scheduled_cycle` 隐式 `setdefault(V2_DATA_ROUTER_ENABLED)`（hidden override）。
- **修改**: 移除隐式 override（唯一开关=`config/data_router.enabled`）；`data_sources/__init__` 文档改为“唯一数据入口”；router audit 增 `field/requested_symbol/candidate_sources/selection_reason/pit/quality`。
- **测试**: `test_router_contract` 13/13（含 V1 数据隔离断言）。
- **遗留**: V2 仍读 `data/live_fxtm`（V1 采集的**原始 tick feed**）。按 §10 允许共享底层 feed；V2 不读 V1 run_state/ledger/state。完全自有采集留待后续（`market_data.tick_dir` 可配）。

## P0-04 — Freshness + Health
- **问题**: freshness 基于 `generated_utc`（快照生成时刻）→ 全源失败仍 "fresh"；`health.build_report` 未接入决策。
- **修改**: `context` 以 **data_ts** 计龄（`_fresh_from_data_ts`，未来 ts→unknown）；新增 `build_health`（overall/technical/macro/router/pit/freshness/price_space/broker）；`ctx.freshness`/`ctx.health`；`hermes.gate` 增 G2：health FAIL→REJECT、DEGRADED→WAIT。
- **测试**: `test_freshness_health` 16/16。
- **行为变化**: `BEHAVIOR_CHANGE=TRUE`（数据降级/缺失 → WAIT/REJECT）。**非策略**。
- **遗留**: broker_status 仍 `UNKNOWN`（P0 范围外）。

## P0-05 — Cache AS-OF / PIT
- **问题**: 旧 `cache.py` 单槽 last-write-wins，无 as-of。
- **修改**: 新增 `data_sources/pit_cache.py`（append-only `data_cache/pit_store.jsonl`，含 data_ts/received_ts/source/source_hash/schema_version；`get_asof` 严格 `<=decision_ts`）；router 成功取数写入记录。
- **测试**: `test_pit_cache` 11/11（future/late-received/missing/dup/diff-source/invalid）。
- **遗留**: 旧 `cache.py` 仍在用（router fallback）；BLS/COT publication-time 未强制（P1）。

## 风险 / 说明
- 本阶段未改策略（candidate/priority/threshold/SL/TP/频次均未动）。
- 所有新增数据质量门均为 fail-closed。
- 未触碰 V1；未动历史 run/ledger/run_state；未下单。
