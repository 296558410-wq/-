# -*- coding: utf-8 -*-
"""V2 Module 6 — FXTM DEMO 真实执行器（BROKER_DEMO）。

把 Hermes 决策在**独立测试实例 "******"（fxtm_demo_01）**上真实下单/平仓；账目以 broker 实际为准。
与 PaperExecutor 同接口（acc / open / close / account / _fresh / size_position_raw），便于 ADP.process 透明路由。

硬门（不可绕过）:
- execution.execution_mode == "BROKER_DEMO" 且 broker.enabled == true 且 execution.broker_demo_enabled == true；
- 且 live_trading 必须 false（本执行器绝不 LIVE）；adapter 再校验 实例/服务器/DEMO。
不读 Agent1/2；不改 entry/SL/TP 语义；单标的单仓；失败即时拒绝（不静默缩仓）。
成本/盈亏以 broker deals 为准（commission/swap/profit），入账并与账本对账。
"""
from __future__ import annotations
import math
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import fxtm_demo_adapter as FA  # noqa: E402
import broker_validate as BV  # noqa: E402


def _now():
    return datetime.now(timezone.utc).isoformat()


# 已实现成交的“数值等同”判定（仅比对账/去重相关的已实现字段；reason/时限等元数据不参与）
_TRADE_NUM_FIELDS = ("gross_usd", "commission_usd", "swap_usd", "net_usd", "entry", "exit", "qty_lots")


def _same_trade(a, b):
    for k in _TRADE_NUM_FIELDS:
        va, vb = a.get(k), b.get(k)
        if va is None and vb is None:
            continue
        try:
            if abs(float(va) - float(vb)) > 1e-6:
                return False
        except (TypeError, ValueError):
            if va != vb:
                return False
    return True


class RefuseExecution(Exception):
    def __init__(self, code, message=""):
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)


