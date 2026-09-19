# -*- coding: utf-8 -*-
"""只读读取 V2 关联的 FXTM Demo 账户 ("******", 独立实例 fxtm_demo_01)。
仅 account_info + positions_get；绝不下单/改单。供 dashboard 以子进程方式调用。"""
import json, sys
try:
    import MetaTrader5 as mt5
except Exception as e:  # noqa: BLE001
    print(json.dumps({"ok": False, "error": f"mt5_import:{e}"}, ensure_ascii=False)); sys.exit(0)

PATH = r"C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe"
ok = mt5.initialize(path=PATH, portable=True)
a = mt5.account_info()
if not a:
    print(json.dumps({"ok": False, "error": str(mt5.last_error())}, ensure_ascii=False)); sys.exit(0)
poss = mt5.positions_get() or []
out = {"ok": True, "login": a.login, "server": a.server, "trade_mode": a.trade_mode,
       "demo": a.trade_mode == 0, "balance": a.balance, "equity": a.equity,
       "margin": a.margin, "margin_free": a.margin_free, "leverage": a.leverage,
       "currency": a.currency, "positions": len(poss),
       "positions_detail": [{"ticket": int(p.ticket), "symbol": p.symbol,
                             "side": "LONG" if p.type == 0 else "SHORT", "volume": float(p.volume),
                             "entry": float(p.price_open), "current": float(p.price_current),
                             "sl": float(p.sl), "tp": float(p.tp), "profit": float(p.profit),
                             "magic": int(p.magic), "opened": int(p.time)} for p in poss]}
print(json.dumps(out, ensure_ascii=False))
mt5.shutdown()
