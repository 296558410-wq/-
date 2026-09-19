# -*- coding: utf-8 -*-
"""V1 全生命周期数据重建 + 诊断（只读；不优化、不改 V1；无订单）。

产出: V1_LIFECYCLE_DATA_REGISTRY.json, V1_TRADE_MASTER.jsonl, V1_LIFECYCLE_TIMELINE.json,
      V1_PNL_SERIES.json, V1_DIRECTIONAL_PERIODS.json, V1_MARKET_REGIME.json, V1_LOSS_STREAK.json
"""
from __future__ import annotations
import hashlib
import json
import statistics as st
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

V1 = Path(r"C:\AIQuant\research\hermes\trader_v1")
AUDIT = Path(r"C:\AIQuant\research\hermes\v1_audit")
DATA = Path(r"C:\AIQuant\data")
TICKS = DATA / "live_fxtm"
NOW = datetime.now(timezone.utc).isoformat()
HOR = [1000, 2000, 5000, 10000, 30000, 60000, 180000, 300000, 900000]
SEED = 20260917


def sha(p):
    try:
        h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
    except Exception:  # noqa: BLE001
        return None


def ep(s):
    if not s:
        return None
    try:
        return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp() * 1000)
    except Exception:  # noqa: BLE001
        return None


def load_ticks():
    fr = [pd.read_parquet(f, columns=["time_msc", "bid", "ask"]) for f in sorted(TICKS.glob("ticks_*.parquet"))]
    d = pd.concat(fr, ignore_index=True).sort_values("time_msc")
    t = d["time_msc"].to_numpy(); bid = d["bid"].to_numpy(); ask = d["ask"].to_numpy()
    return t, (bid + ask) / 2.0, bid, ask


