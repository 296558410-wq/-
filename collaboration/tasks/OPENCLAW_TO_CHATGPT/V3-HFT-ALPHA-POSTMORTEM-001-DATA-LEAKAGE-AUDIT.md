# DATA_LEAKAGE_AUDIT — V3-HFT-ALPHA-POSTMORTEM-001

- Mode: **AUDIT_ONLY / READ_ONLY**. Does not change `V3-HFT-ALPHA-DISCOVERY-001`.
- Inputs frozen: freeze sha256 `557bcc3c96338c1261f8a5b70371a6a679ff61ec433fbd24234aabf782b8a4d0`,
  report sha256 `976333c528f06f8fa76a5c661af692774e1964a681cafff6f9891dc9392f0881`.
- Code audited: `alpha/tools/run_experiments.py`, `alpha/features/feature_builder.py`.

## Verdict: **PASS**

No data leakage into model/threshold/cost/latency **selection**. One documented minor exposure
(TEST metrics computed during the screen loop) that cannot inflate a negative result.

## Checks

| check | result | evidence |
|---|---|---|
| chronological folds | PASS | `run_experiments.py:41-43` — TRAIN 08-04..08-22, VAL 08-24..09-05, TEST 09-07..09-22 by UTC day number; no shuffling |
| purge + embargo = h | PASS | `run_experiments.py:256-258` — `purge = (train & fwd_day>=VAL_start) \| (val & fwd_day>=TEST_start)` |
| feature causality (PIT) | PASS | `feature_builder.compute_tick_features` uses only `ts<=i` (rolling/lag); grid as-of = `searchsorted(ts,grid,'right')-1` = last tick ≤ instant |
| normalization train-only | PASS | `run_experiments.py:314,424` — `mu,sd = Xi[train].mean(0)/std(0)`, applied to val/test |
| no interpolation | PASS | `forward_labels` picks the first real tick ≥ `t+h`; gaps ⇒ undefined/not-clean, never filled |
| TEST used for selection | **PASS (none)** | `run_experiments.py:343-348` selects family by `val_net_edge_usd`; model loop selects on VAL; no selection key uses TEST |
| threshold selection | PASS | position threshold = frozen cost `c_bp`, not tuned on TEST |
| cost / latency selection | PASS | cost tiers and latency grid frozen; latency uses real ticks via `searchsorted`, not re-optimised |
| overlap handling | PASS | `ρ=h/median_dt`; `effective_n=n/max(ρ,1)`; non-overlapping t-test; block bootstrap block `=max(50,10ρ)` |
| TEST metrics observed during screening | **MINOR_EXPOSURE** | `run_experiments.py:319` `for tag,msk in (("val",va),("test",te))` computes BOTH folds per candidate; `test_net_edge_*` is written into `models/model_manifest.json:iteration_log` |

## Note on the minor exposure

TEST was evaluated and logged on every one of the 30 screen iterations
(`model_manifest.json → iteration_log[*].test_net_edge_bp`). It was **never used to select**
anything (selection key is VAL-only). This weakens the literal freeze statement
"TEST is never used before §13", but it is **non-blocking** for the NO_ALPHA verdict:
peeking can only help *find* an edge, and none was found (0/30 survive BH-FDR q=0.05).

## Recommended remediation (for future studies, not applied here)

Evaluate TEST only once, after selection is final, and omit TEST columns from the screen log.
