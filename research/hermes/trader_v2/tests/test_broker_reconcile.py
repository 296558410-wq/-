# -*- coding: utf-8 -*-
"""V2 回归测试 — Broker 自动平仓 / 对账状态一致性（T1–T8）。

背景（事故 2026-09-16，run V2-PAPER-20260915-112856-d341）：
  Broker 侧 TP/SL 自动平仓 → reconcile 写了账本，但没有同步 executor.acc["closed_trades"]
  → _account_match() 的 net_pnl / trade_count / commission 三项永久 false → run BLOCKED。

本测试**完全离线**（FakeBroker 替身；不连 MT5、不触网、不下真单、不写生产账本）。

T1 Broker 自动 TP    : open → broker TP → reconnect → reconcile → account match PASS
T2 Broker 自动 SL    : 同上（反向）
T3 Engine 主动 close : 原有路径不受影响
T4 重复 reconcile    : 同一 broker close 连续发现两次 → 不得重复记账本
T5 Restart recovery  : open → 进程崩溃 → broker close → 重启 → reconcile → 最终一致
T6 Partial state     : executor/broker 历史缺失 → fail-closed，不下新单
T7 Ledger consistency: Broker == Executor == Ledger == Replay
T8 Account conservation: 必须 PASS

日志: logs/test_broker_reconcile.log
"""
from __future__ import annotations
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for sub in ("execution", "ledger", "runtime"):
    sys.path.insert(0, str(ROOT / sub))
import hermes_paper_adapter as ADP  # noqa: E402
import broker_demo_executor as BDE  # noqa: E402
import fxtm_demo_adapter as FA  # noqa: E402
import ledger as L  # noqa: E402
import replay as R  # noqa: E402
import shadow_run as SR  # noqa: E402

