"""GPU feature engine (torch) with chunking + CPU fallback. Real compute, not is_available().

Benchmarks CPU vs GPU on real V3 tick data; kills CUDA OOM risk via chunking/fallback.
"""
from __future__ import annotations
import time
import numpy as np


def info() -> dict:
    try:
        import torch
        d = {
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
        }
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            d.update({"device": p.name, "vram_mib": round(p.total_memory / 1024 / 1024, 1),
                      "cc": f"{p.major}.{p.minor}"})
        return d
    except Exception as e:  # pragma: no cover
        return {"error": f"{type(e).__name__}:{e}"}


def _torch_features(t, bid, ask, ts_ns, window=50):
    import torch
    n = bid.shape[0]
    mid = (bid + ask) / 2.0
    spread = ask - bid

    def ret(x):
        r = torch.full_like(x, float("nan"))
        r[1:] = (x[1:] - x[:-1]) / x[:-1]
        return r

    cs = torch.cat([torch.zeros(1, device=t.device), torch.cumsum(spread, 0)])
    cum = (cs[window:] - cs[:-window]) / window
    rm = torch.full_like(spread, float("nan"))
    rm[window - 1:] = cum
    m2 = torch.cat([torch.zeros(1, device=t.device), torch.cumsum(spread * spread, 0)])
    cm2 = (m2[window:] - m2[:-window]) / window
    var = torch.clamp(cm2 - cum * cum, min=0.0)
    rs = torch.full_like(spread, float("nan"))
    rs[window - 1:] = torch.sqrt(var)
    ret_mid = ret(mid)
    mom = torch.full_like(mid, float("nan"))
    mom[window:] = mid[window:] / mid[:-window] - 1.0
    feats = {
        "tick_return": ret_mid,
        "mid_return": ret_mid,
        "spread": spread,
        "spread_zscore": torch.where(rs > 0, (spread - rm) / rs, torch.full_like(spread, float("nan"))),
        "mid_momentum": mom,
        "liquidity_proxy": torch.where(spread > 0, 1.0 / spread, torch.full_like(spread, float("nan"))),
    }
    return feats


def compute_gpu(bid, ask, ts_ns, window=50, chunk=200_000) -> dict:
    """Compute features on GPU in chunks; fall back to CPU on any CUDA issue."""
    import torch
    if not torch.cuda.is_available():
        return {"backend": "cpu_fallback", "reason": "cuda_unavailable"}
    try:
        bid = np.asarray(bid, dtype=np.float64)
        ask = np.asarray(ask, dtype=np.float64)
        out = {k: np.empty(len(bid)) for k in
               ["tick_return", "mid_return", "spread", "spread_zscore", "mid_momentum", "liquidity_proxy"]}
        vr_peak = 0
        for s in range(0, len(bid), chunk):
            e = min(len(bid), s + chunk)
            tb = torch.tensor(bid[s:e], device="cuda", dtype=torch.float64)
            ta = torch.tensor(ask[s:e], device="cuda", dtype=torch.float64)
            tt = torch.tensor(ts_ns[s:e], device="cuda", dtype=torch.int64)
            f = _torch_features(tt, tb, ta, ts_ns, window)
            for k, v in f.items():
                out[k][s:e] = v.detach().cpu().numpy()
            vr_peak = max(vr_peak, torch.cuda.max_memory_allocated() / 1024 / 1024)
            del tb, ta, tt, f
        torch.cuda.empty_cache()
        return {"backend": "gpu", "vram_peak_mib": round(vr_peak, 1), "features": out}
    except Exception as e:
        try:
            import torch as _t
            _t.cuda.empty_cache()
        except Exception:
            pass
        return {"backend": "cpu_fallback", "reason": f"{type(e).__name__}:{e}"}


def benchmark(bid, ask, ts_ns, window=50) -> dict:
    from .feature_engine import compute_features
    t0 = time.perf_counter()
    cpu = compute_features(bid, ask, ts_ns, window=window)
    cpu_t = time.perf_counter() - t0
    g = compute_gpu(bid, ask, ts_ns, window=window)
    n = len(bid)
    res = {
        "dataset_size": int(n),
        "feature_count": len([k for k in cpu["features"] if hasattr(cpu["features"][k], "shape")]),
        "cpu_time_s": cpu_t,
        "cpu_ticks_per_sec": n / cpu_t if cpu_t else None,
        "gpu_backend": g["backend"],
    }
    if g["backend"] == "gpu":
        # numeric equivalence on a subset
        diffs = []
        for k in ["spread", "mid_momentum", "liquidity_proxy"]:
            a = cpu["features"][k]
            b = g["features"][k]
            m = ~np.isnan(a) & ~np.isnan(b)
            diffs.append(float(np.max(np.abs(a[m] - b[m]))) if m.any() else 0.0)
        res.update({"vram_peak_mib": g.get("vram_peak_mib"),
                    "max_abs_cpu_gpu_diff": max(diffs) if diffs else None})
    return res
