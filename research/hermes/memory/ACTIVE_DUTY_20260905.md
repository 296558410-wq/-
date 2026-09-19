# ACTIVE DUTY INTELLIGENCE UPDATE（2026-09-05 · 第一次 active duty）

> 仅记录真正改变知识状态的信息（无 material change 时输出 NO MATERIAL UPDATE）。

## MATERIAL UPDATE：方法论/泄漏簇（RQ-05 相关）

### 1. 参数化 look-ahead 升级（FL-23）★ 最重要
- **新证据**：HindsightBench（arXiv:2607.18867）——黑盒、探针级成本的参数化 hindsight 审计协议。
- **关键发现**：date-trigger reflex **代际依赖**，非规模依赖：
  - 2024 代开放模型（1B–70B）全部干净；
  - **2026 代模型（低至 3B active）全部泄漏**；
  - 同 vendor 谱系内切换（Qwen3 → Qwen3.6，固定 MoE 架构 3B）即开启。
  - 行为有效 cutoff 跨 vendor 达 22 个月。
- **对我们的含义**：deepseek-v4-pro 属 2026 代 → **大概率存在参数化泄漏**。RQ-05 从"应做"升级为"必须做"。
- **ACTION**：REVISIT（RQ-05 现在有廉价审计工具 HindsightBench，可对 deepseek 直接探针）。

### 2. 搜索强度泄漏独立确认（FL-20b）
- jonathankinlay（2026-09）：无结构随机价格 → agent 产出 in-sample Sharpe 2.1，**88% 由两整数解释**（回测次数 + 混入赢家数）；独立 run 相关 0.62（crowding 风险）。
- **含义**：FL-20 从"理论风险"变为"有实测数字的确认事实"。

### 3. 结构性护栏 ≠ 统计校正（印证 RLAP）
- 2608.27734：故意泄漏的 oracle 报 Sharpe 35，**完全骗过 Deflated Sharpe + PBO**。
- **含义**：OpenClaw 正在做的 RLAP 结构性思路（look-ahead 不可表达，而非"提示避免"）是**正确的**，且统计校正不能替代它。

## 分类

- FL-23：METHODOLOGY_RISK 升级（代际恶化 + 可审计）
- FL-20b：CONFIRMED（独立实测确认）
- RQ-05：REVISIT（有廉价工具，deepseek 大概率受影响）

## 未改变的部分

方向 alpha（DEAD）、执行/做市（INACCESSIBLE）、风险/成本择时（R1 唯一有肉）、跨资产 lead-lag（CONTRADICTED）——均无新证据改变。
