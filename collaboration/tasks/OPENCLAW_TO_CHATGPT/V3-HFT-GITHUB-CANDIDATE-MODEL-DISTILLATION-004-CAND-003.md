# CAND-003 — Adverse-Selection Conditional Exit

`CANDIDATE_ID = V3-HFT-CAND-003` · `ROLE = EXPLORATORY_CANDIDATE` · `STATUS = UNTESTED`
`PARAMETERS = TBD_IN_PRE_REGISTERED_EXPERIMENT`

## MODEL_PURPOSE

Replace `ENTRY → fixed SL → fixed TP` with an **edge monitor**:

```text
ENTRY -> EDGE MONITOR -> edge alive? -> edge weakening? -> adverse selection? -> EXIT
```
Exit when the **expected remaining edge** falls below the **expected cost of exiting**.

## THE FOUR FAILURE CLASSES (must never be merged into "LOSS", §9.3)

```text
A ENTRY_WRONG        the direction was wrong from the start
B EDGE_DECAY         the direction was right but the edge decayed before capture
C ADVERSE_SELECTION  the fill itself was toxic (price moved against after execution)
D COST_EROSION       the edge existed but the round trip cost consumed it
```
Class attribution requires comparing the realised path against the ex-ante expected path — a
**diagnostic** operation, performed after the trade, on data not available at entry.

## INPUTS / STATE

```text
INPUTS : state(t) (CMP-01) + position + elapsed time + second-crossing cost estimate
STATE  : EDGE_ALIVE / EDGE_WEAKENING / ADVERSE / DEAD  -- with an explicit UNKNOWN state
```

## LABEL AND THE DECAY FUNCTION

```text
E(t) = expected REMAINING edge at time t after entry        (CMP-08)
measured by: the empirical markout curve of the entry cohort (CMP-03), a DIAGNOSTIC instrument
candidate functional forms (NONE is fixed here):
     exponential   E(t) = E0 * exp(-lambda t)
     linear        E(t) = max(0, E0 - a*t)
     hazard        exit intensity h(t) from a survival model (as in Trumplus' discrete-time hazard)
     empirical     no closed form; the measured curve is used directly
CHOSEN FORM = TBD_IN_PRE_REGISTERED_EXPERIMENT
```
**No functional form is asserted.** The distillation found empirical markout curves
(`KlishevDA`, `snowkings`) and a survival/hazard *formulation* (`Trumplus`), but no repo derives a
validated closed-form `E(t)` for a venue like FXTM. The empirical curve is the honest instrument.

## EDGE_LIFETIME (concept, §十)

```text
T0 = entry ; EDGE(t) over T1, T2, T3, ...
EDGE_LIFETIME = the horizon at which E(t) falls below the exit cost
MODEL_CONCEPT only -- NOT estimated from V3's current data in this task
```

## GROSS_EDGE / COST / ADVERSE_SELECTION / NET_EDGE

```text
GROSS_EDGE(t)          = remaining expected gross markout from t to the exit horizon   (CMP-03)
COST_OF_EXIT(t)        = one more spread crossing + commission                          (CMP-06)
                         -- the "second spread payment" (§十三); may NOT be omitted
ADVERSE_SELECTION(t)   = measured post-fill drift; used to set the ADVERSE class only    (CMP-05)
NET_REMAINING_EDGE(t)  = GROSS_EDGE(t) - COST_OF_EXIT(t)
```

## EXIT RULE

```text
EXIT iff NET_REMAINING_EDGE(t) < 0        -- i.e. E[remaining edge] < E[exit cost]
HOLD otherwise
```
This is **not** "exit at a loss" and **not** "exit at a fixed profit". It is the §十二 target.
Whether the comparison should include the uncertainty margin is a pre-registered decision.

## THE SECOND SPREAD PAYMENT (§十三)

```text
ENTRY -> floating profit -> EDGE DECAY -> no exit -> reversal -> EXIT -> pays the spread again
```
Distilled mitigations and their honest status:

| mitigation | status on FXTM |
|---|---|
| limit/maker exit at the target (`n30dyn4m1c`: server-side limit at the mean) | **theoretical** — depends on a fill model FXTM cannot supply |
| touch exit / spread-aware exit | **theoretical** for the same reason |
| market exit | **executable** — pays the spread, but it is the only certain option |
So a `maker exit` may be *modelled* but must never be *assumed*: on FXTM it is `DATA_GAP`-dependent.

## UNCERTAINTY

```text
EDGE_UNCERTAINTY      the decay estimate has the widest CI of the three candidates
EXECUTION_UNCERTAINTY the exit cost is a *second* spread crossing, itself variable (p90 matters)
DATA_UNCERTAINTY      the toxicity class (C) is only L1-measurable without queue data
```

## DATA_REQUIREMENT

L1 sufficient for the *exit timing* experiment; **class C (true adverse selection) is only partially
observable** without real depth/queue/trade flow.

## PARAMETERS

```text
E0 estimator, decay form, exit threshold, uncertainty margin, horizon grid  -> ALL TBD
```

## FAILURE_MODES

```text
F-03 LOOK_AHEAD        the decay curve fitted on the same window it is evaluated on
F-04 POST_FILL_LEAKAGE realised markout driving the timing rule (it is diagnostic-only)
F-05 SELECTION_BIAS    choosing the exit rule after seeing which one reduces losses
F-07 TAIL_DEPENDENCE   exit benefits concentrated in a few paths
```

## OOS_REQUIREMENT

Pre-registered; the decay form and the threshold must be frozen **before** the OOS window is opened.
Price-shift invariance (`AshJha0`) is required as a unit test on any cost/decomposition used here.

## FXTM_COMPATIBILITY

`MEDIUM-HIGH` for the *timing* rule; `LOW` for class-C attribution and for any maker exit.

## EVIDENCE_LEVEL

Anchored on **E3–E4** (`AshJha0` IS/opportunity + price-shift invariance, `snowkings` remaining-hold
accounting, `KlishevDA` markout curves, `Trumplus` hazard formulation).
**The candidate itself is E0/UNTESTED** — and it is the **least established** of the three, because
the decay functional form is not settled by any source.
