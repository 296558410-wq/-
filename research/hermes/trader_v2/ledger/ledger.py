# -*- coding: utf-8 -*-
"""V2 Module 3 — 统一不可变事件账本（append-only + sha256 hash chain）。

- 事件覆盖: DECISION / EXECUTION_REQUEST / EXECUTION_RESPONSE / ORDER_ACCEPTED / ORDER_REJECTED /
  FILL / POSITION_OPEN / POSITION_CLOSE_REQUEST / POSITION_CLOSED / COST / PNL / ACCOUNT_SNAPSHOT /
  ACCOUNT_INIT / SYSTEM_EVENT。WAIT / REJECT 也作为 DECISION 事件保留。
- 不可变: 只追加; event[n].previous_event_hash == event[n-1].event_hash; 首条 previous=GENESIS。
- verify_ledger(): 可发现 删除/修改/插入/乱序/hash 不一致。
- 与环境隔离: 每条事件带 environment / execution_mode。
"""
from __future__ import annotations
import hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "hermes_v2_ledger.jsonl"
GENESIS = "GENESIS"
EVENT_VERSION = 1

EVENT_TYPES = [
    "ACCOUNT_INIT", "DECISION", "EXECUTION_REQUEST", "EXECUTION_RESPONSE",
    "ORDER_ACCEPTED", "ORDER_REJECTED", "FILL", "POSITION_OPEN",
    "POSITION_CLOSE_REQUEST", "POSITION_CLOSED", "COST", "PNL",
    "ACCOUNT_SNAPSHOT", "SYSTEM_EVENT",
]

# §五 语义字段(缺失可为 null, 但不可丢语义)
SCHEMA_FIELDS = [
    "event_id", "event_type", "event_version", "seq",
    "timestamp_utc", "source_timestamp_utc",
    "environment", "execution_mode",
    "strategy_id", "strategy_version", "decision_id", "parent_event_id",
    "symbol", "side", "order_type", "volume",
    "requested_price", "reference_bid", "reference_ask", "reference_mid",
    "fill_price", "fill_volume", "spread", "slippage",
    "request_timestamp", "response_timestamp", "fill_timestamp", "latency_ms",
    "order_id", "deal_id", "position_id",
    "commission", "swap", "gross_pnl", "net_pnl",
    "account_balance", "account_equity", "free_margin",
    "broker", "broker_server", "status", "retcode", "message",
    "context_hash", "input_hash",
    "previous_event_hash", "event_hash",
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _canon(obj) -> bytes:
    return json.dumps({k: v for k, v in obj.items() if k != "event_hash"},
                      sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class LedgerMalformed(Exception):
    """账本存在不可解析行（截断/部分写入/损坏）。fail-closed：不得静默跳过。"""


def load_events(path=None):
    p = Path(path or LEDGER)
    if not p.exists():
        return []
    out = []
    for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines()):
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError as e:  # FIX(2026-09-15): 截断/部分写入行不再让进程崩溃
                raise LedgerMalformed(f"line {i + 1}: {e}") from e
    return out


def head(path=None):
    evs = load_events(path)
    return evs[-1] if evs else None


def new_event(event_type, **fields):
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unknown event_type: {event_type}")
    ev = {k: None for k in SCHEMA_FIELDS}
    ev["event_type"] = event_type
    ev["event_version"] = EVENT_VERSION
    ev["timestamp_utc"] = _now()
    for k, v in fields.items():
        if k in ("event_id", "event_hash", "previous_event_hash", "seq"):
            raise ValueError(f"reserved field: {k}")
        ev[k] = v
    return ev


def append_event(event, path=None):
    """追加事件; 计算 previous_event_hash / event_hash。返回写入的完整事件。"""
    p = Path(path or LEDGER)
    p.parent.mkdir(parents=True, exist_ok=True)
    evs = load_events(p)
    prev = evs[-1]["event_hash"] if evs else GENESIS
    ev = dict(event)
    ev["previous_event_hash"] = prev
    ev["seq"] = len(evs) + 1
    if not ev.get("event_id"):
        ev["event_id"] = f"evt-{ev['seq']:06d}-{ev['event_type']}"
    ev.pop("event_hash", None)
    ev["event_hash"] = _sha(_canon(ev) + prev.encode("utf-8"))
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        f.flush()
        try:
            os.fsync(f.fileno())   # FIX(2026-09-15): 降低半行/截断写入概率
        except Exception:  # noqa: BLE001
            pass
    return ev


def verify_ledger(path=None):
    """校验 hash 链完整性。返回 (ok, detail)。损坏/截断 → fail-closed，不抛异常。"""
    try:
        evs = load_events(path)
    except LedgerMalformed as e:
        return False, {"reason": "malformed_line(torn/partial write)", "detail": str(e)}
    if not evs:
        return True, {"n": 0, "note": "empty ledger"}
    prev = GENESIS
    for i, e in enumerate(evs):
        if i == 0 and e.get("previous_event_hash") != GENESIS:
            return False, {"at": i, "reason": "genesis_mismatch", "got": e.get("previous_event_hash")}
        if i > 0 and e.get("previous_event_hash") != prev:
            return False, {"at": i, "reason": "chain_break(delete/insert/reorder)", "expected": prev,
                           "got": e.get("previous_event_hash")}
        want = _sha(_canon(e) + str(e.get("previous_event_hash")).encode("utf-8"))
        if e.get("event_hash") != want:
            return False, {"at": i, "reason": "hash_mismatch(tamper)", "want": want, "got": e.get("event_hash")}
        if e.get("seq") != i + 1:
            return False, {"at": i, "reason": "seq_mismatch", "want": i + 1, "got": e.get("seq")}
        prev = e["event_hash"]
    return True, {"n": len(evs), "head": evs[-1]["event_hash"]}


def query(path=None, execution_mode=None, environment=None, event_type=None):
    evs = load_events(path)
    if execution_mode:
        evs = [e for e in evs if e.get("execution_mode") == execution_mode]
    if environment:
        evs = [e for e in evs if e.get("environment") == environment]
    if event_type:
        evs = [e for e in evs if e.get("event_type") == event_type]
    return evs


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("ledger:", LEDGER)
    print("verify:", verify_ledger())
