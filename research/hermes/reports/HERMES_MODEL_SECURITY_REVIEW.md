# HERMES MODEL SECURITY REVIEW（供应链安全审查）

> 生成：2026-09-05 · 对最终候选（Qwen3 8B / Phi-4-mini）做 supply-chain 审查。
> 原则：模型权重本身、转换脚本、启动脚本、第三方仓库**分开审查**；任何可疑 → STOP/REJECT。
> 注：本阶段为**预下载审查**（未实际下载权重，故无实测 hash；下载前 Gate 见 §4）。

---

## 1. 审查对象与结论

| 候选 | 发布方 | 身份可信度 | License | 风险评级 | 结论 |
|---|---|---|---|---|---|
| Qwen3 8B | Alibaba Qwen（HuggingFace 官方 org） | 官方 org，verified | Apache 2.0 | **低** | 可下载（待 Gate） |
| Phi-4-mini | Microsoft（HF 官方 org） | 官方 org，verified | MIT | **低** | 可下载（待 Gate） |

---

## 2. 逐项审查

### 2a. 模型来源 / 发布方身份
- 两者均为**官方组织在 HuggingFace 的 verified org**（Qwen / microsoft），非第三方重上传。
- 建议下载时用 **GGUF 官方或高度可信的量化者**（如 bartowski / Qwen 官方 GGUF / microsoft 官方），
  避免从不明账号下载"同名"GGUF。

### 2b. 仓库真实性
- 正本以 org 官方 repo + commit hash 为准；下载前记录具体 GGUF 文件名 + sha256（HF 提供）。

### 2c. License
- Qwen3：Apache 2.0（可商用，宽松）。
- Phi-4-mini：MIT（宽松）。
- 无 license 风险。

### 2d. 可疑文件 / 可执行 payload
- **GGUF 权重文件本身 = 纯张量数据，不是可执行文件**，不存在代码执行风险（除非 llama.cpp 解析器被投毒，
  而 llama.cpp 是 C++ 开源、有 CI 校验）。
- 风险点主要在：**推理引擎**（llama.cpp / Ollama）的二进制来源，以及**转换脚本**。

### 2e. 自定义代码 / 依赖
- 本候选无自定义推理代码需求（标准 transformer/GGUF，llama.cpp 原生支持）。
- 若有第三方"量化版"附带 `run.sh` / `convert.py`，**必须单独审查**，不执行未读脚本。

### 2f. 推理引擎来源（关键风险点）
- 若走 Ollama：从 ollama.com 官方下载（Windows 安装包），版本固定，更新走官方 channel。
- 若走 llama.cpp：从 ggml-org/llama.cpp 官方 release 下载预编译 Windows CUDA 版，**校验 release 的
  官方来源**，不从第三方网盘下载。
- Hermes 托管运行时（若未来从桌面端启用）：Hermes 自身下载并校验官方 llama.cpp build（文档明示
  "verifies it"），供应链风险最低。

### 2g. 下载器行为 / 网络行为
- Ollama：官方安装器，联网拉模型（默认 ollama.com registry），可离线运行已下载模型。
- llama.cpp：纯本地进程，无回传（模型权重本地加载，不离开机器）。
- 均符合"模型权重不离开本机"的本地部署要求。

---

## 3. 综合安全结论

**两个候选供应链风险均为「低」**，可进入下载 Gate。**唯一需警惕**的是：
1. 不要从非官方/不明 GGUF 账号下载权重（用官方 org 或 bartowski 等高信誉量化者）；
2. 不要执行任何第三方仓库附带的未读脚本；
3. 推理引擎二进制只从官方 release 获取。

---

## 4. 下载前 Gate（任务书 §20，正式安装前逐项打勾）

| # | 检查项 | Qwen3 8B Q4_K_M | Phi-4-mini Q4 |
|---|---|---|---|
| 1 | 来源确定 | Qwen 官方 HF org（或 bartowski GGUF） | microsoft 官方 / bartowski |
| 2 | 版本记录 | Qwen3-8B（2025-04） | Phi-4-mini（2025） |
| 3 | 文件大小 | ~4.4GB | ~2.3GB |
| 4 | hash | 待下载时记录 sha256 | 待下载时记录 sha256 |
| 5 | license | Apache 2.0 | MIT |
| 6 | 预估 RAM | ~6GB | ~4GB |
| 7 | 预估 VRAM | 0（CPU）/ 溢出 | ~2GB |
| 8 | 磁盘 | 4.4GB | 2.3GB |
| 9 | runtime 兼容 | llama.cpp / Ollama 均支持 | 同左 |
| 10 | 是否有更合适候选 | 见 §5 | 见 §5 |

---

## 5. 结论性判断（安全+适配联合）

安全上两者都可通过 Gate。**但**：结合 HERMES_MODEL_HARDWARE_FIT.md，即使通过安全审查并下载，
本机 4GB VRAM / 4C8T 的物理限制**不因"模型安全"而消失**——安全 ≠ 适配 ≠ 胜任 quant 研究。
安全审查通过只解决"能不能安全下载"，不解决"值不值得长期培养"。
