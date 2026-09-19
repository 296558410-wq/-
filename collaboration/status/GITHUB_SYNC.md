# GITHUB_SYNC.md — GitHub 同步状态

> OpenClaw 侧同步状态（最小可靠机制）。**GitHub 不是 V1/V2/V3 的运行时单点故障**：GitHub 不可用时本地核心继续安全运行，状态置 SYNC_PENDING，恢复后自动同步。

状态集：`CONNECTED` / `SYNCED` / `SYNC_PENDING` / `STALE` / `ERROR`

```text
GitHub:        CONNECTED
Remote HEAD:   <origin/main sha>
Local HEAD:    <staging repo HEAD sha>
Sync:          SYNCED
Last Sync:     YYYY-MM-DD HH:MM:SS (GMT+8)
```

## 约定
- `CONNECTED`：可 `git ls-remote`/`git fetch` 到远端。
- `SYNCED`：`local HEAD == remote HEAD` 且工作树干净。
- `SYNC_PENDING`：本地有新 commit 尚未 push，或远端有新 commit 尚未合并。
- `ERROR`：连续失败，记录时间与错误摘要。
- 该文件由 `collaboration/tools/task_bus.py` 在每次运行时刷新（只改本文件）。
