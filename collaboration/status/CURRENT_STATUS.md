# CURRENT_STATUS.md

> 项目协作层的当前事实快照。**禁止把 hypothesis 写成 fact。**
> 每条状态须标注分类：`FACT` / `OBSERVATION` / `HYPOTHESIS` / `UNRESOLVED` / `DATA_GAP`。

---

## Meta

- **Last Updated**: 2026-09-19 (GMT+8)
- **GitHub Repository**: https://github.com/296558410-wq/-.git (Public)
- **Maintained By**: OpenClaw (本地执行)｜Audited By: ChatGPT (独立审计)｜Decided By: 用户

## GitHub Baseline

- **FACT** — Baseline commit: `22f27df40f4f3b71fdbbcc9a92753c3bb2743241`
- **FACT** — Message: `chore: establish clean research baseline`
- **FACT** — Branch: `main`，commit count = 1（该 commit 经 ChatGPT 独立复核）
- **FACT** — 后续协作层提交在此 commit 之上叠加，不修改/重写/删除该 commit，不使用 force push

## Original Local Repository

- **FACT** — 原始项目路径：`C:\AIQuant`
- **FACT** — 原始仓库 HEAD: `d22d9fb`，commit count = 249
- **FACT** — 本协作层任务不修改原始仓库历史
- **FACT** — GitHub 发布使用独立 staging 仓：`C:\AIQuant\github_publish_staging`

## V1 Status

- **FACT** — 路径：`C:\AIQuant\research\hermes\trader_v1`
- **FACT** — 本任务中 V1 = READ ONLY（未修改）

## V2 Status

- **FACT** — 路径：`C:\AIQuant\research\hermes\trader_v2`
- **FACT** — 阶段：Shadow / Paper（非实盘）
- **FACT** — 本任务中 V2 = READ ONLY（未修改）
- **OBSERVATION** — MT5 为 V2 唯一交易决策行情源；MT5 异常须安全 WAIT（不 fallback 交易）

## V3 Status

- **FACT** — 路径：`C:\AIQuant\research\hermes\trader_v3` 与 Hermes V3 workspace `C:\Users\surface\HermesWorkspaces\v3`
- **FACT** — 本任务中 V3 = READ ONLY（未修改）

## Hermes Status

- **FACT** — 角色：交易智能 / XAUUSD 决策智能
- **FACT** — 本任务中 Hermes = READ ONLY（未修改）
- **UNRESOLVED** — Hermes 各版本能力/边界的量化结论未在本层裁定

## Research Status

- **FACT** — 研究方法遵循 §7「研究真实性规则」与 §8「结论分类」
- **UNRESOLVED** — 各候选机制/结论的最终评级（SUPPORTED/…）待后续研究任务产出

## Collaboration Layer Status

- **FACT** — 本层为 v1：角色定义、任务协议、报告协议、决策日志、状态快照、协作文档
- **FACT** — 目录：`collaboration/{status,decisions,tasks/CHATGPT_TO_OPENCLAW,tasks/OPENCLAW_TO_CHATGPT}`

## Known Risks

- **OBSERVATION** — 误把文档关键词（token/password 等）当成凭据的风险 → 需按"值 vs 词"区分
- **OBSERVATION** — 运行态/私密数据误入 GitHub 的风险 → 提交前强制扫描与边界检查
- **HYPOTHESIS** — 若不强制隔离，研究结论可能被误升级为生产行为 → 已以 §9 规则约束

## Known Data Gaps

- **DATA_GAP** — 记录当前已知、未解决的数据缺口（示例：部分宏观/行情源缺失）。具体清单以 V2 运行审计为准，本快照不臆造。

## Next Approved Actions

- **FACT** — 当前无已批准的研究/交易动作
- 说明：任何 research → trading 的改变都必须经用户明确决策（见 `decisions/DECISION_LOG.md`）。

## V2 Full Audit (V2-FULL-AUDIT-001, 2026-09-19)

- **FACT** — 当前运行配置 `execution_mode=BROKER_DEMO`（broker.enabled/broker_demo_enabled=true，live_trading=false）；非 shadow run 使用 `BrokerDemoExecutor`。`BROKER_ORDER_SENT=FALSE` 目前成立仅因无合格周期执行。
- **FACT** — MT5-only 门禁存在：`hermes/context.py::_trading_source_status` 对非 mt5 行情源判 DEGRADED → WAIT。
- **OBSERVATION** — 状态漂移：`v2_run_health.run_id` ≠ `ACTIVE.json.run_id`；ACTIVE run 计数全 0；09-19 出现数个短命 run。
- **SUPPORTED** — Paper/Broker 隔离依赖配置而非硬不变量（G3 事故印证）。
- **DATA_GAP** — Agent1 look-ahead/stale、Agent2 PIT、机会发现阈值、风险门绕过、负向注入矩阵、Ledger/Replay 全量、G3 全量统计，均待独立只读深挖。
- 详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-FULL-AUDIT-RESULT.md`。

## V2 Audit 002/003 (穿透：时序 + PIT + 执行隔离, 2026-09-19)

- **FACT** — Agent1 有显式 look-ahead 防护（`market_data.py:165` 剔除未收盘 bar；`validate.py` 拒未来 bar）；新鲜度阈值存在（`context.FRESH_RULES` / `cache`）。
- **FACT** — 当前 ACTIVE 运行：non-shadow + BROKER_DEMO（若 TRADE → 真实 demo 执行器）。
- **FACT** — 同时有 **4 个 run** `status=RUNNING`（仅 1 个 ACTIVE）。
- **SUPPORTED** — ACTIVE/health 漂移根因：`start_run` 覆盖 ACTIVE 而无对应 cycle。
- **DATA_GAP** — Agent1 逐字段 look-ahead/统一 cutoff、Agent2 PIT（COT/ETF/geopolitics）+ Replay 未来 evidence、Execution 负向测试、Failure Matrix、三实例运行期隔离。
- 详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-AUDIT-002-003-RESULT.md`。

## V2 Audit 003 (执行隔离负向测试 mock + 失败门禁, 2026-09-19)

