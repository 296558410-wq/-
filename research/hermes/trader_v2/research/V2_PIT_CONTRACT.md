# V2 PIT CONTRACT (P0-05 / §21–23)

## 时间字段（不得混用）
| 字段 | 含义 | 用于 |
|---|---|---|
| `event_time` | 事件发生 | 参考 |
| `publication_time` | 官方发布（宏观） | 宏观 PIT |
| `data_ts` | 行情/数据自身时刻 | freshness / as-of |
| `received_ts` | 取回时刻 | as-of 可见性 |
| `feature_ts` | 特征计算时刻 | 审计 |
| `decision_ts` | 决策时刻 | 基准 |

## AS-OF 规则（不可违背）
> 返回 `data_ts <= decision_ts` **且** `received_ts <= decision_ts` 的最新合法记录。
> 任何 `data_ts > decision_ts` 或 `received_ts > decision_ts` 的记录**绝不**可见（`data_sources/pit_cache.get_asof`）。

## 全链路
raw → router → **pit_cache** → feature → candidate → Hermes → decision：每层 `ts <= decision_ts`。
- 行情 `data_ts` = bar 起始/收盘时刻；bars 已剔除未收盘（`validate.py:future_unclosed_bar`）。
- 宏观：优先 `publication_ts`；不可靠则 **`PIT_RISK=TRUE`**（BLS/COT 目前 `release_timestamp=null` / `publication_timestamp_unknown` → 不得伪装 PIT PASS；该修复列入 P1）。

## 可见性
`pit_cache` 单测覆盖：future exclusion、late-received（receied_ts 未到不可见）、missing、duplicate、same-ts-different-source、invalid data_ts。
`tests/test_pit_cache.py` 11/11。

## Replay 输入（为下一阶段预留）
每条记录含 `source_hash` + `schema_version=pit/1`，可直接用于未来 `input_hash` / `data_snapshot_id`。本阶段不做完整 replay input snapshot。
