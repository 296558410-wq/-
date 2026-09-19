# -*- coding: utf-8 -*-
"""V2 — 价格空间转换层（Execution Preparation / Risk Validation）。[P0-01 重定义]

V2 实际交易标的 = **XAUUSD**（signal=execution=XAUUSD）。默认 price_translation = **identity (basis=0)**。
仅当 signal 来源与 execution 参考来源"同标的、不同源"且满足 PIT/fresh/validated 时，才使用 **source_basis_usd**
（不得再称 GC_SPOT_BASIS，除非确实存在 GC=F）。
参考市场 GC=F 仅作 reference_market，不得进入 signal/execution 价格空间。

并在**真正下单前**在 execution space 重新校验 SL/TP/风险/RR/sizing。

铁律（对齐任务书 §二/§五/§十二/§十三）:
- 只做“价格空间换算 + 执行前校验”。**不改** Hermes 决策 / 候选 / 门禁 / 阈值 / confidence /
  expected_R / follow-through / 宏观 / 频次 / WAIT / REJECT 逻辑。
- 属于执行准备层，**不污染 Decision Contract**：Hermes 原始 signal_* 原样保留，另加 execution_*。
- basis = spot − gc（与任务书一致）。注意 Agent1 的 `price_basis.basis_usd = gc − spot = −basis`。
- execution_price = signal_price + basis。
- **fail-closed**：basis 缺失 / 超龄 / 异常跳变 / execution 价格非法(边错误/精度) → 不下单（不猜测、不用常数）。

本模块默认 **不启用**（`config/price_space.json` 的 `enabled=false`）：不启用时调用方不得传入,
从而对正在运行的 run 零影响。

用法（库）:
    import price_space as PS
    rec = PS.prepare(plan, gc_price=..., gc_ts=..., spot_price=..., spot_ts=..., cfg=PS.load_config())
    rec["valid"] -> True(可执行) / False(reject_code 见下)
"""
from __future__ import annotations
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
BASIS_LOG = STATE / "price_space_basis.jsonl"
CONFIG_P = ROOT / "config" / "price_space.json"

CONVERSION_VERSION = "price_space/2.0.0-source-basis"
SIGNAL_INSTRUMENT = "XAUUSD"
EXECUTION_INSTRUMENT = "XAUUSD"
REFERENCE_MARKET = "GC=F"
CONVERSION_FORMULA = ("execution_price = signal_price + source_basis ; "
                      "source_basis = exec_source - signal_source (identity=0 when same instrument+source)")

DEFAULT_CFG = {
    "enabled": False,                     # 默认关闭：不启用则对当前运行零影响
    "signal_instrument": "XAUUSD",
    "execution_instrument": "XAUUSD",
    "reference_market": "GC=F",
    "price_dp": 2,
    "tick_size": 0.01,
    "min_stop_distance_usd": 0.0,         # broker 最小止损距离（execution space）
    "max_basis_age_seconds": 300,         # basis 腿最大允许年龄
    "max_abs_basis_usd": 60.0,            # basis 绝对上限（超过→异常）
    "max_basis_jump_usd": 25.0,           # 相对近期中位数的跳变上限
    "jump_window_hours": 6,
}

# 允许写入账本/执行计划的转换记录字段（均为 additive；不启用时不写）
EVENT_FIELDS = ("signal_instrument", "execution_instrument",
                "signal_entry", "signal_stop_loss", "signal_take_profit",
                "execution_entry", "execution_stop_loss", "execution_take_profit",
                "basis", "basis_method", "basis_source", "basis_ts", "basis_age",
                "source_hash", "conversion_version")


class PriceSpaceError(Exception):
    """执行前价格空间 fail-closed。code ∈ {BASIS_UNAVAILABLE,BASIS_STALE,BASIS_ABS_SANITY,
    BASIS_JUMP,INVALID_EXECUTION_PRICE_SPACE,PRICE_SPACE_ERROR}。"""

    def __init__(self, code, detail=None):
        self.code = code
        self.detail = detail or {}
        super().__init__(f"{code}: {self.detail}")


