"""V3 Tick Recorder — append-only, hourly-sharded, crash-safe, resumable.

Guarantees:
- append-only; never overwrites old shards
- shard per date/hour: <root>/YYYY-MM-DD/HH.jsonl
- fsync on write group (crash-safe)
- on shard rollover: compute sha256, append to manifest.jsonl (registry)
- resume: reopen existing shard and continue
"""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone


class TickRecorder:
    def __init__(self, root: str, fsync_every: int = 1):
        self.root = root
        self.fsync_every = max(1, fsync_every)
        os.makedirs(root, exist_ok=True)
        self.manifest = os.path.join(root, "manifest.jsonl")
        self._fh = None
        self._path = None
        self._count = 0
        self._since_fsync = 0

    def _shard_path(self, ts_ns: int) -> str:
        dt = datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc)
        d = os.path.join(self.root, dt.strftime("%Y-%m-%d"))
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, dt.strftime("%H.jsonl"))

    def _open(self, ts_ns: int, hash_existing: bool = True):
        p = self._shard_path(ts_ns)
        if self._path == p and self._fh:
            return
        self._close(hash_existing)
        # resume: append to existing shard, never overwrite
        self._fh = open(p, "a", encoding="utf-8")
        self._path = p
        self._count = sum(1 for _ in open(p, "r", encoding="utf-8")) if os.path.exists(p) else 0

    def _close(self, hash_it: bool):
        if self._fh:
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self._fh.close()
            if hash_it and self._path:
                self._emit_manifest(self._path)
        self._fh = None
        self._path = None

    def _sha256_file(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    def _emit_manifest(self, path: str):
        rec = {
            "file": os.path.relpath(path, self.root).replace("\\", "/"),
            "sha256": self._sha256_file(path),
            "closed_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.manifest, "a", encoding="utf-8") as m:
            m.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def write(self, tick: dict):
        self._open(tick["timestamp_ns"])
        self._fh.write(json.dumps(tick, ensure_ascii=False) + "\n")
        self._count += 1
        self._since_fsync += 1
        if self._since_fsync >= self.fsync_every:
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self._since_fsync = 0

    def close(self):
        self._close(hash_it=True)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def health(self) -> dict:
        return {"current_shard": self._path, "lines_in_shard": self._count}
