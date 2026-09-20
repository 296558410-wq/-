"""V3 cost model from MEASURED inputs.

Never uses assumed values as if measured: unmeasured components are marked
DATA_GAP and excluded from minimum_required_move (which then returns DATA_GAP).
"""
from __future__ import annotations
from statistics import median


def _stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return {"n": 0, "median": None, "p95": None, "p99": None}
    xs = sorted(xs)

    def pct(p):
        i = min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))
        return xs[i]
    return {"n": len(xs), "median": median(xs), "p95": pct(95), "p99": pct(99)}


class CostModel:
    def __init__(self):
        self.spread_bp = []        # MEASURED from ticks
        self.slippage_bp = []      # MEASURED from execution calibration (else MODEL)
        self.commission_bp = None  # MEASURED only if broker statement given
        self._commission_source = "DATA_GAP"

    def add_spread(self, bid, ask):
        m = (bid + ask) / 2.0
        if m > 0:
            self.spread_bp.append((ask - bid) / m * 1e4)

    def set_commission_bp(self, bp: float, source: str = "MEASURED"):
        self.commission_bp = bp
        self._commission_source = source

    def add_slippage_bp(self, bp: float):
        self.slippage_bp.append(bp)

    # round-trip spread cost = one full spread (in+out) in bp
    def round_trip_cost_bp(self):
        if not self.spread_bp:
            return {"status": "DATA_GAP", "value": None}
        comp = {"spread": _stats(self.spread_bp)["median"]}
        status = "MEASURED_SPREAD"
        if self.slippage_bp:
            comp["slippage"] = _stats(self.slippage_bp)["median"]
        total = comp["spread"] + 2 * comp.get("slippage", 0.0)
        if self.commission_bp is not None:
            total += 2 * self.commission_bp
            comp["commission_x2"] = 2 * self.commission_bp
        else:
            status = "PARTIAL(spread measured; commission DATA_GAP)"
        return {"status": status, "value": total, "components": comp}

    def summary(self) -> dict:
        return {
            "spread_bp": _stats(self.spread_bp),
            "slippage_bp": _stats(self.slippage_bp) if self.slippage_bp else {"n": 0, "source": "DATA_GAP/MODEL"},
            "commission_bp": {"value": self.commission_bp, "source": self._commission_source},
            "round_trip_cost_bp": self.round_trip_cost_bp(),
        }

    def minimum_required_move(self, win_rate: float) -> dict:
        """Symmetric scalp break-even target t* = cost / (2p-1) in bp."""
        rt = self.round_trip_cost_bp()
        if rt["value"] is None:
            return {"status": "DATA_GAP", "value_bp": None}
        d = 2 * win_rate - 1
        if d <= 0:
            return {"status": "NO_SOLUTION", "value_bp": None, "note": "expected = -cost"}
        measured = rt["status"].startswith("MEASURED") and self.commission_bp is not None
        return {
            "status": "MEASURED" if measured else "PARTIAL(commission/slippage not fully measured)",
            "value_bp": rt["value"] / d,
            "win_rate": win_rate,
        }

    def expected_net_edge(self, expected_gross_move_bp: float, win_rate: float | None = None) -> dict:
        rt = self.round_trip_cost_bp()
        if rt["value"] is None:
            return {"status": "DATA_GAP", "expected_net_edge_bp": None}
        return {
            "status": "OK",
            "expected_net_edge_bp": expected_gross_move_bp - rt["value"],
            "alpha_threshold": "NOT_DEFINED_AT_FOUNDATION_STAGE",
        }
