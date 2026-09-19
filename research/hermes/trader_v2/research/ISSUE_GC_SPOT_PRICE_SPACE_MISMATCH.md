# ISSUE — GC=F / XAUUSD spot 价空间错配（instrument price-space mismatch）

- **ID**: ISSUE_GC_SPOT_PRICE_SPACE_MISMATCH
- **STATUS**: **CONFIRMED**
- **发现**: 2026-09-16（首笔真实 Broker Demo 成交后复盘）
- **类型**: 工程/设计缺口（**不是**策略缺陷；本 ISSUE **只报告，不改策略**）
- **受影响**: Hermes V2 全部 TRADE 计划（plan.entry / plan.stop_loss / plan.take_profit）与执行价空间

---

## 1. 事实

| 项 | 值 |
|---|---|
| 信号价空间 | `GC_F`（COMEX 期金，Yahoo `GC=F`）—— `v2_config.instrument_marking` |
| 执行标的 | `XAUUSD`（FXTM Demo 现货） |
| 计划（用 GC 价位） | entry 4305.52 / SL 4322.74 / TP 4277.97（设计 R:R 1.60） |
| 实际成交（spot） | entry 4292.60（broker fill） |
| 观测 basis | **+12.92 USD**（GC − spot） |
| 实际止损距离 | 30.14（设计 17.22） |
| 实际止盈距离 | 14.63（设计 27.55） |
| 实际 R:R | **≈0.49**（设计 1.60） |
| 实际单笔风险 | 0.01 手 × 100oz × 30.14 ≈ **$30.14 ≈ 账户 2.9%**（配置目标 2%） |

### 历史影响（Q4）

`tools/price_space_audit.py` 扫描全部 run：

- TRADE 决策共 **4** 条；其中 2 条有真实成交，**2/2 = 100% 判为 MISMATCH**。
- 已成交样例：
  - `DEC-ctx_afc5647fbab6`（run d341）plan 4305.52 / fill 4292.60 → basis **+12.92** → plan_R 1.60 → actual_R 0.485
  - `DEC-ctx_30ab864391fa`（run 5fe2）plan 4296.81 / fill 4305.53 → basis **−8.72** → plan_R 1.60 → actual_R 4.276
- 结论：**系统性（100% 命中），且 basis 可正可负**（不是单笔偶然偏差）。

---

## 2. 审计问答（任务书 §八）

**Q1 — Hermes 的 entry/SL/TP 是 GC 绝对价还是 XAUUSD 绝对价？**
→ **GC 绝对价**。证据：`hermes/hermes.py: build_plan(cand, price)` 的 `price` 来自
`ctx["market"]["primary_last"]`，而 `ctx.market` 由 `hermes/context.py` 从 **Agent1 主序列 `GC=F`** 填充
（`v2_config.market_data.primary_instrument = "GC=F"`）。SL/TP = `price ± price*0.4%*R`，全部在 GC 价空间。

**Q2 — 执行前是否应经过 GC→Spot 变换？**
→ **应该，但当前代码中不存在任何变换**。全链路检索：`execution/`、`runtime/`、
`hermes_paper_adapter.to_execution_request()` 均**直接透传** `plan.entry / stop_loss / take_profit`
到 `executor.open(...)`，执行器用**现货 tick** 成交（`fxtm_demo_adapter.place_market_order` 用 `symbol_info_tick(SYMBOL).bid/ask`）。
即：**GC 价位被当作 XAUUSD 绝对价直接下单**。

**Q3 — basis 的性质？**
→ **动态**，且：
- 随行情/期限结构变动（今日 ctx 记录 11.97 ~ 13.17；两笔成交观测到 +12.92 与 **−8.72**，符号会翻转）；
- 与 session/roll 相关；
- 与 source 相关（不同现货报价源 basis 不同）。
→ **不可用常数偏移修正**，必须逐笔显式换算。

**Q4 — 历史是否同问题？**
→ **是**，见 §1 历史影响（2/2 成交全部命中）。

---

## 3. 影响面

1. **风险刻度失真**：真实止损距离 ≠ 设计止损距离 → 单笔风险可被放大（本例 2%→2.9%）或缩小。
2. **R:R 失真**：设计 1.60 实际 0.485（也可反向虚高 4.276）→ 期望收益/凯利类度量不可信。
3. **TP/SL 语义漂移**：TP/SL 落在“结构位”以外（结构位是在 GC 空间识别的）。
4. **账本可解释性**：账本记的是 broker 真实成交（正确），但计划与成交的价空间不同源 → 复盘必须做换算。

> 本笔 `+14.63 USD` 只是**碰巧 TP 先到**。盈利不改变“风险刻度失真”这一事实，
> 该笔交易作为 **有效 Broker Demo 执行证据 + 标尺异常案例** 原样保留（未删、未改、未重算）。

---

## 4. 建议的最小修复方案（**仅建议；本任务未改策略**）

```text
signal price space (GC=F)
   │  ← 保留：结构识别 / 决策仍在 GC 空间（策略不变）
   ▼
explicit price-space conversion   ← 新增：basis 逐笔获取（同轮 Agent1 现货交叉校验 / 或 broker tick 与 GC 同步取样）
   │       spot_equiv = gc_price - basis(t)（含符号，逐笔）
   ▼
execution price space (XAUUSD)
   ▼
SL / TP（换算后落到现货空间，保持“距离”语义）
   ▼
Sizing（用换算后的止损距离，风险预算才等于配置值）
```

要点：
- 只改**价空间换算与下单前的 SL/TP/sizing 输入**；**不改** direction/confidence/expected_R 逻辑/阈值/gate。
- basis 需与决策价**同时点**（point-in-time），并写入 decision context / 账本（可审计）。
- 若 basis 不可得 → **fail-closed**（不下单），而不是默默用 GC 价。
- 需要一次明确的“策略参数复核”由用户确认（本 ISSUE 不擅自实施）。

---

## 5. 证据文件

- 审计表：`research/PRICE_SPACE_AUDIT.md`
- 生成脚本：`tools/price_space_audit.py`
- 回归测试：`tests/test_price_space_audit.py`
- 原始成交：`research/runs/V2-PAPER-20260915-112856-d341/ledger.jsonl`（seq 94-95, 117-119）
