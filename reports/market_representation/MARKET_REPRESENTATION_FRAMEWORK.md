# MARKET REPRESENTATION FRAMEWORK（Phase 1 · 2026-09-05 · 冻结前规范）

> 任务：XAUUSD MARKET STATE REPRESENTATION（描述性）。本文件冻结评价框架、基线、探索纪律与
> 稳定性评分方案（结果查看前）。Registry：REPRESENTATION_REGISTRY.yaml（同目录）。
>
> 状态：**PHASE1_FROZEN_SEALED（2026-09-05 20:59 人工裁决 PASS）**。Phase 2 待人工再次明确放行；
> 当前无任何 candidate 被认定为"正确的市场状态表示"——Phase 1 建立的是寻找/验证框架，不是答案。

## 1. 概念区分（硬性）
Representation（市场状态的数学表达）≠ State（某时点状态值）≠ Label（事后命名）≠ Prediction ≠
Strategy。判定准则：候选若 ≈ 过去收益的确定性重编码（momentum/displacement/persistence 同族）→
不视为新表示（冗余检查 §6）。"能预测"不自动 = "正确表示"。

## 2. 评价框架（每候选必报 14 维）
1 Interpretability（可解释公式与语义）· 2 Stability（见 §3 评分）· 3 Portability（跨窗/feed）·
4 Compression（相对原始输入的降维比/信息增量）· 5 State separation（条件分布可分性，描述性）·
6 State persistence（自相关/占位时长）· 7 Transition coherence（状态变化的连续/连贯性）·
8 Cross-period consistency · 9 Cross-feed consistency · 10–13 Sensitivity（scale / price level /
volatility / session 的分层对照）· 14 Threshold-perturbation robustness（±扰动下语义稳定性）。

## 3. "稳定表示"定义与 STABILITY SCORE（权重冻结，结果前）
维度（在代表尺度上以标准化分位数计，0–1）：
A 分布稳定性 .15 · B 条件结构稳定性 .15 · C 状态占用稳定性 .10 · D 转移矩阵稳定性 .10 ·
E 状态持续稳定性 .10 · F 跨窗相似性 .15 · G 跨 feed 相似性 .15 · H regime 稳健性 .10。
SCORE = 加权和；判定阈值（冻结）：≥0.70 稳定 / 0.50–0.70 部分稳定 / <0.50 不稳定。
**经济损失叠加**（§8，不并入数值分，防伪精度）：由 Interpretability + 冗余检查 + Autopsy 覆盖度
定性判定；统计稳定但无语义 → 记录"稳定但空语义"，不评为好表示。

## 4. 基线（Representation Benchmark，冻结）
- B0 raw price features（各尺度原始收益/价格路径统计）
- B1 simple standardized（z-score / 对数变换后标准化）
- B2 volatility-normalized（÷ trailing σ / 相对 rvol）
- B3 path-normalized（效率 eff=|r|/path、path-relative 诸量）
- B4 multi-dimensional state vector（基线复合向量 [vol_f, rv, activity_pct, eff, …] 的稳定性/语义基准）
所有新候选 vs 上述基线族中最接近者比较（增量 = 稳定性/语义/冗余增益，非 PnL）。

## 5. 探索纪律（representation p-hacking 禁止；冻结）
- 候选族上限 12（Registry C1–C12）；每族冻结成员 ≤4（成员公式注册后不可因结果增删）。
- 聚类数上限 12；距离度量固定集 = {欧氏(标准化), 相关距离, DTW(仅事件时间序列)}；不做 1000 表示搜索。
- 一切变换/归一化在 Registry 登记；"最优表示"选择 = 禁止；允许的是：注册→计算→按冻结判据评价。
- 探索记录：Registry 每项 status ∈ NEW/TESTED/SUPPORTED_DESCRIPTIVELY/REDUNDANT/UNSTABLE/UNKNOWN。

## 6. 冗余检查（Representation Correlation / Redundancy Map）
- 同尺度标准化候选两两 |corr| ≥0.90 → 标记 REDUNDANT REPRESENTATION（合并族）。
- past-return-re-encoding 检验：候选 ≈ f(过去收益序列)（R² ≥0.95 可被滞后收益线性/简单函数复现）→
  标记 RE-ENCODING（不算新表示）。
- 族内冗余优先于族间（momentum/displacement/persistence 同信息族）。

## 7. 与既有研究的边界（防换名重复；§21）
| 既有 | 本任务为何不同 |
|---|---|
| Phase 6 GMM states（M1 窗内拟合、vol 维语义） | 本任务：可移植性优先、候选先于拟合、连续向量允许、不做"窗拟合簇→看收益"；Phase6 拟合模型不直接复用（泄漏纪律） |
| Phase 8 candles / Phase 9 detectors / Taxonomy / Portability | 均为阈值事件或日终事后形态；本任务研究**连续状态表示与变化动力学**（ΔState/velocity/transition），不是再定义事件标签 |
| R1'/risk-gate | 风险层决策研究已闭；本任务只回答"状态怎么表示"，不建 gate |
重研任何上述内容须先说明"为何旧结果不能回答该新问题"。

## 8. 数据审计（Phase 1；只读）
| 尺度 | FXTM（2026） | DUKA（2023-24） | 用途 |
|---|---|---|---|
| tick | 23 交易日 4.996M（2026-08-04→09-04） | 0（DATA GAP） | 事件时间/微观（KD-U01） |
| M1 | 100,000（2026-05-26→09-04） | 228,960（2023-09-01→2024-03-16） | 主分析尺度之一 |
| M5 | 53,626（2025-11-30→09-04） | 45,792（2023-09-01→2024-03-16） | 跨尺度 |
| H1 | 4,505（2025-11-30→09-04） | 3,816（2023-09-01→2024-03-16） | 跨尺度/regime 对照 |
- 跨尺度（同 feed 内 M1↔M5↔H1；FXTM tick↔M1 重叠子窗 2026-08/09）= **可测**。
- 严格 cross-period（同 feed 异期）/ cross-feed（同期异 feed）= **NOT TESTABLE**（注册数据双轴差异）→
  dual-role 对照 + 跨尺度为主轴；如实标注，不强行判定。
- 数据版本/时区/缺失/spread 口径沿用 data_registry dataset.json + Phase 9 audit 记录。

## 9. 阶段与 Gate
P1 本文档+Registry+审计（当前）→ P2 描述性探索（按 Registry 逐族计算+登记）→
P3 稳定性/可移植性（SCORE+扰动）→ P4 State Vector/Transition Graph → P5 跨尺度/dual-role →
P6 Adversarial（置换/扰动/去特征/随机基线/状态标签置换）→ P7 Final Gate（MEMO：§36 十问 +
CONTINUE/REDIRECT/STOP/DATA GAP + NEXT BEST RESEARCH QUESTION）。STOP 于 P7 后。
