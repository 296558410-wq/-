# CHATGPT-TASK-V2-FULL-AUDIT-RESULT.md

**Task ID**: V2-FULL-AUDIT-001
**执行者**: OpenClaw（只读）｜**复核者**: ChatGPT｜**决策者**: 用户
**生成时间**: 2026-09-19（GMT+8）
**范围**: `C:\AIQuant\research\hermes\trader_v2` + 相关配置/运行态/调度/账本/证据
**标签**: FACT / SUPPORTED / OBSERVATION / DATA_GAP / UNRESOLVED

> 本报告**只记录**，**不修复**。凡未取证处一律标 `DATA_GAP`，不臆造。

```text
AUDIT_EXECUTED=TRUE
READ_ONLY=TRUE
TRADING_CODE_MODIFIED=FALSE
BROKER_ORDER_SENT=FALSE
FORWARD_STARTED=FALSE
V1_UNTOUCHED=TRUE
V2_TRADING_LOGIC_UNTOUCHED=TRUE
V3_UNTOUCHED=TRUE
HERMES_UNTOUCHED=TRUE
RESULT_REPORT_CREATED=TRUE
CURRENT_STATUS_UPDATED=TRUE
GIT_COMMIT_CREATED=TRUE
GIT_PUSHED=TRUE
```

---

## 1. Executive Summary

- **FACT** V2 具备“**MT5 唯一交易行情源**”的**代码级门禁**：`hermes/context.py::_trading_source_status` 对 `history != mt5` 或 `gold_spot != mt5` 一律判 `DEGRADED`，进而 `technical/overall = DEGRADED`，Hermes gate → **WAIT**。
- **FACT（重要，与本次审计预期不符）** 当前 V2 **并非 PAPER 隔离态**：`config.execution.execution_mode = "BROKER_DEMO"`，`broker.enabled=true`，`broker_demo_enabled=true`；且 `runtime/shadow_run.py::_make_executor` 对**非 shadow** 运行返回 **`BrokerDemoExecutor`（真实 demo 执行器）**。即：**若发生 TRADE，会向 FXTM demo 真实下单**（不是 paper）。
- **FACT** `BROKER_ORDER_SENT=FALSE` 目前成立，仅因**当前无合格交易周期执行**（周末 `MARKET_CLOSED_SKIP`；ACTIVE run 计数全 0），**不是因为执行器被 paper 锁死**。
- **OBSERVATION** 运行态存在**状态漂移**：`v2_run_health.run_id (…8648)` ≠ `ACTIVE.run_id (…084c)`；ACTIVE run 计数全 0 且窗口仅 1 分钟；09-19 01:36–01:41Z 短时间内出现多个短命 run（疑似测试/手动触发）。
- **SUPPORTED** G3 事故（2026-09-17 `NON_PAPER_MODE`）根因是**配置未复位**（BROKER_DEMO 残留）与 shadow 的 PAPER guard 冲突 → 说明**隔离依赖配置正确，而非硬架构不变量**。
- 大量子项（Agent2 PIT、异常吞噬、机会发现阈值、状态机、G3 全量统计、风险门绕过证明）本次**未取足证据 → DATA_GAP**。

**最重要结论**：V2 的“MT5-only + 异常→WAIT”**设计存在且有代码证据**；但**当前部署态是 BROKER_DEMO（非 paper）**，与“Shadow/Paper”叙述不一致，且 paper/broker 隔离**依赖配置而非硬保证**。**进入更长期运行前必须先澄清目标执行态。**

---

## 2. Audit Scope

- 目录：`research/hermes/trader_v2`（config/state/runtime/agents/hermes/execution/ledger/research/tools）
- 配置：`config/v2_config.json`、`config/data_router.enabled`、`config/price_space.json`
- 运行态：`state/*`、`state/runs/ACTIVE.json`、`research/runs/*`、`ledger/*`
- 调度：OpenClaw cron `hermes-v2-cycle`(Windows 任务)/`hermes-v2-observer`；V2 `runtime/v2_scheduled_cycle.py`
- git 历史（`research/hermes/trader_v2` 最近提交）
- **只读**；未运行任何会下单/改状态的命令；未改任何文件。

---

## 3. Architecture Reconstruction（从代码/配置重建）

