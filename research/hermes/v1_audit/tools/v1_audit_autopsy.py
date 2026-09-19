# -*- coding: utf-8 -*-
"""V1 逐笔尸检 + 早期/近期路径对照（只读；不优化；无订单）。

产出 §十九 全部文件。阈值 MFE∈{0,0.5,1,2} USD/oz 为**预注册描述阈值**。
"""
from __future__ import annotations
import hashlib
import json
import statistics as st
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

AUDIT = Path(r"C:\AIQuant\research\hermes\v1_audit")
TICKS = Path(r"C:\AIQuant\data\live_fxtm")
NOW = datetime.now(timezone.utc).isoformat()
HOR = [1000, 2000, 5000, 10000, 30000, 60000, 180000, 300000, 900000]
MFE_TH = [0, 0.5, 1, 2]
EARLY = ("2026-09-08", "2026-09-14")
RECENT = ("2026-09-15", "2026-09-17")


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


def main():
    fr = [pd.read_parquet(f, columns=["time_msc", "bid", "ask"]) for f in sorted(TICKS.glob("ticks_*.parquet"))]
    d = pd.concat(fr, ignore_index=True).sort_values("time_msc")
    t = d["time_msc"].to_numpy(); bid = d["bid"].to_numpy(); ask = d["ask"].to_numpy(); mid = (bid + ask) / 2.0

    master = [json.loads(x) for x in (AUDIT / "V1_TRADE_MASTER.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = []
    for m in master:
        d_ = 1 if m["direction"] == "LONG" else (-1 if m["direction"] == "SHORT" else 0)
        ts = ep(m["T_signal"]); tx = ep(m["T_exit"]); tf = ep(m["T_fill"])
        e = {"trade_id": m["trade_id"], "direction": m["direction"], "realized": m.get("realized_usd"),
             "final": ("WIN" if (m.get("realized_usd") or 0) > 0 else ("LOSS" if m.get("realized_usd") is not None else None)),
             "T_signal": m["T_signal"], "T_exit": m["T_exit"], "holding_s": m.get("holding_s"),
             "horizons": {}, "mfe": None, "mae": None, "tt_mfe_ms": None, "tt_mae_ms": None, "coverage": "OK"}
        i = np.searchsorted(t, ts, side="right") - 1 if ts else -1
        if i < 0:
            e["coverage"] = "DATA_GAP"; e["path_class"] = ["DATA_GAP"]; rows.append(e); continue
        ref = mid[i]
        for h in HOR:
            j = np.searchsorted(t, ts + h, side="right") - 1
            if j <= i or (t[j] - t[i]) > 3600_000:
                e["horizons"][str(h)] = None; continue
            e["horizons"][str(h)] = round(float(d_ * (mid[j] - ref)), 4)
        end = min(tx if tx else ts + 900000, ts + 900000)
        a = np.searchsorted(t, ts); b = np.searchsorted(t, end)
        seg = mid[a:b]
        if len(seg) and d_:
            fav = d_ * (seg - ref)
            e["mfe"] = round(float(fav.max()), 4); e["mae"] = round(float(fav.min()), 4)
            e["tt_mfe_ms"] = int(t[a + int(fav.argmax())] - ts); e["tt_mae_ms"] = int(t[a + int(fav.argmin())] - ts)
        # path class
        d1, d2, d5 = e["horizons"].get("1000"), e["horizons"].get("2000"), e["horizons"].get("5000")
        d30, d60 = e["horizons"].get("30000"), e["horizons"].get("60000")
        labs = []
        if None in (d1, d2, d5):
            labs.append("DATA_GAP")
        else:
            if d1 < 0 and d2 < 0 and d5 < 0:
                labs.append("ENTRY_WRONG_PATH")
            if d1 > 0 and d2 > 0 and d5 > 0 and ((d30 is not None and d30 < 0) or (d60 is not None and d60 < 0)):
                labs.append("ENTRY_RIGHT_THEN_REVERSED")
            if e["mfe"] is not None and e["mfe"] > 0.5 and (m.get("realized_usd") or 0) < 0:
                labs.append("PROFIT_AVAILABLE_BUT_NOT_REALIZED")
            if d1 <= 0 or d2 <= 0 or d5 <= 0:
                if abs(d1) < 0.1 and abs(d5) < 0.15:
                    labs.append("NO_CLEAR_ENTRY_EDGE")
        if not labs:
            labs.append("NO_CLEAR_ENTRY_EDGE")
        e["path_class"] = labs
        rows.append(e)
    (AUDIT / "V1_TRADE_AUTOPSY.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    def period(r):
        d = (r["T_exit"] or "")[:10]
        return "EARLY" if EARLY[0] <= d <= EARLY[1] else ("RECENT" if RECENT[0] <= d <= RECENT[1] else "OTHER")

    def agg(rs):
        cl = [x for x in rs if x.get("realized") is not None]
        wins = [x for x in cl if x["realized"] > 0]; losses = [x for x in cl if x["realized"] < 0]
        mfes = [x["mfe"] for x in cl if x.get("mfe") is not None]
        maes = [x["mae"] for x in cl if x.get("mae") is not None]
        holds = [x["holding_s"] for x in cl if x.get("holding_s") is not None]
        from collections import Counter
        cls = Counter()
        for x in cl:
            for l in x.get("path_class", []):
                cls[l] += 1
        return {"trades": len(cl), "wins": len(wins), "losses": len(losses),
                "win_rate": round(len(wins) / max(1, len(cl)), 3),
                "pnl_total": round(sum(x["realized"] for x in cl), 2),
                "avg_pnl": round(st.mean([x["realized"] for x in cl]), 3) if cl else None,
                "median_pnl": round(st.median([x["realized"] for x in cl]), 3) if cl else None,
                "avg_mfe": round(st.mean(mfes), 3) if mfes else None, "avg_mae": round(st.mean(maes), 3) if maes else None,
                "mfe_gt0_n": sum(1 for v in mfes if v > 0), "mfe_gt0_pct": round(sum(1 for v in mfes if v > 0) / max(1, len(mfes)), 3),
                "mfe_gt0_but_loss": sum(1 for x in cl if (x.get("mfe") or 0) > 0 and x["realized"] < 0),
                "avg_hold_s": round(st.mean(holds), 1) if holds else None, "median_hold_s": round(st.median(holds), 1) if holds else None,
                "path_class_counts": dict(cls)}
    early = [r for r in rows if period(r) == "EARLY"]; recent = [r for r in rows if period(r) == "RECENT"]
    comp = {"schema": "v1_early_recent/1", "ts_utc": NOW, "periods": {"EARLY": EARLY, "RECENT": RECENT},
            "EARLY": agg(early), "RECENT": agg(recent),
            "mfe_thresholds_preregistered": MFE_TH}
    (AUDIT / "V1_EARLY_RECENT_PATH_COMPARISON.json").write_text(json.dumps(comp, ensure_ascii=False, indent=1), encoding="utf-8")

    # loss autopsy
    losses = [r for r in rows if r.get("final") == "LOSS"]
    la = {"schema": "v1_loss_autopsy/1", "ts_utc": NOW, "n_loss": len(losses),
          "losses_with_mfe_gt": {str(th): sum(1 for x in losses if (x.get("mfe") or -9) > th) for th in MFE_TH},
          "losses_with_mfe_gt_pct": {str(th): round(sum(1 for x in losses if (x.get("mfe") or -9) > th) / max(1, len(losses)), 3) for th in MFE_TH},
          "losses_mfe_gt0_but_final_loss": sum(1 for x in losses if (x.get("mfe") or 0) > 0),
          "detail": losses}
    (AUDIT / "V1_LOSS_TRADE_AUTOPSY.json").write_text(json.dumps(la, ensure_ascii=False, indent=1), encoding="utf-8")

    # recent 3 days
    r3 = {}
    for day in ("2026-09-15", "2026-09-16", "2026-09-17"):
        r3[day] = [{"trade_id": x["trade_id"], "direction": x["direction"], "entry": None, "exit": None,
                    "pnl": x["realized"], "mfe": x["mfe"], "mae": x["mae"], "holding_s": x.get("holding_s"),
                    **{f"d{k}": x["horizons"].get(str(k)) for k in HOR}, "path_class": x["path_class"]}
                   for x in rows if (x["T_exit"] or "").startswith(day)]
    (AUDIT / "V1_RECENT_3DAY_AUTOPSY.json").write_text(json.dumps({"schema": "v1_recent3d/1", "ts_utc": NOW, "days": r3}, ensure_ascii=False, indent=1), encoding="utf-8")

    # entry vs exit evidence
    def short_stats(rs):
        return {"n": len(rs), "win_rate": round(sum(1 for x in rs if (x.get("realized") or 0) > 0) / max(1, len(rs)), 3),
                "pnl": round(sum((x.get("realized") or 0) for x in rs), 2),
                "avg_mfe": round(st.mean([x["mfe"] for x in rs if x.get("mfe") is not None] or [0]), 3)}
    ev = {"schema": "v1_entry_vs_exit/1", "ts_utc": NOW,
          "shorts_early": short_stats([r for r in early if r["direction"] == "SHORT"]),
          "shorts_recent": short_stats([r for r in recent if r["direction"] == "SHORT"]),
          "longs_total": short_stats([r for r in rows if r["direction"] == "LONG"]),
          "recent_entry_not_obviously_deteriorated": None, "note": "见 report"}
    ev["recent_entry_not_obviously_deteriorated"] = (
        (agg(recent)["path_class_counts"].get("ENTRY_WRONG_PATH", 0) <= agg(early)["path_class_counts"].get("ENTRY_WRONG_PATH", 0)))
    (AUDIT / "V1_ENTRY_VS_EXIT_EVIDENCE.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")

    # experiment registry update
    reg = json.loads((AUDIT / "V1_AUDIT_EXPERIMENT_REGISTRY.json").read_text(encoding="utf-8"))
    fam = "E_AUTOPSY"
    reg.setdefault("families", {})
    reg["families"][fam] = {"note": "逐笔尸检/早期-近期对照（描述统计为主）", "registered": ["autopsy_path_class", "early_vs_recent", "loss_mfe", "recent3d", "entry_vs_exit"]}
    (AUDIT / "V1_AUDIT_EXPERIMENT_REGISTRY.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({"EARLY": comp["EARLY"], "RECENT": comp["RECENT"],
                      "losses_with_mfe_gt0": la["losses_mfe_gt0_but_final_loss"],
                      "loss_mfe_gt": la["losses_with_mfe_gt_pct"],
                      "shorts_early": ev["shorts_early"], "shorts_recent": ev["shorts_recent"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
