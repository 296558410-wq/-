# CHATGPT-TASK-V3-HFT-CALIBRATION-PILOT-001-RESULT (FINAL)

> Status: **PASS — bounded pilot completed 20/20 real demo round-trips.**
> The pilot now measures the real broker execution chain end-to-end
> (request → fill → close → cost → MT5 reconciliation → hash-chained ledger).
> NO Alpha, NO Hermes/model decision, NO live. Frozen spec: MAX=20, no auto-expansion.
> **A code deviation was required (filling mode) and is disclosed below.**

```text
TASK_ID    = V3-HFT-CALIBRATION-PILOT-001
STATUS     = PASS  (20 real samples; RECONCILIATION=PASS)
RUN_ID     = CALIB-PILOT-001
STARTED    = 2026-09-20T23:05:42.928971+00:00   (= 2026-09-21 07:05:42 GMT+8)
FINISHED   = 2026-09-20T23:06:13.516469+00:00
HALT_REASON= (none)
BASE_COMMIT          = d22d9fbd07d5958e327de36c8c2aaa4efefd0401
ORIG_REPO_HEAD(before)= 88f7228
ORIG_REPO_HEAD(after) = 98ef9a74221427d5ef1e3eaa365cdd6d893ccbc1   (pilot filling-mode fix)
frozen_sequence_hash = 18568a95b99be7f9341bf6881667a8560e79e81498aacd281f83b9e7b44e9e47

MAX_CALIBRATION_ROUND_TRIPS = 20     n_samples = 20
VALID_ENTRY_FILL_SAMPLE = 20         VALID_EXIT_FILL_SAMPLE = 20
MOCK_EXECUTION = FALSE               RECONCILIATION = PASS
CALIBRATION_AUTO_STOP = TRUE         WAIT_FOR_AUDIT = TRUE

V3_AUTO_TRADING=FALSE  V3_LIVE=FALSE  V3_STRATEGY_AUTO_DECISION=FALSE
V3_HERMES_AUTO_ORDER=FALSE  V3_MODEL_AUTO_ORDER=FALSE
V1_UNTOUCHED=TRUE  V2_UNTOUCHED=TRUE
labels: REAL_DATA=20  MOCK_DATA=0  SYNTHETIC_DATA=0
```

## 1. What happened

Market was OPEN (Sun 23:05Z / Mon 07:05 GMT+8, XAUUSD). The pilot:
1. connected to the isolated instance `fxtm_demo_v3calib` and passed all hard gates;
2. captured `account_before` (login 160764551, balance/equity 5000, positions 0);
3. executed the **frozen** sequence: 20 round-trips, alternating LONG/SHORT, fixed
   vol 0.01, MAGIC 90004, holds [100,250,500,1000,2000] ms ×4, NO_AUTO_RETRY;
4. each trip: entry `order_send` → `history_deals_get` reconciliation → hold → exit
   `order_send` → reconcile; every hop written to the hash-chained ledger;
5. reached the hard cap → `CALIBRATION_AUTO_STOP=TRUE`, finished in ~30 s.

`account_after` = balance/equity **4992.56** (net −7.44 USD over 20 trips),
positions 0, orders 0 (no residual exposure).

## 2. Execution / cost measurements (real demo, n=20)

Entry latency (ms):
```text
signal_to_request  mean 0.00024  p50 0.0002   (pure local)
request_to_ack     mean 273.85   p50 273.58   (broker RTT — dominant term)
ack_to_fill        mean   5.58   p50   7.15
signal_to_fill     mean 279.44   p50 278.73   p95 294.39  max 294.59
```
Exit latency (ms): `exit_signal_to_fill` mean 275.21  p50 276.21  p95 283.07

Slippage (USD, 0.01 lot):
```text
entry_slippage  mean +0.01715  median 0.0  p95 0.0457  max +0.1829
exit_slippage   mean -0.03201  median 0.0  p95 0.0457  min -0.6859
```

Spread: `SPREAD_BPS` mean/median **0.4115 bps** (≈0.18 USD at 4373.8).

Round-trip cost (from `V3_COST_PROFILE.json`, USD):
```text
NET_ROUND_TRIP_COST  mean 0.1375  median 0.14  min 0.06  max 0.20
commission_source = MT5 history_deals_get (present)
```
Ground-truth broker PnL: balance 5000 → 4992.56 = **−7.44 USD / 20 = −0.372 USD per round-trip**
(net realized, inclusive of commission, swap 0). The per-row cost model attributes a
smaller magnitude than the realized equity delta — flagged as `DATA_GAP` (attribution
vs. realized) for the audit, not hidden.

