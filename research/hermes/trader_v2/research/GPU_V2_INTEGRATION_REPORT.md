# GPU_V2_INTEGRATION_REPORT — V2 研究计算后端接入

> 日期: 2026-09-13 · GPU: RTX A2000 Laptop 4GB · BASE_COMMIT `c8bf910` · 只读原始数据 · 未改交易执行/风控/Hermes。

## 0. 结论
**FINAL_CLASSIFICATION = B (PARTIALLY_VALIDATED)**
GPU 已作为 V2 **研究计算后端**正确接入且**不进入交易执行/风控链**：CPU/GPU 数值一致、OOM/不可用回退正常、无数据泄漏、V1/V2 执行隔离、无统计定义改动。
**但只有部分研究任务值得 GPU**：bootstrap / Monte Carlo / microbar(≥5M) 收益显著；**rolling 边际**；**permutation 不值得**（argsort 显存大且更慢）；归约/sort 不接入。

## 1. 交付
- 新增 `trader_v2/research_compute/`：`dispatcher.py`（AUTO/CPU/GPU）、`cpu_backend.py`、`gpu_backend.py`（**转发** `gpu_accelerator`，无第二套实现）、`validation.py`（CPU 独立验证硬门）、`chunking.py`（4GB 安全）、`rng.py`、`benchmark.py`、`README.md`。
- 新增 `tests/test_research_compute.py`（**26/26 PASS**）。
- 新增 `research/GPU_V2_BENCHMARK.md`、本报告、`research_compute/gpu_v2_results.json`。

## 2. 接入算子
| 优先级 | 算子 | 状态 | AUTO 判定 |
|---|---|---|---|
| P0 | bootstrap | ✅ GPU | work≥1e8 → GPU |
| P0 | Monte Carlo | ✅ GPU | work≥1e8 → GPU |
| P0 | permutation | ✅ 已接入但 **AUTO=CPU** | 实测 GPU 更慢/显存大 |
| P0 | 大规模 rolling | ✅ GPU | 15M≤n≤40M |
| P1 | tick→microbar | ✅ GPU | 2M≤n≤40M |
| P1 | realized volatility | ✅ GPU | 2M≤n≤40M |
| P1 | spread statistics | ✅ GPU | 2M≤n≤40M |
| P1 | 大规模 feature engineering | ✅ GPU | 2M≤n≤40M |
| 暂缓 | sort / 小 sum·mean / 小 elementwise / 非分块 rolling / GPU bipower / 大 quantile / fp64 优化 | ⛔ 未接入 | — |

## 3. AUTO 规则（`dispatcher.py`，阈值来自 benchmark）
- CUDA 不可用/无算子 → CPU；重采样(permutation) → CPU；bootstrap/MC：work=n_iter×n ≥ 1e8 → GPU；
- rolling：15M≤n≤40M → GPU（<15M 实测 GPU 仅 0.6–0.7x）；elem(microbar/spread/returns/rv/features)：2M≤n≤40M → GPU；
- **GPU OOM** → `empty_cache` → 缩块重试 → 仍失败 → **CPU fallback**（记 `fallback_reason`）。**不因 GPU 可用而强制 GPU**。

## 4. 验证与回退（已测，`tests/test_research_compute.py`）
- CPU/GPU 一致（elementwise: rolling/quotes/returns/rv/microbar）**PASS**；重采样用统计一致（statistical）**PASS**。
- RNG 可复现（CPU/GPU 各自 same seed → 同结果）**PASS**；chunk 等价 **PASS**。
- OOM→CPU fallback **PASS**；GPU 不可用→CPU **PASS**；结果不符→`COMPUTE_VALIDATION_FAILED` **PASS**。
- 时间对齐 / 无未来泄漏（trailing rolling 未来改动不影响过去）**PASS**。
- 隔离：V1 / broker(执行) / ledger / replay 无耦合 **PASS**；运行前后 `config/v2_config.json` 哈希不变 **PASS**。

## 5. 真实数据验证（只读）
- `data/live_fxtm`（1,041,204 ticks）：microbar CPU==GPU（桶/close 逐项一致）；spread_bps CPU==GPU **PASS**。
- `data/staging_duka`（本次用 15.6M）：见 GPU_V2_BENCHMARK。
- 未修改/未重生成任何原始数据。

