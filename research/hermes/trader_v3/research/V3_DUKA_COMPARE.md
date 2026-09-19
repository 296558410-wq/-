# V3 — MT5 vs DUKA 对照 — 2026-08-03

- DUKA: `candles_202608.parquet` rows=8640 bid_rows=4320 (price/1000)
- MT5 XAUUSD M1: 服务器时间偏移搜索 -4..5h
- 结果: `{"server_offset_h": -4, "n_matched_min": 3405, "mean_abs_diff_usd": 337.989, "max_abs_diff_usd": 451.995, "p50_abs_diff_usd": 324.365}`
- **verdict: DATA_GAP — 价格偏差过大**

> 注：MT5 bar 时间为 broker 服务器时间(通常 GMT+2/+3)，非 UTC；对照需考虑偏移。
> tick 级逐笔对照：DUKA 最新 tick = 2026-08-04，MT5 当前窗口无重叠 → TICK_OVERLAP=DATA_GAP。
