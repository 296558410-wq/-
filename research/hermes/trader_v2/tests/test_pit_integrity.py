# -*- coding: utf-8 -*-
"""Phase-1.5 PIT 自测: T0 生成 snapshot；T1 修改新闻 + 修订宏观数据；
验证 T0 snapshot 内容不变，且可完整回溯 T0 evidence → registry → raw → sha256。
日志: logs/test_pit_integrity.log
"""
import sys, json, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
import evidence as EV  # noqa: E402
import release_registry as RR  # noqa: E402
import agent2 as A2  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_pit_integrity.log"
_results = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    log(f"{'PASS' if cond else 'FAIL'} | {name} {detail}")


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== PIT integrity self-test (T0 / T1) ===")

    # ---- T0: 生成快照 ----
    T0 = datetime.now(timezone.utc)
    snap, ver = A2.build("TEST_PIT_T0")
    t0_bytes = ver.read_bytes()
    t0_sha = hashlib.sha256(t0_bytes).hexdigest()
    log(f"T0 snapshot {ver.name} sha={t0_sha[:12]}")
    refs = []
    for grp in ("geopolitics", "macro"):
        for ev in (snap.get(grp, {}).get("events", []) if grp == "geopolitics" else snap["macro"].get("economic_data", [])):
            if ev.get("evidence_id"):
                refs.append(ev["evidence_id"])
    refs += list(snap.get("evidence", {}).get("refs", []))
    refs = sorted(set(refs))
    log(f"T0 evidence refs: {len(refs)}")
    check("T0 refs captured", len(refs) > 0, f"n={len(refs)}")

    # 记录 T0 时各 evidence 的 sha
    t0_ev = {e: (EV.get(e) or {}).get("content_sha256") for e in refs}

    # ---- T1: 新闻被修改 + 宏观被修订（key/url 每次唯一 → 幂等，不受历史状态影响）----
    STAMP = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    KEY = "TEST_CPI_" + STAMP
    u = "https://pit.test/news1-" + STAMP
    EV.record_news({"title": "T0 原始标题", "content": "T0 原始正文", "source": "cnbc", "source_url": u, "published_at": None})
    e_t1 = EV.record_news({"title": "T1 被修改标题", "content": "T1 被修改正文", "source": "cnbc", "source_url": u, "published_at": None})
    log(f"T1 news update version={e_t1.get('version')} prev={str(e_t1.get('previous_content_sha256'))[:8]}")

    # 宏观修订: 同一 release 观察两次不同值
    r1 = RR.observe(KEY, "2026-08", 3.1, "BLS", "https://api.bls.gov", release_timestamp=None)
    r2 = RR.observe(KEY, "2026-08", 3.4, "BLS", "https://api.bls.gov", release_timestamp=None)
    log(f"T1 macro revision: v{r1['revision_number']}->v{r2['revision_number']} first={r2['first_published_value']} latest={r2['latest_known_value']}")

    # ---- 验证 1: T0 快照文件字节不变 ----
    t1_bytes = ver.read_bytes()
    check("T0 snapshot unchanged after T1", hashlib.sha256(t1_bytes).hexdigest() == t0_sha, "byte-identical")

    # ---- 验证 2: T0 引用的原始证据不可变 ----
    immutable_ok = True
    for e in refs:
        rec = EV.get(e)
        if not rec:
            immutable_ok = False
            continue
        ok, detail = EV.verify(e)
        if not ok or rec.get("content_sha256") != t0_ev.get(e):
            immutable_ok = False
            log(f"  evidence changed/mismatch: {e} {detail}")
    check("T0 evidence immutable (sha256)", immutable_ok, f"checked={len(refs)}")

    # ---- 验证 3: 可完整回溯 snapshot → registry → raw → sha256 ----
    chain_ok = True
    for e in refs[:10]:
        rec = EV.get(e)
        if not rec:
            chain_ok = False; continue
        raw = ROOT / rec["raw_path"]
        if not raw.exists():
            chain_ok = False; continue
        doc = json.loads(raw.read_text(encoding="utf-8"))
        if hashlib.sha256(json.dumps(doc["payload"], sort_keys=True, ensure_ascii=False).encode()).hexdigest() != rec["content_sha256"]:
            chain_ok = False
    check("traverse snapshot->registry->raw->sha256", chain_ok, f"traversed={min(len(refs),10)}")

    # ---- 验证 4: PIT 访问器 value_asof ----
    v_t0 = RR.value_asof(KEY, "2026-08", T0.isoformat())     # T0 时点(修订前) → 应看不到 3.4
    v_future = RR.value_asof(KEY, "2026-08", (T0 + timedelta(minutes=10)).isoformat())
    check("PIT value_asof (T0 sees pre-revision)",
          (v_t0 is None or v_t0.get("value") == 3.1) and v_future and v_future.get("value") == 3.4,
          f"T0={None if v_t0 is None else v_t0.get('value')} T1={v_future.get('value') if v_future else None}")

    ok = all(bool(c) for _, c in _results)
    log(f"=== RESULT: {sum(1 for _,c in _results if c)}/{len(_results)} PASS ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
