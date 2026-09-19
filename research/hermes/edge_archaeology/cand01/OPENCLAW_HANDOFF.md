# OPENCLAW HANDOFF（CAND-01 边界审计提交）

> 生成：2026-09-05 · 回答边界审计要求的 9 个问题。

---

## 1. GVZ 能合法测什么
GVZ 能测：**黄金 ATM-IV 水平（及粗 VRP=GVZ−已实现）对 XAUUSD 未来 5–20 日已实现波动的增量**，
相对本地 activity→vol E5 模型。这是"黄金期权 IV 水平维度"的窄测试。

## 2. GVZ 不能测什么
GVZ **不能测**：LJP（左侧跳/看跌需求 = skew 维度，黄金期权最强的文档化预测器）、risk reversal、
term structure、曲面形状、event-near repricing。这些需要完整期权曲面（模型无关 risk-neutral 矩）。

## 3. CAND-01 的 5/10/20d 设计是否合理
**部分合理，但有错配**。文档化的黄金期权经济价值（LJP+VRP→收益）在**月度+** horizon；
5/10/20d 测的是不同的（日频 vol 增量）问题。若框定为"GVZ-RV 是否预示 RV 追赶"，日频合理；
但不能说 CAND-01 在测文档化的 LJP/VRP 机制。**建议缩小声称范围到"日频 vol 增量"**。

## 4. 黄金期权机制是否被支持
**冲突（CONFLICTED），非确立**。支持：黄金 LJP+VRP 预测期货收益（SSRN，OOS）+ 黄金 VRP 预测贵金属
（BIS post-2008）。反驳：JFM 综合回顾称商品无 VRP OOS 可预测。→ 机制"可能存在于 skew/左尾维度
（LJP）"，但"黄金 VRP→returns"作为基础 claim 是 UNPROVEN。

## 5. Muravyev 股票机制转移是否仍有效
**INVALID/PARTIAL TRANSFER**。Muravyev 的"IV 预测=借券费/短卖摩擦代理"针对**股票短卖约束**；
黄金无同构机制，LJP 证据方向与股票**相反**（避险需求）。用股票借券费批评降级黄金期权假设 = 错误转移。
→ HERMES-13 用它削弱黄金期权是过度；但黄金 VRP 自身证据仍冲突（见 #4）。

## 6. surface/skew/term structure 是否 material 盲点
**是 material 盲点**。最强黄金特定预测器（LJP）在曲面左尾，GVZ（ATM）抓不到。GLD 当前 skew/term
虽平坦（此刻结构少），但历史 skew 维度未测。→ 若目标测"黄金期权信息有无"，GVZ 不够（CASE C lean）。

## 7. GC 期权是否 material 改善可观测性
**是**（作为现货桥强于 GLD 期权：期货紧贴 spot，无 ETF/仅 US-hours 限制），但数据成本高、无免费历史。
当前无曲面测试计划 → 暂不采购；仅当要测 LJP/skew 维度才值得。

## 8. 是否进一步采购数据
**否（现在）**。当前 GVZ 免费测试先跑；若 GVZ 增量为正或要测 skew 维度，才评估付费曲面（SpiderRock 等）。
不因"理论可能存在"预先采购昂贵数据。

## 9. 单一最高信息增益实验
**用 GVZ（免费）测一个窄问题**：
```
GVZ_t − 已实现_vol_t（黄金 VRP proxy）对 XAUUSD 未来 5/10/20d 已实现波动的增量 ΔIC，
控 activity→vol E5 模型 + 已实现 vol 水平。
KILL：ΔIC≈0 → GVZ 无日频增量 → 关闭黄金 IV 水平维度。
（注：此测试只覆盖 ATM 水平维度；skew/LJP 维度是 DATA_GAP，本测试不裁定它）
```
这比"GVZ→vol"更精确（用 VRP 而非 IV 水平），且免费可自动（HERMES-12 已验证 GVZ/FRED）。

---

## 决策汇总
**CASE B（主）+ CASE C/D 成分**。GVZ 测的是一个真实的、窄的对象（黄金 ATM-IV 的日频 vol 增量）；
**不是**文档化最强的黄金期权信号（LJP/skew，月度，需曲面）。继续 GVZ 有界测试，但：
1. 缩小声称到"ATM 水平维度日频 vol 增量"；
2. 记录 skew/LJP/曲面/直接 XAUUSD IV = DATA_GAP（不裁定）；
3. 别用冲突的 BIS VRP→returns 当 CAND-01 基础；
4. Muravyev 转移对黄金无效——但黄金 VRP 自身仍冲突。
