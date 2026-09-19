# HERMES QUANT BENCHMARK（量化研究能力基准）

> 生成：2026-09-05 · **冻结版**：评分体系/权重/10 任务在测试开始前写死，测试后零改动。
> 材料来源：HERMES-01 实际读取的 Phase 1–9A + R1' 内部研究（已匿名化/抽象化，不含可交易信号）。
> 被测对象：本地候选模型 vs 云端 deepseek-v4-pro（Hermes 当前主模型，作为参照上界）。

---

## 1. 冻结评分体系（MODEL FITNESS SCORE）

### 1a. 维度与权重（冻结，和=100）

| 维度 | 权重 | 说明 |
|---|---|---|
| Quant reasoning | 15 | 量化机制理解、因子逻辑 |
| Statistical reasoning | 15 | 显著性、多重检验、样本、p 值直觉 |
| Research auditing | 15 | 找泄漏/成本幻觉/设计缺陷 |
| Adversarial reasoning | 10 | 主动攻击"看似正确"结论、说"不知道" |
| Evidence handling | 10 | 区分 REJECT/EDGE/DESCRIPTIVE/因果 |
| Long context | 10 | 64K 稳定、范围限定保持 |
| Coding | 8 | Python 分析正确性 |
| Tool use | 7 | 结构化调用可靠 |
| Structured output | 5 | JSON 精确 |
| Self-correction | 5 | 被指出错误后修正 |

### 1b. 评分标准（0–4 每项，冻结）

| 分 | 含义 |
|---|---|
| 0 | 完全错误 / 幻觉 / 答非所问 |
| 1 | 方向对但关键错误（如把 EDGE 当 REJECT） |
| 2 | 部分正确，遗漏关键陷阱 |
| 3 | 正确，但范围限定/次要陷阱有遗漏 |
| 4 | 正确 + 主动指出范围限定/反证 |

### 1c. 判定门槛（冻结）

- 加权总分 ≥ 3.0（满 4）→ 该维度"胜任 quant 研究"
- 加权总分 < 2.0 → "NOT TRUSTWORTHY FOR THIS TASK"
- 本地模型若在 Statistical/Research auditing/Adversarial 三核心维度任一 < 2.0 → **不具备作 Primary Quant Brain 的资格**（无论总分多高）。

---

## 2. 十个真实研究任务（来自内部材料）

> 每题答案锚定 HERMES-01 已核实的结论；评分以"是否识别出陷阱 + 是否诚实说不知道"为准，不以"结论是否与我一致"为准。

**Task 1（找 lookahead）**：某研究声称"跨周期特征 H10 预测 60m 收益 IC=0.24，显著"。问：最可能的陷阱是什么？
→ 关键点：跨周期 asof 未做上层收盘延迟；截断重算抓不到此类泄漏。

**Task 2（dependency / multiple testing）**：某 session 规则 n≈9000 时 p=0.0000，n≈140–690 非重叠后 p=0.10–0.80。问：问题在哪？
→ 关键点：重叠标签自相关 → effective n 虚高；显著性被当独立样本。

**Task 3（win-rate vs expectancy）**：某策略"95% 胜率"，是否值得上？→ 关键点：95% 胜率+偶发巨亏 = 负期望；正净期望+足够机会+可接受风险才是目标。

**Task 4（cost illusion）**：某高频策略用 mid 价回测年化 40%，是否真实？→ 关键点：mid PnL 无 bid/ask/spread/slippage；≤1m 必须 bid/ask+spread+latency+adverse selection。

**Task 5（redundancy）**：某新提案"固定 vol-target 上做自适应缩放"。这算新研究吗？→ 关键点：若相对 fixed vol-target 无 OOS 增量 Δ → REDUNDANT（R1'-C 实例）。

**Task 6（temporal precedence vs causality）**：观察到"activity 先升，spread 后放宽"。能否说"点差/流动性前导波动"？
→ 关键点：先后≠因果；可能同因（活跃度状态两面）；无工具变量只报顺序。

**Task 7（preregistration）**：给定"宏观日程窗改变参与者构成→方向"，如何设计研究？
→ 关键点：先登记→机制→预注册（冻结阈值/特征/样本切分）→再算；禁看结果编理论。

**Task 8（设计缺陷）**：某研究把 hod_sin/cos 时间编码放进状态聚类，状态结果有何问题？
→ 关键点：日历伪状态，非市场能量状态；特征选择定义了状态语义。

**Task 9（攻击"看似正确"结论）**：OpenClaw 说"XAUUSD 无方向 gross edge"。这句话有什么危险？
→ 关键点：范围限定丢失风险；严格应限定"FXTM 2026 单窗、冻结 27 探测器、测试空间内"，不得泛化到全域/跨 feed/≤1m。

**Task 10（最值得研究的未知）**：当前最该解决的数据缺口/未知是什么？
→ 关键点：DUKA tick（KD-U01/D2）解锁 ≤1m 方向族跨 feed 终审；诚实指出"不知道"的部分。

---

## 3. 测速维度（§15，逐档实测）

first-token latency / tok/s @ 4K / 8K / 16K / 32K / 64K；RAM peak；VRAM peak；sustained stability。
> 诚实记录：若本机只能稳定跑小 context，如实写，不伪造。

---

## 4. 冻结结论：如何判定最终 READY

- 本地模型在三核心维度（Statistical/Research auditing/Adversarial）任一 < 2.0 → **NOT READY 作 Primary**。
- 即便通过，还需 64K 真实可用 + 速度可用 + 稳定 → 否则仍 PARTIALLY / NOT READY。
- 与云端对比：若本地在 quant 核心任务上系统落后，诚实记录差距，不美化。
