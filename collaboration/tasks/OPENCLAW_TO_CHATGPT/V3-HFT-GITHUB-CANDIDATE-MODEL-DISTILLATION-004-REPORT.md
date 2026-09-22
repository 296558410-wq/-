# Final Model Distillation Report — V3-HFT-GITHUB-CANDIDATE-MODEL-DISTILLATION-004

`DISTILLATION_ONLY / READ_ONLY`. No training, no backtest, no MT5, no orders.
All candidates are `UNTESTED`. Every parameter is `TBD_IN_PRE_REGISTERED_EXPERIMENT`.

---

## Q1 — What is CAND-001's real mechanism?

A **gated economic comparison**, not a predictor. It computes an expected gross markout for a horizon,
subtracts the **full** execution cost (spread + commission + `impact` + `opportunity`), optionally
subtracts an expected adverse-selection term, and **only trades when the remainder survives an
uncertainty margin** — otherwise it returns `WAIT`. Mechanism anchors: `siddhantsingh-1` (E4) charges a
cost ladder inside the backtest with **adverse selection measured, not assumed**; `snowkings` (E4)
separates the *signal* from the *cost of acting on it*; `himagna16` (E4) computes a break-even move
before testing. The gate is the mechanism; the directional signal is an input it may reject.

## Q2 — What is CAND-002's real mechanism?

A **cost-regime policy**, answering "can any action be economic right now?" from spread/volatility
state. The distilled answer to §八.4 — *is spread a predictor or a cost?* — is that in every examined
repo (except for the untested cost-multiple gate) **spread is a COST variable and a regime indicator,
not a directional predictor**. `himagna16` states the operative law: *"inefficient at the mid,
efficient at the touch."* Hence CAND-002 deliberately emits `TRADEABLE / NOT_TRADEABLE / UNKNOWN` and
never a direction. It is the only candidate whose mechanism is a **filter**.

## Q3 — What is CAND-003's real mechanism?

An **edge monitor**. Instead of fixed SL/TP, it tracks the **expected remaining edge** and exits when
that falls below the **expected exit cost** (which includes the *second* spread crossing). It also
enforces a four-way separation of outcomes — `ENTRY_WRONG`, `EDGE_DECAY`, `ADVERSE_SELECTION`,
`COST_EROSION` — none of which may be collapsed into "LOSS". Mechanism anchors: `snowkings` (E4)
remaining-hold accounting (`remaining = horizon − delay`, nonpositive ⇒ unavailable), `AshJha0` (E4)
opportunity-cost accounting, `KlishevDA`/`snowkings` markout curves, `Trumplus` (E3) survival/hazard
formulation. The **functional form of the decay is NOT settled** — this is CAND-003's weakest link.

## Q4 — What data does each need?

| candidate | required data | status on FXTM |
|---|---|---|
| CAND-001 | L1 quotes; cost components; (participation/fill for `opportunity`) | L1 AVAILABLE; `impact` & `opportunity` DATA_GAP |
| CAND-002 | L1 quotes + history | **fully AVAILABLE** |
| CAND-003 | L1 quotes + position + second-crossing cost; (depth/queue for class C) | L1 AVAILABLE; class C PARTIAL |

## Q5 — Which can run entirely on FXTM L1?

**CAND-002** (fully). **CAND-001** almost entirely (the `impact`/`opportunity` terms must be carried as
`DATA_GAP`, never 0). **CAND-003** for the timing rule.

## Q6 — Which must depend on L2?

**None of the three are L2-dependent by construction.** The L2 requirement lands on the **PARKED**
`CAND-004` (passive/queue market making) and on the *class-C toxicity attribution* inside CAND-003
(true adverse selection needs depth/queue/signed flow).

## Q7 — Which needs real fill data?

**CAND-004 (PARKED)** for `P(fill)`. For the READY set, only the **`opportunity` term** (CMP-04) needs
real fill/participation data — which is why `gelatotrade`'s Opportunity term is the single most
valuable *accounting* import and simultaneously the term FXTM cannot yet fill.

## Q8 — Which can model cost directly?

**CAND-002** — cost *is* its object. **CAND-001** — cost is an explicit term in the gate.
Both use the canonical decomposition (`CMP-04`): additive, sign-declared, no silent netting.