class BrokerDemoExecutor:
    backend = "fxtm_demo"

    def __init__(self, config=None):
        cfg = config or FA._load_cfg()
        ex = cfg.get("execution", {})
        br = cfg.get("broker", {})
        self.contract = ex.get("contract", {"min_lot": 0.01, "max_lot": 0.05,
                                            "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2})
        self.risk = ex.get("risk", {"per_trade_pct": 1.0, "single_position": True, "max_notional_usd": 25000})
        self.cost = ex.get("cost_model", {})
        self.mode = ex.get("execution_mode", "PAPER")
        self.live = bool(ex.get("live_trading", False))
        self.enabled = bool(br.get("enabled", False) and ex.get("broker_demo_enabled", False))
        self.symbol = cfg.get("symbol", "XAUUSD")
        self.adapter = FA.FXTMDemoAdapter()
        self._connected = False
        self.acc = self._fresh(0.0)

    # ---------- 安全门 ----------
    def _guard(self):
        if self.mode != "BROKER_DEMO":
            raise RefuseExecution("NON_BROKER_DEMO_MODE", f"mode={self.mode}")
        if self.live:
            raise RefuseExecution("LIVE_FORBIDDEN", "live_trading=true")
        if not self.enabled:
            raise RefuseExecution("BROKER_DEMO_NOT_ENABLED", "broker.enabled/broker_demo_enabled 未开")

    # ---------- 连接 / 账户 ----------
    def connect(self):
        self._guard()
        acct = self.adapter.connect()  # adapter 自身门 + 实例/服务器/DEMO 校验
        self._connected = True
        self.acc = self._fresh(float(self.adapter.get_account()["balance"]))
        self._refresh_account()
        return acct

    def disconnect(self):
        try:
            self.adapter.disconnect()
        finally:
            self._connected = False

    def _fresh(self, initial=0.0):
        return {"initial_balance": float(initial), "balance": float(initial), "equity": float(initial),
                "cash": float(initial), "margin_used": 0.0, "realized_pnl": 0.0, "unrealized_pnl": 0.0,
                "peak_equity": float(initial), "drawdown": 0.0, "positions": [], "closed_trades": [],
                "created_utc": _now(), "backend": "fxtm_demo", "currency": "USD"}

    @staticmethod
    def _p(x, dp=2):
        return round(float(x) + 1e-9, dp)

    def _lots(self, x):
        # FLOOR-TO-STEP（与 Paper 一致；风险优先，绝不向上放大）
        dp = int(self.contract.get("lot_dp", 2))
        step = 10.0 ** (-dp)
        return round(math.floor(float(x) / step + 1e-9) * step, dp)

    def size_position_raw(self, entry, sl, equity=None, qty_lots=None):
        if qty_lots is not None:
            return self._lots(qty_lots)
        eq = float(equity if equity is not None else self.acc["equity"])
        dist = abs(entry - sl)
        if dist <= 0:
            return 0.0
        risk_usd = eq * self.risk.get("per_trade_pct", 1.0) / 100.0
        return self._lots(risk_usd / (dist * self.contract["contract_size_oz"]))

    def _pos_view(self, p):
        return {"position_id": str(p["ticket"]), "symbol": self.symbol, "direction": p["side"],
                "qty_lots": float(p["qty"]), "entry": float(p["open_price"]), "sl": p.get("sl"),
                "tp": p.get("tp"), "unrealized_pnl": round(float(p.get("profit") or 0.0), 4),
                "entry_cost_usd": 0.0, "state": "OPEN", "magic": p.get("magic")}

    def _refresh_account(self):
        if not self._connected:
            self.connect()
        a = self.adapter.get_account()
        poss = self.adapter.get_positions().get("positions", [])
        self.acc["balance"] = float(a["balance"])
        self.acc["equity"] = float(a["equity"])
        self.acc["unrealized_pnl"] = round(sum(float(p.get("profit") or 0.0) for p in poss), 4)
        self.acc["positions"] = [self._pos_view(p) for p in poss]
        self.acc["realized_pnl"] = round(self.acc["balance"] - self.acc["initial_balance"], 4)
        self.acc["peak_equity"] = round(max(self.acc.get("peak_equity", self.acc["equity"]), self.acc["equity"]), 4)
        self.acc["drawdown"] = round(self.acc["peak_equity"] - self.acc["equity"], 4)

    def account(self):
        self._refresh_account()
        return self.acc

    # ---------- 开仓 ----------
    def open(self, direction, mid, sl, tp, plan_id, context_id=None, decision_ref=None,
             symbol=None, qty_lots=None, **kw):
        self._guard()
        if not self._connected:
            self.connect()
        symbol = symbol or self.symbol
        dp = int(self.contract.get("price_dp", 2))

        if self.adapter.get_positions().get("positions"):
            return {"ok": False, "status": "rejected", "failure_code": "POSITION_BUSY",
                    "reason": f"{symbol} 已有 open position"}

        eq = float(self.acc.get("equity") or self.acc["initial_balance"])
        dist = abs(float(mid) - float(sl))
        if dist <= 0:
            return reject("RISK_LIMIT", "stop_distance 0 (SL==entry)")
        min_lot = self.contract["min_lot"]
        qty = self.size_position_raw(mid, sl, equity=eq, qty_lots=qty_lots)
        if qty < min_lot:
            qty = min_lot        # 平台最小手底线: 风险预算不足时按 min_lot 执行
        notional = qty * float(mid) * self.contract["contract_size_oz"]
        risk_usd = qty * dist * self.contract["contract_size_oz"]
        max_notional = self.risk.get("max_notional_usd", 25000)
        target_risk = eq * self.risk.get("per_trade_pct", 1.0) / 100.0
        allowed_risk = max(target_risk, min_lot * dist * self.contract["contract_size_oz"])

        def reject(code, reason):
            return {"ok": False, "status": "rejected", "failure_code": code, "reason": reason}

        if qty > self.contract["max_lot"]:
            return reject("RISK_LIMIT", f"position_size {qty} > max_lot {self.contract['max_lot']}")
        if notional > max_notional:
            return reject("RISK_LIMIT", f"notional {notional:.0f} > max {max_notional}")
        if risk_usd > eq + 1e-6:
            return reject("RISK_LIMIT", f"risk {risk_usd:.2f} > equity {eq:.2f}")
        if risk_usd > allowed_risk + 1e-6:
            return reject("RISK_LIMIT", f"risk {risk_usd:.2f} > allowed {allowed_risk:.2f} (target {target_risk:.2f})")

        # P1-C: 发送前预校验（fail-closed；杜绝 BROKER_REJECT_10016）
        _spec = {}
        try:
            _spec = self.adapter.symbol_spec(symbol) or {}
        except Exception:  # noqa: BLE001
            _spec = {}
        _q = {}
        try:
            _q = self.adapter.get_quote(symbol) or {}
        except Exception:  # noqa: BLE001
            _q = {}
        _okp, _code, _det = BV.precheck_order(
            direction, mid, sl, tp, market_bid=_q.get("bid"), market_ask=_q.get("ask"),
            stops_level=(_spec.get("stops_level") or 0.0), digits=_spec.get("digits", dp),
            tick=(_spec.get("tick_size") or 0.01))
        if not _okp:
            return reject(_code, f"precheck rejected: {_det}")

        res = self.adapter.place_market_order(symbol, direction, qty,
                                              sl=self._p(sl, dp) if sl is not None else None,
                                              tp=self._p(tp, dp) if tp is not None else None)
        if not res.get("ok"):
            return reject(f"BROKER_REJECT_{res.get('retcode')}", f"{res.get('comment')}")

        time.sleep(0.5)
        poss = self.adapter.get_positions().get("positions", [])
        if not poss:
            return reject("NO_POSITION_AFTER_FILL", f"order ok(retcode={res.get('retcode')}) 但未见持仓")
        p = poss[-1]
        pos = self._pos_view(p)
        pos.update({"plan_id": plan_id, "context_id": context_id, "decision_ref": decision_ref,
                    "opened_at": _now(), "fill_price": res.get("price"),
                    "order_id": res.get("order"), "deal_id": res.get("deal"),
                    "broker_retcode": res.get("retcode")})
        self._refresh_account()
        return {"ok": True, "status": "filled", "position": pos, "fill": float(p["open_price"])}

    def trade_from_deals(self, ticket, reason="broker_close"):
        """仅从 broker deals 重建一笔已平仓 trade（不回下单）。未平仓/无 deals → None。"""
        try:
            t = int(ticket)
        except Exception:  # noqa: BLE001
            return None
        deals = self.adapter.deals_for_position(t)
        if not deals:
            return None
        exit_deals = [d for d in deals if int(d.get("entry", -1)) == 1]
        if not exit_deals:
            return None
        entry_deals = [d for d in deals if int(d.get("entry", -1)) == 0]
        comm = round(sum(float(d.get("commission") or 0.0) for d in deals), 4)
        swap = round(sum(float(d.get("swap") or 0.0) for d in deals), 4)
        profit = round(sum(float(d.get("profit") or 0.0) for d in deals), 4)
        vol = round(sum(float(d.get("volume") or 0.0) for d in exit_deals), 4) or None
        entry_px = entry_deals[0].get("price") if entry_deals else None
        exit_px = exit_deals[-1].get("price")
        direction = "LONG" if (entry_deals and entry_deals[0].get("type") == 0) else "SHORT"
        net = round(profit + comm + swap, 4)
        return {"position_id": str(t), "direction": direction, "qty_lots": vol,
                "entry": entry_px, "exit": exit_px, "reason": reason,
                "gross_usd": profit, "commission_usd": comm, "swap_usd": swap, "net_usd": net,
                "entry_cost_usd": comm, "exit_cost_usd": 0.0, "closed_at": _now()}

    # ---------- 已实现成交视图（与 close() 同一状态语义；供对账 / 重启恢复复用） ----------
    def register_closed_trade(self, trade, *, replace=True):
        """把一笔已实现成交登记进 acc["closed_trades"]（幂等：按 position_id 唯一）。

        与 close() 状态语义完全一致（同一 dict 形状、同一去重键）；reconcile / 重启恢复
        路径必须走这里，禁止各自维护第二份状态。
        返回 True=新增或更新；False=已存在且数值一致（重复对账，未产生第二份状态）。
        """
        if not trade or not trade.get("position_id"):
            return False
        pid = str(trade["position_id"])
        cur = self.acc.setdefault("closed_trades", [])
        existing = next((t for t in cur if str(t.get("position_id")) == pid), None)
        if existing is not None:
            if _same_trade(existing, trade):
                return False
            if not replace:
                return False
        self.acc["closed_trades"] = [t for t in cur if str(t.get("position_id")) != pid]
        self.acc["closed_trades"].append(trade)
        return True

    def rebuild_closed_trades(self, position_ids, *, reason="broker_sl_tp"):
        """从 broker deal 明细重建指定 position 的已实现成交（跨 reconnect/restart 持久化）。

        为什么需要：acc["closed_trades"] 是进程内状态，connect() 每周期都会 _fresh() 清空；
        若只用内存状态，则「上一周期或上一进程平掉的仓」在下一周期必然对不上账本 → 误判 BLOCK。
        这里以 broker deal 历史为权威源重建 run 范围内的已实现成交集合。
        返回 {"rebuilt": [...], "missing": [...], "duplicate_prevented": [...]}；
        missing = broker 侧无 deal 明细（例如历史不可用）→ 由调用方 fail-closed。
        """
        rebuilt, missing, dup = [], [], []
        for pid in position_ids:
            pid = str(pid)
            if any(str(t.get("position_id")) == pid for t in self.acc.get("closed_trades", [])):
                dup.append(pid)
                continue
            tr = self.trade_from_deals(pid, reason=reason)
            if not tr:
                missing.append(pid)
                continue
            self.register_closed_trade(tr)
            rebuilt.append(pid)
        return {"rebuilt": rebuilt, "missing": missing, "duplicate_prevented": dup}

    # ---------- 平仓 ----------
    def close(self, position_id, price=None, reason="manual", **kw):
        self._guard()
        if not self._connected:
            self.connect()
        ticket = int(position_id)
        res = self.adapter.close_position(ticket)
        if not res.get("ok"):
            return {"ok": False, "error": f"close_rejected:{res.get('retcode')}", "reason": res.get("comment")}
        time.sleep(0.5)
        deals = self.adapter.deals_for_position(ticket)
        comm = round(sum(float(d.get("commission") or 0.0) for d in deals), 4)
        swap = round(sum(float(d.get("swap") or 0.0) for d in deals), 4)
        profit = round(sum(float(d.get("profit") or 0.0) for d in deals), 4)
        entry_deals = [d for d in deals if int(d.get("entry", -1)) == 0]
        exit_deals = [d for d in deals if int(d.get("entry", -1)) == 1]
        vol = round(sum(float(d.get("volume") or 0.0) for d in exit_deals), 4) or None
        entry_px = entry_deals[0].get("price") if entry_deals else None
        exit_px = exit_deals[-1].get("price") if exit_deals else res.get("price")
        direction = "LONG" if (entry_deals and entry_deals[0].get("type") == 0) else "SHORT"
        net = round(profit + comm + swap, 4)
        trade = {"position_id": str(ticket), "direction": direction, "qty_lots": vol,
                 "entry": entry_px, "exit": exit_px, "reason": reason,
                 "gross_usd": profit, "commission_usd": comm, "swap_usd": swap, "net_usd": net,
                 "entry_cost_usd": comm, "exit_cost_usd": 0.0,
                 "closed_at": _now(), "broker_retcode": res.get("retcode")}
        self.register_closed_trade(trade)
        self._refresh_account()
        return {"ok": True, "trade": trade}

    def conservation_ok(self):
        """broker 口径: initial + Σ net == 当前 balance（容差内）。"""
        s = sum(t["net_usd"] for t in self.acc.get("closed_trades", []))
        bal = self.acc["balance"]
        ok = abs((self.acc["initial_balance"] + s) - bal) < 0.05  # broker 四舍五入容差
        return ok, {"sum_net": round(s, 4), "expected_balance": round(self.acc["initial_balance"] + s, 4),
                    "balance": bal, "tolerance": 0.05}


if __name__ == "__main__":
    import sys as _s
    _s.stdout.reconfigure(encoding="utf-8")
    cfg = FA._load_cfg()
    b = BrokerDemoExecutor(cfg)
    print("backend:", b.backend, "mode:", b.mode, "enabled:", b.enabled)
    for fn in ("connect", "account", "get_positions"):
        try:
            print(fn, "->", getattr(b, fn)() if fn != "get_positions" else b.adapter.get_positions())
        except Exception as e:  # noqa: BLE001
            print(fn, "-> refused:", type(e).__name__, e)
