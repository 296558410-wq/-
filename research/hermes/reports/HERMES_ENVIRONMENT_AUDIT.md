# HERMES ENVIRONMENT AUDIT

> 生成：2026-09-05 20:10 Asia/Shanghai
> 作者：Hermes Agent（deepseek-v4-pro / deepseek provider / CLI）
> 性质：环境与运行时自审（仅基础设施，无任何 alpha 研究、无交易、无数据改动）
> 交叉参照：`C:\AIQuant\reports\machine_baseline.md`、`C:\AIQuant\reports\environment_baseline.md`、`C:\AIQuant\reports\env_smoke_summary.txt`

---

## 0. 本报告最重要的三条结论（先读）

1. **我不是本地模型。** 当前运行在 `deepseek-v4-pro`，provider 为 `deepseek`（云端 API）。任务书里"本地研究模型 / 本地模型选择"这个前提，对我当前的运行时**不成立**。这直接改变第二阶段（模型选择）的性质——见 §4 与 §13。

2. **存在三套互相独立的工具链环境**，版本不一致。我的（Hermes）终端里看到的 `python`/`node`/`pip` 版本，**不是** OpenClaw 研究环境里的那套。任何跨环境操作必须显式指定解释器路径，否则会拿错版本。见 §3。

3. **研究系统不是白板。** `C:\AIQuant` 已是一个成熟的研究工作区（Phase 1–9 + R1' + registry + 自带环境基线），且已有它自己的完整环境审计（`environment_baseline.md`）。本报告是与它**交叉核对**的结果，不是从零重建。记忆（memory）当前为**空**，需要从已有研究里"喂"出来，而不是凭空写。

---

## 1. Hermes 运行时

| 项目 | 值 | 来源 |
|---|---|---|
| Hermes 版本 | 0.21.0（desktop-runtime 路径） | config / 目录 |
| 平台 | CLI | 运行时 |
| 主机 OS | Windows 11 专业版 build 10.0.26200（MINGW64/MSYS 外壳） | uname |
| 主机名 | DESKTOP-LQ0B8O3 | uname |
| Profile | default | 运行时 |
| 工作目录 | `C:\Users\surface\.hermes\workspace` | 运行时 |

## 2. 硬件（与已有基线一致，交叉验证通过）

| 项目 | 值 | 与基线 |
|---|---|---|
| 机型 | Surface Laptop Studio | ✅ 一致 |
| CPU | Intel i7-11370H，4 物理核 / 8 逻辑（`nproc=8`） | ✅ 一致 |
| RAM | 31.8 GB（32GB LPDDR4x） | ✅ 一致 |
| GPU | NVIDIA RTX A2000 Laptop，4GB VRAM，driver 591.55 | ✅ nvidia-smi 实测一致 |
| 磁盘 | 953GB 总量 / 857GB 可用（11% 占用） | ✅ 一致 |
| 网络 | google 302 / github 200 / arxiv 200（均可达） | ⚠️ 见 §12 差异 |

## 3. 工具链（★ 三套环境，版本不同）

| 组件 | 我的（Hermes）终端 | OpenClaw 研究环境（基线） | 系统级 |
|---|---|---|---|
| Python | 3.12.13（Hermes 自带 venv） | 3.12.10（`C:\AIQuant\.venv`） | 3.14.7（OpenClaw 专用，禁改） |
| pip | 25.0.1（Hermes venv 内） | 26.2.1（研究 venv 内） | — |
| node | v22.22.0（Hermes 自带） | v24.18.1（OpenClaw 运行时） | — |
| npm | 10.9.4（Hermes 自带） | 11.16.0 | — |
| git | 2.55.0.windows.3 | 2.55.0.windows.3 | ✅ 一致 |

> **含义**：我的 `python`/`node`/`pip` 解析到的是 Hermes 自带 runtime（`C:\Users\surface\.hermes-web-ui\desktop-runtime\hermes\0.21.0\win-x64\...`）。若要操作研究代码/回测，**必须**用 `C:\AIQuant\.venv\Scripts\python.exe`，而不是裸 `python`。

## 4. 模型运行时（★ 与任务书前提冲突）

| 项目 | 值 |
|---|---|
| 当前模型 | `deepseek-v4-pro` |
| provider | `deepseek`（云端 API，非本地） |
| 本地模型 | 无（无 Ollama/vLLM/llama.cpp 本地推理进程） |
| GPU 可用性 | 4GB VRAM，仅够跑小模型（~3B 量化级），不足以支撑"本地研究模型" |

> **结论**：任务书第二阶段的"MODEL_SELECTION_REPORT / 本地模型基准"在语义上需要**重定义**。当前 Hermes 并不承载本地推理；模型选择问题属于"研究推理用哪个云端模型 / 是否另起本地推理栈"，不是"给 Hermes 换一个本地大脑"。4GB VRAM 是硬约束。

## 5. Context 与工具能力

