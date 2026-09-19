# CHATGPT-TASK-V2-AUDIT-002-003-RESULT.md

**Task**: V2-AUDIT-002/003（Agent1 时序完整性 + Agent2 PIT + 执行隔离/运行状态穿透）
**执行**: OpenClaw（只读）｜**复核**: ChatGPT｜**决策**: 用户
**时间**: 2026-09-19（GMT+8）
**标签**: FACT / SUPPORTED / OBSERVATION / DATA_GAP / UNRESOLVED

```text
AUDIT_002_003_EXECUTED=TRUE
READ_ONLY=TRUE
TRADING_CODE_MODIFIED=FALSE
V1_UNTOUCHED=TRUE  V2_TRADING_LOGIC_UNTOUCHED=TRUE  V3_UNTOUCHED=TRUE  HERMES_UNTOUCHED=TRUE
BROKER_ORDER_SENT=FALSE  FORWARD_STARTED=FALSE
BROKER_NEGATIVE_TESTS=DATA_GAP
AGENT1_PIT_VERIFIED=DATA_GAP
AGENT2_PIT_VERIFIED=DATA_GAP
EXECUTION_ISOLATION_VERIFIED=DATA_GAP
ACTIVE_STATE_ROOT_CAUSE=SUPPORTED
FAILURE_MATRIX_COMPLETED=FALSE
RESULT_REPORT_CREATED=TRUE  CURRENT_STATUS_UPDATED=TRUE
GIT_COMMIT_CREATED=TRUE  GIT_PUSHED=TRUE
```

---

## 1. Executive Summary

- **FACT** Agent1 存在**显式 look-ahead 防护**：`agents/technical/market_data.py:165` 丢弃未收盘的最末 bar（`bars[-1].t + tf_seconds > now → 剔除`）；`data_sources/validate.py:31` 拒绝未来 bar。
- **FACT** 新鲜度阈值**存在**：`hermes/context.py::FRESH_RULES`（agent1: 1200s fresh / 3600s stale；agent2: 4500s / 10800s）；`data_sources/cache.py`（宏观 fresh_h=1h / stale_h=168h）。
- **FACT** Agent2 具备 PIT 字段设计：`agents/macro_global/evidence.py::_pit_valid`（`published_at <= retrieved_at`）；但**并非所有进入 Hermes 的字段都被证明 PIT-valid**。
- **FACT（关键）** 当前 V2 运行态：`ACTIVE = V2-PAPER-20260919-014104-084c`，`RUN_META.shadow=False`、`execution_mode=BROKER_DEMO`、`code_commit=d22d9fb`、`config_hash=b0cc254b…`；`run_state.status=RUNNING, cycles=0`。
- **FACT** 存在 **4 个 `run_state.status=RUNNING` 并存的 run**（…8648/…084c/…b3c2/…59f4），但仅 `ACTIVE.json` 指向其一 → 多 RUNNING 状态共存。
- **SUPPORTED** `ACTIVE` 漂移根因：`start_run()` 覆盖 `ACTIVE.json`（`shadow_run.py:173`），而 `v2_run_health.run_id` 来自**最近一次成功 cycle**；测试/手动 `start_run` 新建 run（084c）后无对应 cycle → 两文件不一致。
- **OBSERVATION** 短命 run（09-19 01:36–01:41Z）均为 non-shadow / BROKER_DEMO / `code_commit=d22d9fb` / `config_hash=b0cc254b…` / `cycles=0` → 疑测试或手动入口产生，非生产周期。

---

## 2. Scope

`research/hermes/trader_v2`（agents/data_sources/hermes/execution/runtime/ledger/config/state/research/runs）+ Windows 任务 `hermes-v2-cycle` 设置 + git 历史。只读；未执行下单；未改任何文件。

---

## 3–9. 专项 A：Agent1（时序/血缘/新鲜度）

