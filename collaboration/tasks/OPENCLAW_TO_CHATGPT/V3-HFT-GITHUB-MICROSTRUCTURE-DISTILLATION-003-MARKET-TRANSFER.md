# Market-Structure Transfer Analysis — XAUUSD special review (§十四 / §三十四)

Purpose: decide whether a mechanism observed on another venue can even *in principle* apply to
**FXTM XAUUSD (retail spot-gold CFD)**. This is a structural test, not a performance comparison.

## FXTM XAUUSD (the reference environment)

```text
VENUE              retail CFD/OTC broker (FXTM), server ForexTimeFXTM-Demo01
ACCOUNT/ENV        login 160764551, magic 90004 (V3 calibration instance)
INSTRUMENT         XAUUSD spot-gold CFD (NOT COMEX GC futures, NOT loco-London spot)
BID/ASK            yes (spread ~0.15-0.18 USD ~= 0.34-0.41 bp)
CONTRACT SIZE      100 (0.01 lot = 1 oz), tick size 0.01, tick value 0.10 USD per 0.01 lot
COMMISSION         ~0.22 USD / RT measured ; SPREAD ~0.18 USD / RT
SWAP               present (rerollover 3 days) - matters only for multi-day holds
REAL TICK          yes (datetime64[ms, UTC] quote ticks; volume/last identically 0)
TRADE TAPE         none (no executed-deal prints)
DOM                10 levels REALTIME, but DEPTH_PROFILE = SYNTHETIC_OR_AGGREGATED
                   (constant mirrored ladder 100/400/500/4000/10000 in 60/60 snapshots)
L2 / QUEUE / OFI   DATA_GAP ; HISTORICAL DOM DATA_GAP (realtime only)
EXECUTION          market/pending orders against the broker's quote stream, ~273-279 ms RTT
```

## Comparison

| dimension | FXTM XAUUSD | CME GC futures | LMAX spot FX/metals | Crypto CLOB (BTC) | LOBSTER / NASDAQ |
|---|---|---|---|---|---|
| instrument | spot-gold CFD | future | spot FX/metals | crypto spot | equities |
| matching | broker-side OTC | CME Globex CLOB | exchange CLOB | exchange CLOB | exchange CLOB |
| real L2 depth | **no (synthetic DOM)** | yes (MBO) | yes (L2/L3/ITCH) | yes | yes |
| queue position | **no** | yes | yes (price/time) | yes | yes |
| trade tape / aggressor | **no** | yes | yes (side) | yes | yes |
| OFI computable | **no (proxy only)** | yes | yes | yes | yes |
| fill probability modelable | **no** | yes | yes | yes | yes |
| venue equal for alpha? | — | **no** | **no** | **no** | **no** |

## Verdicts

```text
CME GC / MGC           = OTHER_VENUE (futures) -> D AUXILIARY_ONLY (price-discovery proxy at best)
LBMA / loco London     = OTHER_VENUE (OTC aggregate) -> D AUXILIARY_ONLY
LMAX / EBS / FX venues = OTHER_VENUE (their own pools) -> D AUXILIARY_ONLY
Crypto LOB             = OTHER_VENUE (24/7, different microstructure) -> D / E
NASDAQ / LOBSTER       = OTHER_VENUE (auction + equities) -> E NOT_TRANSFERABLE
```

**Hard rule (§三十三):** *a different venue's L2 alpha is not FXTM XAUUSD alpha.* A mechanism whose
core input is real L2 depth, queue position, signed trade flow, or a fill-probability estimate is
`C DATA-DEPENDENT` at best, and must be parked until FXTM supplies equivalent data.

**What CAN cross the boundary:** mechanisms whose inputs are L1-only (bid/ask/mid/spread/quote
change/tick direction/velocity/acceleration/short return/reversal/spread regime/volatility/quote
arrival/markout) and whose *logic* is venue-independent (execution-cost awareness, adverse-selection
accounting, cost-aware labelling, decision policies of the form TAKE/PASSIVE/WAIT/EXIT).

## Gold-specific pitfalls (§三十四)

```text
GC futures   != XAUUSD CFD         (different matching, margin, tape, hours)
loco London  != FXTM XAUUSD
"gold price correlation" != same execution venue
24/5 FX hours + swap != 24/7 crypto
retail synthetic DOM != real depth
```
