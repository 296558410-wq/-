"""Tick stream + integrity monitor.

Detects: duplicate, out_of_order, timestamp_regression, sequence_gap,
abnormal_spread, abnormal_price, stale_tick.
"""
from __future__ import annotations
from collections import deque
from statistics import median


class IntegrityMonitor:
    def __init__(self, max_spread_mult: float = 10.0, stale_ms: int = 30_000, ewma_alpha: float = 0.01):
        self.n = 0
        self.duplicate = 0
        self.out_of_order = 0
        self.ts_regression = 0
        self.seq_gap = 0
        self.abnormal_spread = 0
        self.abnormal_price = 0
        self.stale = 0
        self._last = None
        self._last_seq = None
        self._spread_window = deque(maxlen=1000)
        self._spread_ewma = None
        self.ewma_alpha = ewma_alpha
        self.max_spread_mult = max_spread_mult
        self.stale_ms = stale_ms
        self.intervals = []

    def feed(self, t: dict) -> dict:
        flags = []
        self.n += 1
        ts = t["timestamp_ns"]
        seq = t.get("tick_sequence")
        bid, ask, spread = t["bid"], t["ask"], t["spread"]

        if bid <= 0 or ask <= 0:
            self.abnormal_price += 1
            flags.append("abnormal_price")

        self._spread_ewma = spread if self._spread_ewma is None else \
            self._spread_ewma + (spread - self._spread_ewma) * self.ewma_alpha
        if self._spread_ewma > 0 and spread > self._spread_ewma * self.max_spread_mult:
            self.abnormal_spread += 1
            flags.append("abnormal_spread")
        self._spread_window.append(spread)

        if self._last is not None:
            lts = self._last["timestamp_ns"]
            dt = ts - lts
            if dt == 0:
                self.duplicate += 1
                flags.append("duplicate")
            if dt < 0:
                self.out_of_order += 1
                self.ts_regression += 1
                flags.append("out_of_order")
                flags.append("timestamp_regression")
            if dt > self.stale_ms * 1_000_000:
                self.stale += 1
                flags.append("stale_tick")
            if dt > 0:
                self.intervals.append(dt)
            if seq is not None and self._last_seq is not None and seq != self._last_seq + 1:
                self.seq_gap += 1
                flags.append("sequence_gap")

        self._last = t
        if seq is not None:
            self._last_seq = seq
        return {"flags": flags}

    # ---- stats ----
    def interval_stats_ms(self) -> dict:
        if not self.intervals:
            return {"median": None, "p95": None, "p99": None, "max": None}
        xs = sorted(self.intervals)
        def pct(p):
            i = min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))
            return xs[i] / 1e6
        return {"median": median(xs) / 1e6, "p95": pct(95), "p99": pct(99), "max": xs[-1] / 1e6}

    def rates(self) -> dict:
        n = max(self.n, 1)
        return {
            "TICK_DUPLICATE_RATE": self.duplicate / n,
            "TICK_OUT_OF_ORDER_RATE": self.out_of_order / n,
            "TICK_SEQUENCE_GAP_COUNT": self.seq_gap,
            "STALE_TICK_COUNT": self.stale,
            "ABNORMAL_SPREAD_COUNT": self.abnormal_spread,
            "ABNORMAL_PRICE_COUNT": self.abnormal_price,
            "TIMESTAMP_REGRESSION_COUNT": self.ts_regression,
            "TICKS": self.n,
        }

    def verdict(self) -> str:
        # Do NOT pass merely because dup=0 and ooo=0
        hard = self.abnormal_price + self.ts_regression + self.seq_gap
        return "FAIL" if hard > 0 else ("REVIEW" if (self.abnormal_spread or self.stale or self.duplicate or self.out_of_order) else "PASS")