```text
Windows Task hermes-v2-cycle (每15m)
  → runtime/v2_scheduled_cycle.py            [调度+健康记录+休市 OBSERVE_ONLY]
       → trading_hours.is_armed()            [交易时段门]
       → runtime/shadow_run.py cycle --minutes 1440 --new
            → ADP.assert_execution_allowed() [启动安全门]
            → agents/technical/agent1.build()   (Agent1)
            → agents/macro_global/agent2.build()(Agent2)
            → hermes/context.build()            → build_health()/_trading_source_status()
            → hermes/hermes.py → decision (WAIT/TRADE) + opportunity
            → execution/_make_executor: PAPER→PaperExecutor | BROKER_DEMO&!shadow→BrokerDemoExecutor
            → ledger/ledger.py append (+SHA256 chain)
            → runtime/replay_inputs.py (snapshot) / ledger/replay.py
       → state/v2_run_health.json / v2_scheduler_state.json
tools/shadow_guardian.py (只读守护) / tools/v2_observer.py (只读聚合)
```

**入口**：`runtime/v2_scheduled_cycle.py`（零 LLM 调度）→ `shadow_run.run_cycle`。
**逐层职责/IO/失败行为**（FACT，源自代码）：
- Data acquisition：`data_sources/router.py`（Primary→Secondary→Cache→Missing，`HISTORY_SOURCES`/`QUOTE_SOURCES`）。
- Validation/Health：`data_sources/{validate,health,audit,cache}.py` + `hermes/context.build_health`。
- Agent1（技术）：`agents/technical/agent1.py`（写 `state/agent1_latest.json`）。
- Agent2（宏观）：`agents/macro_global/agent2.py`（写 `state/agent2_latest.json` + Evidence Registry）。
- Hermes：`hermes/hermes.py` + `hermes/context.py` gate。
- 执行：`execution/paper_executor.py` / `execution/broker_demo_executor.py`(+`fxtm_demo_adapter.py`)。
- 账本/回放：`ledger/ledger.py`、`ledger/replay.py`、`runtime/replay_inputs.py`。

**与文档差异**：`config.market_data.history="yahoo_chart"`、`multi_source_fallback=[sina,tencent,eastmoney,yahoo]`，但提交 `1d7fa24` 声明“drop yahoo/eastmoney/CFTC/BLS”，且 `registry.py` 仍列 `yahoo`(tertiary)。→ **CONFIG ≠ CODE**（见 §23）。

---

## 4. Market Data Lineage（数据血缘）

**FACT** `data_sources/registry.py`：
- `HISTORY_SOURCES`（技术 K 线 5m/15m/60m/4h/1d）：`[("mt5","primary"), ("local_fxtm","secondary"), ("yahoo","tertiary")]`
- `QUOTE_SOURCES["gold_spot"]`：`[("mt5","XAUUSD"), ("sina","hf_XAU"), ("tencent","hf_XAU"), ("local_fxtm", None)]`
- 其它（dxy/ust10y/vix/gld/tip/comex/silver）多来自 `sina/tencent`（宏观/参考，不进入 XAUUSD 交易价格空间）。

**血缘**：`source → router.pick → agent1(quotes/history) → context._trading_source_status → build_health → hermes gate → decision`。
**门禁**：`_trading_source_status` 仅当 `history==mt5 且 gold_spot==mt5` 才 `PASS`；否则 `DEGRADED`（→ §5/§6）。

---

## 5. MT5-Only Verification（Q1）

**FACT**：交易决策行情（技术 K 线 + XAUUSD 现货价）经 `context._trading_source_status()` 强制要求 `mt5`；非 mt5 → `technical/overall DEGRADED`。
**判定 Q1**：**SUPPORTED**（有代码级门禁证据；但“是否覆盖所有决策输入、是否存在 source 标签误标”未穷尽 → 残留 `DATA_GAP`）。

## 6. Fallback Audit（Q2）

**FACT**：router **存在** fallback（history: local_fxtm/yahoo；quotes: sina/tencent/local_fxtm）。
**FACT**：但 `context.build_health` 会把非 mt5 源判 `DEGRADED` → Hermes gate → **WAIT**（`hermes/context.py` L96–L126）。
**判定 Q2**：**SUPPORTED**（存在 fallback 取数路径，但被门禁降级为 WAIT；未发现“fallback 后继续 TRADE”的直接证据）。**残余风险**：若 `a1` 上报的 source 被错误标为 `mt5`，则门禁失效 → `DATA_GAP`（未做伪造源测试）。

