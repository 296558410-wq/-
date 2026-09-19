# V1 逐笔交易尸检报告（早期 vs 近期路径对照）

- 生成：2026-09-17 · `research/hermes/v1_audit/` · **V1/V2/V3 零修改** · **无订单** · 源 = **A（live_fxtm）** · seed 固定
- 期间（**事前固定，不因结果修改**）：**EARLY = 2026-09-08 ~ 09-14**；**RECENT = 2026-09-15 ~ 09-17**
- 产物：`V1_TRADE_AUTOPSY.jsonl` · `V1_EARLY_RECENT_PATH_COMPARISON.json` · `V1_LOSS_TRADE_AUTOPSY.json` · `V1_RECENT_3DAY_AUTOPSY.json` · `V1_ENTRY_VS_EXIT_EVIDENCE.json` · 本报告 · `V1_TRADE_AUTOPSY_SHA256.json`
- 预注册描述阈值：MFE ∈ {0, 0.5, 1, 2} USD/oz（**不搜索更多阈值**）

---

## 0. 一句话结论（白话）
**最近三天（09-15~17）的亏损，大多不是“进场就错”，而是“进场后曾朝正确方向动过、后来回吐/拖长”。**
证据：近期 13 笔里 **只有 1 笔** 属于“入场立即反向（ENTRY_WRONG_PATH）”；**10 笔亏损里有 6 笔曾出现正 MFE**；同时**持仓时间中位数从早期的 ~2705s 拉长到近期的 ~8265s（≈3×）**。
但**样本极小（近期 13 笔）**，且**无法用现有数据把“退出/管理”与“小样本波动”严格分开** → **根本原因仍 `UNRESOLVED`**。
明确排除：**“入场方向失效”不成立（`NOT_SUPPORTED`）**。

## 1. 方法（两期完全一致）
- 锚点 **T_signal**；方向归一（BUY=+1/SELL=−1）；horizon 1/2/5/10/30/60/180/300/900s（源 A，缺口→DATA_GAP，不插值）。
- MFE/MAE 窗口 [T_signal, min(T_exit, +900s)]，方向归一。
- 路径分类（定义见 §5）：ENTRY_WRONG_PATH / ENTRY_RIGHT_THEN_REVERSED / PROFIT_AVAILABLE_BUT_NOT_REALIZED / NO_CLEAR_ENTRY_EDGE / DATA_GAP（**可多标签**）。

## 2. EARLY vs RECENT 对照表（§九 要求）
| 指标 | EARLY (09-08~14) | RECENT (09-15~17) |
|---|---:|---:|
| 交易数 | 44 | 13 |
| 胜率 | **0.614** | **0.231** |
| P&L (USD) | **+127.17** | **−98.95** |
| 平均 MFE (USD/oz) | **+4.25** | **+2.97** |
| 平均 MAE | −5.39 | −2.95 |
| MFE>0 比例 | 1.00 | 0.889 |
| **MFE>0 但最终亏损** | **15** | **6** |
| ENTRY_WRONG_PATH | 4 | **1** |
| ENTRY_RIGHT_THEN_REVERSED | 8 | 1 |
| PROFIT_AVAILABLE_BUT_NOT_REALIZED | 12 | 5 |
| NO_CLEAR_ENTRY_EDGE | 19 | 4 |
| **平均持仓时间 (s)** | **4802.6**（中位 2705.5） | **10676.1**（中位 **8265**） |
| DATA_GAP(路径) | 5 | 5 |

## 3. 亏损的钱丢在哪（§六）
- 全部 **27 笔 LOSS** 中：**MFE>0 = 77.8%**；**MFE>+0.5 = 63.0%**；**MFE>+1 = 51.9%**；**MFE>+2 = 48.1%**。
- ⇒ **多数亏损交易“曾经给过盈利机会”**（OBSERVED_FACT）。**未**据此断言“退出策略错误”。

