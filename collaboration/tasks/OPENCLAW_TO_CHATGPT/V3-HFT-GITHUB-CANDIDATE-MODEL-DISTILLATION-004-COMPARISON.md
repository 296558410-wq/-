# Candidate Model Comparison

**No `BEST` / `WINNER` / `MOST_PROFITABLE` ranking exists here.** Roles are structural, not competitive.
All three are `UNTESTED`. `PARAMETERS = TBD_IN_PRE_REGISTERED_EXPERIMENT` for all three.

## Role assignment

```text
CAND-001  PRIMARY_CANDIDATE      general form: hosts state/edge/cost/gate/exit behind one interface
CAND-002  SECONDARY_CANDIDATE    the policy/filter view; fewest assumptions, highest FXTM fit
CAND-003  EXPLORATORY_CANDIDATE  depends on the least-settled piece (edge-decay functional form)
CAND-004  PARKED                 passive/queue market making  (fill/queue = DATA_GAP)
CAND-005  PARKED                 cross-venue context         (other venue != FXTM pool)
```

## Side-by-side

| dimension | CAND-001 Markout Gate | CAND-002 Spread-State | CAND-003 AS-Conditional Exit |
|---|---|---|---|
| produces | TAKE / WAIT (+EXIT via CMP-08) | TRADEABLE / NOT_TRADEABLE / UNKNOWN | HOLD / EXIT |
| directional? | **yes** (via CMP-02) | **no** | no (uses existing position) |
| components | CMP-01..09 (9) | CMP-01,04,06,07,09 (5) | CMP-01,03,05,06,08,09 (6) |
| anchor evidence | **E4** (snowkings, siddhantsingh) | **E3–E4** (himagna16, aryansiwach) | **E3–E4** (AshJha0, snowkings, KlishevDA) |
| FXTM data | L1; `impact`/`opportunity` = DATA_GAP | **L1 only — least dependent** | L1 for timing; AS class PARTIAL; maker exit DATA_GAP |
| models cost? | yes, explicitly (CMP-04) | **cost IS the object** | yes, incl. the **second** crossing |
| models adverse selection? | as an expected term (only if PIT-estimable) | no | **yes — as the CMP-05 class** |
| handles edge decay? | no (delegated) | no | **yes — its purpose (form TBD)** |
| look-ahead risk | LOW structural, medium procedural | **MEDIUM** (`cost/realised move` is definitionally post-hoc) | **HIGH** (multi-instant; a fitted decay curve is a look-ahead device) |
| selection-bias surface | **LARGEST** (h, windows k, model class, threshold, margin) | concentrated in the **boundaries** | medium (decay form + threshold) |
| cost-kill vulnerability | **highest** (directional taker at short horizons) | designed to *detect* the kill, not avoid it | medium (exit cost counted twice) |
| can it output WAIT? | yes (a valid success) | yes (the default) | HOLD |
| newest unresolved piece | nothing structural | spread: predictor or cost? (answered: **cost/regime**) | **the decay functional form** |
| pre-registration readiness | READY_FOR_PRE_REGISTRATION | READY_FOR_PRE_REGISTRATION | READY_FOR_PRE_REGISTRATION |

## What each candidate is *for*

```text
CAND-001  tests the central economic inequality:  expected net edge > 0 after the full cost chain
CAND-002  tests whether an action is economic at all in the current cost regime (a filter, not an alpha)
CAND-003  tests whether the *timing of the exit* can be improved by monitoring the remaining edge
```

## Shared interface (§三十二)

```text
ModelState -> GrossEdge -> ExecutionCost -> AdverseSelectionRisk -> NetEdge -> Decision(TAKE|WAIT|EXIT)
```
All three express this interface. CAND-002 supplies `ExecutionCost` and a policy state;
CAND-001 supplies the gate; CAND-003 supplies the exit decision. None of them is a strategy on its own.

## Hermes payload (§三十三)

```text
Hermes receives:  gross_edge, expected_cost, expected_adverse_selection, net_edge, confidence,
                  edge_lifetime, execution_state, reason_codes
Hermes decides:   TAKE / WAIT / EXIT
```
Hermes never receives "buy gold".

## Explicit non-claims

```text
no candidate has been trained, backtested, or traded
no parameter has been chosen
no threshold in any spec is a decision
no combination of components may be executed before a pre-registered experiment
```
