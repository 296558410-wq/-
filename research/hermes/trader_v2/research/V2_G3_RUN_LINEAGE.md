# V2 G3 Run Lineage — 2026-09-17

## 当前（最终 G3）
- **run_id**: `V2-SHADOW-20260917-105319-b5e4`
- 类型: SHADOW (PAPER, no-broker)
- start_utc: 2026-09-17T10:53:19Z / end_utc: 2026-09-19T10:53:19Z (48h 窗口)
- 数据层: 冻结于 `V2_G3_DATA_FREEZE_20260917.md` (git `8d997fb`)
- 纳入最终 G3 24h/48h 统计: **YES**

## 历史（保留，不纳入最终统计）
| run_id | 状态 | 说明 |
|---|---|---|
| `V2-SHADOW-20260917-104824-76af` | 过渡（TRANSITIONAL） | 元数据标签修正 + 重新冻结前的 1-cycle run；**不纳入**最终统计；已 finalize |
| `V2-SHADOW-20260917-042036-df35` | 过渡（TRANSITIONAL） | **换源前过渡 Shadow**；ledger/报告/guardian 保留；**不纳入**最终 G3 24h/48h 统计；已 finalize |
| `V2-SHADOW-20260917-041800-3276` | STOPPED | 早期失败尝试，保留 |
| `V2-SHADOW-20260917-021627-f80e` | STOPPED | 早期失败尝试，保留 |
| `V2-PAPER-*` (更早) | 历史 | 更早 paper runs，保留 |

> 规则 (§一/§三): **禁止把换源前的 df35 与新数据层样本混合计算 G3**。df35 仅作历史证据。
