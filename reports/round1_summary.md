# Phase 2 Round 1 — 真实 XAUUSD M1 结果

- dataset: `XAUUSD_M1_MT5-FXTM-Live_20260904_v001` · 2026-05-26 03:43:00+00:00 → 2026-09-04 11:22:00+00:00
- hypotheses tested: 69 · raw sig: 39 · **FDR sig: 37** · survivors: 37
- 耗时: 223.7s（info 21.9s）

## Survivors

| hypothesis | feature | label | IC_OOS | p | q | wf+ | ci95 |
|---|---|---|---|---|---|---|---|
| H1_momentum_03_mom_20_h15 | mom_20 | forward_return_15m | 0.0159 | 0.00125 | 0.00278 | 0.8 | [0.006494040363381758, 0.02652653387860272] |
| H1_momentum_03_mom_20_h240 | mom_20 | forward_return_240m | 0.02069 | 0.0 | 0.0 | 0.8 | [0.011273083615641617, 0.030722890271149203] |
| H1_momentum_04_mom_60_h60 | mom_60 | forward_return_60m | 0.02115 | 0.0 | 0.0 | 0.6 | [0.01148346944166388, 0.03190767376157706] |
| H1_momentum_04_mom_60_h240 | mom_60 | forward_return_240m | 0.02934 | 0.0 | 0.0 | 0.8 | [0.019784293031944428, 0.039944580183808996] |
| H2_mean_reversion_01_zscore_60_h15 | zscore_60 | forward_return_15m | 0.01149 | 0.02 | 0.03833 | 0.8 | [0.0030954564858382116, 0.021354629570945412] |
| H2_mean_reversion_01_zscore_60_h60 | zscore_60 | forward_return_60m | 0.01365 | 0.00625 | 0.01307 | 0.8 | [0.004267808109721287, 0.023188983608767585] |
| H2_mean_reversion_02_dist_mean_60_h60 | dist_mean_60 | forward_return_60m | 0.01792 | 0.0 | 0.0 | 0.8 | [0.008445567369938378, 0.02819584937013871] |
| H2_mean_reversion_03_dist_ema_60_h60 | dist_ema_60 | forward_return_60m | 0.02042 | 0.0 | 0.0 | 0.8 | [0.011256010624001715, 0.03105152823401804] |
| H3_breakout_01_breakout_60_h5 | breakout_60 | forward_return_5m | -0.01149 | 0.02125 | 0.03963 | 0.0 | [-0.021633174881087788, -0.0012403429483260125] |
| H3_breakout_03_dist_lo_60_h60 | dist_lo_60 | forward_return_60m | 0.01788 | 0.0 | 0.0 | 0.6 | [0.00826878517471792, 0.028413521761734856] |
| H4_volatility_01_vol_30_h60 | vol_30 | future_vol_60m | 0.57198 | 0.0 | 0.0 | 1.0 | [0.5644492165734623, 0.5790726351414083] |
| H4_volatility_01_vol_30_h240 | vol_30 | future_vol_240m | 0.24013 | 0.0 | 0.0 | 1.0 | [0.23086980837159252, 0.24916522784441159] |
| H4_volatility_02_atr_14_h60 | atr_14 | future_vol_60m | 0.61914 | 0.0 | 0.0 | 1.0 | [0.6120656201835312, 0.6256738161759601] |
| H4_volatility_02_atr_14_h240 | atr_14 | future_vol_240m | 0.25365 | 0.0 | 0.0 | 1.0 | [0.2445445605854333, 0.262509049116315] |
| H4_volatility_03_rvol_60_h60 | rvol_60 | future_vol_60m | 0.5383 | 0.0 | 0.0 | 1.0 | [0.5297336434207052, 0.5452124501487531] |
| H4_volatility_03_rvol_60_h240 | rvol_60 | future_vol_240m | 0.2166 | 0.0 | 0.0 | 0.8 | [0.20799966225776123, 0.22609127436511406] |
| H4_volatility_04_vol_ratio_15_60_h15 | vol_ratio_15_60 | future_vol_15m | 0.13409 | 0.0 | 0.0 | 1.0 | [0.12458299195591116, 0.144037599852437] |
| H4_volatility_04_vol_ratio_15_60_h60 | vol_ratio_15_60 | future_vol_60m | 0.16504 | 0.0 | 0.0 | 1.0 | [0.1545775579986721, 0.17409718508245473] |
| H5_trend_regime_01_sma_dist_60_h60 | sma_dist_60 | forward_return_60m | 0.01792 | 0.0 | 0.0 | 0.8 | [0.008445567369938378, 0.02819584937013871] |
| H5_trend_regime_01_sma_dist_60_h240 | sma_dist_60 | forward_return_240m | 0.02668 | 0.0 | 0.0 | 0.8 | [0.01637774790499267, 0.03681388655579209] |
| H5_trend_regime_02_ema_dist_60_h60 | ema_dist_60 | forward_return_60m | 0.02042 | 0.0 | 0.0 | 0.8 | [0.011256010624001715, 0.03105152823401804] |
| H5_trend_regime_02_ema_dist_60_h240 | ema_dist_60 | forward_return_240m | 0.02977 | 0.0 | 0.0 | 0.8 | [0.01924170637642957, 0.039831240533521446] |
| H5_trend_regime_03_trend_str_h60 | trend_str | future_vol_60m | 0.0131 | 0.0075 | 0.01522 | 0.2 | [0.0033044621924720047, 0.023348150170880454] |
| H5_trend_regime_03_trend_str_h240 | trend_str | future_vol_240m | 0.03925 | 0.0 | 0.0 | 0.8 | [0.02991464484927635, 0.04851080276936798] |
| H5_trend_regime_04_slope_60_h60 | slope_60 | forward_return_60m | 0.01428 | 0.005 | 0.01078 | 0.6 | [0.0046779422746633026, 0.024965866257503924] |
| H5_trend_regime_04_slope_60_h240 | slope_60 | forward_return_240m | 0.02311 | 0.0 | 0.0 | 0.8 | [0.0138722258841693, 0.033184059579111906] |
| H6_session_02_hour_h5 | hour | forward_return_5m | 0.01652 | 0.0 | 0.0 | 0.6 | [0.006918452117065171, 0.026616762563789878] |
| H6_session_02_hour_h60 | hour | forward_return_60m | 0.04328 | 0.0 | 0.0 | 0.8 | [0.033350548917166274, 0.05315321764103965] |
| H7_vol_x_momentum_02_mom_60_x_vol30_h60 | mom_60_x_vol30 | forward_return_60m | 0.02045 | 0.0 | 0.0 | 0.6 | [0.010779598894458583, 0.0307473366144909] |
| H7_vol_x_momentum_02_mom_60_x_vol30_h240 | mom_60_x_vol30 | forward_return_240m | 0.02507 | 0.0 | 0.0 | 0.6 | [0.014926438472346242, 0.03551015736953986] |
| H8_trend_x_vol_01_trend_str_x_vol30_h60 | trend_str_x_vol30 | forward_return_60m | 0.02065 | 0.0 | 0.0 | 0.8 | [0.010794980439244156, 0.03171417188484914] |
| H8_trend_x_vol_01_trend_str_x_vol30_h240 | trend_str_x_vol30 | forward_return_240m | 0.02458 | 0.0 | 0.0 | 0.6 | [0.014491464305753944, 0.03487717398043119] |
| H9_range_x_momentum_02_mom_60_x_compression_h60 | mom_60_x_compression | forward_return_60m | 0.02302 | 0.0 | 0.0 | 0.6 | [0.013375712517514786, 0.03339996710575759] |
| H10_multi_timeframe_02_h1_vol_ratio_h15 | h1_vol_ratio | future_vol_15m | 0.06147 | 0.0 | 0.0 | 1.0 | [0.05240717420327512, 0.07097443876574958] |
| H10_multi_timeframe_02_h1_vol_ratio_h60 | h1_vol_ratio | future_vol_60m | 0.02307 | 0.0 | 0.0 | 1.0 | [0.013444873070114664, 0.03185827733422703] |
| H10_multi_timeframe_02_h1_vol_ratio_h240 | h1_vol_ratio | future_vol_240m | -0.09704 | 0.0 | 0.0 | 0.2 | [-0.1066000460502958, -0.08657068731870673] |
| H10_multi_timeframe_03_h1_breakout_h60 | h1_breakout | forward_return_60m | 0.01182 | 0.02 | 0.03833 | 0.6 | [0.0016693231284435129, 0.02218015521767865] |

