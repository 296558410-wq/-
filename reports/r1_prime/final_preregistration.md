# R1' FINAL PREREGISTRATION（reports 封面/镜像）

> 规范权威文件：`research/registry/R1'_FINAL_PREREGISTRATION.md`（冻结版，本页为镜像封面）。
> 状态：FROZEN-PENDING-GATE（2026-09-05）。定位：RISK DECISION / ADAPTIVE DECISION LAYER（非方向 Alpha）。

## 一句话
用 trailing-only 的 volatility/activity 信息提高 做不做/何时降险/做多少 三类风险决策的质量，
把机会成本入账后检验净经济价值（N1 事前可识别性 + N2 决策经济学 + C 自适应缩放的增量）。

## 冻结要点（详见权威文件）
- 数据：FXTM H1 v001（239 日，D/V/OOS=143/48/48）· DUKA H1 v001（159 日，一次性跨期）
- 状态机：FULL/REDUCED/STOPPED 整体冻结（ρ=0.5、滞后 2–3 日、kill-switch、B>A>C）
- 基线：AT / NT(仅 benchmark) / FR / FVT(Phase 5 复刻+对拍验收) / ADP-A/B/C
- 判据：12 维度量；day-cluster CI95 主判据；FDR 每腿独立；暴露下限 0.30/40%；1×成本核心、2×3× fragility
- 标签：E q95(252 交易日) 不变；双 feed 现为 DATA GAP → N1 挂数据前置条件 D1/D2；E2(DD) 可算
- Adaptive：threshold=f(trailing state)；更新机制冻结；STATIC 配对对照；禁 OOS 反设计
- 失败处理：REJECT / REDUNDANT / EDGE UNCERTAIN / INVALID(→V2)；允许 A/B/C 部分成功

## 阶段报告链（r1_prime/）
final_preregistration.md（本页）→ gate_report.md → discovery_report.md → validation_report.md →
oos_report.md → cross_period_report.md → cross_feed_report.md → execution_cost_report.md →
adversarial_report.md → final_judgment.md → research_decision_memo.md
