# CAND-002 PROTOCOL — Spread-State Execution

`PREREGISTRATION_ID = V3-HFT-PREREG-001` · `LEVEL = 1` · `STATUS = PREREGISTERED (frozen)`

## 8.1 Research question

> Can the spread / execution-cost **state** distinguish economically tradable from economically
> non-tradable short-horizon states?

## 8.2 Explicit prohibition on the directional substitution (hard)

```text
FORBIDDEN : High spread -> LONG
FORBIDDEN : Low spread  -> SHORT
FORBIDDEN : spread -> future direction
```
Testing any of the above requires a **separate** preregistration. Any result that would only be
interpretable as spread→direction is reported as `NOT_REGISTERED_DIRECTIONAL_TEST`.

## 8.3 Registered hypothesis

```text
H002 (ECONOMIC_GATE_HYPOTHESIS, not a directional alpha):
Spread / execution-cost state can distinguish economically tradable from economically
non-tradable short-horizon states.
```

## 9. Inputs (frozen)

```text
FROZEN_INPUTS:
  bid, ask, mid
  spread_usd, spread_bp
  spread_change (Δ spread over the trailing window w)
  recent_quote_arrival (quote count in trailing 1 s)
  recent_return_1s (bp)
  recent_volatility (rolling std of 1-tick returns, window w_v)
WINDOWS (frozen): w = 200 ticks, w_v = 50 ticks
FORBIDDEN after this line: any new feature, indicator, external signal, or data source.
```

## 10. State definition (frozen form)

```text
FORM = CONTINUOUS  (chosen BEFORE seeing any result; the 3-state variant is NOT used)

COST_MULTIPLE(t,h) = cost_bp(t) / EXPECTED_MOVE_bp(t,h)

EXPECTED_MOVE_bp(t,h) = median |mid(t+h') - mid(t)| over TRAIN segments only, at the same horizon h
                        and the same intraday session bucket, updated per TRAIN fold only
```
Rationale for the continuous form: it needs **no invented boundaries**, so no boundary can be tuned
on TEST. The 3-state variant (`NORMAL / ELEVATED / SPIKE`) is **NOT_REGISTERED**.

`EXPECTED_MOVE` is `ESTIMATED_ON_TRAIN` — it may never be re-estimated on TEST.

## 11. Parameter rules

```text
All thresholds are TBD -> PRE_REGISTERED in registries/parameter_registry.json before any data view.
Forbidden: test result -> pick the best threshold.
Frozen here:
  COST_MULTIPLE is CONTINUOUS and therefore needs no boundary.
  The single decision threshold is 1.0 (pay exactly the cost), taken from the cost identity,
  NOT from data.  TRADEABLE iff COST_MULTIPLE(t,h) < 1.0
  A secondary variant at 0.5 is registered as EXPLORATORY and reported separately.
  spread_usd threshold : NONE (the continuous ratio replaces it)
  volatility threshold : NONE
```

## 12. Output (frozen vocabulary)

```text
TRADEABLE      (COST_MULTIPLE < 1.0)  -> escalated to LEVEL-2 for a directional decision
NOT_TRADEABLE  (COST_MULTIPLE >= 1.0) -> WAIT
UNKNOWN        (a required input is DATA_GAP at that instant)
```
`WAIT` is **not a failure**: it states that current economic conditions cannot carry the cost.

CAND-002 never emits a direction, never emits LONG/SHORT, and never places an order.

## 12b. Required baselines (§三十二)

```text
NO_SIGNAL          always NOT_TRADEABLE
COST_ONLY          LEVEL-0's cost map
RANDOMIZED_CONTROL random policy state with a fixed seed (20260922)
```
The registered test is: does CAND-002's state discriminate realised `cost_to_move` better than the
`COST_ONLY` baseline on the same instants?

## 12c. Primary / secondary / exploratory tests (§三十八)

```text
PRIMARY      : AUC / discrimination of realised cost_to_move at h=30s (pre-chosen, not the best h)
SECONDARY    : the same statistic at the other four horizons
EXPLORATORY  : the 0.5 threshold variant
```
Exploratory results may never be promoted to primary.
