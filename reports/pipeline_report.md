# Pipeline 端到端验证报告

- 时间：2026-09-04T10:57:36.134960+00:00
- DuckDB 统计：{'n_bars': 288, 'first_ts': Timestamp('2026-01-05 08:00:00+0800', tz='Asia/Shanghai'), 'last_ts': Timestamp('2026-01-06 07:55:00+0800', tz='Asia/Shanghai'), 'avg_spread_bp_est': 2.8689, 'close_std': 57.52}
- 特征行数：268
- 回测：Sharpe=7.619 MaxDD=-0.0478
## 结论：管线 Generate→Parquet→DuckDB→Feature→Signal→Backtest→Report 全部跑通