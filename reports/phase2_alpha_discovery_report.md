# AIQuant Phase 2 — Real XAUUSD Data & Alpha Discovery 报告

> 生成：2026-09-04 20:15 (Asia/Shanghai) · git: c1d84d3 + round1 提交
> 数据源：FXTM MT5 **Live 账户只读历史**（未做任何账户/交易操作）· MetaTrader5 官方包 5.0.6162

## 0. 本轮漏斗总览（第一轮真实数据研究）

| 阶段 | 数量 |
|---|---|
| 预登记并冻结 hypotheses | 69（10 families） |
| 实际检验 | 69 |
| raw significant (p<0.05) | 39 |
| **BH-FDR significant** | 37 |
| 转规则信号做成本压力 | 21（方向类） |
| 净成本 3x 仍正 | 2 |
| 子段稳健 (≥3/4 正) 且全门槛通过 | **0** |
| Alpha Registry 状态 | EDGE_UNCERTAIN 25 · REJECTED 13 · **SUPPORTED 0** |

## 1–4. 数据接入与质量（Q1-3 答案）

- **Q1 QC 通过**：三个周期全部 gate_passed（UTC 归一、单调、0 重复、0 缺失、OHLC 0 违例、spread 全正）
- **Q2 覆盖**：M1 2026-05-26→09-04（服务器保留上限 ~100k 根）；M5/H1 2025-12-01→09-04（FXTM Live 保留策略，M1 仅 ~3.4 个月——已如实记录为数据限制）
- **Q3 数据量**：M1 **100,000** 行 · M5 53,626 · H1 4,505
- 注册：`data_registry/XAUUSD_{M1,M5,H1}_MT5-FXTM-Live_20260904_v001`（sha256 + 全元数据）
- 时区：服务器 UTC+3（实测 last-bar 比对 + 周日 22:00 UTC 开盘吻合）→ 已转 UTC
- **已知数据特征**：每日 22:00 UTC 起 71 分钟固定休市（59 次观测）；周末休市 49.2h（周五 21:00→周日 22:00 UTC）；历史不含 tick bid/ask（MT5 API 仅 bar + spread_points）——如实记录

## 5. Baseline market characteristics（Q4，详见 reports/xauusd_baseline.md）

- M1：σ=4.0bp/min；**ac1=−0.025（1 分钟均值回复）**；**ac(|r|)1=0.22（强波动聚集）**；VR(10)≈0.97
- skew 2.1 / kurt 103（右尾跳跃）；spread 均值 $0.159（≈0.37bp）
- 时段：Asia 最静(3.8bp)、London/NY overlap 最活跃(5.7bp)；日内峰值 12–14:00 UTC ✓
- session 平均漂移：Asia −0.24bp/h · London +0.39 · NY −2.9 · overlap +1.9（3.4 个月样本，记录不作结论）
- M5/H1 同构（详见报告）

## 6–7. Feature/无前视

- features/xauusd 库 31 特征（price/momentum/trend/vol/MR/time/market-structure）+ 5 交互派生 + H1 跨周期 3 态
- **截断重算测试（真实数据 6 随机探针，31 特征全等）→ PASS**
- 交互派生（H7/H8/H9）与 H1-asof（H10）同样经属性验证

## 8–11. Hypotheses 与信息面（Q5-11 答案）

预登记 69 条（10 family，参数冻结于 `alpha_engine/hypothesis_registry.json`，禁改）。**先信息后策略**：
- 最强信息：**H4 波动率家族**（vol→future_vol IC 0.13–0.62，BH 全过，WF 5/5）——波动聚集是真实 XAUUSD 最硬的统计事实
- 收益预测类：IC 0.01–0.03（mom20/60 正、zscore/dist 正但弱、breakout 负）；**H10 跨周期在修复泄漏后仅 vol_ratio 保留弱真信息**
- 大样本陷阱如实记录：OOS n≈40k → IC 0.01 也可 p<1e-4；**显著性≠经济性**——故用成本压力+子段做经济门槛（Q6-9 数字见上表）

