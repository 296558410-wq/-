# -*- coding: utf-8 -*-
"""Hermes V2 机会发现（Opportunity Discovery）—— 主动搜索, 非投票。

在冻结的 decision_context 之上, 扫描 A–F 类机会(趋势/突破/假突破反转/宏观重定价/地缘冲击/叙事-资金流背离),
每类产出 candidate: thesis + trigger + invalidation + expected_R_est + priced_in + evidence_ids + counter_thesis。
反证扫描(§六)与定价检查(§七)内建于每个 candidate。**本模块只产候选, 不产最终交易指令。**
"""
from __future__ import annotations
from datetime import datetime, timezone


def _g(d, *path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def _priced_in(recent_move_bps, typical_atr_pct, direction):
    """粗估'是否已被定价': 用近段已走出幅度 vs 典型波动。返回 LOW/MED/HIGH。"""
    if recent_move_bps is None or not typical_atr_pct:
        return "UNKNOWN"
    move = abs(recent_move_bps) / 100.0  # %
    ratio = move / max(typical_atr_pct, 1e-6)
    if direction == "LONG" and recent_move_bps > 0:  # 已涨, 做多=追高
        return "HIGH" if ratio > 2.0 else ("MED" if ratio > 1.0 else "LOW")
    if direction == "SHORT" and recent_move_bps < 0:
        return "HIGH" if ratio > 2.0 else ("MED" if ratio > 1.0 else "LOW")
    return "LOW"


def _evidence_ids(ctx):
    return ctx.get("evidence_ids", [])


def discover(ctx, a1, a2):
    """返回 candidates 列表。"""
    cands = []
    tfs = _g(a1, "timeframes", default={})
    t15 = tfs.get("15m", {}); t60 = tfs.get("60m", {}); t4 = tfs.get("4h", {})
    regime = _g(a1, "market_regime", default={})
    reg = regime.get("regime")
    atr15 = _g(t15, "atr_pct", default=None)
    rm15 = _g(t15, "recent_move_bps", default=None)
    gt = _g(a2, "gold_macro_state", default="UNCERTAIN")
    dxy_pct = _g(a2, "macro", "usd", "change_pct_1d", default=None)
    tnx_pct = _g(a2, "macro", "rates", "change_pct_1d", default=None)
    diverg = _g(a2, "narrative_vs_flow", "narrative_flow_divergence", default=False)
    geo_n = len(_g(a2, "geopolitics", "events", default=[]))
    ev_ids = _evidence_ids(ctx)

    # A. 趋势机会: 多周期同向 + (回撤/结构)
    dirs = {tf: (_g(tfs.get(tf, {}), "structure", "swing_bias") or "neutral") for tf in ("15m", "60m", "4h", "1d")}
    up = sum(1 for v in dirs.values() if v == "up"); dn = sum(1 for v in dirs.values() if v == "down")
    if reg == "trend" and up >= 3:
        cands.append({"id": "opp_trend_long", "category": "trend", "dir_hint": "LONG",
                      "thesis": "多周期同向上行(≥3 TF swing_bias=up)+regime=trend",
                      "trigger": f"回撤守住 15m range 上沿/前低后再抬升", "invalidation": "跌破 15m range60 下沿",
                      "expected_R_est": 2.0, "priced_in": _priced_in(rm15, atr15, "LONG"),
                      "counter_thesis": "HTF 阻力 / 宏观冲突 / 已延伸", "evidence_ids": ev_ids[:5],
                      "macro_align": gt})
    if reg == "trend" and dn >= 3:
        cands.append({"id": "opp_trend_short", "category": "trend", "dir_hint": "SHORT",
                      "thesis": "多周期同向下行(≥3 TF swing_bias=down)+regime=trend",
                      "trigger": "反抽 15m 供给带后再下破", "invalidation": "收复 15m range60 上沿",
                      "expected_R_est": 2.0, "priced_in": _priced_in(rm15, atr15, "SHORT"),
                      "counter_thesis": "超卖反弹 / 宏观转多 / 已延伸", "evidence_ids": ev_ids[:5],
                      "macro_align": gt})

    # B. 突破机会
    bo15 = _g(t15, "breakout", "state")
    if bo15 == "breakout_up":
        cands.append({"id": "opp_bo_long", "category": "breakout", "dir_hint": "LONG",
                      "thesis": "15m 上破 20bar 区间", "trigger": f"收在 {_g(t15,'breakout','range_hi')} 之上",
                      "invalidation": "回到区间内", "expected_R_est": 1.8,
                      "priced_in": _priced_in(rm15, atr15, "LONG"),
                      "counter_thesis": "假突破 / 无量能跟随", "evidence_ids": ev_ids[:5], "macro_align": gt})
    if bo15 == "breakout_down":
        cands.append({"id": "opp_bo_short", "category": "breakout", "dir_hint": "SHORT",
                      "thesis": "15m 下破 20bar 区间", "trigger": f"收在 {_g(t15,'breakout','range_lo')} 之下",
                      "invalidation": "回到区间内", "expected_R_est": 1.8,
                      "priced_in": _priced_in(rm15, atr15, "SHORT"),
                      "counter_thesis": "假突破 / 无量能跟随", "evidence_ids": ev_ids[:5], "macro_align": gt})

    # C. 假突破 / 反转
    if bo15 in ("false_breakout_up",):
        cands.append({"id": "opp_fbo_short", "category": "false_breakout", "dir_hint": "SHORT",
                      "thesis": "上破失败(影线越界未收) = 流动性扫损", "trigger": "确认收回并走低",
                      "invalidation": "重新收破上沿", "expected_R_est": 1.6,
                      "priced_in": "LOW", "counter_thesis": "真突破前的最后一次回踩",
                      "evidence_ids": ev_ids[:5], "macro_align": gt})
    if bo15 in ("false_breakout_down",):
        cands.append({"id": "opp_fbo_long", "category": "false_breakout", "dir_hint": "LONG",
                      "thesis": "下破失败(影线越界未收) = 流动性扫损", "trigger": "确认收回并走高",
                      "invalidation": "重新收破下沿", "expected_R_est": 1.6,
                      "priced_in": "LOW", "counter_thesis": "真突破前的最后一次反抽",
                      "evidence_ids": ev_ids[:5], "macro_align": gt})

    # D. 宏观重新定价: 收益率/美元 明显变动 但黄金尚未跟随
    if tnx_pct is not None and dxy_pct is not None:
        macro_stress = (abs(tnx_pct) >= 1.0) or (abs(dxy_pct) >= 0.5)
        if macro_stress:
            # 收益率↑/美元↑ → 黄金压力 → 潜在 SHORT; 反之 LONG
            dir_hint = "SHORT" if (tnx_pct > 0 and dxy_pct > 0) else ("LONG" if (tnx_pct < 0 and dxy_pct < 0) else None)
            if dir_hint:
                cands.append({"id": f"opp_macro_repricing_{dir_hint.lower()}", "category": "macro_repricing",
                              "dir_hint": dir_hint,
                              "thesis": f"收益率 {tnx_pct:+.2f}%/美元 {dxy_pct:+.2f}% 变动, 黄金或需重新定价",
                              "trigger": "黄金价格向宏观方向确认跟随", "invalidation": "宏观变量回落且黄金无跟随",
                              "expected_R_est": 1.5, "priced_in": _priced_in(rm15, atr15, dir_hint),
                              "counter_thesis": "市场已定价 / 收益率变动非持续性", "evidence_ids": ev_ids[:6],
                              "macro_align": gt, "requires_confirmation": True,
                              "priced_in_check": "需比对 event后 DXY/yields/gold 的先后与 follow-through"})

    # E. 地缘冲击: 有地缘事件 → 观察 headline→price→follow-through
    if geo_n > 0:
        cands.append({"id": "opp_geo_shock", "category": "geopolitical", "dir_hint": "LONG",
                      "thesis": f"存在 {geo_n} 条地缘事件; 需判断是重新定价还是 headline spike",
                      "trigger": "新闻后黄金上冲且 yield/USD 同向确认 + 有 follow-through",
                      "invalidation": "冲高立即回吐且无后续确认",
                      "expected_R_est": 1.4, "priced_in": _priced_in(rm15, atr15, "LONG"),
                      "counter_thesis": "headline spike 已衰竭 / 已被定价 / 可信度低", "evidence_ids": ev_ids[:8],
                      "macro_align": gt, "requires_confirmation": True})

    # F. 叙事 vs 资金流背离
    if diverg:
        cands.append({"id": "opp_narrative_flow_divergence", "category": "narrative_flow",
                      "dir_hint": None,
                      "thesis": "叙事与真实资金流背离(见 Agent2.narrative_vs_flow)",
                      "trigger": "价格选择方向并得到资金流后续确认", "invalidation": "叙事或资金流其一回归一致",
                      "expected_R_est": 1.2, "priced_in": "UNKNOWN",
                      "counter_thesis": "背离为噪音 / 资金流口径滞后", "evidence_ids": ev_ids[:6],
                      "macro_align": gt, "requires_confirmation": True})
    return cands


def regime_tags(ctx, a1, a2):
    """Hermes 自己的 regime 判断(可多标签; 不复用 Agent 的单一标签)。"""
    tags = set()
    r = _g(a1, "market_regime", "regime")
    if r == "trend": tags.add("TREND")
    if r == "range": tags.add("RANGE")
    ec = _g(a1, "timeframes", "15m", "exp_cont", "state")
    if ec == "expanding": tags.add("HIGH_VOLATILITY")
    if ec == "contracting": tags.add("LOW_VOLATILITY")
    bo = _g(a1, "timeframes", "15m", "breakout", "state")
    if bo in ("breakout_up", "breakout_down"): tags.add("BREAKOUT")
    if bo in ("false_breakout_up", "false_breakout_down"): tags.add("BREAKOUT_FAILURE")
    if _g(a1, "data_quality", "gaps"): tags.add("UNCERTAIN")
    dxy_p = _g(a2, "macro", "usd", "change_pct_1d"); tnx_p = _g(a2, "macro", "rates", "change_pct_1d")
    if (dxy_p is not None and abs(dxy_p) >= 0.5) or (tnx_p is not None and abs(tnx_p) >= 1.0):
        tags.add("MACRO_EVENT")
    if len(_g(a2, "geopolitics", "events", default=[])) > 0: tags.add("GEOPOLITICAL_EVENT")
    if not tags: tags.add("UNCERTAIN")
    return sorted(tags)


if __name__ == "__main__":
    import sys, json
    sys.stdout.reconfigure(encoding="utf-8")
    from context import build_context
    ctx, _ = build_context()
    a1 = json.load(open("state/agent1_latest.json", encoding="utf-8")) if False else None
    print("regime tags:", regime_tags(ctx, {}, {}))
