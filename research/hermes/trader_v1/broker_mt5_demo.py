# -*- coding: utf-8 -*-
"""broker_mt5_demo.py — FXTM MT5 Demo 执行适配器(Demo Execution Validation 用)。

边界(硬):
- 仅接受 DEMO 凭据(.env.mt5_demo); 任何 real 账户尝试 → FAIL(不碰真实资金)
- FOK 填充(demo 不支持 IOC, 实测 2026-09-07); symbol_select 前置(否则 10030)
- magic 隔离: 本系统订单统一 magic=90002(与采集/测量 90001 分开)
- fail-closed: 未配置/连接失败/未知状态 → 返回错误, 绝不静默

接口: get_account / get_positions / market_order(side, qty) / close_position / get_trades
状态同步: 每次调用从 broker 拉真实持仓, 返回给 position 层对账(不变量 I6)。
"""
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
ENV_P = REPO / ".env.mt5_demo"
MAGIC = 90002
SYM = "XAUUSD"
FILLING_FOK = 2  # mt5.ORDER_FILLING_FOK


def _load_env():
    """读 demo 凭据(gitignored)。返回 dict 或 None。"""
    if not ENV_P.exists():
        return None
    out = {}
    for ln in ENV_P.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            out[k.strip()] = v.strip()
    if not out.get("DEMO_MT5_LOGIN") or not out.get("DEMO_MT5_PASSWORD"):
        return None
    return out


def _connect():
    env = _load_env()
    if not env:
        return None, "demo_env_missing(.env.mt5_demo)"
    import MetaTrader5 as mt5
    ok = mt5.initialize(login=int(env["DEMO_MT5_LOGIN"]),
                        password=env["DEMO_MT5_PASSWORD"],
                        server=env.get("DEMO_MT5_SERVER", "ForexTimeFXTM-Demo01"))
    if not ok:
        return None, f"mt5_init_fail:{mt5.last_error()}"
    acc = mt5.account_info()
    if acc is None or acc.trade_mode != 0:   # trade_mode 0 = demo
        mt5.shutdown()
        return None, "not_demo_account(abort)"
    if not mt5.symbol_select(SYM, True):
        mt5.shutdown()
        return None, "symbol_select_fail"
    time.sleep(0.3)
    return mt5, None


def get_account():
    mt5, err = _connect()
    if err:
        return {"ok": False, "error": err}
    try:
        acc = mt5.account_info()
        out = {"ok": True, "login": acc.login, "server": acc.server, "demo": True,
               "balance": acc.balance, "equity": acc.equity,
               "margin": acc.margin, "margin_free": acc.margin_free,
               "margin_level": acc.margin_level, "leverage": acc.leverage,
               "currency": acc.currency}
        return out
    finally:
        mt5.shutdown()


def get_positions():
    """当前系统持仓(demo 侧, magic 过滤)。返回 list。"""
    mt5, err = _connect()
    if err:
        return {"ok": False, "error": err}
    try:
        import MetaTrader5 as mt5m
        poss = mt5.positions_get(symbol=SYM, magic=MAGIC) or []
        out = []
        for p in poss:
            out.append({"ticket": p.ticket, "side": "LONG" if p.type == 0 else "SHORT",
                        "qty": p.volume, "open_price": p.price_open,
                        "sl": p.sl, "tp": p.tp, "profit": p.profit,
                        "open_time": p.time})
        return {"ok": True, "positions": out}
    finally:
        mt5.shutdown()


def market_order(side, qty_lots, sl=None, tp=None, deviation_pts=10):
    """市价单(FOK)。side='LONG'/'SHORT'。返回成交结果。"""
    mt5, err = _connect()
    if err:
        return {"ok": False, "error": err}
    try:
        import MetaTrader5 as mt5m
        tick = mt5.symbol_info_tick(SYM)
        if tick is None:
            return {"ok": False, "error": "no_tick"}
        otype = mt5m.ORDER_TYPE_BUY if side == "LONG" else mt5m.ORDER_TYPE_SELL
        price = tick.ask if side == "LONG" else tick.bid
        req = {"action": mt5m.TRADE_ACTION_DEAL, "symbol": SYM, "volume": float(qty_lots),
               "type": otype, "price": price, "deviation": deviation_pts,
               "magic": MAGIC, "comment": "hermes-demo", "type_time": mt5m.ORDER_TIME_GTC,
               "type_filling": mt5m.ORDER_FILLING_FOK}
        if sl is not None:
            req["sl"] = float(sl)
        if tp is not None:
            req["tp"] = float(tp)
        res = mt5.order_send(req)
        if res is None:
            return {"ok": False, "error": f"no_response:{mt5.last_error()}"}
        if res.retcode != mt5m.TRADE_RETCODE_DONE:
            return {"ok": False, "error": f"retcode:{res.retcode}:{res.comment}"}
        return {"ok": True, "ticket": res.order, "fill_price": res.price,
                "volume": res.volume, "deal": getattr(res, "deal", None)}
    finally:
        mt5.shutdown()


