# Final Decision — V3-HFT-L1-STATISTICAL-POWER-CLOSURE-001

## Final state

> ## `B — POWER_NOT_YET_CLOSED`
> Per-horizon: **5 s / 10 s / 30 s / 60 s = POWER_CLOSED (already sufficient)** ·
> **5 min = POWER_NOT_YET_CLOSED** (needs ~294 calendar days for a +0.20 bp net edge).
> States C and D are **ruled out** by the measurements (see below).

## Required data (analytic, empirical σ)

| horizon | effective_N now | σ (bp) | req eff_N (δ=0.20, p80) | headroom | req calendar days (δ=0.20) | verdict |
|---|---|---|---|---|---|---|
| 5 s | 148,226 | 1.181 | 274 | **541×** | 0.1 | POWER_CLOSED |
| 10 s | 74,108 | 1.586 | 494 | **150×** | 0.3 | POWER_CLOSED |
| 30 s | 24,914 | 2.707 | 1,439 | **17×** | 2.9 | POWER_CLOSED |
| 60 s | 12,452 | 3.695 | 2,679 | **4.6×** | 10.8 | POWER_CLOSED |
| 5 min | 2,220 | 8.161 | 13,069 | **0.17×** | **294.3** (≈9.7 months) | **POWER_NOT_YET_CLOSED** |

Sensitivity: at δ = +0.10 bp the 5 min requirement becomes ~1,177 calendar days (~3.2 years); at
δ = +0.50 bp it falls to ~47 days. At δ = +0.20 bp with the FDR m=140 penalty it is ~23,791 effective
samples (~536 calendar days).

## Why not C or D

```text
C POWER_NOT_ECONOMICALLY_REACHABLE : rejected for 5s-60s (already powered; extra data is free of
                                     charge as the collector runs anyway) and not established for
                                     5min: 294 days is long but bounded and finite.
D POWER_STRUCTUREALLY_LIMITED      : rejected by measurement. effective_N grows ~linearly
                                     (5s: +4,118 / usable day; 5min: +62 / usable day);
                                     overlap is fully explained by rho = h/median_dt;
                                     methods A and B agree (EFFECTIVE_N_UNCERTAIN = FALSE);
                                     residual ACF after non-overlapping sampling is negligible.
```

## The dominant finding (which is not about power)

**Statistical power is not the binding constraint.**

1. The data already carries **2,220–148,226 effective observations**; the previous task's
   `effective_N 0…37` counted **trades produced by the threshold rule**, not available samples.
2. The measured net edge is **negative at every horizon** (≈ −1.1 bp unconditional), against a
   **0.914 bp** round-trip cost; the economic bar is a gross ≥ **1.14 bp**.
3. Therefore more data would **sharpen a negative estimate**, not create an edge. Collection is
   justified only to close the 5 min power gap — never as a path to profitability.

## The 12 required answers (§三十五)

```text
Q1  raw/effective/independent N per horizon .... see the table above (raw 7,285,000; eff 2,220-148,226)
Q2  block length .............................. 10 ticks (~2.7 s), frozen once, no per-horizon tuning
Q3  dependence structure ...................... benign: overlap fully explained by rho; ACF dies after
                                                one non-overlapping lag; no clustering failure
Q4  effective_N for 80/90/95% ................. computed per effect size (see power_simulation.md)
Q5  required raw ticks ........................ computed (data_requirement.csv): e.g. 5min δ0.20 = 42.9M
Q6  required quote events ..................... equal to required raw ticks (1 tick = 1 quote update)
Q7  required usable days ...................... e.g. 5min δ0.20 = 211.9 usable days
Q8  required calendar days .................... 294.3 (coverage_ratio_days = 0.72)
Q9  weeks / months ............................ 5s-60s: 0 (already met) ; 5min δ0.20: ~42 weeks (~9.7 months)
Q10 is 500 effective_N enough? ................ NO as a general rule: it is a minimum operational
                                                gate. Enough for 5s-60s at δ>=0.20; NOT enough for
                                                5min (needs 13,069).
Q11 requirement after FDR ..................... x1.82 N multiplier (m=140); 5min δ0.20 -> 23,791
Q12 is continued collection worth it? ......... For 5min only, and as a POWER closure, not as an
                                                alpha search. Value judgement belongs to ChatGPT.
```

## Data-investment view (§三十七)

| collection | 5 s eff_N gained | 5 min eff_N gained | reaches δ=0.20 target? |
|---|---|---|---|
| +1 week | ≈ 20,752 | ≈ 434 | 5s–60s yes · 5min no |
| +1 month | ≈ 83,007 | ≈ 1,735 | 5min still no |
| +3 months | ≈ 269,771 | ≈ 5,639 | 5min still no |
| +6 months | ≈ 539,542 | ≈ 11,279 | 5min ≈ reaching (needs ~62/day) |

(5 s/10 s/30 s/60 s already exceed their requirements today.)

## Preserved prior-artifact traceability (§四十)

```text
LABEL_GAP_GUARD_BUG = FIXED_IN_PREVIOUS_TASK
MECHANICAL_SIGNAL   = REJECTED
TAIL_DEPENDENCE     = OBSERVED
```
Prior files preserved and untouched: `l1_execution_edge/experiment_results_v1_no_gapguard.json`,
`l1_execution_edge/diagnostics.json`, `l1_execution_edge/fdr_results.json`,
`l1_execution_edge/final_decision.md`.

## Next step

```text
STOP.  No alpha replication. No forward. No demo. No live. No new model/feature/data source/MT5.
WAIT_FOR_CHATGPT_FINAL_AUDIT
```

The only defensible follow-up is a **5 min power closure** (~294 calendar days at a +0.20 bp
hypothesis), and only if the group judges that horizon worth 10 months of passive collection —
noting that the current measured edge there is negative.
