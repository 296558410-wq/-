# Final Distillation Report — V3-HFT-GITHUB-MICROSTRUCTURE-DISTILLATION-003

`DISTILLATION ONLY` · `ALPHA_SEARCH = OFF` · `MODEL_TRAINING = OFF` · `FORWARD = NO` · `LIVE = NO` ·
`ORDER_SEND = 0` · no MT5 connection · no strategy copied.

**Evidence base:** 3 parallel read-only audits (`parts/group_A|B|C.md`), **18 repos carded** with 14-item
cards, **19+ slugs verified HTTP 200** via the GitHub API, plus explicit *negative* search results.
Nothing was reproduced (reproduction would need WRDS / S3 requester-pays / private grids / live collectors).

---

## FINAL STATUS (§三十九)

> ### `V3-HFT-CANDIDATE-MODEL = READY_FOR_V3_EXPERIMENT` (for the L1-compatible set)
> **16 mechanisms distilled: 14 READY, 2 PARKED. 3 candidate models are ready to be tested; 2 are parked.**
> Co-existing: `MICROSTRUCTURE_MODEL_DATA_BLOCKED` **for the passive/queue/market-making branch only**
> (MECH-010/011, CANDIDATE-004) — FXTM cannot observe fill probability, queue position or signed flow.
>
> **READY_FOR_V3_EXPERIMENT means "fit to be tested", NOT "profitable".** Nothing here has been tested,
> and nothing here authorises trading.

---

## Q1 — Which repos are genuinely worth absorbing?

| repo | why |
|---|---|
| `NadirAliOfficial/snipe-fx-ea` (E4) | the strongest artifact in the whole distillation — **and it is a negative result** |
| `siddhantsingh-1/execution-aware-alpha-backtester` (E4) | gross/net with attribution by cost type; reversion-ablation diagnostic |
| `snowkings/QIP_adverse_selection` (E4) | execution-state vs alpha distinction; favorable/unchanged/adverse three-way markout |
| `himagna16/kalshi-microstructure` (E4) | pre-registered OOS + "inefficient at the mid, efficient at the touch" |
| `gelatotrade/implementation-shortfall-hyperliquid` (E3) | Perold 4-term IS **including Opportunity on the unfilled fraction** |
| `AshJha0/electronic-trading` (E4 engineering) | cross-language golden values; explicit "what is NOT verified" block |
| `Trumplus/AAPL-...-Fill-Probability` (E3) | the honest fill-probability label + eligibility-censoring protocol |
| `tfrmma/realistic-mm-backtester` / `xiaohany-cmu-S26/lob-fill-engine` (E3) | the correct passive-fill formulation (queue_ahead + size-aware label) |
| `n30dyn4m1c/gold-pro-scalper` (E1) | the portable cost-multiple gate (mechanism only, no results) |
| `RobertN1D/...XAUUSD-GOLD-SCALPER...` (E1) | 500-tick adaptive lookback + p90 spread plumbing; and the author's own DOM disclaimer |

## Q2 — Which only look good but are not executable?

```text
diegourda/Statistical-Arb-MM        "30% adverse-selection reduction" from an engine-free, non-markout toy
Leotaby/Market-Making-Simulator     adverse selection is INJECTED post-fill; no real LOB/queue/feed
Sandyyy123/xauusd-scalper-research  bar-touch fills at exact SL/TP with ZERO spread on a 20-min gold scalp
RobertN1D/... (alpha, not plumbing) 11-generator ranker, never backtested, only flow input is a synthetic DOM
mahmoud20138/OrderFlow-Scalper      unvalidated pipeline on a synthetic DOM; ships defaulted to BTCUSD
aryansiwach/... realisation          valuable decomposition, but market-making revenue inverts under stress
```
None of these may be treated as evidence of edge.

## Q3 — Which mechanisms can be used directly on FXTM?

**14 of 16 are READY** (`github_distillation_registry.json`): MECH-001 cost-multiple gate · MECH-002
adaptive tick-window lookback · MECH-003 rolling p90 spread + spike gate + spread/target ratio ·
MECH-004 cost-type-failure flat-payoff test · MECH-005 Perold IS with Opportunity term ·
MECH-006 spread-vs-edge hurdle + mid-vs-touch · MECH-007 reversion-ablation maker/taker classifier ·
MECH-008 purge/embargo/uniqueness/eligibility protocol · MECH-009 markout with equity ·
MECH-012 sensitivity parameter published · MECH-013 detect whether the input is real ·
MECH-014 real-tick-only acceptance · MECH-015 init invariants/slippage abort/magic isolation ·
MECH-016 limit exit at the mean to avoid paying the spread twice.

Most are **methodology**, not alpha — which is exactly the correct yield of a distillation.

