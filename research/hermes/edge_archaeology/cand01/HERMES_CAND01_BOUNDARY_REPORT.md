# HERMES CAND-01 BOUNDARY REPORT（边界审计）

> 生成：2026-09-05 · 审计"GVZ 是否在测正确的经济对象"。认知目的，非 alpha 搜索。
> 主问题：GVZ/GLD-options 信息对 spot XAUUSD 波动是否有超越本地已实现波动/activity 的增量证据？

---

## 0. 一句话结论

**GVZ 是 PARTIAL PROXY（CASE B），且带 CASE C（skew 维度 DATA_GAP）与 CASE D（VRP→returns 证据冲突）成分。**
GVZ 只承载黄金期权的 **ATM IV 水平**维度；而**最强**的黄金特定证据（LJP=看跌需求/skew → 收益）不在 GVZ 里。

---

## 1. 证据桥在哪一环停（核心）

```
黄金期权信息
  → 黄金期货期权（COMEX）：最强证据在此（LJP + VRP → 期货收益，OOS）
  → GLD 期权（GVZ，ATM IV）：水平维度可及，但 LJP/skew 维度抓不到
  → spot XAUUSD：经由 GLD/期货→spot 套利 proxy，间接
```

**桥分类**：
- 黄金期货期权(LJP/VRP) → 黄金期货收益：**STRONG**（SSRN 3074549，OOS）
- GLD 期权 → GLD：**DIRECT**（GVZ 就是 GLD 期权 IV）
- GLD 期权 → XAUUSD spot：**PARTIAL**（GLD≈spot 套利，但 US-hours + ETF 结构 proxy）
- COMEX 期权 → XAUUSD：**PARTIAL-STRONGER**（期货紧贴 spot，但仍是 proxy）

## 2. 黄金期权信息住哪（Q3 答案）

| 维度 | 证据 | GVZ 捕获? |
|---|---|---|
| LJP（左侧跳/看跌需求） | **最强预测器**（SSRN：LJP+VRP 预测期货收益，全 horizon OOS） | **否**（需 risk-neutral 左尾 = 曲面） |
| VRP | 冲突（BIS 支持 post-2008；JFM 综合否商品 OOS） | 部分（GVZ 是 IV 度量，可近似 IV-RV） |
| ATM IV 水平 | 弱-中 | 是（GVZ = ATM） |
| skew / term structure / 曲面形状 | GLD 当前 skew≈flat(-0.016)、term≈flat；事件近 IV repricing 需曲面 | 否 |

→ **结论：最强维度（LJP/skew）不在 GVZ。** GVZ 是 ATM 单点。

## 3. 时间尺度（Q5）：**错配**

- 文档化的黄金期权价值（LJP+VRP→收益）是 **1 个月–2 年**。
- CAND-01 测 **5/10/20 日**。
- → GVZ 日频测试是合法的"窄"问题（GVZ 对 5-20d 已实现波动的增量），**但不是**在测文档化的经济机制（月度 VRP/LJP）。
- 若日频测试是"GVZ-RV 是否预示 RV 追赶"（vol 均值回归），尚合理；但别把它说成在测 LJP/VRP 机制。

## 4. 机制审计（Q6）：黄金文献支持哪个机制

- **LJP 证据支持 Mechanism A（避险/对冲需求 → 期权溢价/skew → 未来收益）**：更多看跌保护需求（put demand）与更高未来黄金收益相关。
- 不是 Mechanism B（借券摩擦）——黄金无同构卖空约束。
- **Muravyev 转移（Q7）：INVALID/PARTIAL**。黄金 LJP 证据方向与股票相反（是需求非摩擦代理），黄金无短卖约束机制。用股票借券费批评降级黄金期权假设是**错误的跨市场转移**。

## 5. 矛盾（Q8/Q16）

**支持（3）**：
1. SSRN 3074549：黄金 LJP+VRP 预测期货收益，IS+OOS（E3）
2. BIS wp619：黄金 VRP 预测贵金属收益（post-2008，E3）
3. JFM 2014：黄金 IV-收益正关系（demand skew，区别于股票）（E3）

**矛盾/限制（3）**：
1. **JFM 综合 VRP 回顾：商品市场无 VRP 的 OOS 可预测性**（直接反驳 #2）
2. BIS 自限：仅 post-2008；MFIV 期限结构斜率对商品无效（仅贵金属）
3. GLD 当前 skew/term 平坦 → 此刻曲面结构少；gold 期权信息关系"弱于股票"

## 6. GVZ 充分性（Q9）：**PARTIAL PROXY**

- 若真信息在 skew/LJP/term/曲面形状 → GVZ（ATM 单点）**不能**捕获。
- GVZ 可承载：ATM IV 水平、粗 VRP（GVZ-RV）在日/月频的 vol 预测。
- GVZ 不能承载：LJP（左尾）、risk reversal、term structure、event-near repricing。
- **不否定 GVZ 实验，但严格定义其范围。**

## 7. 事件近信息（Q10）：**DATA_GAP / OPEN**

- 无证据表明事件近 IV repricing 对 XAUUSD 有信息（也未测）。
- 但 GVZ 日收盘会抹平日内事件 repricing → 若真信息在事件近，GVZ 抓不到。
- 状态：DATA_GAP（不声称 alpha）。

## 8. 直接 XAUUSD IV 数据（Q11）：EXISTS（付费）非免费

- SpiderRock 历史 vol surface（付费机构）、FX option surface vendors（Data In Harmony）、Zenodo precious-metal vol surface（免费但有限）。
- GVZ 是唯一**免费可自动**的黄金 IV 代理。付费 XAUUSD/曲面数据 = 存在但需评估是否值得（当前无曲面测试计划 → 暂不买）。

## 9. GC 期权 vs GLD 期权（Q12）

- GC（COMEX 期货期权）是"更强"的同一黄金 vol 过程观测（期货紧贴 spot，无 ETF 溢价/仅 US-hours 限制）。
- 但数据成本高（需 options 数据源），且当前无免费 GC options IV 时间序列。
- 若未来要测 LJP/skew 维度，GC 期权 > GLD 期权作为现货桥。

---

## 决策（Q14）

**CASE B（主）**：GVZ 含部分黄金 IV 信息（ATM/VRP 水平维度），但 miss skew/LJP/term/event 维度。
→ **继续 GVZ 作为有界 proxy 测试**，但：
  (a) 框定为"黄金 ATM-IV 水平对 XAUUSD 5-20d vol 的增量"，**不是**"黄金期权信息含量"（宽）。
  (b) GVZ 归零**不杀死**黄金期权假设（skew 维度未测）。
  (c) 记录 skew/LJP/term + 直接 XAUUSD OTC IV 为 **DATA_GAP**。

**CASE C 成分**：LJP（最强证据）在曲面 → 若目标是测"黄金期权信息有无"，GVZ 不够。

**CASE D 成分**：黄金 VRP→收益证据**冲突**（JFM 否商品 OOS）→ 该 claim 是 UNPROVEN/CONFLICTED，不得当成支持 CAND-01 的基础。

---

## 给 OpenClaw 的 9 问回答（见 OPENCLAW_HANDOFF.md）

核心：**PARTIALLY 在测正确对象。** GVZ 测的是一个真实的、但**窄**的对象（黄金 ATM-IV 的 vol 增量），
不是文档化最强的黄金期权信号（LJP/skew，月度，需曲面）。设计上应缩小 CAND-01 的声称范围。