**调用链（FACT，代码重建）**：
```text
scheduler(v2_scheduled_cycle) → shadow_run.run_cycle
 → agents/technical/agent1.build(cycle)
    → agents/technical/market_data.py (HISTORY/QUOTE via data_sources.router)
    → data_sources/local_bars.py (tick→bar, secondary)
    → agents/technical/features.py (feature/regime/candidate)
    → state/agent1_latest.json (+ snapshots/agent1_<cycle>.json)
 → hermes/context.build → build_health → Hermes
```

- **§5 Look-ahead**：**SUPPORTED（部分）** — 有未收盘 bar 剔除 + 未来 bar 校验（上引）。`features.py` 以**已过滤序列**的 `[-1]` 计算（如 `last_close/atr_pct/price_vs_sma20_bps`）。**未穷尽**每一特征的未来泄露（rolling/quantile/normalize）→ `DATA_GAP`。
- **§6 时间一致性（统一 cutoff）**：**DATA_GAP** — 未找到 Agent1 显式“统一 cutoff_time”实现；各 tf 的 `last_bar_ts` 独立。是否会把 M1/M5/H1 不同末点当同一 snapshot → **未证**。
- **§7 Stale**：**SUPPORTED** — 阈值存在（context FRESH_RULES / cache）；具体 tick/bar 阈值清单未列全 → `DATA_GAP`（细节）。
- **§8 Mixed timestamp**：**DATA_GAP**（同上）。
- **§9 Source lineage 逐字段**：**DATA_GAP** — 未建立逐字段 `tick→M1→M5→H1→feature→candidate` 样本证明；`market_data.py` 有未收盘剔除，但 **fallback（local_fxtm/yahoo）不得进入交易特征** 未被逐字段证明（router 允许降级，门禁在 context 层，非 agent1 内）→ 见 §4/§6。

**Q-A1** 无 look-ahead？**DATA_GAP**（有重要防护证据，但未逐项证明）。
**Q-A2** 未收盘 bar？**SUPPORTED 否**（代码剔除）。
**Q-A3** mixed timestamp？**DATA_GAP**。
**Q-A4** stale？**SUPPORTED 有阈值+降级设计**。
**Q-A5** MT5 lineage 逐字段？**DATA_GAP**。

---

## 10–15. 专项 B：Agent2（PIT / 证据链 / 回放）

**调用链（FACT）**：
```text
agent2.build → sources.collect()（DXY/UST10Y/VIX/TIP/GLD/COT/ETF/news）
 → evidence.record_news()（固化 + sha256 + _pit_valid(published<=retrieved)）
 → macro/geopolitics/econ 事件 + news_status + signal_guard
 → state/agent2_latest.json（含 point_in_time / evidence.refs）
 → Hermes
```

- **§11 PIT 核心**：**SUPPORTED（设计）** — `evidence.py::_pit_valid` 明确 `published_at<=retrieved_at`；snapshot 带 `point_in_time`。**但**：`published_at` 常为 `unavailable`（`release_timestamp_unknown=true`），`_pit_valid` 返回 `"unknown"` → **不得视为 PIT-valid**（仅 `retrieved_at` 已知）→ 判定：**PIT 未被全面证明 = DATA_GAP**。
- **§12 逐项**：DXY/UST10Y/VIX/TIP/GLD/GC 均为**当日近实时**（sina/tencent/yahoo），`observation_time≈retrieved`；**COT**：`no_domestic_source(CFTC 403)` → **DATA_GAP/缺失**；**ETF flows**：CN ETF（tencent）→ 观察时刻近实时；PIT 依赖源时间戳 → **DATA_GAP**；**News**：`published_at` + `_pit_valid` → **SUPPORTED（部分）**；**Geopolitics**：由新闻标签推断，`first_seen_at=retrieved_at` → **DATA_GAP**。
- **§13 Evidence Registry**：**SUPPORTED（部分）** — `agent2.build` 逐条 `EV.record_news` 并把 `evidence_id` 写入 snapshot `evidence.refs`；调用链 `news→record→refs→snapshot` 成立。是否存在“入了 registry 但 Agent2 未用 / Agent2 有字段但 registry 无” → **DATA_GAP**（未逐条对齐）。
- **§14 Future contamination**：**DATA_GAP** — 修订/`latest`/`updated` 字段的污染检查未做；宏观缺口项（政策利率/WGC/央行购金）标 `placeholder/未取`。
- **§15 Replay PIT**：**DATA_GAP** — 未证明 replay（如 09-17 13:00Z）不会使用当前 Evidence Cache 的“后见”数据；`replay_inputs.build_snapshot` 基于当时 `d,ctx,a1,a2`，但 evidence 回源风险未证。

