# -*- coding: utf-8 -*-
"""V2 行情层 —— 中国大陆直连多源报价 + 单源历史 K 线（point-in-time）。

设计铁律:
- **历史序列单源**: 每个周期的 OHLC 序列只来自一个源(Yahoo chart), 不跨源拼接。
- **现价多源回退**: 新浪 → 腾讯 → 东财 → Yahoo, 仅作“当前报价”(带源名/时间戳)。
- **point-in-time**: 每个数据点带 retrieval_ts(取回时刻) 与 data_ts(行情自身时刻);
  剔除“未收盘”的最后一根 bar(其结束时刻 > now)。
- 返回结构统一, 供 Agent1 特征计算。
"""
from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests, sys as _sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in _sys.path:
    _sys.path.insert(0, str(ROOT))


def _router():
    """V2 Data Source Router（显式开关；默认关闭 → 走本文件 legacy 路径）。"""
    try:
        import data_sources as _d
        return _d if _d.router_enabled() else None
    except Exception:  # noqa: BLE001
        return None


def last_history_source(symbol, tf="15m"):
    """P0-01: 返回 router 上次为 hist:<symbol>:<tf> 实际选中的 source（供 Agent1 诚实标注）。"""
    _d = _router()
    if _d is None:
        return None
    try:
        rec = (_d.last_selected() or {}).get(f"hist:{symbol}:{tf}")
        return (rec or {}).get("source")
    except Exception:  # noqa: BLE001
        return None


UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
SINA_H = dict(UA); SINA_H["Referer"] = "https://finance.sina.com.cn"
CACHE = ROOT / "data_cache"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url, headers=UA, timeout=12, params=None):
    r = requests.get(url, headers=headers, timeout=timeout, params=params)
    r.raise_for_status()
    return r


# ---------------- 现价（多源回退） ----------------
def quote_sina(sina_code: str):
    r = _get(f"https://hq.sinajs.cn/list={sina_code}", SINA_H)
    txt = r.text.split('"')[1] if '"' in r.text else ""
    if not txt:
        raise ValueError("sina empty")
    f = txt.split(",")
    last = float(f[0])
    # 新浪 hf_ 报价: [0]=最新, [3]≈卖价 → spread
    ask = float(f[3]) if len(f) > 3 and f[3] else last
    bid = float(f[2]) if len(f) > 2 and f[2] else last
    return {"price": last, "bid": bid, "ask": ask, "spread": round(ask - bid, 3),
            "data_ts": f[6] if len(f) > 6 else None, "source": "sina"}


def quote_tencent(tx_code: str):
    r = _get(f"https://qt.gtimg.cn/q={tx_code}")
    txt = r.text.split('"')[1] if '"' in r.text else ""
    if not txt:
        raise ValueError("tencent empty")
    f = txt.split(",")
    last = float(f[0]); bid = float(f[2]) if f[2] else last; ask = float(f[3]) if f[3] else last
    return {"price": last, "bid": bid, "ask": ask, "spread": round(ask - bid, 3),
            "data_ts": f[6] if len(f) > 6 else None, "source": "tencent"}


def quote_eastmoney(secid: str):
    r = _get(f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f58,f57,f170")
    j = r.json().get("data")
    if not j:
        raise ValueError("eastmoney null")
    price = j["f43"] / 100.0  # f43 为分/百分位
    return {"price": price, "bid": None, "ask": None, "spread": None,
            "data_ts": None, "source": "eastmoney", "name": j.get("f58")}


def quote_yahoo(symbol: str):
    j = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
             params={"range": "1d", "interval": "5m"}).json()
    m = j["chart"]["result"][0]["meta"]
    price = m.get("regularMarketPrice")
    return {"price": price, "bid": None, "ask": None, "spread": None,
            "data_ts": m.get("regularMarketTime"), "source": "yahoo"}


# 现价源优先级(按用途): 现货金/白银用国内; 指数/美债用 yahoo 回退
QUOTE_ROUTES = {
    "gold_spot": [("sina", "hf_XAU"), ("tencent", "hf_XAU")],
    "gold_comex": [("sina", "hf_GC"), ("tencent", "hf_GC")],
    "silver": [("sina", "hf_SI"), ("tencent", "hf_SI")],
    "dxy": [("eastmoney", "100.UDI"), ("yahoo", "DX-Y.NYB")],
    "ust10y": [("yahoo", "^TNX")],
    "vix": [("yahoo", "^VIX")],
    "gld": [("tencent", "usGLD"), ("yahoo", "GLD")],
}