## Q9 — Which can model adverse selection?

**CAND-003** models it as a measured class (CMP-05); **CAND-001** carries it as an expected term, but
only if it can be estimated from information available at `t` — otherwise it stays `DATA_GAP`.
Rule enforced: realised markout is `DIAGNOSTIC_ONLY` and may never enter the entry decision.

## Q10 — Which can handle edge decay?

Only **CAND-003**. The task-004 search settled the open question as far as public code allows:

```text
NO repo derives E(t) from microstructural primitives.
The only REUSABLE functional form found is a FIT, implemented identically in two repos:
    r33bt/signal-decay-calculator   (E1): IC(h) = IC0 * exp(-lambda*h) ; half-life = ln2/lambda ; lambda by log-linear OLS
    quantskills/skill-factor-ic-decay (E2): IC(h) = A * exp(-h/tau) ; t_half = tau*ln2 ; Newey-West t, ICIR, rolling stability
The empirically-anchored alternative: markout / IC curves over horizons with NO fitted law
    (KlishevDA, punyamodi, atiselsts, tfrmma).
The only STRUCTURAL time-dependent exit found: zj092912 (E3, REAL data) - a finite-horizon
    optimal-stopping free boundary that tightens as time-to-close shrinks.
```

Two warnings carried straight into the spec: `quantskills` states the half-life is a *fitted shape
parameter, not a promise the signal works for N more days*; and `nirholas/markout-fee` deliberately
imposes a fixed `minHorizon` delay before grading a fill, **to avoid measuring the trade's own impact**
— the same trap CAND-003 must avoid when it measures the decay of its own edge.

`EDGE_LIFETIME` remains `MODEL_CONCEPT`; the exponential form is a **candidate**, not a law.
**No repo implements the 4-way taxonomy** (`ENTRY_WRONG` / `EDGE_DECAY` / `ADVERSE_SELECTION` /
`COST_EROSION`) — CAND-003 must supply it itself, and that is a genuine open gap in public code.

## Q11 — Which is most prone to look-ahead?

**CAND-003.** A multi-instant decision with a *fitted* decay curve is the classic look-ahead device: if
the curve is estimated on the same trades it times, the exit rule "knows" the future. Mitigation:
freeze the decay form before opening the OOS window; keep class attribution post-trade.
Second: **CAND-002**, because `cost / realised move` is *definitionally* post-hoc — the decision must
use `cost / expected move` from history only.

Third, and newly evidenced: **self-impact contamination**. `nirholas/markout-fee` imposes a
`minHorizon` delay before grading precisely because measuring a fill's markout from the same event
double-counts the trade's own impact. CAND-001/003 must apply the same discipline when they use
realised markout as a diagnostic.

## NEW EVIDENCE from the two task-004 gap-searches (appended after the initial report)

```text
1 SPREAD IS COST, NOT A PREDICTOR. 18 verified repos, ZERO show a stable spread-state -> expected
  future-move relationship. Spread appears as a hard gate (chinthakat: MAX_SPREAD_POINTS=50), a P&L
  hurdle (loblab, AMIRMAHMOUDINIA), a decomposition term (aryansiwach, DaniyalMlk), or a quote-width
  OUTPUT driven by volatility (SpencerOzgur: spread = gamma_rv*sigma2_t*(T-t)+B). Gap (A) stays open.

2 INDEPENDENT CONFIRMATION OF V3'S CENTRAL FINDING.
  K1ta141k/loblab (E3): "the move only clears the ~1-tick spread at extreme thresholds where the
     sample is tiny ... that crux (signal < spread) is the whole game in taker alpha".
  AMIRMAHMOUDINIA (E5): "every cost scenario failed the economic gate; even at 0 additional bps the
     selected strategy averaged -0.343 bps/trade; gross break-even additional cost only 0.909 bps".
  0.909 bps vs V3's own 0.914 bp measured round-trip cost - an independent venue reaching the same wall.

3 EXIT-COST ANNIHILATION, MEASURED ON REAL DATA. zj092912/wti-airline-stat-arb (E3): the SAME strategy
  shows mark-to-mid Sharpe 1.08 / +$463,326 and realised -$24,931,458 over 10,907 trades.
  "The entire edge - and then some - is inside the bid-ask spread." This is the strongest single piece
  of evidence for CAND-003's exit-cost term and for counting the SECOND spread crossing.

4 THEORETICAL vs EXECUTABLE MAKER EXIT. SpencerOzgur (E3) is the only repo that runs queue_model='front'
  and 'back' AND reports them separately; aryansiwach (E4) implements the executable version
  (simulate_limit: queue_ahead, cancel_on_through, deadline_ns, residual sweep). This is how maker-exit
  uncertainty must be published - as a PAIR, never one number. (CAND-004 stays PARKED.)

5 OPPORTUNITY COST IS RARE. Only 2 of 18 repos charge unfilled quantity: aryansiwach (unfilled marked to
  final mid, weighted by fill ratio) and DaniyalMlk/slippage (E5, Perold opportunity, with the
  order-basis vs executed-basis convention stated and tested). Retail backtests silently use zero.
  CMP-04 is upgraded to E5 on this basis.

6 NEGATIVE REGISTER. 11 queries returned ZERO repositories (passive execution simulator; opportunity
  cost unfilled order; spread predictor future returns; ... ) and 7 returned noise only. Recorded in
  github_search_registry.json so the search is not repeated.
```

