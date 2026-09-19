# REGRESSION_REPORT — V2 回归（数据加固后）

- 时间: 2026-09-14（GMT+8） |  改动前 BASE_COMMIT: `fb64d17`
- 结论: **既有断言无一削弱，全部 PASS。**

## 新增测试
- `tests/test_data_sources.py` → **37/37 PASS**（routing / 确定性 fallback / cache·freshness / validation /
  timeout·retry·backoff·cooldown·recovery / PIT·no-future / 失败注入 / 断源演练 / V1·broker·ledger·replay 隔离 / health）。

## 既有 V2 测试套件（全部 PASS）
| 测试 | 结果 |
|---|---|
| test_demo_calibration_readonly.py | 5/5 PASS |
| test_event_trigger.py | 10/10 PASS |
| test_ledger_replay.py | 12/12 PASS |
| test_module4_loop.py | 12/12 PASS |
| test_module5_paths.py | 13/13 PASS |
| test_module5_shadow.py | 15/15 PASS |
| test_module6_broker_demo.py | 19/19 PASS（FakeAdapter，离线，不触 broker）|
| test_opportunity_engine.py | 10/10 PASS |
| test_paper_execution.py | 12/12 PASS |
| test_paper_final_validation.py | MODULE 2 FINAL: PASS |
| test_pit_integrity.py | 5/5 PASS |
| test_research_compute.py | 26/26 PASS |
| test_sizing_floor.py | 34/34 PASS |

**13/13 文件 PASS + 新增 37/37。**

## 生产影响
- 生产默认 `V2_DATA_ROUTER_ENABLED=false` → Agent1/Agent2 仍走 **旧路径**（本 run 7a88 不受影响）。
- 改动仅在“数据获取/路由/缓存/新鲜度/超时退避/校验/适配层”，**未触** Hermes 决策/prompt/阈值/sizing/risk/执行器/ledger/replay/GPU。
- **ORDERS_PLACED = 0**（无任何下单代码/调用）。**STRATEGY_CHANGED = NO**。
