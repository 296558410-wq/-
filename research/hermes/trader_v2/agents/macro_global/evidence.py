# -*- coding: utf-8 -*-
"""V2 Evidence 层 —— 不可变证据存储 + 统一 Evidence Registry（Phase-1.5）。

目标: Hermes 未来能证明"当时究竟看到了什么"。
- 每条进入 Agent 的信息 → 固化原始内容到 data_cache/evidence_raw/<evidence_id>_<sha12>.json（只写一次, 禁覆盖）。
- 统一登记 state/evidence_registry.jsonl（每行一条, 含 sha256 / point_in_time_valid）。
- 同一 source_url 内容变化 → 新版本(version+1), 记录 previous/new sha 与 changed_at; 旧版本永久保留。
- snapshot 只引用 evidence_id + content_sha256（不依赖"现在打开 URL 看到什么"）。
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data_cache" / "evidence_raw"
REGISTRY = ROOT / "state" / "evidence_registry.jsonl"

FNV = None  # noqa
_seq_cache = {"loaded": False, "n": 0}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha256(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _load_registry():
    if not REGISTRY.exists():
        return []
    out = []
    for ln in REGISTRY.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except Exception:  # noqa: BLE001
                pass
    return out


def all_evidence():
    return _load_registry()


def get(evidence_id):
    for e in _load_registry():
        if e["evidence_id"] == evidence_id:
            return e
    return None


def _next_id(t):
    regs = _load_registry()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    same = [e for e in regs if e.get("type") == t and e.get("evidence_id", "").startswith(f"ev_{t}_{day}_")]
    return f"ev_{t}_{day}_{len(same)+1:04d}"


def _write_raw(evidence_id, content_sha256, payload):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    p = RAW_DIR / f"{evidence_id}_{content_sha256[:12]}.json"
    if p.exists():
        # 不可变: 已存在则校验一致, 绝不覆盖
        existing = hashlib.sha256(p.read_bytes()).hexdigest()
        if p.read_text(encoding="utf-8") and json.loads(p.read_text(encoding="utf-8")).get("_sha256") != content_sha256:
            raise RuntimeError(f"evidence_raw collision/mismatch: {p}")
        return p, False
    doc = {"evidence_id": evidence_id, "content_sha256": content_sha256,
           "written_at": _now(), "payload": payload, "_sha256": content_sha256}
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return p, True


def _append_registry(rec):
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _pit_valid(published_at, retrieved_at):
    """point_in_time_valid: 发布时刻 <= 取回时刻(或发布未知但已标记)。"""
    if not published_at:
        return "unknown"
    try:
        pa = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
        ra = datetime.fromisoformat(str(retrieved_at).replace("Z", "+00:00"))
        return pa <= ra
    except Exception:  # noqa: BLE001
        return "unknown"


def record(type, source, source_url, payload, published_at=None, effective_at=None,
           credibility=None, tier=None, extra=None, source_rank=None):
    """固化一条证据。返回 registry 记录(dict)。
    news 类型: 同 source_url 内容变化 → 新版本。"""
    content_sha = _sha256(payload)
    retrieved_at = _now()
    # 新闻版本处理
    version, prev_sha, changed_at = 1, None, None
    if type == "news" and source_url:
        prior = [e for e in _load_registry() if e.get("type") == "news"
                 and e.get("source_url") == source_url]
        if prior:
            latest = prior[-1]
            if latest.get("content_sha256") == content_sha:
                # 重复(同 URL 同内容) → 返回既有, 不新增
                latest["_duplicate"] = True
                return latest
            version = int(latest.get("version", 1)) + 1
            prev_sha = latest.get("content_sha256")
            changed_at = retrieved_at
    eid = _next_id(type)
    data_sha = content_sha
    rec = {
        "evidence_id": eid, "type": type, "source": source, "source_url": source_url,
        "published_at": published_at, "retrieved_at": retrieved_at,
        "effective_at": effective_at, "content_sha256": content_sha, "data_sha256": data_sha,
        "point_in_time_valid": _pit_valid(published_at, retrieved_at),
        "credibility": credibility, "source_rank": source_rank, "tier": tier,
        "version": version, "previous_content_sha256": prev_sha, "changed_at": changed_at,
    }
    if extra:
        rec.update({k: v for k, v in extra.items() if k not in rec})
    p, created = _write_raw(eid, content_sha, payload)
    rec["raw_path"] = str(p.relative_to(ROOT))
    rec["raw_created"] = created
    _append_registry(rec)
    return rec


def record_news(item, first_seen_at=None):
    payload = {"title": item.get("title"), "content": item.get("content"),
               "published_at": item.get("published_at") or item.get("published_at_raw"),
               "source": item.get("source")}
    return record("news", item.get("source"), item.get("source_url"), payload,
                  published_at=item.get("published_at") or item.get("published_at_raw"),
                  credibility=item.get("credibility"), tier=item.get("tier"))


def record_data(type, source, source_url, payload, published_at=None, effective_at=None, extra=None):
    return record(type, source, source_url, payload, published_at=published_at,
                  effective_at=effective_at, credibility="CONFIRMED", extra=extra)


def verify(evidence_id):
    """回溯校验: registry → raw → sha256 一致。返回 (ok, detail)。"""
    e = get(evidence_id)
    if not e:
        return False, "not_found"
    p = ROOT / e["raw_path"]
    if not p.exists():
        return False, "raw_missing"
    doc = json.loads(p.read_text(encoding="utf-8"))
    calc = _sha256(doc["payload"])
    ok = (calc == e["content_sha256"] == doc["content_sha256"])
    return ok, ("ok" if ok else f"sha_mismatch calc={calc[:12]} reg={e['content_sha256'][:12]}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("registry entries:", len(all_evidence()))
    if all_evidence():
        e = all_evidence()[-1]
        print("last:", e["evidence_id"], e["type"], e["content_sha256"][:12], "verify:", verify(e["evidence_id"]))
