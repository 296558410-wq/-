# BASELINE_AUDIT_20260914.md — V2 数据层加固 基线审计（只读）

> 任务：V2 数据基础设施加固（中国大陆可达多通道 + 本地兜底）。本文件=基线，改动前记录。
> 时间：2026-09-14 18:5x GMT+8（10:5xZ）。

## 0. BASE_COMMIT
- `BASE_COMMIT = fb64d17895e522c0c044e8e0d6d853f6ba33b9f2`
  （= 今天 07:18 的 V2 dashboard app.js 修复提交；其后无新提交）
- `git status --short` 计数：**576** 项（几乎全为 **runtime 产物**：V2 run state / V1 run_state / money_hunter drift 等；另有少量历史 untracked 探针脚本 `research/hermes/trader_v1/_*.py`）。**无未提交的源码逻辑改动**。

## 1. 运行状态（改动前）
- V2 run：`V2-PAPER-20260913-224157-7a88` RUNNING（09-13T22:41:57Z → 09-14T22:41:57Z），execution_mode=BROKER_DEMO，demo ******，magic=90003。
- V1：引擎 cron `hermes-trader-m15-cycle` 正常；面板 8787/8788/8790 均 200；MT5×2 在。
- 采集：`hermes-tick-collect` 正常。

## 2. 数据源清单（source inventory）
### Agent1 技术层 — `agents/technical/market_data.py`
- **历史 K 线（单源）**：`fetch_history()` / `snapshot_history()` → **Yahoo chart**（`query1.finance.yahoo.com/v8/finance/chart/GC=F`）5m/15m/60m/1d，4h 由 60m 派生（`resample_bars`）。
- **现价（多源）**：`QUOTE_ROUTES` — gold_spot/gold_comex/silver=新浪(hf_XAU/hf_GC/hf_SI)→腾讯；dxy=东财(100.UDI)→Yahoo(DX-Y.NYB)；ust10y/vix=Yahoo；gld=腾讯(usGLD)→Yahoo。
### Agent2 宏观层 — `agents/macro_global/sources.py`
- `yahoo_kv`（DXY/UST10Y 等，Yahoo，单源）；`cftc_cot_gold`（CFTC Socrata）；`bls_series`（BLS API）；`ecb_sdmx`（ECB）；`treasury_fiscaldata`（美财政部）；`em_flow`（东财 ETF 资金流）；`news_wallstcn`（华尔街见闻）；`news_cnbc_rss`（CNBC RSS）。
- 其它：`release_registry.py`/`evidence.py`/`event_trigger.py`。
- 取不到→`null + data_gap`（当前无 freshness 分级、无缓存语义）。

## 3. 当前数据 schema（关键）
- Agent1：`timeframes{tf:{n_bars,state}}`、`quotes{key:{price,bid,ask,spread,data_ts,source,errors}}`、`market_regime`、`key_levels`、`deterministic_candidates`、`volatility`、`data_quality{gaps,by_tf,sources}`、`point_in_time`。
- Agent2：`macro`、`geopolitics`、`gold_flows`、`narrative_vs_flow`、`gold_macro_state`、`key_evidence`、`conflicts`、`risks`、`data_gaps`、`evidence`、`point_in_time`、`signal_guard`。

## 4. 当前失败模式（run 7a88 暴露）
- **Agent1 技术层全瞎**：5m/15m/60m/4h/1d **n_bars=0**；`HTTPError:403 Forbidden` @ Yahoo chart（query1/query2 实测均 403，UA 伪装无效）。**自 2026-09-12 ~04:00Z 起**（上一轮 run a17b 中段），今日整轮延续。
- **现价部分缺**：DXY/UST10Y/VIX/GLD = null（Yahoo/eastmoney 失败）；仅 sina XAU/GC/SI 可用。
- **Agent2 宏观 6 缺口持久**：real_rates(TIP)、CB policy rates、BLS、COT、global gold ETF flows(WGC)、CB gold purchases。
- 实测旁证：sina=200，google=超时 → 本机在中国大陆网络环境；Yahoo=源侧封锁。
- 后果：run 7a88 = 52/52 WAIT，0 成交（fail-safe 正确，但无策略证据产出）。

## 5. 当前测试状态（改动前）
- `trader_v2/tests/`：脚本式 harness（非 pytest）；`test_research_compute.py` 26/26 PASS（今日复跑）。
- 其余：`test_module5_shadow` / `test_module6_broker_demo` / `test_paper_execution` / `test_ledger_replay` / `test_pit_integrity` / `test_sizing_floor` / `test_opportunity_engine` / `test_event_trigger` / `test_demo_calibration_readonly`（logs 有 09-13 记录）。
- 无针对数据源路由/回退/缓存/超时的测试。

## 6. 保护范围（本任务内只读，禁改）
V1 全部 / Hermes 决策·prompt·阈值·confidence·follow-through·entry/exit·SL/TP / sizing·risk / PaperExecutor / BrokerDemoExecutor / FXTM Demo Adapter / demo 账户·magic 90003 / Ledger schema·SHA256·Replay / GPU research_compute / 当前 run 7a88 与 paper-shadow cron。**不下任何单、不 Live、不删历史。**

## 7. 待定（需用户拍板）
1. **实施是否会改动"当前运行中的任务"**：新数据层若接到 agent1/agent2，下一个 15min 周期就会生效，从而改变 run 7a88 剩余周期的输入（不变量：ledger/replay/决策逻辑不动）。→ 是**立即生效**，还是**等本 run 22:41Z 结束后再启用**（用开关隔离）？
2. 范围确认：是否允许新增 `trader_v2/data_sources/` 模块并**改写** `market_data.py`/`sources.py` 的取数实现（保留对外返回 schema 不变）？
