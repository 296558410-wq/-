# 机会退化诊断 — V2 生产决策 (2026-09-15, 只读)
范围: 全部 V2 生产 run 的 `decisions/*.raw.json`（策略冻结，未改任何东西）

## 0. 语料
- 生产决策 **151** 条（150 个 decision context）。
- run 分布：a17b(61, 09-11) · 7a88(84, 09-13~14, 数据瞎期) · 5fe2(2, 修复版) · 8618(1) · 早期 smoke(3)。

## 1. 结论（先说）
**是，明显退化。** 但退化由**两层**造成，且**不是（主要）数据问题**：
1. **供给近单一化**：`opp_geo_shock` 在 **148/148 个周期（100%）** 都出现；技术类机会（trend/breakout/false-breakout）**几乎从不出现**。
2. **选择器是确定性占位器**：生产实测 `decision_source=reference_rules`（**不是**设计的 LLM Hermes），按固定优先级只取**一个**候选，且 `requires_confirmation` 类一律 WAIT。
3. 数据瞎期（7a88）**放大**了退化（技术候选连触发条件都算不出），但即便数据正常（a17b）多样性也有限。

## 2. 选择侧（chosen / reason）
| chosen_opportunity | 次数 | 占比 |
|---|---|---|
| opp_geo_shock | 114 | 75.5% |
| opp_macro_repricing_short | 32 | 21.2% |
| opp_fbo_short | 2 | 1.3% |
| (none) | 3 | 2.0% |

- 前 2 类占 **96.7%**；**无** trend / breakout / long 任何一类被选中。
- reason：**"该机会需市场确认(follow-through 未验)" = 136/151 = 90.1%**；其余：技术/宏观冲突 6、已定价 4、数据不新鲜 3、"证据通过门禁" 2。
- regime_tags：GEOPOLITICAL_EVENT **148**、UNCERTAIN 120、MACRO_EVENT 34 …

## 3. 供给侧（候选池，来自 opportunity_ledger ∩ 生产 context）
- 每周期候选数：**0→2, 1→107（72%）, 2→24, 3→15, 4→2**。→ **7 成周期"没得选"，only-one-candidate**。
- 类别出现周期数：`geo_shock 148/148`、`macro_repricing 34`、`narrative_flow 24`、`bo_* 2`、`fbo_* 2`、`trend 0`。

## 4. 结构性根因（代码级，只读定位）
- `discovery.py`：`opp_geo_shock` 只要 `geopolitics.events` 非空就生成（地缘新闻源几乎每轮都有 → 恒生成）；`requires_confirmation=True`。
- 技术类候选条件严格：`trend` 需 `regime=="trend"` 且 ≥3 个 TF `swing_bias` 同向；`breakout`/`false_breakout` 需 15m 特定 `breakout.state` → 很少满足。
- `hermes.py`：`CATEGORY_PRIORITY=[false_breakout,breakout,trend,macro_repricing,geopolitical,narrative_flow]`，**取第一个有候选的类别**；`gate()` 对该候选 `requires_confirmation` → 直接 WAIT（不再看其它候选）。macro_repricing/geopolitical/narrative 全部 `requires_confirmation=True`。
- ⇒ 当唯一候选是 geo_shock（100% 出现）→ 几乎必然 WAIT。
- 且生产 `decision_source="reference_rules"`（占位参照器；docstring 注明生产应为 LLM 编排，Phase-1 用参照器打通链路）。

## 5. 多样性的时间轨迹
- a17b（09-11，数据可用）：geo 35 / macro 24 / fbo 2 → **3 类**（较多样，且出现 2 次 TRADE）。
- 7a88（09-13~14，数据瞎）：geo 79 / macro 5 → **94% geo**（坍缩）。
- 5fe2/8618（修复版，数据恢复）：macro_repricing_short 3/3（样本极小，但方向提示多样性可能回归）。

## 6. 判断
- "机会退化" **成立**，且主要是**结构性**（供给恒有 geo_shock + 占位选择器偏 WAIT），数据瞎期是放大器。
- 这解释了"150 决策 → 148 WAIT、0 成交"：**不是策略在挑选，而是一个恒定的新闻型机会反复撞上"需要确认"的门。**
- **不等于**策略无价值，但说明：现状下 Hermes 的"判断力"没被真正测试（用的是占位器 + 单一机会）。这是**设计/供给问题**，按冻结原则**不擅自改**，标记 ISSUE 交用户裁决。
