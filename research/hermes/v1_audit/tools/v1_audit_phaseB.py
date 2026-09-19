# -*- coding: utf-8 -*-
"""V1 审计 PHASE B — 时间对齐 + 行情覆盖审计（只读；不计算 Alpha）。

产出:
  V1_TRADE_REPLAY.jsonl        逐笔时间对齐 + 覆盖
  V1_COVERAGE_MATRIX.csv       覆盖矩阵
  V1_TICK_QUALITY.json         live_fxtm tick 质量
  V1_AUDIT_PHASE_B_REPORT.md
"""
from __future__ import annotations
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

V1 = Path(r"C:\AIQuant\research\hermes\trader_v1")
AUDIT = Path(r"C:\AIQuant\research\hermes\v1_audit")
TICKS = Path(r"C:\AIQuant\data\live_fxtm")
NOW = datetime.now(timezone.utc).isoformat()


def ep(ts_str):
    if not ts_str:
        return None
    try:
        return int(datetime.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp() * 1000)
    except Exception:  # noqa: BLE001
        m = re.search(r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})", str(ts_str))
        if m:
            y, mo, d, h, mi, s = map(int, m.groups())
            return int(datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc).timestamp() * 1000)
    return None


def load_ticks():
    frames = []
    for f in sorted(TICKS.glob("ticks_*.parquet")):
        df = pd.read_parquet(f, columns=["time_msc", "bid", "ask"])
        frames.append((f.name, df))
    allt = pd.concat([d for _, d in frames], ignore_index=True)
    allt = allt.sort_values("time_msc")
    return frames, allt


def tick_quality(frames):
    out = {"files": [], "total_rows": 0}
    for name, df in frames:
        t = df["time_msc"].to_numpy()
        bid = df["bid"].to_numpy(); ask = df["ask"].to_numpy()
        dt = t[1:] - t[:-1]
        gaps = dt[dt > 60_000]
        out["files"].append({
            "file": name, "rows": int(len(df)), "dup_ts": int((dt == 0).sum()),
            "nonmonotonic": int((dt < 0).sum()), "same_ts_multi": int((dt == 0).sum()),
            "ask_lt_bid": int((ask < bid).sum()), "zero_price": int(((bid <= 0) | (ask <= 0)).sum()),
            "min_ms": int(t.min()), "max_ms": int(t.max()),
            "gap_gt_60s_n": int(len(gaps)), "gap_gt_60s_max_ms": int(gaps.max()) if len(gaps) else 0,
            "interval_p50_ms": float(pd.Series(dt[dt > 0]).median()) if (dt > 0).any() else None})
        out["total_rows"] += int(len(df))
    return out


def nearest(allt_t, ts_ms):
    if ts_ms is None:
        return None
    import bisect
    i = bisect.bisect_left(allt_t, ts_ms)
    cands = []
    if i < len(allt_t):
        cands.append(int(allt_t[i]))
    if i > 0:
        cands.append(int(allt_t[i - 1]))
    if not cands:
        return None
    best = min(cands, key=lambda x: abs(x - ts_ms))
    return {"tick_ms": best, "delta_ms": int(abs(best - ts_ms)), "side": ("exact" if best == ts_ms else ("after" if best > ts_ms else "before"))}


def coverage(allt_t, t0, t1):
    if t0 is None or t1 is None or t1 < t0:
        return {"n": 0, "covered": False, "max_gap_ms": None}
    import numpy as np
    a = np.searchsorted(allt_t, t0); b = np.searchsorted(allt_t, t1)
    seg = allt_t[a:b]
    if len(seg) == 0:
        return {"n": 0, "covered": False, "max_gap_ms": None}
    gaps = np.diff(seg)
    return {"n": int(len(seg)), "covered": True, "max_gap_ms": int(gaps.max()) if len(gaps) else 0}


