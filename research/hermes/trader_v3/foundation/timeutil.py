"""High-precision clocks for V3.

- wall clock UTC (ns since epoch) for cross-source alignment
- monotonic performance counter (ns) for local receive timing / intervals
"""
from __future__ import annotations
import time
from datetime import datetime, timezone


def utc_ns() -> int:
    """Wall-clock UTC as nanoseconds since Unix epoch."""
    return time.time_ns()


def mono_ns() -> int:
    """Monotonic high-resolution counter in nanoseconds (never goes backwards).

    Falls back to time.monotonic_ns if perf_counter_ns is unavailable.
    """
    try:
        return time.perf_counter_ns()
    except AttributeError:  # pragma: no cover
        return time.monotonic_ns()


def ns_to_iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).isoformat()


def iso_to_ns(iso: str) -> int:
    s = iso.replace("Z", "+00:00")
    return int(datetime.fromisoformat(s).timestamp() * 1e9)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
