# PIT_VALIDATION_REPORT — 无未来泄漏验证

- 时间: 2026-09-14T11:14:33.267473+00:00

- 5m: n=1442, 未收盘(未来)bar=0, 单调递增=True, src=local_fxtm
- 15m: n=484, 未收盘(未来)bar=0, 单调递增=True, src=local_fxtm
- 60m: n=122, 未收盘(未来)bar=0, 单调递增=True, src=local_fxtm
- 4h: n=32, 未收盘(未来)bar=0, 单调递增=True, src=local_fxtm
- 1d: n=5, 未收盘(未来)bar=0, 单调递增=True, src=local_fxtm

- 语义: `signal@close[t]`、`execution@open[t+1]`（bar 由已冻结 tick 生成，最后一根未收盘 bar 被剔除）。
- 重采样确定性: 同一输入两次生成 bar 时间戳完全一致（见 test_data_sources §5）。
- 宏观: cache 只保存“取回时刻已知”的值；**永不**用更晚取回覆盖更早历史；不写未来时间戳。
- **PIT = PASS**