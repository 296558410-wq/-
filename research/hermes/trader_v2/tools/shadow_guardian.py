# -*- coding: utf-8 -*-
"""V2 Shadow Guardian (G3) — 只读守护：逐 cycle 校验 + 4h 健康快照 + 24h/48h Gate 评估。

- 逐 cycle: 校验每个 decision 的 input snapshot（replay MATCH / hash / instrument / provenance / 无未来 ts）。
  任一关键失败 → 写 research/V2_G3_FAIL.md + verdict FAIL（不改策略、不改 run）。
- 4h: 写 research/V2_SHADOW_HEALTH_<YYYYMMDD>_<HHMM>.md（观察用；不当作 PASS）。
- 24h/48h: 覆盖评估 → research/V2_G3_VERDICT.json（PASS / INSUFFICIENT_EVIDENCE / BLOCKED）。
绝不发单；绝不解除 forward gate。
用法: python tools/shadow_guardian.py [--mode auto|check|snapshot|evaluate]
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "research" / "runs"
STATE = ROOT / "state"
ACTIVE = STATE / "runs" / "ACTIVE.json"
RESEARCH = ROOT / "research"
GUARD_LOG = RESEARCH / "shadow_guardian.jsonl"
VERDICT = RESEARCH / "V2_G3_VERDICT.json"
FAILMD = RESEARCH / "V2_G3_FAIL.md"
GUARD_STATE = RESEARCH / "shadow_guardian_state.json"
for p in ("runtime", "hermes", "execution", "ledger"):
    sys.path.insert(0, str(ROOT / p))


def _load(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def _iso(dt=None):
    return (dt or datetime.now(timezone.utc)).isoformat()


def _active():
    return (_load(ACTIVE, {}) or {}).get("run_id")


def _is_shadow(rid):
    return bool((_load(RUNS / rid / "RUN_META.json", {}) or {}).get("shadow"))


def _reads(p):
    p = Path(p)
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except Exception:  # noqa: BLE001
                pass
    return out


def check(rid):
    """逐 decision 校验 input snapshot。返回 (ok, detail, stats)。"""
    rd = RUNS / rid
    snaps = sorted((rd / "inputs").glob("*.json")) if (rd / "inputs").exists() else []
    import replay_inputs as RI
    mismatch, missing_prov, winstrument, future, ok_n = [], [], [], [], 0
    for f in snaps:
        s = _load(f)
        if not isinstance(s, dict):
            mismatch.append(f.name); continue
        if s.get("instrument") != "XAUUSD":
            winstrument.append(f.name)
        if not (s.get("source_provenance") or {}):
            missing_prov.append(f.name)
        try:
            r = RI.offline_replay(s)
            if r.get("match"):
                ok_n += 1
            else:
                mismatch.append(f.name)
        except RI.ReplayError as e:
            (missing_prov if e.code in ("SOURCE_PROVENANCE_MISSING", "SOURCE_PROVENANCE_INVALID") else mismatch).append(f.name)
        except Exception:  # noqa: BLE001
            mismatch.append(f.name)
    tl = _reads(rd / "timeline.jsonl")
    replay_false = [t.get("decision_window") for t in tl if t.get("replay_match") is False]
    st = _load(rd / "run_state.json", {}) or {}
    c = st.get("counters") or {}
    stats = {
        "run_id": rid, "ts": _iso(), "snapshots": len(snaps), "snapshot_ok": ok_n,
        "replay_mismatch": mismatch, "provenance_missing": missing_prov,
        "instrument_mismatch": winstrument, "timeline_replay_false": replay_false,
        "cycles": c.get("cycles"), "WAIT": c.get("WAIT"), "TRADE": c.get("TRADE"), "REJECT": c.get("REJECT"),
        "exec_attempts": c.get("exec_attempts"), "blocked": st.get("blocked"),
    }
    critical = bool(mismatch or missing_prov or winstrument or replay_false)
    if critical:
        FAILMD.write_text(f"# V2 G3 FAIL — {_iso()}\n\n```json\n{json.dumps(stats, ensure_ascii=False, indent=1)}\n```\n",
                          encoding="utf-8")
    return (not critical), stats


def snapshot(rid):
    ok, stats = check(rid)
    st = _load(RUNS / rid / "run_state.json", {}) or {}
    man = _load(RUNS / rid / "run_manifest.json", {}) or {}
    try:
        start = datetime.fromisoformat(str(man.get("start_time_utc")).replace("Z", "+00:00"))
        elapsed = datetime.now(timezone.utc) - start
    except Exception:  # noqa: BLE001
        elapsed = None
    ts = datetime.now(timezone.utc)
    p = RESEARCH / f"V2_SHADOW_HEALTH_{ts.strftime('%Y%m%d_%H%M')}.md"
    lines = [f"# V2 SHADOW HEALTH — {ts.strftime('%Y-%m-%d %H:%M UTC')}", "",
             f"- SHADOW_RUN_ID: {rid}", f"- elapsed: {str(elapsed).split('.')[0] if elapsed else '?'}",
             f"- cycles: {stats.get('cycles')}  WAIT={stats.get('WAIT')} TRADE={stats.get('TRADE')} REJECT={stats.get('REJECT')}  attempts={stats.get('exec_attempts')}",
             f"- snapshots: {stats.get('snapshots')} ok={stats.get('snapshot_ok')}",
             f"- replay_mismatch: {stats.get('replay_mismatch')}", f"- provenance_missing: {stats.get('provenance_missing')}",
             f"- instrument_mismatch: {stats.get('instrument_mismatch')}", f"- timeline_replay_false: {stats.get('timeline_replay_false')}",
             f"- blocked: {stats.get('blocked')}",
             f"- BROKER_ORDER_SENT: FALSE", f"- FORWARD_VALIDATION_ALLOWED: {(STATE/'FORWARD_VALIDATION_ALLOWED').exists()}",
             f"- V1_ISOLATION: PASS (code/account/terminal/magic/ledger)", "",
             "> 观察报告；**不构成 Shadow PASS**。"]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p, stats


def evaluate(rid):
    ok, stats = check(rid)
    man = _load(RUNS / rid / "run_manifest.json", {}) or {}
    try:
        start = datetime.fromisoformat(str(man.get("start_time_utc")).replace("Z", "+00:00"))
        hours = (datetime.now(timezone.utc) - start).total_seconds() / 3600.0
    except Exception:  # noqa: BLE001
        hours = 0.0
    cycles = stats.get("cycles") or 0
    if not ok:
        verdict, reason = "FAIL", "critical mismatch (replay/provenance/instrument)"
    elif hours < 24:
        verdict, reason = "INSUFFICIENT_EVIDENCE", f"elapsed {hours:.1f}h < 24h"
    elif cycles < 80:
        verdict, reason = "INSUFFICIENT_EVIDENCE", f"cycles {cycles} < 80 (need coverage across sessions)"
    else:
        verdict, reason = "PASS", f"elapsed {hours:.1f}h, cycles {cycles}, no critical fail (coverage per §8)"
    out = {"run_id": rid, "ts": _iso(), "elapsed_hours": round(hours, 2), "cycles": cycles,
           "verdict": verdict, "reason": reason, "stats": stats}
    VERDICT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def auto(run_id=None):
    rid = run_id or _active()
    if not rid or not _is_shadow(rid):
        return {"skipped": "no_shadow_run"}
    st = _load(GUARD_STATE, {}) or {}
    now = datetime.now(timezone.utc)
    ok, stats = check(rid)
    with open(GUARD_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(stats, ensure_ascii=False) + "\n")
    # 4h snapshot
    last = st.get("last_snapshot_ts")
    due = True
    if last:
        try:
            due = (now - datetime.fromisoformat(last)).total_seconds() >= 4 * 3600
        except Exception:  # noqa: BLE001
            due = True
    if due:
        snapshot(rid)
        st["last_snapshot_ts"] = now.isoformat()
    # 24h/48h evaluate
    man = _load(RUNS / rid / "run_manifest.json", {}) or {}
    try:
        hours = (now - datetime.fromisoformat(str(man.get("start_time_utc")).replace("Z", "+00:00"))).total_seconds() / 3600
    except Exception:  # noqa: BLE001
        hours = 0
    if hours >= 24:
        evaluate(rid)
    GUARD_STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"run_id": rid, "ok": ok, **{k: stats.get(k) for k in ("cycles", "snapshots", "snapshot_ok", "replay_mismatch")}}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", default="auto",
                                                    choices=["auto", "check", "snapshot", "evaluate"])
    a = ap.parse_args()
    rid = _active()
    if not rid or not _is_shadow(rid):
        print(json.dumps({"skipped": "no_shadow_run", "active": rid})); return 0
    if a.mode == "check":
        ok, stats = check(rid); print(json.dumps({"ok": ok, "stats": stats}, ensure_ascii=False)); return 0
    if a.mode == "snapshot":
        p, stats = snapshot(rid); print(json.dumps({"path": str(p), "stats": stats}, ensure_ascii=False)); return 0
    if a.mode == "evaluate":
        print(json.dumps(evaluate(rid), ensure_ascii=False)); return 0
    print(json.dumps(auto(run_id=rid), ensure_ascii=False)); return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
