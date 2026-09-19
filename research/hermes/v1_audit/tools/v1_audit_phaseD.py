# -*- coding: utf-8 -*-
"""V1 审计 PHASE D — 逐笔真实行情 OUTCOME 重放（只读；不做 Alpha 结论）。

源 A = data/live_fxtm ticks。锚点 T_signal。产出 §十六 全部文件 + 更新两 Registry。
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
TICKS = Path(r"C:\AIQuant\data\live_fxtm")
NOW = datetime.now(timezone.utc).isoformat()
HORIZONS = [1000, 2000, 5000, 10000, 30000, 60000, 180000, 300000, 900000]
GAP_MAX_MS = 60_000
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


def load():
    fr = [pd.read_parquet(f, columns=["time_msc", "bid", "ask"]) for f in sorted(TICKS.glob("ticks_*.parquet"))]
    d = pd.concat(fr, ignore_index=True).sort_values("time_msc")
    return d["time_msc"].to_numpy(), ((d["bid"].to_numpy() + d["ask"].to_numpy()) / 2.0)


def seg_ok(t, a, b):
    """[a,b] 内是否有 tick 且无 >GAP 缺口。返回 (ok, n, maxgap)."""
    i = np.searchsorted(t, a); j = np.searchsorted(t, b)
    seg = t[i:j]
    if len(seg) == 0:
        return False, 0, None
    mg = int(np.diff(seg).max()) if len(seg) > 1 else 0
    # 端点缺口：a→首tick, 末tick→b
    mg = max(mg, int(seg[0] - a), int(b - seg[-1]))
    return (mg <= GAP_MAX_MS and len(seg) > 0), int(len(seg)), mg


def last_le(t, x):
    i = np.searchsorted(t, x, side="right") - 1
    return i if i >= 0 else None


def main():
    t, mid = load()
    replay = [json.loads(x) for x in (AUDIT / "V1_TRADE_REPLAY.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    elig = {e["trade_id"]: e for e in json.loads((AUDIT / "V1_ANALYSIS_ELIGIBILITY.json").read_text(encoding="utf-8"))["trades"]}
    rows = []
    rng = np.random.default_rng(SEED)
    for r in replay:
        tid = r["trade_id"]; d = 1 if (r.get("direction") == "LONG") else (-1 if r.get("direction") == "SHORT" else 0)
        ts = ep(r.get("t_signal")); tx = ep(r.get("t_exit"))
        e = {"trade_id": tid, "direction": r.get("direction"), "dir": d, "t_signal": r.get("t_signal"),
             "final_usd": r.get("realized_usd"), "final": ("WIN" if (r.get("realized_usd") or 0) > 0 else ("LOSS" if (r.get("realized_usd") or 0) is not None else None)),
             "horizons": {}, "mfe": None, "mae": None, "time_to_mfe_ms": None, "time_to_mae_ms": None,
             "entry_ref_ts": None, "entry_ref_mid": None}
        i = last_le(t, ts) if ts else None
        if i is None:
            e["entry_gap"] = "DATA_GAP(no tick <= T_signal)"
        else:
            e["entry_ref_ts"] = int(t[i]); e["entry_ref_mid"] = float(mid[i])
            for h in HORIZONS:
                target = ts + h
                ok, n, mg = seg_ok(t, e["entry_ref_ts"], target)
                j = last_le(t, target)
                if (not ok) or j is None or j < i:
                    e["horizons"][str(h)] = {"status": "DATA_GAP"}
                    continue
                fmid = float(mid[j])
                raw = fmid - e["entry_ref_mid"]
                e["horizons"][str(h)] = {"status": "OK", "future_mid": fmid, "raw_return": raw,
                                         "directional_return": d * raw, "tick_ms": int(t[j])}
            # MFE/MAE over [signal, exit or +900s]
            end = tx if tx else (ts + 900000)
            ok, n, mg = seg_ok(t, e["entry_ref_ts"], min(end, ts + 900000))
            a = np.searchsorted(t, e["entry_ref_ts"]); b = np.searchsorted(t, min(end, ts + 900000))
            seg = mid[a:b]
            if len(seg) and d:
                fav = d * (seg - e["entry_ref_mid"])
                e["mfe"] = float(fav.max()); e["mae"] = float(fav.min())
                e["time_to_mfe_ms"] = int(t[a + int(fav.argmax())] - ts)
                e["time_to_mae_ms"] = int(t[a + int(fav.argmin())] - ts)
        rows.append(e)
    # baseline: reverse = -directional
    for e in rows:
        for h, v in e["horizons"].items():
            if v.get("status") == "OK":
                v["rev_directional_return"] = -v["directional_return"]
                v["rand_directional_return"] = (1 if rng.random() < 0.5 else -1) * v["raw_return"]
    (AUDIT / "V1_MFE_MAE.jsonl").write_text("\n".join(json.dumps({k: e[k] for k in
        ("trade_id", "direction", "mfe", "mae", "time_to_mfe_ms", "time_to_mae_ms", "final")}, ensure_ascii=False) for e in rows) + "\n", encoding="utf-8")

    # 重新写 V1_TRADE_REPLAY.jsonl（含 horizon 结果）—— 备份旧的是 phaseB 版
    (AUDIT / "V1_TRADE_REPLAY_PHASE_D.jsonl").write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in rows) + "\n", encoding="utf-8")

    def stats(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return {"n": 0}
        arr = np.array(vals)
        # permutation sign-flip p (mean!=0)
        rng2 = np.random.default_rng(SEED)
        obs = arr.mean(); cnt = 0
        for _ in range(2000):
            s = (rng2.random(len(arr)) < 0.5) * 2 - 1
            if abs((arr * s).mean()) >= abs(obs):
                cnt += 1
        return {"n": len(vals), "mean_bp_of_usd_raw": round(float(np.mean(vals)), 4),
                "median": round(float(np.median(arr)), 4), "win_rate": round(float((arr > 0).mean()), 3),
                "perm_p_two_sided": round((cnt + 1) / 2001, 4)}
    out = {"schema": "v1_outcome_analysis/1", "ts_utc": NOW, "source": "A(live_fxtm)",
           "entry_reference_rule": "T_signal 时刻最后一个 <= T_signal 的 tick (mid)",
           "gap_rule": f"区间内 >{GAP_MAX_MS/1000:.0f}s 缺口 -> DATA_GAP（不插值）",
           "by_horizon": {}, "raw_N": len(rows),
           "gap_note": "未使用 T_signal 之后 tick 作为 entry reference"}
    for h in HORIZONS:
        dr = [e["horizons"][str(h)].get("directional_return") for e in rows if e["horizons"].get(str(h), {}).get("status") == "OK"]
        rv = [e["horizons"][str(h)].get("rev_directional_return") for e in rows if e["horizons"].get(str(h), {}).get("status") == "OK"]
        rd = [e["horizons"][str(h)].get("rand_directional_return") for e in rows if e["horizons"].get(str(h), {}).get("status") == "OK"]
        out["by_horizon"][str(h)] = {"computable": len(dr), "v1": stats(dr), "reverse": stats(rv), "random": stats(rd)}
    # LONG/SHORT
    for side in ("LONG", "SHORT"):
        sub = [e for e in rows if e["direction"] == side]
        out[f"side_{side}"] = {"n": len(sub)}
        for h in (2000, 30000, 180000, 900000):
            dr = [e["horizons"][str(h)].get("directional_return") for e in sub if e["horizons"].get(str(h), {}).get("status") == "OK"]
            out[f"side_{side}"][str(h)] = stats(dr)
    # WIN/LOSS
    for f in ("WIN", "LOSS"):
        sub = [e for e in rows if e["final"] == f]
        out[f"final_{f}"] = {"n": len(sub)}
        for h in (1000, 2000, 5000, 10000, 30000, 60000, 180000, 300000, 900000):
            dr = [e["horizons"][str(h)].get("directional_return") for e in sub if e["horizons"].get(str(h), {}).get("status") == "OK"]
            out[f"final_{f}"][str(h)] = stats(dr)
    (AUDIT / "V1_OUTCOME_ANALYSIS.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    base = {"schema": "v1_baseline/1", "ts_utc": NOW, "seed": SEED,
            "baselines": ["A_v1_actual", "B_reverse", "C_random(fixed seed)"],
            "note": "baseline 只为对照，不用于优化；seed 固定不可改",
            "summary": {str(h): {"v1_mean": out["by_horizon"][str(h)]["v1"].get("mean_bp_of_usd_raw"),
                                 "reverse_mean": out["by_horizon"][str(h)]["reverse"].get("mean_bp_of_usd_raw"),
                                 "random_mean": out["by_horizon"][str(h)]["random"].get("mean_bp_of_usd_raw")} for h in HORIZONS}}
    (AUDIT / "V1_BASELINE_ANALYSIS.json").write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")

    cost = {"schema": "v1_cost/1", "ts_utc": NOW,
            "OBSERVABLE_NET": "review.realized.pnl_usd（仅含已记录 slippage）",
            "TRUE_NET_STATUS": "DATA_GAP（commission/swap 未记录，禁默认0）",
            "cost_fields": {"slippage": "RECORDED", "spread_at_entry": "DERIVABLE_NOT_RECORDED",
                            "commission": "DATA_GAP", "swap": "DATA_GAP"},
            "stress_ladder": [0, 0.5, 1, 1.5, 2, 3],
            "note": "压力分析仅为敏感性，不代表真实净收益"}
    (AUDIT / "V1_COST_ANALYSIS.json").write_text(json.dumps(cost, ensure_ascii=False, indent=1), encoding="utf-8")

    # registries
    exps = []
    fam = "D_PRICE_PATH"
    for h in HORIZONS:
        exps.append({"experiment_id": f"D_H{h}", "family": fam, "hypothesis": f"V1 方向在 {h}ms horizon 有非零 directional return",
                     "population": "OUTCOME_RECONSTRUCTABLE(53)", "horizon_ms": h, "status": "RUN_OBSERVED"})
    exps += [{"experiment_id": "D_longshort", "family": fam, "status": "RUN_OBSERVED"},
             {"experiment_id": "D_winloss", "family": fam, "status": "RUN_OBSERVED"},
             {"experiment_id": "D_baseline", "family": fam, "status": "RUN_OBSERVED"}]
    (AUDIT / "V1_AUDIT_EXPERIMENT_REGISTRY.json").write_text(json.dumps(
        {"schema": "v1_exp_registry/1", "ts_utc": NOW, "multiple_testing_family": fam,
         "family_size": len(exps), "note": "horizon/side/winloss/baseline 全部登记；主 horizon 不得事后挑选",
         "experiments": exps}, ensure_ascii=False, indent=1), encoding="utf-8")
    # data registry update
    dr = json.loads((AUDIT / "V1_AUDIT_DATA_REGISTRY.json").read_text(encoding="utf-8"))
    dr.setdefault("phaseD_outputs", {})
    for f in ("V1_TRADE_REPLAY_PHASE_D.jsonl", "V1_OUTCOME_ANALYSIS.json", "V1_MFE_MAE.jsonl",
              "V1_BASELINE_ANALYSIS.json", "V1_COST_ANALYSIS.json"):
        dr["phaseD_outputs"][f] = sha(AUDIT / f)
    (AUDIT / "V1_AUDIT_DATA_REGISTRY.json").write_text(json.dumps(dr, ensure_ascii=False, indent=1), encoding="utf-8")

    comp = {str(h): out["by_horizon"][str(h)]["computable"] for h in HORIZONS}
    print(json.dumps({"raw_N": len(rows), "computable": comp,
                      "v1_mean_2s": out["by_horizon"]["2000"]["v1"], "v1_mean_30s": out["by_horizon"]["30000"]["v1"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
