# HERMES MODEL GLOBAL SCAN（全球模型扫描）

> 生成：2026-09-05 · 作者：Hermes Agent · 任务：HERMES-02
> 方法：web_search / web_extract 实测 2026-09 版图（非记忆，非营销语）。所有候选的"量化适配"
> 数字来自 2026 年公开量化对照（bmdpat/45squared/tinyweights/promptquorum），非虚构。
> 铁律：**不预设任何模型获胜**；claim→evidence→benchmark→decision。

---

## 0. 一句话结论（先给，后面逐步证明）

在**这台机器（4GB VRAM / 4C8T CPU / 32GB RAM）**上，2026 年**没有任何本地模型能作为"长期 Quant Research
主脑"**。原因是**三重硬约束叠加**，见 §2。本地模型最多作为"窄任务辅助"（分类/路由/摘要），且增量存疑。

---

## 1. 2026 本地模型版图（实测检索）

### 1a. 通用推理/编码（本地主力候选来源）
| 模型 | 参数 | 特点（2026 实测口径） | License |
|---|---|---|---|
| Qwen3 8B | 8B | 本地编码/推理最稳；76% HumanEval；CPU 4-5 tok/s | Apache 2.0 |
| Qwen3 14B | 14B | 编码+分析强；12-16GB 才舒适 | Apache 2.0 |
| Qwen3.5-27B | 27B | 单 3090 的 agentic 编码主力 | Apache 2.0 |
| Qwen3.6-35B-A3B | 35B MoE(~3B active) | 8GB 卡配 `--n-cpu-moe` 可用 | — |
| Phi-4-mini | 3.8B | "3-4B 推理之王"；GSM8K 88.6%；CPU 12 tok/s | MIT |
| Gemma 4 26B-A4B | 26B MoE(~4B active) | 256K ctx；需 ~12GB VRAM | Apache 2.0 |
| Llama 5.1 / 3.3 8B | 8B | 社区许可；兼容性广 | 社区 |
| Mistral（MoE） | 7B-小 | 快，Apache 2.0，推理分低于 Qwen | Apache 2.0 |

### 1b. 金融/量化专用（任务书 §16 需逐项验证）
| 模型/项目 | 形态 | 实测增量 | 关键判断 |
|---|---|---|---|
| FinGPT (AI4Finance) | 框架+多基座 | 金融 NLP/情感/QA | **不是** quant/microstructure/统计推理 |
| Fastino-Nemotron-Finance | Nemotron 基座 | FinQA 15.86→59.23 | 金融**问答**，非研究审计 |
| QuantEval / FrontierFinance | benchmark | 开源模型落后人类专家 | 证明"金融推理"仍是大模型弱项 |
| Bridgewater Qwen3-235B 微调 | 235B 微调 | 6 任务 84.7% | 大参数+机构级微调，本地不可复现 |
| PandaAI (arXiv 2606) | 神经-符号 agent | 需微调+闭环 | 方向参考，非现成模型 |

> **§16 的答案已现雏形**：金融专用模型提供的增量 = 金融术语/情感/QA/文档提取，**不提供**
> microstructure、市场 regime、时序统计、研究审计、adversarial reasoning——而这些才是 Quant Research
> 的实质。量化研究能力来自**通用推理**，不来自"金融标签"。

---

## 2. 三重硬约束（这台机器上本地模型的根本障碍）

### 约束 1：4GB VRAM 远低于 Hermes 的"8GB 舒适线"
Hermes 官方文档明示：**"8GB+ 显存才能舒适跑小目录模型"**。4GB VRAM 只能完整容纳 ~3B Q4 模型；
7B Q4（~4.4GB）+ KV cache 必然溢出 → CPU/系统 RAM，速度骤降。

### 约束 2：量化质量悬崖正打在 quant 研究要害
2026 研究明确分层：算术/数学推理、结构化输出（JSON）、精确事实提取 = **质量关键任务**，
Q4 以下"质量悬崖"（arithmetic reasoning 掉崖）。而 quant 研究的全部核心（统计检验、lookahead
审查、REJECT/EDGE 判定、机会成本计算）**恰好全落在这类任务**。→ 本机只能跑 Q4，Q4 在关键任务上已掉崖。

### 约束 3：4C/8T CPU 决定速度上限
i7-11370H（无 AVX-512，4 物理核）远弱于公开 benchmark 用的 12 核 i7-12700。公开数字
（Phi-4-mini 12 tok/s、Qwen3 8B 4-5 tok/s）在本机**还要再打折**，估 6-8 与 3-4 tok/s。
64K context（任务书硬门槛）在 CPU Q4 下 KV cache 重 + 慢。

---

## 3. 候选分层（初步，按"是否值得实测"）

| Tier | 候选 | 依据 |
|---|---|---|
| **TIER A（唯一值得实测的辅助候选）** | Qwen3 8B Q4_K_M | 通用推理/编码最强小模型，Apache 2.0，32GB RAM 可 CPU 跑 |
| TIER B | Phi-4-mini 3.8B | 推理强但绝对能力更低；速度快些 |
| TIER C | Qwen3 4B / Gemma 3 4B / Llama 3.2 3B | 速度/极轻，但推理弱，不达 quant 门槛 |
| **REJECT** | >14B 一切模型 | 本机 CPU 速度 <2 tok/s，不可用 |
| **REJECT（标签崇拜）** | FinGPT / 金融微调小模型 | 提供 NLP/情感，不提供 quant 推理；且多为大基座 |

**关键**：TIER A/B 都只是"窄任务辅助"候选，**不是** Primary Quant Brain 候选——因为 §2 三重约束决定了
它们在 quant 核心任务上必然远弱于云端 deepseek-v4-pro。

---

## 4. 需要实测回答的问题（进 benchmark 前冻结）

1. 本机真实 tok/s、first-token latency（4K/8K/16K/32K/64K 逐档）是多少？
2. 64K context 在本机 CPU Q4 下是否真实可用、稳定？
3. 在真实内部研究材料上，本地模型能否正确区分 REJECT vs EDGE UNCERTAIN、识别 lookahead / overlap / cost illusion？
4. 本地模型能否独立攻击一个"看起来正确"的研究结论（adversarial）？能否说"我不知道"？
5. 与云端 deepseek-v4-pro 在相同任务上的差距有多大？

> 若实测证明本地模型在 quant 核心任务上明显弱于云端（预期如此），最终判定 = NOT READY（作主脑），
> 并诚实说明"辅助模型"的增量是否值得维护成本。
