# PRICE_SPACE_AUDIT — GC=F(信号) vs XAUUSD spot(执行)

- 生成: 2026-09-19T01:38:16.514384+00:00
- 信号价空间: GC_F (COMEX futures, Yahoo GC=F)
- 执行标的: XAUUSD (spot, FXTM)
- TRADE 决策总数: 32；已成交: 10；判为 MISMATCH: 5
- **结论: 无系统性偏差**

## 审计表

| decision_id | timestamp | instrument_signal | execution_symbol | side | planned_entry | planned_sl | planned_tp | execution_entry | basis | spot_equivalent_entry | spot_equivalent_sl | spot_equivalent_tp | planned_risk | actual_risk | planned_reward | actual_reward | planned_R | actual_R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DEC-ctx_90c83bcaca11 | 2026-09-11T14:07:53.111693+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4432.1 | 4449.83 | 4403.73 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_feb7a04dfcd8 | 2026-09-11T13:52:52.434499+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4434.9 | 4452.64 | 4406.52 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_30ab864391fa | 2026-09-15T04:53:30.339390+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4296.81 | 4314.0 | 4269.31 | 4305.53 | -8.72 | 4305.53 | 4322.72 | 4278.03 | 17.19 | 8.47 | 27.5 | 36.22 | 1.6 | 4.276 |
| DEC-ctx_afc5647fbab6 | 2026-09-15T22:23:06.055576+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4305.52 | 4322.74 | 4277.97 | 4292.6 | 12.92 | 4292.6 | 4309.82 | 4265.05 | 17.22 | 30.14 | 27.55 | 14.63 | 1.6 | 0.485 |
| DEC-ctx_0d750e73b0cf | 2026-09-16T13:52:43.072143+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4347.77 | 4365.16 | 4319.95 | 4339.04 | 8.73 | 4339.04 | 4356.43 | 4311.22 | 17.39 | 26.12 | 27.82 | 19.09 | 1.6 | 0.731 |
| DEC-ctx_1c8042b9ee65 | 2026-09-16T21:22:41.786976+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4335.78 | 4353.12 | 4308.04 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_55b1efd90824 | 2026-09-16T19:07:33.597429+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4351.82 | 4369.23 | 4323.96 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_683a6dec351c | 2026-09-16T14:22:42.233004+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4348.64 | 4366.03 | 4320.82 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_a463ab883d7a | 2026-09-16T14:07:45.250490+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4346.7 | 4364.09 | 4318.88 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_bca0dad1eebb | 2026-09-16T16:37:52.761172+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4352.65 | 4370.06 | 4324.79 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_10abfa1a0fde | 2026-09-18T10:52:28.215424+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4393.56 | 4411.13 | 4365.45 | 4376.46 | 17.1 | 4376.46 | 4394.03 | 4348.35 | 17.57 | 34.67 | 28.11 | 11.01 | 1.6 | 0.318 |
| DEC-ctx_2851e6706f1c | 2026-09-18T20:37:29.610411+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4386.79 | 4404.34 | 4358.71 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_4579769dab64 | 2026-09-18T19:52:29.363830+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4378.22 | 4395.73 | 4350.2 | 4378.82 | -0.6 | 4378.82 | 4396.33 | 4350.8 | 17.51 | 16.91 | 28.02 | 28.62 | 1.6 | 1.692 |
| DEC-ctx_5bd0cecc11ab | 2026-09-18T15:22:29.054057+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | LONG | 4373.58 | 4356.09 | 4401.56 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_82c8a35f9e4f | 2026-09-18T17:52:38.391783+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | LONG | 4353.79 | 4336.37 | 4381.66 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_97f4b314a933 | 2026-09-18T11:07:28.429416+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4393.2 | 4410.77 | 4365.09 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_a4dc959387ea | 2026-09-18T16:52:30.229629+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4353.6 | 4371.01 | 4322.26 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_b9e96e7ab393 | 2026-09-18T15:07:32.360346+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | LONG | 4381.22 | 4363.7 | 4409.25 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_cab581c0bbe2 | 2026-09-18T20:07:30.205700+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4382.68 | 4400.21 | 4354.63 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_db7f32205464 | 2026-09-18T17:07:29.700654+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4349.16 | 4366.56 | 4317.84 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_0d7922ba27e8 | 2026-09-18T04:22:27.933475+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4357.97 | 4375.4 | 4330.08 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_2835d33aace9 | 2026-09-17T23:52:57.388967+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4341.16 | 4358.52 | 4309.91 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_90f96244ea6a | 2026-09-17T14:23:02.590546+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4331.86 | 4349.19 | 4304.13 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_945b5b4942bf | 2026-09-18T06:37:26.985232+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | LONG | 4340.89 | 4323.53 | 4368.67 | 4341.1 | -0.21 | 4341.1 | 4323.74 | 4368.88 | 17.36 | 17.57 | 27.78 | 27.57 | 1.6 | 1.569 |
| DEC-ctx_a13810accc62 | 2026-09-17T21:52:27.150864+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | LONG | 4352.27 | 4334.86 | 4380.13 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_a6f71af109d8 | 2026-09-18T00:07:57.934743+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | LONG | 4341.62 | 4324.25 | 4369.41 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_b6a3ef74df37 | 2026-09-17T11:08:02.193556+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4327.36 | 4344.67 | 4299.66 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_d84b486709a8 | 2026-09-18T09:07:36.647191+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4377.24 | 4394.75 | 4349.22 | 4377.03 | 0.21 | 4377.03 | 4394.54 | 4349.01 | 17.51 | 17.72 | 28.02 | 27.81 | 1.6 | 1.569 |
| DEC-ctx_de3ee55784b1 | 2026-09-17T22:52:45.583031+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | LONG | 4345.05 | 4327.67 | 4372.86 | None | - | - | - | - | - | - | - | - | - | - |
| DEC-ctx_e0504c3d9c2f | 2026-09-18T08:37:47.502620+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4364.45 | 4381.91 | 4336.51 | 4364.24 | 0.21 | 4364.24 | 4381.7 | 4336.3 | 17.46 | 17.67 | 27.94 | 27.73 | 1.6 | 1.569 |
| DEC-ctx_f3dc913b93c2 | 2026-09-18T10:07:31.367262+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4393.25 | 4410.82 | 4365.14 | 4393.04 | 0.21 | 4393.04 | 4410.61 | 4364.93 | 17.57 | 17.78 | 28.11 | 27.9 | 1.6 | 1.569 |
| DEC-ctx_faf24b604ed6 | 2026-09-18T08:22:27.992346+00:00 | GC_F (COMEX futures, Yahoo GC=F) | XAUUSD (spot, FXTM) | SHORT | 4365.32 | 4382.78 | 4337.38 | 4365.11 | 0.21 | 4365.11 | 4382.57 | 4337.17 | 17.46 | 17.67 | 27.94 | 27.73 | 1.6 | 1.569 |

