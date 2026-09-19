# V2 FULL AUDIT — 20260917

- **Type**: 全系统独立只读审计（不修复、不改动）
- **Date**: 2026-09-17 (GMT+8)
- **Scope**: `C:\AIQuant\research\hermes\trader_v2`（+ ledger/replay/state/manifests/reports/observer/scheduler/data sources/broker/paper/execution/risk/dashboard/tests + Windows Task `\OpenClaw\hermes-v2-cycle`）
- **Method**: 只读代码审阅 + 只读运行证据（账本/审计日志/缓存/快照/清单）+ 隔离只读校验。未运行任何产生副作用的命令；未修改任何文件。
- **AUDIT_COMMIT**: `b2aeb4316e9c54dc6a2745386ca8929622fd2ead`（审计前 HEAD；本轮仅新增本报告）
- **BASE_COMMIT**: `7fe4828eab194ec3fc6c32351662b6b40dfc7176`（价格空间任务基线）
- **CODE_CHANGED = FALSE · CONFIG_CHANGED = FALSE · LEDGER_CHANGED = FALSE · RUN_STATE_CHANGED = FALSE · V1_CHANGED = FALSE · BROKER_ORDER_SENT = FALSE · CURRENT_RUN_MODIFIED = FALSE**

> 说明：文末给出 §30 声明与 WORKTREE_STATUS。所有结论均以 file:line 或运行证据支撑；不确定处显式标注 confidence。

---

## 1. Executive Summary

V2 的**工程骨架**（账本 hash 链、replay 独立性、broker reconcile、scheduler 去重、V1 代码/账户/终端隔离、LIVE 不可达）经证据核查**基本成立**。但审计发现 **5 个 P0**，其中最关键的一条会**根本性改变对 V2 的理解**：

1. **声明标的 ≠ 运行标的（P0-01）**：配置/决策/清单全写 `GC=F`，但 router 打开时技术主序列实际是 **`local_fxtm`（本地 XAUUSD 现货 tick，且与 V1 共用采集）**。router 缓存直证 `hist:GC=F:15m → src=local_fxtm`。这意味着 2026-09-17 完成的 “GC=F→XAUUSD 价格空间” 修复的**语义模型与运行现实不符**（运行中信号=本币现货源，执行=broker 现货），且 `basis_usd` 实为**两个 XAUUSD 现货源之间的价差**，而非 COMEX/现货基差。
2. **Router 实际常开（P0-02）** 与文档 “默认 OFF/走 legacy” 矛盾。
3. **宏观 fail-open（P0-03）**：DXY/UST10Y/VIX 取数失败不报 gap，静默退化为 `NEUTRAL`。
4. **“新鲜度” 与 health 门形同虚设（P0-04）**：freshness 基于快照生成时刻而非数据recency；health_report 从未接入决策路径。
5. **缓存无 point-in-time 维度（P0-05）**：单槽 last-write-wins，无 `as-of`。

**对 forward validation 的直接影响**：当前 forward 样本（10 TRADE）**全部来自同一候选类型** `opp_fbo_short`（有效 N≈2–3 个独立事件），且成交/拒单主要受**数据源不一致**驱动——因此**尚不构成任何可信的 strategy/alpha 证据**（见 §17/§18）。

## 2. 当前运行状态

- 活动 run：`V2-PAPER-20260917-011344-1ed3`（RUNNING，至 2026-09-18 01:13Z），`BROKER_DEMO`，实例 `fxtm_demo_01` / 账户 `******` / magic `90003`，`price_space=ON`。code_commit `d143ad7`。
- 上一 run：`V2-PAPER-20260916-110402-4644` STOPPED（05:13Z finalize），net −26.56，balance 1024.03，ledger verify=True。
- 健康：scheduler 100%、agent1 fresh、lexpense ledger integrity、replay MATCH；agent2 仍固定缺 6 类数据（见 §4）。
- 运行证据时间线取自 `state/v2_run_health.json`、`research/runs/*/run_state.json`、`data_cache/router_audit.jsonl`。

## 3. 架构图（实际路径，router ON）

