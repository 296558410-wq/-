# -*- coding: utf-8 -*-
"""opportunity.py — Opportunity Coverage 漏斗 + Daily ≥3 机会频率研究(L3)

漏斗(用户 §12): M15 Decision Windows → Potential → Qualified → EV-Positive → Executed。
研究(§11): 每日 1/2/3/5/8/10 次频率 × 机会计数/胜率/期望/成本/净EV, 判断市场是否支持 ≥3/天。
用途: Dashboard 覆盖统计 + 研究报告; 全部基于真实决策/计划/成交记录(ledger + decisions), 不伪造。

注意: 数据不足时如实报告(样本太小 → UNKNOWN / NOT SUPPORTED YET), 不硬凑结论。
"""
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "run_state"
LEDGER_P = RUN / "plan_ledger.jsonl"
DEC_DIR = RUN / "decisions"
WF_HIST = RUN / "workflow_history.jsonl"


def _load_lines(p):
    if not Path(p).exists():
        return []
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def funnel(window_hours=24):
    """当前漏斗: 基于 workflow_history + ledger。
    potential = 决策中 opportunity != none 的数量(近似);
    qualified = 注册计划数(通过 validate); ev_positive = 注册时 EV>0 的计划;
    executed = filled/closed 事件数。"""
    hist = _load_lines(WF_HIST)
    evs = _load_lines(LEDGER_P)
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    cut = now - timedelta(hours=window_hours)

    def fresh(ts):
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00")) >= cut
        except Exception:  # noqa: BLE001
            return True

    m15_windows = sum(1 for r in hist if fresh(r.get("utc_ts")))
    decisions = [r for r in hist if fresh(r.get("utc_ts")) and r.get("decision") in ("LONG", "SHORT", "WAIT")]
    waits = sum(1 for d in decisions if d.get("decision") == "WAIT")
    # potential opportunities = 非 WAIT 决策数 + 带机会标注的
    non_wait = [d for d in decisions if d.get("decision") in ("LONG", "SHORT")]
    regs = [e for e in evs if e.get("type") == "registered"]
    qualified = len(regs)
    ev_pos = sum(1 for e in regs
                 if (e.get("plan") or {}).get("expected_net_EV", {}).get("value", 0) > 0)
    executed = sum(1 for e in evs if e.get("type") in ("filled", "closed"))
    return {"window_hours": window_hours, "m15_windows": m15_windows,
            "decisions": len(decisions), "waits": waits,
            "potential_opportunities": len(non_wait), "qualified_opportunities": qualified,
            "ev_positive_opportunities": ev_pos, "executed_trades": executed}


def daily_frequency_study(decisions_log=None, plans_log=None):
    """研究: 每日 1..10 次频率的市场支持度。
    输入: 真实决策+计划样本。输出: 每个频率的假设性 expectancy(基于现有样本的均 R 与胜率)
    与判定 SUPPORTED / NOT_SUPPORTED / INSUFFICIENT_DATA。"""
    evs = _load_lines(LEDGER_P) if plans_log is None else plans_log
    closes = [e for e in evs if e.get("type") == "closed"]
    # 从 closed 事件算 realized R(需要 fill 价 → 简化: 用 payload 的 realized_R 若存在)
    outcomes = []
    for e in closes:
        r_r = (e.get("payload") or {}).get("realized_R")
        if r_r is not None:
            outcomes.append(float(r_r))
    n = len(outcomes)
    if n < 10:
        return {"verdict": "INSUFFICIENT_DATA",
                "note": f"仅 {n} 笔 closed 样本; ≥3/day 频率判定需真实前向样本积累",
                "n_samples": n, "frequencies": {}}
    wins = [x for x in outcomes if x > 0]
    wr = len(wins) / n
    avg_win = sum(wins) / len(wins) if wins else 0
    losses = [x for x in outcomes if x <= 0]
    avg_loss = abs(sum(losses) / len(losses)) if losses else 1
    # 每频率日期望: 假设日交易量 f, EV_day = f * (wr*avg_win - (1-wr)*avg_loss) - f*cost_R
    freq_res = {}
    for f in (1, 2, 3, 5, 8, 10):
        ev_per = wr * avg_win - (1 - wr) * avg_loss
        freq_res[f] = {"ev_per_trade_R": round(ev_per, 3),
                       "ev_day_R": round(ev_per * f, 2)}
    supported = freq_res.get(3, {}).get("ev_day_R", 0) > 0 and wr > 0.35
    return {"verdict": "SUPPORTED" if supported else "NOT_SUPPORTED",
            "n_samples": n, "win_rate": round(wr, 3), "avg_win_R": round(avg_win, 2),
            "avg_loss_R": round(avg_loss, 2), "frequencies": freq_res}


def coverage_summary():
    """Dashboard 用覆盖摘要 + 研究状态。"""
    f = funnel(24)
    study = daily_frequency_study()
    return {"funnel": f, "study": study,
             "target_per_day": 3,
             "note": "≥3/天是研究目标不是 KPI; 市场不支持时明确报 NOT SUPPORTED, 不强迫交易"}


if __name__ == "__main__":
    print(json.dumps(coverage_summary(), ensure_ascii=False, indent=1))
