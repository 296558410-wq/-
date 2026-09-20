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
