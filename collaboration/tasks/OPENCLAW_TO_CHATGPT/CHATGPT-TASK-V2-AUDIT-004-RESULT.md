# CHATGPT-TASK-V2-AUDIT-004-RESULT.md

**Task**: V2-AUDIT-004（最终穿透审计 / 只读验证）
**执行**: OpenClaw（只读 + 纯内存 mock）｜**复核**: ChatGPT｜**决策**: 用户
**标签**: FACT / SUPPORTED / OBSERVATION / DATA_GAP / UNRESOLVED

## 1. Executive Summary

- **FACT** Agent1 特征清单已机械提取（`features.py`：ma/ema/rsi14/atr14/atr_pct/realized_vol_ann/vwap/structure/trend_range/exp_cont/range60/recent_move_bps/price_vs_sma20_bps/breakout/bar_behavior…）；未见 `center=True`/负 shift/bfill 于已提取片段。**穷尽 look-ahead 未证** → DATA_GAP。
- **FACT** Agent2 PIT 字段：`cot.publication_timestamp_unknown=True`、`pit_status=UNKNOWN`（除非 publication 已知）；`news.first_seen_at = retrieved_at`；`point_in_time` 有 `retrieved_at`。→ COT/geopolitics **PIT 未证** → DATA_GAP。
- **FACT（本轮新测）** 并发 `start_run` harness：两线程并发调用，**同一秒收敛到同一 rid**（`V2-PAPER-20260919-132728-1ee2`），`run_dirs=1`、`ACTIVE=1`、**无 JSON 损坏**。→ 该测试**未有效制造“两个不同 run”竞争**，**并发安全性仍 DATA_GAP**（不能因本次未观察到而判安全）。
- **FACT** 当前运行态：`ACTIVE = …084c`（non-shadow / `BROKER_DEMO`）；4 个 run `status=RUNNING`；`BROKER_ORDER_SENT=FALSE`、`FORWARD_STARTED=FALSE`。
- 结论：多项核心安全性质仍 **DATA_GAP**；当前 ACTIVE 为 **non-shadow BROKER_DEMO**（非 PAPER）→ 按任务书判定 **NOT READY FOR FORMAL FORWARD**（且存在 HIGH 类条件）。

## 2. Agent1 PIT

- 复用：`market_data.py:165` 未收盘剔除；`validate.py:31` 未来 bar 拒绝；`local_bars` `label/closed=left`。
- **FACT** 特征清单（上引）均为**已过滤 close 序列**上的函数；未逐特征做未来依赖证明。
- **A1-02 统一 cutoff**：**DATA_GAP**（未见全局 cutoff_time；各 tf `last_bar_ts` 独立）。
- **A1-03 逐特征 look-ahead**：**DATA_GAP**（清单已列；未穷尽 rolling/quantile/normalize）。
- **A1-05 lineage 逐层**：**DATA_GAP**。
- **A1-06 fallback 入交易**：门禁在 `context` 层（非 mt5→DEGRADED）；**agent1 内部无 mt5 校验** → 逐字段证明 **DATA_GAP**。

## 3. Agent2 PIT

- **FACT** `evidence._pit_valid(published,retrieved)`；缺 `published_at` → `unknown`（**不得视为 PIT-valid**）。
- **FACT** `cot.publication_timestamp_unknown=True`；`pit_status=UNKNOWN`；`cot_timestamp_confidence=approximate(report_date only)` → **COT release time 不可靠**（且 CTFC 源 403 缺失）。
- **FACT** `news.first_seen_at = retrieved_at`（≠ first-public）。
- **A2-01..A2-06**：DXY/UST10Y/VIX/TIP/GLD/GC 是否读到 revised/latest、ETF publication、News updated 倒灌、Geopolitics first-public → 逐项 **DATA_GAP**。

## 4. Replay Future Evidence（E_after 注入）

**DATA_GAP — 未执行**。未构造内存 replay 的 `E_after` 注入（T-10/T/T+10 三 decision）。`replay_inputs.build_snapshot` 取显式参数、decision 存 `input_hash`，但**未证实质** → **E_AFTER_BLOCKED=DATA_GAP**。

