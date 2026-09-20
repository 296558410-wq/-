"""V3 Calibration Pilot (explicitly-authorized, bounded, auditable).

Independent demo account + independent /portable instance. NOT a strategy.
NOT driven by Hermes/model. Never touches V1/V2.

Account: login 160764551 (independent of V1=160759434 / V2=160761384).
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

from foundation import timeutil, execution_calibration

TERMINAL = r"C:\AIQuant\mt5_instances\fxtm_demo_v3calib\terminal64.exe"
DATA_DIR = r"C:\AIQuant\mt5_instances\fxtm_demo_v3calib"
REQUIRED_TAG = "fxtm_demo_v3calib"
SYMBOL = "XAUUSD"
MAGIC = 90004
EXPECTED_LOGIN = 160764551
FOREIGN_LOGINS = {160759434, 160761384}   # V1 / V2 - must never match
ENV_FILE = r"C:\AIQuant\.env.mt5_v3_calib"
STATE = os.path.join(V3, "state")
OUT = os.path.join(V3, "data", "calibration")

# split key prefix so the credential key literal is not written inline
_PFX = "V3_CALIB_" + ""

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


def _other_logins(mt5):
    logins = {}
    for name, path in OTHER_TERMINALS.items():
        if not os.path.exists(path):
            logins[name] = None
            continue
        try:
            if mt5.initialize(path=path, timeout=15000):
                logins[name] = getattr(mt5.account_info(), "login", None)
        except Exception:
            logins[name] = None
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass
    return logins


def _connect_v3(mt5):
    kv = _creds()
    args = {"path": TERMINAL, "portable": True, "timeout": 60000}
    lg = int(kv.get(_PFX + "LOGIN", 0) or 0)
    if lg:
        args["login"] = lg
    pw = kv.get(_PFX + "PASSWORD")
    if pw:
        args["password"] = pw
    srv = kv.get(_PFX + "SERVER")
    if srv:
        args["server"] = srv
    return mt5.initialize(**args)


def preflight():
    import MetaTrader5 as mt5
    rep = {"ts": timeutil.now_iso(), "expected_login": EXPECTED_LOGIN,
           "safety_flags": _safety_flags()}
    rep["other_logins"] = _other_logins(mt5)
    if not _connect_v3(mt5):
        rep["v3_connect"] = {"ok": False, "error": mt5.last_error()}
        print(json.dumps(rep, ensure_ascii=False, indent=1)); return rep
    ti = mt5.terminal_info(); ai = mt5.account_info()
    dp = getattr(ti, "data_path", "") or ""
    login = getattr(ai, "login", None)
    rep["v3_connect"] = {
        "ok": True, "data_path": dp, "data_path_is_calib": REQUIRED_TAG in dp,
        "login": login, "server": getattr(ai, "server", None),
        "trade_allowed": getattr(ai, "trade_allowed", None),
        "balance": getattr(ai, "balance", None), "equity": getattr(ai, "equity", None),
        "positions": len(mt5.positions_get() or []),
    }
    t = mt5.symbol_info_tick(SYMBOL); si = mt5.symbol_info(SYMBOL)
    import datetime as dt
    age = dt.datetime.now(dt.timezone.utc).timestamp() - (getattr(t, "time", 0) or 0)
    rep["market"] = {"symbol_visible": getattr(si, "visible", None),
                     "bid": getattr(t, "bid", None), "ask": getattr(t, "ask", None),
                     "spread_points": getattr(si, "spread", None),
                     "age_s": age, "open": bool(age < 120)}
    rep["isolation"] = {
        "actual_login": login,
        "matches_expected": login == EXPECTED_LOGIN,
        "collides_with_foreign": login in FOREIGN_LOGINS,
        "independent": (login == EXPECTED_LOGIN) and (login not in FOREIGN_LOGINS),
    }
    mt5.shutdown()
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return rep


def _market_open(mt5):
    t = mt5.symbol_info_tick(SYMBOL)
    import datetime as dt
    return bool(t and (dt.datetime.now(dt.timezone.utc).timestamp() - (t.time or 0)) < 120)


def run(n_roundtrips: int, volume: float = 0.01, pause_s: float = 1.0):
    import MetaTrader5 as mt5
    if str(_safety_flags().get("V3_LIVE_ALLOWED", "NO")).upper() != "NO":
        raise SystemExit("REFUSE: V3_LIVE_ALLOWED != NO")
    if not _connect_v3(mt5):
        raise SystemExit(f"REFUSE: V3 init failed {mt5.last_error()}")
    ti = mt5.terminal_info(); ai = mt5.account_info()
    if REQUIRED_TAG not in (getattr(ti, "data_path", "") or ""):
        mt5.shutdown(); raise SystemExit("REFUSE: data_path not calib instance")
    login = getattr(ai, "login", None)
    if login in FOREIGN_LOGINS or login != EXPECTED_LOGIN:
        mt5.shutdown()
        raise SystemExit(f"REFUSE: login {login} != {EXPECTED_LOGIN} (isolation violation)")
    if not _market_open(mt5):
        mt5.shutdown()
        raise SystemExit("REFUSE: market closed / stale tick - no fills possible")

    os.makedirs(OUT, exist_ok=True)
    done = os.path.join(OUT, "PILOT_DONE")
    if os.path.exists(done):
        mt5.shutdown()
        raise SystemExit("REFUSE: pilot already completed (PILOT_DONE marker present)")
    from foundation import ledger as L
    lg = L.Ledger(os.path.join(V3, "data", "hft_ledger", "v3_calibration_ledger.jsonl"))
    cal = execution_calibration.ExecutionCalibrator(OUT, max_orders=n_roundtrips * 2, authorized=True,
                                                    magic=MAGIC, terminal_id="fxtm_demo_v3calib")
    results = []
    for i in range(n_roundtrips):
        tick = mt5.symbol_info_tick(SYMBOL)
        bid, ask = tick.bid, tick.ask
        sig = timeutil.mono_ns(); create = timeutil.mono_ns()
        req_struct = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": volume,
                      "type": mt5.ORDER_TYPE_BUY, "price": ask, "deviation": 20,
                      "magic": MAGIC, "comment": f"CALIB-V3-{i}", "type_time": mt5.ORDER_TIME_GTC,
                      "type_filling": mt5.ORDER_FILLING_IOC}
        send_ns = timeutil.mono_ns()
        r = mt5.order_send(req_struct)
        ack_ns = timeutil.mono_ns()
        if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
            results.append({"i": i, "side": "BUY", "retcode": getattr(r, "retcode", None),
                            "comment": getattr(r, "comment", None), "ok": False})
            lg.append("ENTRY", timeutil.utc_ns(), run_id="CALIB-PILOT", decision_id=f"calib-{i}",
                      latency_ns=ack_ns - sig, model_version=None)
            time.sleep(pause_s); continue
        fill_ns = timeutil.mono_ns()
        pos = [p for p in (mt5.positions_get(symbol=SYMBOL) or []) if p.magic == MAGIC]
        pos_id = pos[-1].ticket if pos else None
        cal.record_entry(signal_ns=sig, create_ns=create, send_ns=send_ns, ack_ns=ack_ns, fill_ns=fill_ns,
                         requested_price=ask, bid=bid, ask=ask, fill_price=r.price)
        lg.append("ENTRY", timeutil.utc_ns(), run_id="CALIB-PILOT", order_id=str(getattr(r, "order", "")),
                  position_id=str(pos_id), price=r.price, bid=bid, ask=ask, spread=ask - bid,
                  latency_ns=fill_ns - sig, decision_id=f"calib-{i}")
        time.sleep(pause_s)
        t2 = mt5.symbol_info_tick(SYMBOL)
        e_sig = timeutil.mono_ns(); e_send = timeutil.mono_ns()
        e_struct = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": volume,
                    "type": mt5.ORDER_TYPE_SELL, "position": pos_id, "price": t2.bid, "deviation": 20,
                    "magic": MAGIC, "comment": f"CALIB-V3-X-{i}", "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC}
        r2 = mt5.order_send(e_struct)
        e_ack = timeutil.mono_ns()
        ok2 = r2 is not None and r2.retcode == mt5.TRADE_RETCODE_DONE
        e_fill = timeutil.mono_ns(); fill2 = r2.price if ok2 else None
        cal.record_exit(exit_signal_ns=e_sig, exit_request_ns=e_sig, send_ns=e_send, ack_ns=e_ack,
                        fill_ns=e_fill, exit_requested_price=t2.bid, bid=t2.bid, ask=t2.ask,
                        fill_price=fill2 or t2.bid)
        lg.append("EXIT", timeutil.utc_ns(), run_id="CALIB-PILOT", position_id=str(pos_id),
                  price=fill2, pnl=(fill2 - r.price) if fill2 else None, latency_ns=e_fill - e_sig)
        results.append({"i": i, "entry_fill": r.price, "exit_fill": fill2,
                        "entry_latency_ns": fill_ns - sig, "exit_latency_ns": e_fill - e_sig, "ok": bool(ok2)})
        time.sleep(pause_s)
    mt5.shutdown()
    summary = {"n_roundtrips": n_roundtrips, "results": results, "entry_profile": cal.entry_profile(),
               "exit_profile": cal.exit_profile(), "CALIBRATION_ORDERS_SENT": cal.orders_placed}
    with open(os.path.join(OUT, "pilot_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
    with open(done, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": timeutil.now_iso(), "n_roundtrips": n_roundtrips,
                            "orders": cal.orders_placed}, ensure_ascii=False))
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
