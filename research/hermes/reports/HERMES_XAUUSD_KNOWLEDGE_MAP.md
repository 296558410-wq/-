# HERMES XAUUSD KNOWLEDGE MAP（独立第二意见版）

> 生成：2026-09-05 · 作者：Hermes Agent（独立阅读 Phase 1–9A + R1' 全部报告/注册表后产出）
> 定位：**不是** OpenClaw 的 `knowledge_map.yaml` 的复制。是 Hermes 独立阅读同一批原始报告后，
> 用自己的判定词汇重新组织的知识地图，用于交叉核对（第二意见）。
> 权威源（OpenClaw 第一意见）：`research/registry/hypothesis_registry.yaml`（F-R1..F-R17 冻结）、
> `research/registry/knowledge_map.yaml`（CLOSED/OPEN/UNKNOWN）、`historical_phase_digest.md`。
> 范围纪律：**所有结论严格限定在"FXTM 2026 + DUKA 2023-24、M1+ 层（及 tick 23 日窗）、已冻结
> 协议与搜索空间"内**。不向 XAUUSD 全域或其它 feed/尺度外推。

---

## 0. 一句话总状态

方向层：**NO FEASIBLE ALPHA IN TESTED SEARCH SPACE**（两期双源 0 SUPPORTED + Phase 9 失衡族
27/27 探测器零候选）。信息层：**vol/activity/spread 波动信息跨期跨源稳健成立（但非方向）**。
风险/执行层：**R1' 日级自适应降险已被否定**；当前 **STOP**，被 DUKA tick 数据缺口阻塞。

---

## 1. 我们已经证明了什么（PROVEN，E4–E5 级，跨期+跨源复现）

| # | 结论 | 证据强度 | 关键数字 |
|---|---|---|---|
| P1 | **波动率聚类是 XAUUSD 最硬的信息**（activity→未来波动） | E5 双源双期 | activity→vol 非重叠 IC **0.60–0.89**；Phase 3 vol 家族 IC 复现且更强（vol_30 0.57→0.87） |
| P2 | **spread→未来波动强负相关，且跨源一致** | E5 双源 | DUKA −0.55~−0.59、FXTM −0.22~−0.29，FDR 全过 |
| P3 | **宏观日程（非开盘时刻本身）驱动活动簇聚** | E4 双窗 | 12–15 UTC 压力态 RR 2.93/2.82 同形；伦敦开盘 RR 仅 0.24–0.67（反证） |
| P4 | **引擎本身可信**（能检测注入结构、拒绝无结构数据） | Phase 1 已知答案实验 | 随机游走 REJECTED、人为趋势/波动冲击 SUPPORTED；20 随机特征 OOS 显著 0/20 |
| P5 | **固定点差 feed（FXTM）上无可择时空间**；可变价差 feed（DUKA）有真实但薄的 execution alpha | E4 | DUKA spread 可预测 IC 0.85–0.99 → OOS 节省 0.041bp/笔 t=11.7 |

> 这些是"能站住的"。注意 P1–P3 全部是**非方向**信息——它们预测的是"未来会波动/活跃"，不是"价格往哪走"。

---

## 2. 什么只是相关（CORRELATION，非因果，不可当机制）

| 观察 | 为什么只是相关 |
|---|---|
| spread 与未来波动负相关 | Phase 6/7 判定：**活跃度状态的两面（同因）**，不是"点差导致波动"。无外生工具变量 → 只报观测顺序，不报因果。 |
| 状态转换前 activity 先上升（tick lead-lag n=514） | **描述性排序**（temporal precedence）。点差滞后放宽 = 反应性流动性，是波动"结果"非"前导"。 |
| session/小时方向漂移（Asia 负、London 正） | pooling 抵消反号 session 效应制造假象；非重叠 OOS 后不显著。 |

> 纪律（继承 Phase 6/7）：**temporal precedence ≠ causality**。无工具变量时，一切"先发生→后发生"都停在"伴随/顺序"层。

---

## 3. 什么只是描述性（DESCRIPTIVE，无增量预测信息）

| 项 | 结论 |
|---|---|
| 蜡烛 body/close_pos 描述趋势 | 稳定但弱（IC 0.09–0.14），增量 ΔIC≤0 → **DESCRIPTIVE_ONLY**（F-R16） |
| 蜡烛形态×趋势条件表 | 上下文条件成立（偏移 ≤2–3bp），但不足以支撑独立方向信息主张 |
| Phase 6 GMM 市场状态 | 状态存在且持续 3–12 分钟、fwd_vol 单调，但 **fwd_ret≈0**（状态携带波动信息、无方向信息） |
| Phase 7 tick lead-lag 排序 | 描述性证据，directional_use REJECTED |

---

## 4. 什么已经 REJECTED（明确否定，禁止换名重做）

按 hypothesis_registry F-R1..F-R17（冻结），方向族**全面 REJECTED**：

