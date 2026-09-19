# -*- coding: utf-8 -*-
"""V2 独立只读观察器 (READ-ONLY)。

只读聚合 V2 运行产物 → 计算运行健康率指标 + 机会分布，写自有的 observations/ 目录。
**绝不写入 V2 的 state/、research/runs/、ledger/、config/；不下单；不改策略；不碰 V1。**

指标（任务书 §20）：
  data_health_rate / scheduler_success_rate / hermes_response_rate / execution_success_rate /
  ledger_integrity_rate / replay_match_rate  + WAIT·TRADE·REJECT·成交·PnL·机会分布·供给分布
用法：
  python tools/v2_observer.py            # 快照一次并打印摘要
  python tools/v2_observer.py --quiet    # 只写文件
"""
from __future__ import annotations
import json, os, sys, glob, collections
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # trader_v2
OBS = ROOT / "observations"
RUNS = ROOT / "research" / "runs"
sys.path.insert(0, str(ROOT / "ledger"))
import ledger as L  # noqa: E402  (只读使用)


def _load(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def _tail_jsonl(p, n=1):
    try:
        lines = Path(p).read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(x) for x in lines[-n:]]
    except Exception:  # noqa: BLE001
        return []


def snap():
    now = datetime.now(timezone.utc)
    runs = []
    agg = collections.Counter()
    ledger_ok = ledger_n = replay_ok = replay_n = 0
    a1_ok = a1_n = 0
    chosen = collections.Counter(); reasons = collections.Counter(); cats = collections.Counter()
    n_cand = collections.Counter()
    tx = collections.Counter()
    for d in sorted(os.listdir(RUNS)) if RUNS.exists() else []:
        rd = RUNS / d
        st = _load(rd / "run_state.json")
        if not st:
            continue
        c = st.get("counters", {}) or {}
        tl = _tail_jsonl(rd / "timeline.jsonl", 1)
        led = rd / "ledger.jsonl"
        lok = None
        if led.exists():
            lok, _ = L.verify_ledger(led); ledger_n += 1; ledger_ok += 1 if lok else 0
        rm = tl[0].get("replay_match") if tl else None
        if rm is not None:
            replay_n += 1; replay_ok += 1 if rm else 0
        fr = tl[0].get("agent1_freshness") if tl else None
        if fr is not None:
            a1_n += 1; a1_ok += 1 if fr == "ok" else 0
        # decisions distribution
        for f in glob.glob(str(rd / "decisions" / "*.raw.json")):
            o = _load(f) or {}
            chosen[o.get("chosen_opportunity") or "(none)"] += 1
            reasons[(o.get("reason") or "")[:44]] += 1
        for k in ("TRADE", "WAIT", "REJECT"):
            agg[k] += c.get(k, 0)
        agg["cycles"] += c.get("cycles", 0)
        agg["decisions"] += c.get("decisions", 0)
        agg["exec_attempts"] += c.get("exec_attempts", 0)
        agg["executed"] += c.get("exec_executed", 0)
        agg["rejected"] += c.get("exec_rejected", 0)
        agg["failures"] += sum((st.get("failures") or {}).values())
        runs.append({"run_id": d, "status": st.get("status"), "blocked": st.get("blocked"),
                     "counters": c, "ledger_ok": lok, "replay_match": rm, "a1_freshness": fr,
                     "last": (st.get("last_decision") or {})})
    # supply side (candidate pool)
    ctxs = set()
    for d in os.listdir(RUNS) if RUNS.exists() else []:
        for f in glob.glob(str(RUNS / d / "decisions" / "*.raw.json")):
            o = _load(f) or {}
            if o.get("context_id"): ctxs.add(o["context_id"])
    det = collections.defaultdict(set)
    ol = ROOT / "state" / "opportunity_ledger.jsonl"
    if ol.exists():
        for l in ol.read_text(encoding="utf-8").splitlines():
            try: e = json.loads(l)
            except Exception: continue
            if e.get("context_id") in ctxs and not str(e.get("opportunity_id", "")).endswith("_DECISION"):
                det[e["context_id"]].add(e["opportunity_id"])
                for cat in ("trend", "bo_", "fbo_", "macro_repricing", "geo_shock", "narrative_flow"):
                    if cat in e["opportunity_id"]: cats[cat] += 1; break
    for cid in ctxs:
        n_cand[len(det.get(cid, ()))] += 1
    # scheduler + health
    sched = _load(ROOT / "state" / "v2_scheduler_state.json", {}) or {}
    health = _load(ROOT / "state" / "v2_run_health.json", {}) or {}
    active = _load(ROOT / "state" / "runs" / "ACTIVE.json", {}) or {}

    def rate(a, b):
        return round(a / b, 4) if b else None
    out = {
        "ts": now.isoformat(),
        "active_run": active.get("run_id"),
        "scheduler": {"task": "DIRECT_WINDOWS_TASK", "cycles_attempted": sched.get("cycles_attempted", 0),
                      "missed_cycles": sched.get("missed_cycles", 0), "recovery_count": sched.get("recovery_count", 0),
                      "duplicate_prevented": sched.get("duplicate_prevented", 0),
                      "last_success": health.get("last_success"), "last_failure": health.get("last_failure"),
                      "gateway_dependency": health.get("gateway_dependency"), "llm_dependency": health.get("llm_dependency"),
                      "router_enabled": health.get("router_enabled")},
        "totals": dict(agg),
        "opportunity": {"chosen": dict(chosen.most_common()), "reasons": dict(reasons.most_common(8)),
                        "n_candidates_dist": {str(k): v for k, v in sorted(n_cand.items())},
                        "supply_categories": dict(cats)},
        "rates": {
            "scheduler_success_rate": health.get("last_success") is not None and 1.0 or 0.0,
            "data_health_rate(agent1_fresh)": rate(a1_ok, a1_n),
            "hermes_response_rate": rate((agg["decisions"] - agg["failures"]), agg["decisions"]) if agg["decisions"] else None,
            "execution_success_rate": rate(agg["executed"], agg["exec_attempts"]) if agg["exec_attempts"] else None,
            "ledger_integrity_rate": rate(ledger_ok, ledger_n),
            "replay_match_rate": rate(replay_ok, replay_n),
        },
        "runs": runs,
    }
    OBS.mkdir(parents=True, exist_ok=True)
    (OBS / f"v2_observation_{now.strftime('%Y%m%dT%H%M%SZ')}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (OBS / "latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# V2 观察快照 — " + out["ts"], "", f"- active_run: `{out['active_run']}`",
          f"- rates: {json.dumps(out['rates'], ensure_ascii=False)}",
          f"- totals: {json.dumps(out['totals'], ensure_ascii=False)}",
          f"- scheduler: {json.dumps(out['scheduler'], ensure_ascii=False)}",
          f"- opportunity.chosen: {json.dumps(out['opportunity']['chosen'], ensure_ascii=False)}",
          f"- opportunity.n_candidates: {json.dumps(out['opportunity']['n_candidates_dist'], ensure_ascii=False)}",
          f"- opportunity.supply: {json.dumps(out['opportunity']['supply_categories'], ensure_ascii=False)}"]
    (OBS / "latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    o = snap()
    if "--quiet" not in sys.argv:
        print(json.dumps({"active_run": o["active_run"], "rates": o["rates"], "totals": o["totals"],
                          "chosen": o["opportunity"]["chosen"],
                          "n_candidates": o["opportunity"]["n_candidates_dist"]}, ensure_ascii=False, indent=1))
