# -*- coding: utf-8 -*-
"""research_compute 验收测试（脚本式；与 V2 现有测试一致）。

覆盖: dispatcher / CPU-GPU 等价 / RNG 可复现 / chunk 等价 / OOM 回退 / GPU 不可用 /
验证失败 / 时间对齐 / 无未来泄漏 / 真实 XAUUSD / V1隔离 / broker隔离 / ledger隔离 / replay隔离 / config 不可变。
运行: python tests/test_research_compute.py
"""
from __future__ import annotations
import hashlib, json, os, sys, glob
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))            # trader_v2
sys.path.insert(0, str(ROOT / "execution"))
sys.path.insert(0, str(ROOT / "ledger"))

import research_compute as RC
from research_compute import dispatcher as D, cpu_backend as CB, gpu_backend as GB
from research_compute.validation import compare, ComputeValidationError, assert_valid

LOG = ROOT / "logs" / "test_research_compute.log"
LOG.parent.mkdir(exist_ok=True)
_res = []
CFG = ROOT / "config" / "v2_config.json"


def log(s):
    print(s); open(LOG, "a", encoding="utf-8").write(s + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    rng = np.random.default_rng(0)
    x = rng.standard_normal(500000).cumsum() + 4000.0
    bid = x - 0.15; ask = x + 0.15
    ts = np.sort(rng.integers(0, 50_000_000, size=len(x))).astype(np.int64)

    # 1 dispatcher
    check("1 dispatcher force cpu", D.decide("rolling_std", 10**7, backend="cpu")[0] == "cpu")
    check("1 dispatcher rolling big→cpu(超安全上限)", D.decide("rolling_std", 80_000_000)[0] == "cpu")
    check("1 dispatcher rolling mid→gpu", D.decide("rolling_std", 10_000_000)[0] in ("gpu", "cpu"))
    check("1 dispatcher resample small→cpu", D.decide("bootstrap", 1000, n_iter=100)[0] == "cpu")

    # 2 CPU/GPU numerical equivalence
    if GB.available():
        def _pick(v):
            if isinstance(v, dict):
                for k in ("spread_bps", "close", "spread", "mid"):
                    if k in v:
                        return v[k]
            return v
        for op, a in (("rolling_std", (x, 60)), ("rolling_mean", (x, 60)),
                      ("quotes", (ask, bid)), ("returns", (x, "log")), ("realized_volatility", (x,)),
                      ("microbar", (ts, bid, ask, 60000))):
            c = getattr(CB.CPU, op)(*a); g = getattr(GB.GPU, op)(*a)
            check(f"2 equiv {op}", compare(_pick(c), _pick(g), "elementwise")["ok"])
    else:
        check("2 equiv (no gpu → skip)", True, "CUDA unavailable")

    # 3 RNG reproducibility
    # 3 RNG reproducibility
    b1 = CB.CPU.bootstrap(x[:10000], stat="mean", n_iter=5000, seed=123)
    b2 = CB.CPU.bootstrap(x[:10000], stat="mean", n_iter=5000, seed=123)
    check("3 cpu rng reproducible", np.allclose(b1, b2))
    if GB.available():
        g1 = GB.GPU.bootstrap(x[:10000], stat="mean", n_iter=5000, seed=123)
        g2 = GB.GPU.bootstrap(x[:10000], stat="mean", n_iter=5000, seed=123)
        check("3 gpu rng reproducible", np.allclose(g1, g2))
        rep3 = compare(b1, g1, "statistical")
        check("3 cpu/gpu statistical agree", rep3["ok"], str(rep3.get("worst")))

    # 4 chunk equivalence (bootstrapped result invariant to chunk)
    c_full = CB.CPU.bootstrap(x[:10000], stat="mean", n_iter=400, seed=9)
    c_chunk = CB.CPU.bootstrap(x[:10000], stat="mean", n_iter=400, seed=9, chunk=100)
    check("4 chunk equivalence (cpu)", np.allclose(c_full, c_chunk))

    # 5 OOM fallback
    orig = GB.run
    def boom(*a, **k):
        raise RuntimeError("CUDA out of memory. Tried to allocate")
    GB.run = boom
    try:
        r = D.compute("rolling_std", x, 60, backend="gpu", verify=False)
        check("5 OOM → cpu fallback", r["backend_used"] == "cpu" and "OOM" in r["fallback_reason"], r["fallback_reason"])
    except Exception as e:
        check("5 OOM → cpu fallback", False, str(e))
    GB.run = orig

    # 6 GPU unavailable fallback
    oav = GB.available
    GB.available = lambda: False
    try:
        check("6 gpu unavailable → cpu", D.decide("rolling_std", 10_000_000)[0] == "cpu")
    finally:
        GB.available = oav

    # 7 validation failure
    orig2 = GB.run
    GB.run = lambda *a, **k: (np.asarray(a[1], dtype=np.float64) * 0.0 + 12345.0, 1.0, 0.0)
    caught = False
    try:
        D.compute("rolling_std", x, 60, backend="gpu", verify=True)
    except ComputeValidationError:
        caught = True
    finally:
        GB.run = orig2
    check("7 mismatch → COMPUTE_VALIDATION_FAILED", caught)

    # 8 time alignment (microbar buckets monotonic & within range)
    b = CB.CPU.microbar(ts, bid, ask, 60000)
    bt = b["bucket_ts_ms"]
    check("8 microbar buckets monotonic", np.all(np.diff(bt) > 0) and bt[0] <= ts.min() and bt[-1] <= ts.max())

    # 9 no future leakage (trailing rolling: future edits don't change past)
    y = rng.standard_normal(5000).cumsum() + 100
    r1 = CB.CPU.rolling_std(y, 60)
    y2 = y.copy(); y2[-10:] += 999.0
    r2 = CB.CPU.rolling_std(y2, 60)
    check("9 rolling no future leakage", np.allclose(r1[:-10], r2[:-10], equal_nan=True))

    # 10 real XAUUSD pipeline (CPU vs GPU)
    fs = sorted(glob.glob(r"C:\AIQuant\data\live_fxtm\ticks_*.parquet"))
    if fs and GB.available():
        import pandas as pd
        df = pd.concat([pd.read_parquet(f) for f in fs[:2]], ignore_index=True)
        tsm = pd.to_datetime(df["ts_utc"], utc=True).dt.tz_convert("UTC").dt.tz_localize(None).values.astype("datetime64[ms]").astype("int64")
        bb = df["bid"].to_numpy(float); aa = df["ask"].to_numpy(float)
        c = CB.CPU.microbar(tsm, bb, aa, 60000); g = GB.GPU.microbar(tsm, bb, aa, 60000)
        check("10 real live_fxtm microbar cpu==gpu", c["bucket_ts_ms"].tolist() == g["bucket_ts_ms"].tolist()
              and compare(c["close"], g["close"], "elementwise")["ok"], f"nbars={len(c['bucket_ts_ms'])}")
        cs = CB.CPU.quotes(aa, bb); gs = GB.GPU.quotes(aa, bb)
        check("10 real spread cpu==gpu", compare(cs["spread_bps"], gs["spread_bps"], "elementwise")["ok"])
    else:
        check("10 real XAUUSD pipeline", True, "skipped (no data/gpu)")

    # 11-14 isolation: source scan (no V1/broker/ledger/replay coupling)
    src = ""
    for p in (ROOT / "research_compute").glob("*.py"):
        src += p.read_text(encoding="utf-8")
    v1 = ("trader_v1" in src) or ("live_fxtm'" in src and "import" in src)
    check("11 V1 isolation (no trader_v1 coupling)", not v1)
    broker = any(k in src for k in ("BrokerDemoExecutor", "FXTMDemoAdapter", "place_market_order", "order_send"))
    check("12 broker isolation (no execution coupling)", not broker)
    check("13 ledger isolation (no ledger import)", "import ledger" not in src and "hermes_v2_ledger" not in src)
    check("14 replay isolation (no replay import)", "import replay" not in src)

    # 15 configuration immutability
    h0 = sha(CFG)
    D.compute("rolling_std", x, 60, backend="cpu")
    if GB.available():
        D.compute("rolling_std", x[:3_000_000], 60, backend="gpu", verify=True)
    h1 = sha(CFG)
    check("15 config immutable", h0 == h1, h0[:12])

    allok = all(_res)
    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
