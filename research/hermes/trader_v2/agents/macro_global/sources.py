# -*- coding: utf-8 -*-
"""V2 Agent2 采集层 —— 宏观/地缘/资金流数据源适配（中国大陆直连, point-in-time）。

原则:
- 官方 > 高可信财经 > 专业数据 > 聚合 > 二手。
- 每条信息带 published_at / retrieved_at / source / source_url / credibility。
- 拿不到就诚实报 null + data_gap, 不臆造。
- 只采集“证据/状态”, 不产出任何交易方向信号。
"""
from __future__ import annotations
import json, re, time
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
import requests, sys as _sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in _sys.path:
    _sys.path.insert(0, str(ROOT))

_MISS = object()
_REENTRANT = 0


def _router():
    try:
        import data_sources as _d
        return _d if _d.router_enabled() else None
    except Exception:  # noqa: BLE001
        return None


def _rmacro(name):
    """经 V2 Data Source Router 取宏观数据（含 retry/退避/cache/freshness）；未启用/未注册/已在 router 内 → _MISS。"""
    if _REENTRANT > 0:          # 防回环：router 的 adapter 调用回本函数时必须走 legacy
        return _MISS
    _d = _router()
    if _d is None:
        return _MISS
    try:
        import data_sources.adapters_macro as _am
        if name not in _am.MACRO_DEFS:
            return _MISS
    except Exception:  # noqa: BLE001
        return _MISS
    return _d.macro(name)


UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36"}

