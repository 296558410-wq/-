# CAND-001 — Execution-Aware L1 Markout Gate

`CANDIDATE_ID = V3-HFT-CAND-001` · `ROLE = PRIMARY_CANDIDATE` · `STATUS = UNTESTED`
`PARAMETERS = TBD_IN_PRE_REGISTERED_EXPERIMENT` (no threshold in this file is a decision)

## MODEL_PURPOSE

Decide, at each decision instant, whether a **taker** order is worth placing at horizon `h`, by
comparing an **expected gross markout** against the **full expected execution cost**, and to abstain
otherwise. It is a *gate*, not a signal generator: it can host candidate 002 (state) and 003 (exit).

## MARKET_ASSUMPTION

FXTM XAUUSD, **L1 quote-only** (bid/ask/timestamp). Market orders cross the spread. No real L2:
queue position, true OFI, trade flow and fill probability are `DATA_GAP`; the retail DOM is
`SYNTHETIC_OR_AGGREGATED`. Round-trip cost is the measured **0.914 bp / 0.40 USD**
(`CALIBRATION_20RT_20260921`); the 0.314 bp model is forbidden.

## INPUTS (CMP-01)

```text
bid, ask, mid, spread_bp, spread_pctile_n, rv_n, quote_arrival_rate, time_since_last_quote,
displacement_1s, displacement_5s, mom_k, rev_k, tick_rule_proxy_n      (all as-of, PIT)
FORBIDDEN as inputs: true OFI, microprice, size imbalance, queue position, trade flow,
                     fill probability, any post-fill markout
```

## STATE (CMP-01)

`state(t) = [spread_bp, spread_pctile_n, rv_n, quote_rate, flow_proxy_n, displacement_1s, displacement_5s]`
built with **backward as-of joins only**. No centred or forward-shifted window may appear.

## SIGNAL (CMP-02)

`signal(t) = g(state(t))` → an estimate of the signed expected move. Model class is deliberately
unspecified: `g ∈ {linear, shallow tree}`; **no deep sequence model** (no queue data to justify it).
On FXTM the OFI/microprice terms of the source repos must be **dropped**, so `g` is a degraded version.

## LABEL (CMP-03)

```text
gross label   : d * (mid(t*)-mid(t))            t* = first real tick >= t+h, SAME SEGMENT
executable    : d * (mid(t*) - entry_exec(t+L)) entry_exec = ask(t+L) for LONG, bid(t+L) for SHORT
net label     : executable - cost_bp(t)
```
Three-way outcome reporting (favourable / unchanged / adverse) is mandatory; censored samples are
`HORIZON_CENSORED` and excluded, never 0.

## GROSS_EDGE / COST / ADVERSE_SELECTION / NET_EDGE

```text
GROSS_EDGE(t,h)         = E[ d * (mid(t+h) - mid(t)) ]                       (CMP-03)
COST(t)                 = spread_cost + commission + impact + opportunity     (CMP-04)
                          impact = DATA_GAP on FXTM (must stay DATA_GAP, never 0)
ADVERSE_SELECTION(t,h)  = entry_exec - mid(t+h)  [LONG]                       (CMP-05)
                          DIAGNOSTIC_ONLY; may enter the decision only as a LAGGED, PIT estimate
NET_EDGE(t,h)           = GROSS_EDGE - COST - E[ADVERSE_SELECTION]
```
> This is a **candidate structure**, not a validated identity. If `E[ADVERSE_SELECTION]` cannot be
> estimated from information available at `t`, the term must be carried as `DATA_GAP` (= unknown), not 0.

## ENTRY / WAIT / EXIT

```text
ENTRY (TAKE) iff  NET_EDGE(t,h) - UNCERTAINTY_MARGIN > 0            (CMP-07)
WAIT         otherwise  -- WAIT is a VALID, SUCCESSFUL output; never forced to trade
EXIT         delegated to CMP-08 (see CAND-003)
```

## UNCERTAINTY (CMP-09)

```text
EXPECTED_EDGE, EDGE_UNCERTAINTY (bootstrap CI), EXECUTION_UNCERTAINTY (fill/cost band),
DATA_UNCERTAINTY (explicit DATA_GAP list), effective_N = n / max(1,rho)
```
No CI may be quoted from a raw event count when events cluster.

## DATA_REQUIREMENT

L1 only. Sufficient for the **gross** and **cost** terms; the `ADVERSE_SELECTION` term is
`PARTIAL` (L1 markout only) and the `opportunity` term needs the **fill/participation** model, which
is where FXTM is blind.

## PARAMETERS

```text
h, n (windows), k (momentum lookback), model class hyper-parameters,
UNCERTAINTY_MARGIN, cost tier, FDR family size   -> ALL TBD_IN_PRE_REGISTERED_EXPERIMENT
```
No threshold in this spec may be tuned on the current data.

## FAILURE_MODES

```text
F-01 COST_ERASED_ALPHA      edge < cost
F-03 LOOK_AHEAD             forward window leaking into state
F-04 POST_FILL_LEAKAGE      realised markout used as an input
F-05 SELECTION_BIAS         selecting on TEST / re-selecting after cost stress
F-06 OVERLAP_INFLATION      clustered events quoted as independent
F-07 TAIL_DEPENDENCE        mean driven by a few outcomes
F-08 OPPORTUNITY_OMITTED    unfilled size booked at par
```

## OOS_REQUIREMENT

Chronological split; purge+embargo = h; VAL-only selection; TEST evaluated once; BH-FDR;
block bootstrap; effective_N reported; cost stress 1.0/1.25/1.5/2.0 as robustness only.

## FXTM_COMPATIBILITY

`HIGH` — entirely L1. The only unavailable term is `impact` and a true `opportunity` term.

## EVIDENCE_LEVEL

Anchored on **E4** sources (`snowkings/QIP_adverse_selection`, `siddhantsingh-1/execution-aware-alpha-backtester`)
for the label/cost/gate mechanics. **The candidate itself is E0/UNTESTED** — no experiment has been run.
