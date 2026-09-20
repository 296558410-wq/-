"""V3 HFT Research Foundation (REPAIR-001).

Read-only-safe engineering layer for XAUUSD HFT research.
Stage 1: build infrastructure only. NO auto trading, NO live, NO order_send.

Modules
-------
timeutil            high-precision clocks
tick_schema         unified tick record + validation
tick_engine         tick stream + integrity monitor
tick_recorder       append-only, sharded, crash-safe tick storage
execution_calibration  entry/exit measurement harness (gated; default OFF)
cost_model          measured cost model + minimum_required_move
gpu_engine          GPU feature compute (chunked) + CPU fallback + benchmark
feature_engine      L1 features with timestamp discipline
label_engine        cost-aware labels + overlap/effective_n
pit_guard           point-in-time / leakage guards
ledger              append-only hash-chained event ledger
model_pipeline      dataset -> train/val/test -> artifact -> registry (smoke)
agent_interface     prediction contract (AUTO_DECISION=False)
entry_exit_interface signal interface (ORDER_SEND=False)
registry            data registry (OBSERVED/MISSING/UNKNOWN)
"""
__version__ = "v3-hft-foundation/0.1.0"

SAFETY = {
    "V3_AUTO_TRADING": False,
    "V3_ORDER_SEND": False,
    "V3_LIVE": False,
    "ORDER_SENT": False,
}