```
Data  ┌ Yahoo GC=F (legacy/adapter)  ┐
      │ local_fxtm XAUUSD ticks (V1采集) ← router PRIMARY(hist)   ← ★运行实际用这条
      │ sina/tencent quotes  · CFTC/BLS/news
      ▼
Agent1 (agents/technical/agent1.py → market_data.py → data_sources(router)) → features.py
      ▼ state/agent1_latest.json
Agent2 (agents/macro_global/agent2.py → sources.py → router.macro)  [确定性, 无 LLM]
      ▼ state/agent2_latest.json
context.py  build_context()  ── 冻结 ctx(+context_hash)，写 state/decision_contexts/<id>.json
      ▼
hermes/hermes.py decide()  → discovery.discover() (A–F) → gate() → build_plan(price=ctx.market.primary_last)
      ▼  (plan 标称 GC=F; 实际值来自 local_fxtm)
runtime/shadow_run.py run_cycle(): Agent1/2 → Hermes → freeze → [price_space(opt)] → ADP.process
      ▼
execution/hermes_paper_adapter.process() → executor.open()
      ▼ (PaperExecutor | BrokerDemoExecutor → fxtm_demo_adapter → MT5)
Ledger (per-run ledger.jsonl, append-only sha256链)
      ▼
ledger/replay.py replay(ledger仅) → shadow_run._account_match(pe, replay, acc)
      ▼  run_state.json / metrics.json
Observer (tools/v2_observer.py, 只读, 写 observations/) → Dashboard (dashboard/server.py :8788)
Scheduler: Windows Task \OpenClaw\hermes-v2-cycle → runtime/v2_scheduled_cycle.py → shadow_run cycle
```

逐层确认：无绕过 Pricing/Risk 层的执行路径；`shadow_run` 每周期新建 executor + `reconcile_broker_closes`。**隐式状态共享**：PAPER 模式用模块级 `PE.ACCOUNT_P/EXECUTIONS_P` 全局（BROKER_DEMO 不用）；`data_sources/cache._store` 进程内单例。**hidden fallback**：router cache/last_valid、agent2 `_safe` 哨兵、news `default=[]`。**fail-open**：见 P0-03/P0-04。**silent degradation**：见 P1-02/P1-03。

## 4. 数据审计

### Agent1
- 源：5m/15m/60m/4h/1d 历史经 router（`registry.HISTORY_SOURCES`：**local_fxtm primary → yahoo secondary**，`registry.py:6-12`）；现价 quote（sina→tencent→[local_fxtm]…）。DXY=`QUOTE_SOURCES` eastmoney/yahoo；UST10Y/VX/GLD=yahoo/tencent（`registry.py:15-23`）。
- **运行证据（决定性）**：`data_cache/router_cache.json` → `hist:GC=F:15m {source: local_fxtm, n:706}`；`router_audit.jsonl` history 行 **755/781 selected_source=local_fxtm，0 yahoo**。
- 缺数据行为：全部历史失败 → 返回 `n=0, error=ALL_SOURCES_FAILED`（`router.py:102-106`），**不抛错**；agent1 仍写 `generated_utc=now` 的快照（`agent1.py:104`），`data_quality.gaps` 记录缺 tf。**是否可能进入 TRADE**：见 P0-04。
- `data_quality.sources.history` **硬编码 "yahoo"**（`agent1.py:104`）→ 与实际 local_fxtm 不符（drift，见 §20）。

### Agent2（详见子审证据）
- TIP：Yahoo `TIP`（TIPS ETF 价，**非真实收益率**），**不参与评分**（`sources.py:72-93`; `agent2.py:225-228` 只用 `^TNX`）。
- BLS/COT/WGC/央行购金/政策利率：BLS/COT 有取数但**不参与 gold_macro_state**；WGC/央行/政策利率**未取**（显式 gap）。
- `gold_macro_state` 仅由 DXY/UST10Y/VIX 的 `change_pct` + 中国 ETF 资金流合计决定（`agent2.py:220-247`），**无 LLM**（关键词计数）。
- 真实/缓存/stale/missing/fallback/LLM 区分：见 P0-03、P1-02、P1-04、P1-05。

## 5. PIT / Look-ahead（最高优先级）

