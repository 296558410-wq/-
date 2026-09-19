# CPU vs GPU 自动基准（真实计时）

- 时间: 2026-09-04 18:53:38 中国标准时间
- GPU available: True | VRAM 4.3GB

方法：同一任务同一 seed，CPU/GPU 各重复 3 次取最优；auto 列为 dispatcher 实际决策（可能=CPU 或 GPU）。

| workload | CPU ms | GPU ms | speedup | auto→ | 决策原因 |
|---|---|---|---|---|---|
| bootstrap n=1000 (iter=2000) | 12.7 | 3.9 | 3.3x | gpu | est 16MB fits budget |
| permutation n=1000 (iter=2000) | 19.7 | 4.2 | 4.7x | gpu | est 16MB fits budget |
| bootstrap n=10000 (iter=2000) | 123.9 | 32.0 | 3.9x | gpu | est 160MB fits budget |
| permutation n=10000 (iter=2000) | 197.1 | 35.5 | 5.6x | gpu | est 160MB fits budget |
| bootstrap n=100000 (iter=2000) | 1286.1 | 324.5 | 4.0x | gpu | est 1600MB fits budget |
| permutation n=100000 (iter=2000) | 2051.8 | 375.1 | 5.5x | gpu | est 1600MB fits budget |
| monte_carlo paths=100000 (steps=128) | 332.1 | 257.8 | 1.3x | gpu | est 51MB fits budget |
| monte_carlo paths=1000000 (steps=128) | 3345.9 | 514.3 | 6.5x | gpu | est 512MB fits budget |

注：GPU 启动/拷贝开销在小规模占主导 → auto 会选 CPU；规模越大 GPU 优势越明显；若某行 GPU 更慢则如实保留数字。