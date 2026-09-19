# -*- coding: utf-8 -*-
"""V2 Agent2 事件触发刷新器 —— 让 Agent2 在重大事件时不局限于 60 分钟周期。

机制(诚实标注局限):
1) 指标异动: DXY / UST10Y / VIX 的短窗与日变更幅超阈值 → 触发(快速重定价信号)。
2) 新闻事件: 近 trigger_window 分钟内出现 央行/经济数据/地缘 高影响关键词 → 触发。
3) 校准型事件(CPI/FOMC 等)的“发布瞬间”依赖财经日历, 本阶段无免 Key 直连日历 → 列为 data_gap,
   以“新闻出现即触发”替代(有分钟级延迟)。
输出 state/agent2_trigger.json: {trigger, severity, reasons[], ts}; 供编排层立即重刷 Agent2 + 通知 Hermes。
用法: python event_trigger.py [--window-min 30]
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import sources as S  # noqa: E402
import agent2 as A  # noqa: E402

STATE = ROOT / "state"
THRESHOLDS = {"dxy_1d_pct": 0.8, "ust10y_1d_pct": 2.0, "vix_1d_pct": 8.0}
HIGH_IMPACT_WORDS = ["cpi", "pce", "nfp", "fomc", "rate decision", "emergency", "war",
                     "invasion", "strike", "sanction", "非农", "加息", "降息", "紧急",
                     "战争", "袭击", "制裁", "封锁", "default"]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _news_recent_impactful(news, window_min):
    import time
    now = time.time()
    hits = []
    for n in news:
        txt = (n.get("title", "") + " " + n.get("content", "")).lower()
        if not any(w in txt for w in HIGH_IMPACT_WORDS):
            continue
        tags = S.classify(n.get("title", "") + " " + n.get("content", ""))
        if not tags:
            continue
        pa = n.get("published_at") or n.get("published_at_raw")
        recent = False
        try:
            if isinstance(pa, (int, float)):
                recent = (now - pa) <= window_min * 60
        except Exception:  # noqa: BLE001
            pass
        hits.append({"title": n.get("title"), "source": n.get("source"),
                     "published_at": pa, "tags": tags, "recent_known": recent})
    return hits


def evaluate_inputs(dxy_pct, tnx_pct, vix_pct, news, window_min=45):
    """纯函数版(可测试): 由指标变化 + 新闻列表判定是否触发。"""
    reasons, severity = [], 0
    for name, p, thr in (("DXY", dxy_pct, THRESHOLDS["dxy_1d_pct"]),
                         ("UST10Y", tnx_pct, THRESHOLDS["ust10y_1d_pct"]),
                         ("VIX", vix_pct, THRESHOLDS["vix_1d_pct"])):
        if p is not None and abs(p) >= thr:
            reasons.append(f"{name} 1d {p:+.2f}% ≥ 阈值 {thr}%")
            severity = max(severity, 2)
    hits = _news_recent_impactful(news, window_min)
    for h in hits[:10]:
        reasons.append(f"新闻[{h['tags']}] {h['title'][:60]} ({h['source']})")
        severity = max(severity, 1 if not h.get("recent_known") else 2)
    return {"trigger": len(reasons) > 0, "severity": severity, "reasons": reasons,
            "window_min": window_min, "ts": _now(),
            "limitations": ["无免 Key 财经日历 → 发布瞬间以新闻出现替代(分钟级延迟)",
                            "阈值门限为静态默认值, 未做波动自适应"]}


def evaluate(window_min=45):
    dxy = A._safe(lambda: S.yahoo_kv("DX-Y.NYB", "1d", "5d"))
    tnx = A._safe(lambda: S.yahoo_kv("^TNX", "1d", "5d"))
    vix = A._safe(lambda: S.yahoo_kv("^VIX", "1d", "5d"))
    news = (A._safe(lambda: S.news_wallstcn(40), default=[]) or []) + (A._safe(lambda: S.news_cnbc_rss(40), default=[]) or [])
    news = [n for n in news if isinstance(n, dict) and not n.get("__failed__")]
    out = evaluate_inputs(dxy.get("change_pct"), tnx.get("change_pct"), vix.get("change_pct"),
                          news, window_min)
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "agent2_trigger.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--window-min", type=int, default=45)
    a = ap.parse_args()
    r = evaluate(a.window_min)
    print(json.dumps(r, ensure_ascii=False, indent=1))
