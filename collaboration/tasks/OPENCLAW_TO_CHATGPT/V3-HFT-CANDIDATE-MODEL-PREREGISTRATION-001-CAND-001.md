# CAND-001 PROTOCOL — Execution-Aware L1 Markout Gate

`PREREGISTRATION_ID = V3-HFT-PREREG-001` · `LEVEL = 2` · `STATUS = PREREGISTERED (frozen)`

## 13.1 Research question

> Can L1 information produce an expected gross edge large enough to leave a **positive executable net
> edge after the real round-trip cost**?

## 14. Registered structure (a model STRUCTURE, not a validated identity)

```text
EXPECTED_GROSS_EDGE
  - EXPECTED_EXECUTION_COST
  - EXPECTED_ADVERSE_SELECTION
  = EXPECTED_NET_EDGE
```
Each term's estimation method is frozen below. The equality is a **decomposition convention**; it does
not imply the terms are correctly estimated.

## 14b. Registered estimators (frozen)

```text
EXPECTED_GROSS_EDGE(t,h)      model class ∈ {ridge, decision_tree(depth<=3)}; target = MID_MARKOUT;
                              NO deep/sequence model (no queue data exists to justify one)
EXPECTED_EXECUTION_COST(t)    spread_bp(t) + commission_bp          (measured, not fitted)
EXPECTED_ADVERSE_SELECTION(t) PARTIAL: a LAGGED (PIT) estimate of the entry-cohort markout drift;
                              if not estimable at t  ->  DATA_GAP  (never 0)
EXPECTED_NET_EDGE(t,h)        the subtraction above, per decision instant
DECISION                      TAKE iff  EXPECTED_NET_EDGE - UNCERTAINTY_MARGIN > 0
                              WAIT  otherwise
UNCERTAINTY_MARGIN            = the half-width of the 95% moving-block-bootstrap CI of the
                                expected net edge, re-estimated on TRAIN only (parameter-free rule)
```

## 15. Cost (forced)

```text
ROUND_TRIP_COST = 0.40 USD  ≈ 0.914 bp
SOURCE          = CALIBRATION_20RT_20260921
FORBIDDEN       = 0.1375 USD, 0.314 bp, and any other legacy anchor
```

## 16. No silent zeros (hard)

```text
impact            -> not measurable on FXTM L1      -> DATA_GAP
opportunity cost  -> needs a fill/participation model -> DATA_GAP
fill uncertainty  -> no real queue                  -> DATA_GAP
```
Writing `0` for any of these is `PROTOCOL_VIOLATION`. Required phrasing: `DATA_GAP` or
`UNMODELED_COMPONENT`, **and** an explicit statement of the direction of the resulting bias in the
final report (an omitted cost term biases the net edge **upward**).

## 17. Label taxonomy (four distinct objects, frozen meanings)

```text
FUTURE_MARKOUT          = d * (mid(t+h) - mid(t))                 LABEL_ONLY
EXECUTION_MARKOUT       = d * (mid(t+h) - entry_exec(t+L))         LABEL_ONLY
COST_ADJUSTED_MARKOUT   = MID_MARKOUT - cost_bp                    LABEL_ONLY
REALIZED_PNL            = the accounting result of an actual fill  ONLY_AFTER_EXECUTION (diagnostic)
```
`entry_exec` = ask for LONG, bid for SHORT. **Future outcomes are LABEL_ONLY and may never enter the
decision features.**

## 18. Horizons (frozen, all reported)

```text
PRIMARY          : 5 s, 10 s, 30 s, 60 s, 300 s
REFERENCE_ONLY   : 1 s, 2 s       (cost-blocked; reported for continuity, excluded from selection)
FORBIDDEN        : 50 ms, 200 ms  (data-insufficient)
```
All five primary horizons must be reported in full. Selective reporting of one horizon is
`PROTOCOL_VIOLATION`.

## 19. Sample boundary rule (hard)

Every sample must satisfy

```text
decision timestamp + future horizon  ⊆  the SAME valid session segment
```
Crossing a weekend, a missing-data gap, a session discontinuity or a snapshot boundary makes the
sample `HORIZON_CENSORED` and it is **excluded** — never 0, never interpolated.

## 20. Purge / embargo (frozen)

```text
SPLIT   : chronological by UTC day; no shuffling
PURGE   : >= maximum label horizon = 300 s
EMBARGO : = 300 s (same rule; a separate embargo constant is NOT registered)
```
Adjusting either after the experiment starts is `PROTOCOL_VIOLATION`.

## 20b. Baselines for LEVEL-2 (§三十二)

```text
NO_SIGNAL            always WAIT
COST_ONLY            LEVEL-0 map
MOMENTUM_BASELINE    sign of the trailing 1 s return
RANDOMIZED_CONTROL   seeded (20260922) random TAKE/WAIT at the same rate
```
The registered claim is not "the model makes money"; it is "the gate beats COST_ONLY and the
randomised control at the same decision rate, on the same instants".

## 20c. Complexity accounting (§三十三)

Reported for every level: `feature_count, parameter_count, model_class, number_of_decisions,
trade_count, turnover, gross_edge, net_edge, net_pnl, cost_coverage, max_drawdown`.
A complexity increase that yields no material net improvement is reported as such and **is not an
improvement**.
