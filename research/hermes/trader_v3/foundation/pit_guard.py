"""Point-in-time / leakage guards.

Ensures: no future tick/bar/label/spread/cost used as feature input;
purged+embargoed time-series split; train/test time-overlap = 0.
"""
from __future__ import annotations
import numpy as np


def assert_no_future(feature_timestamp_ns, latest_input_timestamp_ns) -> None:
    fi = np.asarray(feature_timestamp_ns)
    li = np.asarray(latest_input_timestamp_ns)
    bad = int(np.sum(li > fi))
    if bad:
        raise AssertionError(f"PIT violation: {bad} feature(s) use future input")


def purged_split(ts_ns, train_frac: float = 0.6, val_frac: float = 0.2,
                 embargo_ns: int = 0, horizon_ns: int = 0):
    """Chronological split with purge+embargo between folds (no leakage).

    Returns (train_mask, val_mask, test_mask).
    """
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    n = len(ts_ns)
    order = np.argsort(ts_ns, kind="stable")
    i_tr = int(n * train_frac)
    i_va = int(n * (train_frac + val_frac))
    gap = embargo_ns + horizon_ns
    train = np.zeros(n, bool)
    val = np.zeros(n, bool)
    test = np.zeros(n, bool)
    train[order[:max(0, i_tr)]] = True
    val[order[min(n, i_tr):max(0, i_va)]] = True
    test[order[min(n, i_va):]] = True
    # purge a gap of size gap around boundaries
    if gap > 0:
        def purge(mask, boundary_idx):
            if boundary_idx >= n:
                return
            b = ts_ns[order[boundary_idx]]
            train[np.where((ts_ns > b - gap) & (ts_ns < b + gap) & train)[0]] = False
            val[np.where((ts_ns > b - gap) & (ts_ns < b + gap) & val)[0]] = False
        purge(train, i_tr)
        purge(val, i_va)
    return train, val, test


def overlap_check(ts_train, ts_test) -> int:
    """Count samples whose [t, t+? ] time ranges overlap across folds (by exact ts)."""
    s = set(np.asarray(ts_train).tolist())
    return int(sum(1 for t in np.asarray(ts_test).tolist() if t in s))
