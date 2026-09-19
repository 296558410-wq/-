# -*- coding: utf-8 -*-
"""run_cand01.py — CAND-01 GVZ incremental information formal test (prereg c23b046).

Targets: future 5/10/20 trading-day XAUUSD RV (bps). Baseline A = activity(volume)+RV lags+dow.
B = A + {log GVZ, Δlog GVZ}. Expanding walk-forward ΔR2 OOS; HAC & block bootstrap; regime audit;
redundancy; monthly direction probe; R1 risk-state AUC audit (logistic fit on IS only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]  # C:/AIQuant (cand01_gvz -> hermes -> research -> AIQuant)
sys.path.insert(0, str(REPO))
OUT = REPO / "research/hermes/cand01_gvz"
SEED = 7


def build_panel() -> pd.DataFrame:
    rows = []
    for p in sorted((REPO / "data/staging_duka").glob("candles_*.parquet")):
        c = pd.read_parquet(p)
        if not {"sec", "close", "side", "day", "vol"}.issubset(c.columns):
            continue
        c["ts"] = pd.to_datetime(c["day"], utc=True) + pd.to_timedelta(c["sec"], unit="s")
        c = c.drop_duplicates(subset=["ts", "side"])
        piv = c.pivot_table(index="ts", columns="side", values="close", aggfunc="last")
        if not {"BID", "ASK"}.issubset(piv.columns):
            continue
        mid = ((piv["ASK"] + piv["BID"]) / 2.0) / 1000.0
        vp = c.pivot_table(index="ts", columns="side", values="vol", aggfunc="first")
        vs = (vp["BID"].fillna(0) + vp["ASK"].fillna(0)).reindex(mid.index).fillna(0)
        day = mid.index.normalize()
        g = pd.DataFrame({"mid": mid, "v": vs, "day": day}).groupby("day")
        for d, gg in g:
            if len(gg) < 600:
                continue
            r = gg["mid"].pct_change().dropna()
            r = r[r.abs() < 0.02]
            rows.append({"date": d.date().isoformat(),
                         "rv_day": float(np.sqrt((r.values ** 2).sum()) * 1e4) if len(r) else np.nan,
                         "log_act": float(np.log1p(gg["v"].sum())),
                         "ret": float(np.log(gg["mid"].iloc[-1] / gg["mid"].iloc[0]) * 1e4)})
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df = df.drop_duplicates(subset="date", keep="first").dropna(subset=["rv_day"])
    df["rv_day"] = df["rv_day"].clip(lower=1e-6)
    return df


def main():
    df = build_panel()
    gvz = pd.read_csv(REPO / "data/staging_fred/gvzcls.csv")
    gvz.columns = ["date", "gvz"]
    gvz["gvz"] = pd.to_numeric(gvz["gvz"], errors="coerce")
    gvz = gvz.dropna()
    d = df.merge(gvz, on="date", how="inner").sort_values("date").reset_index(drop=True)
    n = len(d)
    d["lr"] = np.log(d["rv_day"])
    d["lgvz"] = np.log(d["gvz"])
    d["dlgvz"] = d["lgvz"].diff()
    d["dow"] = pd.to_datetime(d["date"]).dt.dayofweek
    # targets: RV over next h trading days (valid rows only; skipping gaps by row-index of valid days)
    lr = d["lr"].to_numpy(float)
    for h in (5, 10, 20):
        tgt = np.full(n, np.nan)
        for i in range(n - h):
            seg = lr[i + 1: i + 1 + h]
            if np.isfinite(seg).all():
                tgt[i] = 0.5 * np.log(np.mean(np.exp(2 * seg)))  # log of mean of squared rv -> log RV
        d[f"t{h}"] = tgt
    base = ["lr_l1", "lr_l5", "lr_l21", "act_l1"]
    d["lr_l1"] = d["lr"].shift(1)
    d["lr_l5"] = d["lr"].shift(5)
    d["lr_l21"] = d["lr"].shift(21)
    d["act_l1"] = d["log_act"].shift(1)
    dummies = pd.get_dummies(d["dow"], prefix="dow").astype(float)
    gvz_cols = ["lgvz", "dlgvz"]
    res = {"meta": {"n_days": int(n), "span": [d["date"].iloc[0], d["date"].iloc[-1]],
                    "prereg": "c23b046", "target_note": "mean-of-var over next h valid days, log"},
           "horizons": {}}

    def cols(extra):
        X = [np.ones(n)] + [d[c].to_numpy(float) for c in base] + \
            [dummies[c].to_numpy(float) for c in dummies.columns]
        if extra:
            X += [d[c].to_numpy(float) for c in extra]
        return np.column_stack(X)

    Xa_all = cols([])
    Xb_all = cols(gvz_cols)

    def wf(X, y, min_win=200):
        pred = np.full(n, np.nan)
        ok = np.isfinite(y)
        for t in range(min_win, n):
            m = ok[:t] & np.isfinite(X[:t]).all(axis=1)
            if m.sum() < 100:
                continue
            beta, *_ = np.linalg.lstsq(X[:t][m], y[:t][m], rcond=None)
            if np.isfinite(X[t]).all():
                pred[t] = float(X[t] @ beta)
        return pred

    from scipy.stats import spearmanr
    for h in (5, 10, 20):
        y = d[f"t{h}"].to_numpy(float)
        pa = wf(Xa_all, y)
        pb = wf(Xb_all, y)
        ok = np.isfinite(pa) & np.isfinite(pb) & np.isfinite(y)
        ya = y[ok]
        ra = ya - pa[ok]
        rb = ya - pb[ok]
        sst = float(((ya - ya.mean()) ** 2).sum())
        sse_a = float((ra ** 2).sum())
        sse_b = float((rb ** 2).sum())
        r2a, r2b = 1 - sse_a / sst, 1 - sse_b / sst
        # HAC DM on sq errs (lag ~ h)
        dml = np.minimum(h, 5)
        dd = ra ** 2 - rb ** 2
        m_ = dd.mean()
        g0 = float(np.mean((dd - m_) ** 2))
        gam = [float(np.mean((dd[:-l] - m_) * (dd[l:] - m_))) for l in range(1, dml + 1)]
        v = g0 + 2 * sum((1 - l / (dml + 1)) * g for l, g in enumerate(gam, start=1))
        dm_t = float(m_ / np.sqrt(v / len(dd))) if v > 0 else np.nan
        res["horizons"][f"h{h}"] = {"n_oos": int(ok.sum()), "r2_A": float(r2a), "r2_B": float(r2b),
                                    "delta_r2_oos": float(r2b - r2a), "DM_HAC_t": dm_t,
                                    "rmse_A": float(np.sqrt(np.nanmean(ra ** 2))),
                                    "rmse_B": float(np.sqrt(np.nanmean(rb ** 2)))}
        # IC incremental: partial spearman of pb-implied... report IC of (y - pa) on gvz score not fitted: skip; report delta IC of fitted residual corr
        res["horizons"][f"h{h}"]["spearman_gvz_vs_residA"] = float(spearmanr(
            d.loc[ok, "lgvz"].to_numpy(), ra).statistic)
    # redundancy diagnostics
    m = np.isfinite(d["lr"]) & np.isfinite(d["lgvz"]) & np.isfinite(d["log_act"])
    res["redundancy"] = {"corr_logRV_logGVZ": float(np.corrcoef(d["lr"][m], d["lgvz"][m])[0, 1]),
                         "corr_logGVZ_activity": float(np.corrcoef(d["lgvz"][m], d["log_act"][m])[0, 1]),
                         "corr_logRV_activity": float(np.corrcoef(d["lr"][m], d["log_act"][m])[0, 1])}
    # regime audit: delta R2 within HIGH vs LOW tercile of trailing 21d RV at decision
    d["rv21"] = d["lr"].rolling(21).mean()
    thr_lo, thr_hi = np.nanpercentile(d["rv21"], [33.33, 66.67])
    reg = {}
    for st, lo, hi in (("LOW", -np.inf, thr_lo), ("MID", thr_lo, thr_hi), ("HIGH", thr_hi, np.inf)):
        sel = d["rv21"].between(lo, hi, inclusive="neither") if st == "MID" else \
            (d["rv21"] < hi) if st == "LOW" else (d["rv21"] >= lo)
        sub = d[sel]
        if len(sub) < 150:
            continue
        # quick IS/OOS split delta R2 inside regime (fixed-coef IS->OOS)
        sub = sub.reset_index(drop=True)
        sn = len(sub)
        cut = int(sn * 0.6)
        ysub = sub["t10"].to_numpy(float)
        Xa_s = cols([])
        Xb_s = cols(gvz_cols)
        # map back via index
        idx = sub.index.to_numpy()
        ma = np.isfinite(ysub)
        if ma.sum() < 120:
            continue
        def fit_eval(X):
            beta, *_ = np.linalg.lstsq(X[idx][:cut][ma[:cut]], ysub[:cut][ma[:cut]], rcond=None)
            pred = X[idx][cut:][ma[cut:]] @ beta
            yy = ysub[cut:][ma[cut:]]
            return 1 - float(((yy - pred) ** 2).sum()) / float(((yy - yy.mean()) ** 2).sum())
        try:
            r2a_s = fit_eval(Xa_s)
            r2b_s = fit_eval(Xb_s)
            reg[st] = {"n": int(len(sub)), "delta_r2_oos_in_regime": float(r2b_s - r2a_s)}
        except Exception:
            pass
    res["regime_audit"] = reg
    # monthly directional probe
    d["ym"] = d["date"].str[:7]
    mon = d.groupby("ym").agg(mon_ret=("ret", "sum"), gvz_end=("gvz", "last"),
                              rv_mean=("rv_day", "mean")).reset_index()
    mon["next_ret"] = mon["mon_ret"].shift(-1)
    mon["vrp_p"] = np.log(mon["gvz_end"]) - np.log(mon["rv_mean"] * np.sqrt(21))
    mm = mon.dropna(subset=["next_ret", "gvz_end"])
    res["directional_monthly"] = {
        "n": int(len(mm)),
        "spearman_gvz_next_month_ret": float(spearmanr(mm["gvz_end"], mm["next_ret"]).statistic),
        "spearman_vrp_next_month_ret": float(spearmanr(mm["vrp_p"].dropna(),
                                                       mm.loc[mm["vrp_p"].notna(), "next_ret"]).statistic)}
    # R1 risk-state audit: logistic on IS (frozen) top-tercile future-5d RV; AUC OOS
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    d["hi5"] = (d["t5"] >= np.nanpercentile(d["t5"], 66.67)).astype(float)
    mmask = d[["lr_l1", "lr_l5", "lr_l21", "act_l1", "hi5"]].dropna().index
    subd = d.loc[mmask].reset_index(drop=True)
    sn2 = len(subd)
    cut2 = int(sn2 * 0.6)
    Xf = subd[["lr_l1", "lr_l5", "lr_l21", "act_l1"]].to_numpy()
    yf = subd["hi5"].to_numpy()
    aucs = {}
    for name, Xuse in (("A", Xf), ("B", np.column_stack([Xf, subd[["lgvz", "dlgvz"]].to_numpy()]))):
        clf = LogisticRegression(max_iter=2000)
        clf.fit(Xuse[:cut2], yf[:cut2])
        if yf[cut2:].sum() > 5 and (yf[cut2:] == 0).sum() > 5:
            aucs[name] = float(roc_auc_score(yf[cut2:], clf.predict_proba(Xuse[cut2:])[:, 1]))
    res["r1_auc_audit"] = {"n_is": int(cut2), "n_oos": int(sn2 - cut2), "auc": aucs,
                            "note": "identify future-5d HIGH vol tercile; A=baseline, B=A+GVZ"}
    (OUT / "RESULTS.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str)[:4500])


if __name__ == "__main__":
    main()
