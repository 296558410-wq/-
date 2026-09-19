# V2 SHADOW REPORT (G3) — 20260917

## 当前活动 Shadow run
- **SHADOW_RUN_ID**: `V2-SHADOW-20260917-042036-df35`
- window: 2026-09-17T04:20Z → 2026-09-19T04:20Z（48h target；最短 24h）
- 执行: **PAPER（无 broker）** — `RUN_META.shadow=true`；`_make_executor`/`run_cycle` 均 PAPER。
- 每 decision 写 `inputs/<decision_id>.json`（含 `source_provenance`=hist:XAUUSD:* 的 source_hash）。
- 首个 cycle（04:15Z）：**WAIT / replay_match=True / provenance 完整 / instrument=XAUUSD / no broker**。

## 早期失败尝试（保留为证据，未删除）
- `V2-SHADOW-20260917-021627-f80e`（STOPPED）：首 cycle BROKER_UNAVAILABLE（shadow/PAPER 代码缺口）+ 首 snapshot 无 provenance（pit_cache 冷启动）。
- `V2-SHADOW-20260917-041800-3276`（STOPPED）：首 decision 无 provenance（`shadow_run` 未把 `data_sources` 加入 sys.path）。
- 二者均已 finalize 保留；未删除、未改写。

## 守护（自动）
- `tools/shadow_guardian.py` 已接入 `v2_scheduled_cycle.main`（每 cycle 末尾自动跑）：
  - 逐 cycle 校验每个 input snapshot → offline_replay MATCH / instrument / provenance / 无未来 ts；
    任一关键失败 → 写 `V2_G3_FAIL.md` + verdict FAIL。
  - 每 ≥4h 写 `V2_SHADOW_HEALTH_YYYYMMDD_HHMM.md`（观察，不构成 PASS）。
  - ≥24h 评估覆盖 → `V2_G3_VERDICT.json`（PASS/INSUFFICIENT_EVIDENCE/BLOCKED）。
- OpenClaw cron 检查点：`v2-g3-24h-checkpoint`(2026-09-18T04:30Z)、`v2-g3-48h-checkpoint`(2026-09-19T04:30Z) → 唤醒主会话续跑 G4。

## 安全
`BROKER_ORDER_SENT=FALSE`；`FORWARD_VALIDATION_ALLOWED=NO`（无标记文件）；`FORWARD_STARTED=FALSE`；V1/历史 run 未动。

## 状态
GATE_3_SHADOW = **IN_PROGRESS**（~1 cycle；需 24–48h）。**未 PASS。**
