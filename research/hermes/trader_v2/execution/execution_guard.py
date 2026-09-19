# -*- coding: utf-8 -*-
"""REPAIR-007 STAGE-1/2：执行幂等 + 状态机（执行基础设施；不触碰交易逻辑/PIT/策略）。

IDEMPOTENCY_KEY = decision_id（**非** symbol+timestamp）。

机制：
- claim(decision_id): O_CREAT|O_EXCL 原子占位 → CLAIMED / ALREADY_CLAIMED（跨线程/进程/重启/重入）
- 状态机（单向 + 合法迁移校验）：REQUESTED→EXECUTING→FILLED；分支 REJECTED/FAILED；EXECUTING→UNKNOWN→RECONCILIATION→{FILLED,REJECTED,FAILED}
- UNKNOWN 禁自动重试：can_execute() 在已 claim 后一律 False
- ledger_append_once(): 以 decision_id 为唯一键，marker(O_EXCL) 保证只写一次 FILLED 记录
- 所有写用原子写（runtime/atomic_io.write_atomic）
"""
from __future__ import annotations
import os, json, time
from pathlib import Path

try:
    from atomic_io import write_atomic  # 同 runtime 目录
except Exception:  # noqa: BLE001
    import json as _j
    def write_atomic(p, obj):
        p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + f".tmp.{os.getpid()}")
        tmp.write_text(_j.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, p); return p

_FSM = {
    "REQUESTED": {"EXECUTING", "REJECTED", "FAILED"},
    "EXECUTING": {"FILLED", "FAILED", "UNKNOWN"},
    "UNKNOWN": {"RECONCILIATION"},
    "RECONCILIATION": {"FILLED", "REJECTED", "FAILED"},
    "FILLED": set(), "REJECTED": set(), "FAILED": set(),
}


class ExecutionGuard:
    def __init__(self, base_dir):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _claim_path(self, did): return self.base / f"{did}.claim"
    def _state_path(self, did): return self.base / f"{did}.state.json"

    def claim(self, decision_id):
        """原子占位。返回 (ok: bool, status: str)。ok=False → 已有 claim（含跨进程/重启/重入）。"""
        try:
            fd = os.open(str(self._claim_path(decision_id)), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, json.dumps({"decision_id": decision_id, "claimed_at": time.time(), "pid": os.getpid()}).encode())
            os.close(fd)
        except FileExistsError:
            return False, "ALREADY_CLAIMED"
        self._set_state(decision_id, {"decision_id": decision_id, "status": "REQUESTED",
                                      "history": [{"status": "REQUESTED", "ts": time.time()}], "result": None})
        return True, "CLAIMED"

    def _read_state(self, did):
        p = self._state_path(did)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def _set_state(self, did, st):
        write_atomic(self._state_path(did), st)

    def transition(self, decision_id, new_status, result=None):
        """单向 + 合法迁移校验；非法迁移 → 拒绝（返回 False）。"""
        st = self._read_state(decision_id)
        if st is None:
            return False
        cur = st["status"]
        if new_status not in _FSM.get(cur, set()):
            return False  # 非法迁移（含 UNKNOWN→RETRY 类）
        st["status"] = new_status
        st["history"].append({"status": new_status, "ts": time.time()})
        if result is not None:
            st["result"] = result
        self._set_state(decision_id, st)
        return True

    def can_execute(self, decision_id):
        """已 claim 后一律不可再执行（防重启/重入自动重试；UNKNOWN 尤其禁止）。"""
        return not self._claim_path(decision_id).exists()

    def ledger_append_once(self, ledger_path, decision_id, event):
        """以 decision_id 为唯一键，仅追加一次（marker O_EXCL），返回是否实际写入。"""
        ledger_path = Path(ledger_path)
        marker = self.base / f"{decision_id}.ledger.committed"
        try:
            fd = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileExistsError:
            return False
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"decision_id": decision_id, **event}, ensure_ascii=False) + "\n")
        return True