| F-R | 方向 | 为何拒绝 |
|---|---|---|
| F-R1/F-R17 | 无条件动量（15m–240m） | 两期 0 SUPPORTED；符号策略 1x 成本即亏；跨期反号 |
| F-R2 | 无条件均值回复 | 成本后无正期望；样本内 EDGE 跨期消失 |
| F-R3 | 突破延续 | 两期 0 SUPPORTED |
| F-R5 | 趋势 regime 方向 | 跨期未确认，regime 依赖 |
| F-R6 | session/小时条件方向 | 非重叠 OOS 不显著；重叠噪声伪影 |
| F-R7/8/9/10 | 交互方向（vol×mom / trend×vol / 压缩动量 / 多周期） | 两期 0 SUPPORTED；压缩方向 15–240m 已否定 |
| F-R11 | ≥5m/M1 聚合微观方向 | 重叠标签 p=0.0000 假象，非重叠 p≥0.096；日 t <1.4 |
| F-R13 | 状态方向 | fwd_ret≈0，三窗口 OOS 不显著 |
| F-R16 | 蜡烛增量预测 | ΔIC=−0.0047 CI 含 0 |
| KD-C11 | P1–P7 失衡方向族（tick+M1，27/27） | 27/27 零候选；11 REJECT + 16 EDGE UNCERTAIN |

> **重要区分**（人工裁决 #2 已定）：KD-C11 族级 = `CLOSED_FOR_CURRENT_SEARCH`（治理关闭），
> **不是** REJECTED；探测器级才拆分 11 REJECT / 16 EDGE UNCERTAIN。这两个层级不得混淆。

---

## 5. 什么只是 EDGE UNCERTAIN（样本内边缘，跨期未确认，禁重做）

- **25 个 legacy EDGE**（Phase 2 样本内 IC 显著但经济门槛未全过）→ 全部跨期未确认 → `EDGE_UNCERTAIN_LEGACY`（F-R17）。
- **Phase 9 的 16 个探测器** → EDGE UNCERTAIN（INSUFFICIENT_N / 零事件）：n<300 或冻结阈值在 FXTM 数据上结构性不可达（P5 压缩自限、P7 |P|≥0.5 于 ≥30s 窗不可达、P6 联合条件近不可达）。
- **R1'-A Trade/Wait** → `EDGE_UNCERTAIN / FEED-LIMITED`：FXTM 固定点差 + A_gate 饱和 → 结果不可归因，主试场 DUKA 未完成。

> EDGE UNCERTAIN ≠ REJECTED。它是"证据等级限制"，不是"证伪"。但也不得当作"有希望"去推进——重开需差异化+预注册。

---

## 6. 什么是 SUPPORTED NON-DIRECTIONAL（成立但禁止当方向信号）

| F-R | 内容 | 允许用途 |
|---|---|---|
| F-R4 | activity→vol / spread→vol | 波动/流动性择时信息 → 只能进 **RISK/EXECUTION** 层 |
| F-R12 | spread 择时 execution alpha + vol-target 条件 RISK_ALPHA | 执行层；regime 触发器条件性使用 |
| F-R14 | 状态转换预测（rvol_pct AUC 0.60） | 只携带 vol 信息，无方向信息 |
| F-R15 | 宏观日程时间簇聚 | 信息/时机层事实，无方向主张 |

> **红线**：这些信息**永远不得直接当方向信号**。违反 = REDUNDANT_WITH_EXISTING_RESEARCH，自动 REJECT。

---

## 7. 什么仍然 OPEN（值得继续，但需预注册）

| 方向 | 优先级 | 备注 |
|---|---|---|
| R1 adaptive risk edge（E5 的 adaptive 形式） | 高 | R1' 已试日级版被否 → 未来只能是"形态条件化"或亚日/事件时间门控，非无条件日级 gate |
| Execution 层（DUKA 可变价差状态感知执行） | 中 | 依赖 DUKA M1（已入库）+ 新执行模拟协议 |
| 事件/日程窗 × 微观机制条件化 | 中 | Phase 7 结构 × vol 状态，先描述后预注册 |
| 状态依赖持期 / vol-normalized horizon | 中 | 依附 R1 产出 |
| 新特征合成（推进效率/冲击恢复速度/流动性反应延迟） | 低 | 需机制论证 + 预注册 |

---

## 8. 哪些方向已经重复研究过很多次（redundancy 警示）

- **方向动量/均值回复/突破**：Phase 2 首次 → Phase 3 跨期复验 → Phase 9 P1–P7 又在 10s–15m 层补测 → 全部死。**这是同一个"无条件方向"问题被换了三次尺度/名称追问**，答案一致：无。
- **session 方向**：Phase 2 H6 → Phase 4 session 规则 → Phase 6 假设#5，三次都死于非重叠 OOS。
- **vol/activity 当方向**：Phase 2 H4 → Phase 6 状态方向 → Phase 9 P6，三次都只得到"非方向信息"结论。

> 教训：registry 的 `required_differentiation`（尺度层补测 + 嵌套检验 + 非重叠协议）正是为堵这个洞——**换名不构成差异化**。

