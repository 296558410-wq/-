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

---

_更新约定：每次协作层变更/新决策后更新本文件，并保持分类标注。_
