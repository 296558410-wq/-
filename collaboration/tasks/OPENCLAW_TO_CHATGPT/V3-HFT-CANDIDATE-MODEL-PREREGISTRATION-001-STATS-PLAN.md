# STATISTICAL PLAN (frozen)

`PREREGISTRATION_ID = V3-HFT-PREREG-001` · `STATUS = LOCKED`

## Test hierarchy (§三十八)

```text
PRIMARY      : declared in advance, one per level (see below)
SECONDARY    : the same statistic at the other registered horizons
EXPLORATORY  : everything else, reported separately, NEVER promoted to primary
```
A statistically significant exploratory result may not become a primary finding after the fact.

```text
LEVEL-0 PRIMARY : cost_to_move map at h = 30 s
LEVEL-1 PRIMARY : discrimination (AUC) of realised cost_to_move at h = 30 s vs COST_ONLY
LEVEL-2 PRIMARY : NET_EDGE_PER_TRADE > 0 at h = 30 s after the full cost chain
LEVEL-3 PRIMARY : same-entry improvement in NET_EDGE_PER_TRADE from the conditional exit at h = 30 s
```
The primary horizon is **pre-chosen**, not selected from results.

## Required report fields (§三十五)

```text
NET_PNL · NET_EDGE_PER_TRADE · COST_COVERAGE · MAX_DRAWDOWN · TURNOVER · TRADE_COUNT
plus gross_edge, mean, median, std, p10, p25, p75, p90,
     top1% / top5% / top10% PnL shares
```
Win rate, profit factor and gross return are **insufficient alone** and must never be the headline.

## Uncertainty (required)

```text
- two-sided t-test on NON-OVERLAPPING observations
- moving-block bootstrap CI (statistics/BOOTSTRAP_PLAN.md)
- HAC / overlap-aware uncertainty where overlap remains
- BH-FDR across the declared family (statistics/FDR_PLAN.md)
- effective_N reported alongside raw_N (statistics/POWER_PLAN.md)
```

## Effective sample size (§三十六)

```text
raw_N = 10000 does NOT mean 10000 independent observations.
effective_N = n / max(1, rho) ,  rho = h / median_inter_tick_ms
For overlapping horizons (1s, 5s, 30s, 1min, 5min) the overlap correction is mandatory.
No CI may be quoted from a raw event count when events cluster.
```

## Conclusion classes (§四十四, frozen; three only)

```text
A  SUPPORTED_NET_EDGE
B  NO_SUPPORTED_NET_EDGE
C  DATA / POWER INSUFFICIENT
```
**C may never be written as B.** `NO_ALPHA` may be used **only** when
`SUPPORTED_DATA + ADEQUATE_POWER + COST_REALISTIC + OOS_VALID` all hold; otherwise the conclusion must
be `DATA_INSUFFICIENT` or `POWER_INSUFFICIENT`.

## Failed-result vocabulary (frozen in advance, §四十三)

```text
NO_NET_EDGE · COST_SENSITIVITY_FAILURE · OOS_FAILURE · FDR_FAILURE · POWER_FAILURE · DATA_FAILURE
```

## Stopping rules (§六十)

```text
DATA_LEAKAGE               -> HALT
SNAPSHOT_MUTATION          -> HALT
COST_MODEL_INCONSISTENCY   -> HALT
TEST_SET_VIEWED            -> TEST_CONTAMINATED (do not continue as if clean)
```
