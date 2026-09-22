# Economic Significance — V3-HFT-L1-STATISTICAL-POWER-CLOSURE-001

`AUDIT_ONLY / READ_ONLY / OFFLINE`. Machine twin: `cost_aware_power.csv`.

## The two conditions are different

```text
STATISTICAL_SIGNIFICANCE : net edge != 0 at alpha=0.05 with adequate power
ECONOMIC_SIGNIFICANCE    : net edge >= +0.10 USD/RT
```

A result can be statistically significant and economically worthless. This task measures the
**data required** to reach each; it does not claim either has been achieved.

## Unit conversion (using the canonical calibration)

```text
COST_MODEL           = CALIBRATION_20RT_20260921
0.40 USD / RT        = 0.914 bp at ~4,376 USD/oz
=> 1 bp              ~ 0.4376 USD / RT   (0.01 lot)
NET_EDGE_MIN         = +0.10 USD/RT      ~ +0.23 bp
```

## Gross edge required for economic significance, under cost stress

`gross_required = cost_tier + 0.23 bp`

| cost multiplier | spread+commission (bp) | **gross edge required (bp)** | net at that gross |
|---|---|---|---|
| 1.00× (baseline) | 0.914 | **1.144** | +0.23 bp (+0.10 USD/RT) |
| 1.25× | 1.143 | **1.373** | +0.23 bp |
| 1.50× | 1.371 | **1.601** | +0.23 bp |
| 2.00× | 1.828 | **2.058** | +0.23 bp |

> **Interpretation.** For a V3 L1 signal to be worth executing at all, the *gross* markout edge must
> exceed ≈ **1.14 bp** (and 2.06 bp under a 2× cost shock). The previous task measured best gross
> magnitudes around +0.45 bp at 5 s (and the unconditional long-side net was ≈ −1.1 bp at every
> horizon). **No configuration reached the economic bar.**

## Measured current state (inherited, not re-derived)

| horizon | current net mean (bp) | economically significant? |
|---|---|---|
| 5 s | ≈ −1.10 (unconditional) / −0.47 (rule) | NO |
| 10 s | ≈ −1.10 | NO |
| 30 s | ≈ −1.07 (unconditional) | NO |
| 60 s | ≈ −1.10 | NO |
| 5 min | ≈ −1.15 | NO |

Cost stress **never** improves these; adding data tightens the estimate but cannot move the mean.

## Consequence for the data question

Because the measured net edge is **negative** while cost is **positive and large relative to the
typical move**, additional data increases *precision*, not *profitability*. The power analysis below
therefore answers "could a +0.20 bp edge be detected?" — not "is there a +0.20 bp edge".

*(The `cost_aware_power.csv` written by the first driver pass used a rough 13.7 bp/USD factor for one
column; it has been regenerated with the calibration-derived 0.4376 USD/bp conversion above.)*
