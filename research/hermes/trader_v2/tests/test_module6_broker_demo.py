# -*- coding: utf-8 -*-
"""V2 Module 6 — BROKER_DEMO 接线验收测试（离线；不触网/不连 broker；用 FakeAdapter 替身）。

覆盖:
  §一 门: assert_execution_allowed 允许 PAPER/BROKER_DEMO, 拒绝 LIVE / 未开 broker；
      BrokerDemoExecutor._guard 拒绝非 BROKER_DEMO / live / 未启用。
  §二 路由: ADP.execution_mode_of + BrokerDemoExecutor.backend=fxtm_demo → 事件打 BROKER_DEMO 戳。
  §三 闭环: 一 TRADE 决策 → 开仓 → 平仓 → 账本(EXECUTION_REQUEST/FILL/POSITION_OPEN/POSITION_CLOSED/COST/PNL/ACCOUNT_SNAPSHOT)
      → replay(BROKER_DEMO) 重建 trade_count/net；conservation 用 broker 口径。
  §四 风控: min/max lot / RISK_LIMIT / POSITION_BUSY 在 broker 执行器同样硬拒绝。
日志: logs/test_module6_broker_demo.log
"""
import sys, json, math
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for sub in ("execution", "ledger"):
    sys.path.insert(0, str(ROOT / sub))
import hermes_paper_adapter as ADP  # noqa: E402
import broker_demo_executor as BDE  # noqa: E402
import fxtm_demo_adapter as FA  # noqa: E402
import ledger as L  # noqa: E402
import replay as R  # noqa: E402

