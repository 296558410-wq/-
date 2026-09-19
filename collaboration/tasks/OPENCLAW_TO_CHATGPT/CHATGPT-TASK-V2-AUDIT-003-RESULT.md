# CHATGPT-TASK-V2-AUDIT-003-RESULT.md

**Task**: V2-AUDIT-003（执行隔离负向测试 + 失败门禁 + PIT/Replay）
**执行**: OpenClaw（只读 + 纯内存 mock harness）｜**复核**: ChatGPT｜**决策**: 用户
**标签**: FACT / SUPPORTED / OBSERVATION / DATA_GAP / UNRESOLVED

## 1. Executive Summary

- **FACT（本轮新增，mock 实测）** 执行器选择与 guard 拒绝行为**已用纯内存 harness 验证**（fake executor + 临时目录，**零 FXTM/MT5 连接、零下单**）：
  - `PAPER`（即使 broker/demo=true）→ **PaperExecutor**；`BROKER_DEMO + shadow=true` → **PaperExecutor**；`BROKER_DEMO + !shadow` → **BrokerDemoExecutor**。
  - 缺 broker.enabled / 缺 broker_demo_enabled / live_trading=true / 非法 mode → **全部 REFUSE**。
  - PaperExecutor 初始化失败 → **不回落 broker**；BrokerDemoExecutor 初始化失败 → **不回落 paper**。
- **FACT** MT5/源失败门禁（`context.build_health`）：非 mt5 源 → `overall=DEGRADED`（`trading_source_bad=[history=local_fxtm, gold_spot=sina]`）；a1 缺失 → `overall=FAIL`。→ 期望经 Hermes gate → WAIT。
- **FACT（未变）** 当前 `ACTIVE` = non-shadow + `BROKER_DEMO` → **真实 demo 执行器可达**（E-03 已实测确认代码事实）。
- **SUPPORTED** 4 个 `run_state=RUNNING` 并存根因：`start_run()` 每次新建 run 且**不 finalize 旧 run**，仅 `ACTIVE` 被驱动 → 残留。
- **DATA_GAP** Agent1 逐字段 look-ahead/统一 cutoff、Agent2 逐字段 PIT、Replay future-evidence、完整失败矩阵（F-03..F-14）仍未证。

## 2. Execution Negative Tests（§二，本轮完成，MOCK_ONLY）

| Case | 配置 | 期望 | 实测 | 结论 |
|---|---|---|---|---|
| E-01 | PAPER/!shadow/broker&demo=true | Paper | **FakePaper** | FACT PASS |
| E-02 | BROKER_DEMO/shadow=true | Paper | **FakePaper** | FACT PASS |
| E-03 | BROKER_DEMO/!shadow | BrokerDemo(代码事实) | **FakeBroker** | FACT（路径存在；REAL CALL=FALSE） |
| E-04 | broker.enabled=false | REFUSE | `RefuseToStart` | FACT PASS |
| E-05 | broker_demo_enabled=false | REFUSE | `RefuseToStart` | FACT PASS |
| E-06 | live_trading=true | REFUSE | `RefuseToStart` | FACT PASS |
| E-07 | mode=UNKNOWN | REFUSE | `RefuseToStart` | FACT PASS |
| E-08 | PaperExecutor init 失败 | 无 Broker 回落 | raised `RuntimeError`；instantiated=[Paper] | FACT PASS |
| E-09 | BrokerDemoExecutor init 失败 | 无 Paper 回落 | raised `RuntimeError`；instantiated=[BrokerDemo] | FACT PASS |

附加：`assert_paper_only(BROKER_DEMO)` → REFUSED；`FXTMDemoAdapter._gate()` on PAPER → `RefuseConnection`。
环境：`REAL_BROKER_ACCESS=FALSE / MT5_ORDER_SEND=FORBIDDEN / BROKER_CONNECTION=FORBIDDEN`；harness 脚本在 workspace，未写入交易目录。

## 3. Failure Injection Matrix（§三）

| Case | 故障 | 本轮状态 |
|---|---|---|
| F-01 MT5 unavailable | → DEGRADED（`health` 实测 non-mt5/缺失）；**经 Hermes gate → WAIT** | SUPPORTED（health 层）；端到端 → DATA_GAP |
| F-02 MT5 stale | 走 freshness/gaps → DEGRADED | SUPPORTED（阈值存在）；端到端 DATA_GAP |
| F-03 MT5 malformed | `validate_quote/bars` 存在 | DATA_GAP（未注入） |
| F-04 symbol invalid | — | DATA_GAP |
| F-05 Agent1 missing ts | — | DATA_GAP |
| F-06 Agent1 future ts | `validate.py` 拒未来 bar；`market_data` 剔未收盘 | SUPPORTED（部分）；注入 → DATA_GAP |
| F-07/F-08 Agent2 pub/future | `_pit_valid` 存在；缺失=unknown | DATA_GAP |
| F-09 Hermes timeout | 失败计数（`failures.hermes`）→ 继续 | DATA_GAP（未见 →TRADE 证据，但未证） |
| F-10 PaperExecutor failure | 见 E-08：无 broker 回落 | FACT（无回落）；是否 WAIT → DATA_GAP |
| F-11 Ledger failure | — | DATA_GAP |
| F-12 Broker adapter failure | E-09：无 paper 回落；adapter `_gate` 会 Refuse | FACT（无静默回落） |
| F-13 GitHub failure | 与交易安全无耦合（不同进程） | SUPPORTED |
| F-14 Scheduler failure | Windows 任务 `ExecutionTimeLimit=PT15M`、`MultipleInstances`=默认(IgnoreNew) | SUPPORTED（配置层） |

