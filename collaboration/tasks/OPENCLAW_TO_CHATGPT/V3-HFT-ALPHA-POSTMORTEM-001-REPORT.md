# ALPHA_POSTMORTEM_REPORT — V3-HFT-ALPHA-POSTMORTEM-001

- Mode: **AUDIT_ONLY / READ_ONLY · NO_NEW_ALPHA_SEARCH · NO_NEW_MODEL_SELECTION · NO_NEW_TEST_SELECTION**
- This report **does not change** `V3-HFT-ALPHA-DISCOVERY-001`. Its result stays `NO_ALPHA`.
- The only goal: state **what we know** and **what we do not know** — and refuse to conflate
  *no alpha* with *cannot observe alpha* or *cost too high*.

```text
ALPHA_DISCOVERY_INPUT_COMMIT  = b42c865e49e8ea11a740c14dfbddb8eb74b1e161
ALPHA_DISCOVERY_REPORT_SHA256 = 976333c528f06f8fa76a5c661af692774e1964a681cafff6f9891dc9392f0881
FREEZE_SHA256                 = 557bcc3c96338c1261f8a5b70371a6a679ff61ec433fbd24234aabf782b8a4d0
```

## 0. Verdicts

| audit | verdict |
|---|---|
| DATA_LEAKAGE | **PASS** (no selection leakage; one minor TEST-observation note) |
| DATA_SNAPSHOT | **PASS_WITH_DATA_GAP** (34/35 primary files hash-provable; 1 live tail appending) |
| DATA_CAPABILITY | **DATA_GAP** → `L1_QUOTE_ONLY`, microstructure/trade-flow untestable |
| EXECUTION_COST_BOTTLENECK | **YES** (severe at h ≤ 5 s) |
| LATENCY_BOTTLENECK | **NO** (0 ms already negative) |

## 1. Horizon observability (the "cannot judge" vs "judged" split)

From `statistics/effective_sample.json` (frozen):

| h | n_clean | effective_n | clean_frac | class |
|---|---|---|---|---|
| 50 ms | 2,129 | 2,129 | 0.00076 | **DATA_INSUFFICIENT** (feed 266 ms > 2·50 ms) |
| 200 ms | 1,247,125 | 1,247,125 | 0.446 | **DATA_INSUFFICIENT** (clean_frac < 0.5) |
| 1 s | 2,275,706 | **605,337** | 0.814 | SUFFICIENT |
| 5 s | 2,776,837 | **147,727** | 0.994 | SUFFICIENT |
| 30 s | 2,793,586 | **24,769** | 0.9995 | SUFFICIENT |
| 5 min | 2,782,793 | **2,467** | 0.9957 | SUFFICIENT |
| 1 h | 2,656,438 | **196** | 0.950 | DATA_LIMITED |
| 24 h | 0 | 0 | 0.0 | **DATA_INSUFFICIENT** (every window crosses a session gap) |

Median inter-tick interval = **266 ms**; grid = 1 s; `effective_n = n/max(ρ,1)`, `ρ = h/median_dt`.

## 2. Gross vs net (prediction ≠ tradable edge)

Strict separation, as required:

```text
GROSS_EDGE            = best estimated +0.096 bp  (5 min / B4·GBT, TEST)
- SPREAD              ≈ 0.18 USD
- COMMISSION          ≈ 0.22 USD
- SLIPPAGE            (included via real-tick simulated execution)
- LATENCY_EFFECT      (measured 0..1000 ms; secondary)
= NET_EXECUTABLE_EDGE  = NEGATIVE on every horizon
```

Rank-IC (pre-cost, univariate) is real but small and decays fast:
1 s **−0.179**, 5 s −0.142, 30 s −0.065, 5 min −0.019, 1 h +0.024.
Cost is ~9.5× the best gross edge → the signal cannot pay the toll. **Prediction accuracy is not trading edge.**

## 3. The three layers (they coexist; not compressed into one label)

- **SUPPORTED_NO_ALPHA** — for h ∈ {1 s, 5 s, 30 s, 5 min}: data sufficient, OOS clean, cost real,
  statistics valid → **no supportive alpha** (all OOS net negative; 0/30 survive BH-FDR q=0.05).
- **DATA_LIMITED_NO_ALPHA** — for h ∈ {50 ms, 200 ms, 24 h} (DATA_INSUFFICIENT) and 1 h (eff_n=196):
  we **cannot** make a strong claim, in either direction.
