"""V3 HFT event ledger: append-only, hash-chained.

event_hash = sha256(canonical(event w/o event_hash) + prev_hash)
Supports chain verification and offline replay.
"""
from __future__ import annotations
import hashlib
import json
import os


GENESIS = "0" * 64


def _canon(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Ledger:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.seq = 0
        self.prev = GENESIS
        if os.path.exists(path):
            for ln in open(path, "r", encoding="utf-8"):
                ln = ln.strip()
                if ln:
                    e = json.loads(ln)
                    self.seq = e["event_id"]
                    self.prev = e["event_hash"]

    def append(self, event_type: str, ts_ns: int, **fields) -> dict:
        self.seq += 1
        ev = {"event_id": self.seq, "timestamp_ns": int(ts_ns), "event_type": event_type}
        # deterministic field order
        for k in ["run_id", "decision_id", "model_version", "feature_hash", "price", "bid",
                  "ask", "spread", "order_id", "position_id", "fill_price", "slippage",
                  "latency_ns", "pnl"]:
            if k in fields:
                ev[k] = fields[k]
        ev["prev_hash"] = self.prev
        ev["event_hash"] = hashlib.sha256((_canon(ev) + self.prev).encode()).hexdigest()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(_canon(ev) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.prev = ev["event_hash"]
        return ev

    @staticmethod
    def verify(path: str) -> dict:
        prev = GENESIS
        n = 0
        for ln in open(path, "r", encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            e = json.loads(ln)
            h = e.pop("event_hash")
            if e["prev_hash"] != prev:
                return {"ok": False, "at": e["event_id"], "reason": "prev_hash mismatch"}
            if hashlib.sha256((_canon(e) + prev).encode()).hexdigest() != h:
                return {"ok": False, "at": e["event_id"], "reason": "event_hash mismatch"}
            prev = e["prev_hash"] = h  # restore for next
            prev = h
            n += 1
        return {"ok": True, "events": n, "head": prev}

    @staticmethod
    def replay(path: str) -> list:
        return [json.loads(ln) for ln in open(path, "r", encoding="utf-8") if ln.strip()]
