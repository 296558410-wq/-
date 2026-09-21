# V3-GITHUB-MICROSTRUCTURE-DISTILLATION-002

- Mode: **AUDIT_ONLY / READ_ONLY · NO order_send · NO calibration · NO forward · NO live**
- Builds research infrastructure and tests data capability. It does **not** hunt for a model.
- **The final PASS/non-PASS judgement is left to the external auditor.**

```text
EVALUATION CHAIN (mandatory):
Gross Edge -> Execution Cost -> Adverse Selection -> Slippage -> Commission -> Latency -> NET EXECUTABLE EDGE
Prediction accuracy is NOT alpha.
```

## 0. Final state

> ### Status C: `EXECUTION_COST_BLOCKED`
> co-existing constraint (documented, not the headline): `MICROSTRUCTURE_DATA_BLOCKED` —
> true OFI / microprice / queue / fill probability are `DATA_GAP` on this L1-quote-only feed.

`EXECUTABLE_ALPHA_CANDIDATE` was **not** pursued and was **not** found.

## 1. What was built

| artifact | path |
|---|---|
| microstructure API | `trader_v3/microstructure/{spread,microprice,ofi,tick_flow,imbalance,volatility_state,markout,adverse_selection,fill_probability,arrival_rate,data_state}.py` |
| execution API | `trader_v3/execution/{cost_model_v2,slippage,latency_cost,pnl_attribution,execution_quality}.py` |
| GitHub matrix | `trader_v3/research/github_distillation/microstructure_matrix.csv` (+ `parts/part_A|B|C.md`) |
| Alpha contract v2 | `trader_v3/research/v3_alpha_contract_v2.md` |
| markout study | `trader_v3/research/v3_markout/run_markout_study.py`, `results.json`, `markout_report.md` |
| data state machine | `trader_v3/research/hypotheses/data_state_machine.md` |
| opportunity gate | `trader_v3/research/hypotheses/opportunity_gate.md` |

Reuse, not duplication: the measured cost anchor and calibration come from
`foundation/cost_model.py` + `state/V3_COST_PROFILE.json` / `V3_EXECUTION_PROFILE.json`. The
deprecated **0.314 bp** model is **not** restored; the measured **0.914 bp / RT** anchor is used.

## 2. Measured facts (this task, real data)

- Feed: FXTM L1 quote-only, 7,247,025 ticks, 2026-08-04 → 2026-09-21 (includes still-appending tail).
- Median spread **0.343 bp** (0.150 USD); p90 0.418; p99 0.535.
- Cost anchor **0.914 bp / RT**.
- **Cost / typical move > 1 for h ≤ 2 s** (1 s = 1.43). → `RESEARCH_BLOCKED_BY_COST` for 50 ms – 2 s.
- Unconditional median markout ≈ 0 at every horizon; mean +1.25 bp (fat tail only).
- Median adverse selection ≈ 0 overall, **+0.05…+0.53 bp in high-spread states**, growing with horizon.
- True OFI / microprice / size imbalance / queue / fill probability → **DATA_GAP**.

## 3. Q1–Q12

**Q1 — Which GitHub work is genuinely worth absorbing?** *(SUPPORTED, as methodology)*
`lukeyin08/Order-Flow-Imbalance` (best hygiene: no-look-ahead labels, 70/30 IS-OOS, HAC, gross-vs-net,
real-data replication — and it reports the decisive fact that a taker edge of 0.09 tick vs 2.48-tick
cost ⇒ **zero trades**); `tradingexpert/ordersim` (deterministic execution realism: queue-ahead +
latency); `Hellblazer704/nanolob` (FIFO queue-position fill model + markout-based AS);
`MaharshKhatri/lob-simulator` (fill-probability + explicit adverse-selection costing);
`intrepidkarthi/orderbook` and `jaefit/deep-ofi` (refutation discipline — the latter *refutes* OFI as a
sufficient statistic).

**Q2 — Which are only pretty but not executable?** *(NOT_SUPPORTED)*
`sauloduttra/ofi-signal` (synthetic R²=0.974, no strategy/PnL/cost); `nsoxbekdn/microstructure-lab`
(fully synthetic, no PnL claims); `1816x/Trading-Microstructure-Engine` (README explicitly: no
prediction, no advice; its "OFI" is a **trade-volume imbalance, not CKS OFI**);
`dshan12/Market-Microstructure` (no OOS split, no purge/embargo, costs unquantified, and its own sim
shows 83–87% of "profit" is **inventory appreciation**, not spread capture).
**All 11 listed repos were verified to exist** via the GitHub API; none could be dismissed as fictional.

**Q3 — Is OFI usable for V3 now?** **DATA_GAP.** True OFI needs bid/ask **sizes** (identically 0 on
this feed). Only `OFI_PROXY` (tick-rule) exists, and it is never called "OFI".

**Q4 — Is microprice usable now?** **DATA_GAP.** Requires sizes; `mid` must not be substituted.

**Q5 — Can markout solve the V1/V3 "entry right then reverse" problem?** **PARTIAL.** It *measures*
the phenomenon precisely (median markout ≈ 0; mean +1.25 bp is tail-only; cost-adjusted median
≈ −0.91 bp). Measurement is not a cure: it tells you the opportunity is not there, it does not create one.

**Q6 — Is adverse selection the real V3 bottleneck?** **PARTIAL / NO as the primary bottleneck.**
Median AS ≈ 0 overall; it becomes materially adverse only in **high-spread/high-volatility** states
(+0.05…+0.53 bp, growing with horizon). Cost is the first-order constraint.