- **FACT（mock 实测，零 broker）** — E-01 `PAPER`→Paper；E-02 `BROKER_DEMO+shadow`→Paper；E-03 `BROKER_DEMO+!shadow`→BrokerDemo；E-04..E-07 均 REFUSE；E-08/E-09 初始化失败**无跨执行器回落**。
- **FACT** — 非 mt5 源 → `build_health` DEGRADED；a1 缺失 → FAIL。
- **SUPPORTED** — 4 个 RUNNING 并存 = 旧 run 未 finalize 残留；ACTIVE/health 漂移 = start_run 覆盖 ACTIVE。
- **DATA_GAP** — Agent1/Agent2/Replay PIT；F-03..F-14 失败矩阵；并发；三实例运行期隔离。
- 详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-AUDIT-003-RESULT.md`。

## V2 Audit 004 (最终穿透 / 只读, 2026-09-19)

- **FACT** — Agent1 特征清单已机械提取（features.py）；Agent2 `cot.publication_timestamp_unknown=True`/`pit_status=UNKNOWN`、`news.first_seen_at=retrieved_at`。
- **FACT（本轮新测）** — 并发 `start_run` harness：两线程同秒收敛同 rid，无损坏；**未有效制造差异 run 竞争** → 并发安全仍 DATA_GAP。
- **DATA_GAP** — Agent1/Agent2/Replay PIT、E_after 注入、并发 cycle、幂等、crash recovery、三实例运行期隔离。
- 结论：**NOT READY FOR FORMAL FORWARD**（存在 HIGH 类条件 H-01）。
- 详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-AUDIT-004-RESULT.md`。

## V2 Validation 005 (遗留缺口穿透, 2026-09-19)

- **FACT（新测）** — 并发 `start_run` ×10：**可建两个 run + 覆盖 ACTIVE**（§7 情况 D）→ 新增 **M-04 MEDIUM**。
- **FACT（代码）** — Replay 为快照驱动（`offline_replay` 仅用 snapshot、hash 校验、不联网）→ **E_AFTER_BLOCKED=TRUE**（代码级）。
- **DATA_GAP** — Agent1/Agent2/Replay PIT、concurrent cycle、幂等、crash recovery、运行期隔离。
- 结论：**NOT READY FOR FORMAL FORWARD**（H-01 仍在，风险等同 BLOCKED）。
- 详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-VALIDATION-005-RESULT.md`。

## V2 Repair 006 (运行安全修复, 2026-09-19) — 部分完成

- **已实施（授权范围）**：`runtime/atomic_io.py`(新) + `shadow_run.py`(`_write` 原子写 + `start_run` 加跨进程 `RunLock` + 拒绝覆盖 RUNNING run)。
- **回归**：`tests/test_run_lifecycle_fix.py` **3/3 PASS**（R6-001/R6-002 并发/R6-012 原子写）；执行器回归 E-01..E-09 不变；V1 零接触。
- **仍 DATA_GAP**：concurrent cycle / duplicate idempotency / crash recovery / UNKNOWN / scheduler re-entry / ledger 一致性。
- **H01_UNTOUCHED=TRUE**（execution_mode/broker flags 未改）。`RUN_SAFETY_REPAIR=INCOMPLETE`。
- 代码+测试+报告已同步至 GitHub 协作仓。详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-REPAIR-006-RESULT.md`。

## V2 Repair 006B (并发交易链/幂等/crash recovery, 2026-09-19) — **INCOMPLETE（未改执行链）**

- **DECISION** — 本轮**未修改 V2 执行链代码**：幂等键/执行状态机/crash recovery/UNKNOWN 属**执行语义**改动，回归风险高于 006；在无法完成 R6B-001..R6B-016 全回归（含 multiprocessing/crash injection）前不实施。
- 交付：幂等键设计（建议 `decision_id`）+ 状态机 + crash 三态 + 待实现清单；核心项 DATA_GAP。
- **H01_UNTOUCHED=TRUE**。V1 零接触。原始仓 HEAD/历史未变。
- 详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-REPAIR-006B-RESULT.md`。

## V2 Repair 007 (执行语义/幂等/crash/并发/ledger) — **INCOMPLETE（未改执行链）**

- **DECISION** — 未对 V2 执行链写入代码：R6B-001..016 + SAME_DECISION_X100（跨进程/crash/重启/reconciliation）**无法单轮安全完成**；不为 PASS 造假，**不提交未回归的执行链代码/死代码**。
- 交付：幂等键(`decision_id`)/状态机/crash 三态/ledger 唯一约束 **设计+计划**；核心项 DATA_GAP。
- **H01_UNTOUCHED=TRUE**；V1 零接触；原仓 d22d9fb/249 未变。
- 详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-REPAIR-007-RESULT.md`。

## V2 Repair 007A (执行链维修 STAGE-1/2, 2026-09-19) — 部分完成

