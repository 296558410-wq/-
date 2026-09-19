# AIQuant Phase 3 — Autonomous Alpha Research 报告

> 生成：2026-09-04 22:10 (Asia/Shanghai) · Autonomous Alpha Research Agent 首轮自主执行
> git: 本阶段提交见文末；真实行情始终不入 git（data_registry/、staging_* 已 ignore）

## 执行摘要（自主研究路径）

本轮自主决策路径：**数据瓶颈优先** → 找到 Dukascopy HTTP 通道（此前被误判为不可达：
https 被墙但 http 可用，且月份路径需补零）→ 并行下载触发限速 → 转为礼貌单线程续传 →
先用已获得的 **2023-09→2024-03 连续窗口**（229,020 根 M1，mid 由 BID/ASK 蜡烛合成）
完成跨期复验与新信息层研究。Tick 层已完成解码验证与特征库，等待续传完成后接入。

## 1. 当前数据是否仍是主要瓶颈？
**是，但正在解决。** M1 深度已从 3.4 个月扩到 ~10 个月（FXTM 2026 窗口 + DUKA 2023-24 窗口），
DUKA 续传在后台以反限速速率补齐 2023-01→2026-08（~15h 预计，自动断点续传），
完成后将是 ~3.7 年 M1 + 可选 tick。Tick/bid-ask 已确认可获取（单小时 21,353 ticks，
价格 scale=1000，与 2024-01 金价吻合）。

## 2. 获得了哪些新数据？
| 数据集 | 覆盖 | 行数 | 状态 |
|---|---|---|---|
| XAUUSD_M1_Dukascopy-HTTP_v001 | 2023-09-01 → 2024-03-16 | 229,020 | ✅ 注册+QC |
| XAUUSD_M5/H1_Dukascopy-HTTP_v001 | 同上（派生） | 45,804 / 3,852 | ✅ 注册 |
| DUKA 补齐中（后台续传） | 目标 2023-01→2026-08 | — | ⏳ ~15h |
| Tick 试点 | 单小时解码验证 | 21,353/小时 | ✅ 格式验证（未全量） |

数据质量：QC 全过（0 重复/0 缺失/6 边界缺口）；DUKA spread 均值 $0.488（2023 金价 ~$2050 时
≈2.4bp）vs FXTM $0.159（≈0.5bp）——两个数据源价差结构不同，跨源比较一律在**信息层（无成本）**进行，
成本压力仅在同一源内可比。

## 3–4. Phase 2 Alpha 跨期复验（同一冻结 69 假设；2026 vs 2023-24）

**复现（两期 FDR 显著且方向一致）：**
- **H4 波动率家族：全部复现且更强**（未来波动 IC：vol_30 0.57→0.87、atr_14 0.62→0.89、
  rvol_60 0.54→0.89、vol_ratio 0.13-0.17→0.55-0.60）——波动聚集是跨期最硬的信息
- trend_str→未来波动（+）、h1_vol_ratio→未来波动（h15/h60 一致）、dist_lo→60m 收益
  （+0.018/+0.066）、hour→60m（弱，两期同号）

**被推翻/翻转（Phase 2 弱方向项不跨期）：**
- mom_20→15m：2026 +0.016 → 2023-24 **-0.048**（翻转）
- zscore_60→15m：2026 +0.012 → 2023-24 **-0.042**（翻转，2023-24 反而支持均值回复）
- h1_vol_ratio→240m 波动：2026 -0.097 → 2023-24 +0.457（翻转）

**结论**：Phase 2 的 EDGE 候选（dist_ema/sma_dist 等方向类）**在更长/不同时段上未被确认**；
方向类 IC 的符号在 2023-24（震荡市）与 2026 之间存在系统性差异 → 短周期方向效应是
**regime/时期依赖**的，不是稳定 Alpha。两期最终均 **0 SUPPORTED**。

## 5–8. 新信息层

