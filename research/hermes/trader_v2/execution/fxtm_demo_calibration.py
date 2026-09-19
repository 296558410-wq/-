# -*- coding: utf-8 -*-
"""FXTM Demo 校准 Phase-1 —— 只读行情同步（**绝不下单**）。

- 只附加到 **测试实例**（数据目录含 fxtm_demo_01），绝不碰 V1 终端。
- 只读 XAUUSD bid/ask + 记录 request/response 时间戳与延迟。
- 本模块**不包含**任何下单/改单/平仓能力；调用即拒绝。
用法: python fxtm_demo_calibration.py --seconds 30 --interval 1 [--symbol XAUUSD]
产出: state/demo_calibration/quotes_<utc>.jsonl + 控制台/摘要
"""
from __future__ import annotations
import argparse, json, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state" / "demo_calibration"
TEST_EXE = r"C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe"
READ_ONLY = True
# 用拼接构造, 避免“模式字符串”自匹配导致误报
_P = "order_" + "send(", "order_" + "check(", "positions_" + "close(", "trade_action_" + "modify"
FORBIDDEN_CALLS = _P


def _now():
    return datetime.now(timezone.utc).isoformat()


class RefuseWrite(Exception):
    pass


def attach():
    """附加到测试实例(仅测试目录)。不登录(终端已登录), 不启动 V1。"""
    import MetaTrader5 as mt5
    ok = mt5.initialize(path=TEST_EXE, portable=True, timeout=60000)
    ti = mt5.terminal_info()
    if not ok or ti is None:
        raise RuntimeError(f"attach failed: {mt5.last_error()}")
    if "fxtm_demo_01" not in (ti.data_path or ""):
        mt5.shutdown()
        raise RuntimeError(f"REFUSE: wrong terminal target: {ti.data_path}")
    return mt5


def get_quote(mt5, symbol, ensure_selected=True):
    if ensure_selected:
        mt5.symbol_select(symbol, True)
    req = time.time()
    t = mt5.symbol_info_tick(symbol)
    resp = time.time()
    if t is None:
        return {"ok": False, "error": "no_tick", "symbol": symbol}
    mid = (t.bid + t.ask) / 2
    return {"ok": True, "symbol": symbol, "bid": t.bid, "ask": t.ask,
            "spread": round(t.ask - t.bid, 6),
            "spread_bps": round((t.ask - t.bid) / mid * 1e4, 4) if mid else None,
            "tick_time": int(t.time),
            "req_ts": req, "resp_ts": resp, "latency_ms": round((resp - req) * 1000, 3)}


def sample(symbol="XAUUSD", seconds=30, interval_s=1.0):
    mt5 = attach()
    ti = mt5.terminal_info()
    ai = mt5.account_info()
    rows = []
    t_end = time.time() + seconds
    try:
        while time.time() < t_end:
            rows.append(get_quote(mt5, symbol))
            time.sleep(interval_s)
    finally:
        mt5.shutdown()
    return {"data_path": ti.data_path if ti else None,
            "demo": (ai.trade_mode == 0) if ai else None,
            "symbol": symbol, "rows": rows}


def summarize(res):
    ok = [r for r in res["rows"] if r.get("ok")]
    lat = [r["latency_ms"] for r in ok]
    sp = [r["spread"] for r in ok if r.get("spread") is not None]
    spbps = [r["spread_bps"] for r in ok if r.get("spread_bps") is not None]
    quotes = [{"bid": r["bid"], "ask": r["ask"]} for r in ok]
    return {
        "symbol": res["symbol"], "n_samples": len(res["rows"]), "n_ok": len(ok),
        "latency_ms": {"min": min(lat) if lat else None, "max": max(lat) if lat else None,
                        "mean": round(statistics.mean(lat), 3) if lat else None},
        "spread": {"min": min(sp) if sp else None, "max": max(sp) if sp else None,
                   "mean": round(statistics.mean(sp), 4) if sp else None},
        "spread_bps": {"min": min(spbps) if spbps else None, "max": max(spbps) if spbps else None,
                       "mean": round(statistics.mean(spbps), 4) if spbps else None},
        "first_quote": quotes[0] if quotes else None, "last_quote": quotes[-1] if quotes else None,
        "data_path": res["data_path"], "demo": res["demo"],
    }


def assert_no_write_api():
    """自证: 本模块不含任何写接口的实际调用。"""
    src = Path(__file__).read_text(encoding="utf-8").lower()
    return [c for c in FORBIDDEN_CALLS if c in src]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--seconds", type=int, default=30)
    ap.add_argument("--interval", type=float, default=1.0)
    a = ap.parse_args()
    bad = assert_no_write_api()
    if bad:
        print("REFUSE: module unexpectedly contains write API:", bad); return 2
    res = sample(a.symbol, a.seconds, a.interval)
    summ = summarize(res)
    STATE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    p = STATE / f"quotes_{stamp}.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in res["rows"]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (STATE / f"summary_{stamp}.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False), encoding="utf-8")
    print("WROTE", p.name, "| samples", summ["n_samples"], "ok", summ["n_ok"])
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    print("READ_ONLY: no orders placed")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