## 附：上下文 basis（同轮 Agent1 记录）

| decision_id | ctx_primary_last(GC) | ctx_basis_usd | execution_entry | observed_basis |
|---|---|---|---|---|
| DEC-ctx_90c83bcaca11 | 4432.1 | 44.77 | None | - |
| DEC-ctx_feb7a04dfcd8 | 4434.9 | 45.57 | None | - |
| DEC-ctx_30ab864391fa | 4296.81 | -8.58 | 4305.53 | -8.72 |
| DEC-ctx_afc5647fbab6 | 4305.52 | 13.17 | 4292.6 | 12.92 |
| DEC-ctx_0d750e73b0cf | 4347.77 | 6.29 | 4339.04 | 8.73 |
| DEC-ctx_1c8042b9ee65 | 4335.78 | 71.84 | None | - |
| DEC-ctx_55b1efd90824 | 4351.82 | 82.52 | None | - |
| DEC-ctx_683a6dec351c | 4348.64 | 13.39 | None | - |
| DEC-ctx_a463ab883d7a | 4346.7 | 21.41 | None | - |
| DEC-ctx_bca0dad1eebb | 4352.65 | 5.73 | None | - |
| DEC-ctx_10abfa1a0fde | 4393.56 | 16.51 | 4376.46 | 17.1 |
| DEC-ctx_2851e6706f1c | 4386.79 | 5.63 | None | - |
| DEC-ctx_4579769dab64 | 4378.22 | -2.62 | 4378.82 | -0.6 |
| DEC-ctx_5bd0cecc11ab | 4373.58 | 20.81 | None | - |
| DEC-ctx_82c8a35f9e4f | 4353.79 | -40.39 | None | - |
| DEC-ctx_97f4b314a933 | 4393.2 | 11.76 | None | - |
| DEC-ctx_a4dc959387ea | 4353.6 | -25.24 | None | - |
| DEC-ctx_b9e96e7ab393 | 4381.22 | 26.14 | None | - |
| DEC-ctx_cab581c0bbe2 | 4382.68 | 3.92 | None | - |
| DEC-ctx_db7f32205464 | 4349.16 | -36.19 | None | - |
| DEC-ctx_0d7922ba27e8 | 4357.97 | 3.74 | None | - |
| DEC-ctx_2835d33aace9 | 4341.16 | -4.01 | None | - |
| DEC-ctx_90f96244ea6a | 4331.86 | -35.76 | None | - |
| DEC-ctx_945b5b4942bf | 4340.89 | -51.93 | 4341.1 | -0.21 |
| DEC-ctx_a13810accc62 | 4352.27 | 10.53 | None | - |
| DEC-ctx_a6f71af109d8 | 4341.62 | -4.85 | None | - |
| DEC-ctx_b6a3ef74df37 | 4327.36 | -2.61 | None | - |
| DEC-ctx_d84b486709a8 | 4377.24 | -18.77 | 4377.03 | 0.21 |
| DEC-ctx_de3ee55784b1 | 4345.05 | 2.37 | None | - |
| DEC-ctx_e0504c3d9c2f | 4364.45 | -22.2 | 4364.24 | 0.21 |
| DEC-ctx_f3dc913b93c2 | 4393.25 | 15.6 | 4393.04 | 0.21 |
| DEC-ctx_faf24b604ed6 | 4365.32 | -27.69 | 4365.11 | 0.21 |