**Q7 — Does current cost already eliminate some horizons?** **SUPPORTED (YES).**
Cost/typical-move > 1 for **h ≤ 2 s** → those horizons are `RESEARCH_BLOCKED_BY_COST`.

**Q8 — Is L2 needed?** **SUPPORTED** for any true OFI / microprice / queue / fill-probability claim.
It is **not** needed to reach the cost verdict (which is what blocks this venue today).

**Q9 — Must real execution calibration be added?** **PARTIAL→SUPPORTED.** The 20-trade calibration
gives spread/commission/latency; slippage, per-fill adverse selection and fill probability remain
`DATA_GAP`/`PARTIAL`. Real execution-realism work needs more calibration and L2.

**Q10 — Optimise Prediction Alpha or Execution Alpha?** **Execution Alpha (SUPPORTED).**
Prediction exists but is sub-cost (best gross ≈ +0.096 bp vs 0.914 bp cost); marginal effort belongs in
execution/cost, not in a bigger predictor.

**Q11 — What data, once obtained, would genuinely widen the space?** **SUPPORTED:** L2/market-depth and
trade prints with sizes (signed volume). That unlocks Level-B microstructure and fill probability.

**Q12 — What research should stop permanently?** **SUPPORTED:** (a) sub-2 s liquidity-*taking*
directional mining on this feed; (b) accuracy/R²-based model search on L1-only price data;
(c) treating a `*_PROXY` as the real quantity.

## 4. Research Decision Matrix (task XXIV)

Allowed labels only: `SUPPORTED / PARTIAL / DATA_GAP / NOT_SUPPORTED`. No stars, no "best".

| 研究方向 | 当前数据 | 理论价值 | 当前可测试 | 当前可交易 | 下一步 |
|---|---|---|---|---|---|
| Direction | L1 `AVAILABLE` | PARTIAL | SUPPORTED | NOT_SUPPORTED | stop accuracy mining; keep as Level-A input only |
| Tick flow | L1 `PARTIAL` (proxy) | PARTIAL | PARTIAL | NOT_SUPPORTED | keep as `FLOW_PROXY`, never "OFI" |
| Microprice | `DATA_GAP` (no sizes) | SUPPORTED | DATA_GAP | DATA_GAP | acquire L2 sizes |
| True OFI | `DATA_GAP` (no sizes) | SUPPORTED | DATA_GAP | DATA_GAP | acquire L2 sizes |
| Trade flow | `DATA_GAP` (prints = 0) | SUPPORTED | DATA_GAP | DATA_GAP | acquire trade prints |
| Markout | `PARTIAL` | SUPPORTED | SUPPORTED | PARTIAL | keep; fix end-of-sample clipping |
| Adverse selection | `PARTIAL` | SUPPORTED | PARTIAL | PARTIAL | model conditional on spread/vol state |
| Fill probability | `DATA_GAP` (no L2 queue) | SUPPORTED | DATA_GAP | DATA_GAP | interface exists; needs L2/MBO |
| Queue model | `DATA_GAP` | SUPPORTED | DATA_GAP | DATA_GAP | needs L2/MBO |
| Latency | `PARTIAL` | PARTIAL | PARTIAL | PARTIAL | continuous calibration |
| Cost | `AVAILABLE` (measured) | SUPPORTED | SUPPORTED | SUPPORTED | keep 0.914 bp anchor; never 0.314 bp |
| Execution Alpha | `PARTIAL` | SUPPORTED | PARTIAL | NOT_SUPPORTED | main area of future effort |

## 5. Safety / integrity

```text
ORDER_SEND = 0        CALIBRATION = 0      FORWARD = NO       LIVE = NO
EXPANSION = LOCKED    V1 = UNTOUCHED       V2 = UNTOUCHED
MT5_INSTANCE_COUNT = 3 (isolation PASS, verified running: 1348 / 36460 / 49300)
V3 foundation / ledger / calibration artifacts = UNTOUCHED (read-only import only)
DATA integrity: timestamps UTC; sha256 used; duplicate/out-of-order audited (0 per file)
Statistical protocol declared: time split + purge + embargo + effective_n + block bootstrap + FDR
```

## 6. Problems found (reported, NOT fixed — task XXVI)

1. **`live_fxtm` still appends** → one tail file is not hash-provable; 913 cross-day-file duplicate
   timestamps. Discovered in the preceding postmortem; **not fixed here**.
2. **End-of-sample clipping** in the AS mean statistic (see `markout_report.md` §4). Medians unaffected.
3. **Deprecated 0.314 bp cost model** still exists in old material; this study uses 0.914 bp only.
   A cleanup of stale references is a candidate for a separate task.
4. Pre-existing uncommitted change to `audit/v3_calibration_formula_fix_20trades.csv` (FORMULA-FIX-002
   enrichment) — not caused by this task.

None of these is a defect in the execution chain, MT5 isolation, cost calculation or ledger, so **no
HALT was triggered**.

## 7. One-line conclusion

> On this L1-quote-only venue, the short-horizon move is **smaller than the real round-trip cost**
> (cost/move > 1 for ≤ 2 s); the microstructure quantities that could in principle help
> (true OFI, microprice, queue, fill probability) are **DATA_GAP**. The binding constraint is
> **execution cost**; the second is **data capability**. No executable alpha has been demonstrated.
> Nothing gets traded without evidence.