TMP = HERE / "_tmp"; TMP.mkdir(exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_broker_reconcile.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


CFG = {
    "symbol": "XAUUSD",
    "execution": {
        "execution_mode": "BROKER_DEMO", "live_trading": False, "broker_demo_enabled": True,
        "cost_model": {"spread_bps_typical": 0.35, "slippage_bps": 0.30, "latency_ms": 250,
                       "commission_per_lot_usd": 0.0},
        "contract": {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100, "price_dp": 2,
                     "lot_dp": 2, "leverage": 500},
        "risk": {"per_trade_pct": 2.0, "single_position": True, "max_notional_usd": 25000},
    },
    "broker": {"broker": "FXTM", "environment": "DEMO", "enabled": True},
    "account": {"initial_balance": 1000.0},
}

DECISION = {
    "decision": "TRADE", "ts": "2026-09-16T06:00:00+00:00", "context_hash": "ctx_test",
    "reason": "test", "plan": {"direction": "SHORT", "qty_lots": None, "entry": 4292.60,
                               "stop_loss": 4309.82, "take_profit": 4265.05, "confidence": 0.55},
}

COMMISSION = -0.22  # 与事故当日 broker deal 实际值一致


class FakeBroker:
    """离线 broker 替身：可模拟引擎下单、broker 侧自动 TP/SL 平仓、deal 明细（可选择性缺失）。"""

    def __init__(self, balance=1000.0, entry=4292.60):
        self.connected = False
        self.positions = []
        self.closed = {}          # ticket -> {entry,exit,qty,side,gross,comm,swap,net}
        self.orders = []
        self._ticket = 700000
        self._bal0 = float(balance)
        self.entry = float(entry)

    # ---- 只读接口 ----
    def connect(self):
        self.connected = True
        return {"ok": True, "login": "******", "server": "ForexTimeFXTM-Demo01", "demo": True}

    def disconnect(self):
        self.connected = False

    def _balance(self):
        return round(self._bal0 + sum(v["net"] for v in self.closed.values()), 2)

    def get_account(self):
        b = self._balance()
        return {"ok": True, "login": "******", "server": "ForexTimeFXTM-Demo01", "demo": True,
                "balance": b, "equity": b, "margin": 0.0, "margin_free": b, "leverage": 500, "currency": "USD"}

    def get_positions(self):
        return {"ok": True, "positions": [dict(p) for p in self.positions]}

    def get_quote(self, symbol="XAUUSD"):
        return {"ok": True, "bid": self.entry, "ask": self.entry + 0.35}

    # ---- 下单/平仓 ----
    def place_market_order(self, symbol, side, qty_lots, sl=None, tp=None):
        self.orders.append({"symbol": symbol, "side": side, "qty": qty_lots, "sl": sl, "tp": tp})
        self._ticket += 1
        is_long = side.upper() in ("LONG", "BUY")
        px = self.entry + (0.35 if is_long else 0.0)
        self.positions.append({"ticket": self._ticket, "side": "LONG" if is_long else "SHORT",
                               "qty": float(qty_lots), "open_price": px, "sl": sl, "tp": tp,
                               "profit": 0.0, "magic": 90003})
        return {"ok": True, "retcode": 10009, "comment": "Done", "order": self._ticket,
                "deal": self._ticket + 1, "price": px, "volume": float(qty_lots)}

    def close_position(self, position_id, qty_lots=None):
        p = next((x for x in self.positions if x["ticket"] == int(position_id)), None)
        if not p:
            return {"ok": False, "retcode": 10013, "comment": "not found"}
        exit_px = p["open_price"] + (2.0 if p["side"] == "LONG" else -2.0)
        self.broker_fill_close(p["ticket"], exit_px)
        return {"ok": True, "retcode": 10009, "comment": "Done", "price": exit_px}

    def broker_fill_close(self, ticket, exit_px):
        """模拟 broker 自身（SL/TP）成交平仓：账户侧生效，引擎侧无感知。"""
        p = next(x for x in self.positions if x["ticket"] == int(ticket))
        gross = ((exit_px - p["open_price"]) if p["side"] == "LONG" else (p["open_price"] - exit_px)) * 100 * p["qty"]
        comm = round(COMMISSION * (p["qty"] / 0.01), 4)
        self.closed[p["ticket"]] = {"entry": p["open_price"], "exit": exit_px, "qty": p["qty"],
                                    "side": p["side"], "gross": round(gross, 4), "comm": comm,
                                    "swap": 0.0, "net": round(gross + comm, 4)}
        self.positions = [x for x in self.positions if x["ticket"] != int(ticket)]

    # ---- 成交明细 ----
    suppress_history = False

    def deals_for_position(self, position_id):
        if self.suppress_history:
            return []
        c = self.closed.get(int(position_id))
        if not c:
            return []
        return [
            {"ticket": 1, "order": 1, "position_id": int(position_id), "entry": 0,
             "type": 0 if c["side"] == "LONG" else 1, "price": c["entry"], "volume": c["qty"],
             "profit": 0.0, "commission": 0.0, "swap": 0.0, "magic": 90003, "time": 0},
            {"ticket": 2, "order": 2, "position_id": int(position_id), "entry": 1,
             "type": 1 if c["side"] == "LONG" else 0, "price": c["exit"], "volume": c["qty"],
             "profit": c["gross"], "commission": c["comm"], "swap": c["swap"], "magic": 90003, "time": 0},
        ]


_ORIG = FA.FXTMDemoAdapter


def _use(broker):
    FA.FXTMDemoAdapter = lambda *a, **k: broker
    return BDE.BrokerDemoExecutor(deepcopy(CFG))


def _ledger(name):
    p = TMP / name
    if p.exists():
        p.unlink()
    return p


def _match(ex, led):
    rst = R.replay(led, execution_mode="BROKER_DEMO")
    acc = ex.account()
    return SR._account_match(ex, rst, acc)


# ---------------------------------------------------------------- T1
def t1_broker_auto_tp():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t1_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60)
    check("T1 开仓 EXECUTED", out.get("execution_result") == "EXECUTED", str(out.get("execution_result")))
    pid = out["position_id"]
    b.broker_fill_close(int(pid), 4265.05)          # broker 按 TP 平仓
    ex2 = _use(b); ex2.connect()                    # 下一周期 / 新进程：reconnect（内存态清空）
    n = ADP.reconcile_broker_closes(ex2, led, run_id="T1", execution_mode="BROKER_DEMO",
                                    decision_window="2026-09-16T06:15Z")
    check("T1 reconcile 补记 1 笔", n == 1, f"n={n}")
    check("T1 executor.closed_trades 已同步", len(ex2.acc["closed_trades"]) == 1,
          str(ex2.acc["closed_trades"]))
    match, mism = _match(ex2, led)
    check("T1 account match PASS", match, f"mismatch={mism}")
    return b, led


