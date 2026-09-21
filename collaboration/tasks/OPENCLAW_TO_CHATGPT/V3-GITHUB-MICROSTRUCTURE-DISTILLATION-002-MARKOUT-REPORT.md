# MARKOUT / ADVERSE-SELECTION / COST-TO-MOVE REPORT

- Task: **V3-HFT-GITHUB-DISTILLATION-002** (task VI / VII / VIII / XIV)
- Mode: READ-ONLY on market data. No orders.
- Driver: `research/v3_markout/run_markout_study.py` · raw output: `research/v3_markout/results.json`
- Feed: FXTM L1 quote-only, **7,247,025 ticks**, 2026-08-04T01:05:00.093Z → 2026-09-21T20:24:06.817Z
  (note: this run includes the still-appending live tail; the Alpha-Discovery snapshot was 7,240,039)
- Analysis sample: 1 s as-of grid, freshness ≤ 5 s → **4,216,747 decision instants**
- Convention: all timestamps are **milliseconds since epoch** (native feed resolution).

## 1. Spread (MEASURED)

| metric | value |
|---|---|
| median spread | **0.343 bp** = 0.150 USD |
| p90 | 0.418 bp |
| p99 | 0.535 bp |
| cost anchor (RT) | **0.914 bp** |

## 2. Cost-to-move ratio (task XIV) — *the decisive table*

`Cost / Typical Absolute Move`, cost = 0.914 bp:

| horizon | median \|move\| (bp) | cost / move | verdict |
|---|---|---|---|
| 50 ms | 0.538 | 1.70 | **RESEARCH_BLOCKED_BY_COST** |
| 100 ms | 0.537 | 1.70 | **RESEARCH_BLOCKED_BY_COST** |
| 200 ms | 0.534 | 1.71 | **RESEARCH_BLOCKED_BY_COST** |
| 500 ms | 0.581 | 1.57 | **RESEARCH_BLOCKED_BY_COST** |
| 1 s | 0.639 | 1.43 | **RESEARCH_BLOCKED_BY_COST** |
| 2 s | 0.751 | 1.22 | **RESEARCH_BLOCKED_BY_COST** |
| 5 s | 1.042 | 0.88 | PARTIAL |
| 10 s | 1.421 | 0.64 | PARTIAL |
| 30 s | 2.395 | 0.38 | PARTIAL |
| 60 s | 2.855 | 0.32 | PARTIAL |
| 5 min | 5.429 | 0.17 | PARTIAL |

> **Answer to the task's question:** at horizons **≤ 2 s the natural short-period move is SMALLER than
> the real round-trip cost** (ratio > 1). Research on those horizons is `RESEARCH_BLOCKED_BY_COST`.
> Note this uses the *median*; the p90 is large (19.35 bp at 1 s) because XAUUSD moves are fat-tailed.
> A median-based block is a *policy* statement, not a claim that no tail trade could ever pay.

## 3. Markout profile (task VI), unconditional, all decision instants

Long side (short is the mirror), cost 0.914 bp:

| h | median gross markout | mean gross markout | median \|markout\| | cost-adjusted median |
|---|---|---|---|---|
| 100 ms | −0.011 bp | +1.252 bp | 0.537 bp | −0.925 bp |
| 250 ms | −0.011 bp | +1.252 bp | 0.539 bp | −0.925 bp |
| 500 ms | 0.000 bp | +1.252 bp | 0.581 bp | −0.914 bp |
| 1 s | 0.000 bp | +1.252 bp | 0.639 bp | −0.914 bp |
| 2 s | −0.011 bp | +1.253 bp | 0.751 bp | −0.925 bp |
| 5 s | −0.022 bp | +1.253 bp | 1.042 bp | −0.936 bp |
| 30 s | −0.046 bp | +1.257 bp | 2.395 bp | −0.960 bp |

Reading: the **median** mid-to-mid markout is ≈ 0 at every horizon (no free directional drift), while
the **mean** is ≈ +1.25 bp — entirely a fat-tail effect (a few very large moves). After cost, the
median is negative everywhere. **Markout quantifies "entry right then reverse"; it does not remove it.**

## 4. Adverse selection by state (task VII)

Median AS (bp; positive = price moved against the filled long):

| h | low-spread | mid-spread | high-spread | low-vol | mid-vol | high-vol |
|---|---|---|---|---|---|---|
| 100 ms | −0.046 | −0.011 | **+0.045** | 0.000 | −0.011 | **+0.023** |
| 1 s | −0.126 | 0.000 | **+0.074** | 0.000 | −0.011 | **+0.025** |
| 5 s | −0.296 | −0.012 | **+0.230** | 0.000 | −0.023 | **+0.093** |
| 30 s | −0.670 | −0.035 | **+0.530** | 0.000 | −0.065 | **+0.231** |

Finding: adverse selection is **state-dependent** — it is positive (unfavourable) in the
**high-spread / high-volatility** states and grows with the horizon, reaching ~+0.5 bp at 30 s in
high-spread states. It is small in the median and **second-order to cost** overall, but it is the
mechanism that makes aggressive taking worst exactly when spreads are widest.

> **Data-quality caveat (declared):** the `mean_as_bp` fields in `results.json` are contaminated by
> end-of-sample clipping (entries whose forward window runs past the last tick all map to the final
> tick, giving identical values across horizons). Only the **medians** above are reliable; the means
> are reported in the JSON as raw and must not be quoted. Fix = drop entries whose `t+h` exceeds the
> segment end. This does not affect §2 or the cost verdict.

## 5. Failure-mode classification (task VII), two pre-declared diagnostic rules only

| rule | n | median gross | median net | TYPE1 wrong dir | TYPE2 spread cost | WIN |
|---|---|---|---|---|---|---|
| momentum_sign | 4,211,693 | −0.046 bp | −0.960 bp | 2,355,497 | 1,113,390 | 742,806 |
| reversal_sign | 4,211,693 | +0.046 bp | −0.868 bp | 1,930,182 | 1,350,127 | 931,384 |

Classifier precedence (`execution/execution_quality.py`): if gross ≤ 0 → `TYPE1`; else if net > 0 →
`WIN`; else attribute to the **largest cost component**. Because spread is by far the dominant cost
here, the positive-gross-but-net-negative cases land in `TYPE2` (spread eaten). `TYPE5`
(adverse selection), `TYPE6` (fill failure) and `TYPE7` (generic execution-cost failure) do not appear
for these rules: fill was assumed perfect (no L2), and slippage/latency were not injected into this
diagnostic. **No bare WIN/LOSS is reported anywhere.**

## 6. What this establishes

1. Cost/move > 1 for **h ≤ 2 s** → those horizons are blocked by cost, on the median.
2. Median markout ≈ 0 and median AS ≈ 0 → the edge is not hiding in "entry right then reverse"
   for *unconditional* entries; the story is cost, not adverse selection, at the median.
3. Adverse selection is real but *conditional* (high-spread/high-vol), and grows with horizon.
4. True OFI / microprice / queue / fill probability remain `DATA_GAP` on this feed.
