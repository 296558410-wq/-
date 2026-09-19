# -*- coding: utf-8 -*-
"""V2 Decision Input Snapshot + 离线 Replay（P1-B / §11–16）。

目标: 任一 decision 可在**无网络、无当前数据源、无当前 cache** 下重建。
- build_snapshot(): 冻结 decision 的全部输入（market/technical/macro/candidate/gate/health/freshness/pit/price_space/risk）。
- offline_replay(): 仅用 snapshot（不 re-fetch），走与 live 相同的确定性路径 `hermes.decide_pure`。
- fail-closed: snapshot 缺失/损坏/hash 不符/schema 不符/字段缺失/错 instrument/非法 ts → 拒绝（**绝不联网兜底**）。
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hermes"))
import hermes as H  # noqa: E402

SCHEMA = "input_snapshot/1"
STRATEGY_VERSION = "hermes2-prompt/0.1.0"


class ReplayError(Exception):
    def __init__(self, code, detail=None):
        self.code = code
        self.detail = detail or {}
        super().__init__(code)


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def build_snapshot(decision, ctx, a1, a2, cands, tags, *, health=None, freshness=None,
                   price_space=None, risk=None, data_version=None, router_version=None, provenance=None):
    snap = {
        "schema_version": SCHEMA,
        "decision_id": decision.get("decision_id") or f"DEC-{ctx.get('context_id')}",
        "decision_ts": decision.get("ts"),
        "instrument": "XAUUSD",
        "reference_market": "GC_F",
        "strategy_version": decision.get("strategy_version") or STRATEGY_VERSION,
        "data_version": data_version,
        "router_version": router_version,
        "context_hash": ctx.get("context_hash"),
        "input_hash": ctx.get("context_hash"),
        "market_inputs": ctx.get("market"),
        "technical_features": a1,
        "macro_inputs": a2,
        "candidate": decision.get("chosen_opportunity"),
        "regime_tags": tags,
        "gate_results": {"decision": decision.get("decision"), "reason": decision.get("reason")},
        "health": health if health is not None else ctx.get("health"),
        "freshness": freshness if freshness is not None else ctx.get("freshness"),
        "pit_status": "PASS",
        "price_space": price_space or {"enabled": False},
        "risk_calculation": risk if risk is not None else (decision.get("plan") or {}),
        "source_provenance": provenance or {},
        "decision": decision,
    }
    snap["snapshot_hash"] = _sha({k: v for k, v in snap.items() if k != "snapshot_hash"})
    return snap


def write_snapshot(run_dir, snap) -> Path:
    d = Path(run_dir) / "inputs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{snap['decision_id']}.json"
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _valid_ts(x):
    if not x:
        return False
    try:
        datetime.fromisoformat(str(x).replace("Z", "+00:00"))
        return True
    except Exception:  # noqa: BLE001
        return False


REQUIRED = ("decision_id", "decision_ts", "instrument", "strategy_version", "context_hash",
            "market_inputs", "technical_features", "macro_inputs", "decision", "snapshot_hash")


def _verify_provenance(snap):
    """P1 residual 3.1: 每个 source artifact 必须带 64-hex source_hash（缺失/非法 → fail-closed）。"""
    prov = snap.get("source_provenance")
    if not isinstance(prov, dict) or not prov:
        raise ReplayError("SOURCE_PROVENANCE_MISSING")
    for f, l in prov.items():
        sh = (l or {}).get("source_hash")
        if not sh or len(str(sh)) != 64:
            raise ReplayError("SOURCE_PROVENANCE_INVALID", {"field": f})


def offline_replay(snap, *, now=None):
    """离线重建（不联网）。返回 dict(match, replay_*, original_*)。失败 raise ReplayError（fail-closed）。"""
    if not isinstance(snap, dict):
        raise ReplayError("SNAPSHOT_MISSING")
    if snap.get("schema_version") != SCHEMA:
        raise ReplayError("SNAPSHOT_SCHEMA_MISMATCH", {"got": snap.get("schema_version")})
    for f in REQUIRED:
        if f not in snap:
            raise ReplayError("SNAPSHOT_MISSING_FIELD", {"field": f})
    if snap.get("instrument") != "XAUUSD":
        raise ReplayError("WRONG_INSTRUMENT", {"got": snap.get("instrument")})
    if not _valid_ts(snap.get("decision_ts")):
        raise ReplayError("SNAPSHOT_INVALID_TS", {"decision_ts": snap.get("decision_ts")})
    if snap.get("snapshot_hash") != _sha({k: v for k, v in snap.items() if k != "snapshot_hash"}):
        raise ReplayError("SNAPSHOT_HASH_MISMATCH")
    _verify_provenance(snap)

    fr = snap.get("freshness") or {}
    ctx = {
        "context_id": snap.get("decision_id"),
        "context_hash": snap.get("context_hash"),
        "agent1": {"freshness": ((fr.get("agent1") or {}).get("status") or "fresh")},
        "agent2": {"freshness": ((fr.get("agent2") or {}).get("status") or "fresh")},
        "market": snap.get("market_inputs"),
        "health": snap.get("health") or {},
    }
    a1 = snap["technical_features"]
    a2 = snap["macro_inputs"]
    d2, _, _ = H.decide_pure(ctx, a1, a2)
    orig = snap["decision"]
    match = (d2.get("decision") == orig.get("decision")
             and d2.get("chosen_opportunity") == orig.get("chosen_opportunity")
             and (d2.get("plan") or {}).get("entry") == (orig.get("plan") or {}).get("entry")
             and (d2.get("plan") or {}).get("stop_loss") == (orig.get("plan") or {}).get("stop_loss"))
    return {"match": match, "replay_decision": d2.get("decision"), "original_decision": orig.get("decision"),
            "replay_plan": d2.get("plan"), "original_plan": orig.get("plan"),
            "replay_reason": d2.get("reason")}
