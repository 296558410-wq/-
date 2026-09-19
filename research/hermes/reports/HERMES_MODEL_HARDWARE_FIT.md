# HERMES MODEL HARDWARE FIT（硬件适配实测）

> 生成：2026-09-05 · 实测命令输出（非记忆）· 交叉验证于 HERMES_ENVIRONMENT_AUDIT.md

---

## 1. 实测硬件（本机真实值）

| 项 | 实测值 | 说明 |
|---|---|---|
| GPU | RTX A2000 Laptop，**4096 MiB 总量，3965 MiB 可用** | 4GB，远低于 Hermes "8GB 舒适线" |
| VRAM 驱动/CUDA | driver 591.55；CUDA 可用（nvidia-smi 正常） | 但 4GB 只够 ~3B Q4 |
| CPU | 8 逻辑核（4C/8T） | i7-11370H，无 AVX-512 |
| RAM | 31.8GB 总量，**19.3GB 空闲** | 可 CPU 跑 7-14B，但慢 |
| 磁盘 | 857GB 可用 | 模型下载无压力 |
| 本地模型工具 | **无**（无 ollama/llama-server/llama-cli） | 需自装 |
| Hermes CLI | **无 `hermes` 二进制在 PATH** | 托管运行时是桌面端功能，CLI 不可触发 |

---

## 2. 逐候选硬件适配

| 候选 | 权重(Q4) | 能否入 4GB VRAM | 实际运行方式 | 预估速度（本机） |
|---|---|---|---|---|
| Phi-4-mini 3.8B | ~2.3GB | **能**（约 2GB 入 VRAM，余量紧） | GPU 部分 + 余量 CPU | 6-8 tok/s |
| Qwen3 8B | ~4.4GB | 否（超 VRAM） | 全 CPU（32GB RAM 可） | 3-4 tok/s |
| Qwen3 14B | ~8GB | 否 | 全 CPU | 1-2 tok/s（不可用） |
| >27B MoE | >12GB | 否 | 全 CPU 极慢 | <1 tok/s（不可用） |

---

## 3. 三个决定性问题

### Q1：4GB VRAM 能干什么？
能完整容纳 ~3B Q4 模型（Phi-4-mini 3.8B 勉强）。**7B Q4（~4.4GB）放不进 4GB VRAM**，
必然走 CPU。→ 本机没有任何"纯 GPU 加速"的 7B+ 推理可能。

### Q2：64K context（任务书硬门槛）在本机是否可行？
- 可行但**代价高**：64K context 的 KV cache 在 CPU Q4 下占用数百 MB~GB 级 RAM，且每 token 都要
  扫 KV cache → 速度进一步下降。Hermes 托管运行时"保证 64K（溢出放系统 RAM）"，但那是以速度为代价。
- 结论：64K **技术上可达，但"64K + 慢 + Q4 掉崖"三重叠加**，研究可用性存疑。

### Q3：CUDA/后端能力？
CUDA 可用（driver 591.55），但 4GB VRAM 限制使 CUDA 加速只对 ≤3B 模型有意义。llama.cpp
支持 CUDA + CPU 混合（offload），本机可用，但瓶颈在 CPU 内存带宽（DDR 平台，非 HBM）。

---

## 4. 硬件适配结论

- **没有任何模型能在本机以"可用速度 + 64K + 可接受质量"同时满足 quant 研究的核心需求。**
- 最接近的折中：**Phi-4-mini 3.8B**（唯一能部分入 VRAM 的、推理分尚可的模型），速度 6-8 tok/s，
  但绝对推理能力 + Q4 掉崖使其**不足以做 quant 主脑**。
- **Qwen3 8B**（推理/编码更强）只能 CPU 3-4 tok/s，64K context 下实际 <2 tok/s，不可作为日常研究主脑。
- 结论指向：本机本地模型**只能作窄任务辅助**，不能作 Primary Quant Brain。
