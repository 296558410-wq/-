# AIQuant 工作站建设 — 通宵任务 V1 报告 (overnight_report.md)

> 生成：2026-09-04 07:40 (Asia/Shanghai)
> 机器：DESKTOP-LQ0B8O3 · Windows 11 Pro (26100) · Surface Laptop Studio

## 0. 执行摘要

| 阶段 | 结果 |
|---|---|
| Python 3.12.10 专用环境 + venv + TUNA 镜像 | ✅ 昨晚完成 |
| 软件栈批量安装（~120 包，含 torch 2.14.0+cu126 2.6GB） | ✅ 昨晚完成 |
| **torch 加载修复（WinError 1114/126 → VC 运行库卫星 DLL 缺失）** | ✅ 今晨修复 |
| GPU 基准 (A–M) | ✅ 12 PASS / 2 SKIP / 1 FAIL（如实记录） |
| 自动化测试套件 (7 类) | ✅ **7/7 PASS** |
| 数据层合成数据端到端管道 | ✅ 产出 XAUUSD tick1s/M1/M5/H1 parquet |
| 本报告 | ✅ |

昨晚执行在 torch 安装后中断：进程在 00:21 下载完 torch 轮子后被杀/退出，
且 **torch 无法 import**（事件日志显示 00:37 起反复崩溃）。今晨会话完成全部收尾。

---

## 1. 关键故障与修复：torch 2.14.0+cu126 无法加载

**症状链**（按修复顺序）：
1. `import torch` → `OSError: [WinError 1114]` 于 `c10.dll`；
   事件日志定位：崩溃模块 = `C:\Windows\SYSTEM32\msvcp140.dll` (14.36.32532.0, 2023-11)，
   c0000005 —— **系统 VC 运行库过旧**（2026 版 torch 需要更新的 MSVC runtime）。
2. 修复 msvcp140 后 → `[WinError 126]` 于 `torch_cpu.dll`；
   PE 导入表分析（pefile）：torch_cpu.dll 依赖 **`VCRUNTIME140_THREADS.dll`** ——
   全机不存在（python.org 安装器只带 vcruntime140(+_1)，VC redist 从未装过）。

