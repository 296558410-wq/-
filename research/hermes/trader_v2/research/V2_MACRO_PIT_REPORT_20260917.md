# V2 MACRO PIT REPORT — 20260917 (P1-A)

## 问题
- BLS/COT **发布时刻未强制**；ETF flow **as-of 被丢弃**；macro stale/missing 标签不完整；**news 源失败静默**（`default=[]` → 空 = 看起来“没新闻”）；completeness 不明确。

## 修改（agent2.py）
- 新增纯函数：`macro_field_status`(AVAILABLE/MISSING/ERROR)、`news_source_status`(OK/NEWS_SOURCE_ERROR/EMPTY)、`macro_completeness`。
- `collect()`：新闻源改为**显式捕获错误**（`_src`），产出 `news_status`。
- `build()`：`macro.completeness`（DXY/UST10Y/VIX/TIP/BLS/COT/ETF_FLOW_CN/NEWS/GEOPOLITICS 显式标签）、`macro.news_status`、`macro.macro_pit_risk`；快照顶层 `macro_completeness`/`macro_pit_risk`。
- 新闻失败 → `data_gaps += news_<src>:NEWS_SOURCE_ERROR`（可见，不静默）。
- `gold_flows.cot.pit_status` = UNKNOWN（发布时刻未知）/ PASS；`gold_flows.etf.asof` + `publication_ts` + `pit_status`。
- 关键性：`TRADE_CRITICAL_MACRO=(DXY,UST10Y,VIX)`（Hermes gold_macro_state 依赖）；其余 `CONTEXT_ONLY`。

## PIT 语义
- 市场类宏观（DXY/UST10Y/VIX）：`data_ts` 即市场时刻，`pit_status` 由 freshness 决定。
- 发布型（BLS/COT）：`publication_ts` 决定可见性；**当前不可靠 → `PIT_RISK`（不得伪装 PASS）**。
- ETF flow：保留 `asof`（数据所属日）。

## 测试
`tests/test_macro_pit.py` 15/15。

## 行为变化
`BEHAVIOR_CHANGE=TRUE`（数据质量）：news 源失败此前静默、现计入 gaps。

## 遗留
BLS/COT 精确 publication time 仍无可靠源 → PIT_RISK 显式标注（不再伪装）；接入官方发布时刻后转 PASS。
