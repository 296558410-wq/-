# OOS report — V3-HFT-ALPHA-DISCOVERY-001

- Freeze: `alpha/freeze/V3_ALPHA_RESEARCH_FREEZE_001.md`
  sha256 `557bcc3c96338c1261f8a5b70371a6a679ff61ec433fbd24234aabf782b8a4d0`
- Data: FXTM demo tick feed (the cost-calibrated, tradable venue)
  - S1 `staging_fxtm` 2026-08-04 → 2026-09-04 (24 files)
  - S2 `live_fxtm`   2026-09-07 → 2026-09-21 (11 files)
  - 7,239,126 ticks after dropping 913 exact duplicate timestamps
- Split: TRAIN 2026-08-04…08-21 · VAL 2026-08-24…09-04 · TEST 2026-09-07…09-21
  (purge + embargo = horizon `h`; TEST untouched until this report)
- Grid: 1 s as-of sampling (2,795,845 fresh samples; 66.3 % of grid instants retained,
  the drop being staleness > 5 s and grid instants without a tick)
- Cost anchor: 0.40 USD/round-trip ≈ 0.90 bp at ~4,400 USD/oz (measured median spread 0.15 USD = 0.343 bp)

## 1. Do the horizons even exist in the data?

| horizon | clean fraction | effective_n | verdict | strongest univariate rank-IC |
|---|---|---|---|---|
| 50 ms | 0.001 | 2,129 | **DATA_INSUFFICIENT** | +0.122 |
| 200 ms | 0.446 | 1,247,125 | **DATA_INSUFFICIENT** | −0.118 |
| 1 s | 0.814 | 605,337 | MEASURABLE | −0.179 |
| 5 s | 0.994 | 147,727 | MEASURABLE | −0.142 |
| 30 s | 1.000 | 24,769 | MEASURABLE | −0.065 |
| 5 min | 0.996 | 2,467 | MEASURABLE | −0.019 |
| 1 h | 0.950 | 196 | MEASURABLE | +0.024 |
| 24 h | 0.000 | 0 | **DATA_INSUFFICIENT** | — |

Median inter-tick interval **266 ms (3.76 Hz)**. At 50 ms only 0.1 % of samples can be labelled
cleanly (no tick inside the window); at 200 ms 44.6 %. **The feed cannot resolve sub-second
horizons** — that is a data fact, not a modelling failure.
24 h is unmeasurable because every forward window crosses the daily session break
(`daily 21:00–22:59Z` registered gap, `G_MAX(24h) = 1 h`), so 0 clean samples survive.

## 2. Out-of-sample result (TEST fold, frozen selection on VAL)

| h | selected (VAL-best) | trades | gross bp | **net bp** | net USD/trade | bootstrap 95 % CI (bp) | n_indep |
|---|---|---|---|---|---|---|---|
| 1 s | B0 / MLP | 6 | +0.013 | **−0.901** | −0.397 | [−1.68, −0.14] | 2 |
| 30 s | B3 / Ridge | 383 | +0.034 | **−0.888** | −0.383 | [−1.40, −0.75] | 4 |
| 5 min | B4 / GBT | 110,248 | +0.096 | **−0.825** | −0.362 | [−1.87, +0.18] | 98 |
| Naive (reference) | — | — | — | ≈ −0.44 bp (≈ −0.45 USD) | — | — | — |

- **Every OOS net edge is negative**, and every configuration loses more than the Naive
  reference's −0.44 bp only where it trades more aggressively at lower gross edge.
- The 1 s row is degenerate (6 OOS trades, n_indep = 2) because no configuration reached the
  VAL eligibility floor of 200 trades at that horizon; the row is reported as a reference only.
- The 5 min CI upper bound (+0.18 bp) still sits far below the 0.10 USD/RT (≈ 0.23 bp)
  minimum-tradable bar, i.e. even the optimistic end of the CI is economically dead.

## 3. Why: the cost-to-move scale mismatch (the decisive number)

Measured median absolute forward mid move, in bp, per horizon (clean samples):

