"""Test helpers: deterministic synthetic ticks/arrays (no fixtures on disk)."""
from __future__ import annotations
import numpy as np
from foundation import timeutil


def make_ticks(n=5, start_ns=None, step_ns=250_000_000, base=3300.0):
    start_ns = start_ns or timeutil.iso_to_ns("2026-09-20T00:00:00+00:00")
    out = []
    for i in range(n):
        bid = base + i * 0.01
        out.append({
            "timestamp_utc": timeutil.ns_to_iso(start_ns + i * step_ns),
            "timestamp_ns": start_ns + i * step_ns,
            "mt5_server_time": start_ns + i * step_ns,
            "local_receive_time_ns": i * step_ns,
            "symbol": "XAUUSD",
            "bid": round(bid, 2),
            "ask": round(bid + 0.2, 2),
            "mid": round(bid + 0.1, 4),
            "spread": 0.2,
            "tick_sequence": i + 1,
            "source": "test",
            "terminal_id": "test",
            "account_id": "test",
        })
    return out


def synth_arrays(n=1000, seed=7):
    rng = np.random.default_rng(seed)
    mid = 3300 + np.cumsum(rng.normal(0, 0.05, n))
    spread = 0.2 + np.abs(rng.normal(0, 0.02, n))
    bid = mid - spread / 2
    ask = mid + spread / 2
    ts = np.arange(n, dtype=np.int64) * 250_000_000 + 1_700_000_000_000_000_000
    return bid, ask, ts


def synth_arrays_with_size(n=200, seed=11):
    bid, ask, ts = synth_arrays(n, seed)
    rng = np.random.default_rng(seed)
    bv = rng.integers(1, 50, n).astype(float)
    av = rng.integers(1, 50, n).astype(float)
    return bid, ask, ts, bv, av