## 12–14. 淘汰结果（Q12-14）

- **REJECTED 13**：多为符号策略在 1x 成本即亏（H1 短动量、H3 突破、H7/H9 交互弱项）
- **EDGE_UNCERTAIN 25**：IC 显著但经济门槛未全过——典型如 dist_ema_60→60m（1x Sharpe 2.68 → **3x 成本 −0.50**，成本敏感）；sma_dist_60→240m（3x 仍 1.48 但子段 2/4 正）
- **SUPPORTED：0**。在 3.4 个月 M1 样本 + 当前协议下，没有任何候选同时通过 OOS+FDR+WF+成本 3x+子段 4/5 门槛 → **如实报告 0 candidates（符合 §22 原则）**

## 15–16. GPU 实际计算（Q15-16）

- 本轮 69×800 次置换 IC 检验 + 随机 baseline 20×500 → **GPU（分块 torch，A2000）**；benchmark 已实测 bootstrap 3–4x / permutation 5–6x / MC 6.5x
- 全轮 224s（含 CPU 侧 CI/WF/成本）；随机 baseline 20 特征 5.7s（GPU）——若无 GPU 纯 CPU 预计 ~15–25 分钟

## 17–18. 泄漏与框架 bug（Q17-18，本日自查记录）

1. **H10 跨周期 lookahead（已修复）**：H1 asof 映射未做 1h 收盘延迟 → h1_mom_4 IC 虚高 0.24；延迟修复后 −0.006。**这是截断测试抓不到的类别（跨周期状态映射）——已把"跨周期特征须按上层周期收盘时刻延迟"写入 generator 注释**
2. cost stress 索引错配（特征 RangeIndex vs close DatetimeIndex → 0 交易）→ 修复
3. 策略未按 holding period 建仓（每 bar 翻转 vs 登记 240m）→ 修复为每 holding 根 bar 更新
4. bootstrap CI 曾算全样本（与 OOS 不一致）→ 改为 OOS 同段
5. 7 条 H10 曾因索引类型被静默排除（n_iter=0 过滤）→ reset_index 修复，现 69/69 检验

## 19. Baselines（对照，Q4 附）

| baseline | net | Sharpe |
|---|---|---|
| Random（20 特征同漏斗） | 0/20 显著，median p=0.52 | —（null 正常 ✅） |
| Buy/Hold（同期） | −1.6% | −0.14 |
| Momentum naive（mom60 逐 bar） | −49% | −12.1（成本绞杀） |
| MeanRev naive（z60 逐 bar） | −59% | −15.8 |

候选最优（dist_ema_60/60m）1x Sharpe 2.68 显著优于 B/H 与 naive 规则 → 但成本敏感，未过全门槛。

## 20. 下一阶段（Q19-20 建议）

1. **数据深度**：M1 仅 3.4 个月是最大短板——申请 FXTM 历史更深的数据源（demo 服务器或换经纪商/自建收集），目标 ≥2 年 M1
2. **成本模型细化**：用 MT5 实时 spread 序列校准；测试限价/挂单执行以避开逐 bar 翻转成本
3. 重点方向（按本轮证据）：H4 波动率信息（vol forecast 而非方向）、**低换手趋势-回复混合**（sma_dist 240m 类，成本 3x 存活者优先扩展 lookback/holding 网格）、session 条件波动
4. 框架：把 EDGE 候选升级为 TESTING 状态 → 下一轮独立数据（新月份滚动）复验；ML 特征（树模型 IC）作为 H11+ 需另轮预登记
5. 基线对照入库：每轮自动附 random/BH/momentum/MR 四条

## 附：纪律核对

全程只读历史（copy_rates_*），零交易函数调用；无实盘/EA/自动单；0 candidates 如实接受；所有规格冻结于 registry；数据注册带 sha256；真实行情未入 git（data_registry/ 已 ignore）。
