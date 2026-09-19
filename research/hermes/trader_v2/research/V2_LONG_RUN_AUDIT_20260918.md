# V2 长期运行审计报告 — 2026-09-18

- 范围: `C:\AIQuant\research\hermes\trader_v2`（Shadow/Paper，MT5 唯一交易行情源）
- run: `V2-SHADOW-20260917-105319-b5e4`（48h，PAPER/no-broker）
- 生成(UTC): 2026-09-18T00:0xZ（CST 08:0x）· 审计人: OpenClaw(main)
- 结论等级: **LONG_RUN_READY_WITH_OBSERVATION**（安全不变量已验证；仍待更多周期与首笔“成交”闭环）

> 原则: 安全 > 数据正确性 > 运行稳定性 > 可审计性 > 交易机会。本文不掩盖任何问题。

---

## 0. 证据基线（修改前，只读）
| 项 | 值 |
|---|---|
| git HEAD / branch | `d22d9fb` / `fix/v2-full-system-repair-20260917` |
| 配置 SHA256（before） | `7bfab969722ff38a2d5607257750f138241851b464007186ae101316eaf37aff` |
| context.py（before） | `69cd9cccd4b282a19f7bb40e26a94d9c0eef8eebb2f327fa1f1d6e73f0bd7a39` |
| fxtm_demo_adapter.py（before） | `6aaaa539e5b420ef7915b360cc7f06bb59a36749442c00e79c865fb4d87e085c` |
| mt5_market.py（before） | `256442a90d2415c22f690eca0efb4564d26b88fe7b58e08ce9ae76ec2b97f9c5` |
| run_state | RUNNING，windows 45，counters TRADE 0 / WAIT 45 |
| ledger head（before） | `c6013da0…`（n=99，verify=True） |
| replay | MATCH |
| MT5 PID | V1=`1348`(Program Files) · V2=`36460`(fxtm_demo_01) · V3=`56544`(fxtm_demo_v3) |
| V2 调度 | Windows 任务 `hermes-v2-cycle`（15m）；V1=`OpenClaw cron hermes-trader-m15-cycle` |
| V1/V3 | 未触碰 |

---

## 1. 审计发现

### 1.1 配置与执行 guard —— PASS
`execution_mode=PAPER`、`broker_demo_enabled=false`、`broker.enabled=false`、`live_trading=false`；
`assert_execution_allowed()`=PASS、`assert_paper_only()`=PASS、`PaperExecutor guard`=PASS；
`FORWARD_VALIDATION_ALLOWED` 不存在；`SHADOW_ALLOWED`=true；`BROKER_ORDER_SENT=FALSE`。

### 1.2 行情数据链 —— 发现**硬不变量违例**（已修）
调用链证据：`agent1.build` → `market_data.snapshot_history/fetch_quote` → `data_sources.router`
→ `registry.QUOTE_SOURCES["gold_spot"]=[mt5,sina,tencent,local_fxtm]`、
`registry.HISTORY_SOURCES=[mt5,local_fxtm,yahoo]`（**确定性 fallback**）。
决策门禁证据：`hermes/context.build_health()` 仅依据 `a1.data_quality.gaps` 与 freshness 判定
technical；**完全不看行情源**；`hermes/hermes.gate()`：`overall==DEGRADED → WAIT`。
实测：`build_health(history=local_fxtm, gold_spot=sina, gaps=[], fresh)` → `overall=PASS` ⇒
**fallback 行情可产出 TRADE**（违反 §二/§六）。

### 1.3 MT5 读取与执行武装**耦合**（fallback 的根因）
`execution/fxtm_demo_adapter.FXTMDemoAdapter._gate()` 要求
`execution_mode=="BROKER_DEMO" and broker_demo_enabled`；`data_sources/mt5_market._adapter()` 复用该连接。
⇒ §四 要求“PAPER + broker 双 false”后，**MT5 只读行情也被拒**（实测：
`connect -> refused: execution_mode=PAPER broker_demo_enabled=False`），router 遂静默回退
`local_fxtm/sina`（23:22Z、23:30Z 两轮实测 source=local_fxtm）。
→ 这正是 §三 禁止的 “MT5失败 → 换源” 被**由配置改动间接触发**。

---

