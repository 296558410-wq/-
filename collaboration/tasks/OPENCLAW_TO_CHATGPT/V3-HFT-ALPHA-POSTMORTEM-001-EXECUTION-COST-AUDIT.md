# EXECUTION_COST_AUDIT — V3-HFT-ALPHA-POSTMORTEM-001

- Mode: **AUDIT_ONLY / READ_ONLY**. Uses the completed calibration; **no new order, no re-calibration.**

## Verdict: **EXECUTION_COST_BOTTLENECK = YES (severe at h ≤ 5 s)**

## Frozen cost facts

```text
spread      ≈ 0.18 USD / round-trip
commission  ≈ 0.22 USD / round-trip
total       ≈ 0.40 USD / round-trip  ≈ 0.914 bp at ~4,376 USD/oz
measured median spread = 0.15 USD = 0.343 bp
```

## Cost vs the typical move to capture

Using the frozen `move_scale.json` (median |forward mid move|, bp):

| horizon | median abs move (bp) | n | **cost / move** |
|---|---|---|---|
| 50 ms | 0.979 (unreliable; n=2,129) | 2,129 | 0.93 |
| 200 ms | 0.162 | 1,247,508 | **5.64×** |
| 1 s | 0.346 | 2,276,477 | **2.64×** |
| 5 s | 0.582 | 2,777,738 | **1.57×** |
| 30 s | 1.269 | 2,794,486 | 0.72× |
| 5 min | 4.168 | 2,783,694 | 0.22× |
| 1 h | 16.065 | 2,657,339 | 0.06× |

## Core answer

> For XAUUSD on this feed, at holding periods ≤ 5 s the round-trip cost is **1.6×–5.6×** the median
> absolute price move. The best *gross* edge estimated anywhere in the frozen search is **+0.096 bp**,
> i.e. **~9.5× smaller than the 0.914 bp cost**. Cost alone explains the negative net edge at short
> horizons; no model can pay a toll larger than the typical move it tries to capture.

This is consistent with the per-sample cost actually applied in the run (`cost_bp_mean ≈ 0.914`).

## Note

The 50 ms row is shown for completeness but is statistically unreliable (only 2,129 clean samples,
an order of magnitude smaller than any other row) — see `DATA_CAPABILITY`/`DATA_SNAPSHOT` for why
the 50 ms horizon is `DATA_INSUFFICIENT`.
