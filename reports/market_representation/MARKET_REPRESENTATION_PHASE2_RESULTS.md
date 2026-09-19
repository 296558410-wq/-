# MARKET STATE REPRESENTATION — PHASE 2 RESULTS (descriptive · 2026-09-05)

> Scope: frozen Registry B0-B4/C1-C12 x FXTM(M1/M5/H1)+DUKA(M1/M5/H1); frozen Stability A-H
> weights/thresholds; redundancy(|corr|>=0.90) & re-encoding(R2>=0.95) checks.
> Output is KEEP / PARTIAL / REJECT / UNCERTAIN with rationale only; NO 'best representation' claim.
> Governance: RESEARCH_GATE PASS(11/11) · manifest REP_P2 · SI/PML updated.

## Verdict table

| candidate | family | verdict | rationale | SI |
|---|---|---|---|---|
| C1_disp_z | price displacement | **KEEP** | cells=6 mean=0.80 min=0.56 blcorr=0.36 | SI-REP2-008 |
| C2_range_frac | range/compression | **KEEP** | cells=6 mean=0.76 min=0.72 blcorr=0.82 | SI-REP2-009 |
| C2_comp_ratio | range/compression | **KEEP** | cells=6 mean=0.94 min=0.91 blcorr=0.61 | SI-REP2-010 |
| C3_rv_ratio | realized vol | **KEEP** | cells=6 mean=0.90 min=0.87 blcorr=0.72 | SI-REP2-011 |
| C3_rv_level | realized vol | **KEEP** | cells=6 mean=0.73 min=0.67 blcorr=0.69 | SI-REP2-012 |
| C4_shock_z | vol shock | **KEEP** | cells=4 mean=0.89 min=0.75 blcorr=0.81 | SI-REP2-013 |
| C5_act_pct | activity | **KEEP** | cells=3 mean=0.83 min=0.82 blcorr=0.36 | SI-REP2-014 |
| C5_act_delta | activity | **KEEP** | cells=3 mean=0.81 min=0.81 blcorr=0.19 | SI-REP2-015 |
| C6_spread_state | liquidity/spread | **KEEP** | cells=4 mean=0.91 min=0.85 blcorr=0.17 | SI-REP2-016 |
| C7_persist_w | directional persistence | **KEEP** | cells=6 mean=0.94 min=0.89 blcorr=0.45 | SI-REP2-017 |
| C7_run_len | directional persistence | **KEEP** | cells=4 mean=0.81 min=0.77 blcorr=0.19 | SI-REP2-018 |
| C8_recov | path efficiency/recovery | **REJECT** | redundant-with-baseline (mean |corr|=1.00) | SI-REP2-019 |
| C9_mfe_mae | excursion/MFE-MAE | **KEEP** | cells=4 mean=0.95 min=0.93 blcorr=0.11 | SI-REP2-020 |
| C10_accel | acceleration | **KEEP** | cells=4 mean=0.82 min=0.81 blcorr=0.71 | SI-REP2-021 |
| C12_dstate | state delta | **REJECT** | redundant-with-baseline (mean |corr|=1.00) | SI-REP2-022 |

## Notes & limits
- KEEP = descriptively stable AND non-redundant with baselines (composite >=0.70, min>=0.55, mean |corr vs nearest baseline| <0.90, no re-encoding). KEEP is NOT 'correct market state representation' (portability/semantics are Phase 3+; representation != state != prediction).
- REJECT (redundant-with-baseline): C8_recov & C12_dstate implementations coincided with B3_eff / B4_vec_norm (corr 1.00) - implementation-level degeneracy, not formula-level; true recovery / delta-B4 formulas need V2 re-registration before implementation.
- re-encoding: 0 candidates (none reproducible R2>=0.95 from return lags).
- redundant pairs: 30 (mostly intra-family, e.g., C3_rv_ratio <-> C3_rv_level and vol-family).
- Uniformly high within-window stability (A/C/D/E/H) warns that these sub-scores weakly discriminate among smooth features; discrimination here comes from redundancy/baseline gaps and min-cell. Phase 3 must add portability & semantic criteria.
- Baselines B0-B4: reference only (not keep-candidates).

## Full SI record set

SI-REP2-001 SI-REP2-002 SI-REP2-003 SI-REP2-004 SI-REP2-005 SI-REP2-006 SI-REP2-007 SI-REP2-008 SI-REP2-009 SI-REP2-010 SI-REP2-011 SI-REP2-012 SI-REP2-013 SI-REP2-014 SI-REP2-015 SI-REP2-016 SI-REP2-017 SI-REP2-018 SI-REP2-019 SI-REP2-020 SI-REP2-021 SI-REP2-022