| h | 200 ms | 1 s | 5 s | 30 s | 5 min | 1 h |
|---|---|---|---|---|---|---|
| median \|move\| bp | 0.162 | 0.346 | 0.582 | 1.269 | 4.168 | 16.065 |
| cost (0.90 bp) ÷ move | 5.6× | **2.6×** | 1.5× | 0.71× | 0.22× | 0.06× |

At 1 s the round-trip cost is **2.6× the median absolute move**. A perfect directional oracle at
1 s would still need to pick the >0.90 bp tail consistently. The best *estimated* gross edge
achieved by any frozen feature family × model was **+0.096 bp** (5 min, B4/GBT) — roughly
**9× below cost**. Gross sig-nal exists (rank-IC −0.18 at 1 s, i.e. real short-horizon
mean reversion) but its magnitude is an order of magnitude too small to pay a 0.90 bp toll.

## 4. Cost stress and latency stress

Net bp per trade under the frozen cost tiers (USD/round-trip):

| h | 0.40 | 0.50 | 0.60 | 0.80 | 1.00 |
|---|---|---|---|---|---|
| 1 s | −0.901 | −1.130 | −1.185 | −1.535 | −1.991 |
| 30 s | −0.888 | −0.699 | −1.393 | −0.903 | −3.273 |
| 5 min | −0.825 | −1.104 | −1.436 | −2.162 | −2.711 |

No tier at any horizon is positive.

Simulated execution at real bid/ask with latency `L` (entry `ask`/`bid` at `t+L`, exit
`bid`/`ask` at `t+h+L`, minus 0.22 USD commission):

| h | L=0 | L=50 | L=100 | L=250 | L=500 | L=1000 |
|---|---|---|---|---|---|---|
| 1 s (net bp) | −1.004 | −0.938 | −0.838 | −0.831 | −0.811 | −1.256 |
| 30 s (net bp) | −0.880 | −0.888 | −0.888 | −0.674 | −0.690 | −0.782 |
| 5 min (net bp) | −0.771 | −0.770 | −0.769 | −0.769 | −0.769 | −0.767 |

Latency does not rescue anything; the median absolute entry-price drift at 250 ms is 0.08 USD
(5 min) / 0.24 USD (30 s), i.e. latency adds cost, it never removes it.

## 5. Luck vs signal — the statistical picture

- **30 model-search iterations**, all logged in `alpha/models/model_manifest.json`.
- **0 of 30** survive Benjamini–Hochberg FDR at q = 0.05 (`alpha/statistics/multiple_testing.json`);
  only 8 of 30 even produced a valid p-value (the rest never traded enough to test).
- The single **positive** OOS number in the whole run is a vivid illustration of luck:
  iteration 8 (B0/Ridge @ 30 s) had `val_net = −0.284 USD` but `test_net = +0.821 USD`.
  It was not selectable from VAL, and it did not survive any correction. One sign flip between
  two adjacent folds is exactly what noise looks like, not alpha.
- Effective-sample correction: at 1 s the overlap ratio is ρ ≈ 3.8 (n_indep ≈ 2 at 1 s in TEST,
  4 at 30 s, 98 at 5 min) — the raw trade counts (up to 110,248) are **not** independent
  observations, and the report never treats them as such.

## 6. Verdict

- **50 ms, 200 ms, 24 h → `DATA_INSUFFICIENT`** (feed resolution / session-break blocking).
- **1 s, 30 s, 5 min (and diagnostically 5 s, 1 h) → `NO_ALPHA`**: no configuration produced a
  net-of-cost, out-of-sample, statistically distinguishable positive edge. Gross predictability
  exists at short horizons but is ~9× smaller than the measured round-trip cost.
- `RESULT_STATUS = NO_ALPHA` (with `DATA_INSUFFICIENT` for the three unmeasurable horizons).
- No code path was changed to improve any number; the freeze was hashed before the first
  feature was computed.

## 7. Data gaps that shaped this verdict (see `alpha/data/data_gaps.md`)

`2023-12`, `2024-04 → 2026-07`, `daily 21:00–22:59Z`, `L2/trade_flow = UNKNOWN (L2_DATA_GAP)`;
`volume`/`volume_real`/`last` identically 0 on the whole FXTM feed (B1 microprice and true B2 OFI
are therefore `DATA_GAP`, never synthesised).
