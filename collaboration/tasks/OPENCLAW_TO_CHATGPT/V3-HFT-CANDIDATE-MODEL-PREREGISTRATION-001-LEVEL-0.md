# LEVEL-0 — Cost-Only Baseline

`PREREGISTRATION_ID = V3-HFT-PREREG-001` · `LEVEL = 0` · `STATUS = PREREGISTERED (frozen)`
`MODE = PREREGISTRATION_ONLY / READ_ONLY`

## 7.1 Purpose

Establish the simplest economic baseline for the same decision instants:

```text
EXPECTED_MOVE   vs   ROUND_TRIP_COST
```

No predictor, no signal, no model fitting. LEVEL-0 answers exactly one question:

> **What is the relationship between the typical price move available in this market and the real
> cost of capturing it?**

## 7.2 Forbidden inputs (hard)

```text
CAND-001 signal        FORBIDDEN
CAND-003 decay / E(t)  FORBIDDEN
future markout         FORBIDDEN
future realised PnL    FORBIDDEN
any decision rule that uses a future quantity as an input   FORBIDDEN
```
LEVEL-0 uses **only**: the decision timestamp, the bid/ask at that instant, cost constants, and
historical (backward) move statistics.

## 7.3 This level is not for making money

LEVEL-0 never trades. It produces a **cost-to-move map**, which every later level must be measured
against. Its outputs:

```text
cost_to_move(h) = cost_bp(t) / median_abs_move_bp(h)
coverage        = fraction of decision instants where median_abs_move_bp(h) > cost_bp
per horizon h ∈ {5s, 10s, 30s, 60s, 300s}      (reference-only: 1s, 2s)
```

## 7.4 Frozen definitions

```text
DECISION INSTANT : 1-second as-of grid, freshness <= 5000 ms (last tick at or before the grid time)
MOVE             : median |mid(t+h) - mid(t)| in bp, computed on the SAME segment only
COST             : 0.914 bp (0.40 USD round trip, CALIBRATION_20RT_20260921)
SEGMENT RULE     : mid(t) and mid(t+h) must lie in the same valid session segment
                   (no weekend / gap / snapshot boundary crossing) else the sample is CENSORED
REPORTING        : raw_N, effective_N, median, p75, p90, coverage, and a five-tier cost sensitivity
                   0.40 / 0.50 / 0.60 / 0.80 / 1.00 USD per round trip
```

## 7.5 Frozen success criterion (informational, not a trade claim)

```text
LEVEL-0 result is reported as a MAP, never as a strategy:
  TRADABLE_BY_COST(h)      iff median_abs_move(h) > cost_bp
  BLOCKED_BY_COST(h)       otherwise
```
`BLOCKED_BY_COST` at a horizon is a **legitimate and expected** outcome (it is the state V3 already
measured for h ≤ 2 s) and does not invalidate the protocol.

## 7.6 Relationship to later levels

LEVEL-1/2/3 must each be compared against LEVEL-0 on the **same instants, same horizons, same cost
tiers, same segments**. A later level that cannot beat LEVEL-0's cost map is reported as such.
