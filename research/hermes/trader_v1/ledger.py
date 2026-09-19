# -*- coding: utf-8 -*-
"""ledger.py — Hermes Trade Plan 不可篡改注册表(append-only + sha256 链) + 幂等层。

纪律(TRADE_PLAN_CONTRACT): Trigger 之前必须注册; 禁止看到结果后补计划。
计划不可修改; 状态迁移(registered→triggered→filled/rejected/cancelled→closed)以事件追加。

幂等(L0 修复 H1/H2):
- register_plan(): 同 decision_id 只注册一次(查重 registered 事件)
- transition(): 计划状态机原子转移; 非法/重复转移返回 False 不追加
- 计划状态机: registered → triggered → (filled | rejected | cancelled) → closed
  状态推导 = 该 plan_id 事件序列的末态; 已 terminated 的计划不再参与触发评估
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER_P = HERE / "run_state" / "plan_ledger.jsonl"

# 计划状态机: filled=持仓态(可→closed); 终态 = rejected/cancelled/closed
TERMINAL = {"rejected", "cancelled", "closed"}
# 事件类型 → 允许的后继事件
EVENT_ORDER = ["registered", "triggered", "filled", "rejected", "cancelled", "closed"]
PLAN_FLOW = {
    "registered": {"triggered", "cancelled"},
    "triggered": {"filled", "rejected", "cancelled"},
    "filled": {"closed"},
    "rejected": set(), "cancelled": set(), "closed": set(),
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def head():
    """返回链头 hash 与长度(integrity 报告用)。"""
    if not LEDGER_P.exists():
        return {"hash": None, "len": 0}
    lines = [l for l in LEDGER_P.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return {"hash": None, "len": 0}
    return {"hash": json.loads(lines[-1])["sha256"], "len": len(lines)}


def append(event: dict) -> dict:
    """追加事件(内部原语)。调用方负责业务幂等; 本函数只保证链完整性。"""
    LEDGER_P.parent.mkdir(parents=True, exist_ok=True)
    prev = head()
    body = {k: v for k, v in event.items() if k != "sha256"}
    body["utc_ts"] = body.get("utc_ts", _now())
    blob = json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    h = hashlib.sha256(blob + (prev["hash"] or "").encode("utf-8")).hexdigest()
    body["sha256"] = h
    with open(LEDGER_P, "a", encoding="utf-8") as f:
        f.write(json.dumps(body, ensure_ascii=False) + "\n")
    return body


def verify() -> bool:
    """全链校验(供审计/不变量)。"""
    if not LEDGER_P.exists():
        return True
    prev = None
    for ln in LEDGER_P.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        e = json.loads(ln)
        blob = json.dumps({k: v for k, v in e.items() if k != "sha256"},
                          sort_keys=True, ensure_ascii=False).encode("utf-8")
        want = hashlib.sha256(blob + (prev or "").encode("utf-8")).hexdigest()
        if e["sha256"] != want:
            return False
        prev = e["sha256"]
    return True


def all_events():
    if not LEDGER_P.exists():
        return []
    out = []
    for ln in LEDGER_P.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            out.append(json.loads(ln))
    return out


def plans(filter_type=None):
    """全部事件(时间序); 兼容旧调用 plans(filter_type)。"""
    evs = all_events()
    if filter_type:
        evs = [e for e in evs if e.get("type") == filter_type]
    return evs


def plan_events(plan_id):
    """某 plan_id 的全部事件(时间序)。"""
    return [e for e in all_events() if e.get("plan_id") == plan_id]


def plan_state(plan_id):
    """推导 plan 当前状态: 返回 {state, last_event}。
    state ∈ registered/triggered/filled/rejected/cancelled/closed/unknown
    推导规则: 取事件序中最后一个非中间态事件; 若无 → unknown。"""
    evs = plan_events(plan_id)
    if not evs:
        return {"state": "unknown", "last_event": None}
    # 事件类型即状态迁移标签; 末态 = 最后一个事件类型(终态后不再更新)
    return {"state": evs[-1].get("type"), "last_event": evs[-1]}


def register_plan(plan_id, decision_id, decision, plan, validation=None):
    """幂等注册(L0-H1): 同 decision_id 已注册 → 返回 (None, False, 'dup_decision')。
    返回 (event, ok, reason)。"""
    # 查重: 该 decision_id 是否已有 registered
    for e in all_events():
        if e.get("type") == "registered" and e.get("decision_id") == decision_id:
            return None, False, f"dup_decision:{decision_id}"
    # 查重: plan_id 已存在(重试)
    if plan_state(plan_id)["state"] != "unknown":
        return None, False, f"dup_plan:{plan_id}"
    ev = append({"type": "registered", "plan_id": plan_id, "decision_id": decision_id,
                 "decision": decision, "plan": plan, "validation": validation or {}})
    return ev, True, "ok"


def transition(plan_id, event_type, **payload):
    """计划状态机原子转移(L0-H2): 非法/重复转移返回 (None, False, reason)。
    例如 triggered 已存在 → 再次 triggered 拒绝(防 H2 重复触发)。"""
    st = plan_state(plan_id)["state"]
    if st == "unknown":
        # 允许 registered 直接前置补入场景: 不允许; 必须先 registered
        return None, False, f"unknown_state:{plan_id}:{event_type}"
    allowed = PLAN_FLOW.get(st, set())
    if event_type not in allowed:
        return None, False, f"illegal_transition:{st}->{event_type}"
    if event_type in TERMINAL:
        # 终态唯一性: 该 plan 已 terminated
        for e in plan_events(plan_id):
            if e.get("type") in TERMINAL:
                return None, False, f"already_terminated:{plan_id}:{e.get('type')}"
    ev = append({"type": event_type, "plan_id": plan_id, **payload})
    return ev, True, "ok"


def terminated(plan_id):
    return plan_state(plan_id)["state"] in TERMINAL


def active_plans():
    """尚未 terminated 的计划(registered/triggered 态; filled 表示已持仓由 position 层管理)。"""
    out = []
    for e in all_events():
        if e.get("type") != "registered":
            continue
        pid = e.get("plan_id")
        st = plan_state(pid)["state"]
        if st in ("registered", "triggered"):
            out.append(e)
    return out


if __name__ == "__main__":
    print("ledger head:", head())
    print("verify:", verify())
    print("n events:", len(all_events()))
