# -*- coding: utf-8 -*-
"""V2 Data Source Router — 数据源注册表（source_id / data_type / priority / endpoint / access /
timeout / retry / backoff / freshness_rule / parser / validation / status）。"""
from __future__ import annotations

# 技术 K 线：MT5(本地实例,只读) 优先 → 本地 tick → Yahoo(国外,已降级/不可达)
HISTORY_SOURCES = {
    "5m":  [("mt5", "primary"), ("local_fxtm", "secondary"), ("yahoo", "tertiary")],
    "15m": [("mt5", "primary"), ("local_fxtm", "secondary"), ("yahoo", "tertiary")],
    "60m": [("mt5", "primary"), ("local_fxtm", "secondary"), ("yahoo", "tertiary")],
    "4h":  [("mt5", "primary"), ("local_fxtm", "secondary"), ("yahoo", "tertiary")],
    "1d":  [("mt5", "primary"), ("local_fxtm", "secondary"), ("yahoo", "tertiary")],
}

# 现价多源（全部国内可跑: MT5 / 新浪 / 腾讯；Yahoo 已移除）
QUOTE_SOURCES = {
    "gold_spot":  [("mt5", "XAUUSD"), ("sina", "hf_XAU"), ("tencent", "hf_XAU"), ("local_fxtm", None)],
    "gold_comex": [("sina", "hf_GC"), ("tencent", "hf_GC")],
    "silver":     [("mt5", "XAGUSD"), ("sina", "hf_SI"), ("tencent", "hf_SI")],
    "dxy":        [("sina", "DINIW"), ("tencent", "usDXY")],
    "ust10y":     [("tencent", "usUST")],
    "vix":        [("sina", "znb_VIX"), ("tencent", "usVIX")],
    "gld":        [("tencent", "usGLD")],
    "tip":        [("tencent", "usTIP")],
}

# 每个 source 的元数据
SOURCE_META = {
    "mt5":        {"data_type": "bars/quote", "access": "local MT5 (fxtm_demo_01, read-only)", "timeout": None,
                   "retry": 0, "backoff": 0, "freshness_rule": "tick/bar<15m", "validation": "validate_bars", "status": "ACTIVE"},
    "local_fxtm": {"data_type": "bars/quote", "access": "local parquet (data/live_fxtm)", "timeout": None,
                   "retry": 0, "backoff": 0, "freshness_rule": "tick<15m", "validation": "validate_bars", "status": "ACTIVE"},
    "sina":       {"data_type": "quote", "access": "https hq.sinajs.cn", "timeout": 10, "retry": 1, "backoff": 0.4,
                   "freshness_rule": "<5m", "validation": "validate_quote", "status": "ACTIVE"},
    "tencent":    {"data_type": "quote", "access": "https qt.gtimg.cn", "timeout": 10, "retry": 1, "backoff": 0.4,
                   "freshness_rule": "<5m", "validation": "validate_quote", "status": "ACTIVE"},
    "eastmoney":  {"data_type": "quote/flow", "access": "https push2.eastmoney.com", "timeout": 12, "retry": 1, "backoff": 0.4,
                   "freshness_rule": "<5m", "validation": "validate_quote", "status": "ACTIVE"},
    "yahoo":      {"data_type": "bars/quote", "access": "https query1.finance.yahoo.com", "timeout": 15, "retry": 1, "backoff": 0.5,
                   "freshness_rule": "<1d", "validation": "validate_bars", "status": "UNAVAILABLE(CN 403) — demoted to last resort"},
    "cftc":       {"data_type": "macro", "access": "https publicreporting.cftc.gov", "timeout": 20, "retry": 2, "backoff": 0.6,
                   "freshness_rule": "weekly", "validation": "validate_scalar", "status": "ACTIVE"},
    "bls":        {"data_type": "macro", "access": "https api.bls.gov", "timeout": 20, "retry": 2, "backoff": 0.6,
                   "freshness_rule": "monthly", "validation": "validate_scalar", "status": "ACTIVE"},
    "wallstcn":   {"data_type": "news", "access": "https api-one.wallstcn.com", "timeout": 15, "retry": 1, "backoff": 0.5,
                   "freshness_rule": "<1h", "validation": "none", "status": "ACTIVE"},
    "cnbc":       {"data_type": "news", "access": "https search.cnbc.com RSS", "timeout": 15, "retry": 1, "backoff": 0.5,
                   "freshness_rule": "<1h", "validation": "none", "status": "ACTIVE"},
}


def history_sources(tf):
    return HISTORY_SOURCES.get(tf, [("local_fxtm", "primary"), ("yahoo", "secondary")])


def quote_sources(key):
    return QUOTE_SOURCES.get(key, [])
