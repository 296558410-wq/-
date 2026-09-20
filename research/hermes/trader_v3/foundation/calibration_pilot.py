"""V3-HFT-CALIBRATION-PILOT-001: real MT5 demo execution calibration.

NOT a strategy. NOT alpha. Measures the real broker execution chain
(request -> fill -> close -> cost -> reconciliation -> ledger).

Hard rules:
- independent V3 demo instance only (login 160764551, /portable, data_path *_v3calib)
- MAGIC=90004; comment CALIB-V3; CALIBRATION_ORDER=true
- MAX_CALIBRATION_ROUND_TRIPS = 20 (HARD CAP; CALIBRATION_AUTO_STOP at cap)
- frozen direction sequence + frozen holding sequence (hashed, pre-registered)
- NO_AUTO_RETRY=TRUE; any UNKNOWN -> HALT
- any safety-gate failure -> CALIBRATION_STATUS=HALTED
- MOCK_EXECUTION=FALSE for the real run
- never touches V1/V2
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)
sys.path.insert(0, V3)

from foundation import timeutil, ledger as LED

# ---- spec constants (frozen) ----
MAX_ROUND_TRIPS = 20
SYMBOL = "XAUUSD"
MAGIC = 90004
EXPECTED_LOGIN = 160764551
FOREIGN_LOGINS = {160759434, 160761384}
SERVER_EXPECTED = "ForexTimeFXTM-Demo01"
TERMINAL = r"C:\AIQuant\mt5_instances\fxtm_demo_v3calib\terminal64.exe"
REQUIRED_TAG = "fxtm_demo_v3calib"
ENV_FILE = r"C:\AIQuant\.env.mt5_v3_calib"
STATE = os.path.join(V3, "state")
OUT = os.path.join(V3, "data", "calibration")
LEDGER_PATH = os.path.join(V3, "data", "hft_ledger", "v3_calibration_ledger.jsonl")
_PFX = "V3_CALIB_" + ""

DIRECTIONS = (["LONG", "SHORT"] * 10)[:MAX_ROUND_TRIPS]
HOLDS_MS = ([100, 250, 500, 1000, 2000] * 4)[:MAX_ROUND_TRIPS]
SEQ_HASH = hashlib.sha256(json.dumps({"dir": DIRECTIONS, "hold": HOLDS_MS},
                                     separators=(",", ":")).encode()).hexdigest()

OTHER_TERMINALS = {
    "v1_host": r"C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe",
    "v2_fxtm_demo_01": r"C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe",
}


# ---- helpers ----
def _creds():
    kv = {}
    if os.path.exists(ENV_FILE):
        for ln in open(ENV_FILE, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                kv[k.strip()] = v.strip().strip('"').strip("'")
    return kv


def _flags():
    out = {}
    for k in ("V3_LIVE_ALLOWED", "V3_ORDER_SEND_ALLOWED", "V3_FORWARD_ALLOWED"):
        try:
            out[k] = open(os.path.join(STATE, k), encoding="utf-8").read().strip()
        except Exception:
            out[k] = "NO"
    return out


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


def _acct(mt5):
    a = mt5.account_info()
    return {k: getattr(a, k, None) for k in
            ("login", "server", "balance", "equity", "margin_free", "margin_level",
             "margin", "trade_allowed")}


def _spec(mt5):
    s = mt5.symbol_info(SYMBOL)
    return {k: getattr(s, k, None) for k in
            ("name", "digits", "point", "trade_tick_size", "trade_tick_value",
             "trade_contract_size", "volume_min", "volume_step", "volume_max",
             "spread", "visible", "trade_mode")}


def _pos(mt5):
    return [p for p in (mt5.positions_get(symbol=SYMBOL) or []) if p.magic == MAGIC]


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))
    return xs[i]


def _stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "mean": sum(xs) / len(xs), "median": _median(xs), "p50": _median(xs),
            "p95": _pct(xs, 95), "p99": _pct(xs, 99), "min": min(xs), "max": max(xs)}


class Halt(RuntimeError):
    pass


def _write_state(name, obj):
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=str)


# ---- selftest (MOCK, never counted) ----
class _FakeMT5:
    """Mock broker for chain validation only. MOCK_EXECUTION=TRUE, not calibration data."""
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009

    class _R:
        def __init__(self, price, retcode=10009, order=1):
            self.price = price; self.retcode = retcode; self.order = order; self.comment = "mock"

    def __init__(self):
        self._t = 0

    def symbol_info_tick(self, s):
        self._t += 1
        return type("T", (), {"bid": 2000.0 + self._t * 0.01, "ask": 2000.2 + self._t * 0.01,
                              "time": time.time()})()

    def order_send(self, req):
        return self._R(req["price"] + 0.01)


def selftest():
    """Validate measurement/profile/reconciliation math on MOCK data (not calibration)."""
    import random
    rng = random.Random(0)
    samples = []
    for i in range(20):
        hold = HOLDS_MS[i]
        e = {"calibration_id": f"MOCK-{i}", "direction": DIRECTIONS[i], "hold_target_ms": hold,
             "valid_entry": True, "valid_exit": True}
        e["signal_to_request_ms"] = rng.uniform(0.01, 0.1)
        e["request_to_ack_ms"] = rng.uniform(5, 40)
        e["ack_to_fill_ms"] = rng.uniform(1, 10)
        e["signal_to_fill_ms"] = e["signal_to_request_ms"] + e["request_to_ack_ms"] + e["ack_to_fill_ms"]
        e["entry_slippage_bps"] = rng.uniform(-0.5, 1.5)
        e["exit_slippage_bps"] = rng.uniform(-1.5, 0.5)
        e["spread_bps"] = rng.uniform(1.2, 2.2)
        e["commission"] = 0.0
        samples.append(e)
    prof = _profiles(samples)
    ok = prof["ENTRY_LATENCY"]["signal_to_fill_ms"]["n"] == 20
    print(json.dumps({"MOCK_EXECUTION": True, "labels": "MOCK_DATA", "samples": 20,
                      "chain_ok": ok, "profiles": prof}, ensure_ascii=False, indent=1))
    return ok


# ---- profiles ----
def _profiles(samples):
    en = [s for s in samples if s.get("valid_entry")]
    ex = [s for s in samples if s.get("valid_exit")]
    return {
        "ENTRY_LATENCY": {
            "signal_to_request_ms": _stats([s.get("signal_to_request_ms") for s in en]),
            "request_to_ack_ms": _stats([s.get("request_to_ack_ms") for s in en]),
            "ack_to_fill_ms": _stats([s.get("ack_to_fill_ms") for s in en]),
            "signal_to_fill_ms": _stats([s.get("signal_to_fill_ms") for s in en]),
        },
        "EXIT_LATENCY": {
            "exit_signal_to_fill_ms": _stats([s.get("exit_latency_ms") for s in ex]),
        },
        "ENTRY_SLIPPAGE": _stats([s.get("entry_slippage_bps") for s in en]),
        "EXIT_SLIPPAGE": _stats([s.get("exit_slippage_bps") for s in ex]),
        "SPREAD_BPS": _stats([s.get("spread_bps") for s in samples]),
    }


def _slippage_signs(samples):
    out = {}
    for side, key in (("entry", "entry_slippage_bps"), ("exit", "exit_slippage_bps")):
        xs = [s.get(key) for s in samples if s.get(key) is not None]
        out[side] = {"positive": sum(1 for x in xs if x > 0),
                     "negative": sum(1 for x in xs if x < 0),
                     "zero": sum(1 for x in xs if x == 0)}
    return out


# ---- real run ----
def run(n_roundtrips: int = MAX_ROUND_TRIPS, mock: bool = False):
    import MetaTrader5 as mt5
    if n_roundtrips > MAX_ROUND_TRIPS:
        raise SystemExit(f"REFUSE: n={n_roundtrips} > MAX_CALIBRATION_ROUND_TRIPS={MAX_ROUND_TRIPS}")
    if str(_flags().get("V3_LIVE_ALLOWED", "NO")).upper() != "NO":
        raise SystemExit("REFUSE: V3_LIVE_ALLOWED != NO")
    if mock:
        raise SystemExit("REFUSE: MOCK_EXECUTION is not permitted for the calibration run (see selftest)")

    if not _connect_v3(mt5):
        raise SystemExit(f"REFUSE: V3 init failed {mt5.last_error()}")
    ti = mt5.terminal_info(); ai = mt5.account_info()
    dpath = getattr(ti, "data_path", "") or ""
    login = getattr(ai, "login", None)
    if REQUIRED_TAG not in dpath:
        mt5.shutdown(); raise SystemExit("REFUSE: data_path not V3 isolated instance")
    if login != EXPECTED_LOGIN or login in FOREIGN_LOGINS:
        mt5.shutdown(); raise SystemExit(f"REFUSE: login {login} != {EXPECTED_LOGIN}")

    spec = _spec(mt5)
    volume = float(spec["volume_min"] or 0.01)  # FIXED = broker minimum
    acct0 = _acct(mt5)
    pos0 = _pos(mt5)
    if pos0:
        mt5.shutdown()
        raise SystemExit(f"REFUSE: unexpected initial positions {[p.ticket for p in pos0]}")
    if not _market_open(mt5):
        mt5.shutdown()
        raise SystemExit("REFUSE: market closed / stale tick")

    os.makedirs(OUT, exist_ok=True)
    done_marker = os.path.join(OUT, "PILOT_DONE")
    if os.path.exists(done_marker):
        mt5.shutdown(); raise SystemExit("REFUSE: pilot already completed (PILOT_DONE)")

    lg = LED.Ledger(LEDGER_PATH)
    lg.append("CALIBRATION_START", timeutil.utc_ns(), run_id="CALIB-PILOT-001",
              model_version=None, decision_id="calibration")

    samples = []
    halt_reason = None
    started = timeutil.now_iso()
    for i in range(n_roundtrips):
        try:
            s = _round_trip(mt5, i, float(volume), lg)
        except Halt as h:
            halt_reason = str(h)
            break
        samples.append(s)
    lg.append("CALIBRATION_COMPLETE", timeutil.utc_ns(), run_id="CALIB-PILOT-001",
              decision_id=f"roundtrips={len(samples)}")

    pos1 = _pos(mt5)
    acct1 = _acct(mt5)
    mt5.shutdown()

    # reconcile
    valid_entry = [s for s in samples if s.get("valid_entry")]
    valid_exit = [s for s in samples if s.get("valid_exit")]
    reconciled = [s for s in samples if s.get("reconciliation") == "PASS"]
    profiles = _profiles(samples)
    registry = [{k: s.get(k) for k in
                 ("calibration_id", "order_id", "entry_deal_id", "exit_deal_id", "direction",
                  "hold_target_ms", "hold_actual_ms", "entry_fill_price", "exit_fill_price",
                  "entry_slippage_bps", "exit_slippage_bps", "commission", "swap",
                  "reconciliation", "sample_hash")} for s in samples]

    if halt_reason:
        status = "HALTED"
    elif not valid_entry or not valid_exit:
        status = "INCOMPLETE"
    elif all(s.get("reconciliation") == "PASS" for s in samples) and len(samples) >= 1:
        status = "PASS"
    else:
        status = "PARTIAL"

    pilot = {
        "schema": "v3_calibration_pilot/1",
        "task_id": "V3-HFT-CALIBRATION-PILOT-001",
        "started_utc": started, "finished_utc": timeutil.now_iso(),
        "status": status,
        "halt_reason": halt_reason,
        "MAX_CALIBRATION_ROUND_TRIPS": MAX_ROUND_TRIPS,
        "CALIBRATION_AUTO_STOP": len(samples) >= MAX_ROUND_TRIPS,
        "n_samples": len(samples),
        "VALID_ENTRY_FILL_SAMPLE": len(valid_entry),
        "VALID_EXIT_FILL_SAMPLE": len(valid_exit),
        "RECONCILIATION": "PASS" if samples and len(reconciled) == len(samples) else "PARTIAL",
        "frozen_sequence_hash": SEQ_HASH,
        "directions": list(DIRECTIONS), "holds_ms": list(HOLDS_MS),
        "volume": volume, "spec": spec,
        "account_before": acct0, "account_after": acct1,
        "V3_INITIAL_POSITIONS": len(pos0), "V3_FINAL_POSITIONS": len(pos1),
        "V3_CALIBRATION_OPEN_POSITIONS": len(pos1),
        "MOCK_EXECUTION": False,
        "labels": {"REAL_DATA": len([s for s in samples if s.get("real")]),
                   "MOCK_DATA": 0, "SYNTHETIC_DATA": 0},
        "NO_AUTO_RETRY": True,
        "safety": {"V3_AUTO_TRADING": False, "V3_LIVE": False, "V3_STRATEGY_AUTO_DECISION": False,
                   "V3_HERMES_AUTO_ORDER": False, "V3_MODEL_AUTO_ORDER": False,
                   "V1_UNTOUCHED": True, "V2_UNTOUCHED": True},
        "WAIT_FOR_AUDIT": True,
    }
    _write_state("V3_CALIBRATION_PILOT.json", pilot)
    _write_state("V3_EXECUTION_PROFILE.json", profiles)
    _write_state("V3_COST_PROFILE.json", _cost_profile(samples))
    reg_path = os.path.join(OUT, "registry.jsonl")
    with open(reg_path, "a", encoding="utf-8") as f:
        for r in registry:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    with open(done_marker, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": timeutil.now_iso(), "status": status, "n": len(samples)}))

    out = {"pilot": pilot, "execution_profile": profiles,
           "cost_profile": _cost_profile(samples), "slippage_signs": _slippage_signs(samples)}
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    return out


def _cost_profile(samples):
    rows = []
    for s in samples:
        if s.get("net_pnl") is None:
            continue
        rows.append({
            "calibration_id": s.get("calibration_id"),
            "gross_pnl": s.get("gross_pnl"), "spread_cost": s.get("spread_cost"),
            "entry_slippage": s.get("entry_slippage_price"), "exit_slippage": s.get("exit_slippage_price"),
            "commission": s.get("commission"), "swap": s.get("swap"), "net_pnl": s.get("net_pnl"),
        })
    net = [r["net_pnl"] for r in rows]
    return {"n": len(rows), "round_trip_net_pnl": _stats(net), "rows": rows,
            "NET_ROUND_TRIP_COST": _stats([-x for x in net if x is not None]),
            "commission_source": "MT5 history_deals_get (UNKNOWN if absent)"}


def _market_open(mt5):
    t = mt5.symbol_info_tick(SYMBOL)
    import datetime as dt
    return bool(t and (dt.datetime.now(dt.timezone.utc).timestamp() - (t.time or 0)) < 120)


def _sample_hash(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()


def _round_trip(mt5, i, volume, lg):
    cid = f"V3CAL-{i:02d}"
    hold_target = HOLDS_MS[i]
    direction = DIRECTIONS[i]
    t = mt5.symbol_info_tick(SYMBOL)
    if not t:
        raise Halt("no tick")
    bid, ask = t.bid, t.ask
    mid = (bid + ask) / 2.0
    spread = ask - bid
    import datetime as dt
    stale = (dt.datetime.now(dt.timezone.utc).timestamp() - (t.time or 0)) > 120
    if bid <= 0 or ask <= 0 or ask < bid or spread < 0:
        raise Halt(f"bad quote {bid}/{ask}")

    is_long = direction == "LONG"
    sig = timeutil.mono_ns(); req = timeutil.mono_ns()
    order = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if is_long else mt5.ORDER_TYPE_SELL,
        "price": ask if is_long else bid, "deviation": 20, "magic": MAGIC,
        "comment": f"CALIB-V3-{i:02d}", "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    lg.append("ORDER_REQUEST", timeutil.utc_ns(), run_id="CALIB-PILOT-001", decision_id=cid,
              price=order["price"], bid=bid, ask=ask, spread=spread)
    send = timeutil.mono_ns()
    r = mt5.order_send(order)
    ack = timeutil.mono_ns()
    lg.append("BROKER_RESPONSE", timeutil.utc_ns(), run_id="CALIB-PILOT-001", decision_id=cid,
              order_id=str(getattr(r, "order", "")) if r else None,
              price=getattr(r, "price", None))
    if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
        raise Halt(f"UNKNOWN entry retcode={getattr(r,'retcode',None)} (NO_AUTO_RETRY)")
    fill = timeutil.mono_ns()
    fill_price = r.price
    pos = _pos(mt5)
    if len(pos) != 1:
        raise Halt(f"unexpected positions after entry: {len(pos)}")
    pid = pos[0].ticket
    s = {"calibration_id": cid, "direction": direction, "real": True,
         "timestamp_signal": timeutil.utc_ns(), "bid_at_request": bid, "ask_at_request": ask,
         "mid_at_request": mid, "spread_price": spread,
         "spread_bps": (spread / mid * 1e4) if mid else None,
         "requested_price": order["price"], "fill_price": fill_price,
         "signal_to_request_ms": (req - sig) / 1e6, "request_to_ack_ms": (ack - req) / 1e6,
         "ack_to_fill_ms": (fill - ack) / 1e6, "signal_to_fill_ms": (fill - sig) / 1e6,
         "slippage_price": (fill_price - order["price"]) if is_long else (order["price"] - fill_price),
         "order_id": str(getattr(r, "order", "")),
         "STALE_TICK_AT_REQUEST": bool(stale), "hold_target_ms": hold_target}
    s["entry_slippage_bps"] = (s["slippage_price"] / mid * 1e4) if mid else None
    s["valid_entry"] = True
    lg.append("ENTRY_FILL", timeutil.utc_ns(), run_id="CALIB-PILOT-001", decision_id=cid,
              position_id=str(pid), price=fill_price, bid=bid, ask=ask, spread=spread,
              latency_ns=fill - sig)

    # hold then close (fixed, pre-registered)
    t0 = timeutil.mono_ns()
    time.sleep(hold_target / 1000.0)
    t2 = mt5.symbol_info_tick(SYMBOL)
    e_bid, e_ask = t2.bid, t2.ask
    e_mid = (e_bid + e_ask) / 2.0
    e_sig = timeutil.mono_ns()
    e_order = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": volume,
        "type": mt5.ORDER_TYPE_SELL if is_long else mt5.ORDER_TYPE_BUY,
        "position": pid, "price": e_bid if is_long else e_ask, "deviation": 20, "magic": MAGIC,
        "comment": f"CALIB-V3-X-{i:02d}", "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    lg.append("EXIT_REQUEST", timeutil.utc_ns(), run_id="CALIB-PILOT-001", decision_id=cid,
              position_id=str(pid), price=e_order["price"])
    e_send = timeutil.mono_ns()
    r2 = mt5.order_send(e_order)
    e_ack = timeutil.mono_ns()
    if r2 is None or r2.retcode != mt5.TRADE_RETCODE_DONE:
        raise Halt(f"UNKNOWN exit retcode={getattr(r2,'retcode',None)} (NO_AUTO_RETRY)")
    e_fill = timeutil.mono_ns()
    exit_price = r2.price
    s.update({
        "exit_requested_price": e_order["price"], "exit_bid": e_bid, "exit_ask": e_ask,
        "exit_mid": e_mid, "exit_fill_price": exit_price,
        "exit_slippage_price": (e_order["price"] - exit_price) if is_long else (exit_price - e_order["price"]),
        "exit_latency_ms": (e_fill - e_sig) / 1e6,
        "hold_actual_ms": (t2.time - t.time) * 1000 if (t2 and t) else None,
        "valid_exit": True,
    })
    s["exit_slippage_bps"] = (s["exit_slippage_price"] / e_mid * 1e4) if e_mid else None
    if s["hold_actual_ms"] is None or s["hold_actual_ms"] < hold_target * 0.5:
        s["CALIBRATION_HORIZON_LIMITATION"] = True
    lg.append("EXIT_FILL", timeutil.utc_ns(), run_id="CALIB-PILOT-001", decision_id=cid,
              position_id=str(pid), price=exit_price, latency_ns=e_fill - e_sig)

    # deals / commission / swap / reconciliation
    deals = mt5.history_deals_get(position=pid) or []
    comm = swap = 0.0
    raw = {"commission": None, "swap": None}
    entry_deal = exit_deal = None
    for d in deals:
        if d.entry == mt5.DEAL_ENTRY_IN:
            entry_deal = d
        elif d.entry == mt5.DEAL_ENTRY_OUT:
            exit_deal = d
    if deals:
        comm = sum(getattr(d, "commission", 0.0) or 0.0 for d in deals)
        swap = sum(getattr(d, "swap", 0.0) or 0.0 for d in deals)
        raw = {"commission": comm, "swap": swap}
    s["commission"] = raw["commission"]  # None => UNKNOWN (not 0)
    s["swap"] = raw["swap"]
    s["fee"] = None
    s["entry_deal_id"] = getattr(entry_deal, "ticket", None)
    s["exit_deal_id"] = getattr(exit_deal, "ticket", None)
    gross = ((exit_price - fill_price) if is_long else (fill_price - exit_price)) * (s["volume"] if "volume" in s else 0)
    s["gross_pnl"] = (exit_price - fill_price) if is_long else (fill_price - exit_price)
    s["spread_cost"] = spread
    s["net_pnl"] = (s["gross_pnl"] - spread - abs(s["slippage_price"] or 0) - abs(s["exit_slippage_price"] or 0)
                    - (comm if comm is not None else 0))
    recon = (entry_deal is not None and exit_deal is not None and len(_pos(mt5)) == 0)
    s["reconciliation"] = "PASS" if recon else "FAIL"
    if not recon:
        # still record sample but reconciliation failure should stop the pilot
        s["sample_hash"] = _sample_hash(s)
        lg.append("CALIBRATION_COMPLETE", timeutil.utc_ns(), run_id="CALIB-PILOT-001",
                  decision_id=cid, pnl=s["net_pnl"])
        raise Halt(f"RECONCILIATION_FAIL at {cid}")
    s["sample_hash"] = _sample_hash(s)
    lg.append("CALIBRATION_COMPLETE", timeutil.utc_ns(), run_id="CALIB-PILOT-001", decision_id=cid,
              pnl=s["net_pnl"])
    # post-sample gates
    if len(_pos(mt5)) != 0:
        raise Halt("unexpected open position after round trip")
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--n", type=int, default=MAX_ROUND_TRIPS)
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(0 if selftest() else 1)
    elif a.preflight:
        # reuse the light preflight from the earlier build
        import MetaTrader5 as mt5
        rep = {"ts": timeutil.now_iso(), "expected_login": EXPECTED_LOGIN, "safety_flags": _flags()}
        if _connect_v3(mt5):
            ai = mt5.account_info(); ti = mt5.terminal_info()
            rep["v3"] = {"data_path": getattr(ti, "data_path", None), "login": getattr(ai, "login", None),
                         "server": getattr(ai, "server", None), "balance": getattr(ai, "balance", None),
                         "positions": len(_pos(mt5)), "independent": getattr(ai, "login", None) == EXPECTED_LOGIN}
            rep["spec"] = _spec(mt5)
            mt5.shutdown()
        else:
            rep["v3"] = {"ok": False}
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    elif a.run:
        run(a.n)
    else:
        ap.print_help()
