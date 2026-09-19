# -*- coding: utf-8 -*-
"""V2 Data Source Router — 宏观/资金流适配器。

复用现有 `agents/macro_global/sources.py` 的解析实现（延迟导入避免环），但由 router 施加
  retry / 指数退避 / 缓存 / freshness / 审计 语义。
**注意**: 调用 sources 前将 `sources._REENTRANT += 1`，令其走 legacy 路径，避免“router→adapter→sources→router”回环。
"""
from __future__ import annotations


def _S():
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]          # trader_v2
    p = str(root / "agents" / "macro_global")
    if p not in sys.path:
        sys.path.insert(0, p)
    import sources  # noqa: E402
    return sources


def _legacy(fn_name, *a, **k):
    s = _S()
    s._REENTRANT += 1
    try:
        return getattr(s, fn_name)(*a, **k)
    finally:
        s._REENTRANT -= 1


def yahoo_kv(symbol, interval="1d", rng="5d"):
    return _legacy("yahoo_kv", symbol, interval, rng)


def cot_gold():
    return _legacy("cftc_cot_gold")


def bls(series_ids, start_year=None, end_year=None):
    return _legacy("bls_series", series_ids, start_year, end_year)


def em_flow(secid):
    return _legacy("em_flow", secid)


def news_wallstcn(limit=40):
    return _legacy("news_wallstcn", limit)


def news_cnbc(limit=40):
    return _legacy("news_cnbc_rss", limit)


def treasury(path, params=None):
    return _legacy("treasury_fiscaldata", path, params)


def ecb(flow_ref, key, last_n=1):
    return _legacy("ecb_sdmx", flow_ref, key, last_n)


# —— 注册表：name -> (callable, freshness 规则(新鲜h, 陈旧h), host 说明) ——
MACRO_DEFS = {
    "yahoo_kv:DX-Y.NYB": (lambda: yahoo_kv("DX-Y.NYB", "1d", "5d"), (24, 96), "query1.finance.yahoo.com"),
    "yahoo_kv:^TNX":     (lambda: yahoo_kv("^TNX", "1d", "5d"),     (24, 96), "query1.finance.yahoo.com"),
    "yahoo_kv:^VIX":     (lambda: yahoo_kv("^VIX", "1d", "5d"),     (24, 96), "query1.finance.yahoo.com"),
    "yahoo_kv:TIP":      (lambda: yahoo_kv("TIP", "1d", "5d"),      (24, 96), "query1.finance.yahoo.com"),
    "yahoo_kv:GLD":      (lambda: yahoo_kv("GLD", "1d", "1mo"),     (24, 96), "query1.finance.yahoo.com"),
    "cot:gold":          (lambda: cot_gold(),                        (24 * 8, 24 * 21), "publicreporting.cftc.gov"),
    "bls:macro":         (lambda: bls(["CUUR0000SA0", "CUSR0000SA0", "LNS14000000"], 2026, 2026), (24 * 35, 24 * 120), "api.bls.gov"),
    "emflow:518880":     (lambda: em_flow("1.518880"),               (24, 24 * 5), "push2.eastmoney.com"),
    "emflow:159934":     (lambda: em_flow("0.159934"),               (24, 24 * 5), "push2.eastmoney.com"),
    "news:wallstcn":     (lambda: news_wallstcn(40),                 (1, 12), "api-one.wallstcn.com"),
    "news:cnbc":         (lambda: news_cnbc(40),                     (1, 12), "search.cnbc.com"),
}
