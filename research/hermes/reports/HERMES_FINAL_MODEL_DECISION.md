# HERMES FINAL MODEL DECISION（最终模型决策）

> 生成：2026-09-05 · HERMES-02 · 基于：全球扫描 + 候选注册表 + 硬件实测 + 安全审查 + 冻结评分体系。
> 原则：claim→evidence→benchmark→decision；禁止金融标签崇拜；禁止为完成任务强行安装。

---

## 1. 决策结论（一句话）

**本机不存在值得长期培养的本地 Quant Research Primary 模型；云端 deepseek-v4-pro 应继续作为主脑。
本地模型（若部署）只能作窄任务辅助，且其增量低于维护成本。**

---

## 2. 三重硬约束（不可绕过的证据）

| 约束 | 事实 | 对 Quant Research 的后果 |
|---|---|---|
| 4GB VRAM | 远低于 Hermes "8GB 舒适线"；7B Q4（4.4GB）+KV 必然溢出 | 7B+ 模型只能 CPU，速度骤降 |
| Q4 量化掉崖 | 2026 研究：算术/数学推理、结构化输出、精确事实提取 = 质量关键任务，Q4 以下掉崖 | quant 核心（统计检验/lookahead/机会成本）全中招 |
| 4C/8T CPU | 无 AVX-512，弱于公开 benchmark 的 12 核 | 7B 仅 3-4 tok/s，64K 下更慢 |

## 3. 金融模型 vs 通用模型（§16 答案）

金融专用模型（FinGPT/Fastino-Finance）增量 = 金融 NLP/情感/QA，**不提供** microstructure / 统计推理 /
研究审计 / 对抗推理。→ 金融标签在 Quant Research 主脑维度增量 = **0**。选模型只看通用推理。

## 4. 最终选择

| 角色 | 模型 | 理由 |
|---|---|---|
| **PRIMARY MODEL** | **deepseek-v4-pro（云端，保持现状）** | quant 核心能力（统计/审计/对抗/长上下文）最强，HERMES-01 已验证可靠 |
| SECONDARY / AUXILIARY | 无（暂不设） | 本地辅助模型的增量（窄分类/路由）低于维护成本，且隐私增量在当前研究场景不成立 |
| FALLBACK | Ollama + Qwen3 8B（仅作可回退的离线兜底，非日常主脑） | 唯一本机可达路径（HF 阻塞）；但仅当离线需求真实出现才启用 |

## 5. 为什么不"选一个本地模型"

1. 本机没有任何模型能在"可用速度 + 64K + 可接受质量"上同时满足 quant 核心需求。
2. 唯一本地优势（离线/隐私）在当前研究场景不构成切换理由（研究材料已是本地 git 结论，非机密原始数据）。
3. 任务书明确允许 NOT READY，且禁止"因任务要求安装就随便装一个"。

## 6. 未来若要做本地（FUTURE TRAINING PLAN，仅登记不执行）

- 触发条件：硬件升级到 ≥8GB VRAM（或 ≥12GB）；或出现"需要完全离线 + 窄任务"的真实需求。
- 路径：Hermes 托管 llama.cpp runtime（桌面端）→ 选 Qwen3 8B/14B Q4+。
- domain adaptation（微调）：**不启动**，仅在"确认一个通用模型值得长期培养但需领域适配"时，另行提出训练计划并等授权。

## 7. Recommended Runtime

- **PRIMARY：Ollama**（若启用本地；唯一绕过 HF 阻塞的通道）
- **FALLBACK：Hermes 托管 llama.cpp runtime**（桌面端，供应链最安全）

---

## 最终判定：NOT READY（作本地 Quant Research 主脑）

> 明确：不是"本地模型无法运行"（它能跑，只是慢），而是"**没有一个本地模型值得作为长期 Quant Research
> 主脑来培养**"——因为三重硬件约束 + Q4 掉崖 + 金融标签零增量，决定了本机本地模型在 quant 核心任务上
> 必然系统落后于云端，且无法满足 64K + 稳定 + 速度的硬门槛。
> 云端 deepseek-v4-pro 是正确的主脑；本任务诚实结论 = 不为了"安装模型"而安装一个注定不达标的本地模型。
