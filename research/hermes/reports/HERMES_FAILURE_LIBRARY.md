# HERMES FAILURE LIBRARY（失败库）

> 生成：2026-09-05 · 作者：Hermes Agent
> 用途：把 Phase 1–9A + R1' 研究历史中**真实发生过**的失败模式，系统化为可检索的失败库。
> 每条 = Failure → Why → How detected → How to prevent。目标：未来 agent 不再踩同一个坑。
> 来源：`historical_phase_digest.md`（§跨阶段教训）、各 Phase 报告 §泄漏修复/§自述。
> 状态标签：FIXED（已修复并回归测试）/ PATTERN（系统性风险模式，会在新场景重现）/ STRUCTURAL（数据/环境限制）。

---

## A. 泄漏与数据污染类（最危险，制造假阳性）

### FL-01 跨周期状态映射泄漏（lookahead）
- **Failure**：H10 跨周期特征在 asof 时刻未做上层周期收盘延迟，IC 虚高 0.24，修复后 −0.006。
- **Why**：下层 bar 的"当前时刻"已经包含了上层周期尚未收盘的信息 → 未来信息混入。
- **How detected**：自查 5 项泄漏时发现；**关键：截断重算测试抓不到此类泄漏**（因为截断重算只验证"同一时刻重算一致"，不验证"跨周期 asof 是否对齐"）。
- **How to prevent**：跨周期特征一律延迟到上层周期收盘后；跨周期泄漏单独设检查项（不只靠截断重算）。
- **Status**：FIXED（Phase 2 §17）

### FL-02 重叠标签伪显著性（overlap dependency）★ 最高危 PATTERN
- **Failure**：同一条 session 规则，n≈9000 重叠样本 p=0.0000；n≈140–690 非重叠样本 p=0.10–0.80。
- **Why**：时序标签强自相关，重叠样本被当成独立样本 → effective n 被严重高估 → 显著性虚高。
- **How detected**：Phase 4 显式做"重叠 vs 非重叠"对照后暴露。
- **How to prevent**：一切时序 IC/AUC 检验用非重叠/分块抽样，报告 effective n。Phase 5 已落地 `statistics/overlap.py`（non_overlap_entries / effective_n / ic_at_entries / block_permutation_p / block_bootstrap_ci），回归测试复现"重叠显著虚高→非重叠回落"。
- **Status**：FIXED + PATTERN（任何新数据源接入时必须重跑此对照）

### FL-03 大样本功效陷阱（insufficient scrutiny of p-values）
- **Failure**：n≈40k 下 IC 0.01 也可 p<1e-4 → "显著"但与经济价值无关。
- **Why**：大样本下统计功效极高，任何微小效应都"显著"；显著性被当成经济性。
- **How detected**：Phase 2 观察到 raw 39 / FDR 37 / SUPPORTED 0 的断层（统计显著大量、经济通过为零）。
- **How to prevent**：**显著性跑毛收益，经济性单独看净收益**；显著性门槛与正天数/经济门槛并存；"显著≠可交易"写进每个结论的默认提醒。
- **Status**：PATTERN

### FL-04 成本口径 bug（gross vs net）
- **Failure**：显著性检验跑在净收益上，成本拖累被误判为"显著负 alpha"。
- **Why**：净收益 = 毛收益 − 成本，把成本项混进显著性检验会污染方向判定。
- **How detected**：Phase 1 已知答案实验对不上预期 → 追溯到口径。
- **How to prevent**：显著性/方向判定跑**毛收益**；成本压力单独用净收益看；1x/2x/3x 成本分级（1x 可行性、2x/3x 脆弱性）。
- **Status**：FIXED（Phase 1）

### FL-05 mid-PnL 冒充可交易（theoretical mid-price illusion）
- **Failure**：用 mid 价计算 PnL，忽略真实 bid/ask + 点差 + 滑点 + 延迟，制造"看起来赚钱"的假象。
- **Why**：mid 价是理论价，不含任何交易摩擦；高频/短周期策略的实际成交价必然偏离 mid。
- **How detected**：Phase 9 冻结明确"禁止 mid PnL 宣布成功"。
- **How to prevent**：≤1m 候选必须 bid/ask + spread + latency + slippage + adverse selection + fill 假设模拟；只能理论回测则标 `THEORETICAL ONLY`。
- **Status**：PATTERN（结构性，永远要防）

---

## B. 统计方法论类

