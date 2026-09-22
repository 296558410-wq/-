# Execution Relevance Matrix

Task: **V3-HFT-MICROSTRUCTURE-DATA-SOURCE-AUDIT-001** (task §十三).
Question: *is this book the book V3 actually faces?*

## The seven tests (all must be YES for DIRECTLY_RELEVANT)

```text
1 same instrument?        2 same market?      3 same venue?
4 same liquidity pool?    5 same price formation?
6 same execution venue?   7 alignable to FXTM tick / execution price?
```

A high gold-price correlation, or "XAUUSD ≈ GC", is **not** an execution link.

## Matrix

| SOURCE_ID | source | same instrument | same market | same venue | same liquidity pool | same price formation | same execution venue | alignable to FXTM tick | CLASSIFICATION |
|---|---|---|---|---|---|---|---|---|---|
| **S1** | FXTM XAUUSD via MT5 (account 160764551, magic 90004) | YES | YES | YES | YES | YES | YES | YES (same clock/terminal) | **DIRECTLY_RELEVANT** … but see below |
| **S1-DOM** | FXTM 10-level Market Depth (realtime) | YES | YES | YES | YES | YES | YES | YES | **PARTIALLY_RELEVANT** (synthetic sizes, no history) |
| **S1-TAPE** | FXTM trade prints / volumes | — | — | — | — | — | — | — | **DATA_GAP / NOT_USABLE** (all zeros) |
| **S2** | FXTM first-party historical / institutional feed | UNKNOWN | UNKNOWN | YES | UNKNOWN | UNKNOWN | YES | UNKNOWN | **UNKNOWN → NOT_USABLE** (no public field list) |
| **S3** | CME GC / MGC (MBO, level-2, tape) | NO (futures) | NO (US futures) | NO | NO | linked, not same | NO | correlation only | **AUXILIARY_ONLY** |
| **S4** | LBMA / London OTC statistics | NO (aggregate) | NO | NO | NO | linked, not same | NO | not possible (T+1 aggregate) | **AUXILIARY_ONLY**; per-trade L2 **NOT_FOUND** |
| **S5a** | LMAX Exchange spot FX/metals CLOB | NO (MTF) | NO | NO | NO | linked, not same | NO | correlation only | **AUXILIARY_ONLY** |
| **S5b** | TrueFX (Integral OCX, 3-level institutional) | NO | NO | NO | NO | linked, not same | NO | correlation only | **AUXILIARY_ONLY** |
| **S5c** | Oanda per-account bid/ask buckets | NO (Oanda pool) | NO | NO | NO | linked, not same | NO | correlation only | **AUXILIARY_ONLY** |
| **S5d** | dxFeed (Quote sizes + Order events + on-demand tick) | UNKNOWN | UNKNOWN | NO | NO | linked | NO | correlation only | **AUXILIARY_ONLY / NOT_USABLE** |
| **S5e** | Databento (MBO/MBP, explicit replay) | NO (futures) | NO | NO | NO | linked, not same | NO | correlation only | **AUXILIARY_ONLY** |
| **S5f** | Dukascopy / HistData (L1 tick + tape, no depth) | NO | NO | NO | NO | linked | NO | correlation only | **AUXILIARY_ONLY** (zero depth) |
| **S5g** | CQG (best bid/ask + T&S) | UNKNOWN | UNKNOWN | NO | NO | linked | NO | correlation only | **AUXILIARY_ONLY** |
| **S5h** | cTrader Open API (broker-side DOM) | NO (wrong platform) | NO | NO | NO | NO | NO | no | **NOT_USABLE for FXTM** |
| **S5i** | Refinitiv/LSEG, Bloomberg, ICE, Integral, FXCM, Tickstory | UNKNOWN | UNKNOWN | NO | NO | UNKNOWN | NO | no | **NOT_USABLE (unverifiable)** |
| **S6** | published CME-leads-spot literature (Hauptfleisch et al. 2016) | — | — | — | — | YES (context) | — | n/a | **PARTIALLY_RELEVANT (context)** |

## Reading

* The **only** source that passes all seven tests is FXTM's own feed — which is exactly where the
  sizes are a **constant synthetic ladder** and where no historical depth exists.
* **No third-party source is DIRECTLY_RELEVANT.** Different venue ⇒ different queue ⇒ different
  fill probability ⇒ different adverse selection. Vendor L2 can only serve as a *structural proxy*
  for execution-model calibration, never as "FXTM's queue".
* The single `DIRECTLY_RELEVANT` row (S1) carries no usable microstructure payload
  (see `fxmt_l2_capability.md`), so its *effective* research value is `PARTIAL`.

## Guardrails honoured

* `CME GC ≠ FXTM XAUUSD` — no source equates them.
* `has bid/ask ⇒ has L2` — rejected (S1 has bid/ask, yet no genuine L2 sizes).
* `has volume ⇒ has order flow` — rejected (volume ≡ 0 on the FXTM feed).
* `futures L2 ⇒ can research FXTM L2` — rejected.
