# 09_UNKNOWNS — 仍 UNKNOWN 的关键问题（2026-09-07 审核合并六路）
> 纪律：无法验证标 UNKNOWN，不猜。按"若解决能改变什么"排序。

## 高影响 UNKNOWN（解决→可能改变研究空间）
1. **XAUUSD 状态→条件收益分布（P/AvgWin/AvgLoss 扣成本）无公开实证** —— 必须内部估计（S4-CO U1）。
   若本地漂移环 + 前瞻数据能建立，即为原创知识。DATA_GAP。
2. **隐含加价（last look 拒单/requote/滑点折算）真实值** —— 决定 0.1bps 上界是否实际更低；只需免费 demo 小单探针（S2-EX U3/U2）。
3. **FXTM/DUKA feed 生成管线**（时间戳=dealer 事件时间？单一 LP 合成？插值平滑？）—— 决定所有 quote-path 研究解释边界（S5-GX U1）。
4. **纯报价流能否可靠构造 aggressor/OFI 代理（quote-event imbalance）** —— 无文献覆盖零售 CFD 报价；可本地自测（S1-MS U1/U5；S6-AD ④1）。
5. **0.1bps 上界的 regime 依赖**（只在低波动/深流动性时段存在？坏 regime 归零？）—— 本地数据可答（S2-EX U4）。

## 中影响 UNKNOWN
6. 黄金 VRP（GVZ−RV）符号与对金价预测力 —— 训练知识不一致，未定位权威实证（S4-CO U2）。
7. 黄金 CPI/FOMC 后 >1 日漂移在 2015-2025 高通胀 regime 的系统 OOS（证据偏向无，非定论）（S3-BH U3）。
8. 期权 dealer gamma 对冲是否日频放大黄金波动（OTC 账簿不可观测）（S3-BH U2）。
9. 2020-03 COMEX 溢价峰值精确数值、CME 紧急规则细节、GC 现值（量级可信数值待核）（S5-GX E1）。
10. 黄金整数位止损聚集密度可预测性（需券商专有流）（S3-BH U4）。

## 结构性 UNKNOWN（数据不可得，标记即可不追）
11. 零售 A/B-book 失真度本身（不可观测 = 结构性 UNKNOWN，S6-AD C8）。
12. 账户级零售持仓/成本基准 → 处置效应黄金端强度永远无法直接验证（S3-BH U1）。
13. dealer 身份/库存 → 逆向选择成分分解在纯报价 feed 上不可辨识（S1-MS C2/C9）。
14. Cederburg et al. vol-managed 再评估论文的发表状态（S6-AD C5，标 UNKNOWN 不引卷期）。

## 审核注
UNKNOWN 不自动等于机会。第 1/2/4/5 项是"现有数据或免费 demo 可解"的，优先；
其余在数据/通道解锁前保持 UNKNOWN，禁止猜测填充。
