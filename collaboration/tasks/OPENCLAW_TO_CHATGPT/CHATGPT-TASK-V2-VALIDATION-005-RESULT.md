# CHATGPT-TASK-V2-VALIDATION-005-RESULT.md

**Task**: V2-VALIDATION-005（第四轮遗留 DATA_GAP 穿透验证）
**执行**: OpenClaw（只读 + 纯内存 mock；未连 broker）｜**复核**: ChatGPT｜**决策**: 用户
**标签**: FACT / SUPPORTED / OBSERVATION / DATA_GAP / UNRESOLVED

## 1. Executive Summary

- **FACT（本轮新测·并发 start_run ×10）** `start_run()` **无锁、无存在性检查** → 并发调用**确实可产生两个不同 run**（10 次中多次出现 `run_dirs=2`，ACTIVE 为**后写覆盖**；未观察到 JSON 损坏）。判定对应任务书 **§7 情况 D（状态互相覆盖但无法证明一致性）→ MEDIUM**。
- **FACT（代码级）** Replay 为**快照驱动**：`runtime/replay_inputs.offline_replay(snap)` 仅用已冻结 snapshot（`input_hash`/`snapshot_hash` 校验、缺失/哈希不符/非法 ts → `ReplayError`，**绝不联网兜底**）。→ 外部新增 `E_after` **无法改变已存快照**（`E_AFTER_BLOCKED=TRUE`，方法=静态代码事实；未做注入式活实验）。
- **FACT** Agent1 特征操作未发现 `center=True/负 shift/bfill`（已提取片段）；**但统一 cutoff/逐特征未来依赖仍未证 → DATA_GAP**。
- **FACT** Agent2：`cot.publication_timestamp_unknown=True`、`pit_status=UNKNOWN`、`cot_timestamp_confidence=approximate(report_date only)`；`news.first_seen_at=retrieved_at` → COT/News/Geopolitics PIT **DATA_GAP**。
- 结论：核心项仍多为 **DATA_GAP**，且 **H-01 仍在** ⇒ **NOT READY FOR FORMAL FORWARD（并因 HIGH 类条件等同 BLOCKED）**。

## 2. Agent1 PIT / Look-ahead

- 复用：`market_data.py:165` 未收盘剔除；`validate.py:31` 未来 bar 拒绝；`local_bars` `label/closed=left`。
- **FACT** 特征清单（机械提取）：ma/ema/rsi14/atr14/atr_pct/realized_vol_ann/vwap/structure/trend_range/exp_cont/range60/recent_move_bps/price_vs_sma20_bps/breakout/bar_behavior。
- **UNIFIED_DECISION_CUTOFF=DATA_GAP**（未见全局 cutoff）。
- **AGENT1_LOOKAHEAD_VERIFIED=DATA_GAP**（未逐特征穷尽）。
- **AGENT1_FALLBACK_ISOLATION=DATA_GAP**（门禁在 `context` 层；agent1 内无 mt5 校验）。

## 3. Agent2 PIT

- **CFTC_PIT_VERIFIED=DATA_GAP**（`publication_timestamp_unknown=True`；源 403 缺失）。
- **ETF_PIT_VERIFIED=DATA_GAP**；**NEWS_PIT_VERIFIED=DATA_GAP**（`first_seen_at=retrieved_at`）；**GEOPOLITICS_PIT_VERIFIED=DATA_GAP**。
- **AGENT2_PIT_VERIFIED=DATA_GAP**。

## 4. Replay Future Evidence

- **FACT** `offline_replay(snap)` 仅用 snapshot；hash/schema/ts 校验 fail-closed；不 re-fetch。
- **E_AFTER_BLOCKED=TRUE**（代码事实：快照冻结，E_after 不影响已存 snapshot/输入/决策）。
- **REPLAY_PIT_VERIFIED=DATA_GAP**（快照内输入本身的 PIT 有效性未证，见 §3）。
- 未执行：`E_after` 内容篡改（Test A–D）/≥3 历史决策注入实验。

## 5. Run Lifecycle / 6. Concurrency（本轮核心新测）

**TEST_ID=R5-CONC-001**：并发 `start_run` ×10（临时目录；barrier；`REAL_BROKER_ACCESS=FALSE`）。
- INPUT：两线程同时 `start_run(minutes=1440, shadow=False)`。
- EXPECTED：仅 1 run 或安全序列化（PASS）。
- ACTUAL：**多次 `run_dirs=2`（两 run 并存）、ACTIVE 后写覆盖、JSON 未损坏**；仅同秒+同 sha1 后缀时收敛为 1 run。
- EVIDENCE：`v2_conc2.py` 输出（trial1 `run_dirs=2`，ACTIVE=`…668e`；trial2/3/4 `run_dirs=1`）。
- RESULT：**§7 情况 D → MEDIUM**（`start_run` 无锁无存在性检查 → 可建多 run、覆盖 ACTIVE）。

## 7. Duplicate Execution / 8. Crash Recovery

- **DUPLICATE_ENTRY_IDEMPOTENCY=DATA_GAP**（未做 execute() ×2/5/10 幂等实验）。
- **CONCURRENT_CYCLE_TESTED=FALSE**；**CRASH_RECOVERY_CHECKED=FALSE**（未做 8 点注入）。

## 9. Exception Path

- **EXCEPTION_PATH_CHECKED=TRUE**（复用第三/四轮：`shadow_run.py` 19 处 except，未见 `failure→default→TRADE`）。
- **未结合并发/崩溃**（见 §7/§8）→ 部分 DATA_GAP。