**Q-B1** Agent2 PIT？**DATA_GAP**（有设计，未证）。
**Q-B2** COT 按 release/publication？**DATA_GAP**（当前 COT 源缺失/403）。
**Q-B3** ETF PIT？**DATA_GAP**。
**Q-B4** News PIT？**SUPPORTED（部分）**。
**Q-B5** Geopolitics PIT？**DATA_GAP**。
**Q-B6** Replay 未来 evidence？**DATA_GAP**（未证伪）。

---

## 16–18. 专项 C：执行隔离穿透

**执行器选择真值表（FACT，源自 `runtime/shadow_run.py::_make_executor` L141–148 + 各 guard）**：

| execution_mode | shadow | broker.enabled | broker_demo_enabled | live_trading | 实际 executor |
|---|---|---|---|---|---|
| PAPER | false | false | false | false | PaperExecutor |
| PAPER | true | false | false | false | PaperExecutor |
| BROKER_DEMO | true | true | true | false | **PaperExecutor**（shadow 强制） |
| BROKER_DEMO | false | true | true | false | **BrokerDemoExecutor（真实 demo）** ← 当前 ACTIVE |
| BROKER_DEMO | false | false | false | false | `assert_execution_allowed` REFUSE（需双 true） |
| LIVE | * | * | * | * | REFUSE（`assert_execution_allowed` 拒 LIVE） |
| 非法 mode | * | * | * | * | REFUSE |

- `_make_executor`：`mode==BROKER_DEMO and not shadow → BrokerDemoExecutor`；否则 `PaperExecutor`。
- `assert_execution_allowed`：PAPER 需四 false；BROKER_DEMO 需 `broker.enabled && broker_demo_enabled` 且 `live_trading==false`；任何 LIVE → `RefuseToStart`。
- `fxtm_demo_adapter._gate`：`execution_mode==BROKER_DEMO && broker_demo_enabled` 否则 `RefuseConnection`；终端/服务器/账户/magic 硬约束。

**§18 负向测试（Case 1–9）**：**DATA_GAP — 未执行**（本轮未运行 mock harness；避免任何 broker 侧副作用）。真值表为**代码静态推导（FACT about code）**，非运行验证。
**§17 Escape**：**SUPPORTED** — 未发现绕过 `_make_executor`/guard 的 direct broker 调用；broker 下单符号集中在 `execution/fxtm_demo_adapter.py`(place_market_order) + `broker_demo_executor.py`。穷尽性 → `DATA_GAP`。

**Q-C1** 当前 PAPER？**否（FACT：BROKER_DEMO）**。
**Q-C2** BROKER_DEMO 可被非 shadow 调用？**FACT 是**（ACTIVE run 即此类）。
**Q-C3** Paper→Broker escape？**SUPPORTED 无（除配置切换）**。
**Q-C4** Broker→Paper fallback？**DATA_GAP**（未证 broker 初始化失败时会否静默改走 paper）。
**Q-C5** LIVE 绝对拒绝？**SUPPORTED**（guard 明确拒）。
**Q-C6** direct broker API bypass？**SUPPORTED 未发现**；穷尽 → `DATA_GAP`。

---

## 19–21. 配置一致 / ACTIVE 漂移 / Run 生命周期