### FL-06 session 混杂（confounding / pooling 抵消）
- **Failure**：Asia imb→负、London/overlap imb→正，pooling 后互相抵消 → 掩盖真实（或制造假）效应。
- **Why**：不同 session 的机制/参与者不同，pooling 把它们当成同质样本。
- **How detected**：Phase 4 session 分层后暴露反号效应。
- **How to prevent**：session 只作**分层变量/条件基线**（B6），禁止单独作 alpha 源；报告必须分层，禁止跨 session 混合归因。
- **Status**：FIXED（F-R6 冻结为"仅分层允许"）

### FL-07 bootstrap CI 口径错误
- **Failure**：bootstrap CI 曾算全样本（而非按持有期/非重叠重采样）。
- **How detected**：Phase 2 自查。
- **How to prevent**：CI 与显著性用同一抽样协议（非重叠/分块/按持有期）。
- **Status**：FIXED（Phase 2）

### FL-08 索引错配 / 静默排除 / holding-period 错配
- **Failure**：成本压力索引错配（0 交易）；H10 索引类型错误致 7 条静默排除；策略未按 holding period 建仓。
- **Why**：数据对齐类 bug 通常**不报错、静默产生错误结果**——最危险的一类。
- **How detected**：Phase 2 自查 5 项泄漏时逐一核对。
- **How to prevent**：任何 join/对齐/重采样操作后做行数/索引/空值断言的冒烟测试；关键实验支持 TRUNCATED DATA RECOMPUTATION。
- **Status**：PATTERN

### FL-09 特征选择决定状态语义（calendar 伪状态）
- **Failure**：Phase 6 状态向量首版含 hod_sin/cos → 状态退化成"日历分段伪状态"，非市场能量状态。
- **Why**：把时间编码特征混入状态聚类，聚类结果会按日历而非市场结构分裂。
- **How detected**：去掉时间特征后状态语义剧变 → 意识到特征选择定义了状态含义。
- **How to prevent**：状态/聚类类特征避免直接编码日历时间；报告状态时声明特征向量的语义含义。
- **Status**：FIXED（Phase 6 教训）

---

## C. 因果与归因类

### FL-10 temporal precedence = causality（先后冒充因果）
- **Failure**：tick lead-lag 显示 activity 先升、spread 后放宽 → 曾被倾向解读为"点差/流动性前导波动"。
- **Why**：先发生≠导致；可能是共同因（活跃度状态）的先后表现。
- **How detected**：Phase 6/7 用"状态变量 vs 因果"框架重新审视：spread→vol 是活跃度状态两面（同因）。
- **How to prevent**：无外生工具变量时，只报观测顺序，不报因果；一切"X 领先 Y"结论默认加"temporal precedence，未证因果"。
- **Status**：PATTERN

### FL-11 事后窗口命名冒充事前状态（post-hoc regime naming）
- **Failure**：Phase 5 的"2026 不稳定期 / 2023-24 平滑期"是**窗口级事后命名**，曾被当作可用状态变量。
- **Why**：事后看到哪个窗口波动大，就给它起个名字当"regime 触发器"——这是看结果定标签。
- **How detected**：R1' 机制定义明确区分"事前可识别（trailing-only）vs 事后分类"。
- **How to prevent**：状态变量必须 trailing-only、决策时刻可算；任何"regime 标签"若不能在事前算出来，禁止当信号。
- **Status**：PATTERN（R1' B-N1 正是在测"事前可识别性"，被 D2 数据缺口阻塞）

### FL-12 样本内 EDGE 跨期翻转（regime overfitting）
- **Failure**：mom_20→15m 2026 期 +0.016 → 2023-24 期 −0.048；zscore_60 +0.012 → −0.042。25 个 EDGE 全部跨期未确认。
- **Why**：方向效应 regime 依赖（2026 趋势 vs 2023-24 震荡反号），单期样本内"发现"是 regime 过拟合。
- **How detected**：Phase 3 跨期复验（这是整个研究最重要的一道关卡）。
- **How to prevent**：**跨期复验是必经关卡**，单期候选最多 EDGE UNCERTAIN，不得宣称成立；方向符号必须两期一致。
- **Status**：STRUCTURAL（方向层本性的体现）

---

## D. 数据与环境类

