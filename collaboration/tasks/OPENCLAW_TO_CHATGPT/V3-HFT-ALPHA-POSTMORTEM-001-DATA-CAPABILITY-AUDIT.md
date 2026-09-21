# DATA_CAPABILITY_AUDIT — V3-HFT-ALPHA-POSTMORTEM-001

- Mode: **AUDIT_ONLY / READ_ONLY**.

## Verdict: **DATA_GAP** — feed is `L1_QUOTE_ONLY` (price / spread / time only)

## Fields that exist

| field | status |
|---|---|
| `bid`, `ask`, `ts_utc` (`datetime64[ms, UTC]`), `flags` | present |
| `mid = (bid+ask)/2`, `spread = ask-bid` | derived (exact) |

## Fields that are missing or identically zero

| field | evidence |
|---|---|
| `volume` | `volume_nonzero_frac = 0` on every FXTM file |
| `volume_real` | `volume_real_nonzero_frac = 0` on every FXTM file |
| `last` (trade price) | `last_nonzero_frac = 0` on every FXTM file |
| L2 order book / depth, order sizes, queue position, signed trade flow | **absent from the feed** |

Independent re-check (this audit, read-only): across all 35 FXTM files the count of rows with
`volume != 0` or `last != 0` is **0**.

## Consequence for feature families

| concept | status |
|---|---|
| microprice `(bid·ask_vol + ask·bid_vol)/(bid_vol+ask_vol)` | **DATA_GAP** — needs sizes |
| true order-flow imbalance (signed sizes) | **DATA_GAP** |
| VPIN / Kyle-λ / queue imbalance | **DATA_GAP** |
| B2 order-flow imbalance | only a **tick-rule L1 proxy** (`sign(Δmid)` over 20 ticks) — a weak information proxy, not real flow |

`FEATURE_CAPABILITY = L1_QUOTE_ONLY`. Only price-derived families (B0, B3, B4, B5, B6) plus the
tick-rule B2 proxy are testable. **Any future claim of a microstructure / order-flow alpha is
untestable on this feed** and must not be inferred from a null result on it.
