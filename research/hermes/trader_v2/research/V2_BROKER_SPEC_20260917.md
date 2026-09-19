# V2 BROKER SPEC — 20260917 (P1-C)

- generated: 2026-09-17T02:01:29.519183+00:00
- instance: fxtm_demo_01 / symbol XAUUSD (V2 independent)
- **verified = True**   note: 

## 实测 (MT5 symbol_info, live)

| field | value | source | retrieval_ts | verified |
|---|---|---|---|---|
| digits | 2 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| point | 0.01 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| tick_size | 0.01 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| tick_value | 0.1 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| contract_size | 100.0 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| volume_min | 0.01 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| volume_step | 0.01 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| volume_max | 100.0 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| stops_level | 0 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| freeze_level | 0 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| filling_mode | 1 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |
| execution_mode | 2 | MT5 symbol_info | 2026-09-17T02:01:29.519183+00:00 | True |

## config 假设 (供对照, 非实测)

| field | config value |
|---|---|
| min_lot | 0.01 |
| max_lot | 0.05 |
| contract_size_oz | 100 |
| price_dp | 2 |
| lot_dp | 2 |
| leverage | 500 |

## 说明
- 实测优先；config 仅对照。未取得字段标 UNVERIFIED（不假设）。
- 本脚本不发单（BROKER_ORDER_SENT=FALSE）。
