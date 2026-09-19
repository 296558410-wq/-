# -*- coding: utf-8 -*-
"""Hermes V2 决策上下文（Decision Context）—— 冻结"当时用了什么"（Phase-1 §18）。

每次决策生成一个 decision_context, 引用当时实际使用的:
  Agent1 snapshot / Agent2 snapshot / market snapshot / evidence / config / 版本
并计算 context_hash。固化写入 state/decision_contexts/<context_id>.json（不可覆盖）。
以后 Agent2 更新 snapshot 也不得改变过去的 decision_context。
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # hermes/context.py → trader_v2 (修正: 原 parents[2] 多算一级)
STATE = ROOT / "state"
CTX_DIR = STATE / "decision_contexts"
CONFIG = ROOT / "config" / "v2_config.json"
HERMES_VERSION = "hermes2/0.1.0"
PROMPT_VERSION = "hermes2-prompt/0.1.0"

FRESH_RULES = {"agent1": [(1200, "fresh"), (3600, "stale"), (10**9, "expired")],
               "agent2": [(4500, "fresh"), (10800, "stale"), (10**9, "expired")]}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _freshness(ts_iso, kind):
    if not ts_iso:
        return "unknown", None
    try:
        t = datetime.fromisoformat(str(ts_iso).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return "unknown", None
    age = (datetime.now(timezone.utc) - t).total_seconds()
    for thr, lbl in FRESH_RULES[kind]:
        if age < thr:
            return lbl, int(age)
    return "expired", int(age)


def _to_epoch(x):
    """接受 iso 字符串或 epoch 秒/毫秒 → epoch 秒（失败 None）。P0-04 用 data_ts。"""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        v = float(x)
        return v / 1000.0 if v > 1e12 else v
    try:
        return datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception:  # noqa: BLE001
        return None


def _fresh_from_data_ts(epoch_s, kind):
    """P0-04: freshness 基于 data_ts（非 snapshot 生成时刻）。age = now - data_ts。"""
    if epoch_s is None:
        return "unknown", None
    age = datetime.now(timezone.utc).timestamp() - epoch_s
    if age < -5:
        return "unknown", int(age)          # 未来时间戳 → 不可信
    for thr, lbl in FRESH_RULES[kind]:
        if age < thr:
            return lbl, int(age)
    return "expired", int(age)


def _a1_data_ts(a1):
    """Agent1 数据时戳 = 各周期已收盘 bar 的最新时刻。"""
    by = (a1.get("data_quality") or {}).get("by_tf") or {}
    es = [_to_epoch((v or {}).get("last_bar_ts")) for v in by.values()]
    es = [e for e in es if e is not None]
    return max(es) if es else None


def _a2_data_ts(a2):
    """Agent2 数据时戳 = 核心宏观字段 data_ts 的最新值。"""
    m = (a2 or {}).get("macro") or {}
    es = [_to_epoch((m.get(k) or {}).get("data_ts")) for k in ("usd", "rates")]
    es = [e for e in es if e is not None]
    return max(es) if es else None


def _trading_source_status(a1):
    """P0-06(2026-09-18): 交易决策行情（技术 K 线 + XAUUSD 现货价）必须来自 MT5。
    非 mt5（local_fxtm/sina/tencent/eastmoney/yahoo/cache）→ 降级。
    缺失源字段（合成 fixture / 向后兼容）不在此判据。"""
    dq = (a1 or {}).get("data_quality") or {}
    srcs = dq.get("sources") or {}
    hist = srcs.get("history")
    spot = (((a1 or {}).get("quotes") or {}).get("gold_spot") or {}).get("source")
    bad = [f"{n}={v}" for n, v in (("history", hist), ("gold_spot", spot)) if v is not None and v != "mt5"]
    return ("DEGRADED" if bad else "PASS"), bad


def build_health(a1, a2, a1_fr, a2_fr, router_enabled):
    """P0-04: 汇总数据健康度（供 Hermes gate）。PASS / DEGRADED / FAIL。
    P0-06: 交易行情源非 MT5 → technical/overall DEGRADED（MT5 断流 → 安全 WAIT）。"""
    gaps = (a1 or {}).get("data_quality", {}).get("gaps") or []
    src_status, src_bad = _trading_source_status(a1)
    if not a1:
        tech = "FAIL"
    elif gaps or a1_fr in ("stale", "unknown", "expired") or src_status == "DEGRADED":
        tech = "DEGRADED"
    else:
        tech = "PASS"
    ms = (a2 or {}).get("macro_status", "OK")
    macro = {"OK": "PASS", "DEGRADED": "DEGRADED"}.get(ms, "FAIL" if a2 else "FAIL")
    fr = "PASS" if (a1_fr == "fresh" and a2_fr == "fresh") else (
        "FAIL" if ("expired" in (a1_fr, a2_fr) or "unknown" in (a1_fr, a2_fr)) else "DEGRADED")
    comp = {"technical": tech, "trading_source": src_status, "macro": macro,
            "router": "PASS" if router_enabled else "DEGRADED",
            "pit": "PASS", "freshness": fr, "price_space": "DISABLED", "broker": "UNKNOWN"}
    overall = "FAIL" if "FAIL" in comp.values() else ("DEGRADED" if "DEGRADED" in comp.values() else "PASS")
    return {"overall_status": overall, "trading_source_bad": src_bad,
            **{f"{k}_status": v for k, v in comp.items()}}


def build_context(cycle=None, agent1_path=None, agent2_path=None):
    a1 = _load(agent1_path or STATE / "agent1_latest.json") or {}
    a2 = _load(agent2_path or STATE / "agent2_latest.json") or {}
    cfg_raw = CONFIG.read_text(encoding="utf-8") if CONFIG.exists() else ""
    config_hash = hashlib.sha256(cfg_raw.encode("utf-8")).hexdigest()
    # P0-04: freshness 基于 data_ts（数据自身时刻），而非 snapshot 生成时刻
    a1_data_ts = _a1_data_ts(a1)
    a2_data_ts = _a2_data_ts(a2)
    a1_fr, a1_age = _fresh_from_data_ts(a1_data_ts, "agent1")
    a2_fr, a2_age = _fresh_from_data_ts(a2_data_ts, "agent2")
    try:
        _flag = (ROOT / "config" / "data_router.enabled").read_text(encoding="utf-8").strip().lower()
        router_enabled = _flag in ("1", "true", "yes", "on")
    except Exception:  # noqa: BLE001
        router_enabled = False
    health = build_health(a1, a2, a1_fr, a2_fr, router_enabled)
    market = {"instrument": "XAUUSD", "reference_market": "GC_F",
              "primary_last": (a1.get("price_basis") or {}).get("primary_last"),
              "primary_source": (a1.get("price_basis") or {}).get("primary_source"),
              "spread": (a1.get("quotes", {}).get("gold_spot") or {}).get("spread"),
              "source_basis_usd": (a1.get("price_basis") or {}).get("source_basis_usd"),
              "basis_usd": (a1.get("price_basis") or {}).get("basis_usd"),
              "retrieved_at": _now()}
    evidence_ids = []
    for ev in (a2.get("geopolitics", {}).get("events") or []):
        if ev.get("evidence_id"):
            evidence_ids.append(ev["evidence_id"])
    evidence_ids += list(a2.get("evidence", {}).get("refs", []))
    evidence_ids = sorted(set(evidence_ids))
    ctx = {
        "context_id": None,  # 由 hash 决定
        "cycle": cycle or (a1.get("cycle") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")),
        "created_utc": _now(),
        "agent1": {"snapshot_id": a1.get("cycle"), "cycle": a1.get("cycle"),
                   "generated_utc": a1.get("generated_utc"), "freshness": a1_fr, "age_seconds": a1_age,
                   "path": str((agent1_path or STATE / "agent1_latest.json")), "version": a1.get("agent_version")},
        "agent2": {"snapshot_id": a2.get("cycle"), "cycle": a2.get("cycle"),
                   "generated_utc": a2.get("snapshot_ts"), "freshness": a2_fr, "age_seconds": a2_age,
                   "path": str((agent2_path or STATE / "agent2_latest.json")), "version": a2.get("agent_version")},
        "market": market,
        "freshness": {"agent1": {"data_ts": a1_data_ts, "status": a1_fr, "age_seconds": a1_age},
                      "agent2": {"data_ts": a2_data_ts, "status": a2_fr, "age_seconds": a2_age}},
        "health": health,
        "evidence_ids": evidence_ids,
        "config_hash": config_hash,
        "versions": {"agent1": a1.get("agent_version"), "agent2": a2.get("agent_version"),
                     "hermes": HERMES_VERSION, "prompt": PROMPT_VERSION},
    }
    ch = _sha({"cycle": ctx["cycle"],
               "agent1": {k: v for k, v in ctx["agent1"].items() if k != "path"},
               "agent2": {k: v for k, v in ctx["agent2"].items() if k != "path"},
               "market": {k: v for k, v in ctx["market"].items() if k != "retrieved_at"},
               "evidence_ids": ctx["evidence_ids"], "config_hash": ctx["config_hash"],
               "versions": ctx["versions"]})
    ctx["context_hash"] = ch
    ctx["context_id"] = f"ctx_{ch[:12]}"
    CTX_DIR.mkdir(parents=True, exist_ok=True)
    p = CTX_DIR / f"{ctx['context_id']}.json"
    if not p.exists():  # 冻结: 不覆盖
        p.write_text(json.dumps(ctx, indent=1, ensure_ascii=False), encoding="utf-8")
    return ctx, p


def load_context(context_id):
    return _load(CTX_DIR / f"{context_id}.json")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    c, p = build_context()
    print("context_id:", c["context_id"], "a1_fresh", c["agent1"]["freshness"], "a2_fresh", c["agent2"]["freshness"])
    print("evidence_ids:", len(c["evidence_ids"]), "path:", p)
