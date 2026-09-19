# -*- coding: utf-8 -*-
"""metrics.py — Dashboard 数据源(Single Source of Truth 聚合层)。

只读聚合: ledger(计划/成交) + positions(持仓) + statistics(轮次) + review(复盘)。
Dashboard 不维护第二套账户状态; 本模块是唯一读取路径。
无真实 broker → account 段明确 '暂无账户数据', 禁止伪造。
"""
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "run_state"
POS_DIR = RUN / "positions"
LEDGER_P = RUN / "plan_ledger.jsonl"
STATS_P = RUN / "statistics.json"
REVIEW_DIR = HERE / "memory" / "reviews"


def _read(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default if default is not None else {}


def _lines(p):
    if not Path(p).exists():
        return []
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def account():
    """账户数据: demo 模式读真实 broker; paper 模式明示暂无。"""
    import trader_core as TC  # noqa: PLC0415
    if TC.EXEC_MODE == "demo":
        a = TC.broker_account()
        if not a.get("error"):
            return {"available": True, "note": f"FXTM Demo (login {a['login']})",
                    "balance": a.get("balance"), "equity": a.get("equity"),
                    "free_margin": a.get("margin_free"), "used_margin": None,
                    "margin_level": a.get("margin_level"), "floating_pnl": None,
                    "leverage": 500, "mode": "DEMO", "server": a.get("server")}
        return {"available": False, "note": f"demo 不可达: {a.get('error')}",
                "balance": None, "equity": None, "free_margin": None,
                "used_margin": None, "margin_level": None, "floating_pnl": None,
                "leverage": 500, "mode": "DEMO"}
    return {"available": False, "note": "暂无账户数据(Paper 模式, 未连真实 Broker)",
            "balance": None, "equity": None, "free_margin": None, "used_margin": None,
            "margin_level": None, "floating_pnl": None, "leverage": 500, "mode": "PAPER"}


def trades():
    """今日/本周/本月 成交统计(from ledger closed + review realized)。"""
    evs = _lines(LEDGER_P)
    closes = [e for e in evs if e.get("type") == "closed"]
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    iso_week = now.isocalendar()
    out = {"today": 0, "week": 0, "month": 0, "total": len(closes),
           "today_target": 3, "list": []}
    for e in closes:
        ts = str(e.get("utc_ts", ""))[:10]
        realized = e.get("realized_usd")
        out["list"].append({"plan_id": e.get("plan_id"), "exit": ts,
                            "realized_usd": realized, "reason": e.get("reason")})
        if ts == today:
            out["today"] += 1
        try:
            d = datetime.fromisoformat(e.get("utc_ts", "").replace("Z", "+00:00"))
            if d.isocalendar()[:2] == iso_week[:2]:
                out["week"] += 1
            if d.strftime("%Y-%m") == now.strftime("%Y-%m"):
                out["month"] += 1
        except Exception:  # noqa: BLE001
            pass
    return out


def stats_overview():
    """交易统计: 胜率/盈利因子/期望/回撤 等(from reviews; 样本少时如实显示)。"""
    rv = []
    if REVIEW_DIR.exists():
        for f in REVIEW_DIR.glob("RV-*.json"):
            try:
                rv.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
    pnls = [r.get("realized", {}).get("pnl_usd") for r in rv
            if r.get("realized", {}).get("pnl_usd") is not None]
    n = len(pnls)
    out = {"n_trades": n, "win_rate": None, "profit_factor": None,
           "expectancy": None, "avg_win": None, "avg_loss": None,
           "max_drawdown": None, "total_pnl": None, "note": ""}
    if n == 0:
        out["note"] = "暂无已平仓交易(真实前向样本积累中)"
        return out
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x <= 0]
    gw = sum(wins)
    gl = abs(sum(losses))
    out.update(
        win_rate=round(len(wins) / n, 3),
        profit_factor=round(gw / gl, 2) if gl > 0 else None,
        expectancy=round(sum(pnls) / n, 2),
        avg_win=round(gw / len(wins), 2) if wins else None,
        avg_loss=round(gl / len(losses), 2) if losses else None,
        total_pnl=round(sum(pnls), 2),
        max_drawdown=None)
    # equity 曲线暂缺 → 回撤 UNKNOWN(样本>20 再算)
    return out


def positions_open():
    """当前持仓(快照 + 浮盈)。"""
    out = []
    if not POS_DIR.exists():
        return out
    for p in sorted(POS_DIR.glob("*.json")):
        try:
            snap = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if snap.get("state") == "CLOSED":
            continue
        out.append(snap)
    return out


def decisions_recent(n=10):
    """最近决策(供 Dashboard 显示 Hermes 判断)。"""
    fs = sorted((RUN / "decisions").glob("*.json"), key=lambda x: x.stat().st_mtime) \
        if (RUN / "decisions").exists() else []
    out = []
    for f in fs[-n:]:
        d = _read(f)
        if d:
            out.append({"file": f.name, "decision": d.get("decision"),
                        "utc_ts": d.get("utc_ts"), "opportunity": d.get("opportunity"),
                        "reason": ((d.get("answers_14") or {}).get("14") or "")[:120]})
    return out


def market_state_summary():
    """状态包摘要(D1/H4/H1/M15)。"""
    pkg = _read(RUN / "state_package_latest.json")
    if not pkg:
        return {}
    return pkg.get("market_state", {})


def all_summary():
    """Dashboard 一次取全(避免多文件读)。"""
    st = _read(STATS_P)
    return {
        "account": account(),
        "trades": trades(),
        "stats": stats_overview(),
        "positions": positions_open(),
        "decisions": decisions_recent(),
        "market": market_state_summary(),
        "counters": st.get("counters", {}),
        "waits": st.get("waits", {}),
        "invariants": st.get("last_invariants", {}),
    }