def load_config(path=None) -> dict:
    cfg = dict(DEFAULT_CFG)
    p = Path(path or CONFIG_P)
    try:
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001  (缺失/损坏 → 默认关闭)
        pass
    return cfg


# ---------------- 工具 ----------------
def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _to_epoch(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception:  # noqa: BLE001
        return None


def _dp(x, dp):
    return round(float(x) + 1e-9, int(dp))


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


# ---------------- basis ----------------
def resolve_basis(*, gc_price, spot_price, gc_ts=None, spot_ts=None, now_ts=None,
                  source="agent1_pair", max_age_s=300, max_abs_usd=60.0,
                  recent_basis=None, max_jump_usd=25.0) -> dict:
    """PIT basis = spot − gc。失败即抛 PriceSpaceError（fail-closed）。"""
    if gc_price in (None, "") or spot_price in (None, ""):
        raise PriceSpaceError("BASIS_UNAVAILABLE", {"gc_price": gc_price, "spot_price": spot_price})
    try:
        gc_price = float(gc_price); spot_price = float(spot_price)
    except (TypeError, ValueError):
        raise PriceSpaceError("BASIS_UNAVAILABLE", {"gc_price": gc_price, "spot_price": spot_price})
    if gc_price <= 0 or spot_price <= 0:
        raise PriceSpaceError("BASIS_UNAVAILABLE", {"reason": "non_positive", "gc": gc_price, "spot": spot_price})

    # 时间对齐/新鲜度：取两条腿中“最旧”的一条计龄（保守）
    gc_e, spot_e = _to_epoch(gc_ts), _to_epoch(spot_ts)
    legs = [t for t in (gc_e, spot_e) if t is not None]
    if not legs or now_ts is None:
        raise PriceSpaceError("BASIS_UNAVAILABLE", {"reason": "missing_timestamp",
                                                    "gc_ts": gc_ts, "spot_ts": spot_ts})
    basis_ts_e = min(legs)
    age = float(now_ts) - basis_ts_e
    if age < -5:  # 未来时间戳 = 数据错误
        raise PriceSpaceError("BASIS_STALE", {"reason": "future_timestamp", "age": age})
    if age > float(max_age_s):
        raise PriceSpaceError("BASIS_STALE", {"age": round(age, 1), "max": max_age_s})

    basis = spot_price - gc_price
    if abs(basis) > float(max_abs_usd):
        raise PriceSpaceError("BASIS_ABS_SANITY", {"basis": round(basis, 4), "max_abs": max_abs_usd})

    if recent_basis and max_jump_usd is not None:
        med = statistics.median(recent_basis)
        if abs(basis - med) > float(max_jump_usd):
            raise PriceSpaceError("BASIS_JUMP", {"basis": round(basis, 4), "median": round(med, 4),
                                                 "max_jump": max_jump_usd, "n_recent": len(recent_basis)})

    return {"basis": round(basis, 4), "basis_method": "spot_minus_gc",
            "basis_source": source, "basis_ts": _now_iso() if basis_ts_e is None else
            datetime.fromtimestamp(basis_ts_e, timezone.utc).isoformat(),
            "basis_age": round(age, 1), "gc_price": gc_price, "spot_price": spot_price,
            "source_hash": _sha({"gc": gc_price, "spot": spot_price, "gc_ts": gc_ts,
                                 "spot_ts": spot_ts, "source": source})}


# ---------------- 换算 ----------------
def convert(direction, entry, sl, tp, basis, dp=2) -> dict:
    """signal → execution（同一 basis 平移）。仅平移，不改方向/距离语义。"""
    d = (direction or "").upper()
    if d not in ("LONG", "SHORT"):
        raise PriceSpaceError("PRICE_SPACE_ERROR", {"reason": "bad_direction", "direction": direction})
    e = _dp(float(entry) + basis, dp)
    s = _dp(float(sl) + basis, dp)
    t = _dp(float(tp) + basis, dp)
    return {"execution_entry": e, "execution_stop_loss": s, "execution_take_profit": t}


def validate_execution(direction, entry, sl, tp, *, live_bid=None, live_ask=None,
                       min_stop_distance=0.0, tick=0.01, dp=2):
    """在 execution space 校验 SL/TP 边 + broker 最小止损距离 + tick/精度。返回 (ok, code, detail)。"""
    d = (direction or "").upper()
    e, s, t = float(entry), float(sl), float(tp)
    det = {}

    def _on_tick(x):
        if not tick:
            return True
        return abs((round(x / tick)) * tick - x) < 1e-6

    for nm, v in (("entry", e), ("sl", s), ("tp", t)):
        if not _on_tick(v):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {"reason": f"{nm}_off_tick", nm: v, "tick": tick}

    stop_dist = abs(e - s)
    targ_dist = abs(t - e)
    det.update({"stop_distance": round(stop_dist, 4), "target_distance": round(targ_dist, 4)})
    if stop_dist <= 0:
        return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "zero_stop_distance"}
    if targ_dist <= 0:
        return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "zero_target_distance"}

    # SL/TP 必须在正确一侧
    if d == "SHORT":
        if not (s > e):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "short_sl_not_above_entry"}
        if not (t < e):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "short_tp_not_below_entry"}
        if live_ask is not None and not (s > float(live_ask)):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "short_sl_at_or_below_market",
                                                           "live_ask": live_ask}
        if live_bid is not None and not (t < float(live_bid)):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "short_tp_at_or_above_market",
                                                           "live_bid": live_bid}
    elif d == "LONG":
        if not (s < e):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "long_sl_not_below_entry"}
        if not (t > e):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "long_tp_not_above_entry"}
        if live_bid is not None and not (s < float(live_bid)):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "long_sl_at_or_above_market",
                                                           "live_bid": live_bid}
        if live_ask is not None and not (t > float(live_ask)):
            return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "long_tp_at_or_below_market",
                                                           "live_ask": live_ask}
    else:
        return False, "INVALID_EXECUTION_PRICE_SPACE", {"reason": "bad_direction", "direction": direction}

    if min_stop_distance and stop_dist < float(min_stop_distance) - 1e-9:
        return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "below_min_stop_distance",
                                                       "min_stop": min_stop_distance}
    if min_stop_distance and targ_dist < float(min_stop_distance) - 1e-9:
        return False, "INVALID_EXECUTION_PRICE_SPACE", {**det, "reason": "tp_below_min_stop_distance",
                                                       "min_stop": min_stop_distance}
    return True, None, det


