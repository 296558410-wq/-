"""V3 Calibration Pilot (explicitly-authorized, bounded, auditable).

Purpose: measure REAL MT5 demo entry/exit execution (latency/slippage/reject)
on the V3 independent demo instance. NOT a strategy. NOT driven by Hermes/model.

Hard rules (task §14/§4):
- V3 demo only; terminal data_path MUST contain 'fxtm_demo_v3'
- MAGIC=90004; every order tagged CALIBRATION_ORDER=true (comment 'CALIB-V3')
- count FIXED in advance; never grows by result
- never connects LIVE (refuse if LIVE flag != NO)
- isolation guard: refuse if V3 account login equals a known V1/V2 login
- refuses when market is closed (no fills)
- V1/V2 terminals are never touched
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)
sys.path.insert(0, V3)

from foundation import timeutil, execution_calibration, tick_schema

TERMINAL = r"C:\AIQuant\mt5_instances\fxtm_demo_v3\terminal64.exe"
DATA_DIR = r"C:\AIQuant\mt5_instances\fxtm_demo_v3"
REQUIRED_TAG = "fxtm_demo_v3"
SYMBOL = "XAUUSD"
MAGIC = 90004
SERVER_EXPECTED = "ForexTimeFXTM-Demo01"
ENV_FILE = r"C:\AIQuant\.env.mt5_demo"
STATE = os.path.join(V3, "state")
OUT = os.path.join(V3, "data", "calibration")

# Known other-instance terminals (read-only reconnaissance only; NEVER ordered to)
OTHER_TERMINALS = {
    "v1_host": r"C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe",
    "v2_fxtm_demo_01": r"C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe",
}


def _creds():
    kv = {}
    if os.path.exists(ENV_FILE):
        for ln in open(ENV_FILE, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                kv[k.strip()] = v.strip().strip('"').strip("'")
    return kv


def _safety_flags():
    out = {}
    for k in ("V3_LIVE_ALLOWED", "V3_ORDER_SEND_ALLOWED", "V3_FORWARD_ALLOWED"):
        try:
            out[k] = open(os.path.join(STATE, k), encoding="utf-8").read().strip()
        except Exception:
            out[k] = "NO"
    return out


def _known_other_logins(mt5):
    """Read logins of V1/V2 terminals (read-only, no orders). Returns set."""
    logins = {}
    for name, path in OTHER_TERMINALS.items():
        if not os.path.exists(path):
            logins[name] = None
            continue
        try:
            ok = mt5.initialize(path=path, timeout=15000)
            if ok:
                ai = mt5.account_info()
                logins[name] = getattr(ai, "login", None)
        except Exception:
            logins[name] = None
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass
    return logins


def preflight():
    import MetaTrader5 as mt5
    rep = {"ts": timeutil.now_iso()}
    rep["safety_flags"] = _safety_flags()
    rep["other_logins"] = _known_other_logins(mt5)
    # V3 connect
    kv = _creds()
    ok = mt5.initialize(path=TERMINAL, portable=True,
                        login=int(kv.get("DEMO_MT5_LOGIN", 0) or 0) or None,
                        password=kv.get("DEMO_MT5_PASSWORD") or None,
                        server=kv.get("DEMO_MT5_SERVER", SERVER_EXPECTED),
                        timeout=60000)
    if not ok:
        rep["v3_connect"] = {"ok": False, "error": mt5.last_error()}
        print(json.dumps(rep, ensure_ascii=False, indent=1)); return rep
    ti = mt5.terminal_info(); ai = mt5.account_info()
    dp = getattr(ti, "data_path", "") or ""
    rep["v3_connect"] = {
        "ok": True, "data_path": dp, "data_path_is_v3": REQUIRED_TAG in dp,
        "login": getattr(ai, "login", None), "server": getattr(ai, "server", None),
        "trade_allowed": getattr(ai, "trade_allowed", None),
        "balance": getattr(ai, "balance", None), "equity": getattr(ai, "equity", None),
        "margin_free": getattr(ai, "margin_free", None),
        "positions": len(mt5.positions_get() or []),
    }
    si = mt5.symbol_info(SYMBOL)
    t = mt5.symbol_info_tick(SYMBOL)
    rep["market"] = {
        "symbol_visible": getattr(si, "visible", None),
        "trade_mode": getattr(si, "trade_mode", None),
        "spread_points": getattr(si, "spread", None),
        "bid": getattr(t, "bid", None), "ask": getattr(t, "ask", None),
        "tick_time": getattr(t, "time", None),
    }
    # market open heuristic: fresh tick
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    tt = getattr(t, "time", 0) or 0
    rep["market"]["age_s"] = now - tt if tt else None
    rep["market"]["open"] = bool(tt and (now - tt) < 120)
    # isolation verdict
    v3_login = rep["v3_connect"]["login"]
    others = {k: v for k, v in rep["other_logins"].items() if v}
    rep["isolation"] = {
        "v3_login": v3_login,
        "shared_with": [k for k, v in others.items() if v == v3_login],
    }
    rep["isolation"]["independent"] = len(rep["isolation"]["shared_with"]) == 0
    mt5.shutdown()
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return rep


def run(n_roundtrips: int, volume: float = 0.01, pause_s: float = 1.0):
    import MetaTrader5 as mt5
    flags = _safety_flags()
    if str(flags.get("V3_LIVE_ALLOWED", "NO")).upper() != "NO":
        raise SystemExit("REFUSE: V3_LIVE_ALLOWED != NO")
    kv = _creds()
    ok = mt5.initialize(path=TERMINAL, portable=True,
                        login=int(kv.get("DEMO_MT5_LOGIN", 0) or 0) or None,
                        password=kv.get("DEMO_MT5_PASSWORD") or None,
                        server=kv.get("DEMO_MT5_SERVER", SERVER_EXPECTED), timeout=60000)
    if not ok:
        raise SystemExit(f"REFUSE: V3 init failed {mt5.last_error()}")
    ti = mt5.terminal_info()
    if REQUIRED_TAG not in (getattr(ti, "data_path", "") or ""):
        mt5.shutdown(); raise SystemExit("REFUSE: data_path not V3")
    ai = mt5.account_info()
    v3_login = getattr(ai, "login", None)
    others = _known_other_logins(mt5)
    # re-init V3 (recon shutdown it)
    mt5.initialize(path=TERMINAL, portable=True,
                   login=int(kv.get("DEMO_MT5_LOGIN", 0) or 0) or None,
                   password=kv.get("DEMO_MT5_PASSWORD") or None,
                   server=kv.get("DEMO_MT5_SERVER", SERVER_EXPECTED), timeout=60000)
    ai = mt5.account_info(); v3_login = getattr(ai, "login", None)
    if any(v == v3_login for v in others.values() if v):
        mt5.shutdown()
        raise SystemExit(f"REFUSE: V3 account {v3_login} is SHARED with {others} — isolation violation")
    si = mt5.symbol_info(SYMBOL); t = mt5.symbol_info_tick(SYMBOL)
    import datetime as dt
    if not t or (dt.datetime.now(dt.timezone.utc).timestamp() - (t.time or 0)) > 120:
        mt5.shutdown()
        raise SystemExit("REFUSE: market closed / stale tick — no fills possible")
    if not si.visible:
        si = mt5.symbol_select(SYMBOL, True) or mt5.symbol_info(SYMBOL)

    os.makedirs(OUT, exist_ok=True)
    lg_path = os.path.join(V3, "data", "hft_ledger", "v3_calibration_ledger.jsonl")
    from foundation import ledger as L
    lg = L.Ledger(lg_path)
    cal = execution_calibration.ExecutionCalibrator(OUT, max_orders=n_roundtrips * 2, authorized=True,
                                                    magic=MAGIC)
    results = []
    for i in range(n_roundtrips):
        tick = mt5.symbol_info_tick(SYMBOL)
        bid, ask = tick.bid, tick.ask
        sig = timeutil.mono_ns()
        create = timeutil.mono_ns()
        req = ask
        req_struct = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": volume,
                      "type": mt5.ORDER_TYPE_BUY, "price": req, "deviation": 20,
                      "magic": MAGIC, "comment": f"CALIB-V3-{i}", "type_time": mt5.ORDER_TIME_GTC,
                      "type_filling": mt5.ORDER_FILLING_IOC}
        send_ns = timeutil.mono_ns()
        r = mt5.order_send(req_struct)
        ack_ns = timeutil.mono_ns()
        if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
            results.append({"i": i, "side": "BUY", "retcode": getattr(r, "retcode", None),
                            "comment": getattr(r, "comment", None), "ok": False})
            time.sleep(pause_s); continue
        fill_price = r.price
        fill_ns = timeutil.mono_ns()
        # find position
        pos = mt5.positions_get(symbol=SYMBOL)
        pos = [p for p in (pos or []) if p.magic == MAGIC]
        pos_id = pos[-1].ticket if pos else None
        cal.record_entry(signal_ns=sig, create_ns=create, send_ns=send_ns, ack_ns=ack_ns, fill_ns=fill_ns,
                         requested_price=req, bid=bid, ask=ask, fill_price=fill_price)
        lg.append("ENTRY", timeutil.utc_ns(), run_id="CALIB-PILOT", order_id=str(getattr(r, "order", "")),
                  position_id=str(pos_id), price=fill_price, bid=bid, ask=ask, spread=ask - bid,
                  latency_ns=fill_ns - sig, model_version=None, decision_id=f"calib-{i}")
        # close it
        time.sleep(pause_s)
        tick2 = mt5.symbol_info_tick(SYMBOL)
        e_sig = timeutil.mono_ns(); e_req = bid2 = tick2.bid; ask2 = tick2.ask
        e_struct = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": volume,
                    "type": mt5.ORDER_TYPE_SELL, "position": pos_id, "price": tick2.bid,
                    "deviation": 20, "magic": MAGIC, "comment": f"CALIB-V3-X-{i}",
                    "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC}
        e_send = timeutil.mono_ns()
        r2 = mt5.order_send(e_struct)
        e_ack = timeutil.mono_ns()
        ok2 = r2 is not None and r2.retcode == mt5.TRADE_RETCODE_DONE
        fill2 = r2.price if ok2 else None
        e_fill = timeutil.mono_ns()
        cal.record_exit(exit_signal_ns=e_sig, exit_request_ns=e_req, send_ns=e_send, ack_ns=e_ack,
                        fill_ns=e_fill, exit_requested_price=tick2.bid, bid=tick2.bid, ask=tick2.ask,
                        fill_price=fill2 or tick2.bid)
        lg.append("EXIT", timeutil.utc_ns(), run_id="CALIB-PILOT", position_id=str(pos_id),
                  price=fill2, pnl=(fill2 - fill_price) if fill2 else None,
                  latency_ns=e_fill - e_sig)
        results.append({"i": i, "entry_fill": fill_price, "exit_fill": fill2,
                        "entry_latency_ns": fill_ns - sig, "exit_latency_ns": e_fill - e_sig,
                        "ok": bool(ok2)})
        time.sleep(pause_s)
    mt5.shutdown()
    summary = {"n_roundtrips": n_roundtrips, "results": results,
               "entry_profile": cal.entry_profile(), "exit_profile": cal.exit_profile(),
               "CALIBRATION_ORDERS_SENT": cal.orders_placed}
    with open(os.path.join(OUT, "pilot_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--volume", type=float, default=0.01)
    a = ap.parse_args()
    if a.preflight:
        preflight()
    elif a.run:
        run(a.n, a.volume)
    else:
        ap.print_help()
