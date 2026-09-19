# Environment Baseline Report

> Generated: 2026-09-04 15:45 UTC (Asia/Shanghai 2026-09-04 23:45)
> Scope: one-shot XAUUSD AI Quant research environment baseline (infrastructure only - no alpha research).
> Machine-readable source: reports/env_baseline_info.json, reports/env_smoke_results.json, reports/env_smoke_*.json

## 1. System
| OS | Microsoft Windows 11 专业版 build 10.0.26200 |
| Machine | DESKTOP-LQ0B8O3 (Surface Laptop Studio, i7-11370H 4C/8T) |
| RAM | 31.8 GB |
| Disk C: | free 862 GB / 952.6 GB |

## 2. GPU
| GPU | NVIDIA RTX A2000 Laptop GPU (CC 8.6) |
| NVIDIA Driver | 591.55 (driver CUDA 13.1     |) |
| VRAM | 4096 MiB |
| CUDA Toolkit | NOT installed by design (torch pip wheel bundles CUDA runtime cu126) |

## 3. Python
| System Python | 3.14.7 (C:\Users\surface\AppData\Local\Programs\Python\Python314) - UNMODIFIED |
| Python 3.12 | 3.12.10 (used for research venv) |
| Research venv | C:\AIQuant\.venv\Scripts\python.exe |
| pip | pip 26.2.1 from C:\AIQuant\.venv\Lib\site-packages\pip (python 3.12) |

## 4. Key package versions (research venv)
| package | version |
|---|---|
| torch | n/a |
| numpy | 2.5.2 |
| pandas | 3.0.5 |
| scipy | 1.18.1 |
| statsmodels | 0.15.0 |
| scikit-learn | 1.9.0 |
| xgboost | 3.4.1 |
| lightgbm | 4.7.0 |
| pyarrow | 25.0.1 |
| polars | 1.44.1 |
| numba | 0.67.0 |
| fastparquet | 2026.5.0 |
| openpyxl | 3.1.5 |
| matplotlib | 3.11.1 |
| pytest | 9.1.1 |
| pytest-cov | 7.1.0 |
| ruff | 0.16.6 |
| black | 26.5.1 |
| MetaTrader5 | n/a |
| duckdb | 1.5.5 |
| bottleneck | n/a |
| backtesting | 0.6.6 |
| vectorbt | 1.1.0 |
| pandera | 0.33.1 |
| hydra-core | 1.3.6 |
| python-dotenv | 1.2.3 |
| PyYAML | n/a |

## 5. Toolchain
| git | git version 2.55.0.windows.3 |
| git-lfs | git-lfs/3.7.1 (GitHub; windows amd64; go 1.25.1; git b84b3384) |
| openssh | OpenSSH_for_Windows_9.5p2, LibreSSL 3.8.2 |
| node | v24.18.1 |
| npm | 11.16.0 |
| powershell | 5.1.26100.9168 |
| openclaw | 2026.7.1-2 (from C:\Users\surface\dtlopenclaw\tools\openclaw\node_modules\openclaw\package.json) |
| MT5 terminal | C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe |

## 6. Torch/CUDA runtime
- torch 2.14.0+cu126 (cuda build 12.6), device NVIDIA RTX A2000 Laptop GPU
  - matmul4096: cpu 0.3494s / gpu 0.0655s -> 5.33x
  - montecarlo_pi: cpu 0.3876s / gpu 0.0338s -> 11.48x
  - bootstrap_400x100k: cpu 0.1997s / gpu 0.0273s -> 7.31x
  - permutation_400x100k: cpu 0.648s / gpu 0.0958s -> 6.76x

## 7. Protected invariants
- System Python 3.14.7 untouched; C:\AIResearch untouched; C:\AIQuant intact.
- No order functions invoked on MT5; no account state mutated; Dukascopy: no bulk download (single-file smoke only).

See reports/env_smoke_results.json for per-check machine-readable results.