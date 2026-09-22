# Failure Matrix

Task: **V3-HFT-L1-EXECUTION-EDGE-DISCOVERY-001**. READ_ONLY / OFFLINE.

## Per-horizon outcome (VAL selection, TEST evaluated once)

| horizon | selected | n_trades | **effective_N** | gross (implied) | net mean bp | net median bp | win | 1.25x cost | status |
|---|---|---|---|---|---|---|---|---|---|
| 5 s | PRICE/ridge | 708 | **37** | ≈ +0.45 | −0.47 | −0.45 | 0.44 | mean −0.44, n 329 | **PREDICTIVE_BUT_NOT_EXECUTABLE** (power insufficient) |
| 10 s | SPREAD/tree | 92 | **2** | negative | −6.29 | −2.12 | 0.36 | −7.43, n 76 | **NO_SUPPORTED_L1_EDGE** (insufficient) |
| 30 s | SPREAD/logistic | 108 | **0** | ≈ +8.9 | +7.99 | +1.47 | 0.58 | **n drops 108 → 6, mean → −0.60** | **DATA_INSUFFICIENT** |
| 60 s | SPREAD/logistic | 234 | **1** | ≈ +12.9 | +12.01 | +1.50 | 0.64 | **n 234 → 40, mean → +6.38** | **DATA_INSUFFICIENT** |
| 5 min | SPREAD/ridge | 432 | **0** | ≈ +12.0 | +11.05 | +1.78 | 0.63 | n 432 → 196 (mean +15.9, still <500) | **DATA_INSUFFICIENT** |

**Required effective_N = 500. Every horizon is 0–37.** No horizon reaches the pre-registered
statistical power, so no horizon can carry an alpha claim — positive or negative.

## Why the positive means are not an edge (§三十 checks)

| check | finding | verdict |
|---|---|---|
| LOOKAHEAD | features PIT-causal; labels use the first real tick ≥ t+h; no future data | CLEAN |
| TIMESTAMP | 11 out-of-order elements, 1,014 duplicate timestamps in the concatenated stream | MINOR |
| **SEGMENT/GAP** | **`labels_for` originally had no session-segment guard** — forward windows could cross weekend/session gaps and manufacture large "moves" | **BUG FOUND + FIXED (re-run)** |
| OVERLAP | rho = h/median_dt (18.8–1127.8); effective_N correction applied | CONTROLLED |
| COST | canonical 0.914 bp; 0.314 bp never used | CLEAN |
| TAIL | top10% of trades = **70%** of PnL; median negative with mean positive | **TAIL_DEPENDENT** |
| **PREDICTOR IDENTITY** | `corr(pred, spread_bp) = −0.9994`; `long_share ≈ 0` (all shorts); `pred = −spread/2` alone yields **0 trades** | **MECHANICAL, NOT A FORECAST** |
| COST STRESS | at 30 s/60 s a **1.25×** cost takes n from 108→6 and 234→40 | **NOT ROBUST** |
| CENSORING | censored samples excluded, never 0; censored_n reported | CLEAN |
| DATA_SNAPSHOT | immutable snapshot only; manifest sha256 pinned in every artifact | CLEAN |
| TEST_CONTAMINATION | selection on VAL only; TEST evaluated once | CLEAN |

## Sub-classification (§二十八)

```text
SIGNAL_LIMITED  = TRUE   (5 s and 10 s medians are negative; no consistent direction)
COST_LIMITED    = TRUE   (5 s: gross ≈ +0.45 bp vs cost 0.914 bp)
DATA_LIMITED    = TRUE   (dominant: effective_N 0-37 at every horizon; all regimes INSUFFICIENT_SAMPLE)
```

## What was NOT done (deliberately)

```text
no Transformer / LSTM / large MLP / RL
no feature mining, no window sweep, no threshold sweep
no re-selection after cost stress
no <=2s alpha search (1s/2s appear as REFERENCE_ONLY only)
no forward / live / expansion
```
