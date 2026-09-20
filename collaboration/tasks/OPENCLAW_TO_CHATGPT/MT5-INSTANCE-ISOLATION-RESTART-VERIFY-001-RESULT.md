# CHATGPT-TASK-MT5-INSTANCE-ISOLATION-RESTART-VERIFY-001-RESULT

```text
TASK_ID = MT5-INSTANCE-ISOLATION-RESTART-VERIFY-001
STATUS  = PASS
MT5_INSTANCE_ISOLATION_RESTART_VERIFY = PASS

TOTAL_RUNNING_MT5 = 3
UNMAPPED_RUNNING_MT5 = 0
ORPHAN_RUNNING_MT5 = 0

V3_CALIBRATION_PAUSED = TRUE ("\OpenClaw\v3-calibration-pilot" = Disabled)
ORDER_SENT = FALSE
V1_UNTOUCHED = TRUE (strategy/config/scheduler/ledger; see prior 1-line instance pin)
V2_UNTOUCHED = TRUE
```

## Purpose
Verify the fix from `MT5-INSTANCE-ISOLATION-AUDIT-FIX-001` (pin explicit terminal paths, retire the
`fxtm_demo_v3` phantom) **holds across restarts** of the components/terminals that previously
auto-launched / hijacked the default terminal.

## Restart test matrix (all measured)

| # | Test (restart / trigger) | expectation | result |
|---|---|---|---|
| R0 | Baseline | 3 terminals | 3 (1348 V1, 36460 V2, 45404 V3calib) — PASS |
| R1 | Run `hermes-tick-collect` (fresh process, pinned path) | no phantom | `COLLECTED new=94`; phantom=0 — PASS |
| R2 | Restart money_hunter dashboard (pinned `_quote_loop`) | no phantom | 8787 up; phantom=0 — PASS |
| R3 | Invoke V1 broker path `broker_mt5_demo.get_positions()` | no phantom / targets V1 | `positions_ok=True n=1`; phantom=0 — PASS |
| R4 | Graceful stop + explicit relaunch V3 terminal | returns on 160764551 | stop → 2 terminals (nothing auto-started); relaunch → V3 back login=160764551 — PASS |
| R5 | 50 s soak | no respawn | 3 terminals; phantom=0 — PASS |

## Account assertion (read-only, explicit paths)

```text
V1 = 160759434  (C:\Program Files\ForexTime (FXTM) MT5)
V2 = 160761384  (mt5_instances\fxtm_demo_01, /portable)
V3 = 160764551  (mt5_instances\fxtm_demo_v3calib, /portable)
distinct_accounts = TRUE
fxtm_demo_v3 phantom = ABSENT (count 0)
```

## Key result
After restarting the collector, the dashboard, the V1 broker usage, and the V3 terminal, the
`fxtm_demo_v3` phantom **did not reappear** and the project stayed at exactly **3 isolated instances**.
The isolation survived the restarts it was designed to survive.

## Residual / caveat
- The longest continuous observation was R5 (50 s) plus the earlier 150 s; a **full 15-min V1/V2 cycle
  window was not awaited**. However, R1/R3 exercised the exact cycle code paths (collector + V1 broker)
  in fresh processes and produced no phantom.
- Always pass explicit `path=` to `mt5.initialize()` in any new code (no-path default is non-deterministic).
- `C:\AIQuant\mt5_instances\fxtm_demo_v3` directory retained (evidence); do not `initialize()` it.
