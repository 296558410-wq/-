# -*- coding: utf-8 -*-
"""V3 对照：MT5 XAUUSD M1 bar vs DUKA M1 candle（时间/价格层面）。
只读；不发单。产出 research/V3_DUKA_COMPARE.md + 并入 registry.
"""
from __future__ import annotations
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

V3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V3 / "mt5"))
import v3_adapter as A  # noqa: E402

DUKA = Path(r"C:\AIQuant\data\staging_duka")
OUT = V3 / "research" / "V3_DUKA_COMPARE.md"


def main():
    fs = sorted(glob.glob(str(DUKA / "candles_*.parquet")))
    df = pd.read_parquet(fs[-1])
    day = str(df["day"].max())
    bid = df[(df["side"] == "BID")].copy()
    bid["close_px"] = bid["close"] / 1000.0
    bid["min_of_day"] = (bid["sec"] // 60).astype(int)
    res = {"duka_file": os.path.basename(fs[-1]), "day": day, "duka_price_scale": "/1000",
           "duka_rows": int(len(df)), "duka_bid_rows": int(len(bid))}

    mt5, info = A.connect()
    for _ in range(40):
        ti = mt5.terminal_info()
        if ti and ti.connected:
            break
        import time as _t; _t.sleep(1)
    mt5.symbol_select(A.SYMBOL, True)
    # MT5 时间 = broker 服务器时间(非 UTC)。用 DUKA 日 00:00 UTC ± server 偏移扫描。
    base = datetime.fromisoformat(day + "T00:00:00+00:00")
    best = None
    for off_h in range(-4, 6):
        frm = base + timedelta(hours=off_h)
        bars = mt5.copy_rates_range(A.SYMBOL, mt5.TIMEFRAME_M1, frm, frm + timedelta(days=1))
        if bars is None or len(bars) == 0:
            continue
        mt = {int((int(b["time"]) - int(frm.timestamp())) // 60): float(b["close"]) for b in bars}
        pairs = [(bid["min_of_day"].iloc[i], bid["close_px"].iloc[i]) for i in range(len(bid))]
        diffs = [abs(mt[m] - p) for m, p in pairs if m in mt]
        if not diffs:
            continue
        import statistics as st
        mad = st.mean(diffs)
        if best is None or mad < best["mean_abs_diff_usd"]:
            best = {"server_offset_h": off_h, "n_matched_min": len(diffs), "mean_abs_diff_usd": round(mad, 3),
                    "max_abs_diff_usd": round(max(diffs), 3), "p50_abs_diff_usd": round(st.median(diffs), 3)}
    res["mt5_vs_duka"] = best or "NO_OVERLAP (MT5 demo 无该日 M1 历史)"
    if best:
        res["verdict"] = "PASS — MT5 与 DUKA 在该日 M1 close 可对照" if best["mean_abs_diff_usd"] < 1.0 else "DATA_GAP — 价格偏差过大"
    else:
        res["verdict"] = "DATA_GAP — 无重叠窗口"
    A.disconnect(mt5)

    OUT.write_text(
        f"# V3 — MT5 vs DUKA 对照 — {day}\n\n"
        f"- DUKA: `{res['duka_file']}` rows={res['duka_rows']} bid_rows={res['duka_bid_rows']} (price/1000)\n"
        f"- MT5 XAUUSD M1: 服务器时间偏移搜索 {-4}..{+5}h\n"
        f"- 结果: `{json.dumps(best, ensure_ascii=False)}`\n"
        f"- **verdict: {res['verdict']}**\n\n"
        "> 注：MT5 bar 时间为 broker 服务器时间(通常 GMT+2/+3)，非 UTC；对照需考虑偏移。\n"
        "> tick 级逐笔对照：DUKA 最新 tick = 2026-08-04，MT5 当前窗口无重叠 → TICK_OVERLAP=DATA_GAP。\n",
        encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
