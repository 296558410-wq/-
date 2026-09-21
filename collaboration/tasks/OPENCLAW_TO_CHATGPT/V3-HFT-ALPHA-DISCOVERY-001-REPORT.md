# V3_HFT_ALPHA_DISCOVERY_001_REPORT

- Task: **V3-HFT-ALPHA-DISCOVERY-001**
- Question: does V3 have a **net-of-real-cost, reproducible, statistically distinguishable-from-luck**
  directional alpha on XAUUSD L1 quote data?
- Mode: research + engineering, **read-only** on market data; **no order placement of any kind**.
- Freeze (hash-locked before any search):
  `alpha/freeze/V3_ALPHA_RESEARCH_FREEZE_001.md`
  sha256 `557bcc3c96338c1261f8a5b70371a6a679ff61ec433fbd24234aabf782b8a4d0`

---

## 1. What was done (one paragraph)

Loaded and **actually scanned** every relevant parquet family, produced a real data manifest and gap
list, hashed a frozen research plan (data range, 8 horizons, labels, cost tiers, splits, statistics,
rejection rules, 30-iteration cap), implemented the frozen causal feature families B0–B6 + the
cost-aware forward-mid labels, built a 1-second as-of sample panel over the FXTM demo tick feed,
ran a **30-iteration** feature/model/horizon search with TRAIN-only fitting and VAL-only selection,
then evaluated TEST once with BH-FDR multiple-testing control, moving-block bootstrap CIs,
overlap/effective-N correction, 5-tier cost stress and 6-level latency stress using real ticks.

## 2. Data (measured, not assumed)

| feed | files | rows | UTC range | median spread | tick rate |
|---|---|---|---|---|---|
| `staging_fxtm/ticks_*` (primary) | 24 | 4,995,855 | 2026-08-04T01:05Z → 2026-09-04T15:50Z | 0.150 USD | 2.3–2.7 Hz |
| `live_fxtm/ticks_*` (primary) | 11 | 2,244,184 | 2026-09-07T01:05Z → 2026-09-21T19:39Z | 0.150 USD | 1.9–2.4 Hz |
| **primary total** | **35** | **7,239,126** (after 913 exact-dup ts dropped) | | | |
| `staging_duka/assembled/ticks_*` (cross-check) | 7 | 15,563,968 | 2023-09-01T22:00Z → 2026-08-04T20:59Z | 0.320–0.630 USD | 0.65–3.3 Hz |
| `staging_duka/ticks_YYYYMMDD` | 140 | 15,563,968 | same ticks, split by day | — | — |
| `staging_duka/candles_*` | 179 | 15,618,240 | 2010-01-01 → 2026-08-03 | — | 1-min bars |

- duplicates = 0, out-of-order = 0 on every FXTM file; UTC proven (tz-aware `datetime64[ms, UTC]`).
- `volume`, `volume_real`, `last` are **identically 0** across the whole FXTM feed.
- Median inter-tick interval **266 ms (3.76 Hz)**; measured median spread **0.343 bp**.

Details: `alpha/data/data_manifest.json` (498 KB, per-file), `alpha/data/data_gaps.md`.

## 3. Frozen design (short form)

- Splits by UTC date: TRAIN 08-04…08-21 (1,150,083 samples) · VAL 08-24…09-04 (792,525) ·
  TEST 09-07…09-21 (852,336); purge+embargo = `h`.
- Horizons: 50 ms, 200 ms, 1 s, 5 s, 30 s, 5 min, 1 h, 24 h. Label = forward mid return to the
  first real tick ≥ `t+h` (never interpolated); net = gross − `RT_USD/mid·1e4`.
- Cost: anchor 0.40 USD/RT, stress tiers 0.40/0.50/0.60/0.80/1.00 USD/RT;
  minimum tradable net edge 0.10 USD/RT.
- Statistics: α = 0.05, **BH-FDR q = 0.05** across the 30-iteration family, moving-block bootstrap
  (2,000 resamples, block = max(50, 10ρ)), effective-N = n / ρ.
- Rejection: any of net ≤ 0 · CI lower ≤ 0 · FDR p ≥ 0.05 · net ≤ 0.10 USD/RT · turnover·cost ≥ gross.
- **Iteration cap 30, used exactly 30.** Family B0–B6 each ≤ 2 features, PIT-causal.

## 4. Features evaluated

| family | features | status |
|---|---|---|
| B0 lagged returns (baseline) | `r1_bp`, `r2_bp` | computed |
| B1 microprice deviation | `micro_dev_bp`, `micro_dev_norm` | **DATA_GAP** (no sizes; columns are 0) |
| B2 order-flow imbalance | `ofi_signed_sum`, `ofi_proxy` (tick-rule L1 proxy) | proxy only |
| B3 short-term momentum | `mom10_bp`, `mom50_bp` | computed |
| B4 spread/volatility state | `spread_z50`, `vol50_bp` | computed |
| B5 limited reversal | `rev10_clip_bp`, `rev50_clip_bp` | computed |
| B6 interaction | `mom10_x_spreadz`, `mom10_x_vol` | computed |

