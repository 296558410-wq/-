# -*- coding: utf-8 -*-
"""run_cand01_supp.py — confusion-test supplement (deterministic).
A2 = A + smoothed local RV (trailing 21d & 63d mean log RV). Compare B(A+GVZ) vs A2.
If delta collapses -> GVZ level is smoothed-vol representation (KILL-06/confusion).
Also R1 AUC with A2 and regime split by rv21 tercile (mask-based)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from run_cand01 import build_panel  # noqa

OUT = REPO / "research/hermes/cand01_gvz"
SEED = 7


def main():
    df = build_panel()
    gvz = pd.read_csv(REPO / "data/staging_fred/gvzcls.csv")
    gvz.columns = ["date", "gvz"]
    gvz["gvz"] = pd.to_numeric(gvz["gvz"], errors="coerce")
    d = df.merge(gvz.dropna(), on="date", how="inner").sort_values("date").reset_index(drop=True)
    n = len(d)
    d["lr"] = np.log(d["rv_day"].clip(lower=1e-6))
    d["lgvz"] = np.log(d["gvz"])
    d["dlgvz"] = d["lgvz"].diff()
    d["dow"] = pd.to_datetime(d["date"]).dt.dayofweek
    d["lr_l1"] = d["lr"].shift(1); d["lr_l5"] = d["lr"].shift(5); d["lr_l21"] = d["lr"].shift(21)
    d["act_l1"] = d["log_act"].shift(1)
    d["rv21"] = d["lr"].rolling(21).mean().shift(1)   # smoothed local vol, known at decision
    d["rv63"] = d["lr"].rolling(63).mean().shift(1)
    lr = d["lr"].to_numpy(float)
    for h in (5, 10, 20):
        tgt = np.full(n, np.nan)
        for i in range(n - h):
            seg = lr[i + 1: i + 1 + h]
            if np.isfinite(seg).all():
                tgt[i] = 0.5 * np.log(np.mean(np.exp(2 * seg)))
        d[f"t{h}"] = tgt
    dummies = pd.get_dummies(d["dow"], prefix="dow").astype(float)
    base = ["lr_l1", "lr_l5", "lr_l21", "act_l1"]
    gvz_cols = ["lgvz", "dlgvz"]

    def design(extra):
        X = [np.ones(n)] + [d[c].to_numpy(float) for c in base] + [dummies[c].to_numpy(float) for c in dummies.columns]
        X += [d[c].to_numpy(float) for c in extra]
        return np.column_stack(X)

    Xa = design([])
    Xa2 = design(["rv21", "rv63"])
    Xb = design(gvz_cols)

    def wf(X, y, min_win=250):
        pred = np.full(n, np.nan)
        ok = np.isfinite(y)
        for t in range(min_win, n):
            m = ok[:t] & np.isfinite(X[:t]).all(axis=1)
            if m.sum() < 120:
                continue
            beta, *_ = np.linalg.lstsq(X[:t][m], y[:t][m], rcond=None)
            if np.isfinite(X[t]).all():
                pred[t] = float(X[t] @ beta)
        return pred

    res = {"n": n, "span": [d["date"].iloc[0], d["date"].iloc[-1]]}
    for h in (5, 10, 20):
        y = d[f"t{h}"].to_numpy(float)
        pa, pa2, pb = wf(Xa, y), wf(Xa2, y), wf(Xb, y)
        ok = np.isfinite(pa) & np.isfinite(pa2) & np.isfinite(pb) & np.isfinite(y)
        ya = y[ok]
        sst = float(((ya - ya.mean()) ** 2).sum())
        r2 = {k: 1 - float(((ya - p[ok]) ** 2).sum()) / sst for k, p in (("A", pa), ("A2", pa2), ("B", pb))}
        res[f"h{h}"] = {"r2": r2,
                        "delta_B_vs_A": float(r2["B"] - r2["A"]),
                        "delta_B_vs_A2": float(r2["B"] - r2["A2"]),
                        "n_oos": int(ok.sum())}
    res["redundancy"] = {"corr_lgvz_rv21": float(np.corrcoef(
        pd.concat([d["lgvz"], d["rv21"]], axis=1).dropna().iloc[:, 0],
        pd.concat([d["lgvz"], d["rv21"]], axis=1).dropna().iloc[:, 1])[0, 1]),
                         "corr_lgvz_rv63": float(np.corrcoef(
        pd.concat([d["lgvz"], d["rv63"]], axis=1).dropna().iloc[:, 0],
        pd.concat([d["lgvz"], d["rv63"]], axis=1).dropna().iloc[:, 1])[0, 1])}
    # R1 AUC: A vs A2 vs B (logistic IS->OOS, top-tercile h5)
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    d["hi5"] = (d["t5"] >= np.nanpercentile(d["t5"], 66.67)).astype(float)
    sub = d.dropna(subset=["lr_l1", "lr_l5", "lr_l21", "act_l1", "rv21", "lgvz", "hi5"]).reset_index(drop=True)
    cut = int(len(sub) * 0.6)
    yf = sub["hi5"].to_numpy()
    aucs = {}
    for name, cols_ in (("A", ["lr_l1", "lr_l5", "lr_l21", "act_l1"]),
                        ("A2", ["lr_l1", "lr_l5", "lr_l21", "act_l1", "rv21"]),
                        ("B", ["lr_l1", "lr_l5", "lr_l21", "act_l1", "lgvz", "dlgvz"])):
        clf = LogisticRegression(max_iter=2000)
        Xf = sub[cols_].to_numpy()
        clf.fit(Xf[:cut], yf[:cut])
        if yf[cut:].sum() > 5 and (yf[cut:] == 0).sum() > 5:
            aucs[name] = float(roc_auc_score(yf[cut:], clf.predict_proba(Xf[cut:])[:, 1]))
    res["r1_auc"] = aucs
    # regime audit by rv21 tercile (mask-based; delta B vs A2 within regime, fixed 60/40 fit)
    thr_lo, thr_hi = np.nanpercentile(d["rv21"].dropna(), [33.33, 66.67])
    reg = {}
    for st, lo, hi in (("LOW", -np.inf, thr_lo), ("MID", thr_lo, thr_hi), ("HIGH", thr_hi, np.inf)):
        sel = (d["rv21"] >= lo) & (d["rv21"] < hi)
        idx = np.where(sel.to_numpy())[0]
        y10 = d["t10"].to_numpy(float)
        if len(idx) < 150:
            continue
        cutr = int(len(idx) * 0.6)
        def r2r(X):
            tr = idx[:cutr]; er = idx[cutr:]
            mtr = np.isfinite(y10[tr]) & np.isfinite(X[tr]).all(axis=1)
            mer = np.isfinite(y10[er]) & np.isfinite(X[er]).all(axis=1)
            beta, *_ = np.linalg.lstsq(X[tr][mtr], y10[tr][mtr], rcond=None)
            yy = y10[er][mer]
            return 1 - float(((yy - X[er][mer] @ beta) ** 2).sum()) / float(((yy - yy.mean()) ** 2).sum()) if len(yy) > 40 else np.nan
        reg[st] = {"n": int(len(idx)), "r2_A2": r2r(Xa2), "r2_B": r2r(Xb)}
    res["regime_audit"] = reg
    (OUT / "RESULTS_SUPP.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