## 7. MT5 Health Gates（Q10 部分）

**FACT**：`data_sources/validate.py`（`validate_quote`）、`health.py`、`cache.py`（FRESH/STALE_BUT_VALID/…）、`hermes/context._freshness`（基于 `data_ts` 而非生成时刻）。
**DATA_GAP**：`tick_max_age` / `bar_max_age` **具体阈值**未在本次逐一定位确认（未在报告中臆断）；OHLC 一致性（high≥max(o,c) 等）与异常跳变阈值的**完整清单未取全**。

## 8. Agent1 Audit（Q4）｜9. Agent2 Audit（Q5）｜11. Opportunity Discovery

**DATA_GAP**：本次**未逐行**完成 Agent1 look-ahead/stale/mixed-timestamp 证明、Agent2 的 PIT/future-info 全项核验、以及 A–F 机会发现的阈值/失效/去重逐项证据。**需要单独只读深挖任务**。
**现有旁证（FACT）**：`context._freshness` 用 `data_ts`；`Agent2` 使用 `published_at/retrieved_at` 与 Evidence Registry（`_pit_valid`），存在 PIT 设计（`agents/macro_global/evidence.py`）。

## 10. Hermes Audit（Q3）

**FACT**：Hermes gate 依赖 `build_health`；非 mt5 源或 gaps/stale → `DEGRADED` → WAIT。
**判定 Q3**：**SUPPORTED**（stale/fallback 行情会被降级 → WAIT）；**未来信息**风险 → `DATA_GAP`（未证）。

## 12. Risk Gate Audit

**DATA_GAP**：未完成“风险门可被 fallback/exception/direct call 绕过”的穷尽证明。
**FACT**：存在 sizing 硬拒（`max_lot`）、单仓约束（POSITION_BUSY）、`price_space` 校验、`broker_validate`（SL 侧校验）。

## 13. Paper/Broker Isolation（Q6）—— **本次最关键**

- **FACT**：`config.execution.execution_mode="BROKER_DEMO"`；`broker.enabled=true`；`broker_demo_enabled=true`；`live_trading=false`；`backends_available=[paper_local,fxtm_demo,oanda_v20]`；`backend="fxtm_demo"`。
- **FACT**：`runtime/shadow_run.py::_make_executor`：`mode==BROKER_DEMO and not shadow → BrokerDemoExecutor`；`shadow → PaperExecutor`。
- **FACT**：`state/runs/ACTIVE.json` = `V2-PAPER-20260919-014104-084c`，其 `RUN_META.shadow=False`、`execution_mode=BROKER_DEMO` → **该 ACTIVE 运行若出 TRADE 会走真实 demo 执行器**。
- **FACT**：`execution/fxtm_demo_adapter.py` 硬约束：仅 `fxtm_demo_01` 终端、`server==ForexTimeFXTM-Demo01`、`magic=90003`、账户须 DEMO、凭据仅走环境变量。
- **FACT**：`hermes_paper_adapter.assert_paper_only()` 要求 `PAPER`+四 false；`assert_execution_allowed()` 允许 `PAPER/BROKER_DEMO`、拒 `LIVE`。
- **判定 Q6**：**UNRESOLVED/否** —— 当前**不是** paper 隔离；`BROKER_ORDER_SENT=FALSE` 只因**无合格周期**。**Paper 与 broker 不是硬隔离，是配置切换**。`FORWARD_STARTED`：`state/FORWARD_VALIDATION_ALLOWED=true`（门已开）→ 组合上非 paper。

## 14. G3 Incident Review（Q7）

- **FACT**：`state/V2_G3_EXECUTION_INCIDENT.json` root_cause：`execution_mode=BROKER_DEMO`（09-11 demo arming 残留，commit 3227043）与 shadow 的 PaperExecutor guard（要求 mode==PAPER）冲突 → shadow run 每笔 TRADE 被拒（`NON_PAPER_MODE`）；status=`CONFIG_FIX_APPLIED`。
- **SUPPORTED**：事故暴露的是**配置/架构耦合**：执行器选择取决于 `execution_mode × shadow`，隔离是**约定**而非不可绕过的硬不变量。
- **判定 Q7**：**同类风险仍在**（当前 ACTIVE 即 BROKER_DEMO 非 shadow）→ **MEDIUM-HIGH。**

## 15. Ledger/Replay Audit（Q8）