- **EXECUTION_LIMITED_NO_ALPHA** — a real gross mean-reversion exists but is ~9× below cost;
  even a perfect short-horizon predictor would not trade profitably at 0.40 USD/RT.

## 4. Q1–Q10

**Q1 — Data leakage?** **No.** Folds chronological; purge+embargo = h; features PIT-causal;
scaler train-only; selection keyed on VAL only; cost/latency frozen. *Minor:* TEST metrics were
computed and logged during the 30 screens (never used to select). → `DATA_LEAKAGE = PASS`.

**Q2 — Did the 30 experiments run on provably frozen data?** **Almost entirely.**
`data_manifest.json` carries per-file `sha256`. **staging 24/24 match; live 10/11 match.**
The one mismatch is the actively-appended tail `live_fxtm/ticks_20260921.parquet`
(+4,736 rows; ts_max 19:39:06Z → 20:09:07Z). → `PASS_WITH_DATA_GAP` (non-blocking; append is after
the run and inside TEST only).

**Q3 — Which horizons are truly DATA_INSUFFICIENT?** **50 ms, 200 ms, 24 h**
(frozen rule: feed resolution / clean_frac < 0.5 / gap crossing). Adjacent: **1 h** is
`DATA_LIMITED` (eff_n = 196).

**Q4 — Which horizons have enough power for a NO_ALPHA conclusion?** **1 s (eff_n 605,337),
5 s (147,727), 30 s (24,769), 5 min (2,467).** These support `SUPPORTED_NO_ALPHA`.

**Q5 — Does real cost explain the negative net?** **Yes — primarily.** Cost = 0.914 bp;
median 1 s move = 0.346 bp (**2.64×**); 200 ms = 5.64×; 5 s = 1.57×; best gross edge = +0.096 bp
(**9.5× short**). Cost tiers 0.40→1.00 USD/RT never turn net positive.

**Q6 — Is latency the main bottleneck?** **No.** Net is already negative at **0 ms** on every
horizon (−1.004 / −0.880 / −0.771 bp). Latency is secondary, non-monotonic, ≤ ~0.25 bp.

**Q7 — Does L1 lack key microstructure information?** **Yes.** `volume = volume_real = last ≡ 0`
⇒ microprice and **true OFI** are `DATA_GAP`; only a tick-rule proxy was tested. No L2/depth/queue.

**Q8 — Can DUKA fill the gap?** **No for execution** — DUKA is a different venue with its own
spread (0.32–0.63 USD ≈ 1.4–1.7 bp), so it cannot substitute FXTM's cost/spread or prove FXTM
executable alpha. **Yes for** historical microstructure sanity checks, cross-source structure
validation, and price-move scaling. DUKA must **not** be pushed into TEST to "get more data".

**Q9 — Which NO_ALPHA is it?** **A + B + C together** (allowed combination):
`SUPPORTED_NO_ALPHA + DATA_LIMITED_NO_ALPHA + EXECUTION_LIMITED_NO_ALPHA`.

**Q10 — Most reasonable next stage?** **Not decided by this task.** Evidence only:
continue / add data / add execution observability / change alpha hypothesis / stop the HFT route —
the choice belongs to ChatGPT.

## 5. Blocking vs non-blocking

- **BLOCKING_ISSUES = none.**
- NON_BLOCKING: TEST metrics logged in the screen; one live tail file not hash-provable (DATA_GAP);
  913 cross-day-file duplicate timestamps in the live feed.

## 6. FUTURE_RESEARCH_HYPOTHESES (declared, **not tested**)

1. Acquire L2/depth or trade-print data before any microstructure/order-flow alpha claim.
2. Freeze a byte-stable tick snapshot before any future OOS run.
3. If a lower-cost execution venue exists, re-test the 30 s–5 min horizons.

## 7. Evidence files

`DATA_LEAKAGE_AUDIT.{json,md}` · `DATA_SNAPSHOT_AUDIT.{json,md}` ·
`DATA_CAPABILITY_AUDIT.{json,md}` · `EXECUTION_COST_AUDIT.{json,md}` · `LATENCY_AUDIT.{json,md}` ·
`ALPHA_FAILURE_MATRIX.csv` · `ALPHA_POSTMORTEM_RESULT.json` · `SHA256SUMS.txt` ·
driver `run_postmortem_audit.py`.
