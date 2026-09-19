# V2 Module 6 报告 — BROKER_DEMO 执行接线（闭环打通）

> 日期: 2026-09-13 · 账户: FXTM Demo `******`（独立实例 `C:\AIQuant\mt5_instances\fxtm_demo_01`，magic=90003）· 执行器: `execution/broker_demo_executor.py`

## 目标
把"门打开"——让 V2 在满足安全门时把 Hermes 决策**真实**下到独立 DEMO 实例，形成
`DECISION → EXECUTION_REQUEST → broker 下单 → FILL → POSITION_OPEN → … → POSITION_CLOSED/COST/PNL → ACCOUNT_SNAPSHOT`
的可对账闭环；V1 与真实资金保持零接触。

## 交付（commit）
- `70ae8da` Module 6 接线：`BrokerDemoExecutor` + ADP 路由 + `assert_execution_allowed`（demo-only 门）+ 离线测试 19/19。
- `3227043` arm 配置：`execution_mode=BROKER_DEMO`、`broker.enabled=true`、`broker_demo_enabled=true`、`live_trading=false`；`risk.per_trade_pct=2.0`（见下"风险预算"）。
- `d176837` 收尾：run_manifest 记录真实 execution_mode；测试与实时 config 解耦；面板文案中性化；cron 备份。
- `a7b814c` 修 3 个预存在 FAIL 测试（幂等化 + V1-isolation 扫描收敛）。

## 关键实现
- **执行器** `BrokerDemoExecutor`：与 `PaperExecutor` 同接口（acc/open/close/account/_fresh/size_position_raw），
  但 order/close 走 `FXTMDemoAdapter`；成本/盈亏以 **broker deals 实际值**（profit/commission/swap）为准；
  FLOOR-TO-STEP 手数、min/max_lot/notional/risk 硬拒绝与 Paper 一致；单标的单仓。
- **路由** `hermes_paper_adapter.process(..., execution_mode=)`：事件打 `environment/execution_mode` 戳；
  PAPER 路径行为不变；BROKER_DEMO 用 broker 的 commission/swap 入账。
- **门** `assert_execution_allowed()`：允许 PAPER 或 BROKER_DEMO，**任何 LIVE 一律 REFUSE**；
  `assert_paper_only()` 保留给 PAPER-only 语境。适配器 `_gate` 仍要求 实例=`fxtm_demo_01` / server=`ForexTimeFXTM-Demo01` / DEMO，否则 `RefuseConnection`。
- **broker 口径对账** `_account_match`：balance/equity/realized/commission 与账本 replay 一致（容差 0.05）。

## 测试
- 新增 `tests/test_module6_broker_demo.py`：**19/19 PASS**（离线 FakeAdapter，不触网/不连 broker）。
- 全量回归：12 个测试文件**全绿**（含原 3 个预存在 FAIL 已修）。
- 实机只读预检：adapter 连上 ******（DEMO/服务器/账户校验过），读 account \$999.87、quote 正常。

## 手数政策 v2（Module 6.1, 2026-09-13 按用户要求改）
**问题**：`qty=floor(风险预算/(dist·100))` 在小账户上天数不足 → floor 到 0.00 → 被 min_lot 拒 → "能接 broker 但永不下单"（\$1000 demo 亦如此：1%≈\$10，SL≈18pt → 0.005）。
**改法（贴合实际的平台最小手底线）**：
- `qty = max(floor_to_step(raw), min_lot)`；**不再因 qty<min_lot 拒单**（平台最小手 0.01 是硬底线，小账户也按 0.01 交易）。
- 风险允许额 = `max(per_trade_pct%·equity, min_lot·dist·100)`（即"风险预算或最小手风险，取大者"）；并加 `risk<=equity` 保险。
- `max_lot` 仍**硬拒**（不 clamp）；`notional` 上限不变。
- 新不变式：`actual_risk ≤ max(target, min_lot_risk)` 且 `actual_risk ≤ equity`（§六随机 1200 例验证）。
**效果**：\$200 / \$1000 账户均可成交 0.01（\$200 时 0.01 风险≈\$15–25 ≈ 7.5–12.5%，属小账户固有）；\$10k 级仍按风险预算（本次配置 `per_trade_pct=2.0`）。`test_sizing_floor` 34/34 PASS。

## 安全 / 隔离（硬约束，均已满足）
- `live_trading=false`；不会触真实资金；不动 V1 任何文件/终端/账户（V1 主终端 ****** 与 V2 独立实例 ****** 完全分离）。
- 凭据不落盘（`/portable` 免密）；日志仅掩码。
- `BROKER_DEMO` 事件与 `PAPER` 事件在账本/`replay(execution_mode=)` 中按环境分离。

## 验证状态
- 代码/单元/回归/连通性：**已验**（离线 + 只读实机）。
- **真实下单闭环：未验**——2026-09-13（周日 UTC）市场休市，试下单返回 `10018 Market closed`。
  真实 open→close→pnl 闭环须待**周一开市**（周日 22:00Z / 本地周一 06:00）后验证。
  已排程：`hermes-v2-fixed-run-start`（周日 20:00Z 起 24h BROKER_DEMO run）+ `hermes-v2-fixed-run-acceptance`（周一 20:20Z 自动 finalize + 验收）。

## 尚未做 / 待办
- 周一开市后实机闭环验证（run + acceptance 自动跑）。
- 周日 00:00–19:59Z 两个 job 仍空转 skip（省 token 优化：主 job 改 `1-5` + 加周日 `20-23` 专属 job；本次未改，因 cron next-run 计算存疑，谨慎优先）。
- V1 的 `hermes-trader-m15-cycle` 同样有空转（属 V1 cron，未动）。
