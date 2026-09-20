"""Prediction contract: Model -> Agent/Hermes. Stage-1 skeleton.

AUTO_DECISION=FALSE: this layer produces predictions only; it does not trade.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum


class Decision(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"
    EXIT = "EXIT"


AUTO_DECISION = False


@dataclass
class PredictionContract:
    prob_up: float
    prob_down: float
    expected_return: float
    expected_net_edge: float
    prediction_horizon_ms: int
    model_version: str

    def validate(self):
        s = self.prob_up + self.prob_down
        if not (0.99 <= s <= 1.01):
            raise ValueError(f"prob_up+prob_down must ~1 (got {s})")
        return True

    def to_dict(self) -> dict:
        return asdict(self)


def decision_from_prediction(pred: PredictionContract, threshold: float | None = None) -> Decision:
    """Skeleton only. No auto trading. Returns WAIT unless a (future) alpha
    threshold is explicitly supplied by the Alpha stage."""
    if threshold is None:
        return Decision.WAIT
    if pred.expected_net_edge > threshold and pred.prob_up >= pred.prob_down:
        return Decision.LONG
    if pred.expected_net_edge > threshold and pred.prob_down > pred.prob_up:
        return Decision.SHORT
    return Decision.WAIT