# ---------------- 组合：完整转换记录 ----------------
def prepare(plan, *, gc_price, gc_ts, spot_price, spot_ts, spot_source="agent1_pair",
            now_ts=None, cfg=None, recent_basis=None, live_bid=None, live_ask=None,
            contract_size_oz=100.0) -> dict:
    """signal plan(GC) → 完整 execution 记录 dict（含 valid / reject_code，永不抛异常给调用方）。

    plan 使用 Hermes 原始字段: direction / entry / stop_loss / take_profit。
    """
    cfg = {**DEFAULT_CFG, **(cfg or {})}
    dp = int(cfg.get("price_dp", 2))
    rec = {
        "conversion_version": CONVERSION_VERSION,
        "conversion_formula": CONVERSION_FORMULA,
        "signal_instrument": cfg.get("signal_instrument", "XAUUSD"),
        "execution_instrument": cfg.get("execution_instrument", "XAUUSD"),
        "valid": False, "reject_code": None, "reject_detail": None,
    }
    try:
        direction = (plan or {}).get("direction")
        entry, sl, tp = (plan or {}).get("entry"), (plan or {}).get("stop_loss"), (plan or {}).get("take_profit")
        rec.update({"signal_entry": entry, "signal_stop_loss": sl, "signal_take_profit": tp})
        if entry is None or sl is None or tp is None:
            raise PriceSpaceError("PRICE_SPACE_ERROR", {"reason": "incomplete_signal_plan"})

        b = resolve_basis(gc_price=gc_price, spot_price=spot_price, gc_ts=gc_ts, spot_ts=spot_ts,
                          now_ts=now_ts, source=spot_source,
                          max_age_s=cfg.get("max_basis_age_seconds", 300),
                          max_abs_usd=cfg.get("max_abs_basis_usd", 60.0),
                          recent_basis=recent_basis, max_jump_usd=cfg.get("max_basis_jump_usd", 25.0))
        conv = convert(direction, entry, sl, tp, b["basis"], dp=dp)
        rec.update(conv)
        rec.update({"basis": b["basis"], "basis_method": b["basis_method"], "basis_source": b["basis_source"],
                    "basis_ts": b["basis_ts"], "basis_age": b["basis_age"], "source_hash": b["source_hash"]})

        ok, code, det = validate_execution(direction, conv["execution_entry"], conv["execution_stop_loss"],
                                           conv["execution_take_profit"], live_bid=live_bid, live_ask=live_ask,
                                           min_stop_distance=cfg.get("min_stop_distance_usd", 0.0),
                                           tick=cfg.get("tick_size", 0.01), dp=dp)
        rec["stop_distance"] = det.get("stop_distance")
        rec["target_distance"] = det.get("target_distance")
        if rec["stop_distance"] and rec["target_distance"]:
            rec["rr"] = round(rec["target_distance"] / rec["stop_distance"], 4)
            rec["risk_usd_per_lot"] = round(rec["stop_distance"] * float(contract_size_oz), 2)
        if not ok:
            raise PriceSpaceError(code, det)
        rec["valid"] = True
        return rec
    except PriceSpaceError as e:
        rec["valid"] = False
        rec["reject_code"] = e.code
        rec["reject_detail"] = e.detail
        return rec
    except Exception as e:  # noqa: BLE001  (绝不把异常抛给下单路径; fail-closed)
        rec["valid"] = False
        rec["reject_code"] = "PRICE_SPACE_ERROR"
        rec["reject_detail"] = {"error": f"{type(e).__name__}:{e}"}
        return rec