TMP = HERE / "_tmp"; TMP.mkdir(exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_module6_broker_demo.log"
_res = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


CFG = {
    "symbol": "XAUUSD",
    "execution": {
        "execution_mode": "BROKER_DEMO", "live_trading": False, "broker_demo_enabled": True,
        "cost_model": {"spread_bps_typical": 0.35, "slippage_bps": 0.30, "latency_ms": 250, "commission_per_lot_usd": 0.0},
        "contract": {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2, "leverage": 500},
        "risk": {"per_trade_pct": 1.0, "single_position": True, "max_notional_usd": 25000},
    },
    "broker": {"broker": "FXTM", "environment": "DEMO", "enabled": True},
    "account": {"initial_balance": 10000.0},
}

DECISION = {
    "decision": "TRADE", "ts": "2026-09-14T06:00:00+00:00", "context_hash": "ctx_test",
    "reason": "test", "plan": {"direction": "LONG", "qty_lots": 0.01, "entry": 4400.0,
                               "stop_loss": 4380.0, "take_profit": 4430.0, "confidence": 0.6},
}


class FakeAdapter:
    """离线替身: 模拟一个 DEMO broker 的开/平/账户/成交明细。"""
    BAL = 10000.0

    def __init__(self):
        self.connected = False
        self.positions = []
        self.closed = {}
        self.orders = []
        self._ticket = 555000

    def connect(self):
        self.connected = True
        return {"ok": True, "login": "******", "server": "ForexTimeFXTM-Demo01", "demo": True}

    def disconnect(self):
        self.connected = False

    def get_account(self):
        bal = self.BAL + sum(v["net"] for v in self.closed.values())
        return {"ok": True, "login": "******", "server": "ForexTimeFXTM-Demo01", "demo": True,
                "balance": round(bal, 2), "equity": round(bal, 2), "margin": 0.0,
                "margin_free": round(bal, 2), "leverage": 500, "currency": "USD"}

    def get_positions(self):
        return {"ok": True, "positions": [dict(p) for p in self.positions]}

    def place_market_order(self, symbol, side, qty_lots, sl=None, tp=None):
        self.orders.append({"symbol": symbol, "side": side, "qty": qty_lots, "sl": sl, "tp": tp})
        self._ticket += 1
        entry = 4400.0 + (0.3 if side.upper() in ("LONG", "BUY") else -0.3)
        p = {"ticket": self._ticket, "side": "LONG" if side.upper() in ("LONG", "BUY") else "SHORT",
             "qty": float(qty_lots), "open_price": entry, "sl": sl, "tp": tp, "profit": 0.0, "magic": 90003}
        self.positions.append(p)
        return {"ok": True, "retcode": 10009, "comment": "Done", "order": self._ticket,
                "deal": self._ticket + 1, "price": entry, "volume": float(qty_lots)}

    def close_position(self, position_id, qty_lots=None):
        p = next((x for x in self.positions if x["ticket"] == int(position_id)), None)
        if not p:
            return {"ok": False, "retcode": 10013, "comment": "not found"}
        self.positions = [x for x in self.positions if x["ticket"] != int(position_id)]
        exit_px = p["open_price"] + (2.0 if p["side"] == "LONG" else -2.0)
        gross = (exit_px - p["open_price"]) * 100 * p["qty"]
        comm = -0.07 * p["qty"] / 0.01
        self.closed[p["ticket"]] = {"entry": p["open_price"], "exit": exit_px, "qty": p["qty"],
                                    "side": p["side"], "gross": round(gross, 4), "comm": round(comm, 4),
                                    "swap": 0.0, "net": round(gross + comm, 4)}
        return {"ok": True, "retcode": 10009, "comment": "Done", "price": exit_px}

    def deals_for_position(self, position_id):
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


def main():
    _FAKE = FakeAdapter()
    orig = FA.FXTMDemoAdapter
    FA.FXTMDemoAdapter = lambda *a, **k: _FAKE

    # ---------- §一 门 ----------
    try:
        ADP.assert_execution_allowed({"execution": {"execution_mode": "PAPER", "live_trading": False,
                                                    "broker_demo_enabled": False}, "broker": {"enabled": False}})
        check("§一 PAPER 门 PASS", True)
    except Exception as e:
        check("§一 PAPER 门 PASS", False, str(e))
    try:
        ADP.assert_execution_allowed(deepcopy(CFG))
        check("§一 BROKER_DEMO 门 PASS(已开)", True)
    except Exception as e:
        check("§一 BROKER_DEMO 门 PASS(已开)", False, str(e))
    for bad, nm in (({**deepcopy(CFG), "broker": {"enabled": False}}, "broker.enabled=false"),
                    ({"execution": {"execution_mode": "BROKER_DEMO", "live_trading": False, "broker_demo_enabled": False},
                      "broker": {"enabled": True}}, "broker_demo_enabled=false"),
                    ({"execution": {"execution_mode": "LIVE", "live_trading": True, "broker_demo_enabled": True},
                      "broker": {"enabled": True}}, "LIVE")):
        try:
            ADP.assert_execution_allowed(bad); check(f"§一 拒绝 {nm}", False, "unexpected pass")
        except ADP.RefuseToStart:
            check(f"§一 拒绝 {nm}", True)

    # ---------- §二 路由 ----------
    ex = BDE.BrokerDemoExecutor(deepcopy(CFG))
    check("§二 backend==fxtm_demo", ex.backend == "fxtm_demo", ex.backend)
    check("§二 execution_mode_of", ADP.execution_mode_of(deepcopy(CFG)) == "BROKER_DEMO")
    # _guard 拒绝
    for bad_mode in ({"execution": {"execution_mode": "PAPER", "live_trading": False, "broker_demo_enabled": True},
                      "broker": {"enabled": True}},):
        b = BDE.BrokerDemoExecutor(bad_mode)
        try:
            b._guard(); check("§二 _guard 拒 PAPER", False, "unexpected pass")
        except BDE.RefuseExecution:
            check("§二 _guard 拒 PAPER", True)

    # ---------- §三 闭环 ----------
    led = TMP / "mod6_ledger.jsonl"
    if led.exists():
        led.unlink()
    ex2 = BDE.BrokerDemoExecutor(deepcopy(CFG))
    ex2.connect()
    check("§三 connect seed initial==broker", ex2.acc["initial_balance"] == FakeAdapter.BAL, str(ex2.acc["initial_balance"]))
    out = ADP.process(deepcopy(DECISION), ex2, led, market_mid=4400.0, close_after=True)
    check("§三 execution_result==EXECUTED", out.get("execution_result") == "EXECUTED", str(out.get("execution_result")))
    evs = L.load_events(led)
    modes = {e.get("execution_mode") for e in evs}
    envs = {e.get("environment") for e in evs}
    check("§三 事件全 BROKER_DEMO", modes == {"BROKER_DEMO"} and envs == {"BROKER_DEMO"}, f"modes={modes} envs={envs}")
    types = [e["event_type"] for e in evs]
    need = {"EXECUTION_REQUEST", "EXECUTION_RESPONSE", "FILL", "POSITION_OPEN", "POSITION_CLOSED", "COST", "PNL", "ACCOUNT_SNAPSHOT"}
    check("§三 闭环事件齐全", need.issubset(set(types)), str(sorted(set(types))))
    ok, det = L.verify_ledger(led)
    check("§三 账本链 verify", ok, str(det))
    st = R.replay(led, execution_mode="BROKER_DEMO")
    check("§三 replay trade_count==1", st["trade_count"] == 1, str(st["trade_count"]))
    acc = ex2.account()
    check("§三 replay net == broker realized", abs(st["net_pnl"] - acc["realized_pnl"]) < 0.05,
          f"replay={st['net_pnl']} broker={acc['realized_pnl']}")
    cok, cdet = R.conservation(st)
    check("§三 conservation(broker口径)", cok, str(cdet))

    # ---------- §四 风控 ----------
    ex3 = BDE.BrokerDemoExecutor(deepcopy(CFG)); ex3.connect()
    too_big = BDE.BrokerDemoExecutor(deepcopy(CFG)); too_big.connect()
    r = too_big.open("LONG", 4400.0, 4380.0, 4430.0, "P", qty_lots=0.06)
    check("§四 max_lot 硬拒", (not r["ok"]) and r["failure_code"] == "RISK_LIMIT", str(r.get("failure_code")))
    r2 = ex3.open("LONG", 4400.0, 4380.0, 4430.0, "P", qty_lots=0.01)
    check("§四 开仓成功", r2["ok"], str(r2.get("failure_code")))
    r3 = ex3.open("LONG", 4400.0, 4380.0, 4430.0, "P", qty_lots=0.01)
    check("§四 POSITION_BUSY", (not r3["ok"]) and r3["failure_code"] == "POSITION_BUSY", str(r3.get("failure_code")))
    ex3.close(r2["position"]["position_id"])

    FA.FXTMDemoAdapter = orig
    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if all(_res) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
