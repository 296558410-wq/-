# OPENCLAW_TO_CHATGPT — 结果回写

本目录是 **OpenClaw → ChatGPT** 的结果出口。

## 产出
- `<TASK_ID>_RESULT.md` —— 每个任务的结果（格式见 `RESULT_SCHEMA.md`）。
- `CLAIMS.json` —— 任务领取/状态流水（JSON Lines，一行一事件）。**这是运行态协作记录**，非交易 runtime。
  （文件名不用 `.jsonl`，因为 repo `.gitignore` 含 `*.jsonl`。）

## CLAIMS.json 事件字段（§七）
```json
{"TASK_ID":"...","EVENT":"DISCOVERED|CLAIMED|RUNNING|DONE|REJECTED","TS":"...","OPENCLAW_VERSION":"...","LOCAL_HEAD":"...","REMOTE_HEAD":"..."}
```

## 说明
- 结果文件由 OpenClaw 在完成任务后写入并 commit+push。
- ChatGPT 读取本目录以进行独立审计。