# ---------------- basis 历史（用于异常跳变检测；仅在本层启用时写入） ----------------
def record_basis(basis, ts=None, path=None):
    p = Path(path or BASIS_LOG)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ts or _now_iso(), "basis": round(float(basis), 4)}) + "\n")
    except Exception:  # noqa: BLE001
        pass


def recent_basis(window_hours=6, now_ts=None, path=None):
    p = Path(path or BASIS_LOG)
    if not p.exists():
        return []
    now_ts = now_ts if now_ts is not None else datetime.now(timezone.utc).timestamp()
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            o = json.loads(ln)
            t = _to_epoch(o.get("ts"))
            if t is not None and (now_ts - t) <= window_hours * 3600:
                out.append(float(o["basis"]))
        except Exception:  # noqa: BLE001
            continue
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config()
    print("price_space cfg:", json.dumps(cfg, ensure_ascii=False))
    print("enabled:", cfg["enabled"])
    demo = prepare({"direction": "SHORT", "entry": 4351.82, "stop_loss": 4369.23, "take_profit": 4323.96},
                   gc_price=4351.82, gc_ts=_now_iso(), spot_price=4351.82 - 82.52, spot_ts=_now_iso(),
                   now_ts=datetime.now(timezone.utc).timestamp(), cfg={**cfg, "enabled": True})
    print("demo(basis≈-82.52, over max_abs):", json.dumps(demo, ensure_ascii=False))
