# -*- coding: utf-8 -*-
"""V2 宏观发布/修订登记（Phase-1.5）。

问题: 宏观数据(BLS CPI 等)会修订; Hermes 在 T 决策时只能看到 T 之前已公开的版本。
机制(观察式, 诚实):
- 每次采集宏观值时登记一条 observation; 同一 (release_id, period) 值变化 → revision 链(version 递增)。
- release_timestamp 若官方源未提供 → 明确 release_timestamp_source="unavailable", 不伪造精确时间。
- value_asof(...) 提供 "只能看到 as_of 之前已观察到版本" 的访问器(PIT)。
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "state" / "macro_releases.jsonl"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load():
    if not REG.exists():
        return []
    return [json.loads(l) for l in REG.read_text(encoding="utf-8").splitlines() if l.strip()]


def _append(rec):
    REG.parent.mkdir(parents=True, exist_ok=True)
    with open(REG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def observe(release_id, release_period, value, source, source_url,
            release_timestamp=None, release_timestamp_source=None, observed_at=None):
    """登记一次观测; 返回本次 observation 记录(含 revision 语义)。"""
    observed_at = observed_at or _now()
    prior = [r for r in _load()
             if r["release_id"] == release_id and str(r["release_period"]) == str(release_period)]
    first_val = prior[0]["value"] if prior else value
    latest = prior[-1] if prior else None
    if latest is None:
        rev_num = 0
        changed = False
    elif latest["value"] != value:
        rev_num = int(latest.get("revision_number", 0)) + 1
        changed = True
    else:
        rev_num = int(latest.get("revision_number", 0))
        changed = False
    rec = {
        "release_id": release_id, "release_period": str(release_period),
        "value": value, "first_published_value": first_val, "latest_known_value": value,
        "revision_number": rev_num, "revision_timestamp": observed_at if changed else None,
        "revision_changed": changed,
        "release_timestamp": release_timestamp,
        "release_timestamp_source": release_timestamp_source or ("unavailable" if release_timestamp is None else "source"),
        "release_timestamp_unknown": release_timestamp is None,
        "source": source, "source_url": source_url, "observed_at": observed_at,
        "point_in_time_confidence": "low" if release_timestamp is None else "medium",
    }
    _append(rec)
    return rec


def value_asof(release_id, release_period, as_of):
    """PIT 访问器: 返回 as_of 时刻已可公开的版本(observed_at <= as_of 的最后一条)。"""
    rows = [r for r in _load() if r["release_id"] == release_id
            and str(r["release_period"]) == str(release_period)]
    rows = [r for r in rows if r["observed_at"] <= as_of]
    if not rows:
        return None
    return rows[-1]


def chain(release_id, release_period):
    return [r for r in _load() if r["release_id"] == release_id
            and str(r["release_period"]) == str(release_period)]


def summary():
    rows = _load()
    ids = {r["release_id"] for r in rows}
    revs = [r for r in rows if r.get("revision_changed")]
    return {"n_observations": len(rows), "n_releases": len(ids), "n_revisions": len(revs),
            "releases": sorted(ids)}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary(), ensure_ascii=False, indent=1))
