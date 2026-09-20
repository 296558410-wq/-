"""Unified V3 tick schema (L1 quotes).

Fields are described in trader_v3/schemas/v3_tick_schema.json.
Never fabricate fields the broker does not provide.
"""
from __future__ import annotations
from typing import Any

REQUIRED = [
    "timestamp_utc",
    "timestamp_ns",
    "mt5_server_time",
    "local_receive_time_ns",
    "symbol",
    "bid",
    "ask",
    "mid",
    "spread",
    "tick_sequence",
    "source",
    "terminal_id",
    "account_id",
]
OPTIONAL = ["last", "volume", "volume_real", "flags"]

# Fields that are "OBSERVED" (present in raw source) vs "DERIVED"
DERIVED = {"mid", "spread"}


class TickValidationError(ValueError):
    pass


def make_tick(
    *,
    timestamp_ns: int,
    mt5_server_time: Any,
    local_receive_time_ns: int,
    symbol: str,
    bid: float,
    ask: float,
    tick_sequence: int,
    source: str,
    terminal_id: str,
    account_id: str,
    timestamp_utc: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Build a normalized tick with derived mid/spread. No fabricated data."""
    from .timeutil import ns_to_iso

    t = {
        "timestamp_utc": timestamp_utc or ns_to_iso(timestamp_ns),
        "timestamp_ns": int(timestamp_ns),
        "mt5_server_time": mt5_server_time,
        "local_receive_time_ns": int(local_receive_time_ns),
        "symbol": symbol,
        "bid": float(bid),
        "ask": float(ask),
        "mid": (float(bid) + float(ask)) / 2.0,
        "spread": float(ask) - float(bid),
        "tick_sequence": int(tick_sequence),
        "source": source,
        "terminal_id": terminal_id,
        "account_id": account_id,
    }
    if extra:
        for k in OPTIONAL:
            if k in extra and extra[k] is not None:
                t[k] = extra[k]
    return t


def validate_tick(t: dict) -> None:
    missing = [k for k in REQUIRED if k not in t]
    if missing:
        raise TickValidationError(f"missing required fields: {missing}")
    if t["ask"] < t["bid"]:
        raise TickValidationError(f"crossed quote: ask {t['ask']} < bid {t['bid']}")
    if not (t["bid"] > 0 and t["ask"] > 0):
        raise TickValidationError("non-positive price")
    # mid/spread must be consistent (derived, not fabricated)
    if abs(t["spread"] - (t["ask"] - t["bid"])) > 1e-9:
        raise TickValidationError("spread inconsistent with ask-bid")
