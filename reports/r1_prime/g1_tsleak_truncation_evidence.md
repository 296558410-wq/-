# G1 TS-LEAK / TRUNCATION EVIDENCE（R1' · 2026-09-05）

> 裁决 #3/#4 硬检查：adaptive 更新严格 trailing-only；未来截断重算不得改变历史 decision-time
> state/decision/sizing。实现：research/r1prime/features.py · evaluate.py。

## 1. Trailing-only 构造（代码级）
- vol_f：EWM(r²).**shift(1)** × √8760 → bar b 只用 ≤ b−1 信息（与 Phase 5 相同，更严）。
- 滚动分位（q70/q85/q90/q33/q66/q95）：rolling(500, min_obs=300).quantile(q).**shift(1)** →
  阈值只用 ≤ b−1；信号（G/A_gate/vf_high）在 bar b 用 ≤ b−1 阈值与 ≤ b 状态比较，日快照取当日
  最后一根 bar → 决策日 t 全部输入 ≤ t 收盘。
- 日决策 μ：state.mu[t] 于 t 收盘决定，经 shift(1) 只作用于 t+1 的 bar（evaluate.mu_per_bar）。
- 最小样本不足（<300 观测）→ 阈值为 NaN → 信号 NaN → 当日无状态迁移（缺失行为冻结）。
- ADP-C 目标档：tier 由**前一日**收盘 rv 快照决定（shift(1)），当日恒定。

## 2. E 标签隔离
E/E2 标签仅存在于评估层（N1 测量）；features/machine/evaluate **不含任何标签计算或引用**（代码级
隔离；测试断言机器模块不 import 标签函数）。E 确认分量（未来 1–2 日）只用于事后 N1 命中率，永不进入
决策路径（宪章 §10 / 裁决 #7）。

## 3. 未来截断重算证据
方法：FXTM H1 全序列 vs 在 UTC 日 120 处截断的子序列，分别计算全部特征与日快照，比较截断点前所有
公共日的 8 个关键量（G / A_gate / vf_high / rv / vf / act / adpc_target / vf_up）。

结果（g1_evidence.json truncation）：
- 公共日：**121**
- max |abs diff|：**0.0**（8 列全部逐位一致）

→ 截断未来数据不改变任何历史 decision-time 状态；由构造保证（仅 ≤t 输入），并由重算实证。

## 4. 附带验证
- 引擎腿（μ=1）日收益 ≡ Phase 5 日序列（max diff 0.0，双窗）→ 时移/成本语义与基线逐位一致
  （无"隐藏提前量"空间：若存在 lookahead，μ=1 的引擎不可能与 Phase 5 完全相等）。
- 全库 89/89 测试通过（含 truncation invariance 单测）。
