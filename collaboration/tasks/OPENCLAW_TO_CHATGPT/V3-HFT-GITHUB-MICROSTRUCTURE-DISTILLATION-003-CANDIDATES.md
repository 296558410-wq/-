# Candidate Model Spec — V3-HFT-CANDIDATE-* (UNTESTED)

**Status vocabulary used throughout:** `READY_FOR_V3_EXPERIMENT` means the §三十八 conditions are met
*as a candidate to be tested* — it is **not** evidence of profitability. `PARKED` means a gate fails.
No candidate here has been tested, and none authorises trading (§二十七).

---

## CANDIDATE-001 — Execution-Aware L1 Markout Gate

```text
CANDIDATE_ID = V3-HFT-CANDIDATE-001
NAME         = Execution-Aware L1 Markout Gate
DATA         = FXTM L1 (bid/ask/ts) - available now
INPUT        = spread, spread_pctile_200t, mid_return_1s, displacement_5s, mom_3t/10t,
               rev_5t, overshoot_z, rv_50t, absret_10t, quote_update_rate_1s,
               time_since_last_quote_s, tick_rule_proxy_20t/50t
PREDICTION   = expected_gross_markout(h), expected_adverse_selection(h),
               expected_execution_cost(h)  ->  expected_net_edge(h)
DECISION     = TAKE / WAIT / EXIT     (never bare LONG/SHORT)
LABEL        = direction * (mid(t+h) - entry_exec_price) - cost_bp(t)   (net, segment-guarded)
COST         = 0.914 bp / RT (canonical), stress 1.0/1.25/1.5/2.0
EXECUTION    = taker (market), modelled at the measured ~279 ms RTT
GATES        = Gate1 mechanism clear ✓ | Gate2 FXTM L1 observable ✓ | Gate3 net>cost UNTESTED
FRESH EVIDENCE = V3 measured: gross exists but ~9.5x below cost; cost/median-move > 1 for h<=2s
KNOWN FAILURE  = COST_ERASED_ALPHA ; TAIL_DEPENDENCE ; MECHANICAL_SIGNAL_ARTIFACT
STATUS         = READY_FOR_V3_EXPERIMENT (as a falsifiable test of the gate itself)
```

## CANDIDATE-002 — Spread-Regime Execution Policy (non-directional)

```text
CANDIDATE_ID = V3-HFT-CANDIDATE-002
NAME         = Spread-Regime Execution Policy
DATA         = FXTM L1 - available now
INPUT        = spread_bp, spread_pctile_200t, rv_50t, quote_update_rate_1s, arrival intensity
OUTPUT       = POLICY STATE: TRADEABLE / NOT_TRADEABLE / UNKNOWN   (no price forecast)
MECHANISM    = decide ONLY whether any action can be economic at this instant, from the cost regime;
               a WAIT is a valid, valuable output
LABEL        = not a return label: a classification of realised cost-to-move (cost / median |move|)
COST         = canonical + stress
GATES        = Gate1 ✓ | Gate2 ✓ | Gate3 UNTESTED (policy claims no edge of its own)
KNOWN FAILURE  = regime labels can be a proxy for time-of-day rather than microstructure
STATUS         = READY_FOR_V3_EXPERIMENT
NOTE           = this is a *filter*, not an alpha; it is the natural home for the L1 route's
                 one robust finding (cost dominates below ~2 s).
```

## CANDIDATE-003 — Adverse-Selection-Conditional Exit

```text
CANDIDATE_ID = V3-HFT-CANDIDATE-003
NAME         = Adverse-Selection-Conditional Exit
DATA         = FXTM L1 - available now
INPUT        = entry state (spread regime, volatility, flow proxy) + evolving markout
LOGIC        = condition the EXIT on the measured post-fill markout, not only on PnL:
               exit when the markout trajectory signals adverse selection
LABEL        = markout trajectory per horizon (L1-computable)
COST         = canonical; exit cost is a second spread crossing (must be counted twice)
GATES        = Gate1 ✓ | Gate2 ✓ | Gate3 UNTESTED
KNOWN FAILURE  = V3 measured median adverse selection ~0 overall, positive (+0.05..+0.53 bp) only in
                 high-spread/high-vol states -> the mechanism is CONDITIONAL and small
STATUS         = READY_FOR_V3_EXPERIMENT
```

## CANDIDATE-004 — Passive / Queue-Aware Market Making  → **PARKED**

```text
CANDIDATE_ID = V3-HFT-CANDIDATE-004
NAME         = Passive Fill + Inventory-Skewed Quoting (spread capture)
DATA         = REAL L2 depth + queue position + signed trade flow
GATES        = Gate1 ✓ (mechanism clear, well documented in literature and public repos)
               Gate2 ✗ FAILS - FXTM cannot observe: fill probability, queue position,
                          signed/aggressive flow (DOM is SYNTHETIC/aggregated, no historical DOM)
               Gate3 UNTESTED - cannot even be simulated without P(fill)
STATUS       = PARKED  ->  MICROSTRUCTURE_MODEL_DATA_BLOCKED (this branch only)
```

## CANDIDATE-005 — Cross-Venue Context Filter (auxiliary)

```text
CANDIDATE_ID = V3-HFT-CANDIDATE-005
NAME         = Cross-Venue Context Filter (CME GC / other-venue L2 as context only)
GATES        = Gate1 ✓ | Gate2 ✗ (OTHER_VENUE data cannot represent FXTM's pool)
STATUS       = PARKED / AUXILIARY_ONLY (D)  - permitted only as a macro-context descriptor
```

---

## Gate summary (§二十四)

| candidate | Gate 1 mechanism | Gate 2 FXTM data | Gate 3 cost survival | status |
|---|---|---|---|---|
| 001 Execution-Aware L1 Markout Gate | ✓ | ✓ | UNTESTED | READY_FOR_V3_EXPERIMENT |
| 002 Spread-Regime Execution Policy | ✓ | ✓ | UNTESTED | READY_FOR_V3_EXPERIMENT |
| 003 AS-Conditional Exit | ✓ | ✓ | UNTESTED | READY_FOR_V3_EXPERIMENT |
| 004 Passive / Queue-aware MM | ✓ | **✗ DATA_GAP** | UNTESTED | **PARKED** |
| 005 Cross-Venue Context | ✓ | ✗ OTHER_VENUE | UNTESTED | PARKED (auxiliary) |

**3 candidate mechanisms are ready to be tested; 2 are parked for data reasons.** The parked pair
constitutes the `MICROSTRUCTURE_MODEL_DATA_BLOCKED` branch (§四十一).

## What a candidate must still show (§二十六 checklist)

```text
1 mechanism clear            ✓ for 001/002/003
2 data requirement clear     ✓ (L1)
3 label clear                ✓ (net, segment-guarded, execution-price based)
4 execution logic clear      ✓ (TAKE/PASSIVE/WAIT/EXIT)
5 cost model explicit        ✓ (0.914 bp, stress tiers)
6 OOS method explicit        ✓ (chronological split + purge/embargo + effective_N)
7 failure modes known        ✓ (see negative_evidence_registry.json)
8 FXTM transferability       ✓ for 001/002/003, ✗ for 004/005
```
