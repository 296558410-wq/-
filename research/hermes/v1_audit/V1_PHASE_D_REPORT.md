# V1 审计 · PHASE D — 逐笔真实行情 OUTCOME 重放（描述性，不做 Alpha 结论）

- 生成：2026-09-17 · `research/hermes/v1_audit/` · **零修改 V1/V2/V3** · **无任何订单** · 源 = **A（live_fxtm，V1 当时保存）**。
- 产物：`V1_TRADE_REPLAY.jsonl`(PHASE-D 富集；PHASE-B 版保留为 `V1_TRADE_REPLAY_PHASE_B.jsonl`)、`V1_OUTCOME_ANALYSIS.json`、`V1_MFE_MAE.jsonl`、`V1_BASELINE_ANALYSIS.json`、`V1_COST_ANALYSIS.json`、`V1_AUDIT_EXPERIMENT_REGISTRY.json`(更新)、`V1_AUDIT_DATA_REGISTRY.json`(更新)、`V1_AUDIT_PHASE_D_SHA256.json`
- 脚本：`tools/v1_audit_phaseD.py`

## 0. 纪律
- 本阶段只输出 **OBSERVED OUTCOME EVIDENCE**；**不得**给“V1 有/无 Alpha”结论；未改 V1/未重跑/未优化 TP·SL·holding/未删亏损单。
- ENTRY 描述遵守 PHASE C 协议：**不得**写“V1 因为 X/Y/Z 所以 BUY/SELL”（除 T_signal 前有直接证据）。
- entry reference = **T_signal 时刻最后一个 ≤ T_signal 的 tick(mid)**；区间内 >60s 缺口 → 该 horizon **DATA_GAP**（不插值、不用后首 tick 补、不删交易）。

## 1. 各 horizon 可计算数（Q1）
- 对象：OUTCOME_RECONSTRUCTABLE **53**（+4 笔 DATA_GAP/UNRESOLVABLE **保留在总体记录**）。
- 锚点 entry-ref 可得 → 逐 horizon 可计算 **47**（1s..300s）/ **46**（900s）；其余 **DATA_GAP**（入场前无有效 tick 或跨缺口）。

| horizon | 可计算 | V1 mean(directional,USD/oz) | median | win_rate | perm_p |
|---|---|---|---|---|---|
| +1s | 47 | +0.084 | 0.06 | 0.617 | 0.028 |
| +2s | 47 | +0.118 | 0.14 | 0.617 | 0.021 |
| +5s | 47 | +0.207 | 0.135 | 0.638 | 0.005 |
| +10s | 47 | (见 JSON) | | | |
| +30s | 47 | +0.090 | -0.04 | 0.426 | 0.579 |
| +60s | 47 | -0.219 | -0.25 | 0.447 | 0.438 |
| +180s | 47 | (见 JSON) | | | |
| +300s | 47 | (见 JSON) | | | |
| +900s | 46 | -0.645 | -0.4375 | 0.435 | 0.455 |

## 2. 入场方向之后的真实价格运动（Q2）
- **短 horizon（1–5s）方向均值轻微为正**（+0.08~+0.21 USD/oz，win 0.62–0.64）；
- **≥60s 转为轻微为负**（-0.22 ~ -0.65）。→ 描述性：短窗略顺、长窗略逆，但幅度极小。

## 3. LONG vs SHORT（Q3）
- LONG **n=8**（可计算 7）/ SHORT **n=49**（可计算 39–40）。**样本极不平衡**。
- LONG 2s mean +0.38（win 0.857, p 0.03，n=7）；SHORT 2s +0.073。
- **仅报告事实**：**不据小样本宣布某方向有效/无效**。

## 4. FINAL_WIN vs FINAL_LOSS 的入场后路径（Q4）
- WIN n=30 / LOSS n=27。
- **LOSS 组在 +2s 方向均值为正**（+0.167, win 0.667, p 0.016），30s 转负 → 与“入场后短期曾顺向、后回吐”**描述一致**（**不据此下结论**）。
- WIN 组 2s/30s 轻微为正。

## 5. MFE / MAE（Q5）
- 方向归一化（BUY 上为正 / SELL 下为正），窗口 [T_signal, T_exit]。
- **MFE 中位 ≈ +2.30 USD/oz；MAE 中位 ≈ −3.36 USD/oz**（n=57）。
- 观察：**MAE 幅度大于 MFE** → 入场后先逆行更多（描述性，非结论）。

## 6. 与 baseline 对比（Q6）
- A=V1 实际 / B=反向 / C=随机（**固定 seed 20260917**，不可改）。
- 反向 = −方向均值；随机 ≈ 0（±噪声）。V1 在短窗略优于反向，长窗略劣于反向——**但均属小样本、且落在 12 项检验家族内**。
- **不得**据此称“明显区别于 baseline”。

## 7. 受数据缺口影响的结果（Q7）
- **10 笔**无有效 entry-ref / 跨 49.2h 周末缺口 + 每日日切 → 逐 horizon 不可计算（DATA_GAP）；`POS-20260913T2217Z`、`POS-20260915T0632Z` 全窗 GAP；`POS-20260917T1047Z` 未平仓。
- 900s 档再少 1 笔（46）。

## 8. 受成本 DATA_GAP 影响的结果（Q8）
- **OBSERVABLE_NET** = review.realized.pnl_usd（**仅含已记录 slippage**）。
- **TRUE_NET_STATUS = DATA_GAP**（commission/swap 未记录，**禁默认 0**）。
- 成本压力 0/0.5/1/1.5/2/3× **与真实成本严格分开**；**不得**把压力结果当作完整真实净收益。

## 9. 仅为描述性、尚不足以称 Alpha（Q9）
- 所有 horizon 均值幅度 ~0.1–0.6 USD/oz（≈ 0.02–0.15 bp 量级，且**未扣 spread/commission/swap**）；
- 家族含 **9 horizon + LONG/SHORT + WIN/LOSS + baseline ≥ 12 项检验** → 未过 BH-FDR，2s/5s 的小 p 值**属多重检验风险**；
- 交易间存在**时间重叠** → raw N=47 **非独立样本**，effective N 更低（block bootstrap/permutation 已在 JSON，但不足以支持 Alpha）。
- ⇒ **本阶段结论：仅为 OBSERVED OUTCOME EVIDENCE；既不说“V1 有 Alpha”，也不说“V1 没有 Alpha”。**

## 10. 下一阶段“应允许”的分析（描述，供放行）
- 对**集合 B**做**事后路径/成本（可重建项）**的进一步分层（须登记、控多重检验、承认缺口）；
- **ENTRY 类**归因只能建立在 **T_signal 前已保存证据**上；
- **任何 Alpha 判定须更后阶段**，且必须先解决：entry-ref 覆盖缺口、commission/swap DATA_GAP、重叠样本 effective N。

> 所有数字可复现（脚本 + 源A sha256 + seed）。引用须带 `V1_OUTCOME_ANALYSIS.json` + `V1_AUDIT_PHASE_D_SHA256.json`。
