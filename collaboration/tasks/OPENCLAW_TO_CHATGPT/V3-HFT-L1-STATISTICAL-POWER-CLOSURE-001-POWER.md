# Power Simulation — V3-HFT-L1-STATISTICAL-POWER-CLOSURE-001

`AUDIT_ONLY / READ_ONLY / OFFLINE`. Machine twin: `power_simulation.json`.

## Method (frozen in `power_plan.json`)

```text
estimator     : one-sample two-sided t-test on the non-overlapping net series (mean != 0)
simulation    : block bootstrap on the EMPIRICAL (CENTRED) non-overlapping net series
                replications = 1000 ; n grid = 100 … 200,000 ; delta added to null samples
analytic      : n = ((z_{1-a/2} + z_power) * sigma / delta)^2 with sigma measured from the data
primary       : analytic (the current data cannot bootstrap n larger than its own non_overlapping_N)
effect sizes  : +0.10 / +0.20 / +0.30 / +0.50 / +1.00 bp  — PREDEFINED hypotheses only
```

**A methodology bug was found and fixed during this task:** the first run bootstrapped the
*uncentered* series, so the test detected the current mean (−1.1 bp) instead of the hypothesised
effect. The series is now centred (zero-mean null) before the effect is added.

## Required EFFECTIVE_N by effect size and power target

(Analytic, primary. `σ` measured per horizon.)

| horizon | σ (bp) | δ=0.10 p80 / p90 / p95 | δ=0.20 p80 / p90 / p95 | δ=0.30 p80 / p90 / p95 | δ=0.50 p80 / p90 / p95 | δ=1.00 p80 / p90 / p95 |
|---|---|---|---|---|---|---|
| 5 s | 1.181 | 1,095 / 1,466 / 1,813 | 274 / 367 / 454 | 122 / 163 / 202 | 44 / 59 / 73 | 11 / 15 / 19 |
| 10 s | 1.586 | 1,975 / 2,644 / 3,270 | 494 / 661 / 818 | 220 / 294 / 364 | 79 / 106 / 131 | 20 / 27 / 33 |
| 30 s | 2.707 | 5,753 / 7,702 / 9,525 | 1,439 / 1,926 / 2,382 | 640 / 856 / 1,059 | 231 / 309 / 381 | 58 / 78 / 96 |
| 60 s | 3.695 | 10,716 / 14,345 / 17,741 | 2,679 / 3,587 / 4,436 | 1,191 / 1,594 / 1,972 | 429 / 574 / 710 | 108 / 144 / 178 |
| 5 min | 8.161 | 52,273 / 69,979 / 86,544 | 13,069 / 17,495 / 21,636 | 5,809 / 7,776 / 9,616 | 2,091 / 2,800 / 3,462 | 523 / 700 / 866 |

### Simulation vs analytic (validation)

The block-bootstrap simulation reproduces the analytic requirement to within the expected margin
and is **more demanding**, as heavy tails demand:

| horizon | δ=0.20, p80 — simulation | analytic | ratio |
|---|---|---|---|
| 5 s | 500 | 274 | 1.8× |
| 10 s | 500 | 494 | 1.0× |
| 30 s | 2,000 | 1,439 | 1.4× |
| 60 s | 5,000 | 2,679 | 1.9× |
| 5 min | *not reachable* (grid capped at n ≤ 2,489) | 13,069 | — |

Where the data supports the check, the empirical-tail inflation factor is **≈1.0–1.9×** — this is
the concrete penalty for the heavy tail observed in the previous task, and it is reported rather
than smoothed away (no winsorization was used for the primary numbers; winsorization is a
sensitivity variant only).

## Is 500 enough? (§二十四)

**No — 500 is a minimum operational gate, not a statistical guarantee.**

| horizon | effective_N now | enough for δ=0.20? | enough for δ=0.10? |
|---|---|---|---|
| 5 s | 148,226 | YES (541× headroom) | YES (135×) |
| 10 s | 74,108 | YES (150×) | YES (38×) |
| 30 s | 24,914 | YES (17×) | YES (4.3×) |
| 60 s | 12,452 | YES (4.6×) | YES (1.2×) |
| 5 min | 2,220 | **NO — needs 13,069 (5.9×)** | **NO — needs 52,273 (23.5×)** |

`POWER_THRESHOLD` is therefore **horizon-specific and effect-size-specific**, not a flat 500.

## FDR-adjusted power (§二十五)

With the inherited replication family of **m = 140** tests (5 horizons × 7 families × 4 models),
BH at q = 0.05 implies a practical single-test α ≈ 3.57e-4, i.e. a required-N multiplier of
**×1.82** over the single-test requirement:

| horizon | req eff_N δ=0.20 p80 (single) | with FDR m=140 |
|---|---|---|
| 5 s | 500 | 500 |
| 10 s | 500 | 900 |
| 30 s | 2,000 | 2,621 |
| 60 s | 5,000 | 4,880 |
| 5 min | 13,069 (analytic) | 23,791 |

Even with the FDR penalty, **5 s–60 s remain already powered**; 5 min does not.
