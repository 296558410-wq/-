# -*- coding: utf-8 -*-
"""position.py — Hermes Position State Machine + 仓位管理(L1)。

状态机(DESIGN_V11 §2):
  FLAT → ENTRY_PENDING → PARTIALLY_FILLED/OPEN → CONFIRMING → PROFIT_EXPANSION
       → MATURE → EXHAUSTION → EXIT_PENDING → CLOSED
设计要点:
- 状态唯一: position_id 单快照 + 事件日志; 幂等更新
- 非法迁移 → FAIL CLOSED(raise PositionInvariantError, 记录, 冻结新操作)
- 支持: partial fill / partial exit / ADD / REDUCE / CLOSE / reject / restart recovery
- 快照持久化(JSON) = 重启恢复源; 事件日志(ledger 同构 jsonl) = 审计
- 数量与价格: 全部 round 到合约精度(price 2dp, lots 2dp), 见 CONTRACT_SPEC

仓位不变量(设计 §7)内建于迁移: I1 未知状态禁止 / I2 重复平仓拒绝 /
I4 SL 不可向风险增大方向 / I5 SL/TP 价格合法 / I11 CLOSED 终态。
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_DIR = HERE / "run_state" / "positions"

# ---- 合约规格(paper; XAUUSD CFD) ----
CONTRACT_SPEC = {
    "contract_size_oz": 100.0,     # 1 lot = 100 oz
    "price_dp": 2,                 # 价格小数位
    "lot_dp": 2,                   # 手数小数位
    "min_lot": 0.01,
    "max_lot": 50.0,
    "leverage": 500.0,             # 账户杠杆(固定, 风险层不使用它定仓位)
    "margin_pct": 1 / 500.0,       # 1% 保证金比例(1:500)
    "tick_size": 0.01,
}

# 合法迁移表(行=当前态, 值=允许的下一事件类型)
LEGAL_MOVES = {
    "FLAT": {"ENTER"},                             # 触发+risk pass → 进入
    "ENTRY_PENDING": {"FILL", "REJECT", "CANCEL", "TIMEOUT"},
    "PARTIALLY_FILLED": {"FILL", "REJECT_REMAINDER", "CANCEL_REMAINDER"},
    "OPEN": {"CONFIRM", "ADD", "REDUCE", "PARTIAL_EXIT",
             "SET_STOP", "SET_TP", "MOVE_STOP", "MOVE_TP",
             "EXIT_REQUEST", "HARD_STOP_HIT", "HARD_TP_HIT"},
    "CONFIRMING": {"CONFIRM", "ADD", "REDUCE", "PARTIAL_EXIT",
                   "SET_STOP", "SET_TP", "MOVE_STOP", "MOVE_TP",
                   "EXIT_REQUEST", "HARD_STOP_HIT", "HARD_TP_HIT",
                   "INVALIDATE"},
    "PROFIT_EXPANSION": {"REDUCE", "PARTIAL_EXIT", "SET_STOP", "SET_TP", "MOVE_STOP",
                         "MOVE_TP", "EXIT_REQUEST", "HARD_STOP_HIT", "HARD_TP_HIT",
                         "MATURE", "INVALIDATE"},
    "MATURE": {"REDUCE", "PARTIAL_EXIT", "MOVE_STOP", "MOVE_TP", "EXIT_REQUEST",
               "HARD_STOP_HIT", "HARD_TP_HIT", "EXHAUST", "INVALIDATE"},
    "EXHAUSTION": {"EXIT_REQUEST", "HARD_STOP_HIT", "HARD_TP_HIT"},
    "EXIT_PENDING": {"EXIT_FILL", "EXIT_REJECT", "CANCEL_EXIT"},
    "CLOSED": set(),                                 # 终态
}

# 事件 → 目标状态
EVENT_TARGET = {
    "ENTER": "ENTRY_PENDING", "FILL": "OPEN", "REJECT": "FLAT",
    "CANCEL": "FLAT", "TIMEOUT": "FLAT", "REJECT_REMAINDER": "OPEN",
    "CANCEL_REMAINDER": "OPEN", "CONFIRM": "OPEN",
    "ADD": "OPEN", "REDUCE": "OPEN", "PARTIAL_EXIT": "OPEN",
    "SET_STOP": "OPEN", "SET_TP": "OPEN", "MOVE_STOP": "OPEN", "MOVE_TP": "OPEN",
    "EXIT_REQUEST": "EXIT_PENDING", "HARD_STOP_HIT": "EXIT_PENDING",
    "HARD_TP_HIT": "EXIT_PENDING", "EXIT_FILL": "CLOSED",
    "EXIT_REJECT": "OPEN", "CANCEL_EXIT": "OPEN",
    "INVALIDATE": "EXIT_PENDING", "MATURE": "MATURE", "EXHAUST": "EXHAUSTION",
}


class PositionError(Exception):
    pass


class PositionInvariantError(PositionError):
    """不变量破坏 → FAIL CLOSED。"""


def _now():
    return datetime.now(timezone.utc).isoformat()


def r2(x):
    return round(float(x) + 1e-9, 2)  # 价格 2dp(防浮点)


def rlots(x):
    return round(float(x) + 1e-9, 2)  # 手数 2dp


class Position:
    def __init__(self, position_id, plan_id, side, entry_zone=None, stop_level=None,
                 tp_levels=None):
        self.position_id = position_id
        self.plan_id = plan_id
        self.side = side                     # "LONG" | "SHORT"
        self.state = "FLAT"
        self.qty_lots = 0.0                  # 当前持仓手数
        self.avg_entry = None                # 加权均价
        self.initial_stop = stop_level
        self.stop_level = stop_level
        self.tp_levels = tp_levels or []     # [{price, frac}] frac 累计
        self.tp_filled_frac = 0.0            # 已实现止盈比例
        self.entry_zone = entry_zone or {}
        self.events = []
        self.created_utc = _now()
        self.mfe = 0.0                       # max favorable (R 或价格, 用价格)
        self.mae = 0.0
        self.stop_authority = "initial"      # initial|structure|volatility|profit|hard
        self.thesis_status = "active"        # active|weakened|invalidated
        self.fail_closed = False
        self._log("CREATED", {"side": side})

    # ---------- 内部 ----------
    def _log(self, event, payload=None):
        rec = {"ts": _now(), "event": event, "position_id": self.position_id,
               "state": self.state, "payload": payload or {}}
        self.events.append(rec)

    def snapshot(self):
        """完整快照(持久化/恢复用)。"""
        return {k: v for k, v in self.__dict__.items()}

    def restore(self, snap):
        for k, v in snap.items():
            setattr(self, k, v)
        return self

    def _require(self, event):
        if self.fail_closed:
            raise PositionInvariantError(f"FAIL_CLOSED: position {self.position_id} frozen")
        allowed = LEGAL_MOVES.get(self.state, set())
        if event not in allowed:
            raise PositionInvariantError(
                f"illegal_transition:{self.state}->{event} (position {self.position_id})")
        return True

    def _move(self, event, target, payload=None):
        self._require(event)
        self.state = target
        self._log(event, payload)
        self._persist()

    # ---------- 生命周期 ----------
    def enter(self, ref_price=None):
        self._move("ENTER", "ENTRY_PENDING", {"ref": ref_price})

    def fill(self, price, qty_lots):
        """成交(可能 partial)。第一笔成交建立仓位; 后续成交累计(试探仓/分批)。
        状态语义: ENTRY_PENDING 下首次成交若未达计划量 → PARTIALLY_FILLED;
        达计划量(由调用方判定 full) → OPEN。add() 内直接累计不重复设态。"""
        self._require("FILL")
        price = r2(price)
        qty_lots = rlots(qty_lots)
        if qty_lots <= 0:
            raise PositionInvariantError("fill qty<=0")
        new_qty = rlots(self.qty_lots + qty_lots)
        if new_qty > CONTRACT_SPEC["max_lot"]:
            raise PositionInvariantError(f"max_lot exceeded: {new_qty}")
        if self.avg_entry is None:
            self.avg_entry = price
        else:
            self.avg_entry = r2((self.avg_entry * self.qty_lots + price * qty_lots) / new_qty)
        self.qty_lots = new_qty
        if self.state == "ENTRY_PENDING" and self.qty_lots > 0:
            self.state = "OPEN"
        elif self.state == "PARTIALLY_FILLED" and self.qty_lots >= CONTRACT_SPEC["min_lot"]:
            self.state = "OPEN"
        self._log("FILL", {"price": price, "qty": qty_lots, "avg": self.avg_entry})
        self._persist()

    def partial_entry(self, price, qty_lots):
        """部分成交: 进 PARTIALLY_FILLED(仍在等待剩余成交)。"""
        self._require("FILL")
        price, qty_lots = r2(price), rlots(qty_lots)
        if qty_lots <= 0:
            raise PositionInvariantError("fill qty<=0")
        self.avg_entry = price if self.avg_entry is None else self.avg_entry
        self.qty_lots = rlots(self.qty_lots + qty_lots)
        if self.state == "ENTRY_PENDING":
            self.state = "PARTIALLY_FILLED"
        self._log("FILL", {"price": price, "qty": qty_lots, "partial": True,
                            "avg": self.avg_entry})
        self._persist()

    def reject(self, reason="order_rejected"):
        """订单被拒(无成交)→ FLAT。"""
        if self.qty_lots == 0:
            self._move("REJECT", "FLAT", {"reason": reason})
        else:
            self._move("REJECT_REMAINDER", "OPEN", {"reason": reason})

    def set_stop(self, level, authority="initial", allow_breakeven=False):
        """设/移止损。I4: 不允许向风险增大方向移动。
        LONG: 新 SL 必须 >= 旧 SL; SHORT 反向。authority 需一致。
        allow_breakeven=True: 允许 SL == entry(保本状态); 否则 SL 必须严格优于 entry 侧。"""
        level = r2(level)
        old = self.stop_level
        if old is not None:
            if self.side == "LONG" and level < old - CONTRACT_SPEC["tick_size"]:
                raise PositionInvariantError(f"stop widening LONG: {old}->{level}")
            if self.side == "SHORT" and level > old + CONTRACT_SPEC["tick_size"]:
                raise PositionInvariantError(f"stop widening SHORT: {old}->{level}")
        # 价格合法性: 相对 entry。保本允许 == entry; 非保本须留至少 1 tick 距离
        if self.avg_entry is not None:
            if self.side == "LONG":
                limit = r2(self.avg_entry) if allow_breakeven else \
                    r2(self.avg_entry - CONTRACT_SPEC["tick_size"])
                if level > limit:
                    raise PositionInvariantError(
                        f"stop must be <= {limit} (entry={self.avg_entry}, be={allow_breakeven})")
            if self.side == "SHORT":
                limit = r2(self.avg_entry) if allow_breakeven else \
                    r2(self.avg_entry + CONTRACT_SPEC["tick_size"])
                if level < limit:
                    raise PositionInvariantError(
                        f"stop must be >= {limit} (entry={self.avg_entry}, be={allow_breakeven})")
        self.stop_level = level
        self.stop_authority = authority
        self._move("MOVE_STOP" if old is not None else "SET_STOP",
                   "OPEN" if self.state in ("OPEN", "CONFIRMING") else self.state,
                   {"level": level, "authority": authority})

    def set_tp(self, levels):
        """设止盈 levels=[{price,frac}], frac 累计 ≤1。"""
        tot = sum(float(x.get("frac", 0)) for x in levels)
        if tot > 1.0 + 1e-9:
            raise PositionInvariantError("TP total frac > 1")
        self.tp_levels = [{"price": r2(x["price"]), "frac": float(x.get("frac", 0))}
                          for x in levels]
        self._log("SET_TP", {"levels": self.tp_levels})
        self._persist()

    def mark(self, price):
        """每轮按市价更新 MFE/MAE(用于决策与 Dashboard)。不迁移状态。"""
        if self.fail_closed:
            raise PositionInvariantError(f"FAIL_CLOSED: position {self.position_id} frozen")
        price = r2(price)
        if self.avg_entry is None or self.qty_lots <= 0:
            return
        if self.side == "LONG":
            fav = price - self.avg_entry
            adv = self.avg_entry - price
        else:
            fav = self.avg_entry - price
            adv = price - self.avg_entry
        self.mfe = max(self.mfe, fav)
        self.mae = max(self.mae, adv)
        self._persist()

    def pnl_at(self, price):
        """浮盈 USD(未实现; 平仓部分除外)。"""
        if self.avg_entry is None or self.qty_lots <= 0:
            return 0.0
        diff = (price - self.avg_entry) if self.side == "LONG" else (self.avg_entry - price)
        return diff * CONTRACT_SPEC["contract_size_oz"] * self.qty_lots

    def partial_exit(self, price, qty_lots, reason="partial_tp"):
        """部分平仓: 减 qty; 若减到 0 且非最终 → 不合法(应走 full exit)。"""
        self._require("PARTIAL_EXIT")
        qty_lots = rlots(qty_lots)
        if qty_lots <= 0 or qty_lots > self.qty_lots:
            raise PositionInvariantError(f"partial_exit qty invalid: {qty_lots} of {self.qty_lots}")
        if qty_lots >= self.qty_lots:
            raise PositionInvariantError("partial_exit qty >= total; use full exit")
        realized = (price - self.avg_entry) * CONTRACT_SPEC["contract_size_oz"] * qty_lots \
            if self.side == "LONG" else \
            (self.avg_entry - price) * CONTRACT_SPEC["contract_size_oz"] * qty_lots
        self.qty_lots = rlots(self.qty_lots - qty_lots)
        self._move("PARTIAL_EXIT", "OPEN", {"price": r2(price), "qty": qty_lots,
                                            "realized_usd": round(realized, 2), "reason": reason})

    def add(self, price, qty_lots, ev_justification):
        """加仓(ADD)。铁律: 仅当 EV 上升 + 有理由; Risk 层已验。禁摊平(引擎层拒绝亏损加仓)。"""
        self._require("ADD")
        if self.qty_lots <= 0:
            raise PositionInvariantError("ADD on zero position")
        # 禁摊平: 加仓价不得比当前均价更差(摊平检测)
        if self.side == "LONG" and price < r2(self.avg_entry - 1e-9):
            raise PositionInvariantError("ADD below avg (averaging down) forbidden")
        if self.side == "SHORT" and price > r2(self.avg_entry + 1e-9):
            raise PositionInvariantError("ADD above avg (averaging up) forbidden")
        if not ev_justification:
            raise PositionInvariantError("ADD without EV justification")
        price, qty_lots = r2(price), rlots(qty_lots)
        new_qty = rlots(self.qty_lots + qty_lots)
        if new_qty > CONTRACT_SPEC["max_lot"]:
            raise PositionInvariantError(f"max_lot exceeded: {new_qty}")
        self.avg_entry = r2((self.avg_entry * self.qty_lots + price * qty_lots) / new_qty)
        self.qty_lots = new_qty
        self._log("ADD", {"price": price, "qty": qty_lots, "just": ev_justification})
        self._persist()

    def request_exit(self, reason):
        self._move("EXIT_REQUEST", "EXIT_PENDING", {"reason": reason})

    def hard_stop_hit(self, price):
        self._move("HARD_STOP_HIT", "EXIT_PENDING", {"price": r2(price)})

    def hard_tp_hit(self, price, frac=1.0):
        self._move("HARD_TP_HIT", "EXIT_PENDING", {"price": r2(price), "frac": frac})

    def exit_fill(self, price, qty_lots=None, reason="exit"):
        """平仓成交 → CLOSED。qty 缺省=全平。重复平仓拒绝(I3)。"""
        if self.state == "CLOSED":
            raise PositionInvariantError(f"already closed: {self.position_id}")
        self._require("EXIT_FILL")
        qty = rlots(qty_lots if qty_lots is not None else self.qty_lots)
        if qty <= 0 or qty > self.qty_lots:
            raise PositionInvariantError(f"exit qty invalid: {qty} of {self.qty_lots}")
        price = r2(price)
        realized = (price - self.avg_entry) * CONTRACT_SPEC["contract_size_oz"] * qty \
            if self.side == "LONG" else \
            (self.avg_entry - price) * CONTRACT_SPEC["contract_size_oz"] * qty
        self.qty_lots = rlots(self.qty_lots - qty)
        self.state = "CLOSED"
        self._log("EXIT_FILL", {"price": price, "qty": qty, "realized_usd": round(realized, 2),
                                "reason": reason})
        self._persist()
        return round(realized, 2)

    def exit_reject(self, reason="exit_rejected"):
        self._move("EXIT_REJECT", "OPEN", {"reason": reason})

    def mark_state(self, new_state, event):
        """显式状态推进(CONFIRMING→OPEN / →PROFIT_EXPANSION / MATURE / EXHAUSTION)。"""
        self._require(event)
        self.state = EVENT_TARGET.get(event, new_state)
        self._log(event, {})
        self._persist()

    # ---------- 持久化 / 恢复 ----------
    def _persist(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        p = STATE_DIR / f"{self.position_id}.json"
        p.write_text(json.dumps(self.snapshot(), indent=1, ensure_ascii=False), encoding="utf-8")

    def to_dict(self):
        return {"position_id": self.position_id, "plan_id": self.plan_id, "side": self.side,
                "state": self.state, "qty_lots": self.qty_lots, "avg_entry": self.avg_entry,
                "stop_level": self.stop_level, "tp_levels": self.tp_levels,
                "mfe": self.mfe, "mae": self.mae, "stop_authority": self.stop_authority,
                "thesis_status": self.thesis_status, "fail_closed": self.fail_closed,
                "created_utc": self.created_utc, "events_n": len(self.events)}


def load_position(position_id):
    """从快照恢复(重启恢复)。"""
    p = STATE_DIR / f"{position_id}.json"
    if not p.exists():
        return None
    snap = json.loads(p.read_text(encoding="utf-8"))
    pos = Position(snap["position_id"], snap["plan_id"], snap["side"])
    pos.restore(snap)
    return pos


def open_positions():
    """全部未 CLOSED 仓位(恢复/管理/审计)。"""
    out = []
    if not STATE_DIR.exists():
        return out
    for p in STATE_DIR.glob("*.json"):
        try:
            snap = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if snap.get("state") != "CLOSED" and not snap.get("fail_closed"):
            out.append(snap)
    return out
