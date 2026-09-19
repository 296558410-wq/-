# PRICE_SPACE_IMPACT_REPORT — 历史 replay 影响评估（只读）

- 生成: 2026-09-16T23:32:32.290212+00:00
- 换算: `execution = signal + basis`, `basis = spot − gc`; spot 参照 = ctx(primary_last − basis_usd)
- 守卫: max_abs_basis_usd=60.0, max_basis_jump_usd=30.0, max_basis_age_seconds=300
- 样本: 含可执行 plan 的历史 TRADE 决策 **n=10**；已成交 n=3；10016 n=2
- basis 观测样本(所有决策上下文) n=162

## 逐笔

| decision_id | side | GC entry | GC SL | GC TP | plan_rr | 历史成交 | 历史实际风险 | 历史实际RR | basis | 换算 entry | 换算 SL | 换算 TP | 无守卫 | 带守卫 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DEC-ctx_90c83bcaca11 | SHORT | 4432.1 | 4449.83 | 4403.73 | 1.6 | RISK_LIMIT | - | - | -44.77 | 4387.33 | 4405.06 | 4358.96 | OK | OK |
| DEC-ctx_feb7a04dfcd8 | SHORT | 4434.9 | 4452.64 | 4406.52 | 1.6 | RISK_LIMIT | - | - | -45.57 | 4389.33 | 4407.07 | 4360.95 | OK | OK |
| DEC-ctx_30ab864391fa | SHORT | 4296.81 | 4314.0 | 4269.31 | 1.6 | 4305.53 | 8.47 | 4.276 | 8.58 | 4305.39 | 4322.58 | 4277.89 | OK | OK |
| DEC-ctx_afc5647fbab6 | SHORT | 4305.52 | 4322.74 | 4277.97 | 1.6 | 4292.6 | 30.14 | 0.485 | -13.17 | 4292.35 | 4309.57 | 4264.8 | OK | OK |
| DEC-ctx_0d750e73b0cf | SHORT | 4347.77 | 4365.16 | 4319.95 | 1.6 | 4339.04 | 26.12 | 0.731 | -6.29 | 4341.48 | 4358.87 | 4313.66 | OK | OK |
| DEC-ctx_1c8042b9ee65 | SHORT | 4335.78 | 4353.12 | 4308.04 | 1.6 | BROKER_REJECT_10016 | - | - | -71.84 | 4263.94 | 4281.28 | 4236.2 | OK | BASIS_ABS_SANITY |
| DEC-ctx_55b1efd90824 | SHORT | 4351.82 | 4369.23 | 4323.96 | 1.6 | BROKER_REJECT_10016 | - | - | -82.52 | 4269.3 | 4286.71 | 4241.44 | OK | BASIS_ABS_SANITY |
| DEC-ctx_683a6dec351c | SHORT | 4348.64 | 4366.03 | 4320.82 | 1.6 | POSITION_BUSY | - | - | -13.39 | 4335.25 | 4352.64 | 4307.43 | OK | OK |
| DEC-ctx_a463ab883d7a | SHORT | 4346.7 | 4364.09 | 4318.88 | 1.6 | POSITION_BUSY | - | - | -21.41 | 4325.29 | 4342.68 | 4297.47 | OK | BASIS_JUMP |
| DEC-ctx_bca0dad1eebb | SHORT | 4352.65 | 4370.06 | 4324.79 | 1.6 | POSITION_BUSY | - | - | -5.73 | 4346.92 | 4364.33 | 4319.06 | OK | OK |

## 汇总（任务书 §十 指标）

- 历史 TRADE 总数: **10**
- 原始有效订单数(成交): 3
- 转换后有效订单数(无守卫): 10
- 转换后无效订单数(无守卫): 0
- 原始 broker rejection: 7（其中 10016 = 2）
- 理论上可避免的 10016: 2/2（换算后落到执行价空间正确一侧；见逐笔 换算 SL/TP）
- R:R 改变数量(实际 vs 计划): 3
- risk_pct 改变数量(实际 vs 计划): 3
- 超过风险上限数量(历史实际 risk_pct>2.0% @$1000): 2
- volume 改变数量: 0（平移不改变止损距离→sizing 不变）
- TRADE→REJECT(带守卫 fail-closed): 3
- TRADE→WAIT: 0（本层不改策略；仅执行层拒绝）

## 结论

1. 历史 3/3 成交的“计划 vs 成交”均 MISMATCH（含既有审计 2/2）：实际 R:R 0.485 / 4.276 / 0.731（设计均 1.60）。
2. 2 笔 10016 完全可由价格空间错配解释：GC 计划整体高于执行现货 ~72–83 USD → 对 SHORT 其 TP 落到市价上方。
3. 纯换算(无守卫)可把这 2 笔落到执行价空间正确一侧（10016 可避免）；但守卫(abs/jump)会把它们 fail-closed（更保守）——
   因为该 basis 相对近期中位数属异常跳变(§五规则9)。
4. 原始 ledger / run_state / 历史成交 **未被修改**。
