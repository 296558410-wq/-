# V3_ALPHA_RESEARCH_FREEZE_001

- **Task**: V3-HFT-ALPHA-DISCOVERY-001
- **Created (UTC)**: 2026-09-21T20:0x (see FREEZE_HASH.json for exact hash + timestamp)
- **Status**: FROZEN — no search, threshold, split or cost change may be made after this file is hashed.
- **Companion hash record**: `alpha/freeze/FREEZE_HASH.json` (sha256 of this file, computed after write).

This document is the single source of truth for the experiment. All later artifacts
(`features/feature_spec.md`, `labels/label_spec.md`, `models/model_manifest.json`,
`backtest/*`, `statistics/*`, `oos/*`) must restate these decisions verbatim and may not widen them.

---

## 1. Research scope / question

**Question**: Does V3 (XAUUSD, L1 quote feed) contain a **net-of-real-cost**, **reproducible**,
**statistically distinguishable-from-luck** directional alpha, measurable on the data that
actually exists on disk?

In scope: predictive (directional) signal discovery on tick/L1 data; cost-aware evaluation;
latency stress; out-of-sample validation; multiple-testing control.

Out of scope: any order placement, any strategy/execution code change, any calibration change,
V1/V2/OpenClaw changes, L2/order-book inference (data absent), macro/fundamental work.

## 2. Data range (from a real scan, not from the registry)

Primary feed (the tradable, cost-calibrated venue = FXTM demo):

| segment | files | UTC range | rows |
|---|---|---|---|
| S1 `data/staging_fxtm/ticks_*.parquet` | 24 | 2026-08-04T01:05Z → 2026-09-04T15:50Z | 4,995,855 |
| S2 `data/live_fxtm/ticks_*.parquet` | 11 | 2026-09-07T01:05Z → 2026-09-21T19:39Z | 2,244,184 |
| **primary total** | 35 | 2026-08-04 → 2026-09-21 | **7,240,039** |

Measured feed properties (median over files): spread ≈ 0.15 USD; raw tick cadence ≈ 1.9–2.7 Hz;
duplicates = 0; out-of-order = 0; `volume`/`volume_real`/`last` are **identically zero** →
no trade prints and no sizes on this feed.

Secondary feed (cross-venue robustness check only, never used for fitting or selection):

| segment | files | UTC range | rows |
|---|---|---|---|
| `data/staging_duka/assembled/ticks_*.parquet` | 7 | 2023-09-01T22:00Z → 2026-08-04T20:59Z | 15,563,968 |

Duka spread ≈ 0.32–0.63 USD (1.4–1.7 bp); `bid_vol == ask_vol` in 33–85% of ticks.

**Registered gaps carried forward (must be reflected as DATA_GAP, never interpolated):**
`2023-12`, `2024-04 → 2026-07`, `daily 21:00–22:59Z`, `L2/trade_flow = UNKNOWN (L2_DATA_GAP)`.

## 3. Train / Val / Test split (chronological, by UTC date)

| fold | dates (UTC) | files | role |
|---|---|---|---|
| TRAIN | 2026-08-04 → 2026-08-21 | 14 | fit only |
| VAL   | 2026-08-24 → 2026-09-04 | 10 | model/threshold selection only |
| TEST  | 2026-09-07 → 2026-09-21 | 11 | **untouched until final report** |

- Purge + embargo between folds = the evaluated horizon `h` (labels of TRAIN samples whose
  forward window would reach into VAL are dropped; likewise VAL→TEST).
- Weekends/holidays are natural breaks and are never stitched for label windows.
- No random shuffling anywhere. TEST is never used before §13.

## 4. Horizons (8, frozen)

`h ∈ {50 ms, 200 ms, 1 s, 5 s, 30 s, 5 min, 1 h, 24 h}` = `{50, 200, 1000, 5000, 30000, 300000, 3600000, 86400000}` ms.

## 5. Sample construction (frozen)

- **Primary sample grid**: Δ = 1 s. At each grid instant the *as-of* tick is the last tick with
  `ts ≤ grid`. Only `ts ≤ decision_time` information is used (PIT guard).
- **Fine sample (sub-second demonstration, h ∈ {50, 200} ms only)**: every tick. Purpose = measure
  whether the feed can even resolve the horizon; not used for any selection.
- A sample is **label-defined** iff the forward lookup finds a tick at `ts ≥ t+h` inside the same segment.
- A sample is **clean** iff `slack = (t* − t − h)/h ≤ 0.5` and the window `(t, t*]` contains no gap > `G_MAX(h)`.
- `G_MAX(h) = max(60 s, 10·h)` for `h ≤ 5 min`; `G_MAX(h) = 1 h` for `h ≥ 1 h`.
- Overlap ratio `ρ(h) = h / median_inter_tick_interval`; the **independent sub-sample** keeps every
  `⌈ρ⌉`-th sample. `effective_n(h) = floor(N_defined / max(ρ,1))`.