Models: `Naive` (reference, no fit), `Ridge`, `Logistic`, `GBT` (HistGradientBoosting),
`MLP` (torch, CUDA RTX A2000 Laptop).

## 5. Headline result

**`RESULT_STATUS = NO_ALPHA`** (with `DATA_INSUFFICIENT` for 50 ms / 200 ms / 24 h).

| h | selected | trades | gross bp | net bp | net USD | boot CI (bp) |
|---|---|---|---|---|---|---|
| 1 s | B0/MLP (reference; no VAL-eligible config) | 6 | +0.013 | −0.901 | −0.397 | [−1.68, −0.14] |
| 30 s | B3/Ridge | 383 | +0.034 | −0.888 | −0.383 | [−1.40, −0.75] |
| 5 min | B4/GBT | 110,248 | +0.096 | −0.825 | −0.362 | [−1.87, +0.18] |

- 0 of 30 tests survive BH-FDR q = 0.05.
- Every OOS net edge is negative; Naive reference ≈ −0.44 bp.
- **Decisive scale argument**: cost ≈ 0.90 bp; median |1 s move| = 0.346 bp → cost is 2.6× the
  typical move; best estimated gross edge (+0.096 bp) is ~9× below cost.
- Gross short-horizon predictability *does* exist (rank-IC −0.179 at 1 s, −0.142 at 5 s — real
  mean reversion), but it is an order of magnitude too small to pay the toll.
- Latency (0→1000 ms) never turns net positive; cost tiers 0.40→1.00 never turn net positive.
- Evidence of luck, not signal: iteration 8 (B0/Ridge @30 s) VAL −0.284 USD → TEST **+0.821 USD**.
  Not selectable, not significant.

## 6. Compliance with the boundaries

| constraint | status |
|---|---|
| `order_send` / `order_check` calls | **0** (no MT5 trading API used at all; data read from disk) |
| LIVE / real funds / auto-order paths | **not enabled, not touched** |
| V1 / V2 / OpenClaw / MT5 instances / Scheduler / real ledger | **untouched** (all writes confined to `research/hermes/trader_v3/alpha/`) |
| `PILOT_DONE`, `hft_ledger/*`, `V3_CALIBRATION_PILOT.json` | **untouched** |
| V3 `execution` / `calibration` / `foundation/**` business logic | **untouched** (read-only import of `feature_builder`-local code only) |
| Interpolation / fabricated ms-level data | **none**; gaps written as DATA_GAP |
| Design/threshold/split changed to improve results | **none**; freeze hashed before the first computation |
| Iteration cap | 30 used of 30 — **cap respected, not exceeded** |
| HALT conditions | none triggered (no need to modify frozen V3 business code) |

## 7. Deliverables

```
alpha/freeze/V3_ALPHA_RESEARCH_FREEZE_001.md, FREEZE_HASH.json
alpha/data/data_manifest.json, data_gaps.md
alpha/features/feature_spec.md, feature_builder.py
alpha/labels/label_spec.md
alpha/models/model_results.json, model_manifest.json
alpha/backtest/B0_baseline.json … B6_backtest.json, cost_sensitivity.json, latency_sensitivity.json
alpha/statistics/statistical_tests.json, multiple_testing.json, effective_sample.json, move_scale.json
alpha/oos/oos_results.json, oos_report.md
alpha/reports/V3_HFT_ALPHA_DISCOVERY_001_REPORT.md, V3_HFT_ALPHA_DISCOVERY_001_RESULT.json
alpha/tools/{scan_data,write_data_docs,run_experiments}.py   (reproducible driver)
```

## 8. Reproduction

```
C:\AIQuant\.venv\Scripts\python.exe alpha\tools\scan_data.py
C:\AIQuant\.venv\Scripts\python.exe alpha\tools\write_data_docs.py
C:\AIQuant\.venv\Scripts\python.exe alpha\tools\run_experiments.py     # ~210 s
```
Deterministic seed 20260921; environment: Python 3.12.10, numpy 2.5.2, pandas 3.0.5,
scikit-learn 1.9.0, scipy 1.18.1, statsmodels 0.15.0, torch 2.14.0+cu126 (CUDA True).

## 9. Not claimed

This report does **not** claim PASS. It does not claim alpha exists. It reports
`NO_ALPHA` for the measurable horizons and `DATA_INSUFFICIENT` for the unresolvable ones,
with the full evidence chain and the audit verdict left to the external reviewer.