## Alpha Registry

- `H1_momentum_03_mom_20_h15_v001` → **EDGE_UNCERTAIN** (ic=0.0159, q=0.0028)
- `H1_momentum_03_mom_20_h240_v001` → **EDGE_UNCERTAIN** (ic=0.0207, q=0.0)
- `H1_momentum_04_mom_60_h60_v001` → **REJECTED** (ic=0.0212, q=0.0)
- `H1_momentum_04_mom_60_h240_v001` → **EDGE_UNCERTAIN** (ic=0.0293, q=0.0)
- `H2_mean_reversion_01_zscore_60_h15_v001` → **EDGE_UNCERTAIN** (ic=0.0115, q=0.0383)
- `H2_mean_reversion_01_zscore_60_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0136, q=0.0131)
- `H2_mean_reversion_02_dist_mean_60_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0179, q=0.0)
- `H2_mean_reversion_03_dist_ema_60_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0204, q=0.0)
- `H3_breakout_01_breakout_60_h5_v001` → **REJECTED** (ic=-0.0115, q=0.0396)
- `H3_breakout_03_dist_lo_60_h60_v001` → **REJECTED** (ic=0.0179, q=0.0)
- `H4_volatility_01_vol_30_h60_v001` → **EDGE_UNCERTAIN** (ic=0.572, q=0.0)
- `H4_volatility_01_vol_30_h240_v001` → **EDGE_UNCERTAIN** (ic=0.2401, q=0.0)
- `H4_volatility_02_atr_14_h60_v001` → **EDGE_UNCERTAIN** (ic=0.6191, q=0.0)
- `H4_volatility_02_atr_14_h240_v001` → **EDGE_UNCERTAIN** (ic=0.2536, q=0.0)
- `H4_volatility_03_rvol_60_h60_v001` → **EDGE_UNCERTAIN** (ic=0.5383, q=0.0)
- `H4_volatility_03_rvol_60_h240_v001` → **EDGE_UNCERTAIN** (ic=0.2166, q=0.0)
- `H4_volatility_04_vol_ratio_15_60_h15_v001` → **EDGE_UNCERTAIN** (ic=0.1341, q=0.0)
- `H4_volatility_04_vol_ratio_15_60_h60_v001` → **EDGE_UNCERTAIN** (ic=0.165, q=0.0)
- `H5_trend_regime_01_sma_dist_60_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0179, q=0.0)
- `H5_trend_regime_01_sma_dist_60_h240_v001` → **EDGE_UNCERTAIN** (ic=0.0267, q=0.0)
- `H5_trend_regime_02_ema_dist_60_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0204, q=0.0)
- `H5_trend_regime_02_ema_dist_60_h240_v001` → **EDGE_UNCERTAIN** (ic=0.0298, q=0.0)
- `H5_trend_regime_03_trend_str_h60_v001` → **REJECTED** (ic=0.0131, q=0.0152)
- `H5_trend_regime_03_trend_str_h240_v001` → **EDGE_UNCERTAIN** (ic=0.0392, q=0.0)
- `H5_trend_regime_04_slope_60_h60_v001` → **REJECTED** (ic=0.0143, q=0.0108)
- `H5_trend_regime_04_slope_60_h240_v001` → **EDGE_UNCERTAIN** (ic=0.0231, q=0.0)
- `H6_session_02_hour_h5_v001` → **REJECTED** (ic=0.0165, q=0.0)
- `H6_session_02_hour_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0433, q=0.0)
- `H7_vol_x_momentum_02_mom_60_x_vol30_h60_v001` → **REJECTED** (ic=0.0205, q=0.0)
- `H7_vol_x_momentum_02_mom_60_x_vol30_h240_v001` → **REJECTED** (ic=0.0251, q=0.0)
- `H8_trend_x_vol_01_trend_str_x_vol30_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0206, q=0.0)
- `H8_trend_x_vol_01_trend_str_x_vol30_h240_v001` → **REJECTED** (ic=0.0246, q=0.0)
- `H9_range_x_momentum_02_mom_60_x_compression_h60_v001` → **REJECTED** (ic=0.023, q=0.0)
- `H10_multi_timeframe_02_h1_vol_ratio_h15_v001` → **EDGE_UNCERTAIN** (ic=0.0615, q=0.0)
- `H10_multi_timeframe_02_h1_vol_ratio_h60_v001` → **EDGE_UNCERTAIN** (ic=0.0231, q=0.0)
- `H10_multi_timeframe_02_h1_vol_ratio_h240_v001` → **REJECTED** (ic=-0.097, q=0.0)
- `H10_multi_timeframe_03_h1_breakout_h60_v001` → **REJECTED** (ic=0.0118, q=0.0383)

## Cost rows（FDR 存活者的规则信号成本压力）

- H1_momentum_03_mom_20_h15: 1x=-3.1985 2x=-9.2624 3x=-15.2476 net=-0.1693 trades=2823 subperiod+=0.0
- H1_momentum_03_mom_20_h240: 1x=-2.76 2x=-3.1891 3x=-3.6174 net=-0.1487 trades=199 subperiod+=0.25
- H1_momentum_04_mom_60_h60: 1x=-0.8816 2x=-2.6882 3x=-4.4874 net=-0.0553 trades=837 subperiod+=0.5
- H1_momentum_04_mom_60_h240: 1x=-2.2353 2x=-2.6905 3x=-3.1448 net=-0.1236 trades=211 subperiod+=0.25
- H2_mean_reversion_01_zscore_60_h15: 1x=-2.4365 2x=-6.4939 3x=-10.5135 net=-0.1334 trades=1883 subperiod+=0.25
- H2_mean_reversion_01_zscore_60_h60: 1x=1.4924 2x=-0.2429 3x=-1.9731 net=0.0775 trades=802 subperiod+=0.75
- H2_mean_reversion_02_dist_mean_60_h60: 1x=1.4924 2x=-0.2429 3x=-1.9731 net=0.0775 trades=802 subperiod+=0.75
- H2_mean_reversion_03_dist_ema_60_h60: 1x=2.6809 2x=1.0871 3x=-0.5029 net=0.1508 trades=736 subperiod+=0.75
- H3_breakout_01_breakout_60_h5: 1x=-10.4977 2x=-17.6589 3x=-24.5944 net=-0.1649 trades=2077 subperiod+=0.0
- H3_breakout_03_dist_lo_60_h60: 1x=-0.2876 2x=-0.449 3x=-0.6102 net=-0.0237 trades=75 subperiod+=0.25
- H5_trend_regime_01_sma_dist_60_h60: 1x=1.4924 2x=-0.2429 3x=-1.9731 net=0.0775 trades=802 subperiod+=0.75
- H5_trend_regime_01_sma_dist_60_h240: 1x=2.4593 2x=1.968 3x=1.4768 net=0.1368 trades=227 subperiod+=0.5
- H5_trend_regime_02_ema_dist_60_h60: 1x=2.6809 2x=1.0871 3x=-0.5029 net=0.1508 trades=736 subperiod+=0.75
- H5_trend_regime_02_ema_dist_60_h240: 1x=1.66 2x=1.169 3x=0.6782 net=0.0875 trades=227 subperiod+=0.5
- H5_trend_regime_04_slope_60_h60: 1x=0.3799 2x=-1.3932 3x=-3.1602 net=0.0131 trades=820 subperiod+=0.5
- H5_trend_regime_04_slope_60_h240: 1x=-0.2073 2x=-0.7062 3x=-1.2046 net=-0.0194 trades=231 subperiod+=0.25
- H7_vol_x_momentum_02_mom_60_x_vol30_h60: 1x=-0.8816 2x=-2.6882 3x=-4.4874 net=-0.0553 trades=837 subperiod+=0.5
- H7_vol_x_momentum_02_mom_60_x_vol30_h240: 1x=-2.2353 2x=-2.6905 3x=-3.1448 net=-0.1236 trades=211 subperiod+=0.25
- H8_trend_x_vol_01_trend_str_x_vol30_h60: 1x=1.545 2x=-0.0087 3x=-1.5586 net=0.0806 trades=718 subperiod+=0.75
- H8_trend_x_vol_01_trend_str_x_vol30_h240: 1x=-1.9505 2x=-2.4533 3x=-2.955 net=-0.1096 trades=233 subperiod+=0.25
- H9_range_x_momentum_02_mom_60_x_compression_h60: 1x=-0.8816 2x=-2.6882 3x=-4.4874 net=-0.0553 trades=837 subperiod+=0.5
- H10_multi_timeframe_03_h1_breakout_h60: 1x=0.1567 2x=-0.966 3x=-2.0863 net=0.0023 trades=565 subperiod+=0.5