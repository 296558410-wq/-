# V2 P1 REPAIR REPORT — 20260917

阶段: P1 验证可信度与执行安全。未启动 Shadow/Forward；`FORWARD_VALIDATION_ALLOWED=NO`。

| 模块 | 结论 | commit | 测试 |
|---|---|---|---|
| P1-G Forward gate 硬化 | PASS | `7284f10`,`7071939` | test_forward_gate 7/7 |
| P1-A Macro PIT | PASS | `9c6d539` | test_macro_pit 15/15 |
| P1-C Broker spec + precheck | PASS | `d364f5d` | test_broker_validate 9/9 |
| P1-D Dashboard | PASS | `cc539d3` | test_dashboard_consistency 12/12 |
| P1-B Replay input snapshot | PASS | `e0f2a6a` | test_replay_snapshot 11/11 |
| P1-E LLM/Token audit | PASS | `0e33811` | test_llm_independence 7/7 |
| P1-F Failure injection | PASS | `0e33811` | test_failure_injection 13/13 |

## P1-A 宏观 PIT
问题: BLS/COT 发布时刻未强制、ETF flow as-of 丢弃、news 失败静默、completeness 不清。
修改: `agent2` 增 `macro_field_status/news_source_status/macro_completeness`；`macro.completeness`、`macro.news_status`、`macro.macro_pit_risk`；新闻失败计入 `data_gaps`；`cot.pit_status`、`etf.asof/publication_ts/pit_status`；`TRADE_CRITICAL_MACRO=(DXY,UST10Y,VIX)`。
行为变化: `BEHAVIOR_CHANGE=TRUE`（news 失败现可见）。

## P1-C Broker
实测（V2 独立实例 fxtm_demo_01，只读）：digits=2, tick=0.01, contract=100, vol_min=0.01/step=0.01/max=100, stops_level=0, freeze=0, filling=1, exec=2。
新增 `execution/broker_validate.precheck_order`；`BrokerDemoExecutor.open()` 发送前预校验（方向边/市价一侧/stops_level/tick）→ 失败 `PRECHECK_REJECT`（不下单，杜绝 10016）。
**BROKER_ORDER_SENT=FALSE**（spec probe 只读）。

## P1-D Dashboard
`mode_info`（run_mode/execution_mode/broker/account_type/instrument/reference_market/data_source/router/price_space/pit/health）；`_sizing_rows` base_equity 来自实际账户（缺→显式缺失，不伪造）；account fallback 不再伪造 0；app.js 去 `虚拟账户/Paper`。

## P1-B Replay snapshot
`hermes.decide_pure`（无副作用，共用路径）；`runtime/replay_inputs.py`（build_snapshot + write `<run>/inputs/<dec>.json` + offline_replay）；fail-closed（missing/schema/hash/wrong instrument/invalid ts），**绝不联网**。

## P1-E LLM 审计
STATIC/PROCESS/NETWORK/RUNTIME/FALLBACK 全 PASS；运行时无 LLM SDK/endpoint/key；live=reference_rules。

## P1-F Failure injection
13 类注入全部 fail-closed（SEE `V2_FAILURE_INJECTION_REPORT_20260917.md`）。

## 回归
**FULL_REGRESSION = 31/31 PASS**（含 ledger/replay/module5/v2_repair/broker_reconcile/dxy/data_sources 等）。

## 行为变化
`BEHAVIOR_CHANGE=TRUE`（数据质量 + 执行安全 + gate 硬化）；`STRATEGY_CHANGED=FALSE`（策略/候选/阈值/SL/TP/频次未动）。

## 遗留（转 Shadow/后续）
- replay `input_hash` 现等同 context_hash（可并入 pit_cache source_hash）。
- broker 真实 dry-run 的 OS 级抓包 / process-tree 复核（Shadow 阶段）。
- dashboard 仍含 MT5 只读探测 + 少量硬断言（P2/P3）。
- BLS/COT 精确 publication time 仍无源（标注 PIT_RISK）。

## 无害第三方提交
`068b0c4 hermes: V3 unified plan…` 为**并发写入者**（非本任务）提交，仅新增 research 文档，不影响本阶段代码/测试。
