# -*- coding: utf-8 -*-
"""V3 独立 MT5 适配器 — 只读研究连接；order_send 在代码层硬性拦截。

隔离约束：
- 只连 V3 实例 `C:\\AIQuant\\mt5_instances\\fxtm_demo_v3\\terminal64.exe`（/portable），**绝不**连 V1/V2。
- data_path 必须含 `fxtm_demo_v3`，否则拒绝。
- Magic=90004（V1=90002 / V2=90003）。
- `order_send` 在任何情况下都 raise（不依赖配置；配置仅二次确认）。三个安全闸门必须全为 NO。
"""
from __future__ import annotations
import json
import os
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[1]
EXE = r"C:\AIQuant\mt5_instances\fxtm_demo_v3\terminal64.exe"
DATA_DIR = r"C:\AIQuant\mt5_instances\fxtm_demo_v3"
REQUIRED_TAG = "fxtm_demo_v3"
SYMBOL = "XAUUSD"
MAGIC = 90004
SERVER_EXPECTED = "ForexTimeFXTM-Demo01"
STATE = V3_ROOT / "state"
ENV_FILE = Path(r"C:\AIQuant\.env.mt5_demo")
SAFETY_FILES = {"V3_LIVE_ALLOWED": "NO", "V3_ORDER_SEND_ALLOWED": "NO", "V3_FORWARD_ALLOWED": "NO"}


class OrderSendBlocked(RuntimeError):
    """V3 代码层硬拦截：任何 order_send 调用直接失败。"""


class RefuseConnection(RuntimeError):
    pass


def safety_flags():
    out = {}
    for k, default in SAFETY_FILES.items():
        p = STATE / k
        try:
            out[k] = p.read_text(encoding="utf-8").strip()
        except Exception:  # noqa: BLE001
            out[k] = default
    return out


def assert_readonly():
    f = safety_flags()
    bad = [k for k, v in f.items() if str(v).upper() != "NO"]
    if bad:
        raise OrderSendBlocked(f"V3 safety flags not NO: {bad}")


def _creds():
    kv = {}
    if ENV_FILE.exists():
        for ln in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            kv[k.strip()] = v.strip().strip('"').strip("'")
    return (int(kv.get("DEMO_MT5_LOGIN", 0) or 0), kv.get("DEMO_MT5_PASSWORD", ""), kv.get("DEMO_MT5_SERVER", SERVER_EXPECTED))


def _install_order_guard(mt5):
    """把 mt5.order_send 替换为 raise（硬拦截），与配置无关。"""
    def _blocked(*a, **k):
        raise OrderSendBlocked("V3: order_send is hard-blocked at code level (research read-only environment)")
    try:
        mt5.order_send = _blocked
    except Exception:  # noqa: BLE001
        pass
    # 同时拦截 order_check（会触发交易预检）
    def _blocked_check(*a, **k):
        raise OrderSendBlocked("V3: order_check is disabled")
    try:
        mt5.order_check = _blocked_check
    except Exception:  # noqa: BLE001
        pass
    return True


def order_send(*a, **k):
    """即使有人 import 本模块调用，也必然失败。"""
    raise OrderSendBlocked("V3: order_send is hard-blocked")


def connect(readonly=True):
    """连接 V3 独立实例。返回 (mt5, info)。"""
    assert_readonly()
    if not os.path.exists(EXE):
        raise RefuseConnection(f"V3 terminal not found: {EXE}")
    import MetaTrader5 as mt5
    login, pwd, server = _creds()
    ok = mt5.initialize(path=EXE, portable=True, login=login or None, password=pwd or None,
                        server=server or None, timeout=60000)
    if not ok:
        raise RefuseConnection(f"initialize failed: {mt5.last_error()}")
    ti = mt5.terminal_info()
    dp = (getattr(ti, "data_path", "") or "")
    if REQUIRED_TAG not in dp:
        mt5.shutdown()
        raise RefuseConnection(f"refused: data_path not V3 ({dp})")
    _install_order_guard(mt5)
    ai = mt5.account_info()
    info = {"data_path": dp, "path": getattr(ti, "path", None), "connected": getattr(ti, "connected", None),
            "login": getattr(ai, "login", None), "server": getattr(ai, "server", None),
            "trade_allowed": getattr(ai, "trade_allowed", None), "readonly": True,
            "magic": MAGIC, "symbol": SYMBOL}
    return mt5, info


def disconnect(mt5):
    try:
        mt5.shutdown()
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(safety_flags(), ensure_ascii=False))
    try:
        order_send()
    except OrderSendBlocked as e:
        print("order_send blocked OK:", e)
