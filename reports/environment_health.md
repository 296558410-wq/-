# RESEARCH ENVIRONMENT HEALTH CHECK

> 2026-09-04 15:45 UTC | honest statuses (no masking)

| area | status | detail |
|---|---|---|
| A. System | PASS | system audit (OS/CPU/RAM/disk/nvidia-smi) ok |
| B. Python | PASS | venv python 3.12.10 imports ok (stats/ml/ts modules PASS) |
| G. Data | PASS | parquet/duckdb/pyarrow available; data read paths verified (ts_leak/tick roundtrip) |
| L. OpenClaw | PASS | OpenClaw executed venv python + pytest + research scripts via exec (this session) |
| M. API | PASS | DeepSeek minimal call -> see env_smoke_deepseek.json |
| N. Security | PASS | git_smoke no secrets tracked; .gitignore covers .env/keys/data/cache/logs; no remotes |
| O. Reproducibility | PASS | requirements-lock.txt + fixed seeds + JSON results archived in git |
| C. GPU [gpu_bench] | PASS |  |
| D. Statistics [stats_smoke] | PASS |  |
| E. ML [ml_smoke] | PASS |  |
| F. Backtest [backtest_smoke] | PASS |  |
| H. Tick/Microstructure [tick_smoke] | PASS |  |
| J. Dukascopy [duka_smoke] | WARN |  |
| I. MT5 [mt5_smoke] | WARN |  |
| K. Git [git_smoke] | PASS |  |