## 2. 最小安全修改（均在 V2，未动 V1/V3/策略/风控/信号/G3 冻结/历史账本）

### F1 — MT5 唯一交易行情源守卫（`hermes/context.py`）
新增 `_trading_source_status(a1)`：若技术 K 线 `sources.history != "mt5"` 或 `quotes.gold_spot.source != "mt5"`
（含 `cache(...)`）→ 记为 DEGRADED；并入 `build_health` 的 technical，health 输出新增
`trading_source_status` 与 `trading_source_bad`。
效果：MT5 不可用/换源 → `technical=DEGRADED`、`overall=DEGRADED` → `gate → WAIT`（**安全 WAIT**，不产生信号）。

### F2 — MT5 只读行情与“执行武装”解耦（`execution/fxtm_demo_adapter.py` + `data_sources/mt5_market.py`）
- `FXTMDemoAdapter`：`connect()` 拆为 `_attach()` + `connect()`；新增 `connect_readonly()`（**跳过 execution 武装门，保留终端/账户/服务器隔离校验；绝不发单**）。
- `mt5_market._adapter()` 改用 `connect_readonly()`。
效果：PAPER/no-broker 下 MT5 只读行情恢复可用；下单路径仍各自 `_gate()`，硬拦截不变。

### F3 — 恢复 sizing 基线（`config/v2_config.json`，2026-09-18 下午）
同一 commit `3227043` 还把 `risk.per_trade_pct 1.0→2.0`、`execution.backend paper_local→fxtm_demo`。
配 $10000 paper 账户 + ~17pt 止损 → 2% 风险 = 0.11 手 > `max_lot 0.05` ⇒ **每笔 TRADE 均 RISK_LIMIT 拒（0 成交）**。
已恢复至 pre-demo 基线（`f3bf407`）：`per_trade_pct 2.0→1.0`、`backend fxtm_demo→paper_local`。
现配置 diff = `3227043` 的**完全逆操作**；sizing 现为 0.05 手 ≤ max_lot，可正常成交。

### 测试
- 新增 `tests/test_mt5_only_source.py`（9/9 PASS）。
- 更新 `tests/test_v2_repair.py` R7c（旧断言写死 `BROKER_DEMO`，与新不变量冲突）→ 断言 PAPER+broker disarm（21/21 PASS）。

### SHA256（after）
| 文件 | before | after |
|---|---|---|
| config/v2_config.json | `7bfab969…` | `01bc3b8b…`（恢复5项演示遗留） |
| hermes/context.py | `69cd9ccc…` | `78952a51…` |
| execution/fxtm_demo_adapter.py | `6aaaa539…` | `8188a19b…` |
| data_sources/mt5_market.py | `256442a9…` | `954b3dcc…` |
| tests/test_v2_repair.py | — | `a0e33a14…` |
| tests/test_mt5_only_source.py (新) | — | `f99a2f55…` |

---

## 3. 修改后验证
- git diff：4 文件（context.py / fxtm_demo_adapter.py / mt5_market.py / test_v2_repair.py）+ 1 新测试。
- 全量回归：**34 个测试文件全绿**（含 test_data_sources 37/37、test_freshness_health 16/16、test_failure_injection 13/13、test_module6_broker_demo 19/19、test_broker_reconcile 25/25、test_mt5_only_source 9/9、test_v2_repair 21/21 等）。
- guards：`assert_execution_allowed`/`assert_paper_only`/PaperExecutor guard 全 PASS。
- MT5 只读恢复：`quote src=mt5`、`history 15m n=891`、`1d n=88`（router 选中 `mt5`）。
- ledger verify=True；replay MATCH；V1/V3 未动。

### 修改后真实周期证据（scheduler；15m）
| window (Z) | decision | overall | source | execution |
|---|---|---|---|---|
| 23:15 | WAIT | DEGRADED | local_fxtm | —（修复前） |
| 23:30 | WAIT | DEGRADED | local_fxtm | —（F1 生效，拦截 fallback） |
| 23:45 | **TRADE**(SHORT) | **PASS** | **mt5** | `REQUESTED→RESPONSE: REJECTED:RISK_LIMIT` |

