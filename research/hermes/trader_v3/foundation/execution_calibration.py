"""Execution calibration harness (SAFE BY DEFAULT).

Purpose: measure real MT5 DEMO entry/exit execution characteristics.
NOT a strategy. NOT auto trading.

Safety:
- Default DISABLED. Real order path requires explicit authorization
  (authorize(file flag) + fixed max_orders) and is never driven by
  Hermes/model/scheduler.
- Every order is tagged CALIBRATION_ORDER=true and MAGIC=90004.
- Count is fixed in advance; cannot grow dynamically.
- Mock mode measures the full timing/slippage pipeline without any broker.
"""
from __future__ import annotations
import json
import os
import time
from statistics import median


class CalibrationDisabled(RuntimeError):
    pass


def _pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    i = min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))
    return xs[i]


class ExecutionCalibrator:
    def __init__(self, out_dir: str, max_orders: int = 0, authorized: bool = False,
                 magic: int = 90004, terminal_id: str = "fxtm_demo_v3"):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.max_orders = int(max_orders)
        self.authorized = bool(authorized)
        self.magic = magic
        self.terminal_id = terminal_id
        self.orders_placed = 0
        self.entries = []
        self.exits = []

    # ---------- measurement ----------
    def record_entry(self, *, signal_ns, create_ns, send_ns, ack_ns, fill_ns,
                     requested_price, bid, ask, fill_price):
        spread = ask - bid
        slip = (fill_price - requested_price)
        rec = {
            "signal_time_ns": signal_ns,
            "request_create_time_ns": create_ns,
            "mt5_send_time_ns": send_ns,
            "broker_ack_time_ns": ack_ns,
            "fill_time_ns": fill_ns,
            "requested_price": requested_price,
            "bid_at_request": bid,
            "ask_at_request": ask,
            "fill_price": fill_price,
            "spread_at_request": spread,
            "slippage_price": slip,
            "slippage_bps": (slip / mid(bid, ask) * 1e4) if (bid + ask) else None,
            "latency_total_ns": fill_ns - signal_ns,
            "latency_breakdown": {
                "signal_to_send_ns": send_ns - signal_ns,
                "send_to_ack_ns": ack_ns - send_ns,
                "ack_to_fill_ns": fill_ns - ack_ns,
                "signal_to_fill_ns": fill_ns - signal_ns,
            },
        }
        self.entries.append(rec)
        self._append("entry_measurements.jsonl", rec)
        return rec

    def record_exit(self, *, exit_signal_ns, exit_request_ns, send_ns, ack_ns, fill_ns,
                    exit_requested_price, bid, ask, fill_price):
        slip = (exit_requested_price - fill_price)  # for a long exit you sell at bid; adverse = below requested
        rec = {
            "exit_signal_time_ns": exit_signal_ns,
            "exit_request_time_ns": exit_request_ns,
            "mt5_send_time_ns": send_ns,
            "broker_ack_time_ns": ack_ns,
            "exit_fill_time_ns": fill_ns,
            "exit_requested_price": exit_requested_price,
            "exit_bid": bid,
            "exit_ask": ask,
            "exit_fill_price": fill_price,
            "exit_slippage": slip,
            "exit_latency_ns": fill_ns - exit_signal_ns,
        }
        self.exits.append(rec)
        self._append("exit_measurements.jsonl", rec)
        return rec

    def _append(self, name, rec):
        with open(os.path.join(self.out_dir, name), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---------- profiles ----------
    def _stats(self, xs):
        xs = [x for x in xs if x is not None]
        if not xs:
            return {"n": 0}
        return {"n": len(xs), "mean": sum(xs) / len(xs), "median": median(xs),
                "p95": _pct(xs, 95), "p99": _pct(xs, 99), "max": max(xs)}

    def entry_profile(self) -> dict:
        return {
            "ENTRY_LATENCY_PROFILE": {
                "signal_to_fill_ns": self._stats([e["latency_breakdown"]["signal_to_fill_ns"] for e in self.entries]),
                "signal_to_send_ns": self._stats([e["latency_breakdown"]["signal_to_send_ns"] for e in self.entries]),
                "send_to_ack_ns": self._stats([e["latency_breakdown"]["send_to_ack_ns"] for e in self.entries]),
                "ack_to_fill_ns": self._stats([e["latency_breakdown"]["ack_to_fill_ns"] for e in self.entries]),
                "slippage_bps": self._stats([e["slippage_bps"] for e in self.entries]),
            },
            "n": len(self.entries),
        }

    def exit_profile(self) -> dict:
        return {
            "EXIT_LATENCY_PROFILE": {
                "exit_latency_ns": self._stats([e["exit_latency_ns"] for e in self.exits]),
                "exit_slippage": self._stats([e["exit_slippage"] for e in self.exits]),
            },
            "n": len(self.exits),
        }

    # ---------- real order gate (DISABLED by default) ----------
    def place_calibration_order(self, send_fn=None, **order):
        if not self.authorized:
            raise CalibrationDisabled(
                "CalibrationDisabled: real demo orders require explicit authorization "
                "(authorized=True). Default V3_ORDER_SEND=FALSE.")
        if self.orders_placed >= self.max_orders:
            raise CalibrationDisabled(
                f"CalibrationDisabled: fixed cap reached ({self.orders_placed}/{self.max_orders}); "
                "count may not grow dynamically.")
        if send_fn is None:
            raise CalibrationDisabled("CalibrationDisabled: no send_fn supplied (no broker path).")
        order = dict(order)
        order["CALIBRATION_ORDER"] = True
        order["MAGIC"] = self.magic
        self.orders_placed += 1
        self._append("calibration_orders.jsonl", order)
        return send_fn(order)


def mid(bid, ask):
    return (bid + ask) / 2.0


def mock_tick(bid, ask, t_ns=None):
    t_ns = t_ns or time.perf_counter_ns()
    return {"bid": bid, "ask": ask, "t_ns": t_ns}
