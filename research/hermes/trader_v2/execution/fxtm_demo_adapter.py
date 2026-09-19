# -*- coding: utf-8 -*-
"""V2 FXTM Demo 适配器 —— 真实连接（钉定独立实例 "******" / fxtm_demo_01）。

安全约束(硬):
- 默认 DISABLED: execution.execution_mode=="BROKER_DEMO" **且** broker_demo_enabled==true 才允许连接/下单。
- **只允许** 连接测试实例 `C:\\AIQuant\\mt5_instances\\fxtm_demo_01\\terminal64.exe`（data_path 必须含 fxtm_demo_01），
  **绝不允许**连 V1 主终端（%ProgramFiles%\\ForexTime (FXTM) MT5）。
- 账户必须 DEMO 且 server==ForexTimeFXTM-Demo01；下单走独立 magic=90003（V1 用 90002），便于隔离。
- 凭据不落盘：本实例以 /portable 免密连接（终端已登录）；如需显式登录只走环境变量 FXTM_DEMO_*。
"""
from __future__ import annotations
import os
from pathlib import Path
import json
from datetime import datetime, timezone

from broker_interface import BrokerInterface, RefuseConnection

ROOT = Path(__file__).resolve().parents[1]
TEST_EXE = r"C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe"
REQUIRED_TERMINAL_TAG = "fxtm_demo_01"
REQUIRED_SERVER = "ForexTimeFXTM-Demo01"
SYMBOL = "XAUUSD"
MAGIC = 90003
ENV_KEYS = {"login": "FXTM_DEMO_LOGIN", "password": "FXTM_DEMO_PASSWORD",
            "investor": "FXTM_DEMO_INVESTOR", "server": "FXTM_DEMO_SERVER"}