def close_position(ticket, qty_lots=None):
    """按 ticket 平仓。qty 缺省=全平。"""
    mt5, err = _connect()
    if err:
        return {"ok": False, "error": err}
    try:
        import MetaTrader5 as mt5m
        poss = mt5.positions_get(ticket=ticket) or []
        if not poss:
            return {"ok": False, "error": "position_not_found"}
        p = poss[0]
        otype = mt5m.ORDER_TYPE_SELL if p.type == 0 else mt5m.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(SYM)
        price = tick.bid if p.type == 0 else tick.ask
        qty = qty_lots or p.volume
        req = {"action": mt5m.TRADE_ACTION_DEAL, "symbol": SYM, "volume": float(qty),
               "type": otype, "position": ticket, "price": price, "deviation": 10,
               "magic": MAGIC, "comment": "hermes-demo-close",
               "type_time": mt5m.ORDER_TIME_GTC, "type_filling": mt5m.ORDER_FILLING_FOK}
        res = mt5.order_send(req)
        if res is None:
            return {"ok": False, "error": f"no_response:{mt5.last_error()}"}
        if res.retcode != mt5m.TRADE_RETCODE_DONE:
            return {"ok": False, "error": f"retcode:{res.retcode}:{res.comment}"}
        return {"ok": True, "ticket": ticket, "close_price": res.price,
                "profit": getattr(res, "profit", None)}
    finally:
        mt5.shutdown()


def get_trades():
    """近期成交历史(magic 过滤)。"""
    mt5, err = _connect()
    if err:
        return {"ok": False, "error": err}
    try:
        import MetaTrader5 as mt5m
        deals = mt5.history_deals_get(datetime(2026, 9, 7)) if False else None
        # 简化: 返回 positions(open)即可; deals 查询用 position 关闭后由调用方记录
        return {"ok": True, "note": "use get_positions + local ledger"}
    finally:
        mt5.shutdown()


def get_closing_deal(position_id, lookback_hours=8):
    """查 position 的离场成交(broker 随单 SL/TP 自动平仓后本地对账用, 2026-09-08)。
    返回 {ok, price, time, profit, reason_code, type} 或 {ok:False, error}。
    找不到(未平/无记录)→ ok:False, 调用方不得臆断平仓价。"""
    mt5, err = _connect()
    if err:
        return {"ok": False, "error": err}
    try:
        import MetaTrader5 as mt5m
        from datetime import datetime as _dt, timedelta
        start = _dt.now() - timedelta(hours=lookback_hours)
        deals = None
        try:
            # 无窗 + position 精确查询: 本 build 带时间窗重载会忽略 position 且截断最近 ~3h
            # 成交(2026-09-08 曾把上一笔 LONG SL @4415.45 当成本仓 SHORT TP 对账价), 无窗形式 probe 验证正确
            deals = mt5.history_deals_get(position=position_id) or []
        except TypeError:  # 老版 wrapper 无 position 参数 → 全量后过滤
            deals = [d for d in (mt5.history_deals_get(start, _dt.now()) or [])
                     if getattr(d, "position_id", None) == position_id]
        outs = [d for d in deals if d.entry == 1]  # DEAL_ENTRY_OUT
        if not outs:
            return {"ok": False, "error": "no_closing_deal"}
        d = sorted(outs, key=lambda x: x.time)[-1]
        return {"ok": True, "price": d.price, "time": d.time, "profit": d.profit,
                "reason_code": d.reason, "type": d.type}
    finally:
        mt5.shutdown()


def history_balance(n=50):
    """demo 真实成交历史 → equity/balance 曲线点(从 history_deals 累计)。
    返回 [{time, balance, profit}...] 按时间序(用 deal profit 累加近似)。"""
    mt5, err = _connect()
    if err:
        return {"ok": False, "error": err}
    try:
        import MetaTrader5 as mt5m
        from datetime import datetime as _dt
        # 拉今天所有 deals(含 magic 90001/90002 测试 + hermes)
        start = _dt(2026, 9, 7)
        deals = mt5.history_deals_get(start, datetime.now()) or []
        rows = []
        bal = 2000.0  # demo 初始余额(账户创建值; 若不准以 account.balance 校准尾点)
        acc0 = mt5.account_info()
        # 倒推起点: 用所有 deal profit 从当前 balance 反推不可靠 → 用起始 2000
        running = bal
        for dl in sorted(deals, key=lambda x: x.time):
            running += dl.profit or 0
            rows.append({"t": _dt.fromtimestamp(dl.time).strftime("%m-%d %H:%M"),
                         "balance": round(running, 2),
                         "profit": round(dl.profit or 0, 2),
                         "type": dl.type})
        # 校准: 若终点与 account.balance 偏差大, 整体平移
        if rows and acc0:
            drift = (acc0.balance or 0) - rows[-1]["balance"]
            if abs(drift) > 1:
                for r in rows:
                    r["balance"] = round(r["balance"] + drift, 2)
        return {"ok": True, "points": rows, "final_balance": acc0.balance if acc0 else None}
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(get_account(), ensure_ascii=False, indent=1))
