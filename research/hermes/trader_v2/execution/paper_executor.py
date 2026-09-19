# -*- coding: utf-8 -*-
"""V2 LOCAL PAPER 执行器（模块 2 最终版）。

独立 paper 账户; 模拟 spread/slippage/latency/commission; LONG/SHORT/SL/TP/close/PnL。
硬门: 仅当 execution_mode == "PAPER" 且 live_trading == False 才工作, 否则 RefuseExecution(code="NON_PAPER_MODE")。
显式 Bid/Ask 语义; 执行前校验 ENTRY_INVALIDATED 与 RISK_LIMIT(拒绝, 不静默缩仓)。
执行输入必须来自冻结的 Hermes 决策/上下文; 本类不读取 Agent1/Agent2, 不修改 entry/SL/TP。
"""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
ACCOUNT_P = STATE / "paper_account.json"
EXECUTIONS_P = STATE / "paper_executions.jsonl"
EXECUTION_MODE = "PAPER"
LIVE_TRADING = False


class RefuseExecution(Exception):
    def __init__(self, code, message=""):
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


class PaperExecutor:
    backend = "paper_local"

    def __init__(self, config=None):
        cfg = config or _load(ROOT / "config" / "v2_config.json", {}) or {}
        ex = cfg.get("execution", {})
        self.cost = ex.get("cost_model", {})
        self.contract = ex.get("contract", {"min_lot": 0.01, "max_lot": 0.05,
                                            "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2})
        self.risk = ex.get("risk", {"per_trade_pct": 1.0, "single_position": True})
        self.mode = ex.get("execution_mode", "PAPER")
        self.live = bool(ex.get("live_trading", False))
        self.initial = float((cfg.get("account") or {}).get("initial_balance", 10000.0))
        self.acc = _load(ACCOUNT_P) or self._fresh()

    # ---------- 安全门 ----------
    def _guard(self):
        if self.mode != "PAPER" or self.live or EXECUTION_MODE != "PAPER" or LIVE_TRADING:
            raise RefuseExecution("NON_PAPER_MODE", f"mode={self.mode} live={self.live}")

    def _p(self, x):
        return round(float(x) + 1e-9, self.contract.get("price_dp", 2))

    def _lots(self, x):
        # FLOOR-TO-STEP: 手数向下取整到 lot step (风险优先, 绝不向上放大)。
        # 保证 floor(raw) <= raw => actual_risk <= target_risk。
        dp = int(self.contract.get("lot_dp", 2))
        step = 10.0 ** (-dp)
        return round(math.floor(float(x) / step + 1e-9) * step, dp)

    def _fresh(self):
        return {"initial_balance": self.initial, "balance": self.initial, "equity": self.initial,
                "cash": self.initial, "margin_used": 0.0, "realized_pnl": 0.0, "unrealized_pnl": 0.0,
                "peak_equity": self.initial, "drawdown": 0.0, "positions": [], "closed_trades": [],
                "created_utc": _now(), "backend": "paper_local", "currency": "USD"}

    def _save(self):
        STATE.mkdir(parents=True, exist_ok=True)
        ACCOUNT_P.write_text(json.dumps(self.acc, indent=1, ensure_ascii=False), encoding="utf-8")

    def _record(self, rec):
        STATE.mkdir(parents=True, exist_ok=True)
        with open(EXECUTIONS_P, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---------- Bid/Ask 语义 ----------
    def _bid_ask(self, mid, spread_bps, bid=None, ask=None):
        if bid is not None and ask is not None:
            return float(bid), float(ask), "REAL"
        half = mid * spread_bps / 1e4 / 2.0
        return self._p(mid - half), self._p(mid + half), "PROXY"   # 无真实盘口 → 用 spread_bps 推导

    def _entry_fill(self, direction, mid, spread_bps, slippage_bps, bid, ask):
        b, a, src = self._bid_ask(mid, spread_bps, bid, ask)
        slip = mid * slippage_bps / 1e4
        if direction == "LONG":       # 买入 → 用 Ask, 再叠加不利滑点
            return self._p(a + slip), b, a, src
        else:                          # 卖出 → 用 Bid, 再叠加不利滑点
            return self._p(b - slip), b, a, src

    def _exit_fill(self, direction, ref_price, spread_bps, slippage_bps, bid, ask):
        """平仓: LONG 用 Bid 出, SHORT 用 Ask 出(均叠加不利滑点)。"""
        b, a, src = self._bid_ask(ref_price, spread_bps, bid, ask)
        slip = ref_price * slippage_bps / 1e4
        if direction == "LONG":
            return self._p(b - slip), src
        else:
            return self._p(a + slip), src

    def _commission(self, qty):
        return float(self.cost.get("commission_per_lot_usd", 0.0)) * qty

    # ---------- 仓位核算(不静默缩仓) ----------
    def size_position_raw(self, entry, sl, equity=None, qty_lots=None):
        if qty_lots is not None:
            return self._lots(qty_lots)
        eq = float(equity if equity is not None else self.acc["equity"])
        dist = abs(entry - sl)
        if dist <= 0:
            return 0.0
        risk_usd = eq * self.risk.get("per_trade_pct", 1.0) / 100.0
        return self._lots(risk_usd / (dist * self.contract["contract_size_oz"]))

    # ---------- 开仓 ----------
    def open(self, direction, mid, sl, tp, plan_id, context_id=None, decision_ref=None,
             symbol="XAUUSD", spread_bps=None, slippage_bps=None, latency_ms=None, qty_lots=None,
             decision_price=None, exec_price=None, invalidation=None, bid=None, ask=None):
        self._guard()
        sb = self.cost.get("spread_bps_typical", 0.35) if spread_bps is None else spread_bps
        slb = self.cost.get("slippage_bps", 0.30) if slippage_bps is None else slippage_bps
        lat = self.cost.get("latency_ms", 250) if latency_ms is None else latency_ms
        dec_px = mid if decision_price is None else decision_price
        exe_px = dec_px if exec_price is None else exec_price
        base = {"plan_id": plan_id, "context_id": context_id, "decision_ref": decision_ref,
                "direction": direction, "symbol": symbol, "requested_entry": self._p(mid),
                "market_price_at_decision": self._p(dec_px), "market_price_at_execution": self._p(exe_px),
                "latency_ms": lat, "invalidation_condition": invalidation, "ts": _now(),
                "spread_bps": sb, "slippage_bps": slb}

        def reject(code, reason):
            rec = dict(base, status="rejected", failure_code=code, rejection_reason=reason)
            self._record(rec)
            return {"ok": False, "status": "rejected", "failure_code": code, "reason": reason, "record": rec}

        # 每 symbol 最多一个 open position
        if any(p.get("symbol", "XAUUSD") == symbol for p in self.acc["positions"]):
            return reject("POSITION_BUSY", f"{symbol} 已有 open position")
        # ENTRY_INVALIDATED: latency 期间价格穿越失效条件 → 拒绝(不允许先成交再止损)
        if invalidation is not None and exe_px is not None:
            inv = invalidation
            if isinstance(inv, dict):
                inv = inv.get("price_cross_up") if direction == "SHORT" else inv.get("price_cross_down")
            if inv is not None:
                if direction == "LONG" and exe_px <= inv:
                    return reject("ENTRY_INVALIDATED", f"exec {exe_px} <= invalidation {inv}(LONG)")
                if direction == "SHORT" and exe_px >= inv:
                    return reject("ENTRY_INVALIDATED", f"exec {exe_px} >= invalidation {inv}(SHORT)")
        # 手数: FLOOR_TO_STEP, 且不低于平台最小手(小账户也可交易); max_lot 仍硬拒(不 clamp)
        fill, b, a, src = self._entry_fill(direction, exe_px, sb, slb, bid, ask)
        dist = abs(fill - sl)
        if dist <= 0:
            return reject("RISK_LIMIT", "stop_distance 0 (SL==entry)")
        min_lot = self.contract["min_lot"]
        qty = self.size_position_raw(fill, sl, qty_lots=qty_lots)
        if qty < min_lot:
            qty = min_lot        # 平台最小手底线: 风险预算不足时按 min_lot 执行
        max_notional = self.risk.get("max_notional_usd", 25000)
        target_risk = self.acc["equity"] * self.risk.get("per_trade_pct", 1.0) / 100.0
        allowed_risk = max(target_risk, min_lot * dist * self.contract["contract_size_oz"])  # 至少允许平台最小手
        notional = qty * fill * self.contract["contract_size_oz"]
        risk_usd = qty * dist * self.contract["contract_size_oz"]
        if qty > self.contract["max_lot"]:
            return reject("RISK_LIMIT", f"position_size {qty} > max_lot {self.contract['max_lot']}")
        if notional > max_notional:
            return reject("RISK_LIMIT", f"notional {notional:.0f} > max {max_notional}")
        if risk_usd > self.acc["equity"] + 1e-6:
            return reject("RISK_LIMIT", f"risk {risk_usd:.2f} > equity {self.acc['equity']:.2f}")
        if risk_usd > allowed_risk + 1e-6:
            return reject("RISK_LIMIT", f"risk {risk_usd:.2f} > allowed {allowed_risk:.2f} (target {target_risk:.2f})")
        comm = self._commission(qty)
        entry_cost = (abs(fill - (b + a) / 2)) * qty * self.contract["contract_size_oz"] + comm
        pid = f"PPOS-{plan_id}"
        pos = {"position_id": pid, "plan_id": plan_id, "context_id": context_id,
               "decision_ref": decision_ref, "symbol": symbol, "direction": direction,
               "qty_lots": qty, "entry": fill, "sl": self._p(sl), "tp": self._p(tp) if tp else None,
               "mid_at_open": exe_px, "spread_bps": sb, "slippage_bps": slb, "latency_ms": lat,
               "spread_source": src, "entry_cost_usd": round(entry_cost, 4), "opened_at": _now(),
               "state": "OPEN", "mfe": 0.0, "mae": 0.0}
        self.acc["positions"].append(pos)
        self.mark(exe_px)
        self._save()
        rec = dict(base, status="filled", position_id=pid, fill_price=fill, qty_lots=qty,
                   entry_cost_usd=round(entry_cost, 4), spread_source=src)
        self._record(rec)
        return {"ok": True, "status": "filled", "position": pos, "fill": fill, "cost": entry_cost, "record": rec}

    def mark(self, mid):
        un = 0.0
        for p in self.acc["positions"]:
            d = (mid - p["entry"]) if p["direction"] == "LONG" else (p["entry"] - mid)
            pnl = d * self.contract["contract_size_oz"] * p["qty_lots"]
            p["unrealized_pnl"] = round(pnl, 4)
            p["mfe"] = round(max(p.get("mfe", 0.0), pnl), 4)
            p["mae"] = round(min(p.get("mae", 0.0), pnl), 4)
            un += pnl
        self.acc["unrealized_pnl"] = round(un, 4)
        self.acc["equity"] = round(self.acc["balance"] + un, 4)
        self.acc["peak_equity"] = round(max(self.acc.get("peak_equity", self.acc["equity"]), self.acc["equity"]), 4)
        self.acc["drawdown"] = round(self.acc["peak_equity"] - self.acc["equity"], 4)
        self._save()

    def check_exits(self, mid, spread_bps=None, slippage_bps=None, bid=None, ask=None):
        self._guard()
        out = []
        for p in list(self.acc["positions"]):
            hit = None
            if p["direction"] == "LONG":
                if p["sl"] is not None and mid <= p["sl"]:
                    hit = ("SL", p["sl"])
                elif p["tp"] is not None and mid >= p["tp"]:
                    hit = ("TP", p["tp"])
            else:
                if p["sl"] is not None and mid >= p["sl"]:
                    hit = ("SL", p["sl"])
                elif p["tp"] is not None and mid <= p["tp"]:
                    hit = ("TP", p["tp"])
            if hit:
                out.append(self.close(p["position_id"], hit[1], reason=hit[0],
                                      spread_bps=spread_bps, slippage_bps=slippage_bps, bid=bid, ask=ask))
        return out

    def close(self, position_id, price, reason="manual", spread_bps=None, slippage_bps=None, bid=None, ask=None):
        self._guard()
        p = next((x for x in self.acc["positions"] if x["position_id"] == position_id), None)
        if not p:
            return {"ok": False, "error": "position_not_found"}
        sb = self.cost.get("spread_bps_typical", 0.35) if spread_bps is None else spread_bps
        slb = self.cost.get("slippage_bps", 0.30) if slippage_bps is None else slippage_bps
        fill, src = self._exit_fill(p["direction"], price, sb, slb, bid, ask)
        comm = self._commission(p["qty_lots"])
        ref_mid = price
        exit_cost = abs(fill - ref_mid) * p["qty_lots"] * self.contract["contract_size_oz"] + comm
        gross = ((fill - p["entry"]) if p["direction"] == "LONG" else (p["entry"] - fill)) \
            * self.contract["contract_size_oz"] * p["qty_lots"]
        net = round(gross - p["entry_cost_usd"] - exit_cost, 4)
        self.acc["balance"] = round(self.acc["balance"] + net, 4)
        self.acc["realized_pnl"] = round(self.acc["realized_pnl"] + net, 4)
        self.acc["positions"] = [x for x in self.acc["positions"] if x["position_id"] != position_id]
        trade = {"position_id": position_id, "plan_id": p["plan_id"], "direction": p["direction"],
                 "qty_lots": p["qty_lots"], "entry": p["entry"], "exit": fill, "reason": reason,
                 "gross_usd": round(gross, 4), "entry_cost_usd": p["entry_cost_usd"],
                 "exit_cost_usd": round(exit_cost, 4), "net_usd": net, "opened_at": p["opened_at"],
                 "closed_at": _now(), "sl": p["sl"], "tp": p["tp"], "latency_ms": p["latency_ms"],
                 "spread_source": src}
        self.acc["closed_trades"].append(trade)
        self.mark(fill)
        self._save()
        self._record({"status": "closed", "position_id": position_id, "reason": reason,
                      "exit_price": fill, "net_usd": net, "ts": _now()})
        return {"ok": True, "trade": trade}

    def account(self):
        return self.acc

    def conservation_ok(self):
        s = sum(t["net_usd"] for t in self.acc["closed_trades"])
        eq_ok = abs((self.acc["balance"] + self.acc["unrealized_pnl"]) - self.acc["equity"]) < 1e-6
        bal_ok = abs((self.initial + s) - self.acc["balance"]) < 1e-6
        return (eq_ok and bal_ok), {"sum_net": round(s, 4), "expected_balance": round(self.initial + s, 4),
                                    "balance": self.acc["balance"], "equity_identity": eq_ok,
                                    "balance_identity": bal_ok}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    pe = PaperExecutor()
    print("backend:", pe.backend, "mode:", pe.mode, "balance:", pe.acc["balance"])
