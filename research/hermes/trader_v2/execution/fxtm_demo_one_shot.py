# -*- coding: utf-8 -*-
"""FXTM Demo 校准 Phase-2 —— 一次性最小 XAUUSD Demo 市价单(BUY) + 立即平仓（仅测试实例）。

硬门 REFUSE_EXECUTION: 非测试目录 / 非 DEMO / server 不符 / 无 symbol / 无 volume_min。
一次下单 + 一次平仓; 无循环/加仓/反向/挂单/重试。默认仅预检, --execute 才发送。
产出 state/demo_calibration/phase2/{order_request,order_response,close_request,close_response,summary}.json
"""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "state" / "demo_calibration" / "phase2"
TEST_EXE = r"C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe"
REQUIRED_SERVER = "ForexTimeFXTM-Demo01"
SYMBOL = "XAUUSD"
EXP_DIRECTION = "BUY"


def _utc():
    return datetime.now(timezone.utc).isoformat()


class RefuseExecution(Exception):
    pass


def mask(s):
    s = str(s)
    return (s[:2] + "*" * max(0, len(s) - 4) + s[-2:]) if len(s) > 4 else "***"


def _load_json():
    return json.loads((ROOT / "config" / "v2_config.json").read_text(encoding="utf-8"))


def connect():
    import MetaTrader5 as mt5
    ok = mt5.initialize(path=TEST_EXE, portable=True, timeout=60000)
    ti = mt5.terminal_info()
    if not ok or ti is None:
        raise RefuseExecution(f"attach_failed:{mt5.last_error()}")
    if "fxtm_demo_01" not in (ti.data_path or ""):
        mt5.shutdown(); raise RefuseExecution(f"wrong_terminal:{ti.data_path}")
    return mt5, ti


def gate(mt5, ti):
    ai = mt5.account_info()
    if ai is None: raise RefuseExecution("no_account")
    if ai.trade_mode != 0: raise RefuseExecution(f"not_demo:{ai.trade_mode}")
    if ai.server != REQUIRED_SERVER: raise RefuseExecution(f"wrong_server:{ai.server}")
    mt5.symbol_select(SYMBOL, True)
    si = mt5.symbol_info(SYMBOL)
    if si is None: raise RefuseExecution("no_symbol")
    if not si.volume_min or si.volume_min <= 0: raise RefuseExecution("no_volume_min")
    t = None
    for _ in range(10):  # 换账户/首启后行情可能未就绪 → 最多等 ~10s
        t = mt5.symbol_info_tick(SYMBOL)
        if t is not None and t.ask > 0 and t.bid > 0:
            break
        mt5.symbol_select(SYMBOL, True)
        time.sleep(1)
    if t is None or t.ask <= 0 or t.bid <= 0: raise RefuseExecution("no_tick")
    return ai, si, t


