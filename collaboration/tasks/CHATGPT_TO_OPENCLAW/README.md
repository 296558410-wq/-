# CHATGPT_TO_OPENCLAW — 任务总线（第一阶段）

本目录是 **ChatGPT → OpenClaw** 的任务入口（第一阶段用 **GitHub 文件**作为机器任务总线；不依赖 Issues API 写权限）。

## 怎么用（ChatGPT 侧）
1. 复制 `TASK_SCHEMA.md` 的字段，创建一个任务文件：`collaboration/tasks/CHATGPT_TO_OPENCLAW/<TASK_ID>.yaml`
2. `STATUS: PROPOSED`，提交并 push 到 `main`。
3. OpenClaw 的**自动发现任务**（见下）会周期扫描本目录。

## OpenClaw 如何发现（自动，无需用户复制）
- OpenClaw 定时任务 `collab-task-bus` 周期性执行 `collaboration/tools/task_bus.py --once`。
- 该脚本 `git fetch origin`，读取 **origin/main** 上本目录的任务文件，发现 `STATUS: PROPOSED`。
- **不覆盖原任务文件**；领取与状态变化记录在 `../OPENCLAW_TO_CHATGPT/CLAIMS.json`（PROPOSED→QUEUED→RUNNING→DONE）。
  （注：不含 `.jsonl` 后缀——repo `.gitignore` 有 `*.jsonl`，避开以免误被忽略。）
- 完成后在 `../OPENCLAW_TO_CHATGPT/<TASK_ID>_RESULT.md` 写结果，并 commit+push。
- 通过"是否已存在 RESULT/CLAIM"避免重复执行。

## 状态集
`PROPOSED` → `QUEUED` → `RUNNING` → `COMPLETED` / `REJECTED` / `CANCELLED`
（任务文件本体保持 `PROPOSED` 不被改写；实际状态以 `CLAIMS.json` 与 RESULT 为准。）

## 第一阶段范围
只支持**只读**任务（`READ_ONLY: true`）。第一阶段**不做**：自动改交易代码、自动部署、自动下单、自动改策略/风控、自动合并交易 PR。
