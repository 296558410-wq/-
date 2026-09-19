# PRICE_SPACE_FIX_AUDIT — GC=F 信号空间 → XAUUSD 执行空间

- **ID**: PRICE_SPACE_FIX_AUDIT
- **生成**: 2026-09-17 (只读审计)
- **BASE_COMMIT**: `7fe4828eab194ec3fc6c32351662b6b40dfc7176`
- **branch**: `fix/v2-gc-spot-price-space`
- **范围**: 只读。不改策略、不改 4644、不改 V1、不改历史账本。
- **结论（一句话）**: `GC=F` 是 signal space、`XAUUSD` 是 execution space；链路中**没有任何价格空间换算**；已确认系统性错配，并给出 10 笔历史 TRADE 的完整证据。

---

## 1. 链路与价格来源（只读复核）

```
Agent1(yahoo GC=F + sina/tencent 现货)                     ← 数据层
  └─ price_basis.primary_last = GC=F 15m last_close       ← 「信号价」
  └─ price_basis.spot_check.gold_spot = 现货(sina hf_XAU)  ← 「现货参照」
  └─ price_basis.basis_usd = primary_last − gold_spot      ← 「basis(GC−现货)」仅监控
      ↓
hermes/context.py  ctx.market.primary_last = a1.price_basis.primary_last
      ↓
hermes/hermes.py   build_plan(cand, price=ctx.market.primary_last)
   entry = round(price,2)
   risk  = round(price*0.004, 2)            # 0.4% 结构风险
   LONG : sl=price−risk  tp=price+risk*est_r
   SHORT: sl=price+risk  tp=price−risk*est_r
      ↓
hermes_paper_adapter.normalize()  entry_reference=plan.entry / stop_loss / take_profit
      ↓
hermes_paper_adapter.to_execution_request()   # 纯翻译，原值透传
      ↓
runtime/shadow_run.py  px = ctx.market.primary_last ; ADP.process(market_mid=px)
      ↓
executor.open(side, mid=px, sl, tp)              # mid/sl/tp 全是 GC 价
      ↓
fxtm_demo_adapter.place_market_order(XAUUSD, ...)  # 在 XAUUSD 现货上成交，sl/tp 原样下发
```

**结论**: 信号价空间 = `GC_F`（Yahoo `GC=F`，COMEX 期货代理）。执行标的 = `XAUUSD`（FXTM Demo 现货）。
`entry/SL/TP/mid` 全程停留在 GC 价空间，**执行前未做任何换算**（`grep` 全仓无 price-space 转换）。

## 2. 审计清单（任务书 §三）

| 项 | 实际值 / 来源 |
|---|---|
| Hermes `entry` | `hermes.py::build_plan` → `plan.entry`；= `ctx.market.primary_last`（GC=F） |
| `stop_loss` | `plan.stop_loss` = entry ± price*0.4%（GC 空间） |
| `take_profit` | `plan.take_profit` = entry ± price*0.4%*expected_R（GC 空间） |
| `entry_reference` | `hermes_paper_adapter.normalize` = `plan.entry`（GC） |
| `primary_instrument` | `config.market_data.primary_instrument = "GC=F"`；`instrument_marking.instrument="GC_F"` |
| execution symbol | `XAUUSD`（`v2_config.symbol` / shadow_run 默认） |
| broker symbol | `XAUUSD`（`fxtm_demo_adapter.SYMBOL`，FXTM Demo01, magic 90003） |
| decision timestamp | `d.ts`（hermes 决策写出时刻） |
| signal timestamp | `a1.generated_utc` / `ctx.market.retrieved_at` / `quotes.gold_spot.data_ts` |
| 当前价格来源 | 特征=`Yahoo GC=F`（单源历史）；现价=`sina→tencent→eastmoney→yahoo` 回退 |
| GC=F 数据源 | Yahoo chart `GC=F`（历史 5m/15m/60m/1d） |
| XAUUSD spot 数据源 | Agent1 交叉校验 `sina hf_XAU`；**执行**用 broker `symbol_info_tick` |
| basis（现有） | `a1.price_basis.basis_usd = GC=F − sina现货`（**仅监控，未用于执行**） |

**确认**: `GC=F` = signal space；`XAUUSD` = execution space。✅

## 3. 历史成交的实际关系（任务书 §三 / §十）

全部历史 TRADE 决策（10 笔，2026-09-11 → 2026-09-17），`basis_obs = GC entry − 实际成交`：

