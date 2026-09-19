# TASK_SCHEMA — ChatGPT → OpenClaw 任务格式（第一阶段）

任务文件：`collaboration/tasks/CHATGPT_TO_OPENCLAW/<TASK_ID>.yaml`

```yaml
TASK_ID:                # 例 CHATGPT-TASK-001（唯一；报告须同 ID）
TASK_TYPE:              # 例 READONLY_HEALTHCHECK
CREATED_BY: ChatGPT
CREATED_AT:             # ISO8601
PRIORITY:               # LOW | NORMAL | HIGH
STATUS: PROPOSED        # PROPOSED 才会被领取

OBJECTIVE: >
SCOPE: >
READ_ONLY: true         # 第一阶段必须 true

ALLOWED_PATHS:          # 允许 OpenClaw 改动的路径（相对 repo 根）
  - collaboration/

FORBIDDEN_PATHS:        # 明确禁止
  - research/hermes/trader_v1/
  - research/hermes/trader_v2/
  - research/hermes/trader_v3/

SAFETY_CONSTRAINTS: >
  # 不得下单/不得改交易系统/不得 force push 等

INPUTS: >
EXPECTED_OUTPUT: >
ACCEPTANCE_CRITERIA: >
REQUIRED_REPORT: >      # 期望的结果文件路径
REQUIRED_COMMIT: >      # 是否要求 commit（是/否 + message 约定）
```

## 解析约定
- 采用"`KEY:` 行 + 缩进续行/列表"的**最小 YAML**；OpenClaw 用轻量解析（不依赖第三方库）。
- 必填：`TASK_ID, TASK_TYPE, CREATED_BY, CREATED_AT, STATUS, OBJECTIVE, READ_ONLY`。
- `READ_ONLY!=true` 的任务在**第一阶段一律拒绝**（`STATUS=REJECTED`，原因写入 CLAIMS/RESULT）。

## TASK_TYPE 白名单（第一阶段）
```text
READONLY_HEALTHCHECK   # 对协作链做只读健康检查
```
未在白名单内的类型 → 不执行；输出 `RESULT` 标注 `UNSUPPORTED_TASK_TYPE`。