## 6. 真实研究案例等价（§15）
案例：`live_fxtm` 1m → `signal=sign(logret_t)` vs `fwd=logret_{t+1}`；A=up(n=3256) / B=down(n=3331)，共 6601 bars。
| 量 | CPU | GPU | 一致 |
|---|---|---|---|
| mean(A−B) | 1.779e-4 | — | — |
| median(A−B) | 1.400e-4 | — | — |
| std(A)/std(B) | 2.659e-4 / 2.572e-4 | — | — |
| q05/q50/q95(A) | [-2.573e-4, 6.627e-5, 4.926e-4] | — | — |
| bootstrap CI(mean A) | [7.832e-5, 9.662e-5] | [7.875e-5, 9.621e-5] | ✅（RNG 噪声内）|
| permutation p (diff) | 0.0005 | (AUTO=CPU) | ✅ |
| BH-FDR raw | [0.022, 0.004, 0.6806, 0.002, 0.6826] | 同 | ✅ |
| BH-FDR adj | [0.1098, 0.01, 0.6826, 0.0025, 0.6826] | 同 | ✅ |
**结论一致（误差在预定义 tolerance 内）。**

## 7. Benchmark（wall-clock，AUTO 有效区间；详见 GPU_V2_BENCHMARK.md）
| 任务 | n | CPU ms | GPU e2e ms | speedup | VRAM peak |
|---|---|---|---|---|---|
| monte_carlo | 1M | 994 | 41 | **24.2×** | 772MB |
| monte_carlo | 20M | (cap) | 287 | — | 2.2GB |
| bootstrap | 100k×1000 | 1399 | 90 | **15.6×** | 2.4GB |
| microbar | 5M | 125 | 78 | 1.6× | 325MB |
| microbar | 20M | 485 | 260 | 1.9× | 1.3GB |
| rolling_std | 5M | 156 | 252 | 0.62× | 320MB |
| rolling_std | 20M | 600 | 332 | 1.8× | 1.3GB |
| permutation | 200k×1000 | 16200 | (AUTO=CPU) | — | — |
> kernel-only 见 `gpu_accelerator/REPORT.md`（headline 结论：归约/滚动类 kernel 极快，但 end-to-end 受 H2D/D2H 主导；**不得把 kernel speedup 当真实加速**）。**所有 VRAM 峰值 ≤2.5GB**，无 WDDM 越界。

## 8. 越界修复（§8，唯一改动到 `gpu_accelerator` 的地方，原因说明）
接入过程中实测到两类越界（WDDM paging），已修复：
1. `permutation` 峰值 **14GB→7.2GB→（AUTO 改 CPU）**：`core/gpu_backend.py` permutation 分块系数 `×8×2 → ×8×4`（按 rand4B+idx8B+out4B 保守估）；并将 AUTO 固定为 CPU（GPU 本就更慢）。
2. `monte_carlo` 峰值 **4.3GB→2.5GB**：分块系数 `×3 → ×6`。
改动仅限 `gpu_accelerator/core/gpu_backend.py`（分块系数），**未改任何算子定义/结果语义**；理由：任务 §8 明确禁止重复 `rolling_std@100M → 6.4GB WDDM` 这类执行。

## 9. 隔离证据
- `research_compute/*.py` 扫描：无 `trader_v1` 耦合；无 `BrokerDemoExecutor/FXTMDemoAdapter/order_send/place_market_order`；无 `import ledger`；无 `import replay`。
- GPU 层只产生**研究数值结果**；不写 Ledger、不下单/改单/平仓/改 SL/TP/volume/risk、不碰 broker state、不触 MT5。
- Hermes 仍是唯一决策者；GPU 不产生 TRADE、不改 Decision Contract、不绕 Risk Gate。

## 10. 核心问题（§21）
1. **每个核心研究任务省了多少 wall-clock？** bootstrap ≈**15×**、Monte Carlo ≈**24×**（大规模重采样）——这是真收益；microbar ≈**1.6–1.9×**（≥5M）；rolling ≈**0.6–1.8×**（仅 ≥15M 才正收益）；permutation **0×**（GPU 更慢，AUTO 用 CPU）；归约/sort **不接入**。
2. **有没有改变任何研究结论？** 没有。CPU/GPU 一致（elementwise 预定义容差内；重采样统计一致）；真实案例（bootstrap CI / permutation p / BH-FDR）**逐项一致**。
3. **GPU 故障时是否安全？** 安全。OOM→释放→缩块→重试→**CPU fallback**；GPU 不可用→CPU；结果不符→`COMPUTE_VALIDATION_FAILED`（不进入 Hermes）。已测。
4. **GPU 是否完全没进入交易执行和风控链？** 是。只做研究计算；与 Paper/Broker/Ledger/Replay/Risk Gate **零耦合**（源码扫描 + 无 import）。

## 11. 最终分类
**B — PARTIALLY_VALIDATED**：接入正确、数值一致、回退安全、无泄漏、隔离成立、性能有**部分**实际收益（重采样/大规模 microbar）；但 rolling 收益边际、permutation 不值得、其余暂缓。
> 按要求**保留可用部分，不强行扩大**；未自动改策略/阈值/参数、未开 LIVE、未下 Broker 单、未创建下一模块。
