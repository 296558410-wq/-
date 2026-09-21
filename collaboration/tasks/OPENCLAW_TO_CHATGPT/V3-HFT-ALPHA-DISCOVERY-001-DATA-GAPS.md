# V3-HFT-ALPHA-DISCOVERY-001 — DATA GAPS (measured, not assumed)

- Generated: 2026-09-21T19:47:27.267187+00:00
- Source: real scan of parquet files under `C:\AIQuant` (`alpha/tools/scan_data.py`).
- No value below is inferred from the registry; every number comes from reading the files.

## 1. Registered gaps that remain open (carried from `state/V3_DATA_REGISTRY_v2.json`)

| gap | status | impact on this study |
|---|---|---|
| `2023-12` | MISSING | DUKA tick timeline not contiguous across 2023-11→2024-01 |
| `2024-04 → 2026-07` (28 months) | MISSING | **no 1h/4h/1d horizon is measurable on DUKA across this window** |
| `daily 21:00–22:59Z` | MISSING | only 1-2 hours/day; long-horizon windows cross it |
| `L2 / trade_flow` | UNKNOWN (L2_DATA_GAP) | B1 microprice and true B2 OFI are **not computable** |

## 2. Feed-level facts measured in this scan

### 2.1 FXTM staging ticks (primary feed, part 1)

| file | rows | ts_min (UTC) | ts_max (UTC) | max_gap_s | dup_rate | ooo_rate | med_spread_USD | tick_Hz |
|---|---|---|---|---|---|---|---|---|
| ticks_20260804.parquet | 191470 | 2026-08-04T01:05:00 | 2026-08-04T23:54:59 | 8.5 | 0.00000 | 0.000000 | 0.150 | 2.33 |
| ticks_20260805.parquet | 219587 | 2026-08-05T01:05:00 | 2026-08-05T23:54:59 | 8.7 | 0.00000 | 0.000000 | 0.150 | 2.67 |
| ticks_20260806.parquet | 216506 | 2026-08-06T01:05:00 | 2026-08-06T23:54:59 | 10.9 | 0.00000 | 0.000000 | 0.150 | 2.63 |
| ticks_20260807.parquet | 219909 | 2026-08-07T01:05:00 | 2026-08-07T23:54:59 | 12.7 | 0.00000 | 0.000000 | 0.150 | 2.67 |
| ticks_20260810.parquet | 206727 | 2026-08-10T01:05:00 | 2026-08-10T23:54:59 | 11.4 | 0.00000 | 0.000000 | 0.150 | 2.52 |
| ticks_20260811.parquet | 203565 | 2026-08-11T01:05:00 | 2026-08-11T23:54:59 | 10.5 | 0.00000 | 0.000000 | 0.150 | 2.48 |
| ticks_20260812.parquet | 200747 | 2026-08-12T01:05:00 | 2026-08-12T23:54:59 | 11.7 | 0.00000 | 0.000000 | 0.150 | 2.44 |
| ticks_20260813.parquet | 208013 | 2026-08-13T01:05:00 | 2026-08-13T23:54:59 | 10.2 | 0.00000 | 0.000000 | 0.150 | 2.53 |
| ticks_20260814.parquet | 191547 | 2026-08-14T01:05:00 | 2026-08-14T23:54:59 | 12.2 | 0.00000 | 0.000000 | 0.150 | 2.33 |
| ticks_20260817.parquet | 195802 | 2026-08-17T01:05:00 | 2026-08-17T23:54:58 | 10.3 | 0.00000 | 0.000000 | 0.150 | 2.38 |
| ticks_20260818.parquet | 196600 | 2026-08-18T01:05:00 | 2026-08-18T23:54:59 | 9.7 | 0.00000 | 0.000000 | 0.150 | 2.39 |
| ticks_20260819.parquet | 216186 | 2026-08-19T01:05:00 | 2026-08-19T23:54:59 | 8.9 | 0.00000 | 0.000000 | 0.150 | 2.63 |
| ticks_20260820.parquet | 216009 | 2026-08-20T01:05:00 | 2026-08-20T23:54:59 | 9.9 | 0.00000 | 0.000000 | 0.150 | 2.63 |
| ticks_20260821.parquet | 214297 | 2026-08-21T01:05:00 | 2026-08-21T23:54:59 | 9.6 | 0.00000 | 0.000000 | 0.150 | 2.61 |
| ticks_20260824.parquet | 236997 | 2026-08-24T01:05:00 | 2026-08-24T23:54:59 | 7.4 | 0.00000 | 0.000000 | 0.160 | 2.88 |
| ticks_20260825.parquet | 226707 | 2026-08-25T01:05:00 | 2026-08-25T23:54:59 | 12.9 | 0.00000 | 0.000000 | 0.160 | 2.76 |
| ticks_20260826.parquet | 205517 | 2026-08-26T01:05:00 | 2026-08-26T23:54:59 | 10.2 | 0.00000 | 0.000000 | 0.150 | 2.50 |
| ticks_20260827.parquet | 210034 | 2026-08-27T01:05:00 | 2026-08-27T23:54:59 | 9.6 | 0.00000 | 0.000000 | 0.150 | 2.56 |
| ticks_20260828.parquet | 221907 | 2026-08-28T01:05:00 | 2026-08-28T23:54:59 | 9.3 | 0.00000 | 0.000000 | 0.150 | 2.70 |
| ticks_20260831.parquet | 219813 | 2026-08-31T01:05:00 | 2026-08-31T23:54:59 | 13.8 | 0.00000 | 0.000000 | 0.150 | 2.67 |
| ticks_20260901.parquet | 226039 | 2026-09-01T01:05:00 | 2026-09-01T23:54:58 | 9.4 | 0.00000 | 0.000000 | 0.150 | 2.75 |
| ticks_20260902.parquet | 219698 | 2026-09-02T01:05:00 | 2026-09-02T23:54:59 | 12.0 | 0.00000 | 0.000000 | 0.150 | 2.67 |
| ticks_20260903.parquet | 215354 | 2026-09-03T01:05:00 | 2026-09-03T23:54:59 | 10.5 | 0.00000 | 0.000000 | 0.150 | 2.62 |
| ticks_20260904.parquet | 116824 | 2026-09-04T01:05:00 | 2026-09-04T15:50:12 | 9.6 | 0.00000 | 0.000000 | 0.160 | 2.20 |