- **Bars PIT 良好（PASS）**：三层剔除未收盘 bar（`validate.py:29-30`, `adapters_market.py:89-91`, `local_bars.py:59-61`）。抽样 7 个决策，`ctx.agent1.generated_utc` 均 > 用于特征的 bar 时间（例：1ed3 dec 01:23:13 > a1_gen 01:22:25；15m last_bar 01:00 ≤ 01:22）。**无未来 bar**。
- **决策冻结 PIT 良好（PASS）**：`context.py` 每决策冻结 ctx + context_hash，不覆盖（`context.py:92-96`）。
- **PIT_RISK-1（P1-06）**：BLS/COT/宏观标量**未强制“发布时间 ≤ decision_ts”**。COT 取 `report_date DESC` 最新已发布报告，且 `publication_timestamp_unknown=True`（`sources.py:121-128`）→ 历史 replay 存在无界泄漏窗口（cutoff 周二 / 发布周五）。BLS `release_timestamp=null`，`value_asof` 从不调用。
- **PIT_RISK-2（P0-05）**：缓存无时间维度（见 §14 与 P0-05）。
- **live vs replay 信息源不同（P1-10）**：replay **完全不读市场数据**（`replay.py` 头注 + 仅读账本），故“数据驱动决策”无法从账本复现/归因。
- **basis timestamp**：价格空间层要求 PIT（`price_space.py` 记 `basis_ts/age/source_hash`），设计正确；但 basis 的“GC 腿”实际是 local_fxtm 现货（P0-01）。

## 6. Strategy Logic

- 候选 A–F 真实产生于 `discovery.discover()`（`discovery.py:36-140`）：A 趋势(≥3TF)、B 突破、C 假突破、D 宏观重定价、E 地缘、F 叙事×资金流。
- 优先级 `CATEGORY_PRIORITY=["false_breakout","breakout","trend","macro_repricing","geopolitical","narrative_flow"]`（`hermes.py:31`）+ 取每类首个（`hermes.py:104-108`）。
- **候选被覆盖/静默丢弃**：`decide()` 记录全部候选到 `opportunity_ledger`，但**只对优先级最高类别的首个候选**做 gate；其余**静默不评估**（无日志区分“评估后被否”与“未评估”）。
- **重复计算**：E 类 `opp_geo_shock` 只要 `geo_n>0` 即产生，且 `dir_hint="LONG"` 固定 + `requires_confirmation=True`（`discovery.py:120-129`）→ 与宏观 BEARISH 恒冲突 → 恒 WAIT。观测：chosen `opp_geo_shock` 200 次（WAIT）。

## 7. Price Space（审计既有修复，不改）

- 换算公式：`execution = signal + basis`，`basis = spot − gc`（`price_space.py`）。校验：换算 entry ≈ 实际成交（d341 4292.35 vs 4292.60）。符号约定单处定义，未见 GC−spot / spot−GC 混用（`price_space.py:resolve_basis` 只算 `spot−gc`）。
- 守卫：缺/超龄/abs/jump → fail-closed（`price_space.py:prepare`）。历史影响：10 TRADE→无守卫 10 有效 / 带守卫 7 有效 3 fail-closed；2×10016 可用该机制解释。
- **但前提语义错误（P0-01）**：运行时 `signal` 实为 local_fxtm 现货，非 GC=F；`spot` 为 sina 现货。**该模块自洽且有效，但“GC→XAUUSD”的命名/文档与运行现实不符**；其效果实质是**把 local-tick 现货对齐到 sina/broker 现货**。**建议：不改代码，仅修订文档/标注 + 重新评估 P0-01。**

## 8. Risk / Sizing

- 链：`size_position_raw → _lots(FLOOR_TO_STEP) → min_lot floor → max_lot(HARD REJECT) → notional/risk`（`broker_demo_executor.py:114-165`）。
- 证明 `实际风险 ≤ 配置风险`：0.01 手 × 100oz × ~17 stop ≈ $17 on equity ~1024 = ~1.7% ≤ 2%（目标）；历史 3 笔实测 risk 0.85%–2.9%（2 笔 >2%，因价格空间错配，非 sizing 逻辑）。
- **不可避免偏差（MIN-LOT FLOOR）**：`if qty<min_lot: qty=min_lot`（`broker_demo_executor.py:141-142`），小账户下实际风险可 **超过** 目标（记录于 §7 影响报告）。`max_lot` 硬拒（不 clamp）。tick/dp=2/0.01。contract 100oz、leverage 500（config）。
- `allowed_risk=max(target, min_lot*dist*cs)`（`:150`）——风险上限以此放宽以允许最小手。

