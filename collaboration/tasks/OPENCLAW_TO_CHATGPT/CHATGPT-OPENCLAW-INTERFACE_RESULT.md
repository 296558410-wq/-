# CHATGPT-OPENCLAW-INTERFACE_RESULT.md

> 任务：把 ChatGPT → GitHub → OpenClaw 任务接口真正打通（第一阶段）。
> 真实 E2E：`CHATGPT-TASK-001`、`CHATGPT-TASK-002`（均只读健康检查）。
> 本报告随本 commit 入库（`LOCAL_HEAD` 指向"包含本报告的 commit"）。

## 最终状态

```text
STATUS=READY_WITH_LIMITATIONS

GITHUB_READ=PASS
GITHUB_WRITE=PASS            # 经 OpenClaw GCM 的 git push；GitHub API 写未使用
ISSUE_READ=PASS
ISSUE_WRITE=FORBIDDEN        # 403，无 token；不绕过

TASK_DISCOVERY=PASS          # cron `collab-task-bus` 自动扫描 origin/main
TASK_CLAIM=PASS              # CLAIMS.json：PROPOSED→CLAIMED→RUNNING→COMPLETED/FAILED
TASK_EXECUTION=PASS
RESULT_UPLOAD=PASS
END_TO_END_TEST=PASS         # TASK-001、TASK-002 全链路

V1_UNTOUCHED=TRUE
V2_UNTOUCHED=TRUE
V3_UNTOUCHED=TRUE
HERMES_UNTOUCHED=TRUE
BROKER_ORDER_SENT=FALSE

LOCAL_HEAD=<the commit that adds this report>
REMOTE_HEAD=<same as LOCAL_HEAD; verified on origin/main>

BLOCKERS=最后一公里：ChatGPT（无写权限、无 token）无法自送内容到任何 OpenClaw 可读存储；当前由 bridge 的 inbox 落盘 / 或 ChatGPT 写权限承担
DATA_GAPS=①Issue 驱动需 token（不使用）；②发现为轮询（3 分钟）
NEXT_STEP=用户可选：给 ChatGPT 写权限，或接受 inbox 落盘投递；OpenClaw 侧已全自动
```

## 桥接设计（本项目新增）
- `collaboration/tools/submit_task.py` —— **安全投递入口**：校验（READ_ONLY=true、TASK_TYPE 白名单、TASK_ID 唯一且严格正则、产物仅在 `collaboration/` 下）→ 写入任务总线 → 正常 commit+push。
- `collaboration/tools/task_bus.py` —— 每轮先消费本地 `C:\AIQuant\collab_inbox\*.yaml`（经 submit 校验后入库），再自动发现/领取/执行/回写。
- `collaboration/tasks/CHATGPT_TO_OPENCLAW/BRIDGE.md` —— 投递协议说明。

## E2E（真实，未人工复制任务正文）
```text
TASK-001：da151c(push 任务) → cron 自动发现(87e76a7 产出 RESULT)
TASK-002：投入 inbox → 8d6d31c(bridge 自动写入任务总线) → 9035044(cron 自动领取/执行/回写 RESULT) → inbox 文件移入 _done
链路：ChatGPT(task) → [bridge] → GitHub → OpenClaw(discover→claim→run→result) → GitHub ✓
```

证据：远端历史；`collaboration/tasks/OPENCLAW_TO_CHATGPT/CHATGPT-TASK-00{1,2}_RESULT.md`；`CLAIMS.json`。

## 以后 ChatGPT 如何直接投递
1. **有写权限**：直接把 `collaboration/tasks/CHATGPT_TO_OPENCLAW/<TASK_ID>.yaml`（`STATUS: PROPOSED`）推到 `main`。
2. **用桥接入口**：`python collaboration/tools/submit_task.py <task.yaml>`（或 `--inbox`）。
3. **inbox 落盘**：把 YAML 放 `C:\AIQuant\collab_inbox\`；`collab-task-bus` 自动消费入库。
→ 之后 **无需用户复制**：OpenClaw 自动发现/领取/执行/回写。

## 安全
- 任务内容**永不进入 shell**；TASK_ID 严格校验（防穿越/注入）；产物仅限 `collaboration/`。
- 只读默认；trading/V1/V2/V3/Hermes 默认禁止；无 force/amend/squash。
- GitHub 不可用：inbox 保留本地待同步；核心不受影响。
- 原始 `C:\AIQuant`：`d22d9fb`/249 未变；未下单；未改交易系统。
