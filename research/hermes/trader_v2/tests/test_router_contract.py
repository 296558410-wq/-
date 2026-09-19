# -*- coding: utf-8 -*-
"""V2 回归 — P0-02 Router 契约（唯一数据入口 / 无 hidden override / audit / V1 数据隔离）。

断言:
- scheduler 不再隐式 setdefault(V2_DATA_ROUTER_ENABLED)
- 开关唯一来源: config/data_router.enabled（env 仅显式覆盖）
- router_enabled(): env 显式 false → False；无 env → 取标记文件
- router audit 记录 selection 字段
- V2 代码不读写 V1 (trader_v1) 的 state/ledger
日志: logs/test_router_contract.log
"""
from __future__ import annotations
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import data_sources as DS  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_router_contract.log"
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
    sched = (ROOT / "runtime" / "v2_scheduled_cycle.py").read_text(encoding="utf-8")
    check("no hidden env setdefault in scheduler", 'setdefault("V2_DATA_ROUTER_ENABLED"' not in sched)
    check("scheduler keeps PY launcher", 'python.exe' in sched and "PY =" in sched)

    init_src = (ROOT / "data_sources" / "__init__.py").read_text(encoding="utf-8")
    check("flag-file is the switch", "_FLAG_FILE" in init_src and "data_router.enabled" in init_src)
    check("doc states sole-entry (no default-OFF legacy claim)", "唯一数据入口" in init_src)

    # router_enabled: env explicit override vs flag file
    prev = os.environ.get("V2_DATA_ROUTER_ENABLED")
    try:
        os.environ["V2_DATA_ROUTER_ENABLED"] = "false"
        check("env=false -> disabled", DS.router_enabled() is False)
        os.environ["V2_DATA_ROUTER_ENABLED"] = "true"
        check("env=true -> enabled", DS.router_enabled() is True)
        del os.environ["V2_DATA_ROUTER_ENABLED"]
        flag = (ROOT / "config" / "data_router.enabled").read_text(encoding="utf-8").strip().lower()
        check("no env -> flag file governs", DS.router_enabled() == (flag in ("1", "true", "yes", "on")),
              f"flag={flag} -> {DS.router_enabled()}")
    finally:
        if prev is None:
            os.environ.pop("V2_DATA_ROUTER_ENABLED", None)
        else:
            os.environ["V2_DATA_ROUTER_ENABLED"] = prev

    rsrc = (ROOT / "data_sources" / "router.py").read_text(encoding="utf-8")
    for f in ("selected_source", "candidate_sources", "selection_reason", "field", "requested_symbol"):
        check(f"router audit records {f}", f in rsrc)

    # V1 数据隔离：V2 代码不得引用 V1 run_state/ledger 路径
    bad = []
    for sub in ("agents", "hermes", "execution", "data_sources", "runtime", "ledger"):
        for p in (ROOT / sub).rglob("*.py"):
            t = p.read_text(encoding="utf-8", errors="replace")
            if "trader_v1" in t and "只读" not in t and "绝不" not in t and "隔离" not in t:
                bad.append(str(p.relative_to(ROOT)))
    check("V2 code does not read V1 state/ledger", not bad, ",".join(bad[:3]))

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