def parse_ledger():
    trades = {}
    counts = {"registered": 0, "triggered": 0, "trigger_risk_pass": 0, "trigger_risk_fail": 0,
              "filled": 0, "closed": 0, "cancelled": 0}
    for ln in (V1 / "run_state" / "plan_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        o = json.loads(ln); ty = o.get("type"); pid = o.get("plan_id")
        counts[ty] = counts.get(ty, 0) + 1
        if ty == "triggered":
            counts["trigger_risk_pass" if o.get("risk_pass") else "trigger_risk_fail"] += 1
        if not pid:
            continue
        t = trades.setdefault(pid, {"plan_id": pid})
        if ty == "registered":
            t["direction"] = o.get("decision") or (o.get("plan") or {}).get("direction")
            t["t_signal"] = o.get("utc_ts") or ep(pid)
            pl = o.get("plan") or {}
            t["entry_zone"] = pl.get("entry_zone"); t["sl_plan"] = pl.get("stop_loss")
            t["tp_plan"] = pl.get("take_profit")
        elif ty == "filled":
            t["t_fill"] = o.get("utc_ts"); t["fill_price"] = o.get("price"); t["position_id"] = o.get("position_id"); t["qty"] = o.get("qty")
        elif ty == "closed":
            t["t_exit"] = o.get("utc_ts"); t["exit_price"] = o.get("exit_price"); t["close_reason"] = o.get("reason"); t["realized_usd"] = o.get("realized_usd")
    return trades, counts


def main():
    t, mid, bid, ask = load_ticks()
    trades, counts = parse_ledger()
    # positions/reviews
    pos = {}
    for f in (V1 / "run_state" / "positions").glob("POS-*.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        ev = {e.get("event"): e.get("ts") for e in p.get("events", [])}
        pos[p.get("position_id")] = {"t_enter": ev.get("ENTER"), "t_exitfill": ev.get("EXIT_FILL"), "sl": p.get("initial_stop"), "tp": p.get("tp_levels")}
    rev = {}
    for f in (V1 / "memory" / "reviews").glob("RV-*.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        rev[r.get("plan_id")] = r
    # master table (filled)
    master = []
    for pid, tr in trades.items():
        if not tr.get("t_fill"):
            continue
        tid = tr.get("position_id") or pid
        rv = rev.get(pid, {})
        p_ = pos.get(tid, {})
        ts = ep(tr.get("t_signal")); tf = ep(tr.get("t_fill")); tx = ep(tr.get("t_exit"))
        hold_s = int((tx - tf) / 1000) if (tx and tf) else None
        # spread derivable at fill
        import bisect
        i = bisect.bisect_right(t, tf) - 1 if tf else None
        spread_bp = None
        if i is not None and i >= 0 and mid[i] > 0:
            spread_bp = round((ask[i] - bid[i]) / mid[i] * 1e4, 3)
        master.append({"trade_id": tid, "plan_id": pid, "position_id": tid, "direction": tr.get("direction"),
                       "T_signal": tr.get("t_signal"), "T_order": p_.get("t_enter"), "T_fill": tr.get("t_fill"),
                       "T_exit": tr.get("t_exit"), "size": tr.get("qty"), "entry_price": tr.get("fill_price"),
                       "exit_price": tr.get("exit_price"), "stop_loss": p_.get("sl") or tr.get("sl_plan"),
                       "take_profit": p_.get("tp") or tr.get("tp_plan"), "realized_usd": tr.get("realized_usd"),
                       "holding_s": hold_s, "slippage_bps": (rv.get("execution") or {}).get("slippage_bps"),
                       "spread_bp_derivable": spread_bp, "commission": "DATA_GAP", "swap": "DATA_GAP",
                       "close_reason": tr.get("close_reason"), "reconstruction": "OUTCOME_RECONSTRUCTABLE",
                       "final": ("WIN" if (tr.get("realized_usd") or 0) > 0 else ("LOSS" if tr.get("realized_usd") is not None else None))})
    master.sort(key=lambda x: x["T_exit"] or "")
    (AUDIT / "V1_TRADE_MASTER.jsonl").write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in master) + "\n", encoding="utf-8")

    # P&L series
    closed = [m for m in master if m["realized_usd"] is not None]
    closed.sort(key=lambda x: x["T_exit"])
    cum = 0; eq = []
    for m in closed:
        cum += m["realized_usd"]; eq.append(cum)
    peak = -1e18; dd = 0
    for v in eq:
        peak = max(peak, v); dd = min(dd, v - peak)
    daily = {}
    for m in closed:
        d = (m["T_exit"] or "")[:10]; daily[d] = round(daily.get(d, 0) + m["realized_usd"], 2)
    wins = [m["realized_usd"] for m in closed if m["realized_usd"] > 0]
    losses = [m["realized_usd"] for m in closed if m["realized_usd"] < 0]
    # streaks
    def streaks(seq):
        mx_w = mx_l = cw = cl = 0
        for m in seq:
            if m["realized_usd"] > 0:
                cw += 1; cl = 0
            elif m["realized_usd"] < 0:
                cl += 1; cw = 0
            mx_w = max(mx_w, cw); mx_l = max(mx_l, cl)
        # recent streak
        rec = 0
        for m in reversed(seq):
            if m["realized_usd"] < 0:
                rec += 1
            else:
                break
        return mx_w, mx_l, rec
    mw, ml, recent_loss_streak = streaks(closed)
    pnl = {"schema": "v1_pnl/1", "ts_utc": NOW, "n_closed": len(closed), "n_open": len(master) - len(closed),
           "total_realized_usd": round(sum(m["realized_usd"] for m in closed), 2),
           "win_n": len(wins), "loss_n": len(losses), "win_rate": round(len(wins) / max(1, len(closed)), 3),
           "profit_factor": round(sum(wins) / abs(sum(losses)), 3) if losses else None,
           "avg_win": round(st.mean(wins), 2) if wins else None, "avg_loss": round(st.mean(losses), 2) if losses else None,
           "expectancy": round(sum(m["realized_usd"] for m in closed) / max(1, len(closed)), 3),
           "max_drawdown_usd": round(dd, 2), "max_win_streak": mw, "max_loss_streak": ml,
           "recent_loss_streak": recent_loss_streak, "cumulative_curve": [round(v, 2) for v in eq],
           "daily_realized_usd": daily,
           "period_range": [closed[0]["T_exit"][:10] if closed else None, closed[-1]["T_exit"][:10] if closed else None],
           "TRUE_NET_STATUS": "DATA_GAP(commission/swap 未记录)", "OBSERVABLE_NET_USD": round(sum(m["realized_usd"] for m in closed), 2)}
    (AUDIT / "V1_PNL_SERIES.json").write_text(json.dumps(pnl, ensure_ascii=False, indent=1), encoding="utf-8")

    # periods: terciles by closed order + USER recent (last 7 days)
    n = len(closed)
    k1, k2 = n // 3, 2 * n // 3
    periods = {"early": closed[:k1], "mid": closed[k1:k2], "recent": closed[k2:]}
    last_day = closed[-1]["T_exit"][:10] if closed else None
    user_recent = [m for m in closed if (m["T_exit"] or "")[:10] >= "2026-09-10"]  # last ~7d before 09-17

    # directional per period
    def dir_stats(ms):
        out = {}
        for h in HOR:
            vals = []
            for m in ms:
                ts = ep(m["T_signal"]); 
                if not ts: continue
                i = np.searchsorted(t, ts, side="right") - 1
                if i < 0: continue
                j = np.searchsorted(t, ts + h, side="right") - 1
                if j < 0 or j <= i: continue
                if t[j] - t[i] > 3600_000: continue
                d = 1 if m["direction"] == "LONG" else (-1 if m["direction"] == "SHORT" else 0)
                vals.append(d * (mid[j] - mid[i]))
            if vals:
                arr = np.array(vals)
                out[str(h)] = {"n": len(vals), "mean": round(float(arr.mean()), 4), "median": round(float(np.median(arr)), 4),
                               "win_rate": round(float((arr > 0).mean()), 3)}
        return out
    dperiod = {"schema": "v1_directional_periods/1", "ts_utc": NOW, "seed": SEED,
               "all": dir_stats(closed), "early": dir_stats(periods["early"]), "mid": dir_stats(periods["mid"]),
               "recent": dir_stats(periods["recent"]), "user_recent_7d": dir_stats(user_recent),
               "periods_def": {"early": [periods['early'][0]['T_exit'][:10] if periods['early'] else None, periods['early'][-1]['T_exit'][:10] if periods['early'] else None],
                               "mid": [periods['mid'][0]['T_exit'][:10] if periods['mid'] else None, periods['mid'][-1]['T_exit'][:10] if periods['mid'] else None],
                               "recent": [periods['recent'][0]['T_exit'][:10] if periods['recent'] else None, periods['recent'][-1]['T_exit'][:10] if periods['recent'] else None],
                               "user_recent_7d": ">=2026-09-10 (USER_DEFINED_RECENT_PERIOD, 描述性)"}}
    (AUDIT / "V1_DIRECTIONAL_PERIODS.json").write_text(json.dumps(dperiod, ensure_ascii=False, indent=1), encoding="utf-8")

    # market regime per period (spread bp p50, tick rate /h, realized vol)
    def regime(ms):
        if not ms:
            return {}
        t0 = ep(ms[0]["T_signal"]); t1 = ep(ms[-1]["T_exit"]) or (t0 + 3600_000)
        a = np.searchsorted(t, t0); b = np.searchsorted(t, t1)
        seg_bid = bid[a:b]; seg_ask = ask[a:b]; seg_mid = mid[a:b]; seg_t = t[a:b]
        hrs = max(1e-9, (t1 - t0) / 3600_000)
        sp = (seg_ask - seg_bid) / np.maximum(seg_mid, 1e-9) * 1e4
        ret = np.diff(seg_mid) / np.maximum(seg_mid[:-1], 1e-9)
        return {"spread_bp_p50": round(float(np.median(sp)), 3), "spread_bp_p90": round(float(np.percentile(sp, 90)), 3),
                "ticks": int(len(seg_t)), "tick_rate_per_h": round(len(seg_t) / hrs, 1),
                "realized_vol_bp_per_tick": round(float(ret.std() * 1e4), 4) if len(ret) else None,
                "range_usd": round(float(seg_mid.max() - seg_mid.min()), 2) if len(seg_mid) else None}
    mreg = {"schema": "v1_market_regime/1", "ts_utc": NOW, "source": "A(live_fxtm)",
            "early": regime(periods["early"]), "mid": regime(periods["mid"]), "recent": regime(periods["recent"])}
    (AUDIT / "V1_MARKET_REGIME.json").write_text(json.dumps(mreg, ensure_ascii=False, indent=1), encoding="utf-8")

    # loss streak vs random baseline
    p = len(wins) / max(1, len(closed))
    rng = np.random.default_rng(SEED)
    seqlen = len(closed)
    sims = []
    for _ in range(5000):
        s = rng.random(seqlen) < p
        c = mx = 0
        for x in s:
            c = 0 if x else c + 1; mx = max(mx, c)
        sims.append(mx)
    sims = np.array(sims)
    lst = {"schema": "v1_loss_streak/1", "ts_utc": NOW, "seed": SEED, "n": seqlen, "win_rate_used": round(p, 3),
           "observed_max_loss_streak": ml, "observed_recent_loss_streak": recent_loss_streak,
           "random_max_loss_streak_p50": int(np.median(sims)), "random_p95": int(np.percentile(sims, 95)),
           "observed_percentile": round(float((sims <= ml).mean()) * 100, 1),
           "verdict": "WITHIN_RANDOM_RANGE" if (sims <= ml).mean() < 0.95 else "EXCEEDS_RANDOM"}
    (AUDIT / "V1_LOSS_STREAK.json").write_text(json.dumps(lst, ensure_ascii=False, indent=1), encoding="utf-8")

    # timeline
    tl = {"schema": "v1_lifecycle_timeline/1", "ts_utc": NOW,
          "counts": counts, "n_filled": len(master), "n_closed": len(closed),
          "first_decision": None, "first_trade": closed[0]["T_fill"] if closed else None,
          "last_trade": closed[-1]["T_exit"] if closed else None,
          "by_day": {d: {"n": sum(1 for m in closed if (m["T_exit"] or "")[:10] == d),
                         "net": round(daily.get(d, 0), 2)} for d in sorted(daily)},
          "direction_counts": {"LONG": sum(1 for m in master if m["direction"] == "LONG"),
                               "SHORT": sum(1 for m in master if m["direction"] == "SHORT")}}
    (AUDIT / "V1_LIFECYCLE_TIMELINE.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")

    # data registry (lifecycle scan)
    reg = {"schema": "v1_lifecycle_data_registry/1", "ts_utc": NOW, "assets": []}
    def add(path, src, cls, used):
        p = Path(path)
        if p.is_file():
            reg["assets"].append({"path": str(p), "source": src, "class": cls, "used_by_v1": used,
                                  "sha256": sha(p), "bytes": p.stat().st_size})
    for nm, cls, used in [("run_state/plan_ledger.jsonl", "C", True), ("run_state/statistics.json", "C", True),
                          ("run_state/trader_summary.txt", "B", True), ("run_state/workflow_history.jsonl", "B", True),
                          ("run_state/state_package_latest.json", "E", False), ("memory/reviews", "C", True)]:
        pp = V1 / nm
        if pp.is_dir():
            reg["assets"].append({"path": str(pp), "source": "V1", "class": cls, "used_by_v1": used, "file_count": len(list(pp.glob('*')))})
        else:
            add(pp, "V1", cls, used)
    for nm, cls, used in [("run_state/decisions", "B", True), ("run_state/positions", "B", True)]:
        pp = V1 / nm
        if pp.is_dir():
            reg["assets"].append({"path": str(pp), "source": "V1", "class": cls, "used_by_v1": used, "file_count": len(list(pp.glob('*')))})
    for d, src, cls in [(TICKS, "V1 collector", "A/D"), (DATA / "staging_mt5", "collector", "D"), (DATA / "staging_fxtm", "collector", "D")]:
        if d.exists():
            fs = list(d.glob("*.parquet"))
            reg["assets"].append({"path": str(d), "source": src, "class": cls, "used_by_v1": False, "file_count": len(fs)})
    reg["state_history"] = "无历史 state snapshot（仅 latest）→ class E / DATA_GAP"
    (AUDIT / "V1_LIFECYCLE_DATA_REGISTRY.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({"counts": counts, "n_master": len(master), "n_closed": len(closed),
                      "total_usd": pnl["total_realized_usd"], "win_rate": pnl["win_rate"], "PF": pnl["profit_factor"],
                      "maxDD": pnl["max_drawdown_usd"], "max_loss_streak": ml, "recent_loss_streak": recent_loss_streak,
                      "loss_streak_verdict": lst["verdict"],
                      "daily": daily,
                      "dir_all_2s": dperiod["all"].get("2000"), "dir_recent_2s": dperiod["recent"].get("2000"),
                      "dir_recent_30s": dperiod["recent"].get("30000")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
