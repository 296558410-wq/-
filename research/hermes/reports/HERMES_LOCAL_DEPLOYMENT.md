# HERMES LOCAL DEPLOYMENT（本地部署方案）

> 生成：2026-09-05 · HERMES-02 · 部署方式比较 + Primary/Fallback runtime 决定
> 原则：优先最简单、最稳定、最少维护的路径；不为"高级"增加基础设施复杂度。

---

## 1. 部署方式比较（本机实测条件）

| 方式 | 可行性 | 说明 |
|---|---|---|
| **Hermes 托管 llama.cpp runtime** | ⚠️ 桌面端专属 | 文档明示从 Settings→Providers→Local Models 触发；本机**无 `hermes` CLI**，CLI 侧不可触发。是"最推荐"路径，但当前我只能记录为"桌面端未来可启用"。 |
| **Ollama** | ✅ 可用 | ollama.com 可达（200）；winget 可装；Hermes 有官方 Ollama 集成文档；`custom` provider 指向 `http://localhost:11434/v1`。**最简路径。** |
| **llama.cpp 手动** | ⚠️ 部分 | llama.cpp 官方 release 二进制可从 GitHub 拉，但 **HuggingFace 不可达（000）**，GGUF 权重下载受阻；需另找 GGUF 镜像。 |
| vLLM / SGLang | ❌ | 面向 GPU 大显存，本机 4GB 无意义。 |

> **关键环境事实**：HuggingFace 直连不可达 → 任何"从 HF 下 GGUF"的方案在本机都受阻；
> 而 Ollama 走自己的 registry（ollama.com），**绕过了 HF 阻塞**。这决定了 Ollama 是唯一顺畅路径。

## 2. Runtime 决定

- **PRIMARY RUNTIME（若部署本地模型）：Ollama**（`custom` provider → `http://localhost:11434/v1`）
  - 理由：唯一在本机可达的模型分发通道 + Hermes 官方文档路径 + 最少维护。
- **FALLBACK RUNTIME：Hermes 托管 llama.cpp runtime**（桌面端 Settings→Providers→Local Models）
  - 理由：供应链最安全（Hermes 自动下载+校验官方 llama.cpp build），但需桌面端操作，且同样受 HF/模型源可达性约束。
- **不采用**：llama.cpp 手动（HF 不可达，GGUF 下载受阻）、vLLM/SGLang（4GB 无意义）。

## 3. 若部署，模型候选（按 Ollama 可用性）

| 候选 | Ollama 标签（2026） | 本机运行方式 | 预估速度 |
|---|---|---|---|
| Qwen3 8B | `qwen3:8b`（或最新） | CPU | 3-4 tok/s |
| Phi-4-mini | `phi4-mini`（或最新） | 部分 GPU | 6-8 tok/s |

> 注：具体标签名以 2026-09 Ollama registry 实际为准，安装后 `ollama list` 确认。

## 4. 部署与验证清单（任务书 §21，若走到底）

1. 安装 Ollama → `ollama --version`
2. 拉取模型 → `ollama pull <model>`
3. 启动服务 → `ollama serve`（默认 11434）
4. 验证 model loads + 正常对话 + 结构化输出 + 长上下文 + 稳定会话
5. 若不能稳定工作 → 记录 FAILURE/CAUSE/RISK/RECOMMENDATION，判定 NOT READY

## 5. 环境隔离声明

- Ollama 安装到 `C:\Users\surface\AppData\Local\Programs\Ollama\`，模型存 `~\.ollama\`。
- **不触碰**：System Python 3.14.7 / C:\AIQuant\.venv / C:\AIResearch / OpenClaw runtime / MT5 / 已有研究数据 / 已有 Hermes memory & skills。
