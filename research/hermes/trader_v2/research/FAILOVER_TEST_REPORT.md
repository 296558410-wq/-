# FAILOVER_TEST_REPORT — 断源/断网演练（只读，不触 broker）

- 时间: 2026-09-14T11:14:31.268033+00:00
- 场景: 强制注入 Yahoo 403 + 新浪失败 + 东方财富失败 + 全部外部宏观源失败；只保留本地 tick。

| 检查 | 结果 |
|---|---|
| 本地 XAUUSD 技术层 15m | **OK**（src=local_fxtm, n=484）|
| 现价 gold_comex（无本地兜底）| None price=None（预期 missing/None）|
| 宏观 COT（有 last_valid）| returned last_valid (noncommercial_net=123456) |
| 不崩溃 | **OK**（无异常穿透）|
| Broker Demo 订单 | **0**（本模块无任何下单代码/调用）|

结论: 外部全挂时，**本地技术层照常出 K 线**；现价无本地源则诚实缺省；宏观进入 **STALE_BUT_VALID / SOURCE_DOWN**，绝不臆造、绝不下单。