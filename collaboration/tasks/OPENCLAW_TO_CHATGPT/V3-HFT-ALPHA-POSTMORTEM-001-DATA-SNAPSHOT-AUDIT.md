# DATA_SNAPSHOT_AUDIT — V3-HFT-ALPHA-POSTMORTEM-001

- Mode: **AUDIT_ONLY / READ_ONLY**.
- Question: *which data snapshot did the 30 Alpha-Discovery experiments actually read, and is it
  provable by hash?*

## Frozen input identity

```text
ALPHA_DISCOVERY_INPUT_COMMIT      = b42c865e49e8ea11a740c14dfbddb8eb74b1e161
ALPHA_DISCOVERY_HEAD_RECORD       = e83ae7690526a4722ba3cde6540f6fc29e717118
ALPHA_DISCOVERY_REPORT_SHA256     = 976333c528f06f8fa76a5c661af692774e1964a681cafff6f9891dc9392f0881
ALPHA_DISCOVERY_RESULT_SHA256     = b38e153e545bd0b8646ace00bb200753ec56047ce73f0bd73bbb15301574bd80
FREEZE_SHA256                     = 557bcc3c96338c1261f8a5b70371a6a679ff61ec433fbd24234aabf782b8a4d0
data_manifest_generated_utc       = 2026-09-21T19:47:27Z
```

## Verdict: **PASS_WITH_DATA_GAP** (non-blocking)

Provenance chain: `experiment → data_manifest.json(family) → per-file sha256 → current file bytes`.
`data_manifest.json` **does carry a per-file `sha256`** for every tick file, so the chain is testable.

| family | files | sha256 matches | mismatch | cross-file dup |
|---|---|---|---|---|
| `staging_fxtm/ticks_*` | 24 | **24** | 0 | 0 |
| `live_fxtm/ticks_*` | 11 | **10** | 1 | **913** |

### The single unprovable file

`live_fxtm/ticks_20260921.parquet` — actively appended by the collector **after** the discovery snapshot:

| field | manifest snapshot | now |
|---|---|---|
| rows | 168,582 | 173,318 (**+4,736**) |
| `ts_max_utc` | 2026-09-21T19:39:06.708Z | 2026-09-21T20:09:07.349Z |
| sha256 match | — | **False** |

All other 10 live files match byte-for-byte (rows delta = 0, ts_max unchanged).

### Cross-file duplicates (the "913 rows")

The 913 duplicate timestamps are **cross-day-file boundary repeats**: per-file duplicates = 0.
They do **not** enter the frozen analysis (the discovery run read the pre-append snapshot), so they
are `NON_BLOCKING`. They do mean any *future* study must de-duplicate at file boundaries.

## Why this is non-blocking

- 34 of 35 primary files are byte-provable against the manifest.
- The appended rows fall **after** the discovery run and land inside the TEST window only; the
  frozen products (`oos/`, `backtest/`, `statistics/`) were written before the append.
- Therefore `NO_ALPHA` is not invalidated by the append; only *one tail file's* bytes are
  not re-provable today — recorded honestly as `DATA_GAP`.

## Recommended remediation (not applied here)

Snapshot-freeze (copy + hash) the tick feed before any future OOS run, or run against the
monthly `assembled/` aggregates rather than the live-appending daily tail.