# ---------------------------------------------------------------- T2
def t2_broker_auto_sl():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t2_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60)
    pid = out["position_id"]
    b.broker_fill_close(int(pid), 4309.82)          # broker 按 SL 平仓（亏损）
    ex2 = _use(b); ex2.connect()
    n = ADP.reconcile_broker_closes(ex2, led, run_id="T2", execution_mode="BROKER_DEMO")
    check("T2 reconcile 补记 1 笔", n == 1, f"n={n}")
    match, mism = _match(ex2, led)
    check("T2 account match PASS(SL 亏损)", match, f"mismatch={mism}")
    rst = R.replay(led, execution_mode="BROKER_DEMO")
    check("T2 亏损入账(net<0)", rst["net_pnl"] < 0, str(rst["net_pnl"]))


# ---------------------------------------------------------------- T3
def t3_engine_close():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t3_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60, close_after=True)
    check("T3 引擎主动 close EXECUTED", out.get("execution_result") == "EXECUTED")
    match, mism = _match(ex, led)
    check("T3 原路径 account match PASS", match, f"mismatch={mism}")
    n = ADP.reconcile_broker_closes(ex, led, run_id="T3", execution_mode="BROKER_DEMO")
    check("T3 对账不重复补记", n == 0, f"n={n}")


# ---------------------------------------------------------------- T4
def t4_duplicate_reconcile():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t4_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60)
    b.broker_fill_close(int(out["position_id"]), 4265.05)
    ex2 = _use(b); ex2.connect()
    n1 = ADP.reconcile_broker_closes(ex2, led, run_id="T4", execution_mode="BROKER_DEMO")
    evs1 = L.load_events(led)
    ex3 = _use(b); ex3.connect()
    n2 = ADP.reconcile_broker_closes(ex3, led, run_id="T4", execution_mode="BROKER_DEMO")
    evs2 = L.load_events(led)
    check("T4 首次补记 1 笔", n1 == 1, f"n1={n1}")
    check("T4 二次对账 0 笔（不重复记账本）", n2 == 0, f"n2={n2}")
    check("T4 账本事件数不变", len(evs1) == len(evs2), f"{len(evs1)} vs {len(evs2)}")
    check("T4 POSITION_CLOSED 仅 1 条",
          sum(1 for e in evs2 if e["event_type"] == "POSITION_CLOSED") == 1)
    check("T4 链 verify 仍 OK", L.verify_ledger(led)[0])
    match, mism = _match(ex3, led)
    check("T4 account match PASS", match, f"mismatch={mism}")


# ---------------------------------------------------------------- T5
def t5_restart_recovery():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t5_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60)
    pid = out["position_id"]
    del ex                                            # 模拟进程崩溃：executor 内存态全部丢失
    b.broker_fill_close(int(pid), 4265.05)            # broker 侧在“崩溃期间”平仓
    ex_new = _use(b); ex_new.connect()                # 重启：全新 executor
    check("T5 重启后内存态为空", ex_new.acc["closed_trades"] == [], str(ex_new.acc["closed_trades"]))
    n = ADP.reconcile_broker_closes(ex_new, led, run_id="T5", execution_mode="BROKER_DEMO")
    check("T5 重启恢复补记 1 笔", n == 1, f"n={n}")
    match, mism = _match(ex_new, led)
    check("T5 重启后最终一致(match PASS)", match, f"mismatch={mism}")


