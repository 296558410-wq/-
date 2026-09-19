# -*- coding: utf-8 -*-
"""C-31 deterministic canonicalization (spec: research/V3_CANONICALIZATION_SPEC.md).

仅做**元数据/序列化**规范化，不改任何研究语义字段（A/B/C/D 一律保留原值）。
用法:
  python v3_canonicalize.py json <in.json> <out.json>
  python v3_canonicalize.py csv  <in.csv>  <out.csv>
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

VOLATILE_KEYS = {"mtime", "generated_utc", "generated_at", "ts", "timestamp", "runtime_ms", "duration_ms",
                 "elapsed_ms", "elapsed", "host", "hostname", "machine", "cwd", "wall_clock", "run_ts"}
ROOM_PREFIX = "C:/Users/surface/HermesWorkspaces/v3"


def _norm_paths(s):
    return s.replace(ROOM_PREFIX, "<ROOM>").replace(ROOM_PREFIX.replace("/", "\\"), "<ROOM>")


def _prune(o):
    if isinstance(o, dict):
        return {k: _prune(v) for k, v in o.items() if k not in VOLATILE_KEYS}
    if isinstance(o, list):
        return [_prune(x) for x in o]
    if isinstance(o, float):
        return 0.0 if o == 0 else o  # 消除 -0.0
    if isinstance(o, str):
        return _norm_paths(o)
    return o


def canon_json(text):
    obj = json.loads(text)
    obj = _prune(obj)
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"


def canon_csv(text):
    body = text.replace("\r\n", "\n").replace("\r", "\n")
    body = _norm_paths(body)
    return body if body.endswith("\n") else body + "\n"


def main():
    kind, src, dst = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    t = src.read_text(encoding="utf-8")
    out = canon_json(t) if kind == "json" else canon_csv(t)
    dst.write_text(out, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
