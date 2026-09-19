# Phase 3 跨期复验：同一冻结 69 假设

- 2026 窗口：FXTM M1 2026-05-26 03:43:00+00:00 → 2026-09-04 11:22:00+00:00（100k bars）
- 2023-24 窗口：DUKA M1 2023-09-01 00:00:00+00:00 → 2024-03-16 23:59:00+00:00（229k bars）
- 2026 funnel: raw 39 / FDR 37 / SUPPORTED 0
- 2023-24 funnel: raw 38 / FDR 35 / SUPPORTED 0

## 两期均显著(FDR)且方向一致

| hypothesis | IC 2026 | IC 2023-24 |
|---|---|---|
| H4_volatility_02_atr_14_h60 | 0.6191 | 0.8895 |
| H4_volatility_01_vol_30_h60 | 0.5720 | 0.8663 |
| H4_volatility_03_rvol_60_h60 | 0.5383 | 0.8937 |
| H4_volatility_02_atr_14_h240 | 0.2536 | 0.7862 |
| H4_volatility_01_vol_30_h240 | 0.2401 | 0.7961 |
| H4_volatility_03_rvol_60_h240 | 0.2166 | 0.7639 |
| H4_volatility_04_vol_ratio_15_60_h60 | 0.1650 | 0.5487 |
| H4_volatility_04_vol_ratio_15_60_h15 | 0.1341 | 0.5975 |
| H10_multi_timeframe_02_h1_vol_ratio_h15 | 0.0615 | 0.5759 |
| H6_session_02_hour_h60 | 0.0433 | 0.0257 |
| H5_trend_regime_03_trend_str_h240 | 0.0393 | 0.0960 |
| H10_multi_timeframe_02_h1_vol_ratio_h60 | 0.0231 | 0.5625 |
| H3_breakout_03_dist_lo_60_h60 | 0.0179 | 0.0659 |
| H5_trend_regime_03_trend_str_h60 | 0.0131 | 0.0620 |

## 方向反转或消失的重点项

- H10_multi_timeframe_02_h1_vol_ratio_h240: 2026 IC=-0.0970 → 2023-24 IC=0.4568
- H1_momentum_03_mom_20_h15: 2026 IC=0.0159 → 2023-24 IC=-0.0478
- H2_mean_reversion_01_zscore_60_h15: 2026 IC=0.0115 → 2023-24 IC=-0.0423

## 分 family 方向一致率

| family | 两期都显著对数 | 方向一致数 |
|---|---|---|
| H10_multi_timeframe_02_h1_vol_ratio_h15 | 1 | 1 |
| H10_multi_timeframe_02_h1_vol_ratio_h240 | 1 | 0 |
| H10_multi_timeframe_02_h1_vol_ratio_h60 | 1 | 1 |
| H1_momentum_03_mom_20_h15 | 1 | 0 |
| H2_mean_reversion_01_zscore_60_h15 | 1 | 0 |
| H3_breakout_03_dist_lo_60_h60 | 1 | 1 |
| H4_volatility_01_vol_30_h240 | 1 | 1 |
| H4_volatility_01_vol_30_h60 | 1 | 1 |
| H4_volatility_02_atr_14_h240 | 1 | 1 |
| H4_volatility_02_atr_14_h60 | 1 | 1 |
| H4_volatility_03_rvol_60_h240 | 1 | 1 |
| H4_volatility_03_rvol_60_h60 | 1 | 1 |
| H4_volatility_04_vol_ratio_15_60_h15 | 1 | 1 |
| H4_volatility_04_vol_ratio_15_60_h60 | 1 | 1 |
| H5_trend_regime_03_trend_str_h240 | 1 | 1 |
| H5_trend_regime_03_trend_str_h60 | 1 | 1 |
| H6_session_02_hour_h60 | 1 | 1 |