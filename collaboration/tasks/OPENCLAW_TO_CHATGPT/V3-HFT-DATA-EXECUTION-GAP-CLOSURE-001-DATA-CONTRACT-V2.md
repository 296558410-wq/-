# V3 Research Data Contract v2

Task: **V3-HFT-DATA-EXECUTION-GAP-CLOSURE-001** (task XXXIII).
Any experiment that violates this contract is an **INVALID EXPERIMENT**.

## 1. SOURCE

```text
FXTM demo (magic 90004) is the ONLY execution reference.
  staging_fxtm/ticks_*.parquet   (historical batch)
  live_fxtm/ticks_*.parquet      (live, continuously APPENDED)
```

Other sources (DUKA, Yahoo, Sina, Tencent, GC, GLD) may be used **only** as explicitly-marked
auxiliary research. They must **never** substitute FXTM's executable bid/ask/spread/execution price.

## 2. SNAPSHOT

```text
SNAPSHOT_ID                = V3-SNAP-20260922T025312Z
path                       = trader_v3/data/snapshots/<SNAPSHOT_ID>/
rule                       = research READS THE SNAPSHOT ONLY, never the live feed
LIVE_SOURCE_MUTABLE        = TRUE      (the collector may keep appending)
RESEARCH_SNAPSHOT_IMMUTABLE= TRUE      (copy-on-cut + read-only attribute + per-file sha256)
```

## 3. TIMEZONE / TIMESTAMP_UNIT

```text
TIMEZONE        = UTC (required)
TIMESTAMP_UNIT  = ms (declared, never inferred)
guard           = microstructure/timestamp_unit_guard.py
rule            = a missing/unknown unit -> DATA_INVALID (never a guess)
```

## 4. FIELDS

| field | rule |
|---|---|
| BID, ASK | real quotes; `mid = (bid+ask)/2` |
| SPREAD | `ask - bid`; must be > 0 |
| EXECUTION_PRICE | long enters at `ask`, short enters at `bid` (never mid) |
| volume / volume_real / last | identically 0 → **DATA_GAP**; never a signal |

## 5. COST_MODEL

```text
COST_MODEL_VERSION = CALIBRATION_20RT_20260921
REAL_RT_COST_BP    = 0.914   (spread 0.18 + commission 0.22 USD/RT)
0.314 bp           = HISTORICAL_INVALID_FOR_CURRENT_RESEARCH  (must not appear)
six separate terms : spread_cost, commission, slippage, latency_cost, adverse_selection, impact
slippage           : SIGNED; only the UNFAVORABLE part is a cost; abs(slippage) forbidden
commission         : broker PnL is negative-of-cost; research/ledger costs are positive-subtracted
```

## 6. MARKOUT

```text
LONG :  EXECUTION_MARKOUT = future_mid - entry_execution_price
SHORT:  EXECUTION_MARKOUT = entry_execution_price - future_mid
MID_MARKOUT           = direction * (future_mid - entry_mid)
COST_ADJUSTED_MARKOUT = MID_MARKOUT - cost_bp
MARKOUT > 0 => favorable move
```

## 7. ADVERSE SELECTION

```text
LONG_AS_h  = entry_execution_price - future_mid
SHORT_AS_h = future_mid - entry_execution_price
AS > 0 => adverse (price moved against the fill)
AS = -EXECUTION_MARKOUT
```

## 8. DATA_GAP

Unmeasurable ⇒ `DATA_GAP`. Never `0`, never an unnamed proxy. Proxies carry a `_PROXY` suffix.

## 9. OBSERVABILITY

Every execution field carries `OBSERVABLE | PARTIAL | NOT_OBSERVABLE`.
`NOT_OBSERVABLE` ⇒ derived statistics are `NOT_TESTED`, never 0.

## 10. CENSORING

Long-horizon samples whose forward window is cut by the sample end are
`HORIZON_CENSORED` (not eligible), never `0`.

## 11. VALIDITY

An experiment is INVALID if it: reads the live feed directly; omits the timestamp unit;
uses the 0.314 bp cost; folds `abs(slippage)` into cost; treats `NOT_OBSERVABLE` as 0;
or reports a bare WIN/LOSS without a failure type.