- **已实施**：`execution/execution_guard.py`（幂等键=`decision_id` 的原子占位 + 单向状态机 + UNKNOWN 禁重试 + ledger 幂等）。
- **回归（真实模块/文件系统；threads+8 进程）**：`tests/test_execution_guard.py` **10/10 PASS**（含 R6B-003/004/005/007/009/010/011/012 + SAME_DECISION_X100=1 + 不同 decision 独立）。
- **wiring**：guard **尚未接入 shadow_run/executor** → 引擎级 R6B = DATA_GAP → `RUN_SAFETY_007=INCOMPLETE`。
- **H01/PIT/策略/V1/V3 未改**；原仓 HEAD/历史未变。详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-REPAIR-007A-RESULT.md`。

## V2 Repair 007 STAGE-3 (风险 A/B 修复, 2026-09-19)

- **已修**：`execution_guard.transition` 加跨进程锁（风险B）；`ledger_append_once` 先 append+fsync 后 marker、以账本内容去重（crash-一致，风险A）。
- **回归**：`tests/test_execution_guard.py` **12/12 PASS**（+R6B-008 ledger crash-一致、+R6B-004b 跨进程迁移单赢家）。
- **wiring**：guard 尚未接入 `shadow_run` 真实 TRADE 入口 → 引擎级 R6B = DATA_GAP → `RUN_SAFETY_007=INCOMPLETE`。
- H01/PIT/策略/V1/V3 未改；原仓 HEAD/历史未变。详见 `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V2-REPAIR-007-STAGE3-RESULT.md`。

---

_更新约定：每次协作层变更/新决策后更新本文件，并保持分类标注。_

## 2026-09-19 22:46 — REPAIR-007 STAGE4B
- EXECUTION_GUARD_WIRED=TRUE (run_cycle TRADE branch; key=decision_id)
- SINGLE_TRADE=PASS; DUP(engine-level)=PASS (ALREADY_CLAIMED)
- 其余 4B 回归=DATA_GAP; RUN_SAFETY_007=INCOMPLETE
- shadow_run.py 仅加 TRADE 分支 Guard 接线; 未改策略/Hermes/A1/A2/PIT/H-01/execution_mode/V1/V3

## 2026-09-19 22:56 - REPAIR-007 STAGE4B-REMAINDER
- R7 engine-level suite ALL PASS (single/x10/x100/TOCTOU20/cross8/cross10/diff-dec/crash-before/crash-after/sched-reentry/ledger-idempotency/unknown-safe)
- DECISION_ID_SCOPE=PER_RUN; UNKNOWN_AUTO_RETRY=0; MAX_SAME_DECISION_EXECUTOR_CALLS=1
- FIX: guard.ledger_append_once idempotency key -> (decision_id,event_type,position_id)
- DATA_GAP: LEDGER_CRASH_CONSISTENCY, V2_EXEC/LEDGER + V1 regression; RUN_SAFETY_007=INCOMPLETE

## 2026-09-19 23:01 - FINAL-CLOSEOUT-001
- R8 ledger crash-consistency ALL PASS (before-append/after-append/write-failure) + reject->FAILED + exception->UNKNOWN
- V2_EXECUTION/LEDGER_REGRESSION=PASS; LEDGER_PARTIAL_WRITE=DATA_GAP
- V1_REGRESSION=FAIL (1/81 pre-existing time-dependent V1 test; V1 source untouched)
- RUN_SAFETY_007=FAIL (gate: real FAIL present)
- DECISION_ID_SCOPE=PER_RUN

## 2026-09-19 23:06 - FINAL-CLOSEOUT-R8D
- LEDGER_PARTIAL_WRITE=PASS (partial/corrupt/truncated ledger -> restart blocked LEDGER_UNVERIFIABLE, no re-exec)
- R7+R8 re-run ALL PASS; DATA_GAPS=0; V2_EXECUTION_SAFETY_CORE=PASS
- V1_REGRESSION=FAIL (pre-existing time-dependent V1 test; untouched)
- RUN_SAFETY_007=FAIL (mechanical gate: V1_REGRESSION FAIL)

## 2026-09-19 23:10 - FORWARD-READINESS-001
- CURRENT_EXECUTION_MODE=BROKER_DEMO (broker armed, non-shadow run) -> PAPER_ISOLATION_GATE=FAIL
- PAPER_FORWARD_READY=NO; BLOCKER=EXECUTION_MODE_NOT_PAPER
- PAPER_EXECUTOR_SELECTION=PASS; EXECUTION_GUARD_PRESENT=PASS; V2_EXECUTION_SAFETY_CORE=PASS
- CONFIG_NOT_MODIFIED=TRUE; READ-ONLY audit

## 2026-09-19 23:16 - PAPER-STATE-FIX-001 (user-authorized)
- V2 execution_mode BROKER_DEMO -> PAPER; broker.enabled=false; broker_demo_enabled=false
- PAPER_EXECUTOR_SELECTION=PASS; PAPER_ISOLATION_GATE=PASS; PAPER_CONFIG_CANNOT_ROUTE_TO_BROKER=PASS
- V2_EXECUTION_SAFETY_CORE=PASS (R7 full PASS under PAPER)
- PAPER_STATE_READY=UNPROVEN (LEDGER_VERIFY/SCHEDULER_CONFIG_READ DATA_GAP); FORWARD_STARTED=FALSE

## 2026-09-19 23:18 - PAPER-STATE-FINAL-VERIFY-002
- FACT(current): CURRENT_EXECUTION_MODE=PAPER; BROKER_ENABLED=false; BROKER_DEMO_ENABLED=false
- (historical/LEGACY: earlier BROKER_DEMO audits)
- PAPER_ISOLATION_GATE=PASS; PAPER_CONFIG_CANNOT_ROUTE_TO_BROKER=PASS; CONFIG_CONSISTENCY=PASS
- LEDGER_VERIFY=PASS; LEGACY_BROKER_DEMO_HISTORY=TRUE
- SCHEDULER_CONFIG_READ/PAPER_SCHEDULER_PATH=DATA_GAP -> PAPER_STATE_READY=UNPROVEN
- FORWARD_STARTED=FALSE

## 2026-09-19 23:23 - PAPER-SCHEDULER-VERIFY-003
- V2_SCHEDULER: Windows Task \OpenClaw\hermes-v2-cycle -> trader_v2/runtime/v2_scheduled_cycle.py, every 15m, Running
- SCHEDULER_CONFIG_READ=PASS; PAPER_SCHEDULER_PATH=PASS; SCHEDULER_EXECUTION_MODE=PAPER
- V1_CRON=TRUE (openclaw cron hermes-trader-m15-cycle -> trader_v1); V2_CRON=FALSE
- V1_V2/V2_V3 isolation=PASS; PAPER_STATE_READY=PASS; FORWARD_STARTED=FALSE

## 2026-09-19 23:37 - BROKER-DEMO-FORWARD-48H START
- V2 execution_mode PAPER -> BROKER_DEMO (user GO); broker.enabled=true; broker_demo_enabled=true; allow_real_trading=false
- LIVE_GATE=LOCKED; MT5 demo terminal fxtm_demo_01 PID36460; MAGIC=90003; creds=.env.mt5_demo
- FORWARD_STARTED=TRUE start 2026-09-19T15:36:00Z end 2026-09-21T15:36:00Z; CODE_FREEZE=TRUE CONFIG_FREEZE=TRUE
- FORWARD_STATUS=INCOMPLETE (in progress); monitor cron every 3h

## 2026-09-20 02:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+3h, UTC 2026-09-19T18:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003; server=ForexTimeFXTM-Demo01 (DEMO)
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_triples=0 (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~3h/48h); V1/V3 untouched; REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-20 05:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+6h, UTC 2026-09-19T21:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003; server=ForexTimeFXTM-Demo01 (DEMO); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_triples=0 (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1; observe window 21:30Z a1/a2 OK (gold_spot 4378.65)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~6h/48h); V1/V3 untouched; REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-20 08:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+9h, UTC 2026-09-20T00:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003; server=ForexTimeFXTM-Demo01 (DEMO); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B...0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE; orig repo HEAD d22d9fb unchanged
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0 (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1; observe window 00:15Z a1/a2 OK (gold_spot 4378.65)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~9h/48h); V1/V3 untouched (V1 PID1348/V3 PID56544 unchanged); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-20 11:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+12h, UTC 2026-09-20T03:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); server=ForexTimeFXTM-Demo01 (DEMO); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE; orig repo HEAD d22d9fb unchanged
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0 (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1; observe window 03:15Z a1/a2 OK (gold_spot 4378.65)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~12h/48h); V1/V3 untouched (V1 PID1348/V3 PID56544 unchanged); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-20 14:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+15h, UTC 2026-09-20T06:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); server=ForexTimeFXTM-Demo01 (DEMO); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE; orig repo HEAD d22d9fb unchanged
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0 (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1; observe window 06:30Z a1/a2 OK (gold_spot 4378.65)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~15h/48h); V1/V3 untouched (V1 PID1348/V3 PID56544 unchanged); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-20 17:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+18h, UTC 2026-09-20T09:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); server=ForexTimeFXTM-Demo01 (DEMO); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE; orig repo HEAD d22d9fb unchanged
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (prev_hash==prior event_hash, GENESIS->evt12) (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1; observe window 09:15Z a1/a2 OK (gold_spot 4378.65)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~18h/48h); V1/V3 untouched (V1 PID1348/V3 PID56544 unchanged); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-20 19:30 - V3-HFT-FOUNDATION-AUDIT-001 (只读审计 · COMPLETE)
- **FACT** — V3_HFT_AUDIT=COMPLETE; **V3_HFT_FOUNDATION_STATUS=NOT_READY**
- **FACT** — V3_ORDER_SENT=FALSE; V3_LIVE_GATE=LOCKED (V3_LIVE/ORDER_SEND/FORWARD_ALLOWED=NO); MT5 只读 (fxtm_demo_v3, magic 90004, order_send 代码层 hard-block)
- **FACT** — V1_UNTOUCHED=TRUE; V2_UNTOUCHED=TRUE; V3_UNTOUCHED=TRUE; HERMES_UNTOUCHED=TRUE; READ_ONLY=TRUE
- **FACT** — 当前 V3 = RESEARCH_READONLY (统计可行性研究)，无 scheduler / agent / GPU 路径 / execution / ledger / model / label / feature engine
- **FACT** — 历史 tick: DUKA 7 月度 parquet, 15,563,968 行, 2023-09-01 .. 2026-08-04, 140 日; dup=0, ooo=0; HFT_TRAINING_DATA_STATUS=PARTIAL
- **FACT** — 成本: spread 实测 (p50 1.6449bp/0.347 USD-oz); commission/slippage 非实测 -> COST_MODEL=PARTIAL
- **FACT** — GPU: RTX A2000 Laptop 4GB, CUDA 12.6, torch 2.14.0+cu126, 计算+显存测试 PASS; V3 未使用
- **DATA_GAP (15)** — entry/exit latency, 实测 commission/slippage/min-move, features, labels, agent链, entry/exit engine, trade ledger, PIT, local_receive_time, tick loss detection, 历史缺口, 独立账号
- 报告: `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V3-HFT-FOUNDATION-AUDIT-001-RESULT.md` (+ `.json`)
- **DECISION** — 未进入修复阶段; 等待 `V3-HFT-FOUNDATION-REPAIR-001`

## 2026-09-20 19:55 - V3-HFT-FOUNDATION-REPAIR-001 (stage-1 infrastructure · PARTIAL)
- **FACT** — V3_HFT_FOUNDATION_STATUS=PARTIAL; BASE_COMMIT d22d9fb; BASE_CONFIG_SHA256 8F576ABD…CCB8 (CONFIG_CHANGED=NO); local FINAL_COMMIT f9a06e6
- **FACT** — 新增 foundation/ (14 模块 + tests) + schemas/ (7) + V3_FOUNDATION_VALIDATION.json
- **FACT** — TICK_ENGINE/GPU_ENGINE/FEATURE_ENGINE/PIT_GUARD/LEDGER/TICK_RECORDER/DATA_REGISTRY=READY
- **FACT** — EXECUTION_MEASUREMENT=PARTIAL (harness+mock 验证; 真实 demo calibration 未执行); COST_MODEL=PARTIAL (spread 实测 1.60bp@15.56M; commission/slippage DATA_GAP); LABEL_ENGINE=PARTIAL (net=DATA_GAP)
- **FACT** — TEST_COUNT=28 PASS=28 FAIL=0; GPU real compute CPU/GPU diff=0.0 (500k ticks, VRAM 29MiB)
- **FACT** — V3_AUTO_TRADING=FALSE; V3_ORDER_SEND=FALSE; V3_LIVE=FALSE; ORDER_SENT=FALSE (CALIBRATION_ORDERS_SENT=0)
- **FACT** — V1_UNTOUCHED=TRUE; V2_UNTOUCHED=TRUE (V2 BROKER_DEMO 48h forward 未受影响)
- **DATA_GAP** — real broker latency; measured commission/slippage; net labels; >=5000 real calibration samples; L2/trade flow; independent V3 account
- 报告: `collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V3-HFT-FOUNDATION-REPAIR-001-RESULT.md` (+ `.json`, `schemas/`)
- **DECISION** — 不进入自动交易; 下一步须单独建立 `V3-HFT-ALPHA-RESEARCH-001`

## 2026-09-20 19:45 - V3-CALIBRATION-PILOT-001 (preflight · BLOCKED)
- **FACT** — ORDER_SENT=FALSE; CALIBRATION_ORDERS_SENT=0 (未下任何单)
- **BLOCKER** — V3 initialize() 解析到 login 160759434，与 v1_host **同一账号** -> 非独立 demo (违反 §14)；data_path 亦非 fxtm_demo_v3 -> V3 实际未隔离
- **BLOCKER** — 市场休市 (XAUUSD tick age ~128999s)；XAUUSD 约 Sun 22:00Z 重开
- **FACT** — v2 login=160761384 (独立于 V3 target 160759434)；V1/V2 未改
- **NEED** — 给 V3 一个真正独立的 demo 账号 (login/password/server) 或用户对隔离方式明示
- 产物: reports/v3_hft_foundation/V3_CALIBRATION_PILOT_STATUS.json; foundation/calibration_pilot.py

## 2026-09-20 20:00 - V3-CALIBRATION-PILOT-001 (ARMED)
- **FACT** — 独立 demo 账号绑定成功: login=160764551 (Advo Demo) via /portable 实例 fxtm_demo_v3calib + 独立 env (.env.mt5_v3_calib, gitignored); preflight isolation.independent=TRUE
- **FACT** — 根因(自动换回): 原 v3 实例非 /portable + 蹭 V1 的 .env.mt5_demo(DEMO_MT5_LOGIN=160759434)。已彻底改掉。V1(160759434)/V2(160761384) 未改。
- **FACT** — 市场休市; 已排程 Windows 任务 \OpenClaw\v3-calibration-pilot @ 2026-09-21 06:30 GMT+8 (10 roundtrips, 0.01, MAGIC 90004, 含 PILOT_DONE 防重)
- **FACT** — ORDER_SENT=FALSE 至今; 当前跑 --run 被闸门拒绝(market closed)
- 产物: foundation/calibration_pilot.py, run_calibration_pilot.cmd, state/V3_CALIBRATION_PILOT_STATUS.json

## 2026-09-20 20:08 - V3-HFT-CALIBRATION-PILOT-001 (ARMED, spec-compliant)
- **FACT** — 按任务书重建 pilot: MAX_CALIBRATION_ROUND_TRIPS=20(硬上限, n>20 拒绝), 冻结方向(交替 LONG/SHORT) + 冻结持有序列[100,250,500,1000,2000]ms, hash=18568a95…, CALIBRATION_VOLUME=FIXED 0.01, NO_AUTO_RETRY, 24 项自动停止门, MT5 对账(cid↔order↔deal↔ledger, PASS 才计入), Ledger 7 事件 hash-chain
- **FACT** — 隔离: 用独立实例 fxtm_demo_v3calib / login 160764551 (spec §4 写 fxtm_demo_v3 但该实例实为 V1 共享账号 160759434 → 按 §3 用隔离实例, 已记录偏差)
- **FACT** — preflight: independent=TRUE, positions=0, spec 已记录(contract 100/tick 0.1/min 0.01); selftest(MOCK) chain_ok=true
- **FACT** — 市场休市 → 0 单; ORDER_SENT=FALSE
- **FACT** — 已排程 \OpenClaw\v3-calibration-pilot @ 2026-09-21 06:30 GMT+8 (--n 20)
- 交物: CHATGPT-TASK-V3-HFT-CALIBRATION-PILOT-001-RESULT.md(+.json, PRELIMINARY/INCOMPLETE); state/V3_CALIBRATION_PILOT_STATUS.json
- **DECISION** — 真实 20 笔后出 FINAL(REAL_DATA), 然后 WAIT_FOR_AUDIT; 不自动扩到 5000

## 2026-09-20 20:26 - MT5-INSTANCE-ISOLATION-AUDIT-FIX-001 (PASS)
- **FACT** — BEFORE=4 running terminals -> AFTER=3 (canonical): V1 ProgramFiles/160759434, V2 fxtm_demo_01/160761384, V3 fxtm_demo_v3calib/160764551
- **FACT** — 4th instance root cause: fxtm_demo_v3(non-portable) 建时蹭 V1 creds(.env.mt5_demo) + 4 处 no-path mt5.initialize() 的“默认终端”劫持 -> 幽灵实例反复自启; calibration 又建了 fxtm_demo_v3calib
- **FACT** — 修复: pin 显式 terminal path 于 dashboard/_quote_loop, self_collect/mt5_live_collect, demo_exec_instrument, trader_v1/broker_mt5_demo(1行, 语义不变, 见报告§6); 重启 dashboard; 优雅停幽灵(无/F), 90s 未自启; V3 config/adapter 改指 fxtm_demo_v3calib
- **FACT** — V3_CALIBRATION_PAUSED=TRUE (\\OpenClaw\\v3-calibration-pilot Disabled); ORDER_SENT=FALSE
- **FACT** — V2_UNTOUCHED=TRUE; V1 strategy/config/scheduler/ledger 未改(仅 1 行实例管理 pin, 可回退)
- 产物: reports/v3_hft_foundation/MT5_INSTANCE_{REGISTRY,ISOLATION}.json; CHATGPT-TASK-MT5-INSTANCE-ISOLATION-AUDIT-FIX-001-RESULT.md(+.json)
- **DECISION** — MT5_INSTANCE_ISOLATION=PASS; WAIT_FOR_AUDIT; V3 calibration 暂停待审计

## 2026-09-20 20:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+21h, UTC 2026-09-20T12:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); server=ForexTimeFXTM-Demo01 (DEMO); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE; orig repo HEAD d22d9fb unchanged
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (prev_hash==prior event_hash, GENESIS->evt12) (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1; observe window 12:15Z a1/a2 OK (gold_spot 4378.65)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~21h/48h); V1/V3 untouched (V1 PID1348/V3 PID56544 unchanged); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-20 20:52 - MT5-INSTANCE-ISOLATION-RESTART-VERIFY-001 (PASS)
- **FACT** — 重启验证通过: R1 tick-collector(新进程, pinned)/R2 dashboard 重启/R3 V1 broker 调用/R4 V3 终端优雅停+显式重启/R5 50s soak → 幽灵 fxtm_demo_v3=0, 维持 3 实例
- **FACT** — 账号两两不同: V1 160759434 / V2 160761384 / V3 160764551; V3 重启后回到 160764551
- **FACT** — V3_CALIBRATION_PAUSED=TRUE; ORDER_SENT=FALSE; V2_UNTOUCHED=TRUE
- 产物: CHATGPT-TASK-MT5-INSTANCE-ISOLATION-RESTART-VERIFY-001-RESULT.md(+.json); reports/v3_hft_foundation/MT5_INSTANCE_ISOLATION.json 已并入 restart_verify

## 2026-09-20 21:01 - CALIBRATION-PILOT-001 RESUME + V1 pin registered
- **FACT** — 用户确认保留 V1 connection pin: 登记 V1_MT5_CONNECTION_SAFETY_PIN; V1_STRATEGY_UNTOUCHED=TRUE, V1_TRADING_LOGIC_UNTOUCHED=TRUE, V1_CONNECTION_PIN_CHANGED=TRUE, V1_FILE_TREE_UNTOUCHED=FALSE (state/V1_MT5_CONNECTION_SAFETY_PIN.json)
- **FACT** — pilot 硬化: 新增硬门槛(MT5 实例数==3, 无 fxtm_demo_v3 幽灵, 无 unmapped/orphan, V1/V2 映射, LIVE 门, 账号/持仓) + HALT 不自行修复继续; 新增 V3_CALIBRATION_PREFLIGHT
- **FACT** — V3_CALIBRATION_PREFLIGHT(12:59Z): 全部门 PASS, 仅 MARKET_OPEN=false(周末) -> READY_TO_START=false
- **FACT** — 恢复排程 \\OpenClaw\\v3-calibration-pilot(Enabled) @ 2026-09-21 06:30 GMT+8, --n 20; MAX=20 硬上限
- **FACT** — V3_CALIBRATION_PAUSED=FALSE(已恢复); ORDER_SENT=FALSE; 20 笔后自动停 -> WAIT_FOR_CHATGPT_AUDIT

## 2026-09-20 23:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+24h, UTC 2026-09-20T15:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); server=ForexTimeFXTM-Demo01 (DEMO); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE; orig repo HEAD d22d9fb unchanged
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (prev_hash==prior event_hash, GENESIS->evt12) (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (weekend); cycle_result=MARKET_CLOSED_SKIP; 0 orders / 0 trades this window; missed_cycles=1; observe window 15:30Z a1/a2 OK (gold_spot 4378.65)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~24h/48h); V1/V3 untouched (V1 PID1348; V3 PID49300 after MT5 isolation restart-verify); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-21 02:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+27h, UTC 2026-09-20T18:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); account 160761384 / server=ForexTimeFXTM-Demo01 (DEMO); MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (prev_hash==prior event_hash, GENESIS->evt12) (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260919-145431-c5a1; run_status=RUNNING; market_open=false (pre-open, XAUUSD reopens ~Sun 22:00Z); cycle_result=MARKET_CLOSED_SKIP; last_completed 2026-09-20T18:22Z; 0 orders / 0 trades this window; observe window 18:15Z a1/a2 OK (gold_spot 4378.65)
- REPO: orig repo HEAD advanced d22d9fb -> 88f7228 (non-V2 workstreams: v3-calib resume / mt5-instance-isolation fix / money-hunter weekly review); d22d9fb is ancestor; V2 config still hash-frozen (CONFIG_UNCHANGED=TRUE)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~27h/48h); V1/V3 untouched (V1 PID1348; V3 PID49300); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only

## 2026-09-21 05:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+30h, UTC 2026-09-20T21:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); account 160761384 / server=ForexTimeFXTM-Demo01 (DEMO); MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); creds=.env.mt5_demo (C:\AIQuant\.env.mt5_demo)
- CONFIG_INTEGRITY: sha256(config)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == freeze baseline -> CONFIG_UNCHANGED=TRUE
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (GENESIS->evt12) (last evt 2026-09-11T13:09:29Z demo-calibration); per-run ledgers append-only
- RUN ACTIVE run_id=V2-PAPER-20260920-200702-f507; run_status=RUNNING; market_open=false (pre-open, XAUUSD reopens ~Sun 22:00Z, ~23min out); cycle window 21:30Z decision=WAIT / 0 orders / 0 trades; last_completed 2026-09-20T21:37:35Z; observe window 19:45Z a1/a2 OK (gold_spot 4378.65); missed_cycles=1
- NOTE: health.run_id == ACTIVE.run_id (V2-PAPER-20260920-200702-f507) -> 早前 run_id 漂移(OBSERVATION @ V2-FULL-AUDIT-001)已消除
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~30h/48h); V1/V3 untouched (V1 PID1348; V3 PID49300); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only; END not reached -> no end-report this cycle

## 2026-09-21 06:45 - V3-HFT-CALIBRATION-PILOT-001 (FINAL, HALTED)
- The scheduled bounded pilot ran at market open: \OpenClaw\v3-calibration-pilot, 06:30 GMT+8 (= 2026-09-20T22:30:01Z), exit=0; `run_calibration_pilot.cmd --run --n 20`.
- RESULT: **HALTED**, halt_reason="UNKNOWN entry retcode=10027 (NO_AUTO_RETRY)". 0 roundtrips / 0 real samples / MOCK_EXECUTION=false / RECONCILIATION=PARTIAL / WAIT_FOR_AUDIT=true.
- ROOT CAUSE: retcode 10027 = TRADE_RETCODE_CLIENT_DISABLES_AT -> automated trading DISABLED in the client terminal `fxtm_demo_v3calib` (terminal-level Algo Trading OFF). account_info().trade_allowed=true (account OK); block is terminal-side. First time the real order_send path was exercised (prior V3 work was MOCK only).
- EVIDENCE: instance fxtm_demo_v3calib login=160764551; account before==after (balance/equity 5000, positions 0); ledger v3_calibration_ledger.jsonl 4 events hash-chain OK (START->ORDER_REQUEST price 4376.02 bid 4375.79 spread 0.23->BROKER_RESPONSE order_id 0->COMPLETE roundtrips=0); guard data/calibration/PILOT_DONE={"status":"HALTED","n":0}; V3_EXECUTION_PROFILE/V3_COST_PROFILE all n=0.
- SAFETY: V3_LIVE=false / V3_AUTO_TRADING=false / ORDER_SENT=false / V1_UNTOUCHED=true / V2_UNTOUCHED=true. MT5 hosts intact: V1 160759434 (pid1348) / V2 160761384 (fxtm_demo_01 pid36460) / V3 160764551 (fxtm_demo_v3calib pid49300); UNMAPPED=0; no ghost fxtm_demo_v3.
- NEXT (needs explicit user GO; no auto-repair): enable Algo Trading on fxtm_demo_v3calib terminal -> clear PILOT_DONE -> re-arm & re-run at market open -> FINAL REAL_DATA -> STOP/WAIT_FOR_AUDIT. Frozen spec unchanged (MAX=20, no expansion to 5000).
- RESULT files updated: collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V3-HFT-CALIBRATION-PILOT-001-{RESULT.md,json} (FINAL).

## 2026-09-21 07:06 - V3-HFT-CALIBRATION-PILOT-001 (FINAL, **PASS** 20/20)
- User enabled Algo Trading on `fxtm_demo_v3calib` (terminal-level trade_allowed: V1 True / V2 True / V3 now True). Re-ran bounded pilot -> **PASS**.
- RESULT: status=PASS, n_samples=20, VALID_ENTRY_FILL=20, VALID_EXIT_FILL=20, RECONCILIATION=PASS, MOCK_EXECUTION=false, REAL_DATA=20, CALIBRATION_AUTO_STOP=true, WAIT_FOR_AUDIT=true. Run 2026-09-20T23:05:42Z -> 23:06:13Z (~30s).
- MEASURED (n=20, 0.01 lot XAUUSD): entry signal->fill mean 279.4ms (request->ack 273.9ms = broker RTT dominant; ack->fill 5.6ms); exit signal->fill mean 275.2ms; entry slippage median 0 / mean +0.017 USD (max +0.183); exit slippage median 0 / mean -0.032 (min -0.686); spread ~0.4115 bps; NET_ROUND_TRIP_COST model mean 0.1375 USD.
- ACCOUNT: 5000 -> **4992.56** (net -7.44 USD / 20 = -0.372 USD per round-trip realized); orders=0 / positions=0 residual. Ledger `data/hft_ledger/v3_calibration_ledger.jsonl` 131 events, hash-chain verify OK.
- DEVIATION (disclosed, user-GO'd): frozen pilot hardcoded `ORDER_FILLING_IOC` -> broker rejected with retcode **10030 INVALID_FILL** (XAUUSD `filling_mode=1` = FOK only; verified via order_check). Fixed V3-only: `_filling_mode()` auto-selects FOK/IOC/RETURN; entry+exit use it. C:\AIQuant local commit **98ef9a7**. Frozen spec otherwise unchanged (MAX=20, frozen seq hash 18568a95, NO_AUTO_RETRY).
- SAFETY: V3_LIVE=false / V3_AUTO_TRADING=false / ORDER_SENT_LIVE=false / V1_UNTOUCHED=true / V2_UNTOUCHED=true. MT5 hosts intact: V1 160759434 (pid1348) / V2 160761384 (fxtm_demo_01 pid36460) / V3 160764551 (fxtm_demo_v3calib pid49300); UNMAPPED=0; no ghost.
- Prior halts preserved: `PILOT_DONE.halted_20260920T223001Z` (10027) / `PILOT_DONE.halted_20260920T230018Z` (10030). Current guard `PILOT_DONE={status:PASS,n:20}`.
- NEXT: STOP -> **WAIT_FOR_CHATGPT_AUDIT**. No expansion to 5000; any expansion = separate V3-HFT-CALIBRATION-EXPANSION-001 (not started). No Alpha / no HFT training / no model optimization.
- RESULT files: collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-V3-HFT-CALIBRATION-PILOT-001-{RESULT.md,json} (FINAL PASS).
## 2026-09-21 08:40 - BROKER-DEMO-FORWARD-48H MONITOR (T+33h, UTC 2026-09-21T00:40Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION; flag state/FORWARD_VALIDATION_ALLOWED=true
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); account 160761384 / server=ForexTimeFXTM-Demo01 (DEMO, trade_mode=0, trade_allowed=true) / balance 1035.01 equity 1043.24; MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); creds=C:\AIQuant\.env.mt5_demo (present)
- CONFIG_INTEGRITY: sha256(config/v2_config.json)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == FREEZE baseline (V2_BROKER_DEMO_FORWARD_FREEZE_...json) -> CONFIG_UNCHANGED=TRUE
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (prev_hash==prior event_hash, GENESIS->evt12); all env/execution_mode=BROKER_DEMO (last evt 2026-09-11T13:09:29Z demo-calibration); append-only
- RUN ACTIVE run_id=V2-PAPER-20260920-200702-f507; health.run_id==ACTIVE.run_id; run_status=RUNNING; market_open=true; current_cycle 2026-09-21T00:30Z decision=WAIT / 0 orders / 0 trades this window; last_completed 00:38:03Z; counters attempted=399 wait=279 trade=26 reject=0 missed=1 dup_prevented=5; replay=MATCH; agent1/2/hermes/ledger status OK; health.forward_validation_allowed=false (informational: differs from flag file)
- OBSERVATION: fxtm_demo_01 demo account holds 1 open position (ticket 2376556551 XAUUSD SELL 0.01, magic 90003, comment "v2-exec", opened 2026-09-18T22:52:29Z) NOT present in ledger/hermes_v2_ledger.jsonl (ledger last evt 2026-09-11); pending_orders=0. In V2 demo scope / magic 90003 / demo=true -> NOT a LIVE violation; flagged for audit (opened before forward window start 2026-09-19T15:36Z)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~33h/48h, ~15h remaining); V1 untouched (V1 PID1348 active); V3 untouched (V3 PID49300); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only; END (2026-09-21T15:36Z) not reached -> no end-report this cycle
## 2026-09-21 11:39 - BROKER-DEMO-FORWARD-48H MONITOR (T+36h, UTC 2026-09-21T03:39Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION; flag state/FORWARD_VALIDATION_ALLOWED=true
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01); account 160761384 / server=ForexTimeFXTM-Demo01 (DEMO, trade_mode=0) / balance 1035.01 equity 1047.05; MAGIC=90003 (execution/fxtm_demo_adapter.py; V1=90002/V3=90004); creds=C:\AIQuant\.env.mt5_demo (present)
- CONFIG_INTEGRITY: sha256(config/v2_config.json)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == FREEZE baseline -> CONFIG_UNCHANGED=TRUE
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (seq 1..12, GENESIS->evt12); all env/execution_mode=BROKER_DEMO (last evt 2026-09-11T13:09:29Z demo-calibration); append-only
- RUN ACTIVE run_id=V2-PAPER-20260920-200702-f507; health.run_id==ACTIVE.run_id; run_status=RUNNING; market_open=true; current_cycle 2026-09-21T03:30Z decision=TRADE / execution_result=REJECTED:POSITION_BUSY / 0 paper_orders / 0 trades this window; last_completed 03:38:03Z; counters attempted=411 wait=286 trade=31 reject=0 missed=1 dup_prevented=5; replay=MATCH; agent1/2/hermes/ledger OK; health.forward_validation_allowed=false (informational: differs from flag file true)
- POSITION: fxtm_demo_01 holds 1 open XAUUSD SHORT 0.01 ticket 2376556551 magic 90003 (opened 2026-09-18T22:52:29Z, profit +11.62) NOT in ledger/hermes_v2_ledger.jsonl (last evt 2026-09-11); demo=true / magic 90003 -> NOT a LIVE violation; carried from prior cycle (pre-window open), audit-flagged
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~36h/48h, ~12h remaining); V1 untouched (V1 PID1348); V3 untouched (V3 PID49300); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only; END (2026-09-21T15:36Z) not reached -> no end-report this cycle

## 2026-09-21 14:37 - BROKER-DEMO-FORWARD-48H MONITOR (T+39h, UTC 2026-09-21T06:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION; flag state/FORWARD_VALIDATION_ALLOWED=true
- MT5 fxtm_demo_01 terminal64.exe PID=36460 (portable, C:\AIQuant\mt5_instances\fxtm_demo_01) PRESENT; probe account 160761384 / server=ForexTimeFXTM-Demo01 (DEMO, trade_mode=0, currency=USD, leverage=500) / balance 1064.13 equity 1064.13 / positions=0; MAGIC=90003 (execution/fxtm_demo_adapter.py MAGIC=90003; V1=90002/V3=90004); creds=C:\AIQuant\.env.mt5_demo (present)
- CONFIG_INTEGRITY: sha256(config/v2_config.json)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == FREEZE baseline (V2_BROKER_DEMO_FORWARD_FREEZE_V2-BROKER-DEMO-FWD-20260919-153600.json) -> CONFIG_UNCHANGED=TRUE
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_event_hash=0; hash-chain OK (previous_event_hash==prior event_hash, GENESIS->evt-000012); all env/execution_mode=BROKER_DEMO (last evt 2026-09-11T13:09:29Z demo-calibration); append-only, unchanged since last cycle
- RUN ACTIVE run_id=V2-PAPER-20260920-200702-f507; health.run_id==ACTIVE.run_id; run_status=RUNNING; market_open=true; current_cycle 2026-09-21T06:15Z decision=WAIT / 0 paper_orders / 0 trades this window; last_completed 2026-09-21T06:23:02Z; counters attempted=422 wait=297 trade=31 reject=0 missed_cycles=1 recovery=1 dup_prevented=5; replay=MATCH (shadow_guardian 90 cycles / 94 snapshots / 0 mismatch); agent1/2/hermes/ledger status OK; health.forward_validation_allowed=false (informational: differs from flag file true, as in prior cycles)
- POSITION: fxtm_demo_01 now FLAT (positions=0). Prior cycle open XAUUSD SHORT 0.01 ticket 2376556551 magic 90003 (opened 2026-09-18T22:52:29Z, pre-window) is no longer present; demo balance moved 1035.01 -> 1064.13 (+29.12 realized). Event NOT in ledger/hermes_v2_ledger.jsonl (last evt 2026-09-11). demo=true / magic 90003 -> NOT a LIVE violation; audit-flagged (ledger does not record this demo-shell position lifecycle)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~39h/48h, ~9h remaining); V1 untouched (V1 PID1348 present); V3 untouched (V3 PID49300 present, not in V2 scope); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only; END (2026-09-21T15:36Z) not reached -> no end-report this cycle

## 2026-09-21 17:38 - BROKER-DEMO-FORWARD-48H MONITOR (T+42h, UTC 2026-09-21T09:38Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; LIVE_ALLOWED=false; execution_mode!=LIVE -> NO VIOLATION; flag state/FORWARD_VALIDATION_ALLOWED=true
- MT5 fxtm_demo_01 terminal64.exe PID=36460 PRESENT (C:\AIQuant\mt5_instances\fxtm_demo_01); probe account 160761384 / server=ForexTimeFXTM-Demo01 (DEMO, trade_mode=0, currency=USD, leverage=500) / balance 1064.02 equity 1058.50; MAGIC=90003 (execution/fxtm_demo_adapter.py MAGIC=90003; V1=90002/V3=90004)
- CONFIG_INTEGRITY: sha256(config/v2_config.json)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == FREEZE baseline -> CONFIG_UNCHANGED=TRUE
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 lines; bad_json=0; dup_event_id=0; dup_seq=0; dup_triples=0; hash-chain OK (previous_event_hash==prior event_hash, seq 1..12); all env/execution_mode=BROKER_DEMO (last evt 2026-09-11T13:09:29Z demo-calibration); append-only, unchanged since last cycle
- RUN ACTIVE run_id=V2-PAPER-20260920-200702-f507; health.run_id==ACTIVE.run_id; run_status=RUNNING; market_open=true; current_cycle 2026-09-21T09:15Z decision=WAIT / 0 paper_orders / 0 trades this window; last_completed 2026-09-21T09:23:05Z; counters attempted=434 wait=306 trade=34 reject=0 missed_cycles=1 recovery=1 dup_prevented=5; replay=MATCH (shadow_guardian 90 cycles / 94 snapshots / 0 mismatch); agent1/2/hermes/ledger status OK; health.forward_validation_allowed=false (informational: differs from flag file true, as in prior cycles)
- POSITION: fxtm_demo_01 holds 1 open XAUUSD LONG 0.01 ticket 2376639771 magic 90003 (server-time opened 2026-09-21T11:08:04Z, i.e. ~08:08Z UTC at GMT+3; current -5.52) NOT present in ledger/hermes_v2_ledger.jsonl (ledger last evt 2026-09-11); demo=true / magic 90003 -> NOT a LIVE violation; audit-flagged (ledger does not record this demo-shell position lifecycle)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~42h/48h, ~6h remaining); V1 untouched (V1 PID1348 present); V3 untouched (V3 PID49300 present, not in V2 scope); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only; END (2026-09-21T15:36Z) not reached -> no end-report this cycle

## 2026-09-21 20:38 - BROKER-DEMO-FORWARD-48H MONITOR (T+45h, UTC 2026-09-21T12:37Z)
- SAFETY=PASS: execution_mode=BROKER_DEMO; broker.enabled=true; broker_demo_enabled=true; live_trading=false; allow_real_trading=false; execution_mode!=LIVE; LIVE_ALLOWED absent -> NO VIOLATION
- MT5 fxtm_demo_01 terminal64.exe PID=36460 PRESENT (C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe); MAGIC=90003 (execution/fxtm_demo_adapter.py MAGIC=90003; V1=90002, V3=90004)
- CONFIG_INTEGRITY: sha256(config/v2_config.json)=B0CC254B809DA52844778BBBB8A298DF77DD2D031A8353FEC3F982DAC26BE0E5 == FREEZE baseline -> CONFIG_UNCHANGED=TRUE
- LEDGER ledger/hermes_v2_ledger.jsonl: 12 events; bad_json=0; seq_unique=TRUE; event_id_unique=TRUE; hash_chain_ok=TRUE (seq 1..12, previous_event_hash==prior event_hash); env+execution_mode all BROKER_DEMO; last evt 2026-09-11T13:09:29Z (demo calibration); append-only, unchanged since last cycle
- ACCOUNT (read-only probe via C:\AIQuant\.venv acc_probe.py; login 160761384 / server ForexTimeFXTM-Demo01): demo=true trade_mode=0 currency=USD leverage=500; balance 1064.02; equity 1068.98; margin 8.70; margin_free 1060.28; positions=1
- POSITION: XAUUSD LONG 0.01 ticket 2376639771 magic 90003 entry 4348.59 current 4353.55 sl 4338.63 tp 4383.92 profit +4.96 (opened server-time 2026-09-21T11:08:04Z = ~08:08Z UTC at GMT+3); carried over from prior cycle; NOT present in ledger/hermes_v2_ledger.jsonl (ledger last evt 2026-09-11); demo=true / magic 90003 -> NOT a LIVE violation; audit-flagged (ledger does not record this demo-shell position lifecycle)
- RUN ACTIVE run_id=V2-PAPER-20260920-200702-f507; health.run_id==ACTIVE.run_id; run_status=RUNNING; market_open=true; current_cycle 2026-09-21T12:30Z decision=WAIT / 0 paper_orders; last_completed 2026-09-21T12:37:38Z; counters attempted=447 wait=318 trade=34 reject=1 missed_cycles=1 recovery=1 dup_prevented=5; replay=MATCH (shadow_guardian 90 cycles / 94 snapshots / 0 mismatch); agent1/agent2/hermes/ledger status OK; health.forward_validation_allowed=false (informational: differs from flag file true, as in prior cycles)
- FORWARD_STATUS=INCOMPLETE (in progress, elapsed ~45h/48h, ~3h remaining); this monitor is read-only (no policy/code/config/prompt/PIT/Guard change); V1 not modified (V1 PID1348 present); V3 out of V2 scope (PID49300 present); REAL_BROKER_ACCESS scoped to V2 fxtm_demo_01 only; END (2026-09-21T15:36Z) not reached -> no end-report this cycle