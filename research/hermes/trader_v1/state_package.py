# -*- coding: utf-8 -*-
"""state_package.py — Hermes 决策用确定性市场状态包生成器(无 LLM, 只读数据, 可复算)。

多周期: D1(20 根) / H4(48 根) / H1(24 根) / M15(当前+近期)。
数据源: data/staging_fxtm/*.parquet(历史背景) + data/live_fxtm/*.parquet(当前/前瞻)。
同 feed 同定义(与 baseline_seed/metrics 同源纪律); 缺数据 → 标 DATA GAP, 不伪造。

输出: JSON 状态包(market_state 块, 供 Hermes 决策 + 存档)。
用法: .venv\\Scripts\\python.exe research\\hermes\\trader_v1\\state_package.py
      [--output run_state/state_package_latest.json] [--cycle <M15 标签>]
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent.parent
LIVE_DIR = REPO / "data/live_fxtm"
STAGE_DIR = REPO / "data/staging_fxtm"
HERE = Path(__file__).resolve().parent
OUT_DEFAULT = HERE / "run_state" / "state_package_latest.json"


def load_ticks(glob_dir, limit_days=None):
    """读 parquet tick(ts_utc/bid/ask), 按时间拼接; 只取需要的列降内存。"""
    frames = []
    for p in sorted(Path(glob_dir).glob("ticks_*.parquet")):
        try:
            df = pd.read_parquet(p, columns=["ts_utc", "bid", "ask"])
        except Exception:  # noqa: BLE001
            try:
                df = pd.read_parquet(p, columns=["time_msc", "bid", "ask"])
                df["ts_utc"] = pd.to_datetime(df["time_msc"], unit="ms", utc=True)
            except Exception:  # noqa: BLE001
                continue
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["ts_utc", "mid"])
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("ts_utc").drop_duplicates("ts_utc").reset_index(drop=True)
    out["mid"] = (out["bid"] + out["ask"]) / 2
    if limit_days:
        cut = out["ts_utc"].max() - pd.Timedelta(days=limit_days)
        out = out[out["ts_utc"] >= cut]
    return out[["ts_utc", "mid", "bid", "ask"]]


def resample(df, rule, drop_forming=False):
    """重采样为 bars。drop_forming=True: 若最后一根 bar 尚未结束(其结束时刻 > 最新 tick)则剔除。
    L2-H3 修复: 正式决策只允许已收盘 bar(防 look-ahead/未稳定信号)。"""
    o = df.set_index("ts_utc").resample(rule).agg(
        o=("mid", "first"), h=("mid", "max"), l=("mid", "min"), c=("mid", "last"),
        n=("mid", "count")).dropna(subset=["c"])
    o = o[o["n"] > 0]
    if drop_forming and len(o):
        last_idx = o.index[-1]
        last_end = last_idx + pd.Timedelta(rule)
        latest_tick = df["ts_utc"].max()
        if latest_tick < last_end:  # 该 bar 未收盘 → 剔除
            o = o.iloc[:-1]
    return o.reset_index()


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def swing_struct(close):
    """极简结构标注: 最近 N 根的 HH/HL/LH/LL 计数 + 当前相对摆动点位置。"""
    if len(close) < 10:
        return {"note": "insufficient"}
    tail = close.tail(10)
    hh = int((tail.diff() > 0).sum())
    ll = int((tail.diff() < 0).sum())
    up = close.iloc[-1] > close.iloc[-5]
    return {"hhish": hh, "llish": ll, "last_vs_5ago": "up" if up else "down"}


def trend_range(close, n=14):
    """极简 trend/range 分类: 用效率比(ER)与 ADX 风格近似; 返回类别与分数。"""
    tail = close.tail(n + 1)
    net = abs(tail.iloc[-1] - tail.iloc[0])
    path = tail.diff().abs().sum()
    er = net / path if path > 0 else 0
    cat = "trend" if er > 0.35 else ("range" if er < 0.15 else "mixed")
    return {"cat": cat, "er": round(float(er), 3)}


def expand_contract(close, atr, n=10):
    """expansion/contraction: 近 n 根 ATR 与更早 n 根 ATR 之比。"""
    if len(atr) < 2 * n + 1:
        return {"state": "unknown"}
    recent = float(atr.tail(n).mean())
    prior = float(atr.iloc[-2 * n:-n].mean())
    r = recent / prior if prior > 0 else np.nan
    state = "expanding" if r > 1.3 else ("contracting" if r < 0.75 else "neutral")
    return {"state": state, "ratio": round(r, 2)}


def build_tf(df, rule, name, n_req, drop_forming=True):
    """多周期状态(L2-H3: 默认只消费已收盘 bar, 防未收盘 K 线进入正式决策)。"""
    bars = resample(df, rule, drop_forming=drop_forming)
    if len(bars) < n_req:
        return {"tf": name, "bars": int(len(bars)), "needed": n_req,
                "state": "DATA_GAP", "note": f"need {n_req} bars, have {len(bars)}"}
    close = bars["c"]
    atr = (bars["h"] - bars["l"]).rolling(14).mean()
    last_atr_pct = float(atr.iloc[-1] / close.iloc[-1] * 100) if len(atr) else None
    ma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
    ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    r = rsi(close)
    last_rsi = float(r.iloc[-1]) if len(r) and not np.isnan(r.iloc[-1]) else None
    hi = float(bars["h"].tail(60).max())
    lo = float(bars["l"].tail(60).min())
    return {
        "tf": name, "bars": int(len(bars)), "state": "ok",
        "last_close": float(close.iloc[-1]),
        "last_bar": str(bars["ts_utc"].iloc[-1]),
        "ma": {"ma20": ma20, "ma50": ma50, "ma200": ma200},
        "price_vs_ma20": round(float(close.iloc[-1] / ma20 - 1) * 1e4, 1) if ma20 else None,
        "rsi14": last_rsi,
        "atr_pct_last": round(last_atr_pct, 3) if last_atr_pct else None,
        "structure": swing_struct(close),
        "trend_range": trend_range(close),
        "exp_cont": expand_contract(close, atr),
        "s_r": {"high60": round(hi, 2), "low60": round(lo, 2),
                "pos_in_range": round(float((close.iloc[-1] - lo) / (hi - lo) * 100), 1) if hi > lo else None},
        "recent_move_bps": round(float((close.iloc[-1] / close.iloc[-6] - 1) * 1e4), 1) if len(close) >= 6 else None,
    }


def abnormal_m15(bars_m15):
    """recent abnormal movement: 最近 M15 相对其自身分布(量/幅)的 z。纯描述, 不作方向。"""
    if len(bars_m15) < 30:
        return {"note": "insufficient"}
    mv = (bars_m15["c"] / bars_m15["c"].shift(1) - 1).abs() * 1e4
    recent = mv.tail(6)
    mu, sd = mv.iloc[:-6].mean(), mv.iloc[:-6].std()
    if not sd or np.isnan(sd) or sd == 0:
        return {"note": "flat"}
    return {"last6_max_move_bps": round(float(recent.max()), 1),
            "z_vs_baseline": round(float((recent.max() - mu) / sd), 2),
            "baseline_mean_move_bps": round(float(mu), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUT_DEFAULT))
    ap.add_argument("--cycle", default=None, help="M15 cycle label e.g. 2026-09-07T11:30Z")
    a = ap.parse_args()

    live = load_ticks(LIVE_DIR)
    stage = load_ticks(STAGE_DIR)
    df = pd.concat([stage, live], ignore_index=True) if len(stage) else live
    df = df.sort_values("ts_utc").drop_duplicates("ts_utc").reset_index(drop=True)

    now = datetime.now(timezone.utc)
    cycle = a.cycle or now.strftime("%Y-%m-%dT%H:%MZ")
    n_live = len(live) if len(live) else 0
    live_days = int(live["ts_utc"].dt.date.nunique()) if len(live) else 0

    d1 = build_tf(df, "1D", "D1", 20)
    h4 = build_tf(df, "4h", "H4", 48)
    h1 = build_tf(df, "1h", "H1", 24)
    m15_all = resample(df, "15min", drop_forming=True)   # L2-H3: 剔除未收盘 M15
    m15 = build_tf(df, "15min", "M15", 4)
    abn = abnormal_m15(m15_all)

    # M15 当前即时信息(quote 层, 从最近 tick)
    # —— 实时价覆盖: 优先读 quote_latest.json(dashboard 10s 线程更新) ——
    # 2026-09-07 盯梢修复: state_package 读 parquet 滞后(采集 15min), 而 dashboard 线程
    # 每 10s 写 quote_latest.json → engine 决策/触发用实时价, 避免 plan 触发带脱节
    live_mid_override, live_spr_override = None, None
    try:
        qp = REPO / "data/live_fxtm/quote_latest.json"
        if qp.exists():
            import json as _json
            q = _json.loads(qp.read_text(encoding="utf-8"))
            qts = datetime.fromisoformat(q.get("utc_ts", "").replace("Z", "+00:00"))
            if (now - qts).total_seconds() < 120:  # 新鲜(<2min)才用
                live_mid_override = float(q.get("mid"))
                if q.get("spread_usd") is not None:
                    live_spr_override = round(float(q["spread_usd"]) / live_mid_override * 1e4, 2) if live_mid_override else None
    except Exception:  # noqa: BLE001
        pass

    if len(live):
        last = live.iloc[-1]
        spr = float(last["ask"] - last["bid"])
        spr_bps = spr / float(last["mid"]) * 1e4
        window = live[live["ts_utc"] >= live["ts_utc"].max() - pd.Timedelta(minutes=15)]
        tick_rate = int(len(window) / max((window["ts_utc"].max() - window["ts_utc"].min()).total_seconds() / 60, 0.1))
    else:
        spr_bps, tick_rate = None, None
    if live_mid_override is not None:
        spr_bps = live_spr_override if live_spr_override is not None else spr_bps
    mid_for_pkg = live_mid_override if live_mid_override is not None else \
        (float(live.iloc[-1]["mid"]) if len(live) else None)

    gaps = []
    for tf in (d1, h4, h1):
        if tf.get("state") == "DATA_GAP":
            gaps.append(f"{tf['tf']}: have {tf['bars']}/{tf['needed']} bars")
    if live_days == 0:
        gaps.append("live: 0 days")

    pkg = {
        "generated_utc": now.isoformat(),
        "cycle": cycle,
        "symbol": "XAUUSD",
        "data_quality": {"live_days": live_days, "live_ticks": n_live,
                         "context_days": int(df["ts_utc"].dt.date.nunique()), "gaps": gaps},
        "market_state": {
            "d1": d1, "h4": h4, "h1": h1, "m15": m15,
            "m15_live": {"last_mid": mid_for_pkg,
                         "spread_bps_now": round(spr_bps, 2) if spr_bps else None,
                         "tick_rate_per_min_15m": tick_rate,
                         "quote_source": "quote_latest" if live_mid_override is not None else "parquet",
                         "abnormal": abn},
        },
    }
    p = Path(a.output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(pkg, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"STATE_PACKAGE written: {p}  (live_days={live_days}, gaps={gaps})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
