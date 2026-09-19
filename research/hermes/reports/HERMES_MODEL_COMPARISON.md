# HERMES MODEL COMPARISON（模型对比）

> 生成：2026-09-05 · HERMES-02 · 两个核心对比：金融专用 vs 通用模型；本地 vs 云端。
> 原则：claim→evidence→benchmark→decision，禁止"金融标签崇拜"。

---

## 1. 金融专用模型 vs 通用模型（任务书 §16 逐项验证）

| 能力维度 | 金融专用模型（FinGPT/Fastino-Finance 等） | 通用推理模型（Qwen3 等） | Quant Research 需要谁 |
|---|---|---|---|
| 金融术语/知识 | +（更强） | 有 | **不是关键** |
| 金融文档/情感/NLP | +（FinQA 15.86→59.23） | 有 | 不是关键 |
| 财经问答 | + | 有 | 不是关键 |
| **量化推理/统计** | 无增量 | **由通用推理决定** | **关键** |
| **market microstructure** | 无增量 | 通用 | **关键** |
| **研究审计（找泄漏/成本幻觉）** | 无增量 | 通用 | **关键** |
| **adversarial reasoning** | 无增量 | 通用 | **关键** |
| **code / statistics** | 无增量 | 通用 | **关键** |

**结论**：金融专用模型提供的增量集中在"金融 NLP/情感/QA"，而 Quant Research 的实质
（microstructure、统计推理、研究审计、对抗推理、代码）**全部由通用推理能力决定**。
→ 在本任务语境下，金融标签的增量 = **0**。选模型看通用推理，不看"Finance"字样。

> 补充（2026 证据）：FinGPT 是框架+多基座（非单一小模型）；Fastino-Finance 提升的是金融问答；
> QuantEval/FrontierFinance 证明"金融推理"仍是开源模型普遍弱项，且 best 都是大参数模型。
> Bridgewater 用 Qwen3-235B 微调才到 84.7% —— 本地 4GB VRAM 根本不可能复现这个量级。

---

## 2. 本地模型 vs 云端模型（本机语境）

| 维度 | 本地最优（Qwen3 8B Q4，本机 CPU 3-4 tok/s） | 云端（deepseek-v4-pro，当前 Hermes 主模型） |
|---|---|---|
| Quant reasoning | 中（小模型上限） | 强 |
| Statistical reasoning | Q4 掉崖风险（算术/结构输出是质量关键任务） | 强 |
| Research auditing | 中，长文档推理衰减 | 强（HERMES-01 已验证：正确区分 REJECT/EDGE、识别 lookahead/overlap/cost illusion） |
| Adversarial reasoning | 弱-中 | 强（已对 OpenClaw 结论给出范围受限的第二意见） |
| 64K 长上下文稳定性 | 本机 CPU Q4 慢 + 稳定性存疑 | 稳定 |
| 速度 | 3-4 tok/s（64K 下更慢） | 快（云端） |
| Tool use / 结构化输出 | Q4 掉崖 | 可靠 |
| 隐私 | 本地（数据不出机器） | 云端（数据出机器） |

**关键判断**：本地模型唯一的优势是**隐私/离线**（数据不出机器）。但本任务的研究材料
（Phase 1–9A 报告）已在本地 git 仓库，且是研究**结论**而非机密原始数据；隐私增量在当前
研究场景**不构成切换主模型的理由**。

---

## 3. 结论（供 HERMES_FINAL_MODEL_DECISION.md 引用）

1. 金融标签在 Quant Research 主脑维度提供 **0 增量** —— 不因名字选金融模型。
2. 本地模型在本机的 quant 核心任务上**系统落后云端**，唯一优势是离线/隐私。
3. 因此：**云端 deepseek-v4-pro 应保持 Primary**；本地模型最多作"窄任务辅助"，且需证明增量
   高于维护成本（详见 benchmark 实测后终判）。
