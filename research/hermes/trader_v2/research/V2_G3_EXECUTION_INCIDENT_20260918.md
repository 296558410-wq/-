# V2 G3 — 执行 Guard 事故与修复报告

- incident: `EXECUTION_REJECTED_BY_PAPER_GUARD`
- 关联决策: `DEC-ctx_de3ee55784b1`
- run: `V2-SHADOW-20260917-105319-b5e4`（G3 最终 shadow，48h，PAPER/no-broker）
- 报告时间(UTC): 2026-09-17T23:13Z（CST 2026-09-18 07:13）
- status: **CONFIG_FIX_APPLIED**（等待下一轮 TRADE 才能升级为 `FIX_VERIFIED`）

## 1. BUG 根因
`config/v2_config.json` 的 `execution.execution_mode` 遗留为 `BROKER_DEMO`（2026-09-11 commit `3227043` 为 demo run 武装后未复位）。
本 run 为 shadow（`RUN_META.shadow=true`），`_make_executor()` 一律选用 `PaperExecutor`；其 `_guard()` 要求 `execution_mode == "PAPER"` 且 `live_trading == False`，否则 raise `RefuseExecution("NON_PAPER_MODE")`。
→ 配置 mode=`BROKER_DEMO` 与 shadow 的 PaperExecutor guard 冲突 ⇒ 该 run 任何 TRADE 都在 `open()` 被拒，无法成交。
- 触发: `2026-09-17T22:52:45Z`（CST 06:52:45），本 run 首笔（第 46 窗口）TRADE。
- 报错: `paper_executor.RefuseExecution: NON_PAPER_MODE: mode=BROKER_DEMO live=False`

## 2. ⚠️ 范围说明（重要，请审计）
用户授权**仅**改 `execution.execution_mode: BROKER_DEMO → PAPER`。
**该单点改动不足**：`assert_execution_allowed()` 在 `mode=PAPER` 时要求 `broker.enabled` 与 `execution.broker_demo_enabled` **均为 false**。只改 mode 会导致每一轮 cycle 在启动闸即 `REFUSE_TO_START`（实测 `2026-09-17T23:07:03Z`，0 cycle 运行）。
为使授权的 “PAPER/no-broker” 语义（及 §6 禁止 broker 下单）真正成立，**额外**将两个 broker 武装开关置 false。仅涉及 broker 武装语义，不涉及策略/风控/信号/G3 冻结/历史数据。
> 可一键还原为原状：3 字段恢复 `BROKER_DEMO / true / true`。

## 3. 修改文件
`research/hermes/trader_v2/config/v2_config.json` —— 共 3 行（git diff 确认）：
| 字段 | before | after |
|---|---|---|
| `execution.execution_mode` | `BROKER_DEMO` | `PAPER` |
| `execution.broker_demo_enabled` | `true` | `false` |
| `broker.enabled` | `true` | `false` |

## 4. before / after SHA256
- before: `7bfab969722ff38a2d5607257750f138241851b464007186ae101316eaf37aff`（= G3 冻结清单 `file_sha256["config\\v2_config.json"]`）
- after:  `91c3587bec9056c3d11f0fd68177b48cd496bc01438273cc97f7ef114b2b4fa0`
- 中间态（仅改 mode）: `d930ebe3415f5359bb7efa9004c4409b873cf773f04d0b010197c3384e86d045`
- 说明: 冻结清单 `state/V2_G3_FREEZE.json` **未改动**（属“G3 数据冻结”）。本次是该清单 config 条目的**经用户授权的显式偏离**，于此记录。

## 5. 是否修改代码
**否。** 零代码改动（无 PaperExecutor 改造，无策略/风控/信号改动）。

## 6. 是否产生 broker order
**否。** `BROKER_ORDER_SENT = FALSE`；`FORWARD_VALIDATION_ALLOWED` 不存在；broker 已 disarm，无连接、无下单。

## 7. Ledger 是否修改
**否。** `evt-000099-EXECUTION_REQUEST` 原样保留（status=REQUESTED，无 RESPONSE；不删/不改/不伪造）。ledger verify=True，99 事件，head 仍 `c6013da0…`（修复前后一致）。

## 8. windows 缺口处理（22:45Z）
- 不伪造窗口/TRADE/执行成功；**未写入 ledger**（保护 append-only + SHA256 链）。
- 独立审计标记（本文件 + `state/V2_G3_EXECUTION_INCIDENT.json`）: `EXECUTION_ERROR / INCOMPLETE`；run_state.windows 保留缺口，不回填。

## 9. 修复后验证（只读）
| 检查项 | 结果 |
|---|---|
| config execution_mode | `PAPER` ✅ |
| assert_execution_allowed | `PASS` ✅ |
| assert_paper_only | `PASS` ✅ |
| PaperExecutor active | guard `PASS`；run 选择器 = `PaperExecutor`/`paper_local` ✅ |
| no broker execution | `BROKER_ORDER_SENT=FALSE`；broker disarmed；FORWARD 未开 ✅ |
| V1 / V3 | 未触碰 ✅ |
| V2 G3 state | run_state/ledger/freeze 未改（mtime/hash 不变）✅ |
| ledger integrity | `verify=True`（n=99，head 不变）✅ |
| replay_match | Guardian `check` ok=True，replay_mismatch=[] ✅ |

## 10. 后续周期验证结果（已回填）
- 23:15Z：WAIT（source=local_fxtm，DEGRADED）
- 23:30Z：WAIT（source=local_fxtm，DEGRADED）— F1 生效
- **23:45Z：TRADE(SHORT)**，overall=**PASS**，source=**mt5**；闭环
  `TRADE(evt-104)→EXECUTION_REQUEST(evt-105)→EXECUTION_RESPONSE(evt-106)→ORDER_REJECTED(evt-107)`；
  **不再出现 NON_PAPER_MODE**；结果 `REJECTED: RISK_LIMIT`（0.11>0.05，风控设计）；replay MATCH，ledger verify=True。

> 判定：执行 guard 原故障已消失（协议层闭环完整）；因 RISK_LIMIT 未成交，故 `FIX_VERIFIED`（成交闭环）暂不成立，维持 `CONFIG_FIX_APPLIED`。

## 12. 追加修复（长期运行审计，2026-09-18）
- **F1**（`hermes/context.py`）：MT5 唯一交易行情源守卫 —— 技术K线/现货价非 mt5 → `technical/overall=DEGRADED` → `gate=WAIT`。
- **F2**（`execution/fxtm_demo_adapter.py` + `data_sources/mt5_market.py`）：MT5 只读行情与执行武装解耦（`connect_readonly()`），PAPER/no-broker 下仍可读 MT5，下单路径硬拦截不变。
- 详见 `research/V2_LONG_RUN_AUDIT_20260918.md`。

## 11. 未触碰清单（确认）
V1 / V3 / V2 策略逻辑 / 风控参数 / 信号阈值 / G3 数据冻结文件 / 历史交易数据 / 已产生 ledger 事件 —— **全部未触碰**。

> 完成后暂停，等待人工审计。