## 5. Run Lifecycle（R-01）

**FACT/SUPPORTED**：`start_run()` 写 `RUN_META/run_manifest/run_state` 并**覆盖 `ACTIVE.json`**；`cycle()` 窗口尽才 `finalize`。→ `ACTIVE=B, health=A, A/B 皆 RUNNING` **允许且当前即如此**（`ACTIVE=…084c`、`health=…8648`）。旧 run **未 finalize** → 多 RUNNING 残留。**ACTIVE_ROOT_CAUSE=SUPPORTED**（见 §7）。

## 6. Concurrency

- **R-02 并发 start_run**：**已尝试**（fake env/临时目录）。结果：两线程同秒收敛同 rid → `two_runs_created=false`、无损坏。→ **CONCURRENT_START_TESTED=DATA_GAP**（未有效制造差异 run 竞争）。
- **R-03 并发 cycle / R-04 幂等 / R-05 crash recovery**：**DATA_GAP — 未执行**。

## 7. Duplicate Execution / 8. Crash Recovery

**DATA_GAP**（见 §6）。唯一旁证：`cycle` 内窗口 dedup 与 ledger append 存在（未证全部路径幂等）。

## 9. Exception Paths

**FACT（复用第三轮）** `shadow_run.py` 19 处 except：Agent 失败计数继续；broker/reconcile/price_space 失败→错误标记/reject。**未发现 `failure→default→TRADE`**；逐条证明 → **DATA_GAP**。

## 10. V1/V2/V3 Runtime Isolation

- **FACT（静态）** V2 独立实例 `fxtm_demo_01`（tag 硬校验）、server Demo01、magic 90003；V1 90002；V3 `fxtm_demo_v3`/90004。
- **DATA_GAP**：默认 MT5 路径/`%APPDATA%`/共享缓存/进程/PID 的**运行期**交叉未证。

## 11. Finding Register

| ID | 级 | 标签 | 事实 |
|---|---|---|---|
| H-01 | HIGH | FACT | 当前 ACTIVE = non-shadow + BROKER_DEMO → **真实 demo 执行器可达**（第三轮 E-03 实证）；`BROKER_ORDER_SENT=FALSE` 仅因无合格周期 |
| M-01 | MEDIUM | FACT/SUPPORTED | 4 个 run_state=RUNNING 并存（旧 run 未 finalize）；ACTIVE 覆盖式写入 |
| M-02 | MEDIUM | UNRESOLVED | 短命 run 归因未定 |
| M-03 | MEDIUM | DATA_GAP | Agent1/Agent2/Replay PIT、并发、crash recovery 未证 |

## 12. DATA_GAP Register

1 A1 统一 cutoff；2 A1 逐特征 look-ahead；3 A1 lineage 逐层；4 A1 fallback 逐字段；5 A2 逐字段 PIT；6 CFTC release；7 ETF publication；8 News updated 倒灌；9 Geopolitics first-public；10 Replay E_after；11 并发 start_run；12 并发 cycle/幂等/crash 恢复；13 三实例运行期隔离。

## 13. Final Q&A

- **E4-Q1** SUPPORTED（第三轮 E-01）；**E4-Q2** SUPPORTED（E-02）；**E4-Q3** **是**（当前 non-shadow BROKER_DEMO）；**E4-Q4** DATA_GAP
- **A4-Q1** DATA_GAP；**A4-Q2** DATA_GAP；**A4-Q3** DATA_GAP；**A4-Q4** DATA_GAP；**A4-Q5** DATA_GAP（已见片段无 center/负 shift/bfill）
- **B4-Q1** DATA_GAP；**B4-Q2** DATA_GAP（COT release 不可靠）；**B4-Q3** DATA_GAP；**B4-Q4** DATA_GAP；**B4-Q5** DATA_GAP；**B4-Q6** DATA_GAP
- **R4-Q1/Q2/Q3** DATA_GAP
- **L4-Q1** SUPPORTED（未 finalize 残留）；**L4-Q2** DATA_GAP；**L4-Q3** DATA_GAP；**L4-Q4** DATA_GAP；**L4-Q5** DATA_GAP
- **I4-Q1** DATA_GAP；**I4-Q2** DATA_GAP；**I4-Q3** DATA_GAP

