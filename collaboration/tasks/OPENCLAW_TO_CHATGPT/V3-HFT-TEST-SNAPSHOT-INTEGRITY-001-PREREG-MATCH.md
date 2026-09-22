# PREREGISTRATION MATCH AUDIT

`generated_utc = 2026-09-22T06:15:00Z`

| item | expected | actual | verdict |
|---|---|---|---|
| PREREGISTRATION_SHA256 | `e273be091fc38cda0274cd2fededaeb28c2a11cd3398db770a6023d54faf5dc3` | `e273be091fc38cda0274cd2fededaeb28c2a11cd3398db770a6023d54faf5dc3` | **MATCH** |
| document hashes (22 docs) | stored | recomputed | **MATCH** (0 mismatched) |
| MODEL_SPEC_HASH | `a98717dc424b0acaf0f33c01707dff6be540e2c941ee7a4da9fa803a4d31b53c` | unchanged | **MATCH** |
| FEATURE_SCHEMA_HASH | `2b99c68b3a4a126e27301efbc03c68f6b485fc85565cefcc2a7301a77cc271fc` | unchanged | **MATCH** |
| COST_MODEL_HASH | `6f116cfb2d63bedf6e364e9b5a6c6e15f194f91114e9d0c1780fa4d869cdf0aa` (`CALIBRATION_20RT_20260921`) | unchanged | **MATCH** |
| PARAMETER_REGISTRY | 30 params, TBD = 0 | 30 / 0 | **MATCH** |
| parameter categories | FIXED / ESTIMATED_ON_TRAIN / NOT_ALLOWED_TO_ESTIMATE_ON_TEST | unchanged | **MATCH** |
| TEST_BOUNDARY | RULE_LOCKED | RULE_LOCKED, hash PENDING | **MATCH** |

No protected file was modified; the preregistration directory was read only.