| 能力 | 状态 |
|---|---|
| 上下文 | LLM 上下文窗口（deepseek-v4-pro，未做量化基准——诚实标注 UNKNOWN，见 §13） |
| 文件读写 | ✅ 可读可写 `C:\Users\surface\*`、`C:\AIQuant\*`、`C:\AIResearch\*`（只读原则自守） |
| 终端 | ✅ git-bash/MSYS（POSIX 语法，非 PowerShell） |
| 网络 | ✅ 可出网 |
| web_search / web_extract | ✅ 可用（OpenClaw 基线标"禁用"，见 §12 差异） |
| 长时记忆（memory） | ✅ 机制存在，**当前为空** |
| skills | ✅ 机制存在，当前为 Hermes 内置集（见 §11） |
| 子代理（delegate） | ✅ 可用（隔离上下文并行） |
| MCP | ✅ hermes-studio api / browser / devices / use 四个 server |

## 6. 文件系统与权限

- 对 `C:\AIQuant`、`C:\AIResearch` 具备读取权限；本任务**只新增** `C:\AIQuant\research\hermes\`（Hermes 专属子目录），未改动任何已有文件/目录/registry。
- `C:\AIResearch` 未读取内容（本阶段无需），已确认存在但保持不动。

## 7. 网络

| 目标 | 状态 |
|---|---|
| google.com | 302（可达） |
| github.com | 200（可达） |
| arxiv.org | 200（可达） |

## 8. 当前 Memory

**空。** `~/.hermes/memories/` 无条目。→ 属于"待喂"，不是"已有可检索记忆"。

## 9. 当前 Config（关键项）

- `model.default: deepseek-v4-pro`，`model.provider: deepseek`
- 4 个 MCP server（hermes-studio api/browser/devices/use），指向 `http://127.0.0.1:8748`
- 无本地推理配置。

## 10. 与已有基线的差异（★ 重要，需记录而非默认一致）

| 差异点 | 我的（Hermes） | 已有基线（OpenClaw，9/3–9/4） | 性质 |
|---|---|---|---|
| node 版本 | v22.22.0 | v24.18.1 | 两套运行时 |
| python | 3.12.13（Hermes venv） | 3.12.10（研究 venv）/ 3.14.7（系统） | 三套 python |
| GitHub HTTPS | 可达（200） | 基线标"不可达/超时" | 网络路径或时间变化 |
| web_search | 可用 | 基线标"无 provider/禁用" | Hermes 有独立工具栈 |

> 这些差异本身不是故障，而是"OpenClaw 环境 ≠ Hermes 环境"的实证。跨环境引用结论时，不得假设两者共享同一工具链或网络。

## 11. 当前 Skills（Hermes 内置集）

分类齐全但均为通用能力，**没有 XAUUSD 研究专用技能**：creative / media / research(arxiv、competitor-news、grounded-citations 等) / software-development / web / productivity / note-taking / email / autonomous-ai-agents(含 hermes-agent、claude-code、codex、opencode、computer-use) / 及若干图片/视频生成类。

→ 研究专用技能（no-lookahead review、adversarial review、market autopsy 等）**需要自建**，符合任务书第六阶段方向。

## 12. 结论与状态判定

| 检查 | 结果 |
|---|---|
| 环境是否可用 | ✅ 可用，无阻断性故障 |
| 是否需要 STOP | ⚠️ 不 STOP，但有两个**前提性发现**必须先由你确认（§13） |
| 是否破坏环境 | ✅ 未破坏（只新增 hermes 子目录） |

## 13. 需要你（用户）确认的两个前提问题

**Q1（模型前提）**：任务书把 Hermes 定位为"本地研究模型"，但当前 Hermes 跑在云端 `deepseek-v4-pro`，本地无推理栈、且仅 4GB VRAM。第二阶段"模型选择"应按下述哪个方向？

- (A) 保持现状：Hermes 继续用 deepseek-v4-pro 做研究推理，第二阶段改为"评估 deepseek-v4-pro 是否胜任研究推理（而非选本地模型）"。
- (B) 另起本地推理栈：在 4GB VRAM 约束下选一个 ~3B 量化模型做辅助（并接受其能力远弱于云端）。
- (C) 暂缓：先不碰模型，聚焦记忆/技能/知识地图，模型问题留后。

**Q2（范围与节奏）**：任务书要求"继续自主推进直到全部完成"。但知识地图（第四阶段）、失败库（第五阶段）**必须来自实际读取 Phase 1–9 + R1' 的报告**，不能凭我臆造——否则就是任务书自己禁止的"假 Alpha / 幻觉"。这需要大量逐份阅读。你希望我：

- (A) 现在就按顺序逐阶段读完整份研究，产出真实的知识地图/失败库（耗时较长，但内容真实）。
- (B) 先只交付本审计 + 一份"研究材料清单索引"，读材料的深度工作等你确认后再展开。

---

### 我的默认建议（若你不回复）

- Q1 → 选 (A)：先承认"云端模型 + 4GB VRAM"的现实，把第二阶段重新定义为"deepseek-v4-pro 研究能力评估"，不强行装本地模型。
- Q2 → 选 (A)：立刻开始逐份读取已有研究，产出的知识地图/失败库**只写我实际读到并核实的内容**，读不到的标 `UNKNOWN` / `DATA GAP`，绝不臆造。
