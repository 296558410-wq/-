# PRICE_SPACE_SHADOW_REPORT — old vs new execution plan（只读）

- 生成: 2026-09-16T23:32:32.291213+00:00
- **有可执行 plan 的历史决策 n = 10**（只有 TRADE 才产出 plan；非 TRADE 无价格计划，无法做 plan-diff → 报告实际 n，不伪造）
- basis 空间样本（所有决策上下文）n = 162
- basis 统计: min=-99.08, max=25.7, median=-2.6, |basis|>0.5 占比=97.5%

## old plan(GC) vs new execution plan(XAUUSD)

| decision_id | old entry | new entry | Δ | old SL | new SL | side-valid(old) | side-valid(new) |
|---|---|---|---|---|---|---|---|
| DEC-ctx_90c83bcaca11 | 4432.1 | 4387.33 | -44.77 | 4449.83 | 4405.06 | OK | OK |
| DEC-ctx_feb7a04dfcd8 | 4434.9 | 4389.33 | -45.57 | 4452.64 | 4407.07 | OK | OK |
| DEC-ctx_30ab864391fa | 4296.81 | 4305.39 | 8.58 | 4314.0 | 4322.58 | OK | OK |
| DEC-ctx_afc5647fbab6 | 4305.52 | 4292.35 | -13.17 | 4322.74 | 4309.57 | OK | OK |
| DEC-ctx_0d750e73b0cf | 4347.77 | 4341.48 | -6.29 | 4365.16 | 4358.87 | OK | OK |
| DEC-ctx_1c8042b9ee65 | 4335.78 | 4263.94 | -71.84 | 4353.12 | 4281.28 | OK | OK |
| DEC-ctx_55b1efd90824 | 4351.82 | 4269.3 | -82.52 | 4369.23 | 4286.71 | OK | OK |
| DEC-ctx_683a6dec351c | 4348.64 | 4335.25 | -13.39 | 4366.03 | 4352.64 | OK | OK |
| DEC-ctx_a463ab883d7a | 4346.7 | 4325.29 | -21.41 | 4364.09 | 4342.68 | OK | OK |
| DEC-ctx_bca0dad1eebb | 4352.65 | 4346.92 | -5.73 | 4370.06 | 4364.33 | OK | OK |