## 9. Broker（只读）

配置与实现：`execution/contract`（min 0.01/max 0.05/100oz/dp2/lev500）；adapter 门：terminal 必须含 `fxtm_demo_01`、`trade_mode==0`、server `ForexTimeFXTM-Demo01`（`fxtm_demo_adapter.py:20-21,67-77`）。
- **未本地强制 broker 规则**：最小止损距离（trade_stops_level）与 volume step 未读取/校验 → 依赖 broker 端拒绝（10016）。见 P2-07 与 §7。
- 成本：spread/slippage **未单独入账**（嵌在 broker profit 内）；commission/swap 来自 broker deals（`broker_demo_executor.py:222-235`）。
- 未验证（需 broker 侧数据，本轮只读）：实际 digits/tick size/min stop/spread/commission 与本地假设的一致性 —— **标记为待深查**。

## 10. Ledger

- append-only + 每事件 sha256 链 + `os.fsync`（`ledger.py:74-104`）；`verify_ledger` 检 genesis/链断/篡改/seq（`ledger.py:107-131`）。
- **半写崩溃**：截断/半行 → `load_events` 抛 `LedgerMalformed`（`ledger.py:57-62`）→ `shadow_run` 捕获 → `LEDGER_UNVERIFIABLE` → **BLOCK（fail-closed，不会“半条记录仍认为成功”）**。**PASS**。
- 事件顺序/时间戳/account/close 事件齐全（schema `SCHEMA_FIELDS`）。重复事件由窗口去重 + reconcile 幂等防。
- 注意：新 run 每周期写 `ACCOUNT_SNAPSHOT`；dashboard 不校验链（P2-02）。

## 11. Replay

- `replay.py` **仅读账本**、自行重建 account/positions/closed/PnL（`replay.py:27-92`），**不调用 execution/account 的已算结果** → **REPLAY_INDEPENDENCE = PASS**。
- `_account_match`(BROKER_DEMO) 比 replay(账本) 与 broker 派生已实现量（`shadow_run.py:_account_match`）。历史 3 run 曾因 reconcile 状态不同步 BLOCK（已修 5955ede）。
- 局限（P1-10）：replay 不接触市场数据 → 无法从账本复现“为何决策”。

## 12. Scheduler

- Windows Task `\OpenClaw\hermes-v2-cycle`：`MultipleInstancesPolicy=IgnoreNew`、`ExecutionTimeLimit=PT15M`、`DisallowStartIfOnBatteries=false`、`StopIfGoingOnBatteries=false`；**无 `<StartWhenAvailable>`（默认 false）→ 睡醒不补跑**（与文档一致，属 PASS）。
- `v2_scheduled_cycle.py`：每 15m 直跑 `shadow_run cycle`；`ensure_run` 窗口去重（`shadow_run.py:ensure_run`）→ 不重复交易；missed-window 只**计数不补跑**（`v2_scheduled_cycle.py` missed_cycles）。市场时段门 `trading_hours.is_armed`。
- 情形 A–F：A 正常（证据：连续 cycles）；B 睡眠→见 StartWhenAvailable=false（错过不补）；C crash→账本可恢复 + 窗口去重（有 tests）；D 网络→router cache/降级（fail-open 见 P0-03）；E MT5 不可用→`BROKER_UNAVAILABLE` 记 window 并跳过（`shadow_run.py` connect except）；F 上轮未完→`IgnoreNew` + 窗口去重。
- INFO：`trading_hours` 基于 UTC 且假设 broker=UTC+3；DST/服务器时间若变，armed 边界可能偏移（未验证）。

## 13. Isolation（V1 vs V2）

