# V2 P1 RESIDUAL REPORT — 20260917 (G1)

## 3.1 Replay provenance (input_hash → source_hash)
- 实现：`replay_inputs.build_snapshot(..., provenance=)` 写入 `source_provenance`（每字段 `source/source_hash/data_ts`）；`shadow_run` 从 `pit_cache.get_asof("hist:XAUUSD:*", decision_ts)` 采集。
- `offline_replay` 强制：`source_provenance` 非空且每项 `source_hash` 为 64-hex，否则 `SOURCE_PROVENANCE_MISSING` / `SOURCE_PROVENANCE_INVALID`（fail-closed，不联网）。
- 测试：`test_replay_snapshot` 13/13（含 provenance missing/invalid）。
- **REPLAY_PROVENANCE = PASS**（`RESEARCH/V2_REPLAY_PROVENANCE_REPORT_20260917.md`）。

## 3.2 BLS / COT PIT
- 字段四时戳分离：`event_ts / publication_ts / retrieval_ts / data_ts`（agent2 macro contract）。
- BLS：`release_timestamp=null` → `point_in_time_confidence=low` → `macro_pit_risk += BLS`。
- COT：`publication_timestamp_unknown=True` → `cot.pit_status=UNKNOWN` → `macro_pit_risk += COT`。
- 关键性：`TRADE_CRITICAL_MACRO=(DXY,UST10Y,VIX)`；**BLS/COT 属 CONTEXT_ONLY**（不参与 gold_macro_state）。若未来提为 TRADE_CRITICAL，gate 会因 `macro_status!=OK` 阻止 TRADE。
- 未把 unknown publication 推断为 published；未把 retrieval 当 publication；未把 date-only 当 exact。
- **PIT(BLS/COT) = PIT_RISK（显式，不伪装 PASS）；非阻塞（CONTEXT_ONLY）**。

## 3.3 Shadow 运行期 OS 进程/网络证据
- 机制：`tools/runtime_audit.py`（采集 process tree / ESTABLISHED 远端端点 / python 子进程；标记 model/API/gateway 命中）。Shadow 期间随 cycle 采集。
- **RUNTIME_PROCESS_NETWORK = PASS(mechanism)**；正式产物 `V2_RUNTIME_PROCESS_NETWORK_AUDIT_YYYYMMDD.md` 于 Shadow 期间生成。

## 3.4 Dashboard residual
- 已验证：MT5 只读探测仍在；`BROKER_DEMO≠PAPER`；`ACCOUNT_TYPE` 正确；equity/balance 来自 ledger；sizing base 来自账户；无硬编码 $10,000；无 fake-zero；RUN_MODE/EXECUTION_MODE/HEALTH/PIT/FRESHNESS 见 `mode_info`。
- **DASHBOARD = PASS**（`test_dashboard_consistency` 12/12）。

## 结论
GATE_1_P1_RESIDUAL = PASS。