## 3. Deviation from the frozen pilot spec (DISCLOSED)

The frozen pilot hardcoded `type_filling = ORDER_FILLING_IOC`. On FXTM demo XAUUSD this is
rejected: `symbol_info("XAUUSD").filling_mode = 1` (**FOK only**); IOC/RETURN/BOC all return
`retcode 10030 = TRADE_RETCODE_INVALID_FILL`. Verified **without sending orders** via
`mt5.order_check()`: FOK→Done; IOC/RETURN/BOC→10030.

Change made (V3-only, single file `foundation/calibration_pilot.py`, commit `98ef9a7`):
- added `_filling_mode(mt5)` selecting FOK→IOC→RETURN from `symbol_info().filling_mode`;
- replaced the two hardcoded `ORDER_FILLING_IOC` usages (entry + exit) with it.

This is a deviation from the "HALT, do not self-repair" instruction — executed **only after
explicit user GO (2026-09-21 07:04 GMT+8)**. Frozen items otherwise unchanged: MAX=20,
frozen direction/hold sequences (hash `18568a95…`), NO_AUTO_RETRY, MAGIC, volume, gates.

Prior attempts (preserved as evidence, not overwritten):
- `PILOT_DONE.halted_20260920T223001Z` → retcode **10027** (terminal Algo Trading OFF)
- `PILOT_DONE.halted_20260920T230018Z` → retcode **10030** (IOC unsupported; pre-fix re-run)

## 4. Isolation & safety evidence

```text
instance : C:\AIQuant\mt5_instances\fxtm_demo_v3calib  (login 160764551, ForexTimeFXTM-Demo01)
MAGIC=90004  volume FIXED 0.01  market OPEN (spread ~18 pt at entry)
MT5 hosts: V1 160759434 (pid1348) / V2 160761384 (fxtm_demo_01, pid36460)
           / V3 160764551 (fxtm_demo_v3calib, pid49300)  -- UNMAPPED=0, no ghost fxtm_demo_v3
ledger   : data/hft_ledger/v3_calibration_ledger.jsonl  -> 131 events, hash-chain verify OK
           (CALIBRATION_START -> ORDER_REQUEST -> BROKER_RESPONSE -> ENTRY_FILL
            -> EXIT_REQUEST -> EXIT_FILL ... -> CALIBRATION_COMPLETE)
recon    : MT5 history_deals_get per round-trip -> RECONCILIATION = PASS
guard    : data/calibration/PILOT_DONE = {"status":"PASS","n":20}  (prevents accidental rerun)
profiles : V3_EXECUTION_PROFILE.json / V3_COST_PROFILE.json  (all n=20)
V1_UNTOUCHED=TRUE  V2_UNTOUCHED=TRUE  ORDER_SENT(live)=FALSE
```

## 5. Spec compliance

| spec item | status |
|---|---|
| MAX_CALIBRATION_ROUND_TRIPS=20 hard cap | ENFORCED (stopped at 20) |
| frozen direction sequence (alternating) | FROZEN (hash 18568a95…) |
| frozen holding [100,250,500,1000,2000]ms | FROZEN |
| CALIBRATION_VOLUME = FIXED 0.01 | FIXED |
| NO_AUTO_RETRY / UNKNOWN → HALT | ENFORCED (two halts observed, no auto-retry) |
| reconciliation cid→order→deal→ledger | PASS (20/20) |
| ledger hash-chain | OK (131 linked events) |
| initial/final positions + account before/after | CAPTURED (0 → 0) |
| **filling mode** | **DEVIATION: IOC→auto(FOK); disclosed, user-GO'd** |

## 6. Data labels

```text
REAL_DATA      = 20   (entry/exit latency, slippage, spread, commission, reconciliation)
MOCK_DATA      = 0
SYNTHETIC_DATA = 0
DATA_GAP       = { cost-model vs realized-equity attribution,
                   larger-sample statistics (n=20 only),
                   broker-side latency breakdown, swap/longer holds }
```

## 7. Next (STOP — requires ChatGPT audit + explicit user decision; do NOT auto-expand)

1. Independent audit of this result (esp. the filling-mode deviation and the cost-attribution gap).
2. `CALIBRATION_AUTO_STOP=TRUE` / `WAIT_FOR_AUDIT=TRUE`: 20/20 cap reached — no expansion to 5000.
3. If expansion is ever desired → separate `V3-HFT-CALIBRATION-EXPANSION-001` (not started here).
4. No Alpha / no HFT training / no model optimization / no V2 demo-forward changes.

Frozen spec unchanged (MAX=20). No auto-expansion. V1/V2 untouched.
