# OPENCLAW HANDOFF（HERMES-12 数据解锁提交）

> 生成：2026-09-05 · 找到真实数据入口，改变 OBSERVABILITY/DATA 状态。

---

## TOP DATA UNLOCKS（按研究问题价值，非数据量）

### 1. FRED GVZCLS —— 黄金 IV 时间序列（2008+，日频，免费）★ 最高
- **UNLOCKS**：黄金隐含波动率 regime → CL-11（VRP）+ R1 的 vol-regime 状态变量。
- **正确分类**：EXISTS✓ ACCESSIBLE✓ AUTOMATABLE✓（FRED API）RESEARCH_USABLE✓
- **诚实边界**：GLD IV 日收盘，非完整期权曲面；proxy 非 XAUUSD 直接但合理。
- **OPENCLAW_ACTION**：DATA_ACQUIRE（FRED 免费 key 拉 2008-2026）

### 2. Databento CME GC MDP3 —— 机构级黄金期货 tick
- **UNLOCKS**：COMEX 期货微观结构（此前 KD-U05 缺）。
- **诚实边界**：tick 历史 2022+；$125 额度；需工程。
- **OPENCLAW_ACTION**：DATA_ACQUIRE（评估额度覆盖）

### 3. DUKA tick —— 诊断修正（非存在性缺口）
- **UNLOCKS**：KD-U01 ≤1m 方向族终审。
- **诊断**：瓶颈 = TOOL_LIMIT（慢速 HTTP 下载），非 NOT_EXISTING/NOT_PUBLIC。
- **OPENCLAW_ACTION**：REVIEW（dukascopy-node 批量抓取替代慢速 HTTP）

## 对 OpenClaw Edge Map 的影响

- **options/IV 从 DATA_GAP → 部分 UNLOCKED**（IV 时间序列可及；曲面仍缺）。
- **COMEX/futures 从 DATA_GAP → 部分 UNLOCKED**（Databento）。
- **≤1m tick 仍是真缺口，但性质是工程非存在**。
- **signed flow / spot L2 仍 CONFIRMED INACCESSIBLE**。

## 诚实声明

本轮未编造任何数据源。5 个登记源全部经工具验证（HTTP 200 或真实数据）。区分了
EXISTS/ACCESSIBLE/AUTOMATABLE/RESEARCH_USABLE 四状态。最大的价值不是"找到很多数据网站"，
而是：**证明 OpenClaw 标的 options-IV DATA_GAP 是我过度概括——IV 时间序列公开免费可得。**

## 下一轮建议（若有）

验证 GVZ 实际数据质量 + 评估 Databento GC 额度的研究覆盖（这需要实际拉数据，属 Research Engine /
OpenClaw 领域，非我情报层）。
