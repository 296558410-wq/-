# Phase 9 Data Audit（盘点层，无搜索）
> 目标：确认各时间尺度研究的可用数据与约束；判定 DISCOVERY 与 PASS 的数据资格。

## 1. Tick 窗（10s-3m 主战场）
FXTM MT5：2026-08-04 → 2026-09-04，**23 个交易日，4,995,855 ticks**（日文件 24 个，周末正确空缺）。
- 内容：bid/ask/last/volume/flags（quote 与 trade print 混合；volume>0 为成交记录）
- tick 级 spread：mean $0.162 / median $0.155 / p99 $0.232（**近固定点差 feed** → spread 动态研究受限）
- 分钟覆盖：32,396 M1 微 bar；平均 154 ticks/min（2.5/s）
- 每 session 覆盖（分钟）：Asia ~9.5k / London ~6.8k / NY ~6.5k / overlap ~5.4k（近似）
- **独立日数 23** → 日级稳定性门槛：≥15/23 正天数方有意义；月内 subperiod 不可分（单月）

DUKA tick：**未下载**（蜡烛补全 553/1343 天进行中；tick 月下载排在其后）→ 任何 ≤1m 结论目前
只能算 DISCOVERY 级；**PASS 的跨 feed 验证必须等 DUKA tick**（本阶段时间表将其列为闸门 7 前置条件）。

## 2. M1 窗（1-15m 研究）
- FXTM 2026：100,000 bars（2026-05-26→09-04，≈69 交易日）——含 spread+tick_volume
- DUKA 2023-24：229,020 bars（2023-09-01→2024-03-16，≈130 交易日）——含 spread
- 双期双源 ✓；M5/H1 派生可用（FXTM 原生 M5/H1 亦注册）

## 3. 尺度资格矩阵
| 研究尺度 | FXTM tick(2026) | DUKA M1(2023-24) | 结论资格 |
|---|---|---|---|
| 10s-30s | ✓ 事件时间可做 | ✗（无 tick） | DISCOVERY only（等 DUKA tick） |
| 1m-3m | ✓（tick 聚合） | ✓（M1） | DISCOVERY + 跨期校验 |
| 5m-15m | ✓ | ✓ | 全资格（含跨 feed M1） |

## 4. 关键质量事实（影响设计）
1. FXTM tick 的 quote/trade 混合：方向统计用 mid（报价）而成交方向仅 volume>0 的 last 子集 →
   signed-flow 代理弱；P7 需以 quote 节奏/到达率为主，不承诺成交方向精确性。
2. FXTM 固定点差：spread 族研究（P7 spread 动态）不可行于此 feed → 归入"DUKA tick 待办"。
3. 10-30s 结论的样本：23 天 × 每 30s 约 4.8 万个事件时点，但**独立日 23** → 一切 p 值以日为单位重估。
4. DUKA M1 的 spread 呈水平切换结构（0.31↔0.70 级）→ 若做 spread 条件分析须按水平分桶。

## 5. 审计结论
- DISCOVERY（FXTM tick + 双源 M1）数据就绪，可以启动 P1-P7 探测器预登记与 DISCOVERY 段；
- VALIDATION/OOS（M1 级跨期）可就绪；**CROSS-FEED PASS 闸门依赖 DUKA tick**（补全后另行通知）；
- 无阻碍性数据问题；主要限制（固定点差 feed、23 独立日）已写入框架 §5/§16。
