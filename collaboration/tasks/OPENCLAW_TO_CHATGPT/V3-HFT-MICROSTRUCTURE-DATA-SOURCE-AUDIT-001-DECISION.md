# Microstructure Source Decision

Task: **V3-HFT-MICROSTRUCTURE-DATA-SOURCE-AUDIT-001** — `AUDIT_ONLY`, read-only.
Decision tree of task §二十 applied below. **No alpha search was performed and none is proposed.**

## FINAL STATUS

> ### `PARTIAL_MICROSTRUCTURE_AVAILABLE`
> A **real, FXTM-relevant realtime Market Depth feed exists** (10 levels, measured on the V3
> execution instance), **but it is insufficient** to build FXTM executable microstructure alpha:
> its sizes are a constant synthetic ladder, it has no history, and the trade tape is empty.

All four target research quantities nevertheless remain:

```text
TRUE_OFI          = DATA_GAP
MICROPRICE        = DATA_GAP
QUEUE             = DATA_GAP
FILL_PROBABILITY  = DATA_GAP
```

*(A stricter reading — "synthetic sizes are not true L2" — would return `MICROSTRUCTURE_DATA_GAP`.
Either label leads to the same action; `PARTIAL_*` is chosen because a directly-relevant realtime
depth feed demonstrably exists and its limitations are now measured rather than assumed.)*

## Decision tree traversal (§二十)

```text
存在真实 Microstructure 数据?
  ├─ FXTM: L1 YES; realtime DOM YES(10 lvl); order-by-order L2 NO; trade tape NO
  └─ third parties: no source is FXTM's pool  ->  DIRECTLY_RELEVANT = 0
与 FXTM Execution 直接相关?
  ├─ S1 (FXTM feed itself)        -> YES
  ├─ S1-DOM (realtime depth)      -> YES relevance, but synthetic sizes + no history
  └─ S3/S4/S5 (CME/LBMA/vendors)  -> NO  -> AUXILIARY_ONLY
结论 -> 不进行 Alpha Search -> WAIT FOR CHATGPT
```

## Answers to the ten audit questions (§四)

**Q1 — Does FXTM/MT5 itself carry book-quantity data?**
Partly, and exactly as measured (not as documented): bid/ask/spread/mid = AVAILABLE;
`last`, `volume`, `volume_real` = **0 on all 3,733 ticks** observed; `session_deals`,
`session_buy_orders`, `session_sell_orders`, `session_volume` = **0**; **Market Depth = 10 levels,
realtime**, but with a **constant mirrored size ladder** (60/60 snapshots identical, symmetric sums
= 1.0). "API theoretically supports" and "FXTM actually receives" were checked separately.

**Q2 — What does FXTM officially provide?** Public documentation says **NOT_FOUND**: FXTM's own
URL index (`https://www.fxtm.com/sitemap.xml`, full `<urlset>`) contains **no** market-depth /
Level-2 / order-book / tick-data / API / FIX page. Whether an unadvertised institutional feed exists
behind an onboarding gate is `UNKNOWN` (not guessed). MT5 documents that for OTC symbols the DOM is
broker-quoted and degenerates to Bid/Ask ± price-step when the broker supplies no volumes — which is
precisely the synthetic ladder measured in Q1, i.e. *documentation corroborates the measurement*.

**Q3 — CME/COMEX?** Genuine L2/MBO + tape + queue exist (nanosecond, historical, replayable) but
they are **US futures**, a different venue and instrument → `AUXILIARY_ONLY`. `CME GC ≠ FXTM XAUUSD`.

**Q4 — LBMA / London OTC?** Only **aggregate** T+1 statistics; **no public per-trade bid/ask size,
depth or direction** → `AUXILIARY_ONLY`; per-trade L2 `NOT_FOUND` → `NOT_USABLE`.

**Q5 — Other public/commercial sources?** 16 audited. Best genuine FX/metals L2 = **LMAX**
(L1/L2≤10/L3/ITCH, trade side, µs, 10+ yr). **TrueFX/Integral OCX** sells a 3-level institutional
book. **Oanda** publishes per-account bid/ask buckets. **Dukascopy/HistData** are L1 tick only.
All `AUXILIARY_ONLY`; several unverifiable ones `NOT_USABLE (UNKNOWN)`.

**Q6 — True vs fake L2?** Applied strictly — `has bid/ask ⇒ has L2` and
`has volume ⇒ has order flow` were both **rejected**. Layered separately: L1 `SUPPORTED`;
L2 `PARTIAL` (realtime-only, synthetic sizes); trade flow `DATA_GAP`; queue `DATA_GAP`.

**Q7 — Execution relevance?** Only FXTM's own feed passes all seven tests
(see `execution_relevance_matrix.md`). **Third-party DIRECTLY_RELEVANT sources = 0.**

**Q8 — Timestamp alignment experiment?** **Not applicable / `DATA_GAP`.** No candidate claims to be
FXTM's execution pool, and FXTM's own DOM has no history to align against. Policy recorded in
`timestamp_alignment_policy.md` (declared unit, no future info, no best-lag mining).

**Q9 — Did any alpha mining occur?** **No.** `ALPHA_SEARCH/MODEL_SEARCH/FEATURE_MINING = OFF`;
no sweep of features, models, thresholds, horizons or parameters.

**Q10 — Does this change the cost verdict?** **No.** `50ms/200ms/1s/2s = COST_BLOCKED`
stands untouched. Finding L2 would not license 1-second HFT; every future claim must still pass
the full chain (gross → spread → commission → slippage → latency → adverse selection →
net executable edge) plus OOS, bootstrap, multiple-testing and cost stress.

## What would actually be needed next (evidence, not a request)

```text
1. FXTM first-party depth/tick-feed product (FIX or broker-supplied), OR
2. a written confirmation of FXTM's liquidity-provider pool + that pool's L2,
3. historical retention of the realtime DOM (currently nothing is stored), and
4. a genuine (non-synthetic) size ladder — otherwise microprice collapses to mid.
```

Until then the honest position is: **L1 research restricted to h ≥ 5 s, and no Level-B
microstructure claim on this feed.**

## Status vocabulary (§二十五)

```text
DIRECT_MICROSTRUCTURE_AVAILABLE   = NO
PARTIAL_MICROSTRUCTURE_AVAILABLE  = SELECTED
AUXILIARY_ONLY                    = the class of everything external
MICROSTRUCTURE_DATA_GAP           = the state of TRUE_OFI / MICROPRICE / QUEUE / FILL_PROBABILITY
ALPHA_FOUND / STRATEGY_READY / FORWARD_READY / LIVE_READY = NOT ASSERTED
```
