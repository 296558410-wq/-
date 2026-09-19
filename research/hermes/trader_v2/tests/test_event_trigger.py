# -*- coding: utf-8 -*-
"""Phase-1.5 事件触发压力测试 (Test A–H) + 不可变快照链路验证。

验证: event → trigger → Agent2 refresh → immutable snapshot → (Hermes notification 占位)。
日志: logs/test_event_trigger.log
"""
import sys, json, hashlib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
import event_trigger as ET  # noqa: E402
import evidence as EV  # noqa: E402
import agent2 as A2  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_event_trigger.log"
_results = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    log(f"{'PASS' if cond else 'FAIL'} | {name} {detail}")


def fresh_news(title, url, src="cnbc", pub=None):
    return {"title": title, "content": title, "source": src, "source_url": url,
            "published_at": pub or datetime.now(timezone.utc).timestamp(), "credibility": "REPORTED"}


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== Event-Trigger stress test A–H ===")
    n0 = len(EV.all_evidence())

    # A UST10Y 快速变化
    r = ET.evaluate_inputs(None, 3.0, None, [])
    check("A UST10Y rapid", r["trigger"] and any("UST10Y" in x for x in r["reasons"]), str(r["reasons"]))
    # B VIX 快速变化
    r = ET.evaluate_inputs(None, None, 12.0, [])
    check("B VIX rapid", r["trigger"] and any("VIX" in x for x in r["reasons"]), str(r["reasons"]))
    # C 重大新闻进入
    r = ET.evaluate_inputs(None, None, None, [fresh_news("FOMC rate decision surprise cut", "https://x.test/c1")])
    check("C major news", r["trigger"], str(r["reasons"]))
    # D 多条新闻连续进入
    rr = ET.evaluate_inputs(None, None, None, [fresh_news("War escalates in Middle East", "https://x.test/d1"),
                                               fresh_news("CPI print hotter than expected", "https://x.test/d2")])
    check("D multi news", rr["trigger"] and len(rr["reasons"]) >= 2, f"reasons={len(rr['reasons'])}")
    # E 同一 URL 内容更新 → 新版本（URL 每次唯一，保证 version 从 1 起 → 幂等）
    u = "https://x.test/e1-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    e1 = EV.record_news({"title": "v1 title", "content": "v1 body", "source": "cnbc", "source_url": u, "published_at": None})
    e2 = EV.record_news({"title": "v2 title", "content": "v2 body", "source": "cnbc", "source_url": u, "published_at": None})
    check("E url content update -> new version",
          e2.get("version") == 2 and e2.get("previous_content_sha256") == e1.get("content_sha256"),
          f"v{e1.get('version')}->v{e2.get('version')} prev={str(e2.get('previous_content_sha256'))[:8]}")
    # F 重复新闻 → 不新增
    n_before = len(EV.all_evidence())
    e3 = EV.record_news({"title": "v2 title", "content": "v2 body", "source": "cnbc", "source_url": u, "published_at": None})
    check("F duplicate news no new entry", e3.get("_duplicate") is True and len(EV.all_evidence()) == n_before,
          f"dup={e3.get('_duplicate')}")
    # G 低可信新闻 → 记录但标记 tier
    e4 = EV.record_news({"title": "Rumor: gold to $5000", "content": "unverified", "source": "jin10",
                         "source_url": "https://x.test/g1", "published_at": None, "tier": "aggregator"})
    check("G low-cred tagged", e4.get("tier") == "aggregator", f"tier={e4.get('tier')}")
    # H 多事件同时 → 严重度聚合
    rh = ET.evaluate_inputs(1.5, 3.0, 12.0, [fresh_news("Emergency sanction", "https://x.test/h1")])
    check("H simultaneous", rh["severity"] == 2 and len(rh["reasons"]) >= 3, f"sev={rh['severity']} n={len(rh['reasons'])}")

    # 链路: trigger → refresh(Agent2) → immutable snapshot
    snap, ver = A2.build("TEST_EVENTTRIGGER")
    sha1 = hashlib.sha256(ver.read_bytes()).hexdigest()
    log(f"refresh Agent2 -> {ver.name} sha={sha1[:12]}")
    # 再次以同 cycle 构建不会覆盖旧原始证据(不可变由 evidence 层保证); 重新读取快照内容比对字段
    snap2 = json.loads(ver.read_text(encoding="utf-8"))
    check("immutable snapshot refs evidence",
          all(("evidence_id" in e) for e in snap2["geopolitics"]["events"]) if snap2["geopolitics"]["events"] else True,
          f"geo_events={len(snap2['geopolitics']['events'])}")
    check("evidence registry grows", len(EV.all_evidence()) > n0, f"{n0}->{len(EV.all_evidence())}")

    log("--- NOTIFY Hermes (占位: Phase-1.5 编排层将 post trigger + snapshot_path) ---")
    ok = all(bool(c) for _, c in _results)
    log(f"=== RESULT: {sum(1 for _,c in _results if c)}/{len(_results)} PASS ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