### FL-13 feed 混淆（feed confusion）
- **Failure**：FXTM 固定点差（$0.15–0.16）vs DUKA 可变价差（水平切换 0.31↔0.70）→ 在 FXTM 上研究 spread 动态 = 无空间，结论不能跨 feed 推广。
- **Why**：不同 feed 的点差结构本质不同，却常被当成"同一个 XAUUSD"。
- **How detected**：Phase 5 显式对比两 feed 点差结构。
- **How to prevent**：**跨源比较一律在信息层（无成本）进行，成本压力仅同源内可比**；feed 结构差异写进每个结论的适用范围。
- **Status**：STRUCTURAL + PATTERN

### FL-14 样本深度不足（insufficient sample）
- **Failure**：FXTM M1 仅 3.4 个月、tick 仅 23 独立日 → 日级结论无法裁决 |IC|~0.1 的效应。
- **Why**：MT5 Live 保留上限（~100k M1 bar）；tick 历史不内置于 bar 历史。
- **How detected**：Phase 9 data audit 明确独立日门槛 ≥15/23、≥60/130。
- **How to prevent**：样本充分性在实验前评估；不足则明确标 `EDGE UNCERTAIN (INSUFFICIENT_N)` 而非 REJECT，也不得宣称发现。
- **Status**：STRUCTURAL（DUKA tick 补全前持续阻塞）

### FL-15 结构性零事件 / 阈值不可达
- **Failure**：P5 压缩自限全尺度 0 事件；P7 |P|≥0.5 在 ≥30s 窗不可达；P6 联合条件近不可达 → 16 个探测器"零事件"而非"证伪"。
- **Why**：冻结阈值基于先验设定，落到具体 feed 数据上可能结构性永远不触发。
- **How detected**：Phase 9 Discovery 观察到大量零事件/稀疏事件。
- **How to prevent**：区分"零事件（阈值不可达）"与"REJECT（有样本但 net≤0）"；零事件项标 EDGE UNCERTAIN，不得当 REJECT，也不得因此放宽阈值（放宽=post-hoc）。
- **Status**：PATTERN

---

## E. 治理与流程类

### FL-16 换名不构成差异化（redundant research）
- **Failure**：方向动量/MR/session 等问题被换三次尺度/名称追问（Phase 2→3→9），答案一致无。
- **Why**：缺乏冗余守卫，新探测器用新名字包装旧假设。
- **How detected**：Phase 9A 建立 `hypothesis_registry.yaml` 的 redundancy map（required_differentiation 前置过滤）。
- **How to prevent**：任何新候选注册时必须声明 historical_equivalents + required_differentiation（尺度层补测 + 嵌套检验 vs 历史同族最优 + 非重叠协议），否则 gate 不通过。
- **Status**：FIXED（Phase 9A 冻结守卫）

### FL-17 阈值/定义按 OOS 结果放宽（post-hoc threshold relaxation）
- **Failure**：倾向"放宽 qpressure 阈值 / 降低 P5 n_comp / 给负收益加反向条件"来救活零事件项。
- **Why**：看到结果再调参 = post-hoc，制造虚假显著。
- **How detected**：Phase 9 Gate §Adaptability Assessment 明确禁用清单。
- **How to prevent**：改阈值/定义只能经 registry V2 + Gate；"adaptive"若基于本轮结果设计 = post-hoc，禁用。
- **Status**：PATTERN

### FL-18 复杂度不产生价值（over-engineering）
- **Failure**：R1'-C 自适应三档缩放（mechanism 合理）在 FXTM 上无增量且差于固定 vol-target（vol 12.8% vs 10.5%，Sharpe 0.90 vs 1.13）。
- **Why**：参数变化/复杂度本身不产生 alpha；机制合理≠有增量。
- **How detected**：R1' C 腿三方比较（fixed risk vs fixed vol-target vs adaptive）。
- **How to prevent**：复杂方案必须证明相对简单基线的 OOS 增量 Δ；无增量则标 REDUNDANT，不标"新发现"。
- **Status**：FIXED（R1'-C → REDUNDANT → CLOSED）

---

## 总结：最需要反复提醒未来 agent 的 TOP 5

1. **重叠标签 / 大样本功效**（FL-02 + FL-03）——假阳性制造机，任何新数据源接入必复现。
2. **显著性跑毛收益、经济性看净收益、禁止 mid PnL**（FL-04 + FL-05）——成本纪律三件套。
3. **跨期复验是必经关卡**（FL-12）——单期 EDGE 一律不算数。
4. **temporal precedence ≠ causality**（FL-10）——先后不当因果。
5. **feed 结构决定可研究问题**（FL-13）——跨源只在信息层比较。