| # | decision_id | ts(UTC) | side | GC entry | GC SL | GC TP | planRisk | 实际成交 | basis_obs | ctx basis_usd | 结果 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DEC-ctx_90c83bcaca11 | 09-11 14:07 | SHORT | 4432.10 | 4449.83 | 4403.73 | 17.73 | — | — | 44.77 | RISK_LIMIT（拒） |
| 2 | DEC-ctx_feb7a04dfcd8 | 09-11 13:52 | SHORT | 4434.90 | 4452.64 | 4406.52 | 17.74 | — | — | 45.57 | RISK_LIMIT（拒） |
| 3 | DEC-ctx_30ab864391fa | 09-15 04:53 | SHORT | 4296.81 | 4314.00 | 4269.31 | 17.19 | **4305.53** | **−8.72** | −8.58 | 成交 → 实际 R **4.276**（设计 1.60） |
| 4 | DEC-ctx_afc5647fbab6 | 09-15 22:23 | SHORT | 4305.52 | 4322.74 | 4277.97 | 17.22 | **4292.60** | **+12.92** | 13.17 | 成交 → 实际 R **0.485**（设计 1.60） |
| 5 | DEC-ctx_0d750e73b0cf | 09-16 13:52 | SHORT | 4347.77 | 4365.16 | 4319.95 | 17.39 | **4339.04** | **+8.73** | 6.29 | 成交 → 实际 R **0.731**（设计 1.60） |
| 6 | DEC-ctx_a463ab883d7a | 09-16 14:07 | SHORT | 4346.70 | 4364.09 | 4318.88 | 17.39 | — | — | 21.41 | POSITION_BUSY |
| 7 | DEC-ctx_683a6dec351c | 09-16 14:22 | SHORT | 4348.64 | 4366.03 | 4320.82 | 17.39 | — | — | 13.39 | POSITION_BUSY |
| 8 | DEC-ctx_bca0dad1eebb | 09-16 16:37 | SHORT | 4352.65 | 4370.06 | 4324.79 | 17.41 | — | — | 5.73 | POSITION_BUSY |
| 9 | DEC-ctx_55b1efd90824 | 09-16 19:07 | SHORT | 4351.82 | 4369.23 | 4323.96 | 17.41 | — | — | **82.52** | **BROKER_REJECT_10016 Invalid stops** |
| 10 | DEC-ctx_1c8042b9ee65 | 09-16 21:22 | SHORT | 4335.78 | 4353.12 | 4308.04 | 17.34 | — | — | **71.84** | **BROKER_REJECT_10016 Invalid stops** |

**实际关系**: 3 笔成交的 `basis_obs` 与 Agent1 同轮 `ctx_basis_usd` 几乎一致（误差 0.1–2.4 USD）。
成交#3/#4 即既有审计的 **2/2 MISMATCH** 来源。**basis 动态**（−8.72 ~ +82.52）且**会变号** → 严禁常数转换。

### 3.1 10016 的直接机制

对 SHORT，broker 要求 `SL > market > TP`。
- #9: basis_obs≈+82 → 现货≈`4351.82−82.52=4269.3`；下发的 `TP=4323.96 > market 4269.3` → **TP 落在市价错误一侧 → Invalid stops**。
- #10: 现货≈`4335.78−71.84=4263.9`；下发的 `TP=4308.04 > market` → 同上。

即：**GC 价空间的整条计划（entry/SL/TP）整体高出执行现货 ~70–82 USD**，对做空而言 TP 跑到市价上方 → 10016。

## 4. 根因证据：信号腿与执行标的本身发生背离（不只是「未换算」）

Agent1 快照 `basis_usd` 时间序列（2026-09-16 UTC；basis_usd = GC=F − 现货）：

| 周期(UTC) | GC=F(yahoo) | 现货(sina hf_XAU) | COMEX(sina hf_GC) | basis_usd |
|---|---|---|---|---|
| 17:07 | 4339.21 | 4344.33 | 4387.91 | −5.12 |
| 18:07 | 4350.01 | 4334.52 | 4377.50 | 15.49 |
| 18:37 | 4351.00 | 4273.25 | 3307.60* | 77.75 |
| **19:07** | **4351.82** | **4269.30** | 4301.75 | **82.52** |
| 19:22 | 4349.05 | 4249.97 | 4285.49 | 99.08 |
| 21:07 | 4350.01 | 4263.94 | 4299.58 | 86.07 |
| **21:22** | **4335.78** | 4263.94 | 4299.58 | **71.84** |
| 22:07 | 4268.74 | 4261.51 | 4298.73 | 7.23 |

（*18:37 comex 原始值 4307.60；上表 3307.60 为笔误修正为 4307.60。）

- 现货(sina) 与 COMEX(sina) 在 18:07→18:37 之间同步下移 ~80，而 **yahoo GC=F 几乎不动**；
- broker(FXTM XAUUSD) 站在现货一侧（否则 #9/#10 不会以「TP 高于市价」被拒）。
→ **Yahoo GC=F 信号腿在该时段与真实市场背离**（延迟/陈旧），使「未换算」雪上加霜。

**含义**: 即使做了换算，若信号腿本身陈旧，仍会错。因此修复必须包含：
(a) PIT basis 换算；**(b) 执行前对 execution space 重新验证**；**(c) basis 缺失/超龄/异常跳变一律 fail-closed**。

## 5. 已确认项

1. `GC=F` 是 signal space；`XAUUSD` 是 execution space。✅
2. 代码中**不存在**任何 GC→XAUUSD 价格换算（`execution/`、`runtime/`、`hermes_paper_adapter.to_execution_request()` 全为原值透传）。✅
3. 历史 `basis` 动态、可变号（−8.72 ~ +82.52），**不可用常数修正**。✅
4. 3/3 成交的「计划 vs 成交」全部 MISMATCH（含既有审计 2/2）；2 笔 10016 可直接由价格空间错配解释。✅

## 6. 待修（本任务范围）

新增 `execution/price_space.py`，在 **Execution Preparation / Risk Validation** 层插入：
`signal(GC) → PIT basis → execution(XAUUSD) → 执行前验证(SL/TP 边、最小止损、tick/精度) → sizing(XAUUSD) → broker`。
不改 Hermes、不改候选/门禁/阈值/频次；**fail-closed**；保留 signal_* 与新增 execution_*。

## 7. 证据文件

- 本文件；`research/ISSUE_GC_SPOT_PRICE_SPACE_MISMATCH.md`；`research/PRICE_SPACE_AUDIT.md`
- 原始：各 run `research/runs/*/ledger.jsonl`、`decisions/*.raw.json`、`state/decision_contexts/*.json`、`state/snapshots/agent1_*.json`
