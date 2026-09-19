# -*- coding: utf-8 -*-
"""V2 行情源 — 走 V2 独立 MT5 实例（fxtm_demo_01，只读；不碰 V1）。

提供 XAUUSD/XAGUSD 等 broker 符号的 quote 与 history。无外部网络。
PIT: 剔除未收盘 bar。连接复用（进程内单例）。
"""
from __future__ import annotations
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "execution"))
import fxtm_demo_adapter as FA  # noqa: E402

_TF_SEC = {"5m": 300, "15m": 900, "60m": 3600, "4h": 14400, "1d": 86400}
_TF_COUNT = {"5m": 2000, "15m": 900, "60m": 400, "4h": 150, "1d": 90}
_A = None


def _adapter():
    global _A
    if _A is None:
        _A = FA.FXTMDemoAdapter()
        _A.connect_readonly()   # P0-06(2026-09-18): 行情只读，与 BROKER_DEMO 武装解耦
    return _A


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def available(symbol):
    try:
        m = _adapter()._mt5
        return m.symbol_info(symbol) is not None
    except Exception:  # noqa: BLE001
        return False


def quote(symbol="XAUUSD"):
    m = _adapter()._mt5
    m.symbol_select(symbol, True)
    t = m.symbol_info_tick(symbol)
    if t is None:
        raise RuntimeError(f"mt5 no tick: {symbol}")
    mid = (float(t.bid) + float(t.ask)) / 2.0
    return {"price": round(mid, 2), "bid": float(t.bid), "ask": float(t.ask),
            "spread": round(float(t.ask) - float(t.bid), 3),
            "data_ts": int(t.time), "source": "mt5", "symbol": symbol, "retrieval_ts": _now_iso()}


def history(tf, symbol="XAUUSD"):
    if tf not in _TF_SEC:
        raise ValueError(f"unsupported tf: {tf}")
    m = _adapter()._mt5
    m.symbol_select(symbol, True)
    tfmap = {"5m": m.TIMEFRAME_M5, "15m": m.TIMEFRAME_M15, "60m": m.TIMEFRAME_H1,
             "4h": m.TIMEFRAME_H4, "1d": m.TIMEFRAME_D1}
    r = m.copy_rates_from_pos(symbol, tfmap[tf], 0, _TF_COUNT[tf])
    if r is None or len(r) == 0:
        raise RuntimeError(f"mt5 no rates: {symbol} {tf}")
    now = time.time()
    bars = []
    for x in r:
        t = int(x["time"])
        if t + _TF_SEC[tf] > now:      # PIT: 未收盘剔除
            continue
        bars.append({"t": t, "o": float(x["open"]), "h": float(x["high"]),
                     "l": float(x["low"]), "c": float(x["close"]), "v": float(x["tick_volume"])})
    return {"tf": tf, "symbol": symbol, "source": "mt5", "interval": tf, "bars": bars, "n": len(bars),
            "retrieval_ts": _now_iso(), "last_bar_ts": bars[-1]["t"] if bars else None}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("XAUUSD quote:", quote("XAUUSD"))
    h = history("15m", "XAUUSD")
    print("XAUUSD 15m n=", h["n"], "last=", h["bars"][-1] if h["bars"] else None)
    print("XAGUSD available:", available("XAGUSD"))
