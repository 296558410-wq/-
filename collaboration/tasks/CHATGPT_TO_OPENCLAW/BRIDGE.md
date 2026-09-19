# BRIDGE.md — ChatGPT → OpenClaw 任务投递桥

## 背景（已核验事实）
- ChatGPT 的 GitHub connector **只读**：Issue 写入=403、文件写入=403。
- OpenClaw 的 **GCM Git 凭据可正常 push**（已用 `CHATGPT-TASK-001` E2E 验证）。
- OpenClaw cron `collab-task-bus` 能**自动发现** `collaboration/tasks/CHATGPT_TO_OPENCLAW/*.yaml`。

因此桥接原则：**所有 GitHub 写入都由 OpenClaw（GCM）完成；ChatGPT 只负责"产出任务内容"，不直接写 GitHub，不保存任何 token。**

## 投递路径（三选一）
1. **直连（最优，若 ChatGPT connector 具备写权限）**：ChatGPT 直接把 `CHATGPT_TO_OPENCLAW/<TASK_ID>.yaml` 推入 `main`。
2. **桥接入口（本仓提供的安全网关）**：
   - `python collaboration/tools/submit_task.py <task.yaml>` —— 校验后写入任务总线并 push。
   - `python collaboration/tools/submit_task.py --inbox` —— 处理本地投递目录。
3. **本地 inbox 落盘（最低摩擦的"最后一公里"）**：把任务 YAML 放入
   `C:\AIQuant\collab_inbox\*.yaml`；`collab-task-bus` 每轮**先消费 inbox**（校验→写入任务总线→push），再发现执行。

> 现状说明（诚实标注）：在没有 token、ChatGPT 又无写权限的前提下，ChatGPT 自身**无法**把内容送达任何 OpenClaw 可读的存储；"最后一公里"当前由 **路径 3 的落盘动作** 或 **路径 1 的写权限** 承担。OpenClaw 侧全自动（发现/领取/执行/回写）。

## 安全约束（`submit_task.py` 强制）
- `READ_ONLY` 必须 `true`；`TASK_TYPE` 白名单（当前 `READONLY_HEALTHCHECK`）。
- `TASK_ID` 严格正则（`^[A-Z][A-Z0-9]*-[A-Z0-9-]{1,40}$`）→ 防路径穿越/命令注入；任务内容**永不进入 shell**。
- 产物路径必须在 `collaboration/` 下（trading / V1 / V2 / V3 / Hermes 默认禁止）。
- 重复 `TASK_ID` 拒绝（唯一性；同时检查 working tree 与 `origin/main`）。
- 正常 commit + push；**禁止 force / amend / squash**。

## 状态机
`PROPOSED`（任务文件）→ `CLAIMED` → `RUNNING` → `COMPLETED` / `FAILED`（记录于 `OPENCLAW_TO_CHATGPT/CLAIMS.json`）。
`REJECTED`（校验/范围不通过）。

## 审计与离线
- 审计：`CLAIMS.json`（领取/状态）+ `<TASK_ID>_RESULT.md`（结果）+ git 历史。
- GitHub 不可用：inbox 保留本地待同步任务；`collab-task-bus` 报错但不影响本地核心；恢复后自动补推。
