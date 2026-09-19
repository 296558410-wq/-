# -*- coding: utf-8 -*-
"""V2 零-LLM 调度入口 —— 由 Windows Scheduled Task 直接运行（不依赖 OpenClaw Gateway / LLM / 会话）。

职责（本文件只做“调度 + 健康记录”，不下单、不改策略）：
  1) 显式置 V2_DATA_ROUTER_ENABLED=true（同时 config/data_router.enabled 兜底）
  2) 交易时段门（trading_hours.is_armed）：未 armed（休市）→ 跑 OBSERVE_ONLY（只刷 Agent1/Agent2 情报+新闻+事件，不决策/不执行/不下单），并记 skipped=MARKET_CLOSED
     [2026-09-19 变更：原为整轮直接 return（休市不写任何东西）；改为休市仍采集，使 Hermes 下个开盘周期能知道休市期间发生了什么]
  3) 直跑 shadow_run.py cycle（当前合法 15m 窗口；窗口内 dedup → 不重复执行）
  4) 写 state/v2_run_health.json（可审计运行健康指标）+ state/v2_scheduler_state.json（计数器）

设计约束（对齐任务书 §4/§5/§12）：
  - 无 Gateway / 无 LLM / 无 cron wrapper 依赖
  - StartWhenAvailable=False → 睡眠期间错过的触发 **不补跑**；唤醒后下个触发只跑“当前窗口”
  - MultipleInstances=IgnoreNew → 并发触发只跑一个；引擎窗口 dedup 兜底
退出码：0=正常(含 skip)；1=cycle 报错。
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]        # ...\trader_v2
AIQ = ROOT.parents[2]                              # C:\AIQuant
PY = str(AIQ / ".venv" / "Scripts" / "python.exe")
SHADOW = ROOT / "runtime" / "shadow_run.py"
STATE = ROOT / "state"
HEALTH = STATE / "v2_run_health.json"
SCHED = STATE / "v2_scheduler_state.json"
ACTIVE = STATE / "runs" / "ACTIVE.json"
CERT = STATE / "FORWARD_VALIDATION_ALLOWED"

def _forward_allowed():
    """认证门：未通过最终认证前，禁止启动任何新的"正式 forward run"。
    env V2_FORWARD_VALIDATION_ALLOWED 优先；否则读 state/FORWARD_VALIDATION_ALLOWED 标记文件。
    缺失/不为真 → False（锁定）。此门只阻止"开新 run"，不影响已有 run 的状态。"""
    v = str(os.environ.get("V2_FORWARD_VALIDATION_ALLOWED", "")).strip().lower()
    if v:
        return v in ("1", "true", "yes", "on")
    try:
        return CERT.read_text(encoding="utf-8").strip().lower() in ("1", "true", "yes", "on")
    except Exception:  # noqa: BLE001
        return False


def _now():
    return datetime.now(timezone.utc)


def _iso(dt=None):
    return (dt or _now()).astimezone(timezone.utc).isoformat()


def _win15(dt=None):
    dt = dt or _now()
    return dt.replace(minute=(dt.minute // 15) * 15, second=0, microsecond=0)


def _load(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def _write(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, indent=1, ensure_ascii=False), encoding="utf-8")


def _router_enabled():
    try:
        sys.path.insert(0, str(ROOT))
        import data_sources as d
        return bool(d.router_enabled())
    except Exception:  # noqa: BLE001
        return None


def _gate():
    sys.path.insert(0, str(AIQ / "research" / "hermes"))
    import trading_hours as TH
    return TH.status()


OBSERVE_STATE = STATE / "v2_observe_only.json"
OBSERVE_LOG = STATE / "v2_observe_only.jsonl"


def _observe_only(window_dt):
    """休市只读观察轮（OBSERVE_ONLY）。

    目的：休市（armed=False）期间仍让 Agent1/Agent2 采集行情/新闻/宏观/事件，写入各自 state 快照 +
    Evidence Registry，使 Hermes 在下一开盘周期能"知道"休市期间发生了什么。
    硬约束：不决策、不执行、不下单、不写 ledger / run_state / 运行计数器（只写 agent 快照 + 本文件的观察记录）。
    """
    out = {"ts": _iso(), "window": window_dt.isoformat(), "mode": "OBSERVE_ONLY",
           "trading": "DISABLED(market_closed)", "agent1": None, "agent2": None,
           "news_refs": None, "trigger": None, "errors": []}
    cycle = window_dt.strftime("%Y-%m-%dT%H:%MZ")
    try:
        sys.path.insert(0, str(ROOT / "agents" / "technical"))
        import agent1 as A1
        snap1, _p1 = A1.build(cycle)
        out["agent1"] = {"ok": True, "generated_utc": snap1.get("generated_utc"),
                         "gold_spot": ((snap1.get("quotes") or {}).get("gold_spot") or {}).get("price")}
    except Exception as e:  # noqa: BLE001
        out["agent1"] = {"ok": False, "error": f"{type(e).__name__}:{e}"}
        out["errors"].append("agent1")
    try:
        sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
        import agent2 as A2
        snap2, _p2 = A2.build(cycle)
        out["agent2"] = {"ok": True, "snapshot_ts": snap2.get("snapshot_ts"),
                         "gold_macro_state": snap2.get("gold_macro_state")}
        out["news_refs"] = (snap2.get("evidence") or {}).get("n_refs")
    except Exception as e:  # noqa: BLE001
        out["agent2"] = {"ok": False, "error": f"{type(e).__name__}:{e}"}
        out["errors"].append("agent2")
    try:
        sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
        import event_trigger as ET
        trig = ET.evaluate()
        out["trigger"] = {"trigger": trig.get("trigger"), "severity": trig.get("severity"),
                          "reasons": (trig.get("reasons") or [])[:6]}
    except Exception as e:  # noqa: BLE001
        out["trigger"] = {"error": f"{type(e).__name__}:{e}"}
        out["errors"].append("event_trigger")
    try:
        _write(OBSERVE_STATE, out)
        with open(OBSERVE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass
    return out


def _run_status(run_id):
    """从 run_state + timeline 尾行派生 agent/hermes/ledger/replay 状态。"""
    out = {}
    if not run_id:
        return out
    rd = ROOT / "research" / "runs" / run_id
    st = _load(rd / "run_state.json", {}) or {}
    out["run_status"] = st.get("status")
    f = st.get("failures", {}) or {}
    out["agent1_status"] = "FAIL" if f.get("agent1") else "OK"
    out["agent2_status"] = "FAIL" if f.get("agent2") else "OK"
    out["hermes_status"] = "FAIL" if f.get("hermes") else "OK"
    out["ledger_status"] = "FAIL" if f.get("ledger") else "OK"
    out["blocked"] = st.get("blocked")
    tl = rd / "timeline.jsonl"
    if tl.exists():
        try:
            lines = tl.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                last = json.loads(lines[-1])
                out["last_timeline_window"] = last.get("decision_window")
                out["replay_status"] = "MATCH" if last.get("replay_match") else "MISMATCH"
                out["agent2_data_gaps"] = last.get("agent2_data_gaps")
                if last.get("agent2_error"):
                    out["last_agent2_error"] = last["agent2_error"]
        except Exception:  # noqa: BLE001
            pass
    out["execution_status"] = "BLOCKED" if st.get("blocked") else (
        "REJECTED" if (st.get("counters", {}) or {}).get("exec_rejected") else "OK")
    return out


def main():
    now = _now()
    sched = _load(SCHED, {}) or {}
    health = _load(HEALTH, {}) or {}
    health.update({
        "last_scheduled": _iso(now),
        "scheduler": "DIRECT_WINDOWS_TASK",
        "gateway_dependency": False,
        "llm_dependency": False,
        "router_enabled": _router_enabled(),
    })
    for _k in ("last_started", "last_completed", "last_success", "last_failure"):
        health.setdefault(_k, None)

    cur_win = _win15(now)
    # missed-window 记账（只在 armed 时段计；且只计“错过”，不补跑）
    last_win = sched.get("last_window")
    if last_win:
        try:
            prev = datetime.fromisoformat(last_win)
            gap = (cur_win - prev).total_seconds() / 60.0
            if gap > 15:
                missed = int(gap // 15) - 1
                if missed > 0:
                    sched["missed_cycles"] = sched.get("missed_cycles", 0) + missed
                    sched["recovery_count"] = sched.get("recovery_count", 0) + 1
                    health["last_recovery"] = {"ts": _iso(now), "missed_added": missed, "gap_min": round(gap, 1)}
        except Exception:  # noqa: BLE001
            pass
    sched["last_window"] = cur_win.isoformat()

    gate = _gate()
    health["market_open"] = gate.get("open")
    health["armed"] = gate.get("armed")
    health["current_cycle"] = cur_win.isoformat()

    if not gate.get("armed"):
        # 休市：不再整轮直接返回；跑 OBSERVE_ONLY（只采集情报/新闻，不决策/不执行/不下单）。
        # --dry-run 时不采集（保持 dry-run 零副作用）。
        _dry = "--dry-run" in sys.argv
        obs = None if _dry else _observe_only(cur_win)
        if obs is not None:
            health["observe_only"] = obs
        health["last_completed"] = _iso(now)
        health["cycle_result"] = "MARKET_CLOSED_SKIP"
        health["missed_cycles"] = sched.get("missed_cycles", 0)
        health["recovery_count"] = sched.get("recovery_count", 0)
        health["duplicate_prevented"] = sched.get("duplicate_prevented", 0)
        _write(HEALTH, health); _write(SCHED, sched)
        print(json.dumps({"skipped": "MARKET_CLOSED", "observe_only": obs is not None, "dry_run": _dry,
                          "agent1": (obs or {}).get("agent1", {}).get("ok") if obs else None,
                          "agent2": (obs or {}).get("agent2", {}).get("ok") if obs else None,
                          "errors": (obs or {}).get("errors"), "window": cur_win.isoformat()}, ensure_ascii=False))
        return 0

    # 认证门：未通过最终认证前，禁止启动新的正式 forward run（防止在不修好的代码上产生样本）。
    act = _load(ACTIVE, {}) or {}
    act_live = act.get("run_id") and not act.get("stopped") and (ROOT / "research" / "runs" / act["run_id"]).exists()
    if (not act_live) and (not _forward_allowed()):
        health["last_completed"] = _iso(now)
        health["cycle_result"] = "FORWARD_LOCKED(not_certified)"
        health["forward_validation_allowed"] = False
        health["missed_cycles"] = sched.get("missed_cycles", 0)
        health["recovery_count"] = sched.get("recovery_count", 0)
        health["duplicate_prevented"] = sched.get("duplicate_prevented", 0)
        _write(HEALTH, health); _write(SCHED, sched)
        print(json.dumps({"skipped": "FORWARD_LOCKED", "reason": "not_certified", "window": cur_win.isoformat()}))
        return 0

    health["last_started"] = _iso(now)
    if "--dry-run" in sys.argv:
        health["cycle_result"] = "DRY_RUN (would run: shadow_run.py cycle --minutes 1440 --new)"
        health["last_completed"] = _iso(now)
        health["last_success"] = _iso(now)
        health["missed_cycles"] = sched.get("missed_cycles", 0)
        health["recovery_count"] = sched.get("recovery_count", 0)
        health["duplicate_prevented"] = sched.get("duplicate_prevented", 0)
        rid = (_load(ACTIVE, {}) or {}).get("run_id")
        health.update(_run_status(rid))
        _write(HEALTH, health); _write(SCHED, sched)
        print(json.dumps({"dry_run": True, "armed": True, "window": cur_win.isoformat()}))
        return 0
    t0 = time.time()
    try:
        p = subprocess.run([PY, str(SHADOW), "cycle", "--minutes", "1440", "--new"],
                           cwd=str(AIQ), capture_output=True, text=True, encoding="utf-8", timeout=600)
        rc, out, err = p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except subprocess.TimeoutExpired:
        rc, out, err = 999, "", "TIMEOUT_600s"
    res = {}
    if out:
        try:
            res = json.loads(out.splitlines()[-1])
        except Exception:  # noqa: BLE001
            res = {"raw": out[-400:]}
    health["last_completed"] = _iso()
    health["cycle_seconds"] = round(time.time() - t0, 1)
    health["cycle_result"] = res
    health["run_id"] = res.get("run_id")
    if rc == 0 and not res.get("blocked"):
        health["last_success"] = _iso()
    else:
        health["last_failure"] = {"ts": _iso(), "returncode": rc, "stderr": err[-400:], "result": res}

    # 计数器
    if res.get("skipped_duplicate"):
        sched["duplicate_prevented"] = sched.get("duplicate_prevented", 0) + 1
    sched["cycles_attempted"] = sched.get("cycles_attempted", 0) + 1
    if res.get("decision") == "WAIT":
        sched["wait"] = sched.get("wait", 0) + 1
    elif res.get("decision") == "TRADE":
        sched["trade"] = sched.get("trade", 0) + 1
    elif res.get("decision") == "REJECT":
        sched["reject"] = sched.get("reject", 0) + 1
    health["missed_cycles"] = sched.get("missed_cycles", 0)
    health["recovery_count"] = sched.get("recovery_count", 0)
    health["duplicate_prevented"] = sched.get("duplicate_prevented", 0)
    health["counters"] = {k: sched.get(k, 0) for k in ("cycles_attempted", "wait", "trade", "reject",
                                                       "missed_cycles", "recovery_count", "duplicate_prevented")}
    # 运行态状态
    rid = res.get("run_id") or (_load(ACTIVE, {}) or {}).get("run_id")
    health.update(_run_status(rid))
    # G3 Shadow Guardian（只读守护；逐 cycle 校验 + 4h 快照 + 24h/48h 评估；不发单）
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import shadow_guardian as SG
        _g = SG.auto()
        if _g.get("run_id"):
            health["shadow_guardian"] = {k: _g.get(k) for k in ("cycles", "snapshots", "snapshot_ok", "replay_mismatch")}
            _write(HEALTH, health)
    except Exception:  # noqa: BLE001
        pass
    _write(HEALTH, health); _write(SCHED, sched)
    print(json.dumps(res, ensure_ascii=False))
    return 0 if (rc == 0 and not res.get("blocked")) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
