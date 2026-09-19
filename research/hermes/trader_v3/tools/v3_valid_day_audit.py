# -*- coding: utf-8 -*-
"""V3 Valid-Day Definition Audit — 只读实测 + 阈值敏感性（不得用 Alpha 结果反选定义）。

产出:
  research/V3_VALID_DAY_AUDIT.md
  state/V3_VALID_DAY_AUDIT.json
  data/v3_valid_day_table.csv   (逐日 hours_covered / n_ticks / 缺口)
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

V3 = Path(__file__).resolve().parents[1]
ASSEMBLED = Path(r"C:\AIQuant\data\staging_duka\assembled")
OUTJ = V3 / "state" / "V3_VALID_DAY_AUDIT.json"
OUTMD = V3 / "research" / "V3_VALID_DAY_AUDIT.md"
TABLE = V3 / "data" / "v3_valid_day_table.csv"
TABLE.parent.mkdir(parents=True, exist_ok=True)


def build_day_table():
    rows = []
    for f in sorted(ASSEMBLED.glob("ticks_*.parquet")):
        df = pd.read_parquet(f, columns=["ts_utc"])
        ts = df["ts_utc"].to_numpy()
        sec = ts // 1000
        day = (sec // 86400)
        hour = (sec % 86400) // 3600
        # 逐日聚合
        g = pd.DataFrame({"day": day, "hour": hour})
        agg = g.groupby("day").agg(n=("hour", "size"), hours=("hour", "nunique"))
        for d, r in agg.iterrows():
            dt = datetime.fromtimestamp(int(d) * 86400, timezone.utc).strftime("%Y-%m-%d")
            rows.append({"day": dt, "n_ticks": int(r["n"]), "hours_covered": int(r["hours"])})
        del df
    t = pd.DataFrame(rows).sort_values("day").reset_index(drop=True)
    t.to_csv(TABLE, index=False, encoding="utf-8")
    return t


def period_of(day):
    if "2023-09" <= day[:7] <= "2023-11":
        return "P_A_2023H2"
    if "2024-01" <= day[:7] <= "2024-03":
        return "P_B_2024Q1"
    if day[:7] == "2026-08":
        return "P_C_202608"
    return "other"


def main():
    t = build_day_table()
    t["period"] = t["day"].map(period_of)
    HAVE = t[t["n_ticks"] > 0].copy()
    res = {"schema": "v3_valid_day_audit/1", "ts_utc": datetime.now(timezone.utc).isoformat(),
           "source": str(ASSEMBLED), "days_total_calendar": int(len(t)),
           "days_with_data": int(len(HAVE)), "periods": {}, "sensitivity": {}, "md": str(OUTMD)}

    for p in ("P_A_2023H2", "P_B_2024Q1", "P_C_202608"):
        sub = HAVE[HAVE["period"] == p]
        res["periods"][p] = {"days_with_data": int(len(sub)),
                             "hours_covered_min": int(sub["hours_covered"].min()) if len(sub) else None,
                             "hours_covered_max": int(sub["hours_covered"].max()) if len(sub) else None,
                             "hours_covered_median": float(sub["hours_covered"].median()) if len(sub) else None,
                             "n_ticks_median": float(sub["n_ticks"].median()) if len(sub) else None}

    # 阈值敏感性
    hours_th = [18, 19, 20, 21, 22, 23, 24]
    nticks_th = [0, 100, 500, 1000, 5000, 10000]
    sens = {}
    for H in hours_th:
        row = {}
        for Nn in nticks_th:
            ok = HAVE[(HAVE["hours_covered"] >= H) & (HAVE["n_ticks"] >= Nn)]
            row[str(Nn)] = {"total_days": int(len(ok)),
                            "P_A": int((ok["period"] == "P_A_2023H2").sum()),
                            "P_B": int((ok["period"] == "P_B_2024Q1").sum()),
                            "ticks_retained": int(ok["n_ticks"].sum())}
        sens[str(H)] = row
    res["sensitivity"] = sens

    # 提案值评估
    prop = HAVE[(HAVE["hours_covered"] >= 21) & (HAVE["n_ticks"] >= 1000)]
    res["proposal_eval"] = {"proposal": "hours_covered>=21 AND n_ticks>=1000",
                            "valid_days": int(len(prop)),
                            "P_A": int((prop["period"] == "P_A_2023H2").sum()),
                            "P_B": int((prop["period"] == "P_B_2024Q1").sum()),
                            "ticks_retained": int(prop["n_ticks"].sum()),
                            "frac_of_have": round(len(prop) / max(1, len(HAVE)), 4)}
    # 稳定性：H 在 20..22 之间 valid_days 变化
    def cnt(H, Nn):
        return int(((HAVE["hours_covered"] >= H) & (HAVE["n_ticks"] >= Nn)).sum())
    res["stability"] = {"hours_20_vs_21_vs_22": [cnt(20, 1000), cnt(21, 1000), cnt(22, 1000)],
                        "nticks_500_vs_1000_vs_5000": [cnt(21, 500), cnt(21, 1000), cnt(21, 5000)]}
    # 判定
    stable = (cnt(20, 1000) == cnt(21, 1000) == cnt(22, 1000)) or abs(cnt(20, 1000) - cnt(22, 1000)) <= 3
    res["verdict"] = "FROZEN_CANDIDATE" if stable else "INSUFFICIENT_EVIDENCE"
    res["verdict_reason"] = ("hours 阈值 20/21/22 结果稳定 → 可冻结" if stable
                             else "小时阈值敏感性偏高，且阈值选择本身无唯一数据依据 → INSUFFICIENT_EVIDENCE")

    OUTJ.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    md = [f"# V3 VALID-DAY DEFINITION AUDIT — {res['ts_utc']}", "",
          "> 本审计**只做数据质量敏感性**，**不使用任何 Alpha 结果**反选定义（任务书 §二十 / 新硬门禁一）。", "",
          f"- 日历天数: {res['days_total_calendar']} · 有数据天: {res['days_with_data']}",
          f"- 逐日表: `{TABLE}`", "",
          "## 分期", "```json", json.dumps(res["periods"], ensure_ascii=False, indent=1), "```",
          "## 阈值敏感性 (rows=hours_covered 阈值, cols=n_ticks 阈值; 值=通过天数 [P_A/P_B])",
          "```json", json.dumps(sens, ensure_ascii=False, indent=1), "```",
          "## 提案评估", "```json", json.dumps(res["proposal_eval"], ensure_ascii=False, indent=1), "```",
          "## 稳定性", "```json", json.dumps(res["stability"], ensure_ascii=False, indent=1), "```", "",
          f"## 判定：**{res['verdict']}**", f"- {res['verdict_reason']}", "",
          "### 处置",
          "- 采纳（若 FROZEN_CANDIDATE）：`VALID_DAY := hours_covered >= 21 AND n_ticks >= 1000`，"
          "依据 = C4 同源高峰点 match_rate 0.9881（hours>=21 子集）+ 本敏感性稳定；**冻结后不得再改**。",
          "- 若 INSUFFICIENT_EVIDENCE：保持 PROPOSAL，**不得进入 G2**（G2 开放条件含 Valid-Day=FROZEN）。", ""]
    OUTMD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": res["verdict"], "valid_days": res["proposal_eval"]["valid_days"],
                      "P_A": res["proposal_eval"]["P_A"], "P_B": res["proposal_eval"]["P_B"],
                      "days_with_data": res["days_with_data"], "stability": res["stability"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