- **§19 一致性**：**FACT** `execution_mode=BROKER_DEMO` 在 config / RUN_META / run_manifest 三方一致；`code_commit=d22d9fb`、`config_hash=b0cc254b…` 一致。**冲突项**：`v2_run_health.run_id` 与 `ACTIVE.run_id` 不一致（见下）。
- **§20 ACTIVE 漂移**（回答 Q-D1）：**SUPPORTED** —
  1. `start_run()` 创建 run 并**覆盖** `ACTIVE.json`（`shadow_run.py:173`）。
  2. `v2_run_health.run_id` 由**最近成功 cycle** 的 `res.run_id` 写回（`v2_scheduled_cycle`）。
  3. 测试/手动 `start_run` 新建 `084c`（`cycles=0`，无 cycle）→ health 仍留 `8648`。
  → 漂移 = “ACTIVE 被新 run 覆盖，但无对应 cycle 更新 health”。
- **§21 短命 run**：`084c/b3c2/59f4` 均 `shadow=False, mode=BROKER_DEMO, code_commit=d22d9fb, config_hash=b0cc254b, cycles=0, status=RUNNING`。判定：**OBSERVATION** — 与 09-19 09:36–09:41 CST 的测试/手动入口时间吻合；**不能证实为生产周期**，也**不能排除**调度/入口重复 → `UNRESOLVED`（归因）。

**Q-D1** 根因：**SUPPORTED**（如上）。
**Q-D2** 两个 RUNNING？**FACT：4 个 run_state=RUNNING 并存**（仅 1 个 ACTIVE 被驱动）。
**Q-D3** duplicate execution？**DATA_GAP**（窗口 dedup 存在，未证全部路径）。
**Q-D4** crash recovery？**DATA_GAP**。
**Q-D5** scheduler 重入？**SUPPORTED** — Windows 任务 `MultipleInstances`=默认(IgnoreNew) + `ExecutionTimeLimit=PT15M`；另有 OpenClaw cron/task-bus 独立入口（不同对象）。

---

## 22–23. 异常处理 / 失败矩阵

- **§22 Exception**：**FACT** — `shadow_run.py` 19 处 except：Agent1/Agent2/Hermes 失败**计数并写 timeline**后**继续**该周期；broker/reconcile/price_space 失败→写 error/`BROKER_UNAVAILABLE`/`execution_reject`。**证据**：未发现 `except → TRADE`。但“异常→WAIT”的**逐条**证明 → `DATA_GAP`（需结合 gate）。
- **§23 Failure Injection Matrix**：**DATA_GAP — 未执行**（FALSE）。理论期望（MT5/Agent/Hermes/executor/ledger/scheduler 故障 → WAIT/明确错误）**未实测**。

**Q-E1..E6**：**SUPPORTED（设计层）**（MT5 非-mt5→DEGRADED→WAIT；Agent 失败→health FAIL→gate；LIVE 拒；executor 失败→显式 reject）；**逐条 → DATA_GAP**。

---

## 24. 三实例运行期隔离

- **FACT**：V2 使用独立实例 `C:\AIQuant\mt5_instances\fxtm_demo_01`，终端 tag `fxtm_demo_01`、server `ForexTimeFXTM-Demo01`、magic 90003（V1=90002）；V3 实例 `fxtm_demo_v3`，magic 90004。
- **DATA_GAP**：V1↔V2↔V3 进程/AppData/缓存/日志/state “无交叉”的**运行期**证明未做。

---

## 25. Findings

| ID | 级别 | 标签 | 事实 |
|---|---|---|---|
| R2-01 | HIGH | FACT | 当前 ACTIVE 为 **non-shadow + BROKER_DEMO** → 若出 TRADE 走真实 demo 执行器；非 paper 隔离 |
| R2-02 | MEDIUM | FACT | **4 个 run 同时 status=RUNNING**（仅 1 个 ACTIVE）；run 生命周期松散 |
| R2-03 | MEDIUM | SUPPORTED | ACTIVE/health 漂移根因 = `start_run` 覆盖 ACTIVE 而无对应 cycle |
| R2-04 | MEDIUM | OBSERVATION/UNRESOLVED | 短命 run 归因未定（测试/手动 vs 入口重复） |
| R2-05 | MEDIUM | DATA_GAP | 负向测试矩阵**未执行**；BROKER_NEGATIVE_TESTS=DATA_GAP |
| R2-06 | MEDIUM | DATA_GAP | Agent1 逐字段 look-ahead / 统一 cutoff / mixed-timestamp 未证 |
| R2-07 | MEDIUM | DATA_GAP | Agent2 逐字段 PIT（COT/ETF/geopolitics）与 Replay 未来 evidence 未证 |
| R2-08 | LOW | FACT | Agent1 有未收盘 bar 剔除 + 未来 bar 校验；新鲜度阈值存在 |
| R2-09 | LOW | SUPPORTED | LIVE 被明确拒绝；broker 硬约束（demo/server/magic/terminal） |