**修复方式（免管理员、零系统修改、可复现）**：
- 下载官方 `vc_redist.x64.exe`（aka.ms/vs/17/release，24.4MB，微软 CDN 5.9MB/s）
- 解包 burn bundle → 内含 CAB → 提取 amd64 CRT 文件（版本 **14.44.35211**）
- 复制 9 个 DLL（msvcp140 全家族 + vcruntime140(+_1/_threads) + concrt140）到
  `Python312\` 目录（应用目录 DLL 搜索优先级高于 System32）
- 结果：`torch 2.14.0+cu126 · CUDA True · RTX A2000 Laptop · CC (8,6) · cuDNN 9.1`

备份留存：`C:\AIQuant\cache\vcredist\`（含安装包与解包文件），
过程已登记 `environment/environment.md §6`。

**教训**：2026 版 torch（cu126 轮子）需要完整且较新的 MSVC 运行库；
新装机若从未装过 VS/VC redist，必踩此坑。根治可后续装官方 VC redist（需管理员一次）。

---

## 2. GPU 基准结果（真实计时，reports/gpu_benchmark.md）

设备：NVIDIA RTX A2000 Laptop **4GB** · CC 8.6 (sm_86) · Driver 591.55 · CUDA 12.6 runtime (轮子自带)

| 测试 | 结果 | CPU | GPU | 加速 |
|---|---|---|---|---|
| D 矩阵乘 2048² FP32 | PASS | 64.1 ms | 21.4 ms | **3.0x** |
| F FP16 矩阵乘 | PASS | — | 9.1 ms | (Tensor Core) |
| F BF16 矩阵乘 | PASS | — | 9.3 ms | (Tensor Core) |
| E FP64 矩阵乘（参考） | PASS | — | 323.6 ms | 远慢于 FP32 → 高精度走 CPU |
| H Monte Carlo 2M×128 路径 | PASS | 15.1 s | 0.60 s | **25.2x** |
| I Bootstrap 2000 迭代 | PASS | 8.4 s | 0.77 s | **10.9x** |
| I Bootstrap 10000 迭代 | PASS | 40.7 s | 3.9 s | **10.5x** |
| I Permutation 10000 迭代 | PASS | 31.7 s | 1.9 s | **16.9x** |
| J XGBoost GPU (50 rounds) | PASS | — | 714 ms | device=cuda 生效 |
| K LightGBM GPU | **FAIL** | — | — | PyPI 轮子未编译 CUDA（Windows 需 OpenCL/自编译）；如实记录，CPU 照常可用 |
| L Numba CUDA | SKIP | — | — | 按决策不装 CUDA Toolkit |
| M CuPy | SKIP | — | — | 未安装，暂不引入 |

**A2000 4GB 能力结论（本报告核心交付）**：
- ✅ **能（强烈建议 GPU）**：Monte Carlo / Bootstrap / Permutation / Shuffle 等
  批量随机模拟 —— 10–25x，直接改写秒级/分钟级瓶颈；中小矩阵；FP16/BF16 张量运算；
  小模型 DL/ML 训练与推理（单样本 ≤ ~1.5GB 显存预算）。
- ⚠️ **能但注意**：XGBoost GPU 可用；LightGBM GPU 需自编译 CUDA 版（暂不值得）。
- ❌ **不能/不建议**：>4GB 单样本的大模型训练/推理；FP64 大规模矩阵（走 CPU）；
  Numba CUDA / CuPy 原生工具链（需 Toolkit，按决策不装）。
- 适配改动：原基准脚本 MC/Bootstrap/Permutation 的 GPU 内核按块处理（统计等价，
  峰值显存 <1.5GB），并修复了原脚本 FP16/BF16 参数顺序 bug —— 均已在
  `benchmarks/gpu_benchmark.py` 注明。

---

## 3. 自动化测试（tests/run_all.py → tests/results_20260904_073211.md）

**PASS=7 / FAIL=0**
1. Environment: python3.12 + 核心导入 ✅
2. GPU: CUDA available + CC 8.6 ✅
3. Data: parquet 写读 + DuckDB SQL 查询 ✅
4. Quant: research_engine.permutation_test 逻辑 ✅
5. Stats: CPUBackend.bootstrap seed 可复现 ✅
6. ML: XGBoost 回归 ✅
7. Pipeline: 合成数据端到端（gen_synthetic → run_pipeline）✅

---

## 4. 数据层现状（V1 第 X 阶段基础）

合成管道已产出（data/synthetic/，含 MANIFEST.json 数据版本清单）：
- `XAUUSD_tick1s.parquet` 4.1 MB（1s tick 合成）
- `XAUUSD_M1.parquet` 84 KB · `M5` 21 KB · `H1` 6.8 KB
- `data/cache/aiq_meta.duckdb` 元数据缓存

研究引擎骨架（research_engine/）：backends (CPU/GPU 可切换) · validation
(permutation/bootstrap) · engine —— 测试已验证。

---

## 5. 目录与文档清单

- `C:\AIQuant\`：19 子目录结构 + README.md + .gitignore（未 git init，待批）
- `docs/architecture.md` · `docs/software_stack.md`（CORE/OPTIONAL/LATER/REJECT 全表）
- `environment/requirements.in`（顶层依赖）· `requirements.txt`（全量锁定）· install.log
- `tools/snapshot_env.py`（硬件/驱动/版本快照）
- `reports/machine_baseline.md` · `reports/gpu_benchmark.md` · `reports/overnight_report.md`

---

## 6. 遗留事项（需你决定 / 需你操作）

1. **SSH 公钥网页添加（需你操作）**：GitHub → Settings → SSH keys 粘贴
   `ssh-ed25519 ...`（内容在上轮消息；完成后我跑 `ssh -T git@github.com` 验证）
2. **Git 仓库初始化**：C:\AIQuant 是否 `git init` + 首次提交（我会先写 .gitignore 校验敏感项）
3. **VC 运行库根治（可选）**：管理员装一次官方 VC++ Redistributable
4. **LightGBM GPU（可选）**：需要时自编译 CUDA 轮子或维持 CPU
5. 旧电脑数据迁移通道：防火墙规则 `OC-Transfer-8000` 保留未删，接收服务已停
6. 下一步候选（按你原 V1 框架）：CPU/GPU 分工矩阵落地 → research_engine 扩展 →
   真实 MT5 数据接入方案（需 MT5 终端确认）