- files=24, rows=4995855

### 2.2 FXTM live-collected ticks (primary feed, part 2)

| file | rows | ts_min (UTC) | ts_max (UTC) | max_gap_s | dup_rate | ooo_rate | med_spread_USD | tick_Hz |
|---|---|---|---|---|---|---|---|---|
| ticks_20260907.parquet | 166470 | 2026-09-07T01:05:00 | 2026-09-08T01:16:44 | 12900.5 | 0.00000 | 0.000000 | 0.150 | 1.91 |
| ticks_20260908.parquet | 203959 | 2026-09-08T01:15:44 | 2026-09-09T01:09:07 | 6314.6 | 0.00000 | 0.000000 | 0.150 | 2.37 |
| ticks_20260909.parquet | 210343 | 2026-09-09T01:08:07 | 2026-09-10T01:09:06 | 4201.4 | 0.00000 | 0.000000 | 0.150 | 2.43 |
| ticks_20260910.parquet | 233558 | 2026-09-10T01:08:06 | 2026-09-11T01:09:06 | 4200.3 | 0.00000 | 0.000000 | 0.150 | 2.70 |
| ticks_20260911.parquet | 227498 | 2026-09-11T01:08:06 | 2026-09-14T01:09:06 | 177001.0 | 0.00000 | 0.000000 | 0.150 | 0.88 |
| ticks_20260914.parquet | 214223 | 2026-09-14T01:08:06 | 2026-09-15T01:09:05 | 4201.6 | 0.00000 | 0.000000 | 0.150 | 2.48 |
| ticks_20260915.parquet | 184111 | 2026-09-15T01:08:05 | 2026-09-16T01:09:06 | 11217.0 | 0.00000 | 0.000000 | 0.140 | 2.13 |
| ticks_20260916.parquet | 223031 | 2026-09-16T01:08:06 | 2026-09-17T01:09:06 | 4200.2 | 0.00000 | 0.000000 | 0.150 | 2.58 |
| ticks_20260917.parquet | 213403 | 2026-09-17T01:08:07 | 2026-09-18T01:09:06 | 4200.2 | 0.00000 | 0.000000 | 0.150 | 2.47 |
| ticks_20260918.parquet | 199006 | 2026-09-18T01:08:06 | 2026-09-21T01:09:06 | 177000.1 | 0.00000 | 0.000000 | 0.140 | 0.77 |
| ticks_20260921.parquet | 168582 | 2026-09-21T01:08:06 | 2026-09-21T19:39:06 | 7.0 | 0.00000 | 0.000000 | 0.140 | 2.53 |