- **PASS（代码/账户/终端/magic/账本/state/scheduler）**：V2 独立目录、独立 ledger、独立 state、`fxtm_demo_01`、magic 90003（V1 90002）、V1 只读。审计未触碰 V1（`git status` 中 V1 的 M 为系统自身写入，非本审计）。
- **缺口（P1-11）**：V2 的技术主序列 = `C:\AIQuant\data\live_fxtm`（**V1 采集器 `hermes-tick-collect` 写**）→ **数据面未隔离**（V1 采集停/错会污染 V2；与既有记忆“V1/V2 共用采集器”一致）。

## 14. LIVE Safety

- **PASS（目前未找到逃逸路径）**：`assert_execution_allowed` 仅允许 PAPER/BROKER_DEMO，任何其他 mode（含 LIVE）→ `REFUSE_TO_START`（`hermes_paper_adapter.py:79-104`）；`BrokerDemoExecutor._guard` 拒 `live_trading=true`（`broker_demo_executor.py:88-96`）；adapter 强制 DEMO（`trade_mode==0`、server 白名单、terminal tag）；`v2_config.live_trading=false`；**无 OANDA/其它 broker 实现**（`backends_available` 仅声明）；未发现影响 mode 的环境变量（仅 `V2_DATA_ROUTER_ENABLED`/`TEST_TERM_PID`）。
- **但“LIVE=impossible”依赖**：config `execution_mode` 不被篡改 + demo 账户。若有人改 config 为 `LIVE`：`assert_execution_allowed` 仍拒；若改成 `PAPER`/`BROKER_DEMO` 只能连 demo。**结论：结构性不可达，但属“多门把关”而非“单点不可违反”**（confidence: high，未见逃逸）。

## 15. Failure Injection

| 注入 | 行为 | 判定 |
|---|---|---|
| Agent1 不可用 | `failures.agent1++`，a1=None → ctx freshness unknown → WAIT | fail-closed ✅（但 freshness 见 P0-04） |
| Agent2 不可用 | `failures.agent2++`；macro 用 cache/哨兵 | **部分 fail-open**（P0-03） |
| Hermes timeout/异常 | `failures.hermes++` + window=HERMES_FAILED | fail-closed ✅ |
| Yahoo/Sina 不可用 | router 降级 cache/last_valid；quote 可能旧值当 FRESH | **silent（P1-03）** |
| Broker/MT5 不可用 | `BROKER_UNAVAILABLE`，跳过 cycle | fail-closed ✅ |
| Ledger 截断/重复 | `LedgerMalformed`→BLOCK；reconcile 幂等 | fail-closed ✅ |
| Replay mismatch | `PAPER_REPLAY_MISMATCH`→BLOCK | fail-closed ✅ |
| basis 缺/旧/跳变 | `price_space` fail-closed（REJECTED:PRICE_SPACE_*） | fail-closed ✅ |

## 16. State Machine

RUNNING→(WAIT|TRADE|REJECT)→FILLED→OPEN→CLOSED；BLOCKED（replay/ledger 失配）；STOPPED(COMPLETE finalize)；FAILED via failures 计数；RECOVERY via reconcile_rebuild。
- 找 impossible/orphan/stuck：**未发现 stuck**；`windows` 状态 DONE/DUP；BLOCKED 后需人工 finalize（设计）。
- **风险**：`run_state.failures` reload 覆盖（历史上丢计数，已修 `shadow_run.py` FIX）；窗口状态仅内存+文件双写，崩溃恢复靠 `windows` 去重（P2 级）。

## 17. Forward Evidence（证据分层）

当前正式 forward 样本（BROKER_DEMO run 4644 已 finalize + 1ed3 进行中）：
- cycles ≈ 57(4644)+2(1ed3)；TRADE=6(4644)+0；fills=1；closed=1；win 0 / loss 1；net −26.56；R≈−0.9。
- **Engineering evidence**：调度/账本/replay/reconcile 达标（见 §10-12）。**Execution evidence**：3 次真实成交（含前 run），1×10016×2 已由价格空间解释。**Strategy evidence：不足**。**Alpha evidence：无**。
- 明确排除：`demo_calibration`（`DEMO-CALIB-*`，非策略）、测试/迁移事件、历史 replay。

## 18. Statistical Validity

