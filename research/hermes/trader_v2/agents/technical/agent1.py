# -*- coding: utf-8 -*-
"""V2 Agent1 —— 技术/市场情报 Agent（确定性快照生成, 无 LLM）。

产出"最新状态快照"(非新闻摘要):
  state/agent1_latest.json   + state/snapshots/agent1_<cycle>.json
含: 多周期结构/趋势/波动/VWAP/EMA/关键价位/市场状态/规则型候选机会/数据质量/point-in-time 元数据。
Hermes 每轮读本快照(agent1_latest.json)作为技术情报输入。
用法: python agent1.py [--cycle <label>]
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import market_data as MD  # noqa: E402
import features as F  # noqa: E402

STATE = ROOT / "state"
SNAP = STATE / "snapshots"
AGENT_VERSION = "agent1/0.1.0"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _compact(iso):
    return iso.replace(":", "").replace("-", "").split(".")[0]


def key_levels(tfs):
    lv = {"swing_highs": [], "swing_lows": []}
    for tf in ("60m", "15m"):
        st = tfs.get(tf, {}).get("structure", {}).get("last_swings", [])
        for s in st:
            (lv["swing_highs"] if s["type"] == "H" else lv["swing_lows"]).append(
                {"tf": tf, "price": round(s["price"], 2)})
    lv["range60_15m"] = tfs.get("15m", {}).get("range60")
    lv["vwap_15m"] = tfs.get("15m", {}).get("vwap")
    lv["ma_cluster_60m"] = {k: v for k, v in (tfs.get("60m", {}).get("ma") or {}).items() if v}
    return lv


def candidates(tfs, regime, live):
    """规则型候选机会(仅证据, 非交易决策; Hermes 自行判断采纳/反驳)。"""
    out = []
    t15 = tfs.get("15m", {})
    bo = t15.get("breakout", {}).get("state")
    rp = t15.get("range60", {}) or {}
    vwap15 = t15.get("vwap")
    last = t15.get("last_close")
    if bo == "breakout_up":
        out.append({"id": "cand_bo_up_15m", "type": "breakout_continuation", "dir_hint": "LONG",
                    "reference_level": t15["breakout"]["range_hi"],
                    "falsify_if": f"回到区间内(<{t15['breakout']['range_hi']})",
                    "evidence_strength": 0.6 if regime.get("regime") == "trend" else 0.4,
                    "uncertainty": "需 HTF 同向与跟随"})
    elif bo == "breakout_down":
        out.append({"id": "cand_bo_dn_15m", "type": "breakout_continuation", "dir_hint": "SHORT",
                    "reference_level": t15["breakout"]["range_lo"],
                    "falsify_if": f"回到区间内(>{t15['breakout']['range_lo']})",
                    "evidence_strength": 0.6 if regime.get("regime") == "trend" else 0.4,
                    "uncertainty": "需 HTF 同向与跟随"})
    elif bo == "false_breakout_up":
        out.append({"id": "cand_fbo_up_15m", "type": "failed_breakout_fade", "dir_hint": "SHORT",
                    "reference_level": t15["breakout"]["range_hi"], "falsify_if": "重新站上并收破该位",
                    "evidence_strength": 0.5, "uncertainty": "假突破需后续确认"})
    elif bo == "false_breakout_down":
        out.append({"id": "cand_fbo_dn_15m", "type": "failed_breakout_fade", "dir_hint": "LONG",
                    "reference_level": t15["breakout"]["range_lo"], "falsify_if": "重新跌破并收破该位",
                    "evidence_strength": 0.5, "uncertainty": "假突破需后续确认"})
    if regime.get("regime") == "range" and rp.get("pos_pct") is not None and last:
        if rp["pos_pct"] >= 80:
            out.append({"id": "cand_range_top_15m", "type": "range_top_fade", "dir_hint": "SHORT",
                        "reference_level": rp["high"], "falsify_if": f"收破区间上沿{rp['high']}",
                        "evidence_strength": 0.45, "uncertainty": "区间是否有效"})
        elif rp["pos_pct"] <= 20:
            out.append({"id": "cand_range_bot_15m", "type": "range_bottom_fade", "dir_hint": "LONG",
                        "reference_level": rp["low"], "falsify_if": f"收破区间下沿{rp['low']}",
                        "evidence_strength": 0.45, "uncertainty": "区间是否有效"})
    return out


def build(cycle=None):
    cycle = cycle or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    quotes = {k: MD.fetch_quote(k) for k in
              ("gold_spot", "gold_comex", "silver", "dxy", "ust10y", "vix", "gld")}
    hist = MD.snapshot_history("XAUUSD")
    tfs = {tf: F.tf_features(hist[tf]["bars"], tf) for tf in ("5m", "15m", "60m", "4h", "1d")}
    live = {"price": quotes.get("gold_spot", {}).get("price"),
            "spread": quotes.get("gold_spot", {}).get("spread")}
    regime = F.market_regime(tfs, live)
    # P0-01: 主序列=XAUUSD 现货（router 主源 local_fxtm，yahoo 备用）。GC=F 仅作 reference_market（spot_check.gold_comex）。
    primary_last = tfs.get("15m", {}).get("last_close")
    primary_src = (MD.last_history_source("XAUUSD", "15m") or "unknown")
    spot = quotes.get("gold_spot", {}).get("price")
    basis = round(primary_last - spot, 2) if (primary_last is not None and spot is not None) else None
    basis_bps = round((primary_last / spot - 1) * 1e4, 1) if (primary_last and spot) else None
    price_basis = {"primary": f"XAUUSD@{primary_src}", "primary_source": primary_src, "primary_last": primary_last,
                   "spot_check": {k: quotes.get(k, {}).get("price") for k in ("gold_spot", "gold_comex")},
                   "source_basis_usd": basis, "source_basis_bps": basis_bps,
                   "basis_usd": basis, "basis_bps": basis_bps,
                   "note": "主序列=XAUUSD; basis=主序列源 与 sina 现货源 的 source_basis（仅交叉校验, 未拼接; 非 COMEX 基差）"}
    dq = {tf: {"n_bars": hist[tf]["n"], "retrieval_ts": hist[tf].get("retrieval_ts"),
               "last_bar_ts": hist[tf].get("last_bar_ts"), "error": hist[tf].get("error")}
          for tf in ("5m", "15m", "60m", "4h", "1d")}
    gaps = [tf for tf, v in dq.items() if v["n_bars"] < 20]
    snap = {
        "agent": "agent1-technical", "agent_version": AGENT_VERSION,
        "generated_utc": _now(), "cycle": cycle, "symbol": "XAUUSD",
        "point_in_time": {"retrieval_ts": _now(),
                          "note": "历史=Yahoo(单源, 已剔除未收盘); 现价=多源回退; 不合并非同源序列"},
        "quotes": quotes,
        "price_basis": price_basis,
        "timeframes": tfs,
        "market_regime": regime,
        "key_levels": key_levels(tfs),
        "deterministic_candidates": candidates(tfs, regime, live),
        "volatility": {"atr_pct_15m": tfs["15m"].get("atr_pct"), "atr_pct_60m": tfs["60m"].get("atr_pct"),
                       "exp_cont_15m": tfs["15m"].get("exp_cont"), "rv_ann_15m": tfs["15m"].get("realized_vol_ann")},
        "data_quality": {"gaps": gaps, "by_tf": dq,
                         "sources": {"history": primary_src, "quotes": sorted({q.get("source") for q in quotes.values() if q.get("source")})}},
    }
    STATE.mkdir(parents=True, exist_ok=True); SNAP.mkdir(parents=True, exist_ok=True)
    (STATE / "agent1_latest.json").write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
    ver = SNAP / f"agent1_{_compact(cycle)}.json"
    ver.write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
    return snap, ver


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--cycle", default=None)
    a = ap.parse_args()
    snap, ver = build(a.cycle)
    print("AGENT1_SNAPSHOT written:", ver)
    print("  live gold:", snap["quotes"]["gold_spot"].get("price"), "spread", snap["quotes"]["gold_spot"].get("spread"))
    print("  regime:", snap["market_regime"]["regime"], snap["market_regime"]["trend_range_by_tf"])
    print("  15m:", {k: snap["timeframes"]["15m"].get(k) for k in ("last_close", "rsi14", "trend_range")})
    print("  candidates:", [c["id"] for c in snap["deterministic_candidates"]])
    print("  gaps:", snap["data_quality"]["gaps"])
