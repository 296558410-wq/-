# HERMES MODEL BENCHMARK（模型实测基准）

> 生成：2026-09-05 · HERMES-02 · **诚实状态：实测未执行（部署被网络阻塞），结论基于预评分+分析。**

---

## 1. 实测状态：BLOCKED（非"跳过"，是"被阻塞"）

**为什么没有实测数字**：部署链路在本机被两个网络事实卡死：

| 阻塞点 | 实测 | 后果 |
|---|---|---|
| HuggingFace 直连 | `curl huggingface.co` = **000（不可达）** | 所有"从 HF 下 GGUF"方案受阻 |
| GitHub release CDN | OllamaSetup.exe（~1.5GB）下载速度 **~25MB/min** | 安装包需 ~40min，之后模型 4.4GB 再 ~3h |
| 结论 | 完整部署+基准需 **~3.5 小时** 纯下载 | 不可作为本会话内完成项 |

**处置**（按任务书 §29）：记录 FAILURE/CAUSE/RISK/RECOMMENDATION，STOP，不硬修、不伪造数字。

## 2. FAILURE 记录

- **FAILURE**：本地模型实测基准未执行（0 个 tok/s 数字）。
- **CAUSE**：HF 不可达 + GitHub CDN 限速 ~25MB/min，部署下载需 ~3.5h。
- **RISK**：无（未下载任何权重、未安装任何 runtime，系统干净）。
- **RECOMMENDATION**：若未来真要本地部署，先解决网络（HF 镜像 / 代理 / 换下载通道），且需 ≥8GB VRAM 硬件升级，否则部署了也不达标。

## 3. 预评分（分析依据，非实测，明确标注）

| 维度（冻结权重） | 本地 Qwen3 8B Q4 预判 | 依据 |
|---|---|---|
| Quant reasoning (15) | ~2 | 小模型上限 |
| Statistical reasoning (15) | ~1-2 | Q4 掉崖（算术/结构输出是质量关键任务） |
| Research auditing (15) | ~1-2 | 长文档推理衰减 + Q4 |
| Adversarial reasoning (10) | ~1-2 | 小模型弱项 |
| Evidence handling (10) | ~2 | 需长上下文保持范围限定 |
| Long context 64K (10) | ~1-2 | 本机 CPU Q4 慢 + 稳定性存疑 |
| Coding (8) | ~2 | Qwen3 8B 编码尚可，但 Q4 |
| Tool use (7) | ~1-2 | Q4 结构化输出掉崖 |
| Structured output (5) | ~1-2 | Q4 掉崖 |
| Self-correction (5) | ~2 | 一般 |

> **三核心维度（Statistical / Research auditing / Adversarial）预判均 < 2.0** → 按冻结判定门槛，
> 本地模型**不具备作 Primary Quant Brain 资格**（即便未来补实测，预期也不会改变这一门槛判定）。

## 4. 诚实声明

- 本文件**不含任何实测 tok/s / latency / 64K 数字**，因为没有模型被成功部署。
- 预评分是**分析预判**，不是伪造的实测结果。若用户要求，需先解决网络+硬件后补实测。
- 这一"部署被阻塞"本身，就是"本机不适合本地 quant 主脑"的**额外实证**：即使分析层面存在边际候选，
  实际部署也因基础设施无法在合理时间内完成。
