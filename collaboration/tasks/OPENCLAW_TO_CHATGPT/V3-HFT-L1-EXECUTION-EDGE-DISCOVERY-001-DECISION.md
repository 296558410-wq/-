# Final Decision — V3-HFT-L1-EXECUTION-EDGE-DISCOVERY-001

## Status

> ## `DATA_INSUFFICIENT`
> with sub-classification **DATA_LIMITED (dominant) + SIGNAL_LIMITED + COST_LIMITED**.
>
> No `SUPPORTED_EXECUTABLE_EDGE`. No `EXECUTABLE_ALPHA_CANDIDATE`.
> This task does **not** authorise forward, demo, live or expansion.

## Why `DATA_INSUFFICIENT` and not `NO_SUPPORTED_L1_EDGE`

The pre-registered acceptance rule requires `effective_N >= 500` (condition 6). After VAL-only
selection, **every** horizon's chosen configuration has `effective_N = 0…37` on TEST:

```text
5s   eff_N 37    |  10s eff_N 2   |  30s eff_N 0   |  60s eff_N 1   |  5min eff_N 0
```

All nine regime cells at every horizon are `INSUFFICIENT_SAMPLE` (each < 500).
Because the required power is never reached, the honest statement is **not** "no edge exists";
it is that **this dataset cannot resolve the question at these horizons with this design**.

## Why the positive means are not evidence of edge

1. **The predictor is the entry spread.** `corr(pred, spread_bp) = −0.9994`; the mechanical
   expression `pred = −spread/2` alone produces **0 trades**, so the signal only crosses the cost
   threshold through amplified spread. It is not a forecast of the future mid.
2. **Tail dependence.** Positive horizons have `median > 0` but the top 10% of trades carry ~70% of
   total PnL; win rates are 0.58–0.64 on 108–432 trades.
3. **Not robust.** A 1.25× cost removes almost all trades at 30 s (108 → 6) and 60 s (234 → 40) and
   turns 30 s negative (−0.60 bp). Condition 8 fails.
4. **Selection instability.** The selection statistic (VAL mean) picked configurations whose trade
   counts do not reproduce out of sample (VAL ≥ 100 trades → TEST 92–708 with effective_N ≤ 37).
5. **A real bug was found and fixed mid-task:** the label implementation lacked a
   session/segment guard, letting forward windows cross weekend/session gaps. The re-run with the
   guard changed the selected families (SPREAD survives) but not the conclusion. Both runs are kept
   (`experiment_results_v1_no_gapguard.json`, `experiment_results.json`).

## Acceptance conditions (§二十二) — 0 of 10 satisfied

| # | condition | result |
|---|---|---|
| 1 | gross edge > 0 | only at 30s/60s/5min, on <500 trades |
| 2 | net edge > 0 | only on the same tiny samples |
| 3 | OOS net edge > 0 | unstable across horizons/models |
| 4 | bootstrap CI not entirely < 0 | CI not meaningful at n<50 |
| 5 | BH-FDR q ≤ 0.05 | "35/196 significant" but on heavy-tailed, mechanically-selected samples |
| 6 | effective_N ≥ 500 | **FAILS at every horizon (0–37)** |
| 7 | not tail-driven | **FAILS (top10% ≈ 70%)** |
| 8 | survives 1.25× cost | **FAILS at 30 s / 60 s** |
| 9 | no future data | passes (PIT verified) |
| 10 | direction consistent with markout | passes (unit-tested) |

## Result

```text
Q15 — is there a NET EXECUTABLE EDGE?           NO (no configuration meets the acceptance bar)
Q8  — driven by a few tail events?              YES (top10% ≈ 70% of PnL)
Q7  — horizon with the most complete evidence?  5 s (largest n and eff_N, and negative net)
```

## Next step

**STOP.** Per §二十九/§三十五:
* no forward, no demo, no live, no expansion;
* no model/complexity increase, no further indicator sweep (§二十八);
* if the group wants to pursue it, the next action is a separate, explicitly authorised
  **independent replication** on a *larger/denser* sample (or a longer snapshot), because the binding
  limitation here is **statistical power**, not model capacity.

```text
WAIT_FOR_CHATGPT_FINAL_AUDIT
```
