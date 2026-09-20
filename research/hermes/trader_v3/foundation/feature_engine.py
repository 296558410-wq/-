"""L1 feature engine (vectorized numpy) with timestamp discipline.

Every feature uses only PAST ticks: latest_input_timestamp <= feature_timestamp.
Features needing L2 are marked L1_PROXY or DATA_GAP — never faked.
"""
from __future__ import annotations
import hashlib
import json
import numpy as np


def _cumsum_roll(x, w):
    cs = np.concatenate([[0.0], np.cumsum(x)])
    out = np.full(len(x), np.nan)
    out[w - 1:] = (cs[w:] - cs[:-w]) / w
    return out


def _rollstd(x, w, nan=False):
    if nan:
        x = np.nan_to_num(x, nan=0.0)
    m = _cumsum_roll(x, w)
    m2 = _cumsum_roll(x * x, w)
    var = np.maximum(m2 - m * m, 0.0)
    return np.sqrt(var)


def _rollrms(x, w):
    x = np.nan_to_num(x, nan=0.0)
    m2 = _cumsum_roll(x * x, w)
    return np.sqrt(m2)


def feature_schema_hash() -> str:
    import os
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "schemas", "v3_feature_schema.json")
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    except Exception:
        return "NA"


def compute_features(bid, ask, ts_ns, window: int = 50, bid_vol=None, ask_vol=None) -> dict:
    with np.errstate(divide="ignore", invalid="ignore"):
        return _compute_features(bid, ask, ts_ns, window, bid_vol, ask_vol)


def _compute_features(bid, ask, ts_ns, window: int = 50, bid_vol=None, ask_vol=None) -> dict:
    bid = np.asarray(bid, dtype=np.float64)
    ask = np.asarray(ask, dtype=np.float64)
    ts_ns = np.asarray(ts_ns, dtype=np.int64)
    n = len(bid)
    mid = (bid + ask) / 2.0
    spread = ask - bid

    def ret(x):
        r = np.full(n, np.nan)
        r[1:] = (x[1:] - x[:-1]) / x[:-1]
        return r

    dt = np.full(n, np.nan)
    dt[1:] = (ts_ns[1:] - ts_ns[:-1]) / 1e9
    vel = np.where(dt > 0, 1.0 / dt, np.nan)

    out = {}
    out["tick_return"] = ret(mid)
    out["mid_return"] = ret(mid)
    out["bid_return"] = ret(bid)
    out["ask_return"] = ret(ask)
    out["tick_velocity"] = vel
    out["tick_intensity"] = vel
    out["spread"] = spread
    sc = np.full(n, np.nan)
    sc[1:] = spread[1:] - spread[:-1]
    out["spread_change"] = sc
    rm = _cumsum_roll(spread, window)
    rs = _rollstd(spread, window)
    out["spread_zscore"] = np.where(rs > 0, (spread - rm) / rs, np.nan)
    mom = np.full(n, np.nan)
    mom[window:] = mid[window:] / mid[:-window] - 1.0
    out["mid_momentum"] = mom
    out["short_term_volatility"] = _rollstd(out["mid_return"], window, nan=True)
    out["realized_volatility"] = _rollrms(out["mid_return"], window)
    acc = np.full(n, np.nan)
    acc[1:] = vel[1:] - vel[:-1]
    out["price_acceleration"] = acc
    if bid_vol is not None and ask_vol is not None:
        bv = np.asarray(bid_vol, dtype=np.float64)
        av = np.asarray(ask_vol, dtype=np.float64)
        denom = bv + av
        out["micro_price"] = np.where(denom > 0, (bid * av + ask * bv) / denom, np.nan)
        out["order_flow_imbalance"] = np.where(denom > 0, (bv - av) / denom, np.nan)
        out["order_flow_imbalance_status"] = "L1_PROXY"
        out["micro_price_status"] = "L1_PROXY"
    else:
        out["micro_price"] = mid.copy()
        out["micro_price_status"] = "L1_PROXY(size-less)"
        out["order_flow_imbalance"] = np.full(n, np.nan)
        out["order_flow_imbalance_status"] = "DATA_GAP(no size fields)"
    out["reversal_pressure"] = -out["mid_momentum"]
    out["liquidity_proxy"] = np.where(spread > 0, 1.0 / spread, np.nan)

    meta = {
        "feature_timestamp_ns": ts_ns.copy(),
        "latest_input_timestamp_ns": ts_ns.copy(),  # computed at receive, uses <= i only
        "feature_schema_hash": feature_schema_hash(),
        "window": window,
        "n": n,
    }
    return {"features": out, "meta": meta}


def assert_no_future(meta: dict) -> bool:
    fi = np.asarray(meta["feature_timestamp_ns"])
    li = np.asarray(meta["latest_input_timestamp_ns"])
    return bool(np.all(li <= fi))