- **FACT**：`ledger/ledger.py::verify_ledger` 对 run `…8648`：`verify=True, n=115`。
- **DATA_GAP**：append-only/事件顺序/orphan/duplicate/missing-response/deterministic replay 的**全量**核查未完成。

## 16. Runtime Stability / 17. Scheduler/Task Bus / 18. Exception / 19. State Machine

- **FACT**：`v2_run_health.cycle_result="MARKET_CLOSED_SKIP"`、`armed=false`、`run_status=RUNNING`、`blocked=null`；休市走 OBSERVE_ONLY（本日授权变更）。
- **OBSERVATION（状态漂移）**：health.run_id(`…8648`) ≠ ACTIVE.run_id(`…084c`)；ACTIVE run `counters` 全 0；`end_utc = start+60s`。
- **OBSERVATION**：09-19 01:36:53Z / 01:36:54Z / 01:41:04Z 出现 3 个短命 run（疑测试/手动触发，非生产周期）。
- **FACT（异常处理）**：`shadow_run.py` 含 19 处 `except`（Agent1/Agent2 失败被计数 `failures` 后**继续**该周期其余步骤）；`hermes.py` 1 处；`agent2.py` 3 处；`router.py` 5 处。→ **“失败不伪造成新数据”** 的设计存在，但**“异常→WAIT vs 异常→带旧数据继续”** 的**逐条**判定 → `DATA_GAP`。

## 20. Negative Tests

**DATA_GAP**：本轮**未**执行任何负向注入（避免触交易路径）。§六/§八 列举的 `MT5 unavailable/stale/malformed/symbol invalid/spread invalid/Agent 缺失/Hermes timeout/…` 的**行为矩阵**未实测。

## 21. V1/V2/V3 Isolation

- **FACT**：`config.isolation`：`allow_real_trading=false`、`reuse_v1_* = false`；V2 独立 MT5 实例 `fxtm_demo_01`、magic 90003（V1=90002）。
- **FACT**：本次审计对 V1/V3/Hermes **只读**，未做任何修改。
- **DATA_GAP**：三实例“无交叉 state/订单”的**运行期**证明未做（仅凭配置与命名）。

## 22. Data Integrity / 23. Design-vs-Code Consistency

- **FACT（CONFIG ≠ CODE）**：`config.market_data.history="yahoo_chart"`、`multi_source_fallback` 含 eastmoney/yahoo ↔ `registry.py` 仍列 yahoo；提交 `1d7fa24` 称已 drop。
- **FACT（DESIGN ≠ RUNTIME）**：项目叙述 “V2 当前为 Shadow/Paper”，但**运行配置为 BROKER_DEMO**。
- **FACT（RUNTIME ≠ LEDGER/health）**：health.run_id ≠ ACTIVE.run_id（§16）。

## 24. Findings（汇总）

| ID | 级别 | 标签 | 事实 |
|---|---|---|---|
| F-01 | HIGH | FACT | 当前 `execution_mode=BROKER_DEMO`+broker armed；非 shadow run 用 `BrokerDemoExecutor`；`BROKER_ORDER_SENT=FALSE` 仅因无合格周期 |
| F-02 | MEDIUM | FACT | ACTIVE.run_id ≠ health.run_id（状态漂移）；ACTIVE run 计数全 0 / 窗口 1 分钟 |
| F-03 | MEDIUM | OBSERVATION | 短时间多个短命 run（疑测试/手动），存在重复/漂移风险 |
| F-04 | MEDIUM | SUPPORTED | Paper/Broker 隔离是**配置**而非硬不变量（G3 事故印证） |
| F-05 | LOW-MED | FACT | CONFIG≠CODE：yahoo/eastmoney 残留于 config/registry |
| F-06 | LOW | FACT | MT5-only 门禁存在（非 mt5→DEGRADED→WAIT） |
| F-07 | LOW | FACT | ledger verify=True(n=115)；fxtm 适配器硬约束（demo/server/magic/terminal） |
| F-08 | LOW | FACT | `FORWARD_VALIDATION_ALLOWED=true`（forward 门开启） |

## 25. DATA_GAPS

