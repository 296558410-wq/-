# -*- coding: utf-8 -*-
"""V2 Data Source Router — 本地 XAUUSD K 线（tick/mid → 5m/15m/60m/4h/1d，确定性 + PIT）。

- 数据源：C:\\AIQuant\\data\\live_fxtm\\ticks_*.parquet（bid/ask tick，本地 MT5 采集）。
- mid = (bid+ask)/2；bar 由 mid 确定性重采样（label=left, closed=left）。
- PIT：剔除“结束时刻 > now”的最后一根 bar（防未来数据）。
- 不下载重复数据（优先用现有本地 tick）。
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]            # .../trader_v2
AIQ = ROOT.parents[2]                                  # C:\AIQuant
LIVE = AIQ / "data" / "live_fxtm"

TF_SECONDS = {"5m": 300, "15m": 900, "60m": 3600, "4h": 14400, "1d": 86400}
_PANDAS_RULE = {"5m": "5min", "15m": "15min", "60m": "60min", "4h": "4h", "1d": "1D"}


def _load_mid(days: int = 8) -> pd.DataFrame:
    files = sorted(LIVE.glob("ticks_*.parquet"))[-days:]
    frames = []
    for f in files:
        try:
            d = pd.read_parquet(f, columns=["ts_utc", "bid", "ask"])
        except Exception:  # noqa: BLE001
            continue
        frames.append(d)
    if not frames:
        return pd.DataFrame(columns=["mid"]).set_index(pd.DatetimeIndex([], tz="UTC"))
    df = pd.concat(frames, ignore_index=True)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.dropna(subset=["bid", "ask"])
    df["mid"] = (df["bid"].astype(float) + df["ask"].astype(float)) / 2.0
    df = df.drop_duplicates(subset=["ts_utc"]).set_index("ts_utc").sort_index()
    return df[["mid"]]


def _resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = df["mid"].resample(rule, label="left", closed="left")
    bar = pd.DataFrame({"o": g.first(), "h": g.max(), "l": g.min(), "c": g.last()}).dropna()
    return bar


def build_bars(tf: str, now=None, days: int = 8) -> dict:
    """确定性生成本地 K 线。返回与 market_data.fetch_history 相同 schema 的 dict。"""
    now_ts = (now or datetime.now(timezone.utc)).timestamp()
    if tf not in TF_SECONDS:
        raise ValueError(f"unsupported tf: {tf}")
    df = _load_mid(days=days)
    if df.empty:
        return {"tf": tf, "symbol": "XAUUSD", "source": "local_fxtm", "bars": [], "n": 0,
                "retrieval_ts": datetime.now(timezone.utc).isoformat(), "last_bar_ts": None,
                "error": "no_local_ticks"}
    bar = _resample(df, _PANDAS_RULE[tf])
    bars = []
    for t, r in bar.iterrows():
        sec = int(t.timestamp())
        if sec + TF_SECONDS[tf] > now_ts:      # PIT：未收盘剔除
            continue
        bars.append({"t": sec, "o": round(float(r["o"]), 2), "h": round(float(r["h"]), 2),
                     "l": round(float(r["l"]), 2), "c": round(float(r["c"]), 2), "v": 0.0})
    return {"tf": tf, "symbol": "XAUUSD", "source": "local_fxtm", "interval": tf,
            "range": f"{days}d_ticks", "bars": bars, "n": len(bars),
            "retrieval_ts": datetime.now(timezone.utc).isoformat(),
            "last_bar_ts": bars[-1]["t"] if bars else None}


def local_quote() -> dict:
    """本地最新 mid 报价（来自 tick 末值；无网络）。"""
    df = _load_mid(days=2)
    if df.empty:
        return {"price": None, "source": "local_fxtm"}
    last_ts = df.index[-1]
    return {"price": round(float(df["mid"].iloc[-1]), 2), "bid": None, "ask": None,
            "spread": None, "data_ts": last_ts.isoformat(), "source": "local_fxtm",
            "retrieval_ts": datetime.now(timezone.utc).isoformat()}