### Component upgrades caused by these searches

```text
CMP-04 cost        -> E5  (DaniyalMlk Perold order-vs-executed basis; aryansiwach opportunity-on-unfilled)
CMP-06 execution   -> front/back queue PAIR mandated (SpencerOzgur + aryansiwach); second crossing explicit
CMP-08 exit        -> decay form anchored: E(t)=E0*exp(-lambda t), t_half=ln2/lambda (r33bt/quantskills),
                      with zj092912's exit-cost annihilation as the binding constraint
CMP-09 uncertainty -> E5  (AMIRMAHMOUDINIA pre-registered gates, locked test, HAC, BH-FDR, block bootstrap)
```

## Q12 — Which is most prone to selection bias?

**CAND-001** — it has the largest parameter surface (`h`, windows, `k`, model class, uncertainty
margin, FDR family), and it is a *directional* candidate, which is where multiple-testing bias bites
hardest. **CAND-002**'s exposure is concentrated and therefore more controllable (the regime
boundaries must be fixed before the OOS window).

## Q13 — Which is most easily killed by transaction cost?

**CAND-001.** At short horizons the measured cost (0.914 bp) already exceeds the typical move
(cost/median-move > 1 for h ≤ 2 s), and the only positive results on this horizon family have been
shown to be tail-dependent. The cost kill is the *expected* outcome for a directional taker — which is
precisely what the gate is designed to detect rather than deny.

## Q14 — Which is most worth pre-registering next?

**CAND-001 (`PRIMARY_CANDIDATE`)** — it is the only one that tests the *central* economic inequality
(`expected net edge > 0` after the full cost chain) with the fewest free assumptions about market
behaviour, and it structurally hosts the other two (002 supplies the cost/regime term, 003 the exit).
If the group prefers the **lowest-assumption first step**, `CAND-002` is the alternative: it needs L1
only, has the smallest parameter surface, and its "success" can be a clean `NOT_TRADEABLE` regime map.

**This choice is a research decision, not a result, and belongs to ChatGPT/the group.**

---

## What this task does NOT establish

```text
no candidate has been trained, backtested or traded
no threshold, horizon or feature has been chosen
no claim that any candidate would be profitable
no FXTM data capability has changed (OFI/queue/flow/fill/L2 remain DATA_GAP)
no authorisation for forward / demo / live / expansion
```

## The chain actually walked (§四十一)

```text
GitHub Evidence (E3/E4 sources; 18 cards)
    -> Mechanism (16 distilled; 14 READY / 2 PARKED)
    -> Model Component (10 components, CMP-01..CMP-10)
    -> Mathematical Specification (CAND-001/002/003, all fields filled)
    -> FXTM Data Compatibility (L1 AVAILABLE; impact/opportunity/queue/fill = DATA_GAP)
    -> Execution Compatibility (taker OK; passive PARKED)
    -> Candidate Model  ->  READY_FOR_PRE_REGISTRATION
```

`CANDIDATE_MODEL = UNTESTED` — **not** a trading model.
