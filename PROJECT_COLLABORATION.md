# PROJECT_COLLABORATION.md

> 本项目（AIQuant / Hermes 交易系统）的**协作契约与边界**。
> 所有参与方在行动前必须遵守本文件。
> 版本：v2（2026-09-19 扩充分工/审计/研究真实性规则；v1 于同日初建）

协作链路：

```text
用户 → ChatGPT → GitHub → OpenClaw → Hermes → GitHub → ChatGPT → 用户
```

---

## 1. 角色分工（Roles）

### 1.1 用户（User）

**项目所有者与最终决策者。**

职责：
- 最终接受 / 拒绝重大研究结论
- 是否改变系统架构
- 是否进入下一阶段
- 是否允许高风险操作（如实盘、broker 下单、风控/配置变更）

**用户不是执行机器人**：所有重大决策由用户拍板。

---

### 1.2 ChatGPT

**独立研究员 + 独立审计者 + 质疑者。**

职责：
- 提出研究问题
- 审查 OpenClaw 的工作
- 审查 Hermes 的结果
- 检查数据与方法
- 挑战错误结论
- 检查：look-ahead / data snooping / overfitting / multiple testing / effective N / overlap / 成本 / 数据缺口
- **不因 OpenClaw 或 Hermes 声称成功就接受成功**

边界：**ChatGPT 不直接修改本地交易系统**。

---

### 1.3 OpenClaw

**本地执行控制器 + 项目工程执行者。**

职责：
- 执行 ChatGPT / 用户批准的任务
- 操作本地文件、执行测试、执行研究程序
- 管理 Git、管理任务状态
- 保存证据、生成报告
- 将适合公开协作的成果提交 GitHub

边界：**OpenClaw 不得擅自把实验结果升级为生产结论**。

---

### 1.4 Hermes

**交易智能 / XAUUSD 决策智能。**

职责：
- 市场分析、opportunity discovery
- trading reasoning、交易决策解释
- XAUUSD 相关研究

边界：**Hermes 的结论必须保留证据；Hermes 不能自己定义"成功"**。

---

### 1.5 GitHub

**协作事实层 + 版本控制 + 审计层。**

保存：代码 / 研究报告 / 审计报告 / 任务 / 决策 / 冻结数据 / 方法说明 / 版本信息。

**不保存**：密码 / API keys / tokens / private keys / broker credentials / `.env` / MT5 account snapshots / runtime ledger / live state / 私有账户数据 / 运行态日志。

---

## 2. 版本隔离（Version Isolation）

- **V1 / V2 / V3 相互隔离**，各自独立目录、配置、运行态、账户/magic。
- **不得跨版本修改**；改动任一版本不得触碰其他版本。
- 本协作层任务中：**V1 / V2 / V3 / Hermes / MT5 / Broker 一律 READ ONLY**。
- V1 默认冻结只读，仅观察。

---

## 3. V2 当前阶段

- V2 当前为 **Shadow / Paper 阶段**（非实盘）。
- 实盘（live）硬锁关闭；在取得充分 forward 证据并通过验收前，不进入真实资金交易。

---

## 4. 行情源纪律（V2 硬规则）

1. **MT5 是 V2 唯一的交易决策行情源。** 其它来源不得进入决策/执行价格空间；参考市场仅作 reference。
2. **MT5 异常必须安全 WAIT，不得 fallback 后继续交易。** 缺失/断流/超时/校验失败 → 安全降级为 WAIT，且降级必须**可见**（记录 gap/状态），不得静默用旧数据顶替。

---

## 5. 安全规则（GitHub 内容）

**严禁上传**：账号/密码（含 MT5 login/password/server）、token / API key / 私钥 / 证书、`.env*`、个人敏感信息、运行中的私密数据（实时/运行态账本、持仓账户明细、tick/行情原始数据、私有缓存与证据原文）。

**要求**：上传前做密钥扫描（工作树 + 历史）；发现凭据先脱敏/移除再上传并记录；不删除本地历史证据。

> 注意：**不得仅因文档出现 "token"/"password" 等词就误判**——必须区分 *documentation keyword* 与 *actual credential/value*。

---

## 6. 运行态隔离

以下不得进入 GitHub：`run_state/`、`state/`、live ledger、account snapshots、order snapshots、`trader_summary.txt`、runtime logs、private `memory/reviews`。

新增文件需先判断：**static research artifact** 还是 **runtime/private data**；不得仅按扩展名盲目处理。

> JSONL 说明：`.gitignore` 现有 `*.jsonl`。未来不得简单认为"所有 JSONL = runtime"——也可能是 static research fixture / frozen dataset / reproducible test input，需按用途判断。

---

## 7. 研究真实性规则（所有研究任务）

流水线：

```text
Hypothesis → Frozen Definition → Data → Preprocessing → Signal →
Execution Assumption → Cost → Statistical Test → Multiple Testing →
Robustness → Conclusion
```

禁止"看到赚钱结果 → 再寻找解释"。若确属事后分析，必须显式标记：`POST-HOC`。

---

## 8. 结论分类

所有研究结论必须归入：

```text
SUPPORTED
PARTIALLY_SUPPORTED
EDGE_UNCERTAIN
REJECTED
UNRESOLVED
DATA_GAP
```

禁止以 `BEST` / `GUARANTEED` / `PROFITABLE` / `HIGH CONFIDENCE` / `WILL WORK` 作为未经证据支持的最终结论。

---

## 9. 交易系统特殊规则

本协作层**不得**因任何研究结果自动触发：`LIVE` / `DEMO` / `BROKER_ORDER` / `POSITION_CHANGE` / `RISK_CHANGE` / `CONFIG_CHANGE`。

研究系统与执行系统必须隔离。任何从 **research → trading** 的改变，都必须经过**明确的用户决策**。

---

## 10. 任务与提交规则

- 任务 ID 统一格式：`TASK-YYYYMMDD-NNN`（例 `TASK-20260919-001`）。报告必须使用相同 ID；一个任务只能有一个 ID。
- 任务状态仅允许：`DRAFT` / `READY` / `RUNNING` / `BLOCKED` / `COMPLETED` / `REJECTED` / `CANCELLED`。
- Commit：正常 commit + 正常 push；**不 force / 不 amend / 不 squash 既有 baseline**。
- 协作目录：
  - `collaboration/status/` —— 状态与报告
  - `collaboration/decisions/` —— 用户决策记录
  - `collaboration/tasks/CHATGPT_TO_OPENCLAW/` —— 任务模板
  - `collaboration/tasks/OPENCLAW_TO_CHATGPT/` —— 报告模板
- 提交前自审：`git status` / `git diff` / `git diff --cached` / `git log`，并核对 §19 验收项。

---

_本文件随项目演进更新；更新需记录版本与日期。_
