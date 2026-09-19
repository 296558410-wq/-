# -*- coding: utf-8 -*-
"""V2 Data Source Router — freshness-aware 缓存（区分 FRESH/STALE_BUT_VALID/MISSING/INVALID/SOURCE_DOWN）。

- 低频宏观："没有新数据" ≠ "没有数据"：陈旧但曾在有效期内的值 → STALE_BUT_VALID（仍可用，带 observed_at/age）。
- PIT 铁律：缓存只保存“取回时刻已知”的值；**永不**用更晚的取回覆盖更早的历史快照；不写入未来时间戳。
"""
from __future__ import annotations
import json, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # .../trader_v2
CACHE = ROOT / "data_cache" / "router_cache.json"

FRESH = "FRESH"
STALE = "STALE_BUT_VALID"
MISSING = "MISSING"
INVALID = "INVALID"
SOURCE_DOWN = "SOURCE_DOWN"
STATES = (FRESH, STALE, MISSING, INVALID, SOURCE_DOWN)


def _load() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


_store: dict = _load()


def _save():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(_store, ensure_ascii=False), encoding="utf-8")


def classify(age_hours, fresh_h: float, stale_h: float) -> str:
    if age_hours is None:
        return MISSING
    if age_hours <= fresh_h:
        return FRESH
    if age_hours <= stale_h:
        return STALE
    return MISSING


def _age_hours(rec: dict):
    for k in ("observed_ts", "fetched_ts"):
        ts = rec.get(k)
        if ts:
            return (time.time() - ts) / 3600.0
    return None


def put(key: str, value, source: str, *, observed_at=None, observed_ts=None,
        fresh_h=1.0, stale_h=168.0, state_override=None):
    """写缓存。state_override 用于 INVALID/SOURCE_DOWN 标记（value 可为 None，保留 last_valid）。"""
    now = time.time()
    prev = _store.get(key) or {}
    rec = {
        "value": value if state_override != INVALID else prev.get("value"),
        "last_valid": prev.get("last_valid"),
        "source": source,
        "observed_at": observed_at or prev.get("observed_at"),
        "observed_ts": observed_ts or prev.get("observed_ts"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "fetched_ts": now,
        "fresh_h": fresh_h, "stale_h": stale_h,
        "state_override": state_override,
    }
    if value is not None and state_override is None:
        rec["last_valid"] = value
    _store[key] = rec
    _save()
    return get(key)


def get(key: str):
    rec = _store.get(key)
    if not rec:
        return None
    out = dict(rec)
    age_h = _age_hours(rec)
    out["age_hours"] = round(age_h, 3) if age_h is not None else None
    if rec.get("state_override"):
        out["freshness"] = rec["state_override"]
    else:
        out["freshness"] = classify(age_h, rec.get("fresh_h", 1.0), rec.get("stale_h", 168.0))
    out["usable"] = out["freshness"] in (FRESH, STALE)
    return out


def all_keys() -> list:
    return sorted(_store.keys())