- files=11, rows=2244184

### 2.3 DUKA assembled monthly ticks (secondary / cross-venue check)

| file | rows | ts_min (UTC) | ts_max (UTC) | max_gap_s | dup_rate | ooo_rate | med_spread_USD | tick_Hz |
|---|---|---|---|---|---|---|---|---|
| ticks_202309.parquet | 1916813 | 2023-09-01T22:00:00 | 2023-09-30T23:59:58 | 792007.3 | 0.00000 | 0.000000 | 0.320 | 0.76 |
| ticks_202310.parquet | 1687661 | 2023-10-01T00:00:00 | 2023-10-30T23:59:57 | 579620.9 | 0.00000 | 0.000000 | 0.327 | 0.65 |
| ticks_202311.parquet | 2212646 | 2023-11-01T00:00:00 | 2023-11-29T21:58:59 | 493231.1 | 0.00000 | 0.000000 | 0.330 | 0.89 |
| ticks_202401.parquet | 2126396 | 2024-01-01T00:00:00 | 2024-01-29T23:59:59 | 176421.8 | 0.00000 | 0.000000 | 0.327 | 0.85 |
| ticks_202402.parquet | 2318825 | 2024-02-01T21:00:00 | 2024-02-28T20:58:59 | 176402.9 | 0.00000 | 0.000000 | 0.337 | 0.99 |
| ticks_202403.parquet | 4203589 | 2024-03-01T00:00:00 | 2024-03-30T13:59:59 | 226800.6 | 0.00000 | 0.000000 | 0.374 | 1.65 |
| ticks_202608.parquet | 1098038 | 2026-08-01T00:00:00 | 2026-08-04T20:59:58 | 3621.0 | 0.00000 | 0.000000 | 0.630 | 3.28 |

- files=7, rows=15563968

### 2.4 DUKA daily ticks (`ticks_YYYYMMDD.parquet`, 140 files)

- files=140, rows=15563968 (identical row total to the assembled monthly files:
  the daily files are the same ticks split by day, reconstructed as `date(from filename) + hour + ms-within-hour`).
- date range: `ticks_20230901.parquet` → `ticks_20260804.parquet`
- some 'days' only contain the tail of a session (e.g. `ticks_20230901` covers hours 22-23 only).

### 2.5 DUKA candles

- files=179, rows=15618240, 2010-01-01 → 2026-08-03, columns=['sec', 'open', 'close', 'low', 'high', 'vol', 'side', 'day']
- prices are int-scaled (×1e3); `side` ∈ {BID, ASK}; `sec` = second-of-day.

## 3. Structural gaps that block specific horizons

| horizon | blocking fact |
|---|---|
| 50 ms, 200 ms | FXTM median inter-tick interval ≈ 350–520 ms (1.9–2.7 Hz feed): the feed **cannot resolve** sub-second horizons; most forward windows contain 0 ticks |
| 1 h, 24 h (DUKA) | `2024-04 → 2026-07` missing: no contiguous long-horizon window; `daily 21:00–22:59Z` missing |
| 24 h (FXTM) | only ~34 trading days exist in total → effective_n is tiny |
| B1 / true B2 | `volume`, `volume_real`, `last` are **identically 0** on the whole FXTM feed and `bid_vol == ask_vol` in 33–85% of DUKA ticks |

## 4. Deliberate non-actions

- No interpolation of missing ticks/bars. Missing intervals are reported as gaps.
- No synthesis of L2 fields; B1/B2 true forms are marked `DATA_GAP`.
- No cross-gap stitching for label windows (segment-aware labels).
