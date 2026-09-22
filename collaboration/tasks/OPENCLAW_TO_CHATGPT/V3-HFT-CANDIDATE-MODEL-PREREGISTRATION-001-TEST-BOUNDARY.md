# TEST BOUNDARY (frozen rule; hash pending data collection)

`PREREGISTRATION_ID = V3-HFT-PREREG-001` · `STATUS = RULE_LOCKED / HASH_PENDING`

## The contamination ruling (recorded honestly)

```text
WINDOW 2026-09-07 .. 2026-09-21 has ALREADY BEEN VIEWED.
  Viewed by : V3-HFT-L1-EXECUTION-EDGE-DISCOVERY-001 (TEST fold evaluated once, results reported)
  Also viewed by : V3-HFT-L1-STATISTICAL-POWER-CLOSURE-001 (as aggregate dependence/power input)
=> That window is DEMOTED to DEVELOPMENT_CONTAMINATED.
=> It may NOT serve as the evaluation set for this preregistration.
```
Per §六十 (`TEST_SET_VIEWED => TEST_CONTAMINATED`), this is recorded rather than hidden. Continuing to
call that window "TEST" would be a protocol violation.

## The locked test-boundary RULE

```text
TEST_START          = the first usable FXTM session strictly AFTER
                      PREREGISTRATION_UTC (2026-09-22T06:20:00Z)
TEST_LENGTH         = 10 usable sessions (usable = a session segment with >= 200,000 ticks)
TEST_END            = determined by TEST_LENGTH, not by a calendar date chosen after inspection
TEST_INSTRUMENT     = XAUUSD, same account family, same cost model
TEST_LOCKED_HASH    = PENDING_NOT_YET_COLLECTED
```
The rule is frozen now; the hash can only be computed when the data exists. Recording
`PENDING_NOT_YET_COLLECTED` is the honest state — not a blocked item and not a fabricated hash.

## Immutability after opening

Once `TEST_BOUNDARY` is materialised and hashed:

```text
TEST_BOUNDARY = IMMUTABLE
FORBIDDEN after opening: feature selection, threshold selection, model selection, horizon selection,
                         exit tuning, any re-estimation of TRAIN/DEV parameters on TEST.
```

## Allowed reasons to modify the protocol (§四十二)

```text
DATA_CORRUPTION
CODE_BUG
LOOK_AHEAD_DISCOVERY
BROKER_COST_CORRECTION
SNAPSHOT_INTEGRITY_FAILURE
```
Each requires: `STOP -> DOCUMENT -> VERSION_BUMP -> RE-PREREGISTER`. Silent repair is forbidden.

## Implication for round 1

Because the evaluation set does not yet exist, round 1 **cannot** produce a final verdict now. The
protocol's purpose is precisely to fix, in advance, how that verdict will be computed once the data
arrives. No experiment may be run against the contaminated window and reported as OOS.
