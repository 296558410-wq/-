# Agent2 独立审计报告

> 日期: 2026-09-11 · 范围: `trader_v2/agents/macro_global/*` 与其产出 `state/agent2_latest.json`
> 方法: 真取内容验证 + 代码逐段检查。**只审计 Agent2；不含交易信号。**

## 0. 代码/目录变化
```
trader_v2/agents/macro_global/
├── sources.py        采集层(行情/COT/国内黄金ETF流/新闻) + 来源分级 + 关键词分类
├── agent2.py         快照组装(宏观/地缘/资金流/narrative-vs-flow/方向性压力/冲突/缺口)
└── event_trigger.py  事件触发刷新器(指标异动 + 高影响新闻)
产出: state/agent2_latest.json + state/snapshots/agent2_<cycle>.json + state/agent2_trigger.json
```

## 1. 数据源: 哪些是真实验证可用？
| 源 | 已实测 | 返回内容 |
|---|---|---|
| Yahoo chart (DX-Y.NYB/^TNX/^VIX/TIP/GLD/GC=F) | ✅ 200 | 真实点位+1d%变化 |
| CFTC Socrata COT (6dca-aqww.json, filter GOLD) | ✅ 200 | 真实 OI / 非商业净持仓 |
| 东财 国内黄金ETF 资金流 (518880/159934) | ✅ 200 | 当日主力净流入(元) |
| 华尔街见闻 lives API | ✅ 200 JSON | 实时快讯 |
| CNBC RSS | ✅ 200 XML | 英文快讯(含 CPI 头条) |
| 美国财政部/ECB/PBC/SGE 站点 | ✅ 200 | 可达(尚未结构化入库) |

## 2. 哪些字段只是占位？
- `macro.central_banks.{fed,ecb,boj,pboc}` 政策利率 = **null(placeholder)**
- `gold_flows.central_bank.{purchases,reserves}` = **null**
- `gold_flows.etf.global_etf_holdings`(WGC 全球 ETF) = **null**
- `gold_flows.comex.price` = null(OI 有, 价格未接)
- 均已在 `data_gaps` 明确登记。

## 3. 哪些数据存在延迟？
- **COT**: 周报(截至周二持仓, 周五发布) → 最长 ~7 天“存量”延迟。
- **国内黄金ETF净流**: 东财当日口径(盘后确定)。
- **央行购金/储备**: 月频披露(WGC/PBC) → 未接。
- **新闻**: 秒~分钟级; 但“新闻出现”晚于“事件发生”。

## 4. 哪些数据存在修订？
- 宏观经济数据(CPI/GDP/PCE/NFP)有后续修订; **当前只记录快照值, 未维护修订链** → 已在风险中列出。
- CFTC COT 偶有周度修订, 未跟踪。

## 5. 哪些无法严格 PIT？
- **无免 Key 财经日历** → 事件“发布瞬间”用“新闻出现”近似(分钟级误差)。
- COT `published_at` 用 report_date 近似(未精确到周五 15:30 ET)。
- 国内 ETF 净流无精确发布时刻(按当日)。
→ 已记录; “新闻发布≠事件发生≠市场反应”在 `point_in_time.note` 声明。

## 6. 地缘政治是否存在新闻更新污染？
**存在风险**。当前仅存“当前快照”, 新闻正文若被后续更新, 历史回看时可能看到更新版。
→ 缓解: 已做**版本化 snapshot**(每 cycle 一份), 但**正文级版本留存仍未做**; 进 Hermes 前需补“抓取即固化原文哈希”。

## 7. ETF/COT 是否使用了当时实际可获得的数据？
- COT: 用 `report_date` 截止的周报(符合 PIT)✅
- 国内黄金ETF净流: 用当日实时值(符合)✅
- 全球 ETF: 未取(不适用)

## 8. 事件触发是否真能绕过 60m 周期？
**能**。`event_trigger.py` 独立于 Agent2 周期; 实测已 `trigger=true`(UST10Y +3.82% / VIX +12.22% / 多条地缘新闻)。
编排层将据此**立即重刷 Agent2 → 通知 Hermes**。局限: 事件“发布瞬间”仍依赖新闻出现。

## 9. Agent2 是否偷偷生成了交易信号？
**否**。无 `LONG/SHORT/BUY/SELL` 输出; `gold_macro_state` 仅为**方向性压力标签**(BULLISH/BEARISH/NEUTRAL/UNCERTAIN);
快照含 `signal_guard` 字段自证。交易判断留给 Hermes V2。

## 10. 是否存在未来信息进入 snapshot 的问题？
- 行情序列: Yahoo 已剔除未收盘 bar ✅; 报价带 data_ts/retrieved_at ✅。
- 新闻: 无历史版本 → **存在“事后更新污染历史”的结构性风险**(见 #6) → 列为待办。
- 未使用任何“数据库已更新”的后见信息。

## 结论
Agent2 达 Phase-1 “可运行 + 可记录 + 信息链完整”，**未越界产生信号**；主要缺口集中在
**央行政策/购金、全球 ETF 流量、财经日历、新闻历史版本固化**（4 项，均已登记）。
