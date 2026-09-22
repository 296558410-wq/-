# FXTM L2 / Market-Depth capability — MEASURED

Task: **V3-HFT-MICROSTRUCTURE-DATA-SOURCE-AUDIT-001**. Read-only. No orders (`order_send_called: false`).

## Probe environment (measured 2026-09-22T03:02–03:04Z)

```text
terminal      = C:\AIQuant\mt5_instances\fxtm_demo_v3calib\terminal64.exe
company/name  = FXTM / "ForexTime (FXTM) MT5"   build 6182   connected = TRUE
account       = 160764551  server ForexTimeFXTM-Demo01  USD
symbol        = XAUUSD   digits=2  point=0.01  spread=18pt (0.18 USD)  spread_float=TRUE
```

Evidence files: `evidence/mt5_probe_result.json`, `evidence/mt5_bookdepth_probe.json`,
`evidence/mt5_dom_wait_result.json`, `evidence/mt5_dom_rich_result.json`,
`evidence/mt5_dom_authenticity_result.json`.

## Q1 answer — does FXTM/MT5 actually deliver book quantities?

The task demands separating **"API theoretically supports"** from **"V3 FXTM actually receives"**.

| item | API supports | FXTM actually receives (measured) | verdict |
|---|---|---|---|
| bid / ask | yes | yes (live) | AVAILABLE |
| spread / mid | yes | yes | AVAILABLE |
| tick `last` | yes | **0.0 on every tick** | DATA_GAP |
| tick `volume` | yes | **0 on every tick** (3,733/3,733) | DATA_GAP |
| tick `volume_real` | yes | **0.0 on every tick** | DATA_GAP |
| session trade tape (`session_deals`, `session_buy_orders`, `session_sell_orders`, `session_volume`) | yes | **all 0** | DATA_GAP |
| Market Depth / DOM (`market_book_add/get`) | yes | **YES — 10 levels** (see below) | AVAILABLE (realtime) |
| historical Market Depth | **no MT5 API** | n/a | DATA_GAP |
| `ticks_bookdepth` (declared max depth) | field present | **10** | declared, not proof |
| queue position / order-ahead | no | no | DATA_GAP |
| fill probability | no | no | DATA_GAP |

### The DOM finding, and its authenticity test

1. Immediate `market_book_get` after `market_book_add` returned **0 levels** — a *subscription-timing
   artifact*, not absence.
2. With a proper 20 s wait, `market_book_get` returned **10 levels, stable** (`mt5_dom_wait_result.json`).
3. Rich capture (15 s, 0.2 s poll): **5 bid + 5 ask levels**, sizes ∈ [100, 10000],
   **47 distinct books / 75 polls** → the book *does* update (`mt5_dom_rich_result.json`).
4. **Authenticity test (60 snapshots, 0.3 s poll)** → `distinct_ladders = 1`,
   `symmetric_sum_fraction = 1.0`, `spread_values = [0.18]`:

```text
bid_sizes = [100, 400, 500, 4000, 10000]
ask_sizes = [100, 400, 500, 4000, 10000]     # identical, on all 60 snapshots
verdict   = SYNTHETIC_OR_AGGREGATED_PROFILE
```

**Conclusion:** only the *prices* move. The *sizes* are a fixed, mirrored ladder on both sides — a
broker-published **aggregated/synthetic depth profile**, not an order-by-order queue. It therefore
**cannot support TRUE_OFI, MICROPRICE, QUEUE or FILL_PROBABILITY**, and it is **realtime-only**
(no historical DOM exists in the MT5 Python API).

## Classification — FXTM Market Depth

```text
DATA_TYPE          = DOM / L2 (10 levels, realtime)
CLASSIFICATION     = PARTIALLY_RELEVANT
  + directly from the FXTM execution environment (same pool that fills our orders)
  - sizes are a constant synthetic ladder  -> no genuine size/queue information
  - realtime only, no historical replay    -> cannot backtest or reproduce
  - ticks carry no size/print              -> no trade flow
```

**FXTM TRUE L2 (order-by-order) = DATA_GAP. FXTM TRADE FLOW = DATA_GAP. QUEUE = DATA_GAP.
FILL_PROBABILITY = DATA_GAP. HISTORICAL DEPTH = DATA_GAP.**

## Why this matters for V3

### Documentation corroboration (`parts/part_A.md`)

MT5's own documentation explains the measured shape: for OTC symbols "the Depth of Market can be
formed based on the quotes of the broker", and "**if the broker does not provide volumes, the DOM
window functions as a scalping tool**… the Depth of Market displays price levels calculated based on
the Bid and Ask prices using the price change step"
(https://www.metatrader5.com/en/terminal/help/trading/depth_of_market). OTC mode is also documented
as having **no executed-deal data** (https://www.metatrader5.com/en/terminal/help/trading_advanced/price_data),
which matches `last = volume = volume_real = 0`. And FXTM's public URL index contains no
market-depth/Level-2/tick-data/API/FIX page at all. So the synthetic ladder is not a measurement
artifact — it is the documented behaviour of a broker-quoted, volume-less OTC DOM.

The upshot is unchanged in substance but now *evidenced rather than assumed*: the only
size-bearing FXTM feed is a constant synthetic ladder, so `microprice` collapses to `mid` and
`OFI` cannot be computed from real sizes. The prior `DATA_GAP` verdicts
(`TRUE_OFI`, `MICROPRICE`, `QUEUE`, `FILL_PROBABILITY`) **stand**, now with a measured root cause.
