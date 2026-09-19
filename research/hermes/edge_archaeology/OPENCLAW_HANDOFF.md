# OPENCLAW HANDOFF（HERMES-13 提交）

> 生成：2026-09-05 · 只提交一个真正值得的候选 + 诚实边界。

---

## 唯一值得正式审的候选：CAND-01

**"黄金期权 IV/VRP 的信息含量（非摩擦代理）" —— 检验'黄金期权信息不可用'这个假定**

- **WHY NOW**：黄金 VRP 预测贵金属收益（BIS wp619）+ 黄金 IV-收益正关系与股票不同（JFM 2014）+ Muravyev 借券费批评（针对股票）不能干净转嫁黄金。三证据交汇。
- **WHAT IS NEW**：首次把"黄金期权结构 ≠ 股票 → 摩擦代理批评不转移"作为可测假说提出。
- **WHAT DATA**：GVZ（FRED 免费 2008+，HERMES-12 已验证）+ 本地 activity→vol 已实现波动。
- **MINIMUM TEST**：GVZ 对 XAUUSD 未来已实现波动的增量预测（控 E5 activity→vol 后 ΔIC）；检查方向信息。
- **KILL CONDITION**：GVZ 增量 ΔIC≈0（控 E5 后）且无方向信息 → 假定"仅描述性"成立，关闭。
- **EXPECTED INFO GAIN**：高。通过则开辟黄金 vol-regime/IV 层；杀死则确认假定。
- **风险**：GVZ 是 GLD ETF IV proxy；月度 VRP 预测力 restricted to precious metals。

## 系统级洞察（给 OpenClaw 的战略提示）

**我们可能是"股票中心"思维的受害者。** 这套地图里好几个关键结论（期权=摩擦代理、vol-timing 成本归零、
IV=leverage）都是**股票市场**的规律，被我转嫁到了黄金/贵金属。但黄金是**需求驱动**的避险资产
（demand vol skew、无同构卖空约束）——这些股票规律**可能根本不适用**。

这不是"找到新 alpha"，是**指出我们推理的一个系统性盲区**。CAND-01 就是检验这个盲区的最小测试。

## 不提交的（诚实）

- commodity carry/term-structure 一堆 → REPACKAGING，不浪费 OpenClaw 时间。
- futures-lead-spot（Sehgal）→ REFINEMENT 非 NEW，且不可交易（同期发现份额）。
- 未找到 ≤1m 方向反证 → 仍 DATA_GAP（TOOL_LIMIT 非存在）。

## 底线

本轮产出 = 1 个真正的可测候选（CAND-01）+ 1 个系统级盲区提示（股票中心思维），
**不是** 10 个弱发现。是否符合"最大化信息增益、最小化模型调用"的目标。