23:45Z 闭环（协议层完整）：`TRADE(evt-104) → EXECUTION_REQUEST(evt-105) → EXECUTION_RESPONSE(evt-106) → ORDER_REJECTED(evt-107)`；
**不再出现 `NON_PAPER_MODE`**；ledger verify=True，replay MATCH。
拒因：`RISK_LIMIT: position_size 0.11 > max_lot 0.05`（sizing=2%×10000/(17.36×100)=0.115→floor 0.11；属**风控设计**，非本案 BUG）。

---

## 4. 逐项回答（§十五）
- **A. 今天 V2 是否正常运行？** 是。修后连续周期正常，run_status=RUNNING、blocked=null。
- **B. 15m scheduler 是否稳定？** 是。Windows 任务 `hermes-v2-cycle` 按 :07/:22/:37/:52 运行，missed=0；23:07 曾因配置中间态 REFUSE（已修，之后正常）。
- **C. MT5 是否已成唯一交易决策行情源？** 是（修后）。新增 source 守卫：非 mt5 → DEGRADED→WAIT。
- **D. MT5 断流能否安全 WAIT？** 能。F1 使非 mt5 源 → `overall=DEGRADED` → gate WAIT。
- **E. 是否还有 fallback 能产生交易决策？** 否。fallback 数据仍可作诊断，但已无法通过 gate 产生 TRADE。
- **F. Paper-only 是否成立？** 是。PAPER + broker 双 disarm + guards PASS + `BROKER_ORDER_SENT=FALSE`。
- **G. 是否出现真实 TRADE？** 是。23:45Z 一笔 SHORT（paper，非 broker）。
- **H. execution 闭环是否完整？** **协议层完整**（REQUEST→RESPONSE→ledger→verify→replay MATCH），但**未成交**（RISK_LIMIT 拒）。原始 `NON_PAPER_MODE` 故障已消失。
- **I. replay 是否全 MATCH？** 是。
- **J. ledger 是否完整？** 是（verify=True，append-only 链完整）。
- **K. V1 是否完全未受影响？** 是。
- **L. 是否还有必须继续修的问题？** 无新增。sizing vs max_lot 已由 **F3** 修复（恢复 `per_trade_pct=1.0` 基线）；待下一笔 TRADE 确认成交闭环。
- **M. 系统状态**：**LONG_RUN_READY_WITH_OBSERVATION**

---

## 5. 长期运行安全检查（§十二）
- 进程层: V2 调度=Windows 任务；MT5 V2 实例 pid 36460 唯一；无重复实例/无重启循环。
- 数据层: MT5 tick/rates 读取正常（quote/15m/1d 有数）；PIT 剔除未收盘；spread/bid/ask 有效。
- 决策层: agent1/agent2/hermes 正常；decision contract/WAIT/TRADE/replay 正常。
- 执行层: PaperExecutor 生效；guards PASS；broker 与 broker_demo 均 disable；无 live 路径。
- 审计层: ledger 链/verify/replay/incident/run_state 齐全（新增 `state/V2_G3_EXECUTION_INCIDENT.json`、本报告）。
- 隔离层: V1(magic 90002, Program Files 终端, OpenClaw cron) ≠ V2(magic 90003, fxtm_demo_01, Windows 任务) ≠ V3(magic 90004, fxtm_demo_v3, order_send 硬拦)。state/ledger/config 各自独立。

---

## 6. 待观察 / 待裁定
1. **首笔“成交”闭环**：需一笔 sizing ≤ max_lot 的 TRADE 完成 `REQUESTED→EXECUTED`（当前受 RISK_LIMIT 阻断）。
2. **sizing vs max_lot**（待用户裁定，非 BUG）：`per_trade_pct=2.0` 对 $10000 + `max_lot=0.05` 在小止损下系统性拒单。
3. 持续观察更多真实周期（已设只读巡检 cron，每 15m；异常/TRADE 才告警）。
4. 历史 22:45Z incident（`evt-000099`）与缺口：保持不可变，已在 `V2_G3_EXECUTION_INCIDENT_20260918.md`/`.json` 记录。

> **INCIDENT_REVIEWED**：22:45Z `EXECUTION_REJECTED_BY_PAPER_GUARD` 根因为 execution_mode/guard 冲突；已由 F1（源守卫）+ 配置复位（PAPER）解决其同类路径；`evt-000099` 原样保留，未伪造 RESPONSE。
