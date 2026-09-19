# -*- coding: utf-8 -*-
"""review.py — Trade Review 确定性统计生成(G, REVIEW_CONTRACT) + 周期复盘支持。

平仓后调用: 读取 ledger 事件 → 计算 realized pnl/plan accuracy/execution 统计 → 写 memory/reviews/。
Hermes 评注在下一轮/复盘批次补(REVIEW_CONTRACT 要求字段留空由 Hermes 填)。
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger  # noqa: E402

REVIEW_DIR = HERE / "memory" / "reviews"


def _now():
    return datetime.now(timezone.utc).isoformat()


def build_review(plan_id, fill_event, exit_event, quote_series=None):
    """由 ledger 事件构造 review。quote_series(可选): [(utc, mid)] 计算 MAE/MFE(未接时置 null)。"""
    evs = ledger.plan_events(plan_id)
    reg = next((e for e in evs if e.get("type") == "registered"), {})
    plan = reg.get("plan") or {}
    d = plan.get("direction")
    entry = fill_event.get("entry_price") if fill_event else None
    exit_px = exit_event.get("exit_price") if exit_event else None
    qty = (fill_event or {}).get("qty")
    if entry and exit_px:
        # 2026-09-08 fix: pnl 须乘实际手数(旧代码恒按 1 手 ×100, 0.01 手虚报 100 倍)
        mul = 100 * (float(qty) if qty else 1.0)  # 1 lot = 100 oz; 缺省按 1 手兼容旧事件
        pnl_usd = (exit_px - entry) * mul if d == "LONG" else (entry - exit_px) * mul
        entry_mid = entry
        stop = (plan.get("stop_logic") or {}).get("level_price")
        r = abs(exit_px - entry) / abs(entry - stop) if stop and abs(entry - stop) > 0 else None
    else:
        pnl_usd, r = None, None
    plan_acc = {}
    if plan.get("expected_win_probability") is not None:
        plan_acc["win_prob_est"] = plan.get("expected_win_probability")
        plan_acc["realized_outcome"] = 1 if (pnl_usd is not None and pnl_usd > 0) else (0 if pnl_usd is not None else None)
        plan_acc["calibration_note"] = "single obs; accumulate for calibration"
    review = {
        "review_id": f"RV-{plan_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "utc_ts": _now(), "plan_id": plan_id,
        "direction": d,
        "entry": {"price": entry, "utc_ts": (fill_event or {}).get("utc_ts"),
                  "spread_bps_at_entry": (fill_event or {}).get("spread_bps_at_entry")},
        "exit": {"price": exit_px, "utc_ts": (exit_event or {}).get("utc_ts"),
                 "reason": (exit_event or {}).get("reason")},
        "realized": {"pnl_usd": pnl_usd, "pnl_R": r,
                     "hold_bars_m15": (exit_event or {}).get("hold_bars_m15"),
                     "max_favorable_R": None, "max_adverse_R": None},
        "execution": {"slippage_bps": (fill_event or {}).get("slippage_bps"),
                      "latency_ms": (fill_event or {}).get("latency_ms"),
                      "reject": (fill_event or {}).get("reject")},
        "plan_accuracy": plan_acc,
        "deterministic_summary": f"{d} plan {plan_id}: entry={entry} exit={exit_px} "
                                 f"pnl={pnl_usd} (paper)",
        "hermes_comment": None,  # 由 Hermes 复盘轮填
    }
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    p = REVIEW_DIR / f"{plan_id}.json"
    # append 到同日文件(多条 review 聚合) — 简化: 每 review 一个文件, id 含时间戳
    p2 = REVIEW_DIR / f"{review['review_id']}.json"
    p2.write_text(json.dumps(review, indent=1, ensure_ascii=False), encoding="utf-8")
    return review


def weekly_summary():
    """周复盘统计: 遍历 reviews → 计划质量/WAIT/执行统计(MEMORY_CONTRACT statistics 聚合)。"""
    if not REVIEW_DIR.exists():
        return {"n_reviews": 0}
    rows = []
    for f in sorted(REVIEW_DIR.glob("RV-*.json")):
        try:
            rows.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            continue
    wins = [r for r in rows if (r.get("realized") or {}).get("pnl_usd") is not None and r["realized"]["pnl_usd"] > 0]
    losses = [r for r in rows if (r.get("realized") or {}).get("pnl_usd") is not None and r["realized"]["pnl_usd"] <= 0]
    return {"n_reviews": len(rows), "n_win": len(wins), "n_loss": len(losses),
            "win_rate": round(len(wins) / len(rows), 3) if rows else None,
            "total_pnl_usd_paper": round(sum((r.get("realized") or {}).get("pnl_usd") or 0 for r in rows), 2)}


if __name__ == "__main__":
    print(json.dumps(weekly_summary(), ensure_ascii=False))