def _write(name, obj):
    P2.mkdir(parents=True, exist_ok=True)
    (P2 / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def run(execute=False):
    import MetaTrader5 as m
    mt5, ti = connect()
    ai, si, t = gate(mt5, ti)
    vol = si.volume_min
    pid = os.environ.get("TEST_TERM_PID")
    exp_id = "EXEC-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    req_wall = time.time(); req_mono = time.perf_counter()
    order_request = {
        "experiment_id": exp_id, "timestamp_utc": _utc(), "terminal_pid": pid,
        "data_directory": ti.data_path, "account_id_masked": mask(ai.login), "server": ai.server,
        "symbol": SYMBOL, "trade_mode": ai.trade_mode,
        "bid": t.bid, "ask": t.ask, "mid": round((t.bid + t.ask) / 2, 4),
        "spread_price": round(t.ask - t.bid, 4),
        "spread_bps": round((t.ask - t.bid) / ((t.bid + t.ask) / 2) * 1e4, 4),
        "volume": vol, "volume_min": si.volume_min, "volume_step": si.volume_step, "volume_max": si.volume_max,
        "direction": EXP_DIRECTION, "digits": si.digits, "contract_size": si.trade_contract_size,
        "request_timestamp_monotonic": req_mono, "request_timestamp_wallclock": req_wall,
    }
    _write("order_request.json", order_request)
    if not execute:
        print("PREFLIGHT_OK (未下单; 加 --execute 才执行)")
        print(json.dumps(order_request, ensure_ascii=False, indent=1)); mt5.shutdown()
        return {"preflight": True}

    ask_at_request = t.ask
    req = {"action": m.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": float(vol),
           "type": m.ORDER_TYPE_BUY, "price": ask_at_request, "deviation": 30, "magic": 90002,
           "comment": "v2-calib", "type_time": m.ORDER_TIME_GTC, "type_filling": m.ORDER_FILLING_FOK}
    s_mono = time.perf_counter(); s_wall = time.time()
    res = mt5.order_send(req)
    r_mono = time.perf_counter(); r_wall = time.time()
    fill = getattr(res, "price", None)
    order_response = {
        "send_timestamp_wallclock": s_wall, "send_timestamp_monotonic": s_mono,
        "broker_response_timestamp_wallclock": r_wall, "broker_response_timestamp_monotonic": r_mono,
        "response_latency_ms": round((r_mono - s_mono) * 1000, 3),
        "requested_price": ask_at_request, "actual_fill_price": fill,
        "order_id": getattr(res, "order", None), "deal_id": getattr(res, "deal", None),
        "broker_retcode": getattr(res, "retcode", None), "broker_comment": getattr(res, "comment", None),
        "volume_done": getattr(res, "volume", None),
        "rtt_note": "response_latency_ms = 单次 order_send 端到端(终端IPC+broker); API 无法再拆分本地IPC vs broker内部",
    }
    _write("order_response.json", order_response)

    pos = None; pos_ticket = None
    if res is not None and getattr(res, "retcode", 0) == m.TRADE_RETCODE_DONE:
        time.sleep(0.6)
        poss = mt5.positions_get(symbol=SYMBOL) or []
        if poss:
            p = poss[0]; pos_ticket = p.ticket
            pos = {"ticket": p.ticket, "price_open": p.price_open, "sl": p.sl, "tp": p.tp,
                   "volume": p.volume, "profit": p.profit}

    slippage = round(fill - ask_at_request, 5) if fill is not None else None
    slippage_bps = round((fill - ask_at_request) / ask_at_request * 1e4, 4) if fill is not None else None

    close_request = None; close_response = None; costs = None
    if pos_ticket:
        tick2 = mt5.symbol_info_tick(SYMBOL)
        cs_mono = time.perf_counter(); cs_wall = time.time()
        creq = {"action": m.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": float(pos["volume"]),
                "type": m.ORDER_TYPE_SELL, "position": pos_ticket, "price": tick2.bid, "deviation": 30,
                "magic": 90002, "comment": "v2-calib-close", "type_time": m.ORDER_TIME_GTC,
                "type_filling": m.ORDER_FILLING_FOK}
        cres = mt5.order_send(creq)
        cr_mono = time.perf_counter(); cr_wall = time.time()
        close_request = {"close_request_timestamp_monotonic": cs_mono, "close_request_timestamp_wallclock": cs_wall,
                         "close_bid": tick2.bid if tick2 else None, "close_ask": tick2.ask if tick2 else None,
                         "close_mid": round((tick2.bid + tick2.ask) / 2, 4) if tick2 else None,
                         "close_requested_price": tick2.bid if tick2 else None,
                         "exit_reference": "Bid (BUY 平仓)"}
        cfill = getattr(cres, "price", None)
        close_response = {"close_response_timestamp_wallclock": cr_wall, "close_response_timestamp_monotonic": cr_mono,
                          "close_latency_ms": round((cr_mono - cs_mono) * 1000, 3),
                          "close_order_id": getattr(cres, "order", None), "close_deal_id": getattr(cres, "deal", None),
                          "close_retcode": getattr(cres, "retcode", None), "close_comment": getattr(cres, "comment", None),
                          "close_actual_price": cfill}
        # 交易成本/盈亏
        comm = swap = profit = None
        try:
            dl = mt5.history_deals_get(position=pos_ticket) or []
            comm = sum((d.commission or 0) for d in dl)
            swap = sum((d.swap or 0) for d in dl)
            profit = sum((d.profit or 0) for d in dl)
        except Exception:  # noqa: BLE001
            pass
        cs = si.trade_contract_size
        gross = round((cfill - fill) * cs * pos["volume"], 4) if (cfill is not None and fill is not None) else None
        net = round((profit if profit is not None else gross), 4) if gross is not None else None
        costs = {"entry_spread_price": order_request["spread_price"],
                 "entry_spread_bps": order_request["spread_bps"],
                 "entry_slippage_price": slippage, "entry_slippage_bps": slippage_bps,
                 "exit_spread_price": round(tick2.ask - tick2.bid, 4) if tick2 else None,
                 "exit_slippage_price": round(tick2.bid - cfill, 5) if (tick2 and cfill is not None) else None,
                 "exit_slippage_note": "BUY 平仓: bid - actual (正=更差)",
                 "commission": comm if comm is not None else "NOT_AVAILABLE",
                 "swap": swap if swap is not None else "NOT_AVAILABLE",
                 "other_cost": 0,
                 "gross_pnl": gross, "net_pnl": net,
                 "net_pnl_source": "broker deals sum(profit) if available else gross"}
        _write("close_request.json", close_request)
        _write("close_response.json", close_response)

    summary = {"experiment_id": exp_id, "symbol": SYMBOL, "direction": EXP_DIRECTION,
               "orders_sent": 1, "open_positions_after_test": len(mt5.positions_get(symbol=SYMBOL) or []),
               "order": order_response, "position": pos, "slippage_price": slippage,
               "slippage_bps": slippage_bps, "slippage_sign_note": "BUY: fill - Ask_at_request (正=更差)",
               "close": close_response, "costs": costs, "date_utc": _utc()}
    _write("summary.json", summary)
    mt5.shutdown()
    print("EXECUTED: orders=1 | open_after=%d" % summary["open_positions_after_test"])
    print(json.dumps({k: summary[k] for k in ("order", "slippage_price", "slippage_bps", "close", "costs")},
                     ensure_ascii=False, indent=1))
    return summary


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    try:
        run(a.execute); return 0
    except RefuseExecution as e:
        print("REFUSE_EXECUTION:", e); return 3


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