## 14. Evidence / Test Artifacts

- Harness（workspace，非交易目录）：`v2_exec_harness.py`（第三轮，E-01..E-09）、`v2_conc_harness.py`（本轮，并发 start_run）。
- 代码：`agents/technical/features.py`、`market_data.py:165`、`data_sources/validate.py:31`、`local_bars.py:41-43`、`hermes/context.py:96-127`、`agents/macro_global/{agent2,evidence,sources}.py`、`runtime/shadow_run.py:110,141-148,156-174,188-197,517-526`、`execution/fxtm_demo_adapter.py`。
- 运行态：`state/runs/ACTIVE.json`、`v2_run_health.json`、`research/runs/{…084c,…8648,…b3c2,…59f4}`。

## 15. Git Integrity

仅新增本报告 + `CURRENT_STATUS.md`；无 trading/config/state 修改；无 force/amend/rebase/squash/reset。

## 16. Final Acceptance Fields

```text
AUDIT_004_EXECUTED=TRUE
READ_ONLY=TRUE
TRADING_CODE_MODIFIED=FALSE
CONFIG_MODIFIED=FALSE
STATE_MODIFIED=FALSE
V1_UNTOUCHED=TRUE
V2_TRADING_LOGIC_UNTOUCHED=TRUE
V3_UNTOUCHED=TRUE
HERMES_UNTOUCHED=TRUE
BROKER_ORDER_SENT=FALSE
FORWARD_STARTED=FALSE
REAL_BROKER_ACCESS=FALSE
AGENT1_PIT_VERIFIED=DATA_GAP
AGENT2_PIT_VERIFIED=DATA_GAP
REPLAY_PIT_VERIFIED=DATA_GAP
AGENT1_LOOKAHEAD_VERIFIED=DATA_GAP
UNIFIED_DECISION_CUTOFF=DATA_GAP
AGENT1_FALLBACK_ISOLATION=DATA_GAP
CFTC_PIT_VERIFIED=DATA_GAP
ETF_PIT_VERIFIED=DATA_GAP
NEWS_PIT_VERIFIED=DATA_GAP
GEOPOLITICS_PIT_VERIFIED=DATA_GAP
E_AFTER_BLOCKED=DATA_GAP
ACTIVE_ROOT_CAUSE=SUPPORTED
MULTI_RUN_ROOT_CAUSE=SUPPORTED
CONCURRENT_START_TESTED=DATA_GAP
CONCURRENT_CYCLE_TESTED=FALSE
DUPLICATE_ENTRY_IDEMPOTENCY=DATA_GAP
CRASH_RECOVERY_CHECKED=FALSE
EXCEPTION_PATH_CHECKED=TRUE
V1_V2_V3_RUNTIME_ISOLATION=DATA_GAP
HIGH_FINDINGS=1
MEDIUM_FINDINGS=3
LOW_FINDINGS=0
DATA_GAPS=13
UNRESOLVED=1
RESULT_REPORT_CREATED=TRUE
CURRENT_STATUS_UPDATED=TRUE
GIT_COMMIT_CREATED=TRUE
GIT_PUSHED=TRUE
PARENT_COMMIT=cef1d9679f6a2cb495bae2030ca3bcef8fd3fa3b
FINAL_COMMIT=<the commit that adds this report>
LOCAL_HEAD=<after commit>
REMOTE_HEAD=<after push>
ORIGINAL_REPO_UNTOUCHED=TRUE
```

## 最终判断
核心条件（Agent1/Agent2/Replay PIT、E_AFTER_BLOCKED、并发/幂等/崩溃恢复、运行期隔离）**多为 DATA_GAP**，且存在 **H-01**（non-shadow BROKER_DEMO 实际执行路径）→ 判定：

```text
NOT READY FOR FORMAL FORWARD
（并因 HIGH 类条件，风险上等同 BLOCKED）
```

只读；只记录，不修复；不下单；未 Forward。