- **EFFECTIVE_N_RISK（P1-09，强）**：**全部 10 笔 TRADE 的 chosen 均为 `opp_fbo_short`（假突破做空）**；时间高度聚集（a17b 09-11 两条相隔 15min；4644 六条集中在 09-16 13:52–21:22）。→ 名义 N=10，**有效 N≈2–3 个独立事件**，且单一 regime/时段。**不足以支撑任何统计结论**。
- 重叠/自相关：同一 candidate 连续触发（≥2 次同源 setup），存在信号重叠。
- 时段集中：多为亚盘/欧盘早段；regime 单一（宏观 BEARISH + 技术 LONG 冲突恒 WAIT；仅 fbo 做空偶尔通过）。

## 19. Cost

- 账本守恒：`gross − commission − swap = net`（broker deals 口径），`conservation_ok=True`（4644: gross −26.34, comm −0.22, swap 0 → net −26.56）。**PASS**。
- **P2-07**：broker 模式 **spread/slippage 未单独入账**（嵌在 profit 内），仅 commission/swap 显式；“净额”正确但**成本归因不完整**。PAPER 模式则把 spread+slip+commission 计入 `entry/exit_cost`。

## 20. Config Drift

| 项 | README/文档 | config/代码 实际 |
|---|---|---|
| 主标的 | GC=F | **运行时 local_fxtm XAUUSD**（P0-01） |
| Router | “默认 OFF/走 legacy” | 实际 ON（flag=true + scheduler 强置，P0-02） |
| 数据源 | source_connectivity_matrix 称“本地 tick 为主源” | 与 config `primary_source=yahoo` 冲突 |
| dashboard | README “只读·PAPER·不触网” | BROKER_DEMO + 每 30s 连 MT5（P1-07,P2-01） |
| trading_hours | “不被 V1/V2 import” | scheduler import 它（`v2_scheduled_cycle._gate`） |
| registry 元数据 | 声明 retry/backoff | 适配器另写一套，表未被读取（P2-05） |
| agent1 data_quality.sources.history | — | 硬编码 "yahoo"（实为 local_fxtm） |

## 21. Dashboard