1. Agent1 look-ahead/stale/mixed-timestamp **逐项**证明。
2. Agent2 PIT / future-information **逐项**证明。
3. 机会发现 A–F 阈值/失效/去重/expiry **逐项**。
4. 风险门**绕过**穷尽证明。
5. 负向注入行为矩阵（§20）。
6. 异常吞噬“异常→WAIT vs 继续”**逐条**判定。
7. Ledger/Replay **全量**（orphan/duplicate/missing-response/deterministic）。
8. G3（09-17T10:53Z→09-19T10:53Z）**全量**统计。
9. `tick_max_age/bar_max_age` 实际阈值与 OHLC 一致性清单。
10. 三实例运行期“无交叉”证明。

## 26. UNRESOLVED

- Q6：Paper/Broker 是否“完全隔离”→ 结论：**当前配置下否**；架构上“是否可硬保证”→ UNRESOLVED（依赖配置）。
- Q7：G3 后是否仍有同类漏洞 → **同类条件仍成立**（BROKER_DEMO 非 shadow）。

## 27. Evidence Index（本次直接证据）

- `config/v2_config.json`（execution/broker/market_data/isolation）
- `hermes/context.py` L96–L127（`_trading_source_status`/`build_health`）
- `data_sources/registry.py`（HISTORY_SOURCES/QUOTE_SOURCES）
- `runtime/shadow_run.py` L141–L148（`_make_executor`）、L156+（start_run/shadow gate）
- `execution/hermes_paper_adapter.py` L47–L95（`assert_paper_only`/`assert_execution_allowed`）
- `execution/fxtm_demo_adapter.py` L2–L66（硬约束/`_gate`/magic 90003）
- `state/runs/ACTIVE.json`、`state/v2_run_health.json`、`research/runs/…/RUN_META.json`、`…/run_state.json`
- `state/V2_G3_EXECUTION_INCIDENT.json`
- `ledger/ledger.py::verify_ledger`（run …8648, n=115, True）
- git 历史：`1d7fa24, e64175d, 9b3d398, 1af2e03, 8d997fb, 363c620, 0fc0f30`

## 28. Final Audit Conclusion（回答核心问题）

- **Q1** MT5 唯一决策源：**SUPPORTED**（有门禁代码；不排除 source 误标）。
- **Q2** MT5 异常绝不 fallback 后 TRADE：**SUPPORTED**（非 mt5→DEGRADED→WAIT）；残余 `DATA_GAP`。
- **Q3** Hermes 收到 stale/fallback/future：stale/fallback → **SUPPORTED 会被 WAIT**；future → **DATA_GAP**。
- **Q4** Agent1 look-ahead/stale/mixed：**DATA_GAP**。
- **Q5** Agent2 PIT/future：**DATA_GAP**（有 PIT 设计旁证）。
- **Q6** Paper 与 broker 完全隔离：**否**（当前 BROKER_DEMO/非 shadow；隔离靠配置）。
- **Q7** G3 后同类漏洞：**同类条件仍成立（MEDIUM-HIGH）**。
- **Q8** Ledger/Replay 可靠重建：**SUPPORTED（局部）**；全量 `DATA_GAP`。
- **Q9** 长期运行 silent failure/duplicate/orphan/state drift：**OBSERVATION 存在状态漂移（F-02/F-03）**；全量 `DATA_GAP`。
- **Q10** 最重要 DATA GAP：**Agent1/Agent2 的 look-ahead/PIT 逐项证明缺失**；次为负向测试缺失。
- **Q11** 进入更长期运行前须先解决的**事实依据与风险**（只列，不代决）：
  - F-01/F-04：**当前执行态是 BROKER_DEMO 而非 PAPER**，隔离靠配置 → 必须先澄清“目标执行态”。
  - F-02/F-03：运行态漂移与短命 run → 需澄清 ACTIVE 语义/清理测试产物。
  - §25 的 DATA_GAP 项 → 需补充只读深挖任务。

## 29. Recommended Follow-up Investigations（研究建议，非用户指令）

1. 独立只读任务：Agent1 全量 look-ahead/stale/mixed-timestamp 审计。
2. 独立只读任务：Agent2 PIT + Evidence Registry 全量核验。
3. 只读负向注入矩阵（不触交易）：MT5 断流/陈旧/畸形 → 断言 WAIT。
4. Ledger/Replay 全量（orphan/duplicate/missing-response/deterministic）。
5. G3 全量运行统计与 replay mismatch 清单。
6. 澄清并固化“**V2 目标执行态**（PAPER vs BROKER_DEMO）”与对应安全不变量。

---
_只读审计产物；不构成修改授权。问题只记录，不自行修复。_