**Spread 层（双源交叉，全新发现）**：
- **spread → 未来波动：强负相关且两源一致**（DUKA -0.55~-0.59@15-240m；FXTM -0.22~-0.29；
  CI 不含 0，FDR 全过）——高 spread 之后波动下降。解读：spread 是**活跃度/流动性状态**代理
  （tight spread=活跃=高波动；宽 spread=清淡=低波动），信息方向与"价差=风险溢价"的简单直觉相反
- spread → 未来收益：弱负（DUKA h60 -0.044 强；FXTM h15 -0.019、h60≈0 不显著；z 化后两源皆负）
  ——方向存在但**疑似 session 混杂**（宽 spread 集中在清淡时段），记为 EDGE 待 session 分层复验

**分类回答：**
- 真正的 directional information：**未发现跨期稳定项**
- volatility information：**强且稳定**（H4 全家族 + trend_str + spread 反向）
- liquidity/microstructure information：spread 状态可预测未来波动/部分收益（EDGE）；
  tick 层（imbalance/flow/impact）工具已就绪，数据补齐后即为 R2 冻结清单（28 条预登记待冻结）

## 9–10. 成本/OOS/WF 后
- 所有方向类候选在 1x/2x/3x 成本压力 + 子段门槛下两期均 **0 SUPPORTED**（与 Phase 2 一致）
- 波动率信息类本质是 vol-forecast，不直接构成可交易方向策略（不强行包装为 alpha）

## 11–15. 最强候选与机制
- 信息层面最强：**波动聚集**（跨期 IC 0.54-0.89 级别）→ 应用形态是**波动率/执行时机**而非方向；
- 唯一跨期方向一致项：dist_lo_60→60m（弱，+0.018/+0.066）与 hour 效应——强度不足以过成本门槛
- 机制解释：分钟级波动聚集源于宏观消息簇与流动性供给节奏；方向效应的时期依赖与
  2023-24 震荡/2026 趋势性行情的 regime 差异一致（与合成数据实验 B/C 的结论互相印证）

## 16–17. 值得进入下一阶段？结构性原因？
**否（NO_FEASIBLE_ALPHA，方向类）**。结构性原因：
1. 短周期方向 IC 绝对值 ~0.01-0.04，在 0.5-2.4bp 单边成本下经不起换手损耗
2. 方向效应时期依赖（两期反号），样本内显著性是大样本功效的产物而非稳定信号
3. 波动/流动性信息虽强，但当前协议下无直接方向化映射（需 execution-alpha 框架而非方向 alpha 框架）

## 18. 下一阶段最值得投入
1. **等 DUKA 补齐（~15h）→ 全量跨期复验 + 年度分解**（2023/24/25/26 逐年 IC 表）
2. **Tick 层落地**：先 2024-01 与 2026-08 两个月 → R2 冻结 28 条微观结构假设
   （imbalance/flow/impact/arrival × 5-240m）
3. **执行类研究转向**：vol-forecast → 波动率目标仓位/限价单执行/流动性择时，
   以"降低交易成本与波动"为目标的 execution alpha（若方向 alpha 继续缺席则正式转型）
4. **session 分层复验** spread→收益 与 hour 效应（排除混杂后再定性）

## 状态汇总
| 结论 | 数量 |
|---|---|
| SUPPORTED | 0 |
| EDGE_UNCERTAIN（跨期/成本后不达标） | 若干（详见 round details） |
| REJECTED（翻转/消失/成本淘汰） | 多数方向类 |
| **总判定** | **NO_FEASIBLE_ALPHA（当前协议下无可行方向 Alpha）；存在强波动/流动性信息** |

## Git & 纪律
- 提交：`feat: autonomous alpha research phase 3`（含 DUKA 下载/装配/解码、micro 特征库、
  R2 预登记、跨期与 spread 实验脚本与报告）
- 未 push；无凭证入 git；全程只读数据操作；无真实交易

## 附录：产物
- reports/phase3_crossperiod.md（跨期表）· reports/phase3_spread_info.json · reports/round1_duka2023_details.json
- data_registry/（3 DUKA + 3 FXTM 数据集）· scripts/{dukascopy,duka_download,duka_resume,duka_assemble,phase3_*}.py
- research_engine/features/micro_duka.py · alpha_engine/hypothesis_round2.py（待冻结）
