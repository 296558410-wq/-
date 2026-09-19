# -*- coding: utf-8 -*-
"""V2 Module 3 — 确定性 Replay 引擎（仅读账本; 不调市场数据/Hermes/Broker; 不下单）。

从账本事件重建状态: account / open_positions / closed_positions / pnl / decisions。
同一账本重复 replay 必须得到相同 state_hash（确定性）。
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "hermes_v2_ledger.jsonl"


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def state_hash(state) -> str:
    return hashlib.sha256(_canon(state)).hexdigest()


def _num(x):
    return x if isinstance(x, (int, float)) else 0.0


def replay(path=None, execution_mode=None):
    """返回重建状态 dict（确定性, 无时间戳）。"""
    p = Path(path or LEDGER)
    evs = []
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                evs.append(json.loads(ln))
    if execution_mode:
        evs = [e for e in evs if e.get("execution_mode") == execution_mode]

    init_balance = None; currency = None
    balance = equity = None
    open_pos = {}          # position_id -> {...}
    closed = []
    gross = comm = swap = net = 0.0
    dec = {"TRADE": 0, "WAIT": 0, "REJECT": 0, "OTHER": 0}
    n_order_rejected = 0

    for e in evs:
        t = e.get("event_type")
        if t == "ACCOUNT_INIT":
            init_balance = e.get("account_balance", init_balance)
            currency = e.get("currency", currency)
        elif t == "DECISION":
            d = e.get("status") or e.get("message") or ""
            key = d if d in ("TRADE", "WAIT", "REJECT") else "OTHER"
            dec[key] += 1
        elif t == "ORDER_REJECTED":
            n_order_rejected += 1
        elif t == "FILL":
            pid = e.get("position_id")
            if pid and pid in open_pos:
                open_pos[pid]["fill_price"] = e.get("fill_price", open_pos[pid].get("fill_price"))
                open_pos[pid]["commission"] = _num(e.get("commission")) or open_pos[pid].get("commission", 0.0)
        elif t == "POSITION_OPEN":
            pid = e.get("position_id")
            if pid:
                open_pos[pid] = {"position_id": pid, "symbol": e.get("symbol"), "side": e.get("side"),
                                 "volume": e.get("volume"), "entry": e.get("fill_price"),
                                 "commission": _num(e.get("commission")), "opened_seq": e.get("seq")}
        elif t == "POSITION_CLOSED":
            pid = e.get("position_id")
            op = open_pos.pop(pid, None)
            g = e.get("gross_pnl")
            c = e.get("commission")
            s = e.get("swap")
            g = _num(g) if g is not None else 0.0
            c = _num(c) if c is not None else (op.get("commission", 0.0) if op else 0.0)
            s = _num(s)
            n = e.get("net_pnl")
            n = _num(n) if n is not None else g + c + s
            closed.append({"position_id": pid, "symbol": (e.get("symbol") or (op or {}).get("symbol")),
                           "side": e.get("side") or (op or {}).get("side"),
                           "entry": (op or {}).get("entry"), "exit": e.get("fill_price"),
                           "volume": e.get("volume") or (op or {}).get("volume"),
                           "gross_pnl": round(g, 6), "commission": round(c, 6), "swap": round(s, 6),
                           "net_pnl": round(n, 6), "close_seq": e.get("seq")})
            gross += g; comm += c; swap += s; net += n
        elif t == "COST":  # 未绑定到平仓的成本(若存在)
            if e.get("position_id") is None:
                comm += _num(e.get("commission")); swap += _num(e.get("swap"))
        elif t == "ACCOUNT_SNAPSHOT":
            if e.get("account_balance") is not None:
                balance = e.get("account_balance")
            if e.get("account_equity") is not None:
                equity = e.get("account_equity")

    closed_sorted = sorted(closed, key=lambda x: (x.get("close_seq") or 0, str(x.get("position_id"))))
    open_sorted = [open_pos[k] for k in sorted(open_pos.keys())]
    state = {
        "execution_mode_filter": execution_mode,
        "account": {"initial_balance": init_balance, "balance": balance, "equity": equity, "currency": currency},
        "open_positions": open_sorted,
        "closed_positions": closed_sorted,
        "trade_count": len(closed_sorted),
        "winning_trades": sum(1 for x in closed_sorted if x["net_pnl"] > 0),
        "losing_trades": sum(1 for x in closed_sorted if x["net_pnl"] <= 0),
        "gross_pnl": round(gross, 6), "commission": round(comm, 6), "swap": round(swap, 6),
        "net_pnl": round(net, 6),
        "decisions": dec, "orders_rejected": n_order_rejected, "events_consumed": len(evs),
    }
    state["state_hash"] = state_hash({k: v for k, v in state.items() if k != "state_hash"})
    return state


def conservation(state):
    """账户守恒: initial + gross + commission + swap == balance(或由 net 推算)。返回 (ok, detail)。"""
    acc = state["account"]
    init = acc.get("initial_balance")
    if init is None:
        return False, {"reason": "no_initial_balance"}
    derived = round(init + state["gross_pnl"] + state["commission"] + state["swap"], 6)
    final = acc.get("balance")
    ok = (final is None) or (abs(final - derived) < 1e-6)
    return ok, {"initial": init, "gross": state["gross_pnl"], "commission": state["commission"],
                "swap": state["swap"], "derived_balance": derived, "snapshot_balance": final, "ok": ok}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    s = replay()
    print(json.dumps(s, ensure_ascii=False, indent=1))
    print("conservation:", conservation(s))