## 6. Labels (frozen, gross and net)

- `y_gross(t,h) = mid(t*)/mid(t) − 1`, in bp ×1e4. `mid = (bid+ask)/2`.
- `y_net(t,h) = y_gross(t,h) − c_bp(t,h)`, `c_bp(t,h) = RT_USD / mid(t) × 1e4`.
- `NET_LABEL_STATUS = DATA_GAP` for any sample where label is undefined (never interpolated).

## 7. Cost definition and the 5 stress tiers

Measured structural cost anchor (from the completed V3 execution calibration,
`state/V3_COST_PROFILE.json`): spread ≈ 0.18 USD/RT, commission ≈ 0.22 USD/RT,
**RT anchor ≈ 0.40 USD ≈ 0.914 bp at 4,376 USD/oz**.

Stress tiers (USD per round-trip): **0.40 / 0.50 / 0.60 / 0.80 / 1.00**.
Two evaluations are always produced:
1. **Simulated execution** (latency test): entry at real `ask` (long) / `bid` (short) at `t+L`,
   exit at real `bid` (long) / `ask` (short) at `t+h+L`; minus commission 0.22 USD/RT.
2. **Lump-sum stress**: `y_net = y_gross − tier_USD/mid(t)×1e4`.

## 8. Minimum tradable net edge (frozen)

A configuration is *economically tradable* only if **OOS net edge per trade > 0.10 USD/RT**
(≈ 25% of the 0.40 USD anchor), in addition to every statistical requirement below.

## 9. Significance, multiple testing, overlap

- α = 0.05; **BH-FDR q = 0.05** across the full primary test family (all B0–B6 × model × horizon tests).
- p-values: two-sided t on HAC-free **non-overlapping** returns; plus **block bootstrap** CI.
- **Block bootstrap**: 2,000 resamples; block length = `max(50, 10 × grid_points_per_horizon)`
  samples (preserves within-block autocorrelation/overlap). 95% CI = percentile [2.5, 97.5].
- Overlap always reported; no test is run on overlapping samples without effective_n correction.

## 10. Rejection criteria (frozen)

Report `RESULT_STATUS = NO_ALPHA` if ANY of:
- OOS net edge per trade ≤ 0, **or**
- bootstrap 95% CI lower bound ≤ 0, **or**
- FDR-adjusted p ≥ 0.05, **or**
- OOS net edge ≤ 0.10 USD/RT, **or**
- OOS turnover × cost ≥ gross edge.

Report `DATA_INSUFFICIENT` for a horizon if ANY of:
- `effective_n < 30`, **or**
- clean-label fraction < 50%, **or**
- the feed cannot resolve the horizon (median inter-tick interval > 2·h), **or**
- required lookahead crosses a registered gap.

## 11. OOS standard (frozen)

Fit on TRAIN only. Any selection (family, model, threshold, hyper-parameter) happens on VAL only.
TEST is evaluated once, at the end, and reported as the OOS result. No re-fitting after seeing TEST.

## 12. Feature families (frozen; ≤ 2 features each; strictly causal)

| id | family | features (≤2) |
|---|---|---|
| B0 | lagged returns only (baseline) | `r1 = mid[i]/mid[i-1]−1`, `r2 = mid[i]/mid[i-2]−1` |
| B1 | microprice deviation | `micro_dev = microprice_state − mid` ; `micro_dev_norm` — **DATA_GAP unless sizes exist** |
| B2 | order-flow imbalance | `ofi_proxy = (n_up − n_dn)/(n_up + n_dn)` over window; `ofi_signed_sum` — tick-rule L1 proxy |
| B3 | short-term momentum | `mom10`, `mom50` |
| B4 | spread / volatility state | `spread_z50`, `vol50` |
| B5 | limited reversal | `rev10_clip`, `rev50_clip` (clipped −momentum) |
| B6 | interaction (minimal) | `mom10 × spread_z50`, `mom10 × vol50` |

Raw features are standardised with **TRAIN-only** mean/σ before modelling.

## 13. Models (frozen)

`Naive` (trailing-h same-horizon return, no fit), `Logistic`, `Ridge` (linear),
`HistGradientBoosting` (GBT), `MLP` (torch, small, CUDA if available).
No new large models. Iteration budget: **≤ 30** (feature/model/horizon/threshold combinations),
every one logged to `models/model_manifest.json`.

## 14. Deliverable contract

Outputs under `research/hermes/trader_v3/alpha/`. No order placement (`order_send` calls = 0).
No writes to V1/V2/OpenClaw/scheduler/ledger/calibration paths. Report is evidence-only;
the PASS judgment belongs to the external auditor.

## 15. Hash

`sha256(this file)` recorded in `alpha/freeze/FREEZE_HASH.json`. After hashing, this file is immutable.
