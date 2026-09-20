"""Data registry: OBSERVED / MISSING / UNKNOWN. Never silent-fill gaps."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone


class DataRegistry:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.entries = []

    def add(self, *, name, source, symbol, period, tick_count,
            coverage=None, missing_periods=None, timestamp_resolution=None,
            duplicate_rate=None, out_of_order_rate=None, sha256=None,
            status="OBSERVED", notes=None):
        assert status in ("OBSERVED", "MISSING", "UNKNOWN")
        self.entries.append({
            "name": name, "source": source, "symbol": symbol, "period": period,
            "tick_count": tick_count, "coverage": coverage,
            "missing_periods": missing_periods or [],
            "timestamp_resolution": timestamp_resolution,
            "duplicate_rate": duplicate_rate, "out_of_order_rate": out_of_order_rate,
            "sha256": sha256, "status": status, "notes": notes,
        })

    def save(self):
        doc = {
            "schema": "v3_data_registry/2",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entries": self.entries,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        return doc


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()
