"""Entry/Exit interface (stage-1 skeleton). ORDER_SEND=FALSE enforced.

Can receive signal_time, decision_id, price_snapshot, model_output, agent_decision.
Does NOT place orders.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum


ORDER_SEND = False  # stage-1 hard invariant


class Signal(str, Enum):
    ENTRY_LONG = "ENTRY_LONG"
    ENTRY_SHORT = "ENTRY_SHORT"
    EXIT = "EXIT"
    WAIT = "WAIT"


@dataclass
class OrderIntent:
    signal: str
    signal_time_ns: int
    decision_id: str
    price_snapshot: dict
    model_output: dict | None = None
    agent_decision: str | None = None
    order_send: bool = False


def build_intent(signal: Signal, signal_time_ns: int, decision_id: str,
                 price_snapshot: dict, model_output=None, agent_decision=None) -> OrderIntent:
    return OrderIntent(
        signal=signal.value if isinstance(signal, Signal) else str(signal),
        signal_time_ns=int(signal_time_ns),
        decision_id=decision_id,
        price_snapshot=dict(price_snapshot),
        model_output=model_output,
        agent_decision=agent_decision,
        order_send=False,
    )


def send(intent: OrderIntent):
    raise RuntimeError("V3 stage-1: ORDER_SEND=FALSE (no execution path).")