## Q4 — Which need L2 / are DATA_GAP on FXTM?

**PARKED (2):** MECH-010 FIFO `qty_in_front` + cancel model + size-aware fill label; MECH-011 intensity
calibration + overfit ratio. Both require a real book and real fills. Related: CANDIDATE-004 (passive
quoting) and CANDIDATE-005 (cross-venue context).

## Q5 — Does any repo genuinely reduce adverse selection?

**No.** Every claimed reduction is either (a) measured with a metric that is not markout
(`diegourda`: AS := |realized loss| on synthetic data), or (b) tautological (`Leotaby`: the adverse move
is injected). The only *measured* adverse-selection evidence in this batch is negative
(`snowkings`: 3.7% adverse moves, and still no capture; `siddhantsingh`: the edge is the maker's
reversion, not the taker's).

## Q6 — Which repos push execution cost into the loss / decision rule?

`siddhantsingh-1` (cost ladder charged in the backtest, **adverse selection measured not assumed**),
`himagna16` (fee charged in-code with a pre-computed break-even move), `gelatotrade` (Perold decomposition),
`AshJha0` (IS delay/trading/opportunity), `n30dyn4m1c` (cost-multiple entry gate),
`NadirAliOfficial/snipe-fx-ea` (spread gate + deviation cap + post-fill slippage abort).

## Q7 — Is fill probability usable on V3?

**Not today.** `Trumplus` (AUC ≈ 0.72) and `xiaohany-cmu-S26` show both the method and its ceiling, and
both rely on **queue position, which FXTM cannot observe**. Consequence: fills must be treated as a
**sensitivity band**, never a point estimate (MECH-012). MECH-010/011 and CANDIDATE-004 are PARKED.

## Q8 — Which OOS / statistical discipline is worth stealing?

MECH-008: chronological splits, **purge by label window**, embargo, sample-uniqueness weights,
**eligibility-censoring (unknowable outcomes excluded, never 0)**, per-day (not per-tick) uncertainty,
and pre-registration with a **hash-locked split boundary** (`himagna16`'s drift incident: a stale script
"reports a plausible number computed over in-sample and out-of-sample data pooled together").

## Q9 — Which failure cases are most valuable?

In order: **NEG-105 cost-type failure** (flat ≈ −0.31/trade across 36 real-tick passes) ·
**NEG-101/103/102 COST_ERASED_ALPHA / EXECUTION_FAILURE** (9.11 bp vs 10.3 bp; 10.7¢ break-even;
+0.29 tick vs 1.08 tick) · **NEG-106 synthetic-tick overstatement** (PF 1.97 → 0.34) ·
**NEG-107/108 claim inflation & tautological AS** · **NEG-104 queue-assumption risk** ·
**NEG-111 provenance failures**.

## Q10 — Can 3–5 candidate V3 HFT models be formed?

Yes — `candidate_model_spec.md`: **CANDIDATE-001** Execution-Aware L1 Markout Gate,
**002** Spread-Regime Execution Policy, **003** Adverse-Selection-Conditional Exit,
**004** Passive/Queue-Aware MM (parked), **005** Cross-Venue Context (parked).

## Q11 — Which candidate mechanisms are READY?

**001, 002, 003** — all pass Gate 1 (mechanism) and Gate 2 (FXTM data is L1-observable), with
**Gate 3 (cost survival) UNTESTED**. They are ready *to be tested*, not validated.

## Q12 — Which must NOT be tested now?

```text
CANDIDATE-004  passive / queue-aware market making   -> needs real L2 queue, signed flow, fill model
CANDIDATE-005  cross-venue context                   -> other venue != FXTM pool
MECH-010 / MECH-011                                  -> fill label & intensity calibration need real fills
anything requiring: real L2 depth, queue position, signed trade flow, fill probability,
                     historical DOM, venue-level cancellation data
```
Testing these now would produce an untestable assumption dressed as evidence.

---

## The cross-cutting lesson (§三十)

> **The gross/net gap is the normal case, not the anomaly.** Four independent repos
> (`siddhantsingh`, `snowkings`, `himagna16`, `aryansiwach`) show a *statistically real and economically
> dead* signal. Combined with V3's own measurements (gross ≈ +0.096 bp vs 0.914 bp cost; cost/median-move
> > 1 for h ≤ 2 s), the picture is consistent: **at tick horizons the spread is the alpha of whoever
> quotes, not whoever takes.**

## What this task does NOT establish

```text
no net-of-cost, out-of-sample edge was found or claimed in any repo or here
no candidate has been trained, tested or traded
no FXTM data capability has changed (true OFI/microprice/queue/fill remain DATA_GAP)
no forward / demo / live / expansion is authorised
```
