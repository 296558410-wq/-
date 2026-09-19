# V2 REPLAY INPUT SNAPSHOT REPORT — 20260917 (P1-B)

## 问题
Replay 仅重放 ledger，**无法在没有网络/当前数据源/cache 的情况下重建 decision**。

## 修改
- `hermes.py`：抽出 **`decide_pure(ctx,a1,a2,source,llm_decision)`**（无副作用，live 与 replay 共用同一确定性路径）；`decide()` = decide_pure + 候选留痕（写 OPP_LEDGER）。行为不变。
- 新增 `runtime/replay_inputs.py`：
  - `build_snapshot(decision, ctx, a1, a2, cands, tags, health, freshness, price_space, risk, data_version, router_version)` → 冻结全部输入 + `snapshot_hash`（sha256，改内容必变）。
  - `write_snapshot(run_dir, snap)` → `<run>/inputs/<decision_id>.json`（immutable）。
  - `offline_replay(snap)` → 仅用 snapshot，走 `decide_pure`；返回 match。
- `runtime/shadow_run.run_cycle`：每 decision 写 input snapshot（不改变决策）。

## Fail-closed（offline_replay）
`SNAPSHOT_MISSING / SNAPSHOT_SCHEMA_MISMATCH / SNAPSHOT_MISSING_FIELD / WRONG_INSTRUMENT /
SNAPSHOT_INVALID_TS / SNAPSHOT_HASH_MISMATCH` → 拒绝；**绝不 re-fetch Yahoo/Sina/DXY/broker**。

## 测试
`tests/test_replay_snapshot.py` 11/11：TRADE/REJECT/WAIT 重建一致；确定性；hash 敏感；6 类 fail-closed；无网络 import。

## Snapshot 字段（§12）
decision_id/decision_ts/instrument/reference_market/strategy_version/data_version/router_version/
context_hash/input_hash/market_inputs/technical_features/macro_inputs/candidate/regime_tags/
gate_results/health/freshness/pit_status/price_space/risk_calculation/decision/snapshot_hash。

## 遗留
- `input_hash` 目前 = context_hash（后续可并入 pit_cache source_hash 形成更强 data_version）。
- snapshot 写入在 shadow/forward 阶段实际产生文件（当前系统锁定，未产生）。
