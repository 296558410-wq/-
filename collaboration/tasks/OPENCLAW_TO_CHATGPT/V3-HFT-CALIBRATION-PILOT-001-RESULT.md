# CHATGPT-TASK-V3-HFT-CALIBRATION-PILOT-001-RESULT (PRELIMINARY)

> Status: **INCOMPLETE / PENDING MARKET** — pilot built, armèd and gated; real demo run executes at market open.
> 0 orders sent so far. This is an honest pre-run report, not a PASS.

```text
TASK_ID   = V3-HFT-CALIBRATION-PILOT-001
STATUS    = INCOMPLETE (awaiting market open; 0 real samples)
BASE_COMMIT = d22d9fbd07d5958e327de36c8c2aaa4efefd0401
FOUNDATION_STAGING_COMMIT = 063a4927570a0857eb1c3152d4f357d73c11e602
MOCK_EXECUTION = FALSE (real run)   |   selftest used MOCK only (labeled)

V3_AUTO_TRADING=FALSE  V3_LIVE=FALSE  ORDER_SENT=FALSE
V3_STRATEGY_AUTO_DECISION=FALSE  V3_HERMES_AUTO_ORDER=FALSE  V3_MODEL_AUTO_ORDER=FALSE
V1_UNTOUCHED=TRUE  V2_UNTOUCHED=TRUE
```

## Why not run yet
Market is CLOSED (weekend). The pilot refuses to run when the quote is stale
(`REFUSE: market closed / stale tick`), so no synthetic fills were produced.
XAUUSD reopens ~Sun 22:00Z (Mon 06:00 GMT+8).

## Built to spec (all verified)

| spec item | status |
|---|---|
| MAX_CALIBRATION_ROUND_TRIPS=20 hard cap | ENFORCED (n>20 refused) |
| frozen direction sequence (LONG/SHORT alternating) | FROZEN, hash `18568a95…` |
| frozen holding sequence [100,250,500,1000,2000]ms | FROZEN |
| CALIBRATION_VOLUME=FIXED (broker volume_min 0.01) | FIXED |
| independent gate authorized=True | DEFAULT OFF; run requires explicit path |
| NO_AUTO_RETRY / UNKNOWN → HALT | IMPLEMENTED |
| auto-stop on 24 safety conditions | IMPLEMENTED |
| entry measurement (signal/req/ack/fill, slippage, spread) | IMPLEMENTED |
| exit measurement (fixed hold → close) | IMPLEMENTED |
| commission/swap from MT5 deals (0 vs UNKNOWN) | IMPLEMENTED |
| MT5 reconciliation (cid↔order↔deal↔ledger) | IMPLEMENTED (PASS required to count) |
| ledger events CALIBRATION_START…COMPLETE, hash-chained | IMPLEMENTED |
| initial/final positions, must end 0 open | IMPLEMENTED |
| account before/after (balance/equity/margin) | IMPLEMENTED |
| data separation REAL/MOCK/SYNTHETIC/DATA_GAP | IMPLEMENTED |

## Isolation note (§3 vs §4)
Spec §4 names data dir `fxtm_demo_v3`; that instance is in fact **logged into V1's account (160759434)**.
Using it would violate the §3 isolation hard-rule (V1 untouched / forbidden V1 MT5).
→ Pilot uses the isolated **`fxtm_demo_v3calib`** instance (login **160764551**), verified `independent=TRUE`.

## Evidence (read-only preflight, this run)
```text
instance: fxtm_demo_v3calib  login=160764551  server=ForexTimeFXTM-Demo01  balance=5000  positions=0
spec: point 0.01 digits 2 tick_size 0.01 tick_value 0.1 contract 100 volume_min 0.01
other logins: v1_host=160759434  v2_fxtm_demo_01=160761384  (no collision)
safety flags: V3_LIVE/ORDER_SEND/FORWARD_ALLOWED = NO
selftest (MOCK): chain_ok=true   (labeled MOCK, not calibration data)
```

## Scheduled real run
```text
task  : \OpenClaw\v3-calibration-pilot
when  : 2026-09-21 06:30 GMT+8
cmd   : run_calibration_pilot.cmd  -> python -m foundation.calibration_pilot --run --n 20
log   : trader_v3/logs/calibration_pilot.log
output: state/V3_CALIBRATION_PILOT.json, V3_EXECUTION_PROFILE.json, V3_COST_PROFILE.json
        data/calibration/registry.jsonl
```

## Data labels
```text
REAL_DATA      = 0   (0 real samples yet)
MOCK_DATA      = selftest only (not counted)
SYNTHETIC_DATA = 0
DATA_GAP       = real entry/exit latency, real slippage, real commission/swap, reconciliation
```

## Next
After the 06:30 run → generate the FINAL result (REAL_DATA), then **STOP and WAIT_FOR_AUDIT** (no auto-expansion to 5000).