def fetch_quote(key: str) -> dict:
    _d = _router()
    if _d is not None:
        return _d.quote(key)
    errs = []
    for src, code in QUOTE_ROUTES[key]:
        try:
            if src == "sina":
                q = quote_sina(code)
            elif src == "tencent":
                q = quote_tencent(code)
            elif src == "eastmoney":
                q = quote_eastmoney(code)
            elif src == "yahoo":
                q = quote_yahoo(code)
            else:
                continue
            q["key"] = key; q["retrieval_ts"] = _now_iso(); q["code"] = code
            return q
        except Exception as e:  # noqa: BLE001
            errs.append(f"{src}:{type(e).__name__}")
    return {"key": key, "price": None, "retrieval_ts": _now_iso(), "source": None,
            "errors": errs}


# ---------------- 历史 K 线（单源 Yahoo chart） ----------------
YF_INTERVAL = {"5m": ("5m", "5d"), "15m": ("15m", "5d"), "60m": ("60m", "1mo"), "1d": ("1d", "3mo")}
_TF_SECONDS = {"5m": 300, "15m": 900, "60m": 3600, "1d": 86400}


def fetch_history(symbol: str, tf: str) -> dict:
    """单源历史 OHLC(Yahoo chart)。剔除未收盘最后一根。返回 {tf,bars:[{t,o,h,l,c,v}],source,retrieval_ts}。"""
    _d = _router()
    if _d is not None:
        return _d.history(symbol, tf)
    interval, rng = YF_INTERVAL[tf]
    j = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
             params={"range": rng, "interval": interval}).json()
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    o, h, l, c, v = q.get("open"), q.get("high"), q.get("low"), q.get("close"), q.get("volume")
    bars = []
    for i in range(len(ts)):
        if None in (o[i], h[i], l[i], c[i]):
            continue
        bars.append({"t": int(ts[i]), "o": float(o[i]), "h": float(h[i]),
                     "l": float(l[i]), "c": float(c[i]), "v": float(v[i] or 0)})
    now = time.time()
    if bars and bars[-1]["t"] + _TF_SECONDS[tf] > now:  # 未收盘 → 剔除(look-ahead 防护)
        bars = bars[:-1]
    return {"tf": tf, "symbol": symbol, "source": "yahoo", "interval": interval,
            "range": rng, "bars": bars, "n": len(bars), "retrieval_ts": _now_iso(),
            "last_bar_ts": bars[-1]["t"] if bars else None}


def resample_bars(bars: list, factor: int) -> list:
    """把 bars 每 factor 根合并(用于 4h = 4×1h, 单源派生)。"""
    out = []
    for i in range(0, len(bars) - len(bars) % factor, factor):
        grp = bars[i:i + factor]
        out.append({"t": grp[0]["t"], "o": grp[0]["o"], "h": max(x["h"] for x in grp),
                    "l": min(x["l"] for x in grp), "c": grp[-1]["c"],
                    "v": sum(x["v"] for x in grp)})
    return out


def snapshot_history(symbol: str) -> dict:
    """采集 5m/15m/60m/1d(单源 Yahoo), 4h 由 60m 派生。"""
    _d = _router()
    if _d is not None:
        return {tf: _d.history(symbol, tf) for tf in ("5m", "15m", "60m", "4h", "1d")}
    out = {}
    for tf in ("5m", "15m", "60m", "1d"):
        try:
            out[tf] = fetch_history(symbol, tf)
        except Exception as e:  # noqa: BLE001
            out[tf] = {"tf": tf, "symbol": symbol, "bars": [], "n": 0,
                       "error": f"{type(e).__name__}:{e}", "retrieval_ts": _now_iso()}
    b60 = out.get("60m", {}).get("bars", [])
    out["4h"] = {"tf": "4h", "symbol": symbol, "source": "yahoo(derived from 60m)",
                 "bars": resample_bars(b60, 4), "retrieval_ts": _now_iso()}
    out["4h"]["n"] = len(out["4h"]["bars"])
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(fetch_quote("gold_spot"), ensure_ascii=False))
    print(json.dumps(fetch_quote("dxy"), ensure_ascii=False))
    h = snapshot_history("XAUUSD")
    for tf in ("5m", "15m", "60m", "4h", "1d"):
        print(tf, "n=", h[tf]["n"], "last=", h[tf].get("last_bar_ts"))
