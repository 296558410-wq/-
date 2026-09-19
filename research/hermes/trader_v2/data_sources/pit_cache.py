# -*- coding: utf-8 -*-
"""V2 PIT AS-OF 缓存（P0-05）—— immutable 历史记录 + get_asof。

与旧 `cache.py`（单槽 last-write-wins）并存。本模块提供**不可变、可 as-of 查询**的存储：
每条记录 append-only 写入 `data_cache/pit_store.jsonl`，含 data_ts / received_ts / source / source_hash / schema_version。

铁律:
- 只追加，不覆盖（immutable）。
- `get_asof(field, decision_ts)` 只返回 `data_ts <= decision_ts` **且** `received_ts <= decision_ts` 的最新合法记录。
- 绝不返回未来记录（data_ts 或 received_ts > decision_ts）。
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data_cache" / "pit_store.jsonl"
SCHEMA_VERSION = "pit/1"


def _to_epoch(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        v = float(x)
        return v / 1000.0 if v > 1e12 else v
    try:
        return datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception:  # noqa: BLE001
        return None


def _now_epoch():
    return datetime.now(timezone.utc).timestamp()


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def put_record(field, symbol, value, data_ts, *, received_ts=None, source=None, path=None) -> dict:
    """追加一条不可变记录。data_ts 必填且必须可解析。返回写入的记录。"""
    dts = _to_epoch(data_ts)
    if dts is None:
        raise ValueError("pit_cache: invalid data_ts")
    rts = _to_epoch(received_ts) if received_ts is not None else _now_epoch()
    rec = {"schema_version": SCHEMA_VERSION, "field": field, "symbol": symbol, "value": value,
           "data_ts": dts, "received_ts": rts, "source": source}
    rec["source_hash"] = _sha({"field": field, "symbol": symbol, "value": value, "data_ts": dts, "source": source})
    p = Path(path or STORE)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def _read(path=None):
    p = Path(path or STORE)
    if not p.exists():
        return []
    out = []
    for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines()):
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
            r["_i"] = i
            out.append(r)
        except Exception:  # noqa: BLE001
            continue
    return out


def get_asof(field, decision_ts, symbol=None, path=None):
    """返回 data_ts<=decision_ts 且 received_ts<=decision_ts 的最新记录；无 → None。"""
    d = _to_epoch(decision_ts)
    if d is None:
        return None
    cands = [r for r in _read(path)
             if r.get("field") == field
             and (symbol is None or r.get("symbol") == symbol)
             and r.get("data_ts") is not None and r["data_ts"] <= d
             and r.get("received_ts") is not None and r["received_ts"] <= d]
    if not cands:
        return None
    cands.sort(key=lambda r: (r["data_ts"], r["received_ts"], r["_i"]))
    best = dict(cands[-1])
    best.pop("_i", None)
    best["_age_seconds"] = round(d - best["data_ts"], 3)
    return best


if __name__ == "__main__":
    import sys, tempfile
    sys.stdout.reconfigure(encoding="utf-8")
    tmp = Path(tempfile.mkdtemp()) / "pit.jsonl"
    put_record("quote:gold_spot", "XAUUSD", 4271.8, data_ts=1000, received_ts=1001, source="sina", path=tmp)
    put_record("quote:gold_spot", "XAUUSD", 9999.0, data_ts=5000, received_ts=5001, source="sina", path=tmp)
    print("asof(2000) ->", get_asof("quote:gold_spot", 2000, "XAUUSD", path=tmp))  # must be 1000-record
    print("asof(6000) ->", get_asof("quote:gold_spot", 6000, "XAUUSD", path=tmp))
