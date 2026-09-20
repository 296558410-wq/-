# CHATGPT-TASK-MT5-INSTANCE-ISOLATION-AUDIT-FIX-001-RESULT

```text
TASK_ID = MT5-INSTANCE-ISOLATION-AUDIT-FIX-001
STATUS  = PASS
BEFORE_INSTANCE_COUNT = 4
AFTER_INSTANCE_COUNT  = 3

MT5_INSTANCE_ISOLATION = PASS

V1_UNTOUCHED = TRUE (strategy/config/scheduler/ledger unchanged; ONE instance-management line pinned - see §6)
V2_UNTOUCHED = TRUE
V3_CALIBRATION_PAUSED = TRUE
ORDER_SENT = FALSE
```

## 1. All discovered instances

| ID | project | exe | portable | data_dir | account | magic | pid | state |
|---|---|---|---|---|---|---|---|---|
| INSTANCE_1 | V1 | `C:\Program Files\ForexTime (FXTM) MT5` | no | roaming `158904DF…` | 160759434 | 90002 | 1348 | RUNNING |
| INSTANCE_2 | V2 | `mt5_instances\fxtm_demo_01` | **yes** | `mt5_instances\fxtm_demo_01` | 160761384 | 90003 | 36460 | RUNNING |
| INSTANCE_3 | **V3** | `mt5_instances\fxtm_demo_v3calib` | **yes** | `mt5_instances\fxtm_demo_v3calib` | 160764551 | 90004 | 45404 | RUNNING |
| INSTANCE_4 | UNMAPPED | `mt5_instances\fxtm_demo_v3` | no | roaming `ACE7B8DA…` | 160759434 | – | (was 56544/60436/60880/5740) | **STOPPED / RETIRED** |

> Account 160759434 appeared on **two** terminals (INSTANCE_1 and INSTANCE_4) — the duplication the task targeted.

## 2. Final mapping (after fix)

```text
V1 -> INSTANCE_1  Program Files          acct 160759434  magic 90002  PID 1348
V2 -> INSTANCE_2  fxtm_demo_01 /portable acct 160761384  magic 90003  PID 36460
V3 -> INSTANCE_3  fxtm_demo_v3calib /portable acct 160764551 magic 90004  PID 45404
```

## 3. FOURTH INSTANCE — root cause (required §11/§24)

**WHO_STARTED_IT**
- `fxtm_demo_v3calib` was created by **OpenClaw** during the calibration session (2026-09-20 19:58, parent python = the calibration preflight).
- `fxtm_demo_v3` was a **phantom** auto-(re)launched by `mt5.initialize()` — the money_hunter dashboard's `_quote_loop` (PID 4044) spawned it.

**WHY_IT_EXISTED**
1. **2026-09-17 V3 setup** created `mt5_instances\fxtm_demo_v3` (a **non-portable** copy) and pointed V3's credentials at **V1's** `.env.mt5_demo` (`DEMO_MT5_LOGIN=160759434`). So the "V3 instance" was **born on V1's account**.
2. Several components call **`mt5.initialize()` with NO `path`**:
   `trader_v1/broker_mt5_demo.py`, `money_hunter/dashboard/dashboard.py` (`_quote_loop`), `self_collect/mt5_live_collect.py`, `self_collect/demo_exec_instrument.py`.
3. MT5-python resolves a **single, non-deterministic "default" terminal** (empirically `fxtm_demo_v3`). V1's broker (no path + V1 login 160759434) therefore **bound the default terminal to V1's account** and **(re)launched** it whenever absent → `fxtm_demo_v3` = V1-account **phantom** that kept respawning.
4. Because the canonical V3 instance was unusable, an **isolated portable instance** (`fxtm_demo_v3calib`, login 160764551) was created ad hoc → the **4th** instance.

**RECURRENCE_PREVENTED** — explicit terminal paths pinned in every no-path caller (§5), and V3 repointed off the `fxtm_demo_v3` path (§5).

## 4. Isolation (read-only, measured)

```text
other_logins:  V1=160759434   V2=160761384
V3 (fxtm_demo_v3calib): login=160764551 server=ForexTimeFXTM-Demo01 balance=5000 positions=0
isolation.independent = TRUE   distinct_accounts = TRUE
```

## 5. ACTION_TAKEN / PROCESS_TERMINATION / RESTART_VALIDATION

```text
PAUSE   : \OpenClaw\v3-calibration-pilot disabled  (V3_CALIBRATION_PAUSED=TRUE)
PIN     : explicit terminal paths added in
          - research/money_hunter/dashboard/dashboard.py   (_quote_loop)
          - research/self_collect/mt5_live_collect.py
          - research/self_collect/demo_exec_instrument.py
          - research/hermes/trader_v1/broker_mt5_demo.py   (1 line)
RESTART : money_hunter dashboard restarted (read-only) to load the pinned path
STOP    : phantom fxtm_demo_v3 stopped GRACEFULLY (taskkill, no /F)
VERIFY  : held >=90s with NO respawn; running terminals = 3; each distinct account
REPOINT : V3 config + adapter -> fxtm_demo_v3calib (V3 never initialize()s fxtm_demo_v3)
NOT_DONE: fxtm_demo_v3 directory NOT deleted (kept as audit evidence)
```

## 6. V1_UNTOUCHED disclosure (honest)

V1 **strategy / config / scheduler / ledger / trading path = unchanged.**
**ONE** instance-management line was pinned in `research/hermes/trader_v1/broker_mt5_demo.py`
(`mt5.initialize(path=r"C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe", …)`).
This is **semantics-preserving** (it already targeted V1's account/terminal) and is **revertible**.
It was required because that no-path call was the root launcher/hijacker. If you prefer V1 files untouched,
say so and I will revert it — but then the phantom will respawn (isolation drops to FAIL).

## 7. Residual risk / recommended soak

Only ~150 s of observation (not a full 15-min V1-cycle window). Recommend keeping explicit paths in any new MT5 code
and a longer soak. The `fxtm_demo_v3` directory remains and is still a candidate "default" — do not `initialize()` it.

## 8. Gate

```text
TOTAL_CANONICAL_MT5_INSTANCES=3
V1_INSTANCE_COUNT=1  V2_INSTANCE_COUNT=1  V3_INSTANCE_COUNT=1
UNMAPPED_RUNNING_MT5=0  ORPHAN_RUNNING_MT5=0
V1_UNTOUCHED=TRUE(见§6)  V2_UNTOUCHED=TRUE  V3_CALIBRATION_PAUSED=TRUE
MT5_INSTANCE_ISOLATION=PASS
```

WAIT_FOR_AUDIT=TRUE. V3 Calibration remains PAUSED until you accept this audit.