## 26. DATA_GAPS

1. Agent1 全特征 look-ahead 逐项；2. Agent1 统一 cutoff / mixed-timestamp；3. tick/bar 阈值清单；4. Agent1 fallback 不入交易特征的逐字段证明；5. Agent2 COT/ETF/Geopolitics PIT；6. Replay 未来 evidence；7. Evidence Registry 双向对齐；8. Execution 负向测试 Case 1–9；9. Broker 失败是否静默改 Paper；10. Failure Injection Matrix；11. Scheduler 全入口重入；12. 三实例运行期隔离；13. Ledger/Replay 全量。

## 27. UNRESOLVED

- 短命 run 归因（R2-04）。
- Broker 初始化失败时的行为（C4）。
- Exception→WAIT 的逐条判定（E1–E6）。

## 28. Evidence Index

- `agents/technical/market_data.py:165`（未收盘剔除）、`data_sources/validate.py:12,31,35`、`data_sources/local_bars.py:41–43`（resample label/closed=left）
- `agents/technical/features.py:146,154,178,196,202,210`
- `data_sources/cache.py:15–90`、`data_sources/health.py:22–40`、`hermes/context.py:21–22,40–47,96–127`
- `agents/macro_global/evidence.py`（record/_pit_valid）、`agents/macro_global/agent2.py`（news/geo/econ + refs）
- `runtime/shadow_run.py:110,141–148,156,170–174,188–197,517–526`、`execution/hermes_paper_adapter.py:47–95`、`execution/fxtm_demo_adapter.py:20–66`
- `state/runs/ACTIVE.json`；`research/runs/{…084c,…b3c2,…59f4,…8648}/{RUN_META,run_manifest,run_state}.json`
- Windows 任务 `hermes-v2-cycle` Settings（MultipleInstances 默认 / ExecutionTimeLimit PT15M）
- git：`research/hermes/trader_v2` 最近提交（1d7fa24 等）

## 29. Final Answers（速览）

- A：Q-A1 DATA_GAP ｜ Q-A2 SUPPORTED-否 ｜ Q-A3 DATA_GAP ｜ Q-A4 SUPPORTED ｜ Q-A5 DATA_GAP
- B：Q-B1 DATA_GAP ｜ Q-B2 DATA_GAP ｜ Q-B3 DATA_GAP ｜ Q-B4 SUPPORTED-部分 ｜ Q-B5 DATA_GAP ｜ Q-B6 DATA_GAP
- C：Q-C1 否(FACT) ｜ Q-C2 是(FACT) ｜ Q-C3 SUPPORTED-无 ｜ Q-C4 DATA_GAP ｜ Q-C5 SUPPORTED ｜ Q-C6 SUPPORTED-未发现
- D：Q-D1 SUPPORTED ｜ Q-D2 是(FACT) ｜ Q-D3 DATA_GAP ｜ Q-D4 DATA_GAP ｜ Q-D5 SUPPORTED
- E：Q-E1..E6 SUPPORTED(设计) / 逐条 DATA_GAP

## 30. Recommended Follow-up（研究建议，非用户指令）

1. 只读 mock harness：执行 §18 Case 1–9 与 §23 失败矩阵（fake adapter，零 broker 副作用）。
2. Agent1 逐特征 look-ahead/统一 cutoff 静态审计。
3. Agent2 PIT 逐字段 + Replay 未来 evidence 审计。
4. ACTIVE 生命周期与“多 RUNNING”语义澄清 + 短命 run 归因。
5. 三实例运行期隔离只读核查。
6. Ledger/Replay 全量。

---
_只读审计；只记录，不修复。_