## 4. 近期 3 日逐笔（§十一）
- 明细见 `V1_RECENT_3DAY_AUTOPSY.json`（含每笔 1s..900s、MFE/MAE、holding、path_class）。
- 09-15 / 09-16 / 09-17 逐日列出，可直接看到“哪一类交易造成亏损”。

## 5. SHORT / LONG（§十）
| | n | 胜率 | P&L | 平均 MFE |
|---|---:|---:|---:|---:|
| EARLY SHORT | 37 | **0.676** | **+160.49** | 4.60 |
| RECENT SHORT | 12 | **0.167** | **−109.53** | 1.78 |
| LONG（全期） | 8 | — | — | **LOW_SAMPLE（不下强结论）** |

## 6. 入场是否失效（§十三 反证检查）
- 近期 **ENTRY_WRONG_PATH 仅 1/13** → **`RECENT_ENTRY_DIRECTION_NOT_OBVIOUSLY_DETERIORATED`**。
- 结合 PHASE D（近期 +1s 方向胜率 0.714 ≥ 整体）→ **`entry_direction_failure = NOT_SUPPORTED`**。

## 7. Entry vs Exit 证据（§十四，仅事后描述）
- 近期 **PROFIT_AVAILABLE_BUT_NOT_REALIZED = 5**（13 笔中）；早期 = 12（44 笔中）。
- **持仓时间中位数 2705s → 8265s（≈3× 拉长）** —— **DESCRIPTIVE_DIFFERENCE**。
- ⇒ “退出/管理可能是主要来源之一” = **PARTIALLY_SUPPORTED**；但**不写 `EXIT_IS_THE_CAUSE`**。

## 8. 成本（§十五）
- `OBSERVABLE_NET`（含 slippage）与 `TRUE_NET`（commission/swap **DATA_GAP**，**禁默认 0**）**分开**。

## 9. §十七 逐问回答
1. **最近三天亏损入场时就错了？** → **否**（ENTRY_WRONG_PATH 1/13）— OBSERVED_FACT
2. **多数入场后曾朝正确方向？** → **是**（8/13 MFE>0；6 LOSS 有正 MFE）— OBSERVED_FACT
3. **近期亏损交易多少曾出现正 MFE？** → **6 / 10**（≈60%）— OBSERVED_FACT
4. **与早期区别？** → 早期亏损 15/17 曾正 MFE（≈88%）且 MFE 更高；近期 6/10（≈60%）且 MFE 更低 — DESCRIPTIVE_DIFFERENCE
5. **近期 SHORT 变化？** → 胜率 0.676→0.167、P&L +160.49→−109.53 — DESCRIPTIVE_DIFFERENCE
6. **持仓时间变化？** → **是**（中位 2705s→8265s）— DESCRIPTIVE_DIFFERENCE
7. **亏损 vs 盈利模式区别？** → 早期：持仓短、MFE 高、胜率高；近期：持仓长、MFE 低、胜率低 — PATH_STRUCTURE_DIFFERENCE
8. **退出/管理是主因？** → **PARTIALLY_SUPPORTED**（多数亏损曾正 MFE + 持仓拉长），但 n 小
9. **入场方向失效？** → **NOT_SUPPORTED**
10. **仍无法区分？** → “退出/管理” vs “小样本随机” vs “市场结构” — **UNRESOLVED**

## 10. 结论词表（§十八）
OBSERVED_FACT · DESCRIPTIVE_DIFFERENCE · PARTIALLY_SUPPORTED · NOT_SUPPORTED · UNRESOLVED · INSUFFICIENT_EVIDENCE。
**不写** `V1_HAS_ALPHA` / `V1_HAS_NO_ALPHA` / `V1_IS_BROKEN` / `EXIT_IS_THE_CAUSE` / `ENTRY_IS_THE_CAUSE`。

## 11. 变化点
- 描述上“09-15 起转负”，但 **`CHANGE_POINT_HYPOTHESIS`**（不重定义阶段）；样本不足以确立 `PERFORMANCE_CHANGE_POINT`。

> 未做策略优化、未改 V1、未发单。引用须带对应 JSON + 源A sha256。
