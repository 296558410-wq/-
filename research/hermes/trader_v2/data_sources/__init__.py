# -*- coding: utf-8 -*-
"""V2 Data Source Router — 包入口（P0-02: V2 唯一数据入口）。

**唯一开关**: `config/data_router.enabled`（标记文件）；env `V2_DATA_ROUTER_ENABLED` 仅作**显式**覆盖，
scheduler **不再隐式 setdefault**（P0-02 已移除 hidden override）。
- enabled=true（生产）→ Agent1/Agent2 全部经 Router（source/priority/fallback/freshness/PIT/audit）。
- enabled=false → 仅开发/离线；生产禁止（不得让 Agent 自行绕 Router 另择源）。
"""
from __future__ import annotations
import os
from pathlib import Path

from . import net, cache, health, audit, registry, validate, local_bars  # noqa: F401

_R = None

# FIX(2026-09-15): 用户级环境变量在“已运行的 gateway 进程派生的子进程”中不会继承
# （实测：OpenClaw exec/cron 子进程读不到新设的 V2_DATA_ROUTER_ENABLED）→ 开关会失效。
# 因此加一个 V2 本地标记文件作为等价开关；env 显式设置时仍以 env 为准。
_FLAG_FILE = Path(__file__).resolve().parents[1] / "config" / "data_router.enabled"
_TRUTHY = ("1", "true", "yes", "on")


def router_enabled() -> bool:
    env = str(os.environ.get("V2_DATA_ROUTER_ENABLED", "")).strip().lower()
    if env:
        return env in _TRUTHY
    try:
        return _FLAG_FILE.read_text(encoding="utf-8").strip().lower() in _TRUTHY
    except Exception:  # noqa: BLE001
        return False


ROUTER_ENABLED = router_enabled()   # 导入时快照（仅供展示）


def _router():
    global _R
    if _R is None:
        from .router import Router
        _R = Router()
    return _R


def history(symbol, tf):
    return _router().history(tf, symbol)


def quote(key):
    return _router().quote(key)


def macro(name):
    return _router().macro(name)


def health_report():
    return _router().health_report()


def audit_tail(n=50):
    return audit.tail(n)


def last_selected():
    """P0-01/P0-02: 最近一次各 key 选中的 source（供诚实标注/审计）。"""
    return _router().last


def cooldowns():
    return net.cooldowns()
