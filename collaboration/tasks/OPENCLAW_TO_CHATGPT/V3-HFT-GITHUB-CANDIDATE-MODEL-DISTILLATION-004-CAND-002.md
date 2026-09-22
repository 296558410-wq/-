# CAND-002 — Spread-State Execution

`CANDIDATE_ID = V3-HFT-CAND-002` · `ROLE = SECONDARY_CANDIDATE` · `STATUS = UNTESTED`
`PARAMETERS = TBD_IN_PRE_REGISTERED_EXPERIMENT`

## MODEL_PURPOSE

Decide **whether any action can be economic at this instant**, from the spread/cost regime alone.
It emits a *policy state*, never a direction. A `NOT_TRADEABLE` output is a success.

## MARKET_ASSUMPTION

As CAND-001. Cost is dominated by the spread (0.914 bp measured round trip).

## THE CENTRAL QUESTION (§八.4)

> *Is spread a predictor of the market, or merely a description of the transaction cost?*

**Answer from the distilled evidence: it is primarily a COST and a REGIME variable, not a directional
predictor.** No repo examined demonstrates a stable relationship between spread state and *expected
future move*; the repos that use spread use it as (a) a cost to be compared against the edge
(`siddhantsingh-1` cost hurdle; `himagna16` break-even move; `aryansiwach` quoted/effective/realised
spread decomposition) or (b) a filter that gates whether a target is reachable (`n30dyn4m1c`
cost-multiple gate; `RobertN1D` rolling p90 spread + spike gate). `himagna16` states the sharpest
version: *"inefficient at the mid, efficient at the touch"* — i.e. the apparent edge disappears once
the spread is paid. Spread is therefore classified:

```text
SPREAD = COST_VARIABLE  (primary)
       + MARKET_STATE_VARIABLE  (secondary: a regime indicator that conditions *cost* and *volatility*,
                                 NOT a direction; supported by aryansiwach's stress-regime inversion)
```
Any claim that spread *predicts direction* must be produced by a pre-registered experiment, not assumed here.

## INPUTS / STATE

```text
INPUTS : spread_bp, spread_pctile_n, rv_n, quote_arrival_rate, time_since_last_quote
STATE  : regime labels (NORMAL_SPREAD / ELEVATED_SPREAD / SPIKE) OR the continuous ratio
         cost_to_move(t) = cost_bp(t) / median_abs_move(t,h)          (CMP-01, CMP-04)
```
The **form** (3 discrete states vs a continuous ratio) is not fixed here: the discrete form is the
readable variant, the continuous ratio is the information-preserving one. Choosing between them is a
pre-registered decision.

## SIGNAL / LABEL

```text
SIGNAL : none directional. Output = POLICY_STATE ∈ {TRADEABLE, NOT_TRADEABLE, UNKNOWN}
LABEL  : realised cost_to_move realised_ratio(t,h) = cost_bp(t) / |mid(t+h)-mid(t)|   (CMP-03/CMP-04)
```
`UNKNOWN` is mandatory when the required inputs are `DATA_GAP` for the decision being contemplated.

## GROSS_EDGE / COST / NET_EDGE

```text
GROSS_EDGE : not produced by this candidate (it does not forecast direction)
COST       : the object of study (spread + commission; impact/opportunity as DATA_GAP)
NET_EDGE   : used only as a CAP: if cost >= expected_move, NET_EDGE <= 0 by construction
```

## ENTRY / WAIT / EXIT

```text
ENTRY (TRADEABLE)   iff the cost regime permits a positive net edge for the intended horizon
WAIT  (NOT_TRADEABLE) otherwise  -- the default and a valid terminal state
EXIT                not owned by this candidate
```

## UNCERTAINTY

```text
EXECUTION_UNCERTAINTY (spread varies; p90/p99 matter, not the median)
DATA_UNCERTAINTY      (impact/opportunity unmeasurable on FXTM)
EDGE_UNCERTAINTY      n/a (no edge claim)
```

## DATA_REQUIREMENT

L1 only. **This is the candidate with the least data dependency** and the highest FXTM compatibility.

## PARAMETERS

```text
percentile window n, state boundaries, cost_to_move thresholds, cost tier  -> ALL TBD
```
No boundary may be derived from the current data.

## FAILURE_MODES

```text
F-01 COST_ERASED_ALPHA   gate set so loosely that it passes uneconomic trades
F-05 SELECTION_BIAS      picking the regime boundaries after seeing results
F-13 REGIME_AS_TIME      the regime becoming a proxy for time-of-day instead of microstructure
```

## OOS_REQUIREMENT

Same as CAND-001. Additionally: the regime boundaries must be fixed **before** the OOS window is seen.

## FXTM_COMPATIBILITY

`HIGH` — the most compatible of the three.

## EVIDENCE_LEVEL

Anchored on **E3–E4** (`himagna16`, `aryansiwach`, `siddhantsingh-1`) for the cost/regime mechanics.
**The candidate itself is E0/UNTESTED.**
