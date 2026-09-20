# V3 HFT Research Foundation (REPAIR-001)

Stage-1 infrastructure for an XAUUSD HFT research foundation.
**No auto trading. No live. No order_send. V1/V2 untouched.**

## Modules (`foundation/`)

| module | purpose |
|---|---|
| `timeutil` | UTC ns wall clock + monotonic perf counter |
| `tick_schema` | unified L1 tick record + validation |
| `tick_engine` | tick stream + integrity monitor (dup/ooo/regression/seq-gap/stale/spread/price) |
| `tick_recorder` | append-only, hourly-sharded, crash-safe, resumable, per-file sha256 manifest |
| `execution_calibration` | entry/exit measurement harness (gated; default DISABLED; mock mode) |
| `cost_model` | measured cost model + minimum_required_move + expected_net_edge (no assumed-as-measured) |
| `gpu_engine` | GPU feature compute (chunked, OOM-safe) + CPU fallback + CPU/GPU benchmark |
| `feature_engine` | L1 features with PIT timestamp discipline |
| `label_engine` | cost-aware labels + overlap/effective_n |
| `pit_guard` | no-future enforcement, purged/embargo split |
| `ledger` | append-only hash-chained event ledger (verify/replay) |
| `model_pipeline` | dataset→split→baseline→artifact→registry (smoke only) |
| `agent_interface` | prediction contract (AUTO_DECISION=False) |
| `entry_exit_interface` | signal interface (ORDER_SEND=False) |
| `registry` | data registry (OBSERVED/MISSING/UNKNOWN) |

Schemas: `../schemas/v3_*.json`.

## Run

```powershell
cd C:\AIQuant\research\hermes\trader_v3
C:\AIQuant\.venv\Scripts\python.exe -m foundation.tests.run_all          # 28 tests
C:\AIQuant\.venv\Scripts\python.exe -m foundation.validate_foundation    # real-data validation
```

## Safety invariants

```text
V3_AUTO_TRADING=FALSE
V3_ORDER_SEND=FALSE
V3_LIVE=FALSE
ORDER_SENT=FALSE
```
Real demo calibration orders require explicit `authorized=True` + a fixed cap and are
never driven by Hermes/model/scheduler. Every calibration order is tagged
`CALIBRATION_ORDER=true`, `MAGIC=90004`.
