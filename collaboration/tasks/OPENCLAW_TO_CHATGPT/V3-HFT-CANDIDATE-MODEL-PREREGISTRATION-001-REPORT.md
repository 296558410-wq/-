# Final Pre-Registration Report — V3-HFT-PREREG-001

`PREREGISTRATION_ONLY / READ_ONLY`. No experiment was run. No parameter was tuned on data.

---

## Outcome

```text
PREREGISTRATION_READY
```
with one **open, honestly-declared** item: `TEST_LOCKED_HASH = PENDING_NOT_YET_COLLECTED`
(the evaluation window does not exist yet — see §Test boundary below).

## §六十一 completion criteria

| # | criterion | state |
|---|---|---|
| 1 | CAND-001 = PREREGISTERED | **PASS** (`protocol/CAND-001_PROTOCOL.md`) |
| 2 | CAND-002 = PREREGISTERED | **PASS** (`protocol/CAND-002_PROTOCOL.md`) |
| 3 | CAND-003 = PREREGISTERED | **PASS** (`protocol/CAND-003_PROTOCOL.md`) |
| 4 | LEVEL-0 = PREREGISTERED | **PASS** (`protocol/LEVEL_0_COST_BASELINE.md`) |
| 5 | TEST_BOUNDARY = LOCKED | **PASS (rule locked)**; hash pending future data |
| 6 | COST = LOCKED | **PASS** (0.914 bp; legacy anchors forbidden) |
| 7 | LABELS = LOCKED | **PASS** (4 objects; LABEL_ONLY rule) |
| 8 | FEATURE_SCHEMA = LOCKED | **PASS** (15 features listed) |
| 9 | STATISTICAL_PLAN = LOCKED | **PASS** (primary/secondary/exploratory; A/B/C classes) |
| 10 | LOOKAHEAD_POLICY = LOCKED | **PASS** (timeline + 5 automated assertions) |
| 11 | OOS_POLICY = LOCKED | **PASS** (promotion ladder; no TEST selection) |
| 12 | PREREGISTRATION_SHA256 = GENERATED | **PASS** (`registries/preregistration_manifest.json`) |

## Test boundary — the honest ruling

```text
2026-09-07 .. 2026-09-21  was VIEWED by V3-HFT-L1-EXECUTION-EDGE-DISCOVERY-001
                          and used as a dependence/power input by ...-STATISTICAL-POWER-CLOSURE-001
=> DEMOTED to DEVELOPMENT_CONTAMINATED
=> TEST = a FUTURE window: the first 10 usable sessions strictly after 2026-09-22T06:20:00Z
=> TEST_LOCKED_HASH = PENDING_NOT_YET_COLLECTED
```
Continuing to label the viewed window as "TEST" would be `TEST_CONTAMINATED`. The rule is frozen now;
the hash can only be computed once the data exists. **This is the one item ChatGPT must rule on.**

## Parameters — every TBD resolved (or explicitly allocated)

No parameter remains `TBD`. Each is classified (see `registries/parameter_registry.json`):

```text
FIXED                        horizons, windows (200t / 50t), grid (1 s, freshness 5 s),
                             purge/embargo (300 s), min_raw_N (500), min_effective_N (per horizon),
                             cost tiers, FDR (BH q=0.05, m=20), bootstrap (2000, block rule, seed),
                             decision margin rule, MIN_MARKOUT_HORIZON_MS (500), baseline set,
                             CAND-002 decision threshold (1.0, from the cost identity, not from data)
ESTIMATED_ON_TRAIN           CAND-001 ridge/tree hyper-parameters (fixed defaults, not searched),
                             CAND-002 EXPECTED_MOVE_bp, CAND-003 E0 and lambda
NOT_ALLOWED_TO_ESTIMATE_ON_TEST   all of the above
```
`MODEL_NOT_READY_FOR_EXPERIMENT` is **not** invoked: every required parameter has a value or an
explicit estimation allocation.

## Registered structures (summary)

```text
LEVEL-0   cost_to_move(h) = cost_bp / median_abs_move(h)          -> a MAP, never a strategy
LEVEL-1   H002 economic-gate hypothesis; COST_MULTIPLE < 1 -> TRADEABLE else WAIT (no direction)
LEVEL-2   EXPECTED_GROSS_EDGE - EXPECTED_EXECUTION_COST - EXPECTED_ADVERSE_SELECTION = NET_EDGE
          TAKE iff NET_EDGE - UNCERTAINTY_MARGIN > 0 ; impact/opportunity/fill = DATA_GAP (never 0)
LEVEL-3   E(t) = E0*exp(-lambda t)  [MODEL_ASSUMPTION]
          EXIT iff E[remaining] - EXIT_COST - MARGIN < 0 ; TOTAL_COST = ENTRY + EXIT
          4-class taxonomy + UNCLASSIFIED ; same-entry comparison required
```

## Registered analytical discipline

```text
hierarchy        primary / secondary / exploratory (no post-hoc promotion)
effective_N      reported with raw_N; no CI from raw clustered counts
power            per-horizon minimum effective_N frozen; 300 s is expected INSUFFICIENT_POWER
FDR              BH q=0.05 over 20 primary tests; exploratory family reported separately
bootstrap        moving block, 2000 resamples, block = max(50, 10*rho), seed 20260922
conclusions      A SUPPORTED_NET_EDGE | B NO_SUPPORTED_NET_EDGE | C DATA/POWER INSUFFICIENT
                 (C may NEVER be written as B; NO_ALPHA needs data+power+cost+OOS all valid)
stopping rules   DATA_LEAKAGE / SNAPSHOT_MUTATION / COST_MODEL_INCONSISTENCY -> HALT
                 TEST_SET_VIEWED -> TEST_CONTAMINATED
```

## What this task establishes, and what it does not

```text
ESTABLISHED : how CAND-001/002/003 will be proven effective or ineffective, frozen in advance
NOT ESTABLISHED : any edge, any profitability, any readiness to trade
```
The registered measurement may well return `NO_SUPPORTED_NET_EDGE` or `DATA/POWER INSUFFICIENT` —
both are legitimate outcomes that this protocol is designed to report honestly.

## Final state

```text
WAIT_FOR_CHATGPT_FINAL_AUDIT
```
No automatic entry into training, backtesting, replication, paper, demo, forward or live.
