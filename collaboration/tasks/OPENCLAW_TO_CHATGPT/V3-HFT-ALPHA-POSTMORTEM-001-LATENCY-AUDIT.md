# LATENCY_AUDIT — V3-HFT-ALPHA-POSTMORTEM-001

- Mode: **AUDIT_ONLY / READ_ONLY**. Uses the frozen `backtest/latency_sensitivity.json`; **no new
  latency search.**

## Verdict: **NOT_LATENCY_BOUND**

Net edge (bp) by injected latency, executed on **real ticks** (entry at real ask/bid at `t+L`,
exit at real bid/ask at `t+h+L`, minus commission):

| horizon | 0 ms | 50 ms | 100 ms | 250 ms | 500 ms | 1000 ms |
|---|---|---|---|---|---|---|
| 1 s (B0/MLP) | **−1.004** | −0.938 | −0.838 | −0.831 | −0.811 | −1.256 |
| 30 s (B3/Ridge) | **−0.880** | −0.888 | −0.888 | −0.674 | −0.690 | −0.782 |
| 5 min (B4/GBT) | **−0.771** | −0.769 | −0.769 | −0.769 | −0.769 | −0.767 |

## Decisive point

The frozen §10 rule: *if 0 ms is already negative, latency is not the sole cause.*

> Net edge is **already negative at 0 ms latency on every horizon**. Adding 0 → 1000 ms of latency
> moves the result only modestly (≤ ~0.25 bp, non-monotonic). Therefore **execution latency is a
> secondary effect, not the binding constraint**. The sign of the result is set by cost, not by delay.

If the same table had shown `0 ms positive → 100 ms negative`, this would be an
`EXECUTION_LATENCY_BOTTLENECK`; it does not.