---

## 9. 失败分类学（哪些失败属于哪一类）

### 9a. 统计失败（方法错，结论跟着错，可修复）
- 重叠标签伪显著性（Phase 4：n≈9000 重叠 p=0.0000 → n≈140–690 非重叠 p=0.10–0.80）→ 已修（Phase 5 `overlap.py`）。
- 大样本功效陷阱（Phase 2：n≈40k 下 IC 0.01 → p<1e-4，显著性≠经济性）。
- 显著性跑净收益的口径 bug（Phase 1：成本拖累被误判为显著负 alpha）→ 已修。
- bootstrap CI 算全样本（Phase 2）→ 已修。

### 9b. 数据问题（样本/feed 限制，非机制否定）
- FXTM M1 仅 3.4 个月 / 69 交易日（MT5 保留上限）→ 目标 ≥2 年未达成。
- FXTM tick 仅 23 独立日 → 日级门槛 ≥60/130 无法满足。
- DUKA tick **未下载** → 跨 feed 最终裁定、10s–30s 跨期、maker/执行层全部阻塞。
- FXTM 固定点差 → spread 动态/择时/signed flow 无空间。
- 无 L2 深度/队列、无参与者身份、无新闻 wire 时间戳。

### 9c. 机制不存在（在测试空间内确实没有）
- 无条件方向动量/MR/突破/状态方向：两期双源 0 SUPPORTED → **在 M1+ 层、15–240m 持期、当前成本下，没有无条件方向 alpha**。
- 蜡烛增量预测：ΔIC 显著为负（样本内过拟合侵蚀 OOS）。

### 9d. 执行问题（不是信号不存在，是经济空间太薄/实现未竟）
- 方向信号净 1–10bp/笔 vs 成本 0.5–2.4bp 单边 → 空间极薄。
- tick 级执行模拟器（maker/taker/fill 概率/排队/adverse-selection）**未完成**（Phase 5 预留）。
- 自适应 vol-target 的 regime 触发器**未做**。

---

## 10. 当前 DATA GAP（阻塞项，非失败）

| 编号 | 缺口 | 阻塞什么 | 优先级 |
|---|---|---|---|
| D2 / KD-U01 | **DUKA tick 下载**（130 日独立窗） | ≤1m 方向族跨 feed 最终裁定；A-DUKA 主试场；spread 动态/maker/执行层；N1 事前识别（252 日同 feed 标签历史） | **最高** |
| KD-U02 | 事件日历数据 | 宏观日程因果研究（trigger vs amplifier） | 中 |
| KD-U05 | 跨资产数据（DXY/收益率/COMEX） | 跨资产 lead-lag | 中低 |
| KD-U06 | L2 深度/队列 | maker edge | 不可观测，NOT TESTABLE |
| KD-U07 | 真实 taker 流逆向选择成本 | 执行可行性 | 需 queue/flow 数据 |

---

## 11. 我对 OpenClaw 结论的独立复核（第二意见摘要）

**同意（SUPPORTED BY INDEPENDENT REVIEW）**：
- 方向层 NO_FEASIBLE_ALPHA 的判定，证据链完整、跨期跨源、方法资产（overlap.py 等）已回验。
- E5 级 vol/activity 信息为"非方向"的定性，与我的独立阅读一致。
- 状态变量 vs 因果（spread→vol）的谨慎定性正确。
- KD-C11 族级 vs 探测器级的拆分处理，严谨且必要。

**我要额外强调的风险（非反驳，是放大）**：
1. **"无 gross edge"的表述极容易被未来会话误读为"XAUUSD 无方向 alpha"**。OpenClaw 已多处加了范围限定，但范围限定散落在多份文件的脚注里，未来 agent 若不读全文只读结论句，会漏掉限定。建议：任何引用结论处强制带 scope 标签。
2. **R1' B-N2 的"机会成本 > 保护"结论是 FXTM 单 feed 单窗**，它很强，但它的强结论（"日级 gate 净值为负"）与 DUKA 可变价差 feed 上是否成立，是**两个不同问题**——目前被 DUKA tick 缺口阻塞，容易被误当成"已全面否定"。OpenClaw 已标注，我再次确认此边界关键。
3. **重叠标签/大样本陷阱这两个"假阳性制造机"在早期阶段连续制造了假象**，虽然都已修复，但它们是**系统性风险模式**，不是一次性 bug。任何未来 agent 接入新数据源时，这两个坑会以新形式重现（见失败库）。

---

## 12. 我还不能确定的地方（诚实标注 UNKNOWN）

- deepseek-v4-pro 长上下文/结构化提取的**量化上限**（未做基准——这是第二阶段模型能力评估要补的）。
- 上述所有结论在 **DUKA tick 补全后**是否仍成立（尤其 ≤1m 方向族）。
- XAUUSD 在 **10s–30s 层**是否真无失衡（当前 23 日窗无法裁决，属 EDGE UNCERTAIN 而非 REJECTED）。
