# V2 REPLAY PROVENANCE REPORT — 20260917 (P1 residual 3.1)

## 关系链
```
decision → input snapshot (runtime/replay_inputs.build_snapshot)
          → input_hash (= context_hash)
          → source_provenance[field] = {source, source_hash(64-hex), data_ts}
          → offline_replay 校验 provenance → 缺失/非法 = fail-closed
```
- `source_provenance` 由 `pit_cache.get_asof(field, decision_ts)` 采集（不可变、PIT）。
- snapshot 整体 `snapshot_hash` 覆盖 provenance → 篡改 provenance 必致 `SNAPSHOT_HASH_MISMATCH`。
- 重新赋值 provenance 后 `SOURCE_PROVENANCE_MISSING`（空）/`SOURCE_PROVENANCE_INVALID`（非 64-hex）。
- replay 不访问网络（`replay_inputs` 无 http import；`test_replay_snapshot` 断言）。

## 测试
`test_replay_snapshot` 13/13。

## 结论
REPLAY_PROVENANCE = PASS。
