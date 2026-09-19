# Agent2 Phase-1.5 报告 —— Point-in-Time / Evidence Integrity 加固

> 日期: 2026-09-11 · 范围: `trader_v2/agents/macro_global/*` + `state/evidence_registry.jsonl` + `tests/*`
> 目标: 让 Hermes 未来能证明"当时究竟看到了什么"。**未进入 Hermes V2。V1 只读零改动。**

## 新增/变更
```
agents/macro_global/
├── evidence.py           不可变证据存储 + 统一 Evidence Registry(sha256)
├── release_registry.py   宏观发布/修订登记(观察式) + value_asof(PIT 访问器)
├── agent2.py             ★改: 新闻路由进 evidence; freshness; COT 语义; BLS 接入; evidence 引用块
├── sources.py            ★改: COT 时间语义修正; +BLS/ECB/Treasury 官方源
└── event_trigger.py      ★改: 抽出 evaluate_inputs(可测试纯函数)
tests/
├── test_event_trigger.py 事件触发 A–H + 不可变快照链路
└── test_pit_integrity.py T0/T1 PIT 自测 + 回溯链
产出: state/evidence_registry.jsonl · data_cache/evidence_raw/ · state/macro_releases.jsonl
      logs/test_event_trigger.log · logs/test_pit_integrity.log
```

## 对照需求
1. **新闻正文历史固化** ✅：每条新闻写 `data_cache/evidence_raw/<evidence_id>_<sha12>.json`（只写一次，禁覆盖）；含 event_id/sha256/published_at/retrieved_at/first_seen_at/version。
2. **内容变化新版本** ✅：同 URL 内容变化 → `version+1` + `previous_content_sha256` + `changed_at`；旧版永久保留；同内容重复 → 判重不新增。
3. **统一 Evidence Registry** ✅：`state/evidence_registry.jsonl`，字段 evidence_id/type/source/source_url/published_at/retrieved_at/effective_at/content_sha256/data_sha256/point_in_time_valid。
4. **宏观修订处理** ⚠️ APPROXIMATION：建立了 release_id/period/首次值/最新值/revision_number/revision_timestamp + `value_asof()` PIT 访问器；**仅 BLS 3 序列已接入**，其余宏观源未接（Fed/BEA/BOJ/PBOC 无免 Key 结构化）。
5. **COT 时间语义** ✅：拆分 report_date / publication_date；未获精确发布时刻 → `publication_timestamp_unknown=true`、`timestamp_precision="approximate"`。
6. **财经日历不伪造** ✅：econ 事件 `release_timestamp_source="unavailable"` + `point_in_time_confidence="low"`；不再用新闻时间冒充发布时刻。
7. **官方源接入**：BLS API ✅(免Key)、ECB SDMX ✅、Treasury FiscalData ✅、CFTC COT ✅；Fed/BLS日程 403、BEA 需 Key、BOJ/PBOC 仅站点 → DATA GAP。
8. **事件触发压力测试** ✅ 10/10（A–H 全 PASS，见日志）。
9. **信息新鲜度** ✅：事件态含 `freshness`(fresh/stale/expired/unknown) + `age_seconds`。
10. **signal_guard** ✅ 保留（无 LONG/SHORT/BUY/SELL）。
11. **不扩张数据源** ✅：本轮未加新源，只做"已抓信息可证明"。
12. **PIT 自测** ✅ 5/5：T0 快照字节不变；T0 证据 sha256 不变；snapshot→registry→raw→sha256 可回溯；value_asof 在 T0 看不到 T1 修订。

## 已知 NOT IMPLEMENTED / DATA GAP / APPROXIMATION
- **DATA GAP**: 全球黄金ETF持仓(WGC JS)、央行购金/储备、Fed/BEA/BOJ/PBOC 结构化宏观、官方财经日历发布时刻。
- **APPROXIMATION**: COT 发布时刻；BLS 发布时刻；宏观 revision 仅观察式(BLS)。
- **NOT IMPLEMENTED**: 新闻正文抓取即固化(已存 title/content 摘要与 sha，但未存完整 HTTP body)——当前 payload=结构化摘要，非原始 HTML。