# ---------------------------------------------------------------- T6
def t6_partial_state_fail_closed():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t6_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60)
    b.broker_fill_close(int(out["position_id"]), 4265.05)
    b.suppress_history = True                          # broker deal 历史不可用（部分状态）
    ex2 = _use(b); ex2.connect()
    orders_before = len(b.orders)
    ADP.reconcile_broker_closes(ex2, led, run_id="T6", execution_mode="BROKER_DEMO")
    match, mism = _match(ex2, led)
    check("T6 状态不全 → match FAIL(fail-closed)", match is False, f"mismatch={mism}")
    check("T6 显式标注 history_unavailable", "history_unavailable" in (mism or {}), str(mism))
    check("T6 不执行新订单", len(b.orders) == orders_before, f"{orders_before} -> {len(b.orders)}")
    b.suppress_history = False


# ---------------------------------------------------------------- T7
def t7_ledger_consistency():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t7_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60)
    b.broker_fill_close(int(out["position_id"]), 4265.05)
    ex2 = _use(b); ex2.connect()
    ADP.reconcile_broker_closes(ex2, led, run_id="T7", execution_mode="BROKER_DEMO")
    st = R.replay(led, execution_mode="BROKER_DEMO")
    acc = ex2.account()
    broker_net = round(sum(t["net_usd"] for t in acc["closed_trades"]), 6)
    broker_comm = round(sum(t["commission_usd"] for t in acc["closed_trades"]), 6)
    check("T7 Broker == Executor == Ledger == Replay",
          st["trade_count"] == len(acc["closed_trades"]) == 1
          and abs(st["net_pnl"] - broker_net) < 0.05
          and abs(st["commission"] - broker_comm) < 0.05
          and abs(st["account"]["balance"] - acc["balance"]) < 0.05,
          f"replay(net={st['net_pnl']},comm={st['commission']},bal={st['account']['balance']}) "
          f"broker(net={broker_net},comm={broker_comm},bal={acc['balance']})")


# ---------------------------------------------------------------- T8
def t8_conservation():
    b = FakeBroker(); ex = _use(b)
    led = _ledger("t8_ledger.jsonl")
    ex.connect()
    out = ADP.process(deepcopy(DECISION), ex, led, market_mid=4292.60)
    b.broker_fill_close(int(out["position_id"]), 4265.05)
    ex2 = _use(b); ex2.connect()
    ADP.reconcile_broker_closes(ex2, led, run_id="T8", execution_mode="BROKER_DEMO")
    st = R.replay(led, execution_mode="BROKER_DEMO")
    ok, det = R.conservation(st)
    check("T8 replay conservation PASS", ok, str(det))
    # 账户守恒（run 口径）：账本 ACCOUNT_INIT 开的基准 + broker 已实现净额 == broker 当前 balance
    # 注：executor.conservation_ok() 的 initial_balance 是“每次 connect 快照”，跨 reconnect 会重置，
    #     因此 run 级守恒以账本 ACCOUNT_INIT 为权威基准。
    acc = ex2.account()
    init = st["account"]["initial_balance"]
    broker_realized = round(sum(t["net_usd"] for t in acc["closed_trades"]), 6)
    check("T8 broker 账户守恒(账本基准)", abs((init + broker_realized) - acc["balance"]) < 0.05,
          f"init={init} realized={broker_realized} balance={acc['balance']}")
    bok, bdet = ex2.conservation_ok()
    log(f"INFO | T8 executor.conservation_ok()(session 口径) = {bok} {bdet}")


def main():
    t1_broker_auto_tp()
    t2_broker_auto_sl()
    t3_engine_close()
    t4_duplicate_reconcile()
    t5_restart_recovery()
    t6_partial_state_fail_closed()
    t7_ledger_consistency()
    t8_conservation()
    FA.FXTMDemoAdapter = _ORIG
    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