**FAILURE_MATRIX_COMPLETED=FALSE**（仅 F-01/F-02/F-10/F-12 部分覆盖）。**未发现 `failure → TRADE` 证据**；但**未穷尽 → 不判 PASS**。

## 4. Agent1 PIT Audit（§四）

- **FACT** 未收盘 bar 剔除：`agents/technical/market_data.py:165`；未来 bar 拒绝：`data_sources/validate.py:31`。
- **FACT** resample：`data_sources/local_bars.py:41-43`（`label="left", closed="left"`）；`market_data.resample_bars` 对 60m→4h 聚合。
- **FACT** 特征使用已过滤序列的 `[-1]`（`features.py:146,154,178,196,202,210`）。
- **A1-01 统一 decision cutoff**：**DATA_GAP**（未发现显式统一 cutoff_time；各 tf `last_bar_ts` 独立）。
- **A1-02 未收盘 bar**：**SUPPORTED 否**（有剔除）。
- **A1-03 rolling/shift/diff/center**：**DATA_GAP**（未逐特征穷尽；已见片段无 `center=True`）。
- **A1-04 resample label/closed**：**FACT 已见**（left/left）；M1→M5→H1 聚合边界**未全证** → DATA_GAP。
- **A1-05 merge_asof/forward direction/ffill**：**DATA_GAP**。
- **A1-06 source lineage 逐层**：**DATA_GAP**。
- **A1-07 fallback 入交易决策**：**SUPPORTED（门禁在 context 层降级为 DEGRADED）**；agent1 内部无 mt5 校验 → **DATA_GAP（逐字段）**。

## 5. Agent2 PIT Audit（§五）

- **FACT** `evidence._pit_valid(published_at, retrieved_at)`；缺 `published_at` → `unknown`（**不得视为 PIT-valid**）。
- **DATA_GAP**：A2-01（DXY/UST10Y/VIX/TIP/GLD/GC 是否读到 revised/backfilled）、A2-02（COT 需 release/publication；当前 COT **源缺失/403**）、A2-03（ETF 仅 observation date，无 publication ts）、A2-04（News published vs updated）、A2-05（Geopolitics first-public timestamp；当前用 `first_seen_at=retrieved_at`）。→ **逐字段未能证明 = DATA_GAP**。

## 6. Replay Future-Evidence Audit（§六）

**DATA_GAP**：未构造内存 replay 的 `E_after` 注入测试；`replay_inputs.build_snapshot` 基于当时 `d,ctx,a1,a2`，但**未证** replay/evidence cache 不会读到 `T+1` 后信息。

## 7. ACTIVE / RUN Lifecycle（§七）

- **FACT** `start_run()`（`shadow_run.py:156–174`）创建 run（`RUN_META{shadow,execution_mode}`、`run_manifest{code_commit,config_hash}`、`run_state`）并**覆盖 `ACTIVE.json`**；`cycle()` 窗口尽→`finalize`（`:188–197`）。
- **R-01** `ACTIVE.run_id` 与 `health.run_id`：新 run 后**不等**（health 由最近成功 cycle 写）；**当前不等**（`…084c` vs `…8648`）→ **SUPPORTED 漂移**。
- **R-02** 4 RUNNING/1 ACTIVE：`…8648`(cycles=42) / `…084c` / `…b3c2` / `…59f4`(cycles=0)。均 `shadow=False, mode=BROKER_DEMO, code_commit=d22d9fb, config_hash=b0cc254b`。旧 run **未 finalize** → 多 RUNNING 残留。**SUPPORTED**。
- **R-03** 短命 run 归因：时间戳与 09-19 09:36–09:41 CST 的测试/手动入口吻合；**无法确证** → **UNRESOLVED**（不猜测）。
- **R-04** 多入口：Windows 任务 `hermes-v2-cycle`（默认 IgnoreNew）、OpenClaw cron `collab-task-bus`（不同对象，不改 ACTIVE）、`shadow_run.py start`（手动）、`v2_scheduled_cycle`（调用 shadow_run cycle）。**存在“手动 start_run 与会话/任务并发”的可能** → **DATA_GAP（并发 start_run 未证不双开）**。
- **R-05** 并发 TRADE：**DATA_GAP**（未证是否双执行）。

## 8. Exception Swallowing（§八）

- **FACT** `shadow_run.py` 19 处 except：Agent1/Agent2/Hermes 失败 → 计数+timeline，**继续**；broker/reconcile/price_space 失败 → 写错误/`BROKER_UNAVAILABLE`/`execution_reject`。
- **证据**：**未发现 `failure → default → TRADE` 路径**；但**未逐条证明** `异常→WAIT`。→ **SUPPORTED（无正向反例）/ 逐条 DATA_GAP**。