## 10. V1/V2/V3 Runtime Isolation

- **FACT（静态）** V2=`fxtm_demo_01`(+tag 硬校验)/Demo01/magic90003；V1=90002；V3=`fxtm_demo_v3`/90004。
- **V1_V2_V3_RUNTIME_ISOLATION=DATA_GAP**（默认 MT5 路径/AppData/共享缓存/进程 未做运行期核验）。

## 11. Finding Register

| ID | 级 | 标签 | 事实 |
|---|---|---|---|
| H-01 | HIGH | FACT | 当前 ACTIVE = non-shadow + BROKER_DEMO → 真实 demo 执行器可达；`BROKER_ORDER_SENT=FALSE` 仅因无合格周期 |
| M-01 | MEDIUM | FACT/SUPPORTED | 4 个 run RUNNING 并存；ACTIVE 覆盖式写入、旧 run 未 finalize |
| M-02 | MEDIUM | UNRESOLVED | 短命 run 归因 |
| **M-04** | **MEDIUM** | **FACT（本轮新测）** | **并发 `start_run` 无锁 → 可建两个 run 并覆盖 ACTIVE（§7 情况 D）** |
| M-03 | MEDIUM | DATA_GAP | Agent1/Agent2/Replay PIT、幂等、崩溃恢复、运行期隔离未证 |

## 12. DATA_GAP Register

1 A1 统一 cutoff；2 A1 逐特征 look-ahead；3 A1 fallback 逐字段；4 A2 逐字段 PIT；5 CFTC；6 ETF；7 News；8 Geopolitics；9 Replay 注入实验；10 concurrent cycle；11 幂等；12 crash recovery；13 三实例运行期隔离。

## 13. Final Q&A

- **A4-Q1** DATA_GAP；A4-Q2 DATA_GAP；A4-Q3 DATA_GAP；A4-Q4 DATA_GAP；A4-Q5 DATA_GAP（未见 center/负 shift/bfill）
- **B4-Q1..Q6** DATA_GAP
- **R4-Q1/Q2/Q3**：代码级 **E_after 不影响历史**（快照驱动）；活实验 DATA_GAP
- **L4-Q1** SUPPORTED（未 finalize 残留）；**L4-Q2** **测试=情况D（MEDIUM，可建两 run）**；L4-Q3 DATA_GAP；L4-Q4 DATA_GAP；L4-Q5 DATA_GAP
- **I4-Q1/Q2/Q3** DATA_GAP

## 14. Evidence / Test Artifacts

- `v2_conc2.py`（并发 start_run ×10）、`v2_conc_harness.py`、`v2_exec_harness.py`（workspace，非交易目录）。
- 代码：`runtime/replay_inputs.py:99+`（offline_replay）、`runtime/shadow_run.py:156-197`、`agents/technical/{features,market_data}.py`、`data_sources/validate.py`、`agents/macro_global/{agent2,evidence}.py`。
- 运行态：`state/runs/ACTIVE.json`、`research/runs/*`。

## 15. Git Integrity

仅新增本报告 + `CURRENT_STATUS.md`；`TRADING_CODE_MODIFIED=FALSE · CONFIG_MODIFIED=FALSE · STATE_MODIFIED=FALSE`；无 force/amend/rebase/squash/reset。

## 16. Final Acceptance Fields

```text
VALIDATION_005_EXECUTED=TRUE
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
AGENT1_LOOKAHEAD_VERIFIED=DATA_GAP
UNIFIED_DECISION_CUTOFF=DATA_GAP
AGENT1_FALLBACK_ISOLATION=DATA_GAP
AGENT2_PIT_VERIFIED=DATA_GAP
CFTC_PIT_VERIFIED=DATA_GAP
ETF_PIT_VERIFIED=DATA_GAP
NEWS_PIT_VERIFIED=DATA_GAP
GEOPOLITICS_PIT_VERIFIED=DATA_GAP
REPLAY_PIT_VERIFIED=DATA_GAP
E_AFTER_BLOCKED=TRUE
CONCURRENT_START_TESTED=TRUE
CONCURRENT_CYCLE_TESTED=FALSE
DUPLICATE_ENTRY_IDEMPOTENCY=DATA_GAP
CRASH_RECOVERY_CHECKED=FALSE
EXCEPTION_PATH_CHECKED=TRUE
V1_V2_V3_RUNTIME_ISOLATION=DATA_GAP
ACTIVE_ROOT_CAUSE=SUPPORTED
MULTI_RUN_ROOT_CAUSE=SUPPORTED
HIGH_FINDINGS=1
MEDIUM_FINDINGS=4
LOW_FINDINGS=0
DATA_GAPS=13
UNRESOLVED=1
RESULT_REPORT_CREATED=TRUE
CURRENT_STATUS_UPDATED=TRUE
GIT_COMMIT_CREATED=TRUE
GIT_PUSHED=TRUE
PARENT_COMMIT=d391f1ac7d25168264d61a6062191ce692442658
FINAL_COMMIT=<the commit that adds this report>
LOCAL_HEAD=<after commit>
REMOTE_HEAD=<after push>
ORIGINAL_REPO_UNTOUCHED=TRUE
```

## 最终判定
核心条件仍多项 **DATA_GAP**，且 **H-01 仍在**（non-shadow BROKER_DEMO 实际执行路径）：

```text
NOT READY FOR FORMAL FORWARD （因存在 HIGH 类条件 → 风险上等同 BLOCKED）
```

只读；只记录不修复；未下单；未 Forward。`BROKER_DEMO→PAPER` 的正式状态修改须由用户另立任务明确选择。
