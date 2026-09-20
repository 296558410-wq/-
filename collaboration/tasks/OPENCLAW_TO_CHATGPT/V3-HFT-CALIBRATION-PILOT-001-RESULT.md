# CHATGPT-TASK-V3-HFT-CALIBRATION-PILOT-001-RESULT (FINAL)

> Status: **HALTED (bounded pilot attempted at market open; 0 real samples)**
> The scheduled run executed at market open, passed isolation/safety gates, attempted
> the first entry, and was **halted by the broker with retcode=10027
> (TRADE_RETCODE_CLIENT_DISABLES_AT = "Autotrading disabled by client terminal")**.
> NO_AUTO_RETRY honoured -> no retry, no exp/expansion. WAIT_FOR_AUDIT.

```text
TASK_ID    = V3-HFT-CALIBRATION-PILOT-001
STATUS     = HALTED  (0 real samples; broker refused first order, terminal-side)
RUN_ID     = CALIB-PILOT-001
STARTED    = 2026-09-20T22:30:01.184018+00:00  (= 2026-09-21 06:30:01 GMT+8)
FINISHED   = 2026-09-20T22:30:01.369681+00:00
HALT_REASON= "UNKNOWN entry retcode=10027 (NO_AUTO_RETRY)"
BASE_COMMIT        = d22d9fbd07d5958e327de36c8c2aaa4efefd0401
FOUNDATION_STAGING = 063a4927570a0857eb1c3152d4f357d73c11e602
frozen_sequence_hash = 18568a95b99be7f9341bf6881667a8560e79e81498aacd281f83b9e7b44e9e47

MAX_CALIBRATION_ROUND_TRIPS = 20     n_samples = 0
VALID_ENTRY_FILL_SAMPLE = 0          VALID_EXIT_FILL_SAMPLE = 0
MOCK_EXECUTION = FALSE               RECONCILIATION = PARTIAL
CALIBRATION_AUTO_STOP = FALSE        WAIT_FOR_AUDIT = TRUE

V3_AUTO_TRADING=FALSE  V3_LIVE=FALSE  ORDER_SENT=FALSE
V3_STRATEGY_AUTO_DECISION=FALSE  V3_HERMES_AUTO_ORDER=FALSE  V3_MODEL_AUTO_ORDER=FALSE
V1_UNTOUCHED=TRUE  V2_UNTOUCHED=TRUE
```

## What happened

Market was OPEN (Sun 22:30Z / Mon 06:30 GMT+8, XAUUSD; spread ~23 pt). The pilot:
1. connected to the isolated instance and passed all hard gates;
2. captured `account_before` (login 160764551, balance/equity 5000, positions 0);
3. issued **one** entry request (decision `V3CAL-00`, LONG, fixed vol 0.01, MAGIC 90004);
4. broker returned `order_id=0` -> **retcode 10027**;
5. NO_AUTO_RETRY -> HALT. No exit, no fills, positions still 0, `account_after` unchanged.

## Root cause

`retcode 10027 = TRADE_RETCODE_CLIENT_DISABLES_AT`:
**Automated/algorithmic trading is DISABLED in the client terminal**
(`fxtm_demo_v3calib`). Note `account_info().trade_allowed = true` (account-level OK);
the block is terminal-level (the MT5 "Algo Trading" toggle /
Tools>Options>Expert Advisors "Allow algorithmic trading" is OFF).

Earlier V3 tasks only ever used **MOCK** execution, so this terminal-side gate had
never been exercised against the real `order_send` path until now.

## Evidence (this run)

```text
instance : C:\AIQuant\mt5_instances\fxtm_demo_v3calib  (login 160764551, ForexTimeFXTM-Demo01)
spec     : XAUUSD point 0.01 digits 2 tick_size 0.01 tick_value 0.1 contract 100 vol_min 0.01
spread   : 23 (0.23 USD)
account_before == account_after : balance 5000 / equity 5000 / margin_free 5000 / positions 0
V3_INITIAL_POSITIONS = 0   V3_FINAL_POSITIONS = 0   V3_CALIBRATION_OPEN_POSITIONS = 0
ledger   : data/hft_ledger/v3_calibration_ledger.jsonl  (4 events, hash-chained)
           CALIBRATION_START -> ORDER_REQUEST(price 4376.02, bid 4375.79, spread 0.23)
           -> BROKER_RESPONSE(order_id 0, price 0.0) -> CALIBRATION_COMPLETE(roundtrips=0)
MT5 hosts: V1 160759434 (pid1348) / V2 160761384 (fxtm_demo_01, pid36460)
           / V3 160764551 (fxtm_demo_v3calib, pid49300)  -- UNMAPPED=0, no ghost fxtm_demo_v3
guard    : data/calibration/PILOT_DONE = {"status":"HALTED","n":0}  (prevents accidental rerun)
profiles : V3_EXECUTION_PROFILE.json / V3_COST_PROFILE.json  -> all n=0
```

## Spec compliance (built + verified)

| spec item | status |
|---|---|
| MAX_CALIBRATION_ROUND_TRIPS=20 hard cap | ENFORCED |
| frozen direction sequence (alternating) | FROZEN (hash 18568a95…) |
| frozen holding [100,250,500,1000,2000]ms | FROZEN |
| CALIBRATION_VOLUME=FIXED 0.01 | FIXED |
| NO_AUTO_RETRY / UNKNOWN -> HALT | EXERCISED (this run) |
| auto-stop gate set | IMPLEMENTED |
| MT5 reconciliation cid->order->deal->ledger | IMPLEMENTED (PARTIAL: no deal to reconcile) |
| ledger hash-chain | OK (4 linked events) |
| initial/final positions + account before/after | CAPTURED (both 0) |

## Data labels

```text
REAL_DATA      = 0   (no fills)
MOCK_DATA      = selftest only
SYNTHETIC_DATA = 0
DATA_GAP       = entry/exit latency, slippage, commission/swap, reconciliation  (all still open)
```

## Next (requires explicit user decision — do NOT auto-repair)

1. **Enable algorithmic trading** on the `fxtm_demo_v3calib` terminal
   (Algo Trading toggle / Tools>Options>Expert Advisors) — an environment action, not code.
2. Clear the anti-rerun guard `data/calibration/PILOT_DONE` (only if re-running).
3. Re-arm `\OpenClaw\v3-calibration-pilot` (--n 20) at market open and re-run.
4. Then FINAL REAL_DATA result -> **STOP / WAIT_FOR_AUDIT** (no auto-expansion to 5000).

No Alpha / no Hermes/model decision / no live. Frozen spec unchanged.
