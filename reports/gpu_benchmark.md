# GPU Benchmark Report（真实结果）

- 时间：2026-09-04 07:31:21 中国标准时间
- 机器：DESKTOP-LQ0B8O3 | Windows-11-10.0.26100-SP0
- GPU：NVIDIA RTX A2000 Laptop 4GB (CC 8.6) | Driver 591.55 (CUDA 13.1)

## 结果

| 测试 | 状态 | 详情 |
|---|---|---|
| A_cuda_available | PASS | torch 2.14.0+cu126 cuda.is_available=True cuda=12.6 |
| B_device | PASS | NVIDIA RTX A2000 Laptop GPU / VRAM 4.29GB |
| C_compute_capability | PASS | CC 8.6 / sm_86 |
| D_matrix_fp32_2048 | PASS | CPU 64.1ms / GPU 21.4ms / speedup 3.0x |
| F_FP16_matmul | PASS | GPU 9.1ms (dtype=FP16) |
| F_BF16_matmul | PASS | GPU 9.3ms (dtype=BF16) |
| E_FP64_matmul_ref | PASS | GPU FP64 323.6ms（预期远慢于 FP32，高精度统计建议 CPU） |
| H_monte_carlo_2Mx128 | PASS | CPU 15081ms / GPU 599ms / speedup 25.2x |
| I_bootstrap_2000it | PASS | CPU 8405ms / GPU 774ms / speedup 10.9x |
| I_bootstrap_10000it | PASS | CPU 40679ms / GPU 3862ms / speedup 10.5x |
| I_permutation_10kit | PASS | CPU 31712ms / GPU 1873ms / speedup 16.9x |
| J_xgboost_gpu | PASS | 50 rounds 714ms (device=cuda) |
| K_lightgbm_gpu | FAIL | LightGBMError: CUDA Tree Learner was not enabled in this build.
Please recompile with CMake option -DUSE_CUDA=1 (NVIDIA GPUs) or -DUSE_ROCM=1 (AMD GPUs) (Windows 需 OpenCL，预期走 CPU) |
| L_numba_cuda | SKIP | Numba CUDA target 需要 CUDA Toolkit；按决策当前不安装 Toolkit → 跳过 |
| M_cupy_cuda12x | SKIP | ModuleNotFoundError: No module named 'cupy' → 未安装/不可用，暂不引入 |

## A2000 4GB 能力结论

- **能**：Monte Carlo/Bootstrap/Permutation 批量并行（实测加速见上表）、中小规模矩阵、FP16/BF16、小模型 DL/ML
- **不能/不建议**：>4GB 显存占用的大模型训练、FP64 高精度统计（走 CPU）、依赖 CUDA Toolkit 的工具链（Numba CUDA/CuPy 原生编译）
- XGBoost/LightGBM GPU 实测见上表（失败即如实记录，不强行装 Toolkit）