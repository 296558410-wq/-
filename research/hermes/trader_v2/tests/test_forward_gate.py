# -*- coding: utf-8 -*-
"""V2 回归 — P1-G Forward Gate 硬化（所有入口不可绕过）。

断言:
- forward_allowed() 默认 False（无认证文件）
- start_run() 未认证 → 拒绝（不创建 run / 不改 ACTIVE）
- ensure_run(allow_new=True) 未认证 → (None, False)
- scheduler 与 shadow_run 门一致
- env 显式覆盖可授权（唯一合法入口）
日志: logs/test_forward_gate.log
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "runtime"))
sys.path.insert(0, str(ROOT / "hermes"))
sys.path.insert(0, str(ROOT / "execution"))
sys.path.insert(0, str(ROOT / "ledger"))
sys.path.insert(0, str(ROOT / "agents" / "technical"))
sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
import shadow_run as SR  # noqa: E402
import v2_scheduled_cycle as SCH  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_forward_gate.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    prev = os.environ.pop("V2_FORWARD_VALIDATION_ALLOWED", None)
    active_before = SR.ACTIVE.read_text(encoding="utf-8") if SR.ACTIVE.exists() else None
    try:
        check("default locked", SR.forward_allowed() is False)
        check("scheduler gate agrees", SCH._forward_allowed() is False)

        # start_run must refuse without creating a run
        raised = False
        try:
            SR.start_run(1)
        except RuntimeError as e:
            raised = "not certified" in str(e) or "REFUSE" in str(e)
        check("start_run refuses when locked", raised)
        active_after = SR.ACTIVE.read_text(encoding="utf-8") if SR.ACTIVE.exists() else None
        check("no run created / ACTIVE unchanged", active_before == active_after)

        rid, started = SR.ensure_run(allow_new=True)
        _live = (SR._load(SR.ACTIVE, {}) or {}).get("run_id")
        check("ensure_run(allow_new) does not create a NEW run when locked", started is False, f"{rid},{started}")
        check("returns existing live run (or None) — never a new run", rid in (None, _live), f"rid={rid} live={_live}")

        # explicit env authorization works
        os.environ["V2_FORWARD_VALIDATION_ALLOWED"] = "true"
        check("env explicit -> allowed", SR.forward_allowed() is True)
        check("scheduler gate agrees (env)", SCH._forward_allowed() is True)
    finally:
        os.environ.pop("V2_FORWARD_VALIDATION_ALLOWED", None)
        if prev is not None:
            os.environ["V2_FORWARD_VALIDATION_ALLOWED"] = prev

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