## 9. V1/V2/V3 Isolation（§九）

- **FACT** V2 独立实例 `fxtm_demo_01`（tag 硬校验）、server `ForexTimeFXTM-Demo01`、magic 90003；V1 magic 90002；V3 `fxtm_demo_v3`/90004。
- **DATA_GAP**：进程/AppData/缓存/日志/state 的**运行期交叉**未证。

## 10. Finding Register

| ID | 级 | 标签 | 事实 |
|---|---|---|---|
| H-01 | HIGH | FACT | 当前 ACTIVE = non-shadow + BROKER_DEMO → **真实 demo 执行器可达**（E-03 实测代码事实）；`BROKER_ORDER_SENT=FALSE` 仅因无合格周期 |
| M-01 | MEDIUM | FACT | 4 个 run_state=RUNNING 并存（旧 run 未 finalize） |
| M-02 | MEDIUM | UNRESOLVED | 短命 run 归因未定 |
| M-03 | MEDIUM | DATA_GAP | Agent1/Agent2/Replay PIT 未逐字段证明；完整失败矩阵未完成 |

## 11. DATA_GAP Register

1. A1-01 统一 cutoff；2. A1-03 rolling/shift 穷尽；3. A1-05 merge_asof/ffill；4. A1-06 lineage 逐层；5. A1-07 fallback 逐字段；6. A2-01..A2-05 逐字段 PIT；7. Replay E_after 注入；8. F-03..F-09/F-11 注入；9. R-04/R-05 并发；10. §9 运行期隔离。

## 12. Final Q&A

- **E-Q1** PAPER 100% 不进 BrokerDemo：**SUPPORTED**（E-01 mock 实测 Paper）
- **E-Q2** Shadow 100% 不进 BrokerDemo：**SUPPORTED**（E-02 实测 Paper）
- **E-Q3** BROKER_DEMO non-shadow 明确进 BrokerDemo：**FACT**（E-03 实测）
- **E-Q4** executor failure 改变执行语义：**DATA_GAP**（未见回落，E-08/E-09 支持“不回落”，但语义变化未全证）
- **E-Q5** data failure → TRADE：**未发现证据 / DATA_GAP**
- **E-Q6** exception → TRADE：**未发现证据 / DATA_GAP**
- **A-Q1** 无 look-ahead：**DATA_GAP**（有防护证据）
- **A-Q2** 统一 cutoff：**DATA_GAP**
- **A-Q3** M1/M5/H1 causal：**DATA_GAP**（有未收盘剔除）
- **A-Q4** fallback 入决策：**SUPPORTED 会被降级**；逐字段 DATA_GAP
- **A-Q5** Replay 无未来行情：**DATA_GAP**
- **B-Q1..B-Q6**：**DATA_GAP**（B-Q4 News 部分 SUPPORTED）
- **R-Q1** 漂移根因：**SUPPORTED**
- **R-Q2** 4 RUNNING 原因：**SUPPORTED**（未 finalize 残留）
- **R-Q3** 重复启动入口：**DATA_GAP**
- **R-Q4** 重复 TRADE：**DATA_GAP**
- **R-Q5** crash recovery 安全：**DATA_GAP**

## 13. Recommended Next Investigation（研究建议，非用户指令）

1. 扩展 mock harness：F-03..F-14 全矩阵（fake MT5/source/ledger/scheduler）。
2. Agent1 逐特征 look-ahead + 统一 cutoff 静态审计。
3. Agent2 逐字段 PIT + Replay `E_after` 注入。
4. RUN 生命周期/并发 start_run 审计；短命 run 归因。
5. 三实例运行期隔离只读核查。

## 14. Git Integrity

`git status`/`git diff --check`/`git diff`：仅新增本报告 + `CURRENT_STATUS.md`；无 trading/config/state 修改。
`TRADING_CODE_MODIFIED=FALSE · CONFIG_MODIFIED=FALSE · STATE_MODIFIED=FALSE`

---

```text
AUDIT_003_EXECUTED=TRUE
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
EXECUTION_NEGATIVE_TESTS=TRUE
FAILURE_MATRIX_COMPLETED=FALSE
AGENT1_PIT_VERIFIED=DATA_GAP
AGENT2_PIT_VERIFIED=DATA_GAP
REPLAY_PIT_VERIFIED=DATA_GAP
ACTIVE_ROOT_CAUSE=SUPPORTED
MULTI_RUN_ROOT_CAUSE=SUPPORTED
DUPLICATE_ENTRY_CHECKED=TRUE
EXCEPTION_PATH_CHECKED=TRUE
V1_V2_V3_ISOLATION_CHECKED=DATA_GAP
HIGH_FINDINGS=1
MEDIUM_FINDINGS=3
DATA_GAPS=10
RESULT_REPORT_CREATED=TRUE
CURRENT_STATUS_UPDATED=TRUE
GIT_COMMIT_CREATED=TRUE
GIT_PUSHED=TRUE
FINAL_COMMIT=<the commit that adds this report>
```

_只读审计；只记录，不修复。_
