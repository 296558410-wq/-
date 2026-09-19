# G1 FVT REPLAY COMPARISON（R1' · 2026-09-05）

> 裁决 #1 硬检查：FVT 实现必须与 Phase 5 输出在预定容差内完全一致，否则 G1 FAIL。
> 实现：research/r1prime/replay_phase5.py（逐字节复刻 phase5_voltarget.run 语义）。
> 参考：reports/phase5_voltarget.json · 证据：reports/r1_prime/g1_evidence/g1_evidence.json

## 结果：PASS —— 双窗全部指标相对误差 = 0.0（容差：ann_vol/sharpe/max_dd ≤2%，cost ≤5%）

| 指标 | FXTM_2026_H1 rel diff | DUKA_2023_24_H1 rel diff |
|---|---|---|
| strat ann_vol | 0.0 | 0.0 |
| strat sharpe | 0.0 | 0.0 |
| strat max_dd | 0.0 | 0.0 |
| n_days / n_bars | 0.0 | 0.0 |
| turnover_cost_total_bp | 0.0 | 0.0 |
| vol_forecast_ic_spearman_daily | 0.0 | 0.0 |
| bench ann_vol / sharpe / max_dd | 0.0 | 0.0 |

引擎腿（evaluate.apply_policy，μ=1 & s=FVT）日收益序列 vs Phase 5 日序列：**max diff = 0.0**
（FXTM 与 DUKA 均验证）——即 R1' 腿引擎在无门控时逐字节等价于 Phase 5 FVT，门控增量可干净归因。

## 复刻要点（保证逐位一致）
- vol_f = √(EWM(r², halflife=12, min_periods=12)).shift(1) × √(365×24)；target=0.10；size=clip(·,0,2)
- cost_oneway_bp = spread_bp/2 + 0.1（FXTM 0.36 / DUKA 2.4）；turnover=|Δsize|；ret=size.shift(1)·r − cost
- 日聚合 = 按 UTC 日 groupby sum（skipna）；指标 = ann_ret/vol(365)、sharpe、max_dd、var95、mdd/vol improve
- NaN 语义（warm-up min_periods=12、数据缺口）原样保留 → 与 Phase 5 json 数字完全一致
