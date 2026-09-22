# TEST SESSION DEFINITION — OFFICIAL RULING 001

`recorded_utc = 2026-09-22T06:25:00Z` · resolves the ambiguity flagged by V3-HFT-TEST-SNAPSHOT-INTEGRITY-001.

| item | ruling |
|---|---|
| SESSION | **CONTIGUOUS_SEGMENT** |
| SEGMENT_BOUNDARY | adjacent valid-event gap **> 3000 s** ⇒ NEW SESSION |
| MIN_SESSION_TICKS | **200,000** |
| below the threshold | `INCOMPLETE` (never padded, merged, or threshold-lowered) |
| first TEST session | `session_start >= 2026-09-22T06:20:00Z` |
| segment straddling TEST_START | truncated at the boundary; the pre-boundary part is NOT TEST |
| session IDs | assigned by **data boundary only** (`TEST-S001` … `TEST-S010`), never by volatility / price move / spread / result |
| TEST data source | FXTM XAUUSD L1 only (no DUKA / CME / LBMA / LMAX / OANDA splice) |

```text
event[i] -> event[i+1]
    dt <= 3000 s  =>  SAME SESSION
    dt >  3000 s  =>  NEW SESSION
```

This ruling is applied verbatim in `collect_test_sessions.py`. No interpretation was added here.
