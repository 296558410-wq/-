# AIQuant Phase 4 — Autonomous Microstructure & Execution Alpha Hunt 报告

> 生成：2026-09-04 22:50 (Asia/Shanghai) · git: 见文末
> 数据：FXTM MT5 真实 tick 23 个交易日（2026-08-04→09-04，4,995,855 条，全 bid/ask）+
> Dukascopy 长历史续传中（77 天/约 6% 完成）

## A. DATA（数据基础）

| 项 | 结果 |
|---|---|
| FXTM tick 窗口 | 4,995,855 ticks / 23 交易日 / 32,396 M1 微结构 bar |
| 质量 | spread≤0 占比 0.000%；周末缺口正确；按 time_msc 去重 |
| spread 分布 | mean $0.162 / med $0.155 / p99 $0.232（金价 ~$4,391 时 ≈0.36bp） |
| tick 强度 | ~154 ticks/min，2.5/s 到达率 |
| 源一致性 | FXTM M1 bars（注册数据）与 tick 派生 mid 一致；spread 量级与 Phase 2/3 一致 |
| DUKA 长历史 | 后台续传中（限速保护）；2023-09..2024-03 窗口已入库（Phase 3）——**跨期 tick 复验仍是待办** |

## B. INFORMATION（发现的信息）

**方向类（全部经 OOS+perm，结论见 H）：**
- 逐分钟重叠样本上 12 项冻结检验：仅 imb_r120→60m 过 FDR（OOS IC −0.048），但与筛选矩阵反号 → 样本内假象
- Session 分层（另冻结 10 项）发现**方向相反的 session 效应**：Asia imb→负漂移、London/overlap imb→正漂移（OOS IC 0.13-0.22 级别）——pooling 把它们互相抵消
- **但非重叠再检验（修正重叠标签功效虚高）全部落空**：7 条规则 p≥0.096，按日 t 统计 |t|<1.4

**波动/流动性类（强且稳健）：**
- tick 活跃度→未来波动：非重叠样本 **IC=0.604（n=216, p<1e-4）**；spread→未来波动 −0.24 同向复现
- 与 Phase 3 spread 发现（双源）一致：**活跃度/流动性状态是 XAUUSD 最强的可预测信息层**

## C. DECAY
- spread→收益（负）效应在 1-15m 出现、~10-15m 达峰后衰减（重叠样本；非重叠后不显著）
- 活动度→波动效应在 5-240m 均强（无快速衰减）——波动聚集是小时级结构
- tick imbalance→收益效应（若存在）半衰期 ~30-60m（session 依赖）

## D. REGIME（什么时候存在）
- 方向类：任何 session/regime 分层的**非重叠 OOS 均不显著**（Asia/London/NY/overlap；vol 三分位；spread 三分位）
- 波动信息：全 session、全 regime 存在（活跃度→波动在 low-vol 期 IC 0.05-0.06、整体 0.60）
- 已如实回答"何时存在/何时不存在"：方向类目前无任何稳定存在窗口；波动类全域存在

## E. COST
- 动态成本（信号分钟真实 half-spread + $0.1 滑点）下测试 7 条规则：即使毛收益为正的规则
  （如 London imb +7.4bp/笔）样本不足（10 个 OOS 交易日），日 t 检验全不显著
- 成本本身：$0.08-0.12 单边 vs 净信号 1-10bp/笔 → 成本占比巨大，方向类经济空间极薄

## F. OOS
- 全部正式检验在 60/40 时间切分的 OOS 段执行；置换 p 用 OOS 标签
- 方向类：无一通过（非重叠口径）；波动类：通过（p<1e-4）

## G. ROBUSTNESS
- 按日稳定性：方向规则正天数 5-7/10（不优于随机）
- 剔最差 2 天：无实质改善
- **跨年份验证未完成**（DUKA tick 未就绪）——任何"候选"都不能在此窗口外宣称成立

## H. TRADABILITY 判定
| 项目 | 判定 |
|---|---|
| 方向类微观（imb/flow/spread 条件收益） | **REJECTED**（23 天窗口内无诚实显著性；重叠标签曾造成 p=0.0000 假象，非重叠后 p≥0.096） |
| 波动/流动性预测（activity/spread→fvol） | **SUPPORTED（作为信息）**：非重叠 OOS IC 0.60/-0.24——但它不是方向 alpha，属于 volatility/liquidity timing 信息 |
| 方向 alpha 整体 | **NO_FEASIBLE_ALPHA**（本窗口+协议下） |

**方法学要点（本阶段最大收获）**：重叠标签（每根 bar 的前瞻收益互相重叠）使 permutation/CI
功效虚高——同一条规则在 n≈9000 重叠样本上 p=0.0000，在 n≈140-690 非重叠样本上 p=0.10-0.80。
**所有时间序列 IC 检验必须用非重叠/分块抽样**（已写入阶段报告，后续 alpha_engine 应内置该选项）。

## I. NEXT MOVE（明确建议）
1. **等 DUKA tick（2023-24 窗口）→ 在 n≈1500-3000 非重叠样本上重跑这 7 条 session 规则**
   （单窗口 23 天根本无法裁决 |IC|~0.1 的效应；需要 5-10× 样本 + 独立时期）
2. **把 vol/liquidity 信息转化为执行层价值**：波动率目标仓位、spread 状态感知的限价单执行、
   活跃度过滤——这是当前唯一被双重验证（跨源+非重叠）的信息，应以 execution-alpha 框架评估
3. alpha_engine 增加 overlap-aware 统计（非重叠抽样默认开启），避免后续研究重蹈功效虚高
4. 若 DUKA 全量复验后 session 方向效应仍不显著 → 正式宣告 M1-60m 方向微观无可行 alpha，
   研究重心全部转向 execution/vol-timing

---
*纪律：全程只读数据；无真实交易；FDR/perm/OOS/WF/成本压力均按冻结清单执行；所有阶段 JSON 与脚本入库。*
