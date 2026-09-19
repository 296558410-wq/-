# -*- coding: utf-8 -*-
"""V2 回归 — P0-05 Cache AS-OF / PIT。

断言:
- get_asof 只返回 data_ts<=decision_ts 且 received_ts<=decision_ts
- 未来记录绝不返回
- stale / missing / duplicate / same-timestamp-different-source / source failure
日志: logs/test_pit_cache.log
"""
from __future__ import annotations
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "data_sources"))
import pit_cache as PC  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_pit_cache.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    tmp = Path(tempfile.mkdtemp()) / "pit.jsonl"
    F, S = "quote:gold_spot", "XAUUSD"
    PC.put_record(F, S, 100.0, data_ts=1000, received_ts=1001, source="sina", path=tmp)
    PC.put_record(F, S, 200.0, data_ts=2000, received_ts=2001, source="sina", path=tmp)
    PC.put_record(F, S, 9999.0, data_ts=9000, received_ts=9001, source="sina", path=tmp)  # future

    r = PC.get_asof(F, 2500, S, path=tmp)
    check("asof returns latest <= decision (2000)", r and r["value"] == 200.0, str(r and r["value"]))
    check("future record NOT returned", r and r["value"] != 9999.0)
    r2 = PC.get_asof(F, 9001, S, path=tmp)
    check("at exact future received_ts -> returns 9000", r2 and r2["value"] == 9999.0, str(r2 and r2["value"]))
    check("missing (before any data) -> None", PC.get_asof(F, 500, S, path=tmp) is None)
    check("unknown field -> None", PC.get_asof("quote:foo", 2500, S, path=tmp) is None)

    # received_ts 未到（数据时间早但接收晚）→ 在 decision 前不可见（防 look-ahead）
    tmp2 = Path(tempfile.mkdtemp()) / "pit2.jsonl"
    PC.put_record(F, S, 300.0, data_ts=1000, received_ts=8000, source="sina", path=tmp2)  # received late
    check("late-received not visible before received_ts", PC.get_asof(F, 3000, S, path=tmp2) is None)
    check("late-received visible after received_ts", (PC.get_asof(F, 9000, S, path=tmp2) or {}).get("value") == 300.0)

    # duplicate timestamp, different source → deterministic latest by received_ts
    tmp3 = Path(tempfile.mkdtemp()) / "pit3.jsonl"
    PC.put_record(F, S, 1.0, data_ts=1000, received_ts=1000, source="sina", path=tmp3)
    PC.put_record(F, S, 2.0, data_ts=1000, received_ts=1500, source="tencent", path=tmp3)
    r3 = PC.get_asof(F, 2000, S, path=tmp3)
    check("dup ts different source -> latest received", r3 and r3["value"] == 2.0 and r3["source"] == "tencent",
          str(r3 and (r3["value"], r3["source"])))

    # invalid data_ts rejected (source failure / malformed)
    try:
        PC.put_record(F, S, 1.0, data_ts=None, path=tmp3)
        check("invalid data_ts rejected", False)
    except ValueError:
        check("invalid data_ts rejected", True)

    check("source_hash present", isinstance(r3.get("source_hash"), str) and len(r3["source_hash"]) == 64)
    check("schema_version present", r3.get("schema_version") == "pit/1")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