def _load_cfg():
    try:
        return json.loads((ROOT / "config" / "v2_config.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _mask(s):
    s = str(s or "")
    return (s[:2] + "*" * max(0, len(s) - 4) + s[-2:]) if len(s) > 4 else "***"


class FXTMDemoAdapter(BrokerInterface):
    backend = "fxtm_demo"

    def __init__(self, config=None):
        cfg = config or _load_cfg()
        ex = (cfg.get("execution") or {})
        br = (cfg.get("broker") or {})
        self.execution_mode = ex.get("execution_mode", "PAPER")
        self.broker_demo_enabled = bool(br.get("enabled", False) and ex.get("broker_demo_enabled", False))
        self.environment = br.get("environment", "DEMO")
        self._mt5 = None
        self._account = None

    # ---------- 安全门 ----------
    def _gate(self):
        if not (self.execution_mode == "BROKER_DEMO" and self.broker_demo_enabled):
            raise RefuseConnection(
                f"refuse_connection: execution_mode={self.execution_mode} broker_demo_enabled={self.broker_demo_enabled}")

    def _attach(self):
        import MetaTrader5 as mt5
        self._mt5 = mt5
        ok = mt5.initialize(path=TEST_EXE, portable=True, timeout=60000)
        ti = mt5.terminal_info()
        if not ok or ti is None:
            raise RefuseConnection(f"attach_failed:{mt5.last_error()}")
        if REQUIRED_TERMINAL_TAG not in (ti.data_path or ""):
            mt5.shutdown(); self._mt5 = None
            raise RefuseConnection(f"wrong_terminal(refuse; not {REQUIRED_TERMINAL_TAG}):{ti.data_path}")
        ai = mt5.account_info()
        if ai is None:
            mt5.shutdown(); self._mt5 = None
            raise RefuseConnection("no_account")
        if ai.trade_mode != 0:
            mt5.shutdown(); self._mt5 = None
            raise RefuseConnection(f"not_demo:trade_mode={ai.trade_mode}")
        if ai.server != REQUIRED_SERVER:
            mt5.shutdown(); self._mt5 = None
            raise RefuseConnection(f"wrong_server:{ai.server}")
        mt5.symbol_select(SYMBOL, True)
        self._account = ai
        return {"ok": True, "login": ai.login, "server": ai.server, "demo": True}

    def connect(self):
        self._gate()
        return self._attach()

    def connect_readonly(self):
        """P0-06(2026-09-18): 行情只读 attach —— 跳过 execution 武装门（PAPER 下仍可读 MT5），
        但保留 终端/账户/服务器 隔离校验。**绝不发单**（下单方法仍各自 _gate）。"""
        if self._mt5 is not None:
            return {"ok": True, "cached": True}
        return self._attach()

    def disconnect(self):
        if self._mt5:
            try:
                self._mt5.shutdown()
            except Exception:  # noqa: BLE001
                pass
        self._mt5 = None

    # ---------- 只读 ----------
    def get_account(self):
        self._gate()
        if self._mt5 is None:
            self.connect()
        ai = self._mt5.account_info()
        return {"ok": True, "login": ai.login, "server": ai.server, "demo": ai.trade_mode == 0,
                "balance": ai.balance, "equity": ai.equity, "margin": ai.margin,
                "margin_free": ai.margin_free, "leverage": ai.leverage, "currency": ai.currency}

    def get_balance(self):
        return self.get_account()["balance"]

    def get_equity(self):
        return self.get_account()["equity"]

    def get_positions(self):
        self._gate()
        if self._mt5 is None:
            self.connect()
        poss = self._mt5.positions_get(symbol=SYMBOL) or []
        return {"ok": True, "positions": [
            {"ticket": p.ticket, "side": "LONG" if p.type == 0 else "SHORT", "qty": p.volume,
             "open_price": p.price_open, "sl": p.sl, "tp": p.tp, "profit": p.profit,
             "magic": p.magic} for p in poss if p.magic == MAGIC]}

    def get_quote(self, symbol=SYMBOL):
        self._gate()
        if self._mt5 is None:
            self.connect()
        t = self._mt5.symbol_info_tick(symbol)
        return {"ok": bool(t), "bid": getattr(t, "bid", None), "ask": getattr(t, "ask", None)}

    def symbol_spec(self, symbol=SYMBOL):
        """P1-C: 实测 broker symbol 规格（只读；不发单）。"""
        self._gate()
        if self._mt5 is None:
            self.connect()
        m = self._mt5
        m.symbol_select(symbol, True)
        si = m.symbol_info(symbol)
        if si is None:
            return {"ok": False, "symbol": symbol, "retrieval_ts": datetime.now(timezone.utc).isoformat()}
        g = lambda n: getattr(si, n, None)  # noqa: E731
        return {"ok": True, "symbol": symbol, "digits": g("digits"), "point": g("point"),
                "tick_size": g("trade_tick_size"), "tick_value": g("trade_tick_value"),
                "contract_size": g("trade_contract_size"), "volume_min": g("volume_min"),
                "volume_step": g("volume_step"), "volume_max": g("volume_max"),
                "stops_level": g("trade_stops_level"), "freeze_level": g("trade_freeze_level"),
                "filling_mode": g("filling_mode"), "execution_mode": g("trade_exemode"),
                "trade_mode": g("trade_mode"), "retrieval_ts": datetime.now(timezone.utc).isoformat()}

    # ---------- 下单（受门禁保护; 引擎未接线前不会被调用） ----------
    def place_market_order(self, symbol, side, qty_lots, sl=None, tp=None):
        self._gate()
        if self._mt5 is None:
            self.connect()
        m = self._mt5
        m.symbol_select(symbol, True)
        t = m.symbol_info_tick(symbol)
        if t is None:
            raise RefuseConnection("no_tick")
        is_buy = side.upper() in ("LONG", "BUY")
        req = {"action": m.TRADE_ACTION_DEAL, "symbol": symbol, "volume": float(qty_lots),
               "type": m.ORDER_TYPE_BUY if is_buy else m.ORDER_TYPE_SELL,
               "price": t.ask if is_buy else t.bid, "deviation": 30, "magic": MAGIC,
               "comment": "v2-exec", "type_time": m.ORDER_TIME_GTC, "type_filling": m.ORDER_FILLING_FOK}
        if sl:
            req["sl"] = float(sl)
        if tp:
            req["tp"] = float(tp)
        res = m.order_send(req)
        return {"ok": bool(res and res.retcode == m.TRADE_RETCODE_DONE),
                "retcode": getattr(res, "retcode", None), "comment": getattr(res, "comment", None),
                "order": getattr(res, "order", None), "deal": getattr(res, "deal", None),
                "price": getattr(res, "price", None), "volume": getattr(res, "volume", None)}

    def close_position(self, position_id, qty_lots=None):
        self._gate()
        if self._mt5 is None:
            self.connect()
        m = self._mt5
        poss = m.positions_get(ticket=int(position_id)) or []
        if not poss:
            raise RefuseConnection(f"position_not_found:{position_id}")
        p = poss[0]
        t = m.symbol_info_tick(p.symbol)
        req = {"action": m.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": float(qty_lots or p.volume),
               "type": m.ORDER_TYPE_SELL if p.type == 0 else m.ORDER_TYPE_BUY,
               "position": p.ticket, "price": t.bid if p.type == 0 else t.ask, "deviation": 30,
               "magic": MAGIC, "comment": "v2-close", "type_time": m.ORDER_TIME_GTC,
               "type_filling": m.ORDER_FILLING_FOK}
        res = m.order_send(req)
        return {"ok": bool(res and res.retcode == m.TRADE_RETCODE_DONE),
                "retcode": getattr(res, "retcode", None), "comment": getattr(res, "comment", None),
                "price": getattr(res, "price", None)}

    # ---------- 成交明细（只读） ----------
    def deals_for_position(self, position_id):
        """按持仓 ticket 取 broker deal 明细（entry=0 开 / entry=1 平），用于成本/PnL 对账。"""
        self._gate()
        if self._mt5 is None:
            self.connect()
        dl = self._mt5.history_deals_get(position=int(position_id)) or []
        return [{"ticket": d.ticket, "order": d.order, "position_id": d.position_id, "entry": d.entry,
                 "type": d.type, "price": d.price, "volume": d.volume, "profit": d.profit,
                 "commission": d.commission, "swap": d.swap, "magic": d.magic,
                 "time": d.time} for d in dl]

    def get_order_status(self, order_id):
        self._gate()
        if self._mt5 is None:
            self.connect()
        o = self._mt5.history_orders_get(ticket=int(order_id)) or []
        return {"ok": bool(o)}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    a = FXTMDemoAdapter()
    print("backend:", a.backend, "mode:", a.execution_mode, "enabled:", a.broker_demo_enabled,
          "(default config: 应当 REFUSE)")
    for fn in ("connect", "get_account", "get_positions"):
        try:
            print(fn, "->", getattr(a, fn)())
        except RefuseConnection as e:
            print(fn, "-> refused:", e)
