# -*- coding: utf-8 -*-
"""V2 回归 — P1-B Replay Input Snapshot（离线可重建 + fail-closed）。

断言:
- build_snapshot + offline_replay 重建 decision == 原 decision（WAIT/TRADE/REJECT）
- 确定性: 同一 snapshot 两次 replay 一致
- hash 随内容变化
- fail-closed: missing field / schema mismatch / hash mismatch / wrong instrument / invalid ts
- offline 不联网（import 链不含 http）
日志: logs/test_replay_snapshot.log
"""
from __future__ import annotations
import copy
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "runtime"))
sys.path.insert(0, str(ROOT / "hermes"))
import replay_inputs as RI  # noqa: E402
import hermes as H  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_replay_snapshot.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def _a1(regime="trend", bias="up", pos=50, rm=5.0):
    eb = int(datetime.now(timezone.utc).timestamp())
    tf = lambda: {"trend_range": {"cat": "trend"}, "structure": {"swing_bias": bias},
                  "exp_cont": {"state": "neutral"}, "breakout": {"state": "inside", "range_hi": 4360.0, "range_lo": 4340.0},
                  "range60": {"high": 4360.0, "low": 4340.0, "pos_pct": pos}, "atr_pct": 0.18, "recent_move_bps": rm}
    return {"agent_version": "agent1/test", "generated_utc": datetime.now(timezone.utc).isoformat(),
            "market_regime": {"regime": regime},
            "timeframes": {"15m": tf(), "60m": tf(), "4h": tf(), "1d": tf(), "5m": tf()},
            "price_basis": {"primary_last": 4350.0}, "quotes": {"gold_spot": {"spread": 0.35}},
            "data_quality": {"gaps": [], "by_tf": {"15m": {"last_bar_ts": eb}}}}


def _a2(macro="BULLISH"):
    eb = int(datetime.now(timezone.utc).timestamp())
    return {"agent_version": "agent2/test", "snapshot_ts": datetime.now(timezone.utc).isoformat(),
            "gold_macro_state": macro, "macro_status": "OK",
            "macro": {"usd": {"change_pct_1d": -0.5, "data_ts": eb}, "rates": {"change_pct_1d": -0.5, "data_ts": eb}, "economic_data": []},
            "geopolitics": {"events": []}, "narrative_vs_flow": {"narrative_flow_divergence": False},
            "gold_flows": {"etf": {"cn_gold_etf_net_inflow_sum_cny": 1e6}}, "evidence": {"refs": ["e1"]}}


def _ctx():
    return {"context_id": "ctx_test", "context_hash": "h_test", "market": {"instrument": "XAUUSD", "primary_last": 4350.0},
            "agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"}, "health": {"overall_status": "PASS"}}


def _mk(regime="trend", bias="up", pos=50, rm=5.0, macro="BULLISH"):
    ctx, a1, a2 = _ctx(), _a1(regime, bias, pos, rm), _a2(macro)
    d, cands, tags = H.decide_pure(ctx, a1, a2)
    prov = {"primary_last": {"source": "local_fxtm", "source_hash": "a" * 64, "data_ts": 123}}
    return RI.build_snapshot(d, ctx, a1, a2, cands, tags, provenance=prov), d


def main():
    # TRADE case
    snap, d = _mk()
    check("built snapshot has hash", isinstance(snap.get("snapshot_hash"), str) and len(snap["snapshot_hash"]) == 64)
    r = RI.offline_replay(snap)
    check("replay TRADE matches", r["match"] and r["replay_decision"] == d["decision"], f"{r['replay_decision']} vs {d['decision']}")
    r2 = RI.offline_replay(copy.deepcopy(snap))
    check("determinism", r2["match"] and r2["replay_decision"] == r["replay_decision"])

    # REJECT case (追高 pos 93)
    snapR, dR = _mk(regime="range", bias="neutral", pos=93)
    rR = RI.offline_replay(snapR)
    check("replay REJECT matches", rR["match"] and rR["replay_decision"] == dR["decision"], f"{rR['replay_decision']} vs {dR['decision']}")

    # WAIT case (conflict: LONG vs BEARISH)
    snapW, dW = _mk(macro="BEARISH")
    rW = RI.offline_replay(snapW)
    check("replay WAIT matches", rW["match"] and rW["replay_decision"] == "WAIT", f"{rW['replay_decision']}")

    # hash sensitivity
    mut = copy.deepcopy(snap)
    mut["market_inputs"]["primary_last"] = mut["market_inputs"]["primary_last"] + 1
    try:
        RI.offline_replay(mut); check("hash mismatch reject", False)
    except RI.ReplayError as e:
        check("hash mismatch reject", e.code == "SNAPSHOT_HASH_MISMATCH", e.code)

    # missing field
    mf = copy.deepcopy(snap); mf.pop("macro_inputs", None)
    try:
        RI.offline_replay(mf); check("missing field reject", False)
    except RI.ReplayError as e:
        check("missing field reject", e.code == "SNAPSHOT_MISSING_FIELD", e.code)

    # schema mismatch
    ms = copy.deepcopy(snap); ms["schema_version"] = "x"
    try:
        RI.offline_replay(ms); check("schema mismatch reject", False)
    except RI.ReplayError as e:
        check("schema mismatch reject", e.code == "SNAPSHOT_SCHEMA_MISMATCH", e.code)

    # wrong instrument
    wi = copy.deepcopy(snap); wi["instrument"] = "GC_F"
    try:
        RI.offline_replay(wi); check("wrong instrument reject", False)
    except RI.ReplayError as e:
        check("wrong instrument reject", e.code == "WRONG_INSTRUMENT", e.code)

    # invalid ts
    it = copy.deepcopy(snap); it["decision_ts"] = "not-a-time"
    try:
        RI.offline_replay(it); check("invalid ts reject", False)
    except RI.ReplayError as e:
        check("invalid ts reject", e.code == "SNAPSHOT_INVALID_TS", e.code)

    # offline: module must not import http libs
    src = (ROOT / "runtime" / "replay_inputs.py").read_text(encoding="utf-8")
    check("no network imports in replay_inputs", all(t not in src for t in ("requests", "urllib", "http.client", "socket")))

    # provenance (P1 residual 3.1)
    import hashlib as _hl, json as _js

    def _rehash(o):
        o.pop("snapshot_hash", None)
        o["snapshot_hash"] = _hl.sha256(_js.dumps({k: v for k, v in o.items() if k != "snapshot_hash"},
                                                   sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    sni2 = copy.deepcopy(snap); sni2["source_provenance"] = {}; _rehash(sni2)
    try:
        RI.offline_replay(sni2); check("provenance missing -> reject", False)
    except RI.ReplayError as e:
        check("provenance missing -> reject", e.code == "SOURCE_PROVENANCE_MISSING", e.code)
    sni3 = copy.deepcopy(snap); sni3["source_provenance"] = {"primary_last": {"source_hash": "bad"}}; _rehash(sni3)
    try:
        RI.offline_replay(sni3); check("provenance invalid -> reject", False)
    except RI.ReplayError as e:
        check("provenance invalid -> reject", e.code == "SOURCE_PROVENANCE_INVALID", e.code)

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
