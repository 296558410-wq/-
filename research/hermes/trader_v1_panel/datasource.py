# -*- coding: utf-8 -*-
"""V1 控制面板 — 数据层（READ-ONLY）。

只读 V1 的产物文件与行情文件；**绝不修改 V1 任何东西**、不 import V1 代码、不打开 MT5 终端
（避免与 V1 的 MT5 用法冲突）。价格行情用 V1 dashboard 已写出的 quote_latest.json + tick parquet。
"""
from __future__ import annotations
import json, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path("C:/AIQuant")
V1 = REPO / "research" / "hermes" / "trader_v1"
RS = V1 / "run_state"
LIVE = REPO / "data" / "live_fxtm"
QUOTE = LIVE / "quote_latest.json"
HOURS = REPO / "research" / "hermes" / "trading_hours.py"


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def _rj(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return default


def _rjl(p, limit=None, tail=True):
    out = []
    try:
        lines = Path(p).read_text(encoding="utf-8-sig", errors="replace").splitlines()
        if limit:
            lines = lines[-limit:] if tail else lines[:limit]
        for ln in lines:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:  # noqa: BLE001
                    pass
    except Exception:  # noqa: BLE001
        pass
    return out


def _age(ts):
    if not ts:
        return None
    try:
        return max(0, int((_now() - datetime.fromisoformat(str(ts).replace("Z", "+00:00"))).total_seconds()))
    except Exception:  # noqa: BLE001
        return None


def session_now():
    try:
        import importlib.util as u
        spec = u.spec_from_file_location("th", str(HOURS))
        m = u.module_from_spec(spec); spec.loader.exec_module(m)
        s = m.status()
        return {"open": s["open"], "armed": s["armed"], "reason": s["reason"], "weekday": s["weekday"]}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


# ---- caches ----
_C = {"bars": (0, None), "pos": (0, None)}
_ACC = {"ts": 0.0, "data": None}


def account():
    """只读拉取 demo 账户（复用 V1 自带的 fail-closed demo-only 守卫，隔离子进程调用；
    不修改 V1、不落盘、不写凭据）。"""
    if time.time() - _ACC["ts"] < 30 and _ACC["data"]:
        return _ACC["data"]
    import subprocess
    py = r"C:\AIQuant\.venv\Scripts\python.exe"
    code = ("import sys,json;sys.path.insert(0,r'C:/AIQuant/research/hermes/trader_v1');"
            "import broker_mt5_demo as B;print(json.dumps(B.get_account(),ensure_ascii=False))")
    d = {"ok": False, "error": "unavailable"}
    try:
        r = subprocess.run([py, "-c", code], capture_output=True, text=True, timeout=30)
        out = (r.stdout or "").strip().splitlines()
        if out:
            d = json.loads(out[-1])
        elif r.stderr:
            d = {"ok": False, "error": (r.stderr.strip().splitlines() or ["err"])[-1][:120]}
    except Exception as e:  # noqa: BLE001
        d = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    _ACC.update(ts=time.time(), data=d)
    return d


def quote():
    q = _rj(QUOTE, {}) or {}
    if not q:
        return None
    q["age_s"] = _age(q.get("utc_ts"))
    return q


def bars_m15(n=90):
    if time.time() - _C["bars"][0] < 25 and _C["bars"][1]:
        return _C["bars"][1]
    out = []
    try:
        import pandas as pd
        fs = sorted(LIVE.glob("ticks_*.parquet"))
        if fs:
            df = pd.read_parquet(fs[-1], columns=["ts_utc", "bid", "ask"])
            s = pd.to_datetime(df["ts_utc"], utc=True)
            df = df.assign(t=s).set_index("t")
            o = df["bid"].resample("15min").agg(["first", "max", "min", "last"])
            o = o.dropna()
            o = o.tail(n)
            for ts, r in o.iterrows():
                out.append({"t": ts.isoformat(), "o": round(float(r["first"]), 2), "h": round(float(r["max"]), 2),
                            "l": round(float(r["min"]), 2), "c": round(float(r["last"]), 2)})
    except Exception as e:  # noqa: BLE001
        out = [{"error": str(e)}]
    _C["bars"] = (time.time(), out)
    return out


def positions():
    if time.time() - _C["pos"][0] < 15 and _C["pos"][1]:
        return _C["pos"][1]
    fs = sorted((RS / "positions").glob("*.json"), key=lambda p: p.stat().st_mtime)
    openp, closed, wins, losses, realized, gross_w, gross_l = [], 0, 0, 0, 0.0, 0.0, 0.0
    for f in fs:
        d = _rj(f) or {}
        pid = d.get("position_id"); side = d.get("side"); state = d.get("state")
        entry = None; exitp = None; pnl = None; reason = None; stop = d.get("stop_level")
        for e in d.get("events", []):
            if e.get("event") == "FILL":
                entry = (e.get("payload") or {}).get("price") or entry
            if e.get("event") == "EXIT_FILL":
                pl = e.get("payload") or {}
                exitp = pl.get("price"); pnl = pl.get("realized_usd"); reason = pl.get("reason")
        if state == "OPEN":
            openp.append({"position_id": pid, "side": side, "entry": entry, "stop": stop,
                          "tp": d.get("tp_levels"), "mfe": d.get("mfe"), "mae": d.get("mae"),
                          "opened": d.get("created_utc"), "ticket": d.get("broker_ticket")})
        elif state == "CLOSED" and pnl is not None:
            closed += 1; realized += pnl
            if pnl >= 0: wins += 1; gross_w += pnl
            else: losses += 1; gross_l += pnl
    stats = {"closed": closed, "wins": wins, "losses": losses,
             "win_rate": (round(wins / closed, 3) if closed else None),
             "realized_usd": round(realized, 2),
             "avg_win": (round(gross_w / wins, 2) if wins else None),
             "avg_loss": (round(gross_l / losses, 2) if losses else None),
             "profit_factor": (round(abs(gross_w / gross_l), 2) if gross_l else None)}
    res = {"open": openp[::-1][:8], "stats": stats, "n_files": len(fs)}
    _C["pos"] = (time.time(), res)
    return res


def recent_decisions(n=10):
    fs = sorted((RS / "decisions").glob("*.json"), key=lambda p: p.stat().st_mtime)[-n:]
    out = []
    for f in fs[::-1]:
        d = _rj(f) or {}
        out.append({"cycle": d.get("cycle"), "decision": d.get("decision"), "confidence": d.get("confidence"),
                    "bias": (d.get("bias") or "")[:160], "opportunity": d.get("opportunity")})
    return out


def plan_tail(n=8):
    ev = _rjl(RS / "plan_ledger.jsonl", limit=n)
    out = []
    for e in ev[::-1]:
        p = e.get("plan") or {}
        out.append({"type": e.get("type"), "plan_id": e.get("plan_id"), "decision": e.get("decision"),
                    "direction": p.get("direction"), "zone": p.get("entry_zone"),
                    "trigger": p.get("trigger_condition"), "SL": (p.get("stop_logic") or {}).get("level_price"),
                    "tp": p.get("target_logic"), "R": p.get("expected_R"), "EV": (p.get("expected_net_EV") or {}).get("value"),
                    "reason": e.get("reason"), "ts": e.get("utc_ts")})
    return out


def summary_tail(n=8):
    try:
        lines = [l for l in (RS / "trader_summary.txt").read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        return lines[-n:][::-1]
    except Exception:  # noqa: BLE001
        return []


def build_snapshot():
    sp = _rj(RS / "state_package_latest.json", {}) or {}
    wf = _rj(RS / "workflow_latest.json", {}) or {}
    st = _rj(RS / "statistics.json", {}) or {}
    cl = _rj(RS / "candle_latest.json", {}) or {}
    q = quote()
    pos = positions()
    ms = sp.get("market_state") or {}
    # live pnl for open positions
    if q and q.get("mid"):
        for p in pos["open"]:
            if p.get("entry"):
                d = (q["mid"] - p["entry"]) if p["side"] == "LONG" else (p["entry"] - q["mid"])
                p["live_pt"] = round(d, 2)
    waits = st.get("waits") or {}
    top_wait = sorted((waits.get("wait_reasons") or {}).items(), key=lambda kv: -kv[1])[:6]
    steps = [{"step": s.get("step"), "status": s.get("status"), "result": str(s.get("result"))[:70]}
             for s in (wf.get("steps") or [])]
    tf_rows = []
    for k in ("d1", "h4", "h1", "m15", "m15_live"):
        t = ms.get(k) or {}
        if not t:
            continue
        tf_rows.append({"tf": t.get("tf", k.upper()), "close": t.get("last_close"), "rsi": t.get("rsi14"),
                        "ma20": (t.get("ma") or {}).get("ma20"), "atr_pct": t.get("atr_pct_last"),
                        "cat": (t.get("trend_range") or {}).get("cat"), "er": (t.get("trend_range") or {}).get("er"),
                        "pos": (t.get("s_r") or {}).get("pos_in_range"), "exp": (t.get("exp_cont") or {}).get("state"),
                        "last_bar": t.get("last_bar")})
    return {"now": _iso(_now()), "ts": time.time(), "schema": "v1panel/1",
            "session": session_now(), "quote": q, "account": account(),
            "cycle": sp.get("cycle"), "pkg_generated": sp.get("generated_utc"), "pkg_age_s": _age(sp.get("generated_utc")),
            "data_quality": sp.get("data_quality"),
            "counters": st.get("counters") or {}, "waits": {"consecutive": waits.get("consecutive_waits"),
            "last_ts": waits.get("last_wait_ts"), "last_reason": waits.get("last_reason"), "top": top_wait},
            "invariants": st.get("last_invariants") or {}, "integrity": st.get("integrity") or {},
            "workflow": {"cycle": wf.get("cycle"), "generated": wf.get("generated_utc"), "steps": steps},
            "tf": tf_rows, "candle": cl.get("last") or {},
            "plans": plan_tail(), "decisions": recent_decisions(),
            "positions": pos, "summary": summary_tail(), "bars": bars_m15(),
            "alerts": _alerts(q, st, sp)}


def _alerts(q, st, sp):
    a = []
    if not q or (q.get("age_s") or 9999) > 90:
        a.append({"lvl": "warn", "msg": f"行情快照偏旧 (age={q.get('age_s') if q else '—'}s)"})
    inv = st.get("last_invariants") or {}
    if inv.get("pass") is False:
        a.append({"lvl": "bad", "msg": "invariants FAILED: " + ",".join(inv.get("failed") or [])})
    return a


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    s = build_snapshot()
    for k, v in s.items():
        if isinstance(v, list):
            print(k, f"[{len(v)}]")
        elif k in ("quote", "session", "positions", "waits", "invariants", "data_quality"):
            print(k, json.dumps(v, ensure_ascii=False)[:220])
