# -*- coding: utf-8 -*-
"""V2 Data Source Router — 行情适配器（现价多源 + 历史 K 线本地优先），HTTP 走 net 门卫。"""
from __future__ import annotations
import time
from datetime import datetime, timezone
from . import net, local_bars

UA = net.UA
SINA_H = dict(UA); SINA_H["Referer"] = "https://finance.sina.com.cn"
_TF_SECONDS = {"5m": 300, "15m": 900, "60m": 3600, "4h": 14400, "1d": 86400}
YF_INTERVAL = {"5m": ("5m", "5d"), "15m": ("15m", "5d"), "60m": ("60m", "1mo"), "1d": ("1d", "3mo")}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------- 现价 ----------------
def q_sina(code):
    r = net.fetch(f"https://hq.sinajs.cn/list={code}", headers=SINA_H, read_timeout=10, retries=1, backoff=0.4, cooldown=180)
    if not r["ok"]:
        raise RuntimeError(f"sina:{r['error']}")
    txt = r["text"].split('"')[1] if '"' in r["text"] else ""
    if not txt:
        raise ValueError("sina empty")
    f = txt.split(",")
    if code.upper() == "DINIW":            # 美元指数(国内可跑)
        last = float(f[8] or f[1]); prev = float(f[3]) if len(f) > 3 and f[3] else None
        chg = (last - prev) if prev else None
        return {"price": last, "bid": None, "ask": None, "spread": None, "prev": prev,
                "change": round(chg, 4) if chg is not None else None,
                "change_pct": round(chg / prev * 100, 3) if (chg is not None and prev) else None,
                "data_ts": (f[10] + " " + f[0]) if len(f) > 10 else f[0], "source": "sina"}
    if code.startswith("znb_"):             # 全球指数(如 VIX恐慌指数)
        last = float(f[1]); chg = float(f[2]) if len(f) > 2 and f[2] else None
        pct = float(f[3]) if len(f) > 3 and f[3] else None
        return {"price": last, "bid": None, "ask": None, "spread": None, "change": chg, "change_pct": pct,
                "data_ts": (f[6] + " " + f[7]) if len(f) > 7 else None, "source": "sina"}
    last = float(f[0]); ask = float(f[3]) if len(f) > 3 and f[3] else last; bid = float(f[2]) if len(f) > 2 and f[2] else last
    return {"price": last, "bid": bid, "ask": ask, "spread": round(ask - bid, 3),
            "data_ts": f[6] if len(f) > 6 else None, "source": "sina"}


def q_tencent(code):
    r = net.fetch(f"https://qt.gtimg.cn/q={code}", read_timeout=10, retries=1, backoff=0.4, cooldown=180)
    if not r["ok"]:
        raise RuntimeError(f"tencent:{r['error']}")
    txt = r["text"].split('"')[1] if '"' in r["text"] else ""
    if not txt:
        raise ValueError("tencent empty")
    if code.startswith("hf_"):
        f = txt.split(",")
        last = float(f[0]); bid = float(f[2]) if f[2] else last; ask = float(f[3]) if f[3] else last
        return {"price": last, "bid": bid, "ask": ask, "spread": round(ask - bid, 3),
                "data_ts": f[6] if len(f) > 6 else None, "source": "tencent"}
    # 美股/ETF 格式(~ 分隔): f[3]=最新, f[31]=涨跌, f[32]=涨跌%
    f = txt.split("~")
    if len(f) < 33:
        raise ValueError("tencent us format unexpected")
    last = float(f[3]); chg = float(f[31]) if f[31] else None; pct = float(f[32]) if f[32] else None
    return {"price": last, "bid": None, "ask": None, "spread": None, "change": chg, "change_pct": pct,
            "data_ts": f[30] if f[30] else None, "source": "tencent"}


def q_eastmoney(secid):
    r = net.fetch(f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f58,f57,f170",
                  read_timeout=12, retries=1, backoff=0.4, cooldown=180)
    if not r["ok"] or not r["json"]:
        raise RuntimeError(f"eastmoney:{r['error']}")
    j = (r["json"] or {}).get("data")
    if not j:
        raise ValueError("eastmoney null")
    return {"price": j["f43"] / 100.0, "bid": None, "ask": None, "spread": None,
            "data_ts": None, "source": "eastmoney", "name": j.get("f58")}


def q_yahoo(symbol):
    r = net.fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                  params={"range": "1d", "interval": "5m"}, read_timeout=12, retries=1, backoff=0.5, cooldown=300)
    if not r["ok"] or not r["json"]:
        raise RuntimeError(f"yahoo:{r['error']}")
    m = r["json"]["chart"]["result"][0]["meta"]
    return {"price": m.get("regularMarketPrice"), "bid": None, "ask": None, "spread": None,
            "data_ts": m.get("regularMarketTime"), "source": "yahoo"}


QUOTE_PARSERS = {"sina": q_sina, "tencent": q_tencent, "eastmoney": q_eastmoney, "yahoo": q_yahoo}


# ---------------- 历史 K 线 ----------------
def hist_local(tf):
    return local_bars.build_bars(tf)


def hist_yahoo(symbol, tf):
    interval, rng = YF_INTERVAL[tf]
    r = net.fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                  params={"range": rng, "interval": interval}, read_timeout=15, retries=1, backoff=0.5, cooldown=300)
    if not r["ok"] or not r["json"]:
        raise RuntimeError(f"yahoo:{r['error']}")
    res = r["json"]["chart"]["result"][0]
    ts = res["timestamp"]; q = res["indicators"]["quote"][0]
    o, h, l, c, v = q.get("open"), q.get("high"), q.get("low"), q.get("close"), q.get("volume")
    bars = []
    for i in range(len(ts)):
        if None in (o[i], h[i], l[i], c[i]):
            continue
        bars.append({"t": int(ts[i]), "o": float(o[i]), "h": float(h[i]), "l": float(l[i]),
                     "c": float(c[i]), "v": float((v[i] if v else 0) or 0)})
    now = time.time()
    if bars and bars[-1]["t"] + _TF_SECONDS[tf] > now:
        bars = bars[:-1]
    return {"tf": tf, "symbol": symbol, "source": "yahoo", "interval": interval, "range": rng,
            "bars": bars, "n": len(bars), "retrieval_ts": _now_iso(),
            "last_bar_ts": bars[-1]["t"] if bars else None}
