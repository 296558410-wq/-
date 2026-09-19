# GPU_V2_BENCHMARK — V2 研究计算基准

- 时间(UTC): 2026-09-13T07:31:18.197579+00:00
- GPU: NVIDIA RTX A2000 Laptop GPU
- 口径: wall-clock（best-of-2）；**end-to-end**（含 H2D/D2H）。kernel-only 见 gpu_accelerator/REPORT.md。

| op | n | cpu_ms | gpu_e2e_ms | speedup | vram_peak_mb |
|---|---|---|---|---|---|
| rolling_std | 1,000,000 | 30.86 | None | None | 0.0 |
| microbar | 1,000,000 | 23.65 | 79.25 | 0.3 | 65.1 |
| monte_carlo | 1,000,000 | 994.37 | 41.1 | 24.19 | 772.0 |
| bootstrap | 200,000 | 1372.83 | 131.78 | 10.42 | 2400.9 |
| permutation | 200,000 | 16258.98 | None | None | 0.0 |
| rolling_std | 5,000,000 | 155.69 | 251.51 | 0.62 | 320.0 |
| microbar | 5,000,000 | 124.57 | 77.54 | 1.61 | 325.3 |
| monte_carlo | 5,000,000 | None | 118.04 | None | 2168.5 |
| bootstrap | 200,000 | 1387.8 | 89.84 | 15.45 | 2400.9 |
| permutation | 200,000 | 16078.53 | None | None | 0.0 |
| rolling_std | 10,000,000 | 303.14 | 423.73 | 0.72 | 640.0 |
| microbar | 10,000,000 | 247.82 | 146.69 | 1.69 | 650.7 |
| monte_carlo | 10,000,000 | None | 179.46 | None | 2187.5 |
| bootstrap | 200,000 | 1394.53 | 92.74 | 15.04 | 2400.9 |
| permutation | 200,000 | 16185.88 | None | None | 0.0 |
| rolling_std | 20,000,000 | 599.66 | 332.04 | 1.81 | 1280.0 |
| microbar | 20,000,000 | 485.36 | 260.47 | 1.86 | 1302.3 |
| monte_carlo | 20,000,000 | None | 287.1 | None | 2227.5 |
| bootstrap | 200,000 | 1393.62 | 90.01 | 15.48 | 2400.9 |
| permutation | 200,000 | 16211.83 | None | None | 0.0 |
| rolling_std | 50,000,000 | None | None | None | 0.0 |
| microbar | 50,000,000 | None | None | None | 0.0 |
| monte_carlo | 50,000,000 | None | 890.07 | None | 2347.5 |
| bootstrap | 200,000 | 1401.12 | 90.45 | 15.49 | 2400.9 |
| permutation | 200,000 | 15996.92 | None | None | 0.0 |
| rolling_std | 100,000,000 | None | None | None | 0.0 |
| microbar | 100,000,000 | None | None | None | 0.0 |
| monte_carlo | 100,000,000 | None | 1493.52 | None | 2548.0 |
| bootstrap | 200,000 | 1399.34 | 89.62 | 15.61 | 2400.9 |
| permutation | 200,000 | 16721.7 | None | None | 0.0 |