- `dashboard/datasource.build_snapshot()` 读 run/*、state/*、config；**另起 MT5 只读探测**（`acc_probe.py`）。
- **不得成为唯一事实来源**：已确认它**会**与账本/run_state 分歧：sizing **重算**（硬编码 base_equity=10000，P1-08）、`execution_mode` 标签 PAPER（P1-07）、`ledger_ok=None` 不校验链（P2-02）、V1/execution chip 为硬断言（P3-01）。observer `latest.json` 曾滞后于 ACTIVE（P3-03）。**账本为准；dashboard 仅展示**。

## 22. Git / Reproducibility

- run manifest 记录 `code_commit`（4644=b56f1f6；1ed3=d143ad7）、`config_hash`、versions。**可定位 commit**。
- **不可完整重建**（P2-08）：① 决策所用**市场数据未随 run 归档**（仅 ctx 冻结 market 标量与 evidence_ids，无 bars）；② `price_space` 生效与否不在 manifest（仅 RUN_META 手写）；③ 数据源实际选择（router env/flag）不在 manifest → 同日不同 flag 结果不同（P0-02/P2-08）。→ **重新 checkout 该 commit 无法复现同一 run**。

## 23. Findings（P0/P1/P2/P3/INFO）

见 §24 证据表（含 ID/Severity/Component/Observation/Evidence/Reproduction/Impact/Confidence/Next）。

## 24. Evidence Table

| ID | Sev | Component | Observation | Evidence | Reproduction | Impact | Conf |
|---|---|---|---|---|---|---|---|
| P0-01 | P0 | Data/instrument | 声明 GC=F，运行=local_fxtm XAUUSD | `router_cache.json hist:GC=F:15m src=local_fxtm`; `router_audit` 755/781 local; `router.py:55-56` 忽略 symbol; `local_bars.py:47` | 读 router_cache/audit | 价格空间语义错；决策/manifest 误标；09-17 修复名义≠现实 | 高 |
| P0-02 | P0 | Router switch | Router 实际常开，与文档“默认 OFF”矛盾 | `config/data_router.enabled=true`; `v2_scheduled_cycle.py:30` setdefault; `data_sources/__init__.py:21-36` | 读二文件 | legacy/新路径不可复现 | 高 |
| P0-03 | P0 | Agent2 | DXY/UST10Y/VIX 失败→无 gap→NEUTRAL | `agent2.py:71-73,108-111,220-247`（gaps 仅 TIP/placeholder/BLS/COT） | 注入 macro 失败 | 静默退化污染 forward | 高 |
| P0-04 | P0 | Freshness/gate | freshness=生成时刻；health 未接入 | `context.py:42-54`(基于 generated_utc); `health.build_report` 无调用方（仅 tests/tools） | 读代码 | “新鲜”≠数据在，可能带病决策 | 高 |
| P0-05 | P0 | Cache | 无 PIT 维度（单槽 LWW） | `cache.py:56-91`（无 as_of） | 读代码 | 标量/报价非结构性防未来 | 中高 |
| P1-01 | P1 | Agent2 | conflicts 反降级死代码 | `agent2.py:244-247` | 读代码 | 冲突保护失效 | 高 |
| P1-02 | P1 | Cache/macro | stale 值当 current 供 agent2 | `router.py:151-172`（val 无 freshness）; agent2 只读 value | 读代码 | score 用旧数据 | 中高 |
| P1-03 | P1 | validate | quote 不查时间→旧价=FRESH | `validate.py:48-74`; `router.py:125` | 读代码/注入 | 陈旧报价入决策 | 高 |
| P1-04 | P1 | Agent2 | 中国 ETF 流 as-of 丢弃 | `sources.py:187-204`; `agent2.py:179` | 读代码 | score 最大项可能旧 | 中 |
| P1-05 | P1 | Agent2 | 新闻源故障静默 | `agent2.py:80-82`（default=[]，无 gap） | 读代码 | 断流=安静 | 中高 |
| P1-06 | P1 | PIT | BLS/COT 未强制发布时刻 | `sources.py:121-128,157-158` | 读代码 | 历史 replay 泄漏窗口 | 中高 |
| P1-07 | P1 | Dashboard | BROKER_DEMO 显示为 PAPER/虚拟 | `static/app.js:31,37,63,108`; README.md:3,15 | 打开面板 | 安全标签误导 | 高 |
| P1-08 | P1 | Dashboard | sizing 重算+硬编码 $10k | `datasource.py:124,134,293` | 读代码 | 展示≠账本 | 中 |
| P1-09 | P1 | Stats | 10 TRADE 全为 opp_fbo_short | decisions `chosen_opportunity` 计数=10×fbo_short | 扫 decisions | 有效N≈2–3 | 高 |
| P1-10 | P1 | Replay | replay 不含市场数据 | `replay.py`（仅账本） | 读代码 | 决策不可复现归因 | 中 |
| P1-11 | P1 | Isolation | V2 技术源=V1 采集 tick | `local_bars.py:16`(data/live_fxtm) | 见 §13 | 数据面未隔离 | 高 |
| P2-01 | P2 | Dashboard | 每≤30s 连 MT5，与“不触网”矛盾 | `acc_probe.py:9-19`; `datasource.py:20-38,318` | 读代码 | 监控触交易面 | 高 |
| P2-02 | P2 | Dashboard | 不校验账本链；静默丢行 | `datasource.py:58-72,295` | 读代码 | 展示层不 fail-closed | 高 |
| P2-03 | P2 | Dashboard | 阻塞子进程在 async 路径 | `server.py:44-58`; `datasource.py:318` | 读代码 | 面板卡顿 | 中 |
| P2-04 | P2 | Observer | rate 为二值/全历史聚合 | `v2_observer.py:119,47-79` | 读代码 | 健康指标误导 | 中 |
| P2-05 | P2 | registry | 元数据未被读取 | `registry.py:26-44` vs adapters | 读代码 | 漂移 | 中 |
| P2-06 | P2 | Cache | 多进程 LWW/非原子写 | `cache.py:28,56-77` | 读代码 | 竞争/半写 | 中 |
| P2-07 | P2 | Cost | broker spread/slip 未单项入账 | `broker_demo_executor.py:222-235` | 读账本 | 成本归因不完整 | 中 |
| P2-08 | P2 | Repro | 无市场数据归档/flag 未入 manifest | run_manifest 字段 | 读 manifest | 不可复现 run | 中高 |
| P2-09 | P2 | Tests | `test_research_compute` 预存失败 | `gpu_accelerator/core/__init__.py` 无 `gpu_backend`；干净 worktree 同样失败 | 干净 worktree 复现 | 套件非全绿 | 高 |
| P3-01 | P3 | UI | 硬断言 V1/execution/0 PnL | `datasource.py:281-285,316,340` | 读代码 | 无证据断言 | 中 |
| P3-02 | P3 | Docs | 多处文档漂移 | 见 §20 | — | 维护性 | 高 |
| P3-03 | P3 | Observer | 双计数器/分离缓存/滞后 | `v2_scheduler_state` vs `v2_run_health` | 读 state | 指标不一致 | 中 |
| P3-04 | P3 | Audit | `router_audit.jsonl` 41MB | 文件大小 | dir | 增长 | 中 |
| INFO-01 | INFO | Scheduler | broker=UTC+3 假设；DST 未验 | `trading_hours.py` | — | 边界偏移 | 中 |
| INFO-02 | INFO | Audit | 失败日志限速聚合 | `audit.py:64-82` | — | 证据不全 | 高 |
| INFO-03 | INFO | Data | WGC/央行/政策利率未取（显式 gap） | `agent2.py:206-207,119-120` | — | 已知限制 | 高 |

---

## PASS 清单（WHAT / HOW / EVIDENCE）

| 项 | 如何验证 | 支撑证据 |
|---|---|---|
| Ledger 完整性 | 读 `verify_ledger` + 4644 运行值 | verify=True (134 ev), sha 链/seq |
| Ledger 半写 fail-closed | 读 `load_events` 异常路径 + shadow_run 处理 | `LedgerMalformed`→BLOCK |
| Replay 独立性 | 读 `replay.py`（不调执行/账户） | `replay.py:27-92` |
| V1 代码/账户/终端/magic/ledger 隔离 | 读配置+adapter gates | magic 90003 vs 90002；demo_01 vs 主终端 |
| LIVE 不可达 | 读所有安全门 | `assert_execution_allowed`/`_guard`/adapter DEMO 校验；无 oanda 实现 |
| Bars PIT | 读三层剔除 + 抽样 7 决策 | `validate.py:29-30` 等；a1_gen>bar |
| Scheduler 不补跑 stale | 读 Task XML + ensure_run | 无 StartWhenAvailable；窗口去重 |
| Broker reconcile 三路径 | 读 tests + 运行计数器 | `broker_reconcile.py` T1–T8；counters |
| 风险 ≤ 目标（除 min-lot floor） | 读 sizing 链 + 历史 R | risk 0.85–2.9% |

---

## 29. 复查声明（避免“看起来没问题”）

- 每条 PASS 均给出 **WHAT / HOW / EVIDENCE**（上表）。凡未取得直接证据者，一律标注“待深查”（如 §9 broker 实际 digits/tick/min-stop）。
- 未做任何修复；未改动任何文件（除新增本报告）。

## 30. 收尾声明

```
CODE_CHANGED        = FALSE
CONFIG_CHANGED      = FALSE
LEDGER_CHANGED      = FALSE
RUN_STATE_CHANGED   = FALSE
V1_CHANGED          = FALSE
BROKER_ORDER_SENT   = FALSE
CURRENT_RUN_MODIFIED= FALSE   (运行中的 1ed3 由其调度正常驱动；审计未写它)
```

- **AUDIT_COMMIT**: 见文末 commit（本报告提交，仅此文件）
- **BASE_COMMIT**: `7fe4828eab194ec3fc6c32351662b6b40dfc7176`
- **WORKTREE_STATUS**: 审计未引入任何 tracked 代码/配置改动；工作树中既有的 `M`（V1 run_state、V2 state、tests/_tmp、`PRICE_SPACE_AUDIT.md` 等）均为**运行系统自身**产物，非本次审计所为。
- **临时进程**: 未启动长驻进程；仅短命令（只读 python），均已退出（无残留 PID）。子审计仅读文件。

**审计到此为止，不自动进入下一阶段。**