def parse_ledger():
    trades = {}
    for ln in (V1 / "run_state" / "plan_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        o = json.loads(ln)
        pid = o.get("plan_id")
        if not pid:
            continue
        t = trades.setdefault(pid, {"plan_id": pid})
        ty = o.get("type")
        if ty == "registered":
            t["direction"] = (o.get("decision") or (o.get("plan") or {}).get("direction"))
            t["t_signal"] = o.get("utc_ts") or ep(pid)
            t["signal_src"] = "registered.utc_ts" if o.get("utc_ts") else "plan_id_parse"
        elif ty == "filled":
            t["t_fill"] = o.get("utc_ts"); t["fill_price"] = o.get("price"); t["position_id"] = o.get("position_id")
        elif ty == "closed":
            t["t_exit"] = o.get("utc_ts"); t["exit_price"] = o.get("exit_price"); t["close_reason"] = o.get("reason")
            t["realized_usd"] = o.get("realized_usd")
    return [t for t in trades.values() if t.get("t_fill")]


def main():
    frames, allt = load_ticks()
    allt_t = allt["time_msc"].to_numpy()
    q = tick_quality(frames)
    trades = parse_ledger()
    rows = []
    for t in trades:
        ts = ep(t.get("t_signal")); tf = ep(t.get("t_fill")); tx = ep(t.get("t_exit"))
        n_s = nearest(allt_t, ts); n_f = nearest(allt_t, tf); n_x = nearest(allt_t, tx)
        c_pre = coverage(allt_t, (ts - 60_000) if ts else None, ts)
        c_sf = coverage(allt_t, ts, tf)
        c_fe = coverage(allt_t, tf, tx)
        deltas = [d["delta_ms"] for d in (n_s, n_f, n_x) if d]
        max_delta = max(deltas) if deltas else None
        future_risk = any((d and d["side"] == "after" and d["delta_ms"] > 60_000) for d in (n_s,))
        if ts is None or tf is None or tx is None:
            status = "UNRESOLVABLE"
        elif not (c_sf["covered"] or c_fe["covered"]):
            status = "DATA_GAP"
        elif c_pre["covered"] and c_sf["covered"] and c_fe["covered"]:
            status = "PASS"
        else:
            status = "PARTIAL"
        rows.append({"trade_id": t.get("position_id") or t["plan_id"], "plan_id": t["plan_id"],
                     "direction": t.get("direction"), "t_signal": t.get("t_signal"), "t_fill": t.get("t_fill"),
                     "t_exit": t.get("t_exit"), "fill_price": t.get("fill_price"), "exit_price": t.get("exit_price"),
                     "close_reason": t.get("close_reason"), "realized_usd": t.get("realized_usd"),
                     "align_signal": n_s, "align_fill": n_f, "align_exit": n_x, "max_delta_ms": max_delta,
                     "future_info_risk_at_signal": future_risk,
                     "coverage_before_signal": c_pre, "coverage_signal_to_fill": c_sf, "coverage_fill_to_exit": c_fe,
                     "status": status, "data_source_A_v1_own": "live_fxtm (V1 collector, actual)", "source_class": "A"})
    with open(AUDIT / "V1_TRADE_REPLAY.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(AUDIT / "V1_COVERAGE_MATRIX.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trade_id", "signal", "order", "fill", "exit", "tick_before", "tick_at/after", "max_delta_ms", "status"])
        for r in rows:
            w.writerow([r["trade_id"], r["t_signal"], "", r["t_fill"], r["t_exit"],
                        (r["coverage_before_signal"] or {}).get("n"), (r["align_fill"] or {}).get("delta_ms"),
                        r["max_delta_ms"], r["status"]])
    from collections import Counter
    st = Counter(r["status"] for r in rows)
    # 09-11→09-13 空档检查：看该时段是否有 tick
    g_start = ep("2026-09-11T00:00:00Z"); g_end = ep("2026-09-14T02:00:00Z")
    import numpy as np
    a = np.searchsorted(allt_t, g_start); b = np.searchsorted(allt_t, g_end)
    gap_n = int(b - a); gap_seg = allt_t[a:b]
    gmax = int(np.diff(gap_seg).max()) if len(gap_seg) > 1 else None
    affected = [r["trade_id"] for r in rows if (ep(r["t_fill"] or "") or 0) >= g_start and (ep(r["t_fill"] or "") or 0) < g_end]
    summary = {"schema": "v1_phaseB/1", "ts_utc": NOW, "n_trades": len(rows), "status_counts": dict(st),
               "tick_quality": q, "gap_0911_0913": {"ticks_in_window": gap_n, "max_gap_ms": gmax,
                                                    "weekend_gap": True, "affected_trades": affected,
                                                    "verdict": ("GAP_WEEKEND" if (gmax or 0) > 6 * 3600 * 1000 else ("NO_GAP" if (gmax or 0) < 3600 * 1000 else "GAP_INTRADAY"))},
               "decision_input_snapshot": "decisions/*.json 仅含 state_summary(文本) 且 state_package 仅 latest → "
                                          "历史交易时刻的完整可见输入 = DATA_GAP（不得用 latest 解释历史）",
               "source_identity": {"A_v1_own": "data/live_fxtm/ticks_*.parquet (V1 collector 当时保存)",
                                   "B_v1_mt5_terminal": "Program Files FXTM 终端可读历史（未在本阶段使用）",
                                   "C_alternate": "data/staging_mt5, staging_fxtm（未使用）"}}
    (AUDIT / "V1_TICK_QUALITY.json").write_text(json.dumps({"files": q["files"], "total_rows": q["total_rows"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    (AUDIT / "V1_AUDIT_PHASE_B_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"trades": len(rows), "status": dict(st), "gap_ticks": gap_n, "gap_max_ms": gmax,
                      "affected": len(affected)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
