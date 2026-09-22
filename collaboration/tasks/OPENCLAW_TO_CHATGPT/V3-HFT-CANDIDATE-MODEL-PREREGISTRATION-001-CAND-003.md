# CAND-003 PROTOCOL — Adverse-Selection Conditional Exit

`PREREGISTRATION_ID = V3-HFT-PREREG-001` · `LEVEL = 3` · `STATUS = PREREGISTERED (frozen)`
**This is the leakage-prone level and is handled separately.**

## 22. Registered question

> After entry, does the expected remaining edge fall below the cost of exiting, such that a
> conditional exit reduces cost erosion and adverse selection?

## 23. Four-class outcome taxonomy (frozen; no forced classification)

```text
ENTRY_WRONG         direction wrong from the start
EDGE_DECAY          direction right, edge decayed before capture
ADVERSE_SELECTION   the fill itself was toxic (post-fill drift against the position)
COST_EROSION        the edge existed but the round-trip cost consumed it
UNCLASSIFIED        cannot be reliably attributed
```
Every trade must carry one of these. `UNCLASSIFIED` is mandatory when attribution is not reliable —
forcing a class is a `PROTOCOL_VIOLATION`.
Classification uses post-trade diagnostics and is **DIAGNOSTIC_ONLY**; it may never feed the exit rule.

## 24. Edge decay (frozen as an ASSUMPTION, not a fact)

```text
REGISTERED_FORM       : E(t) = E0 * exp(-lambda * t)
STATUS                : MODEL_ASSUMPTION  (declared as such everywhere it appears)
ALTERNATIVES          : linear, hazard and empirical-curve forms are NOT registered for round 1
```
GitHub evidence shows no source derives `E(t)` from microstructural primitives; the exponential form
is a **fit**. It must be described as an assumption in every result table.

## 25. Decay parameters (frozen allocation)

```text
lambda (and hence t_half = ln2/lambda) : ESTIMATED_ON_TRAIN only, by log-linear OLS
                                         on the TRAIN markout curve
NOT_ALLOWED_TO_ESTIMATE_ON_TEST : TRUE   (no re-estimation after the test boundary is opened)
E0                                     : ESTIMATED_ON_TRAIN
```

## 26. Exit rule (registered candidate structure)

```text
EXIT iff  EXPECTED_REMAINING_EDGE(t) - EXPECTED_EXIT_COST - UNCERTAINTY_MARGIN < 0
HOLD otherwise
```
`EXPECTED_EXIT_COST`, the threshold form and the uncertainty margin are frozen here; no threshold may
be tuned on TEST.

## 27. Second spread crossing (mandatory)

```text
TOTAL_COST = ENTRY_COST + EXIT_COST
EXIT_COST  includes one further spread crossing + commission
```
Modelling only the entry cost is a `PROTOCOL_VIOLATION`. Evidence this matters: an E3 source
(`zj092912`) shows the same strategy at mark-to-mid Sharpe 1.08 (+$463,326) and realised
−$24,931,458 once both crossings are charged.

## 28. Post-hoc information is forbidden as an exit input

```text
future markout / future MFE / future MAE / future reversal    ->  LABEL / DIAGNOSTIC ONLY
```
These may be used to *evaluate* the exit rule; they may never *drive* it in real time.

## 29. Look-ahead protection (frozen timeline)

```text
T0   | available L1 (bid/ask/mid/spread/history)            AVAILABLE
T0   | model state, decision                                AVAILABLE
T0+L | execution                                             MODELLED (L ≈ 279 ms measured RTT)
T+100ms / T+250ms / T+500ms / T+1s / T+2s / T+5s / T+30s     LABEL_ONLY
```
No future node may flow back to T0. At every later decision instant `Tk`, only ticks with `ts <= Tk`
may be used.

## 30. Self-impact contamination rule (frozen)

```text
MIN_MARKOUT_HORIZON_MS = 500
RULE: a fill's own execution is not to be attributed to market adverse selection.
      Any markout measured at a horizon shorter than MIN_MARKOUT_HORIZON_MS is NOT usable as
      evidence of adverse selection (it is inside the execution window: measured RTT ~279 ms).
```
This follows the distilled practice of imposing a minimum horizon before grading a fill, precisely so
that the trade's own impact is not counted as toxicity.

## 30b. Same-entry comparison (hard, §四十七)

CAND-003's improvement must be measured as a **same-entry comparison**:

```text
same entries · same data · same cost · only the EXIT MECHANISM differs
```
Otherwise the improvement cannot be attributed to the exit rather than to the entry.

## 30c. Combination tuning is forbidden (§四十八)

```text
FORBIDDEN: CAND-002 filter + CAND-001 signal + CAND-003 exit -> search the best combination
ROUND 1  : isolate mechanisms; ONE MODEL AT A TIME
```
Round-1 promotion of LEVEL-3 requires LEVEL-2's registered result to be reported first, unchanged.
