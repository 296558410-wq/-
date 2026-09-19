# AIQuant Phase 5 — Autonomous Execution Alpha 报告

> 生成：2026-09-04 23:20 (Asia/Shanghai) · git: 见文末
> 回答核心问题：**是否找到了能让真实系统“交易得更好”的信息？** —— 是（执行层与风险层，条件性）；方向层：否。

## 0. 统计协议升级（Phase 4 教训正式落地）
新增 `research_engine/statistics/overlap.py`（pytest 5/5 绿）：
- `non_overlap_entries` / `effective_n` / `ic_at_entries`（非重叠入场点 OOS IC）
- `block_permutation_p`（iid vs block(2) 对照）、`block_bootstrap_ci`
- 协议规则：前瞻 horizon 检验必须报告 effective sample size；iid p 仅作对照
- 回归测试验证：重叠自相关噪声上 iid 显著虚高、非重叠后回落（Phase 4 现象复现于测试中）

## 1. Liquidity / Spread Timing（双窗口，train 阈值 → OOS 应用）

| 窗口 | spread 持续性 IC | 等待执行节省 | 日 t | 正天数 | 说明 |
|---|---|---|---|---|---|
| FXTM 2026 (100k M1) | 0.86-0.92 | ~0 | — | — | feed spread 近恒定（$0.15-0.16）→ **无可择时空间** |
| DUKA 2023-24 (229k M1) | 0.85-0.99 | **0.041bp/笔** | **11.7** | 69/80 | spread 高度可预测（强自相关+日内模式） |

- 机制：DUKA spread 呈持久+均值回复（含宽价差状态，p99 1.86 vs med 0.49）→ “价差 > session p60 时等待至 ≤ p40（30min 上限）”在 OOS 上稳定省钱；18.7% 等待最终成交于窄价差
- 节省绝对值小（$0.008/笔 @ $2050）→ 对**大单/高频执行**才有意义；容量随 size 线性
- **诚实结论**：存在真实 execution alpha，但 feed 依赖（FXTM 型固定点差 feed 无机会）且单笔幅度薄

## 2. Volatility Timing → 仓位/风险（RISK_ALPHA，双窗口对照）

目标波动率定仓（r²-ewm 无偏 vol forecast，日级重平衡，真实成本）：

| 窗口 | 基准 | 定仓后 | 效果 |
|---|---|---|---|
| FXTM 2026 H1（冲击/不稳定 regime） | vol 34.3% / DD -27.9% / Sharpe 0.40 | vol 10.8% / DD **-12.9%** / Sharpe **0.45** | 波动 -68%、回撤 -54%、Sharpe 提高；成本 15bp 可忽略 |
| DUKA 2023-24 H1（平滑单边牛市） | vol 15.8% / Sharpe 3.75 | vol 15.9% / Sharpe 2.85 | 降杠杆削收益、宽 spread 换手成本 166bp → **净损** |

**Regime 依赖结论**：波动率定时在**波动 regime 不稳定期**（转换/冲击密集，如 2026 窗口）显著改善风险与风险调整收益；在**持续低波动趋势期**（2023-24）因降杠杆与换手成本反而受损。这是“何时有效、何时无效”的清晰答案——vol timing 是**条件性 RISK_ALPHA**（需 regime 触发器/自适应目标，不能无条件使用）。

## 3. Adverse selection / 执行质量（快速检查 + 留待 tick 模拟）
- M1 级无法可靠区分主动/被动成交的 adverse selection；FXTM tick 数据已备好执行模拟器原料，
  但本轮预算内未完成 tick 级限价单模拟（fill 概率/排队）——列为下一轮优先（与 DUKA tick 到位同步）

## 4. 最终判定

| 层 | 判定 | 依据 |
|---|---|---|
| 方向 alpha（M1-60m 微观/价格） | **NO_FEASIBLE_ALPHA** | Phase 2/3/4 非重叠 OOS 全部不显著 |
| 波动率/流动性预测（信息层） | **SUPPORTED** | 非重叠 OOS IC 0.60（activity→vol）；spread→vol -0.24；双源互证 |
| 执行层（spread timing） | **EXECUTION_ALPHA（条件性、薄）** | DUKA 类可变价差 feed：0.041bp/笔，t=11.7，跨 80 天稳定 |
| 风险层（vol targeting） | **RISK_ALPHA（regime 条件性）** | 不稳定波动期：DD -54%/Sharpe +；平滑牛市期：负贡献 |
| 总回答 | **“交易得更好”= 是（执行/风险层，条件明确）；“预测更准”（方向）= 否** | |

## 5. NEXT MOVE（优先级）
1. **tick 级执行模拟器**（FXTM 2026 tick 已备 + DUKA tick 补全后复验）：maker/taker 模拟、
   fill 概率、排队风险、adverse-selection 度量 → 回答“等待执行在 tick 级是否仍省钱”
2. **自适应 vol targeting**：加 regime 触发器（波动转换检测/冲击标记）后再评估两窗口——目标是
   把 RISK_ALPHA 从不稳定期专属扩展为全 regime 稳健（用 Phase 3 的 shock 检测思路）
3. DUKA 全量（~15h 后）→ spread-timing 与 vol-target 全量复验 + 逐年分解
4. 执行成本模型入库：按 feed/时段校准的 half-spread + 容量曲线，供未来任何策略的 execution 层默认使用

---
*纪律：只读数据；无真实交易；全部冻结清单+非重叠/分块统计；双窗口互证；脚本与 JSON 入库。*
