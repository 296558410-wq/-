# -*- coding: utf-8 -*-
"""V2 Data Source Router — Data Health Gate（FRESH / STALE_BUT_VALID / MISSING / INVALID / SOURCE_DOWN）。"""
from __future__ import annotations
from . import cache, net

KEY_VARS = {
    "hist:XAUUSD:5m": "XAUUSD 5m", "hist:XAUUSD:15m": "XAUUSD 15m", "hist:XAUUSD:60m": "XAUUSD 60m",
    "hist:XAUUSD:4h": "XAUUSD 4h", "hist:XAUUSD:1d": "XAUUSD 1d",
    "quote:gold_spot": "XAUUSD spot", "quote:dxy": "DXY", "quote:ust10y": "UST10Y", "quote:vix": "VIX",
    "macro:yahoo_kv:DX-Y.NYB": "DXY(macro)", "macro:yahoo_kv:^TNX": "UST10Y(macro)",
    "macro:yahoo_kv:TIP": "RealRate(TIP)", "macro:cot:gold": "COT(Gold)",
    "macro:bls:macro": "BLS macro", "macro:emflow:518880": "CN Gold ETF 518880",
    "macro:emflow:159934": "CN Gold ETF 159934",
}
TECH_TFS = ("5m", "15m", "60m")


def _state_for(key):
    rec = cache.get(key)
    if rec is None:
        return cache.MISSING, None
    return rec.get("freshness", cache.MISSING), rec.get("age_hours")


def build_report(router=None) -> dict:
    vars_ = {}
    for k, label in KEY_VARS.items():
        st, age = _state_for(k)
        vars_[label] = {"key": k, "freshness": st, "age_hours": age}
    # 源级热状态
    down = net.cooldowns()
    tech_ok = all(vars_.get(f"XAUUSD {tf}", {}).get("freshness") in (cache.FRESH, cache.STALE) for tf in TECH_TFS)
    macro_vars = [v for k, v in vars_.items() if k.startswith(("DXY", "UST10Y", "VIX", "RealRate", "COT", "BLS", "CN Gold"))]
    macro_stale = [v["key"] for v in macro_vars if v["freshness"] == cache.STALE]
    macro_missing = [v["key"] for v in macro_vars if v["freshness"] in (cache.MISSING, cache.SOURCE_DOWN)]
    return {
        "agent1": {"technical_status": ("READY" if tech_ok else "TECHNICAL_DATA_UNAVAILABLE"),
                   "timeframes": {tf: vars_.get(f"XAUUSD {tf}", {}).get("freshness") for tf in ("5m", "15m", "60m", "4h", "1d")}},
        "agent2": {"macro_status": ("HEALTHY" if not macro_missing else ("PARTIAL" if len(macro_missing) < len(macro_vars) else "MISSING")),
                   "stale": macro_stale, "missing": macro_missing},
        "vars": vars_,
        "sources_down": down,
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
