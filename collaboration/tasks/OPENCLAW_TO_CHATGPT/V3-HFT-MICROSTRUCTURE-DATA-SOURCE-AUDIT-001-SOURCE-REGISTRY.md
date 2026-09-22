# Microstructure Source Registry

Task: **V3-HFT-MICROSTRUCTURE-DATA-SOURCE-AUDIT-001** — `AUDIT_ONLY`, read-only.
Machine-readable twin: `source_registry.json`. Evidence: `evidence/`, `parts/part_B.md`, `parts/part_C.md`.

## Classification legend

```text
DIRECTLY_RELEVANT | PARTIALLY_RELEVANT | AUXILIARY_ONLY | NOT_USABLE
```

## Registry

| SOURCE_ID | provider | instrument / venue | data type | bid/ask size | depth | trade flow | historical | FXTM exec link | CLASSIFICATION |
|---|---|---|---|---|---|---|---|---|---|
| **S1** | FXTM (account 160764551, magic 90004) | XAUUSD / FXTM | L1 + tick | no (0) | — | none (all 0) | ticks yes | **DIRECT** | **DIRECTLY_RELEVANT** |
| **S1-DOM** | FXTM | XAUUSD / FXTM | DOM | **synthetic ladder** | 10 lvl realtime | — | **none** | **DIRECT** | **PARTIALLY_RELEVANT** |
| **S2** | FXTM first-party / institutional / FIX | XAUUSD / FXTM | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | would be direct | **NOT_USABLE (UNKNOWN)** |
| **S3** | CME GC/MGC (Databento, CME DataMine) | gold futures / CME Globex | L2, MBO, tape, queue | yes | full book | yes | yes | no (other venue) | **AUXILIARY_ONLY** |
| **S4** | LBMA (via Nasdaq) | Loco London gold / OTC | aggregates | no | no | aggregate | T+1 | no | **AUXILIARY_ONLY** (per-trade L2 `NOT_FOUND`) |
| **S5** | 16 commercial vendors | FX/metals/futures / various | L1–MBO | vendor-dep. | 1/3/10/full | some | some | no | **AUXILIARY_ONLY / NOT_USABLE** |
| **S6** | literature (Hauptfleisch 2016) | gold, London vs NY | publication | — | — | — | — | context only | **PARTIALLY_RELEVANT** |

### S5 detail (the vendor layer)

| vendor | what it really gives | vs FXTM |
|---|---|---|
| LMAX | L1, L2 (≤10 FIX), L3, ITCH full depth, **trade side**, µs, 10+ yr / 800 TB | LMAX's own CLOS — **AUXILIARY_ONLY** |
| TrueFX (Integral OCX) | L1; Institutional **3-level depth**; $4,950 / $7,450 per month | not FXTM — **AUXILIARY_ONLY** |
| Oanda | per-account `bids/asks` PriceBucket depth; no aggressor tape | Oanda pool — **AUXILIARY_ONLY** |
| dxFeed | Quote (bid/ask sizes) + Order events + on-demand tick replay; no verified XAUUSD product | **AUXILIARY_ONLY / NOT_USABLE** |
| Databento | MBO/MBP, explicit raw-event replay; exchange futures | **AUXILIARY_ONLY** |
| CQG | best bid/ask + time&sales only | **AUXILIARY_ONLY** |
| Dukascopy / HistData | L1 tick + tape, **zero depth**, no venue attribution | **AUXILIARY_ONLY** |
| Refinitiv/LSEG, Bloomberg, ICE, Integral, FXCM, Tickstory | no field list obtainable (404/403) | **NOT_USABLE (UNKNOWN)** |
| cTrader Open API | broker-side DOM exists but FXTM is not cTrader | **NOT_USABLE for FXTM** |

## Headline

```text
DIRECTLY_RELEVANT sources found            = 1   (FXTM's own feed)
THIRD-PARTY DIRECTLY_RELEVANT sources      = 0
Genuine order-by-order L2 attached to FXTM = NONE
FXTM trade tape / aggressor flow           = NONE (all zero)
```

**A different venue's L2 is not FXTM's L2** — different queue, different fill probability,
different adverse selection. Vendor L2 is at best a structural proxy for execution-model
calibration, never "FXTM's queue".

## Method / limitations

* `web_search` was **disabled** for this run; external findings come from direct `web_fetch` of
  official URLs (parts B and C), so coverage is limited to known-official pages.
* The `src-a` subagent (FXTM/MT5 web documentation) **returned** and is filed as `parts/part_A.md`.
  Its verdict aligns with the measurement: FXTM's public URL index contains **no** market-depth /
  Level-2 / tick-data / API / FIX page (`NOT_FOUND`), and MT5 documents that for OTC symbols the DOM
  is broker-quoted and degenerates to Bid/Ask ± price-step when no volumes are supplied. Source 1 is
  therefore evidenced by **direct measurement** *and* documentation; Source 2 stays `UNKNOWN`.
* Pages behind Cloudflare/bot-walls were recorded `NOT_USABLE (UNKNOWN)` — never asserted.
