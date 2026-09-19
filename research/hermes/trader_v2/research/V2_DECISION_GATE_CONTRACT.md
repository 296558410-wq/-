# V2 DECISION GATE CONTRACT

`hermes.gate(cand, ctx, a2, a1)` 顺序（代码为准，`hermes/hermes.py`）。硬门禁 vs 软条件标注。

| # | 输入 | 条件 | 输出 | 类型 |
|---|---|---|---|---|
| G1 | ctx.agent1/2.freshness | expired/unknown | WAIT | 硬（数据） |
| G2 | ctx.health.overall_status | FAIL | REJECT | 硬（数据，P0-04） |
| G2b | 同上 | DEGRADED | WAIT | 硬（数据，P0-04） |
| G3 | a2.macro_status | != OK | WAIT | 硬（数据，P0-03） |
| G4 | cand | is None | WAIT | 软（无机会） |
| G5 | cand.dir_hint | is None | WAIT | 软 |
| G6 | dir vs a2.gold_macro_state | 冲突 | WAIT | 软（证据冲突） |
| G7 | cand.priced_in | HIGH | WAIT | 软 |
| G8 | cand.requires_confirmation | true | WAIT | 软 |
| G9 | 15m range60 pos_pct | 追高/追空极值 | REJECT | 软（R:R） |
| G10 | expected_R_est | < 1.0 | REJECT | 软（R:R） |
| G11 | counter_thesis | 缺失 | REJECT | 软 |
| G12 | — | 其余 | TRADE | — |

## 规则
- 数据质量门（G1/G2/G3）**先于**策略门（G4–G11）；任何数据质量问题**不得**被默认值绕过。
- 无 hidden gate：G 全部列于上表（与代码一一对应）。
- G1/G2/G3 为 P0 修复新增/强化的 fail-closed 数据门；属**数据质量**（非策略）。
- config 与代码阈值一致（`MIN_EXPECTED_R=1.0` 于 hermes.py）；无 config 覆盖。

## 行为变化
`BEHAVIOR_CHANGE = TRUE`：数据缺失/降级现在会 WAIT/REJECT（此前可能因 snapshot 生成时刻被判 fresh 而继续）。**非策略变更**。
