# -*- coding: utf-8 -*-
"""stop_authority.py — 唯一 Stop Authority(L2/DESIGN_V11 §4.3)

任何时刻 SL 的唯一权威来源。三种 trailing 逻辑 + 保本, 由本模块仲裁, 规则间不互相覆盖:
- structure: 按价格结构(swing)移动
- volatility: 距离 = k × ATR(自适应)
- profit_protection: 利润状态分级保护
- breakeven: 状态转换(逻辑确认 + 浮盈≥噪声带宽), 非固定 profit>X 规则

优先级(同 DESIGN §3): 由调用方按 决策优先级 传入; 本模块只保证:
- 单次调用只有一个 authority 生效
- 输出 SL 必过 position 层不变量(不扩大风险)
"""
from position import r2, CONTRACT_SPEC


def noise_band_atr(atr_value, k=1.5):
    """噪声带宽(价格单位)= k × ATR。调用方传 ATR(bar 尺度与持仓尺度对齐)。"""
    return round(float(atr_value) * k, 2)


def breakeven_eligible(pos, current_price, atr_value=None, min_profit_ticks=20):
    """保本资格(状态转换): 逻辑确认 + 浮盈 ≥ 保本距离+噪声带宽。"""
    if pos.qty_lots <= 0 or pos.avg_entry is None:
        return False, "no_position"
    if pos.side == "LONG":
        profit = current_price - pos.avg_entry
    else:
        profit = pos.avg_entry - current_price
    noise = noise_band_atr(atr_value) if atr_value else CONTRACT_SPEC["tick_size"] * 5
    threshold = noise + CONTRACT_SPEC["tick_size"] * min_profit_ticks * 0.1
    if profit < threshold:
        return False, f"profit {profit:.2f} < threshold {threshold:.2f}"
    return True, "eligible"


def compute_stop(pos, current_price, authority, params):
    """按 authority 计算新 SL(不直接设置; 返回 {level, authority})。
    params: structure={swing_level}, volatility={atr_value, k}, profit_protection={level},
            breakeven={atr_value}
    返回 None 表示该 authority 当前不适用(调用方保持现状)。
    """
    side = pos.side
    if authority == "structure":
        lvl = params.get("swing_level")
        if lvl is None:
            return None
        lvl = r2(lvl)
        # 结构 SL 合法性: 不得越过均价(LONG SL < avg)
        if side == "LONG" and lvl >= r2(pos.avg_entry - CONTRACT_SPEC["tick_size"]):
            return None
        if side == "SHORT" and lvl <= r2(pos.avg_entry + CONTRACT_SPEC["tick_size"]):
            return None
        return {"level": lvl, "authority": "structure"}
    if authority == "volatility":
        atr = params.get("atr_value")
        k = params.get("k", 1.5)
        if atr is None or pos.avg_entry is None:
            return None
        dist = round(float(atr) * k, 2)
        lvl = r2(pos.avg_entry - dist) if side == "LONG" else r2(pos.avg_entry + dist)
        return {"level": lvl, "authority": "volatility"}
    if authority == "profit_protection":
        lvl = params.get("level")
        if lvl is None:
            return None
        lvl = r2(lvl)
        # 保护性 SL 必须 ≤ 当前已允许范围(由 position 层最终校验)
        return {"level": lvl, "authority": "profit_protection"}
    if authority == "breakeven":
        return {"level": r2(pos.avg_entry), "authority": "breakeven"}
    return None


def select_authority(pos, current_price, priorities):
    """仲裁入口: priorities = [(authority, params), ...] 已按决策优先级降序排列。
    逐个 compute_stop, 返回第一个可用结果; 全不可用 → None。
    调用方(持仓决策)负责在调用前先处理 HARD RISK/INVALIDATION(优先级更高)。"""
    for auth, params in priorities:
        if params is None:
            continue
        res = compute_stop(pos, current_price, auth, params)
        if res is not None:
            return res
    return None