# 来源可信度分级
SRC_TIER = {
    "treasury.gov": "official", "ecb.europa.eu": "official", "cftc.gov": "official",
    "gold.org": "official", "pbc.gov.cn": "official", "sge.com.cn": "official",
    "wallstcn": "wire", "cnbc": "wire", "fxstreet": "wire", "jin10": "aggregator",
    "eastmoney": "aggregator", "yahoo": "aggregator",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get(url, params=None, headers=UA, timeout=15):
    r = requests.get(url, headers=headers, params=params, timeout=timeout)
    r.raise_for_status()
    return r


def _ymd_to_iso(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        return None


# ---------------- 行情/价格类（国内可跑: MT5 / 新浪 / 腾讯，经 Router） ----------------
def macro_kv(key):
    """国内可跑宏观/利率 kv（key ∈ dxy/vix/tip/gld/ust10y/gold_spot），经 V2 Router。
    ust10y 用 7-10Y 国债ETF(tencent usUST) 作价格代理并取反以保持“收益率变化%”语义。
    不可用 → raise（供 _safe 转失败哨兵）。"""
    _d = _router()
    if _d is not None:
        try:
            q = _d.quote(key)
            if q and q.get("price") is not None:
                chg = q.get("change"); pct = q.get("change_pct"); note = None
                if key == "ust10y":      # ETF: 价格↑=收益率↓ → 取反
                    chg = None if chg is None else -chg
                    pct = None if pct is None else -pct
                    note = "proxy: tencent usUST(7-10Y ETF, 反向；非 ^TNX 本身)"
                return {"symbol": key, "last": q.get("price"), "change": chg, "change_pct": pct,
                        "data_ts": q.get("data_ts"), "source": q.get("source"), "retrieved_at": _now(), "note": note}
        except Exception:  # noqa: BLE001
            pass
    raise RuntimeError(f"macro_kv unavailable: {key}")


# ---------------- 行情/价格类（Yahoo — 国外, 已不可用; 仅保留参考） ----------------
def yahoo_kv(symbol, interval="1d", rng="1mo"):
    _v = _rmacro(f"yahoo_kv:{symbol}")
    if _v is not _MISS:
        return _v
    j = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
             params={"range": rng, "interval": interval}).json()
    res = j["chart"]["result"][0]
    meta = res["meta"]
    c = res["indicators"]["quote"][0]["close"]
    closes = [x for x in c if x is not None]
    last = meta.get("regularMarketPrice") or (closes[-1] if closes else None)
    prev = meta.get("chartPreviousClose") or (closes[-2] if len(closes) > 1 else None)
    chg = (last - prev) if (last is not None and prev is not None) else None
    return {"symbol": symbol, "last": last, "prev": prev,
            "change": round(chg, 4) if chg is not None else None,
            "change_pct": round(chg / prev * 100, 3) if (chg is not None and prev) else None,
            "data_ts": meta.get("regularMarketTime"), "source": "yahoo",
            "retrieved_at": _now(), "period": rng}


# ---------------- COT（CFTC Socrata 公开 JSON） ----------------
COT_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"


def cftc_cot_gold():
    """最新黄金 COT（含 report_date 发布周 + 结构）。"""
    _v = _rmacro("cot:gold")
    if _v is not _MISS:
        return _v
    params = {"$where": "contract_market_name like 'GOLD%'",
              "$order": "report_date_as_yyyy_mm_dd DESC", "$limit": 3}
    rows = _get(COT_URL, params=params, timeout=20).json()
    if not rows:
        raise ValueError("no cot rows")
    r = rows[0]

    def num(*keys):
        for k in keys:
            if k in r and r[k] not in (None, ""):
                try:
                    return float(r[k])
                except Exception:  # noqa: BLE001
                    pass
        return None
    # —— COT 时间语义修正(Phase-1.5): 报告日期 ≠ 精确发布时间 ——
    rep = _ymd_to_iso(r.get("report_date_as_yyyy_mm_dd"))
    return {
        "contract": r.get("contract_market_name") or r.get("market_and_exchange_names"),
        "report_date": rep,                      # 持仓截止日(周二)
        "publication_date": None,                # 未取到精确发布时刻
        "publication_timestamp_unknown": True,   # 不伪造精确时间
        "timestamp_precision": "approximate",
        "open_interest": num("open_interest_all"),
        "noncommercial_long": num("noncomm_positions_long_all"),
        "noncommercial_short": num("noncomm_positions_short_all"),
        "commercial_long": num("comm_positions_long_all"),
        "commercial_short": num("comm_positions_short_all"),
        "noncommercial_net": (num("noncomm_positions_long_all") or 0) - (num("noncomm_positions_short_all") or 0),
        "source": "CFTC (Socrata 6dca-aqww)", "source_url": COT_URL,
        "credibility": "CONFIRMED", "retrieved_at": _now(),
        "note": "报告日期=持仓截止(周二); 精确发布时刻(周五 15:30 ET)未获取 → publication_timestamp_unknown=true",
    }


# ---------------- 官方宏观源（Phase-1.5: 结构化接入） ----------------
def bls_series(series_ids, start_year=None, end_year=None):
    """BLS 公开 API(免 Key)。返回最新观测(含 period)。"""
    _v = _rmacro("bls:macro")
    if _v is not _MISS:
        return _v
    import json as _j
    if isinstance(series_ids, str):
        series_ids = [series_ids]
    body = {"seriesid": series_ids}
    if start_year: body["startyear"] = str(start_year)
    if end_year: body["endyear"] = str(end_year)
    r = requests.post("https://api.bls.gov/publicAPI/v1/timeseries/data/",
                      data=_j.dumps(body), headers=dict(UA, **{"Content-Type": "application/json"}), timeout=20)
    r.raise_for_status()
    j = r.json()
    out = []
    for s in j.get("Results", {}).get("series", []):
        for d in (s.get("data") or [])[:3]:
            out.append({"series_id": s.get("seriesID"), "period": f"{d.get('year')}-{d.get('period')}",
                        "period_name": d.get("periodName"), "value": d.get("value"),
                        "latest": d.get("latest") == "true",
                        "release_timestamp": None, "release_timestamp_source": "unavailable",
                        "source": "BLS api.bls.gov", "source_url": "https://api.bls.gov/publicAPI/v1/timeseries/data/"})
    return out


ECB_URL = "https://data-api.ecb.europa.eu/service/data"


def ecb_sdmx(flow_ref, key, last_n=1):
    """ECB SDMX-JSON(免 Key)。"""
    u = f"{ECB_URL}/{flow_ref}/{key}"
    j = _get(u, params={"format": "jsondata", "lastNObservations": last_n}, timeout=20).json()
    structs = j.get("structure", {}).get("dimensions", {}).get("observation", [])
    obs = j.get("dataSets", [{}])[0].get("observations", {})
    vals = []
    for k, v in list(obs.items()):
        vals.append({"key": k, "value": v[0] if v else None})
    return {"source": "ECB SDMX", "source_url": u, "n": len(vals), "values": vals[:last_n * 3],
            "release_timestamp": None, "release_timestamp_source": "unavailable",
            "note": "ECB data-api.ecb.europa.eu; 发布时刻需 ECB 日历(未接)"}


def treasury_fiscaldata(path, params=None):
    """美国财政部 FiscalData API(免 Key)。"""
    u = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/{path}"
    j = _get(u, params=params or {}, timeout=20).json()
    return {"source": "US Treasury FiscalData", "source_url": u,
            "n": j.get("meta", {}).get("total-count"), "data": (j.get("data") or [])[:3],
            "release_timestamp": None, "release_timestamp_source": "unavailable"}


# ---------------- 国内黄金 ETF 资金流（东财） ----------------
def em_flow(secid):
    """东财 主力净流入(单日)。返回最新值 + 日期。"""
    _v = _rmacro(f"emflow:{secid.split('.')[-1]}")
    if _v is not _MISS:
        return _v
    u = ("https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?"
         f"secid={secid}&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55&klt=101&lmt=5")
    j = _get(u, timeout=15).json()
    data = j.get("data") or {}
    kl = data.get("klines") or []
    if not kl:
        raise ValueError("no fflow")
    last = kl[-1].split(",")
    return {"code": data.get("code"), "name": data.get("name"), "date": last[0],
            "main_net_inflow": float(last[1]) if last[1] else None,
            "retrieved_at": _now(), "source": "eastmoney", "source_url": u,
            "credibility": "REPORTED", "note": "单位: 元; 仅当日(东财口径)"}


# ---------------- 新闻/快讯 ----------------
def news_wallstcn(limit=30):
    _v = _rmacro("news:wallstcn")
    if _v is not _MISS:
        return _v
    u = f"https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit={limit}"
    j = _get(u, timeout=15).json()
    out = []
    for it in (j.get("data", {}).get("items") or []):
        out.append({
            "title": (it.get("title") or it.get("content_text") or "")[:180],
            "content": (it.get("content_text") or "")[:400],
            "published_at": it.get("display_time"),
            "source": "wallstreetcn", "source_url": "https://wallstreetcn.com/live/global",
            "credibility": "REPORTED", "tier": "wire",
        })
    return out


def news_cnbc_rss(limit=30):
    _v = _rmacro("news:cnbc")
    if _v is not _MISS:
        return _v
    u = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"
    r = _get(u, timeout=15)
    root = ET.fromstring(r.content)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        out.append({"title": title[:180], "published_at_raw": pub, "source": "cnbc",
                    "source_url": link, "credibility": "REPORTED", "tier": "wire"})
        if len(out) >= limit:
            break
    return out


# 事件/地缘/央行/宏观关键词（用于分类与触发, 非方向信号）
GEOPOL_KEYWORDS = ["war", "strike", "missile", "sanction", "conflict", "taiwan", "ukraine",
                   "russia", "israel", "iran", "gaza", "red sea", "coup", "tension",
                   "中东", "俄乌", "制裁", "台海", "冲突", "战争", "袭击", "停火"]
CB_KEYWORDS = ["fed", "fomc", "ecb", "boj", "pboc", "boe", "snb", "rate", "powell",
               "lagarde", "降息", "加息", "利率", "央行", "美联储", "欧央行", "日本央行", "中国人民银行"]
ECON_KEYWORDS = ["cpi", "pce", "ppi", "nfp", "nonfarm", "payroll", "unemployment", "gdp",
                 "pmi", "ism", "claims", "通胀", "非农", "失业", "零售", "国内生产总值"]


def classify(text):
    t = (text or "").lower()
    tags = []
    if any(k in t for k in GEOPOL_KEYWORDS): tags.append("geopolitics")
    if any(k in t for k in CB_KEYWORDS): tags.append("central_bank")
    if any(k in t for k in ECON_KEYWORDS): tags.append("economic_data")
    return tags


# 黄金方向性措辞（只用于 narrative 侧的粗略计数, 不作交易信号）
GOLD_BULL_WORDS = ["避险", "safe haven", "haven demand", "gold up", "gold rises", "金价上涨",
                   "看涨", "buy gold", "record high", "创高", "走强"]
GOLD_BEAR_WORDS = ["gold falls", "gold drops", "金价下跌", "看跌", "sell gold", "走弱", "回调"]


def narrative_score(items):
    """叙事侧净倾向（-1..1）。仅统计措辞, 不构成信号。"""
    bull = bear = 0
    for it in items:
        t = (it.get("title", "") + " " + it.get("content", "")).lower()
        bull += sum(1 for w in GOLD_BULL_WORDS if w.lower() in t)
        bear += sum(1 for w in GOLD_BEAR_WORDS if w.lower() in t)
    n = bull + bear
    return {"bull_mentions": bull, "bear_mentions": bear,
            "net": round((bull - bear) / n, 2) if n else 0.0, "n_mentions": n}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("DXY", json.dumps(yahoo_kv("DX-Y.NYB"), ensure_ascii=False))
    print("UST10Y", json.dumps(yahoo_kv("^TNX"), ensure_ascii=False))
    print("COT", json.dumps(cftc_cot_gold(), ensure_ascii=False)[:300])
    print("EM518880", json.dumps(em_flow("1.518880"), ensure_ascii=False))
    w = news_wallstcn(10); print("wallstcn n=", len(w), "sample:", json.dumps(w[0], ensure_ascii=False)[:150] if w else None)
    c = news_cnbc_rss(10); print("cnbc n=", len(c), "sample:", json.dumps(c[0], ensure_ascii=False)[:150] if c else None)
