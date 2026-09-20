"""Cost-aware label engine + overlap / effective_n.

net labels require MEASURED costs; otherwise NET_LABEL_STATUS=DATA_GAP.
"""
from __future__ import annotations
import math
import numpy as np


def label_schema_hash() -> str:
    import hashlib
    import os
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "schemas", "v3_label_schema.json")
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    except Exception:
        return "NA"


def future_returns(mid, ts_ns, horizon_ms: int) -> dict:
    mid = np.asarray(mid, dtype=np.float64)
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    h_ns = horizon_ms * 1_000_000
    n = len(mid)
    fwd = np.full(n, np.nan)
    j = 0
    for i in range(n):
        target = ts_ns[i] + h_ns
        if j < i + 1:
            j = i + 1
        while j < n and ts_ns[j] < target:
            j += 1
        if j < n:
            fwd[i] = mid[j] / mid[i] - 1.0
    return fwd


def label(mid, ts_ns, horizon_ms: int, round_trip_cost_bp: float | None = None) -> dict:
    fwd = future_returns(mid, ts_ns, horizon_ms)
    out = {
        "horizon_ms": horizon_ms,
        "gross_future_return": fwd,
        "label_schema_hash": label_schema_hash(),
    }
    if round_trip_cost_bp is None:
        out["net_future_return"] = None
        out["NET_LABEL_STATUS"] = "DATA_GAP"
    else:
        out["net_future_return"] = fwd - (round_trip_cost_bp / 1e4)
        out["cost_bp_applied"] = round_trip_cost_bp
        out["NET_LABEL_STATUS"] = "OK(cost-aware)"
    return out


def overlap_stats(ts_ns, horizon_ms: int) -> dict:
    """sample_interval vs horizon -> overlap_ratio; effective_n = non-overlapping upper bound."""
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    if len(ts_ns) < 2:
        return {"sample_interval_median_ns": None, "overlap_ratio": None, "effective_n": 0}
    d = np.diff(ts_ns)
    d = d[d > 0]
    si = float(np.median(d)) if len(d) else None
    h = horizon_ms * 1_000_000
    if not si:
        return {"sample_interval_median_ns": None, "overlap_ratio": None, "effective_n": 0}
    ratio = h / si
    eff = math.floor(len(ts_ns) / max(ratio, 1.0))
    return {
        "label_horizon_ms": horizon_ms,
        "sample_interval_median_ns": si,
        "overlap_ratio": ratio,
        "effective_n": int(eff),
        "note": "overlapping samples are NOT independent; effective_n is an upper bound",
    }
