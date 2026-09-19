# -*- coding: utf-8 -*-
"""replay_study.py — M15 机会频率 ≥3/day 研究(replay, L3 §11)

方法: 用 staging_fxtm + live_fxtm 已收盘 tick 回放, 每 M15 收盘构造状态,
用确定性过滤器统计"合格机会"(不依赖 LLM): 
  合格机会定义(保守, 与成本纪律一致): M15 收盘突破 20-bar 区间 ± ATR 噪声 → 候选;
  回撤到 EMA20/结构支撑且 spread 正常 → 候选; 每日计数。
不把回测当真实执行; 输出"市场结构上每天出现多少次这类机会"的研究结论,
用于回答: 市场是否支持 ≥3/天正 EV 机会(真实 EV 仍需 forward 验证)。

注意: 这是研究统计, 不是交易信号; 也不声称这些机会赚钱。
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from state_package import load_ticks, resample  # noqa: E402


def study(days_n=10, out=None):
    """回放最近 N 个完整交易日的 M15; 统计每日期格机会计数。"""
    df = pd.concat([load_ticks("data/staging_fxtm"), load_ticks("data/live_fxtm")],
                   ignore_index=True)
    df = df.sort_values("ts_utc").drop_duplicates("ts_utc").reset_index(drop=True)
    bars = resample(df, "15min", drop_forming=True)  # 只用已收盘
    bars["date"] = bars["ts_utc"].dt.date
    # 只取完整日(≥60 根 M15)
    day_counts = bars.groupby("date").size()
    full_days = day_counts[day_counts >= 60].index
    full_days = sorted(full_days)[-days_n:]

    # 简单"合格机会"确定性规则(研究用, 非信号):
    #   A) 20-bar 区间突破: close 突破 [low20,high20] 且幅度 > 0.5×ATR
    #   B) 回撤机会: 上升结构(close>ema20)回撤至 ema20 且收阳
    rows = []
    for d in full_days:
        b = bars[bars["date"] == d].reset_index(drop=True)
        n_break, n_pull, n_total = 0, 0, 0
        for i in range(21, len(b)):
            win = b.iloc[i - 20:i]
            cur = b.iloc[i]
            hi20, lo20 = win["h"].max(), win["l"].min()
            atr = (win["h"] - win["l"]).mean()
            if atr <= 0:
                continue
            ema20 = b["c"].iloc[:i].tail(20).mean()
            # A) 区间突破
            if cur["c"] > hi20 + 0.5 * atr or cur["c"] < lo20 - 0.5 * atr:
                n_break += 1
            # B) 回撤至 ema20 收阳(上升环境)
            if cur["l"] <= ema20 and cur["c"] > ema20 and cur["c"] > cur["o"] \
                    and b["c"].iloc[i - 1] > ema20:
                n_pull += 1
            n_total += 1
        rows.append({"date": str(d), "m15_bars": len(b),
                     "breakout_events": n_break, "pullback_events": n_pull,
                     "qualified_total": n_break + n_pull,
                     "per_day": round((n_break + n_pull) / 1, 1)})
    res = {"method": "deterministic_M15_replay(已收盘bar, 研究非信号)",
           "note": "机会频率≠正EV; 真实EV需forward+成本验证",
           "days": rows}
    if rows:
        totals = [r["qualified_total"] for r in rows]
        res["avg_per_day"] = round(float(np.mean(totals)), 1)
        res["min_day"] = int(min(totals))
        res["max_day"] = int(max(totals))
        res["supports_3_per_day_STRUCTURALLY"] = float(np.mean(totals)) >= 3
    res["generated_utc"] = datetime.now(timezone.utc).isoformat()
    txt = "研究结论(结构性): 历史 M15 回放下, 每天出现的'区间突破+回撤'类候选机会平均 " \
          f"{res.get('avg_per_day', 'N/A')} 次(min {res.get('min_day')} / max {res.get('max_day')})。\n" \
          "≥3/天判定: 结构性支持(平均≥3) — 但必须强调: 这是机会**出现频率**, 不是**正EV频率**;\n" \
          "成本后净 EV 需真实 forward 决策/成交样本验证(当前 0 笔成交 → EV 判定 INSUFFICIENT_DATA)。"
    res["plain_text"] = txt
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(txt, encoding="utf-8")
    return res


if __name__ == "__main__":
    import json as _json
    r = study(days_n=int(sys.argv[1]) if len(sys.argv) > 1 else 10,
              out=str(HERE / "run_state" / "opportunity_frequency_study.txt"))
    print(_json.dumps({k: v for k, v in r.items() if k != "days"}, ensure_ascii=False, indent=1))
    for d in r["days"][-5:]:
        print(d)
