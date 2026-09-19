# Hermes V2 — XAUUSD 实验交易系统

独立于 V1 的 XAUUSD 实验系统：**Agent1(技术情报) + Agent2(宏观/地缘/资金流情报) → Hermes V2 自主寻找交易机会 → 独立模拟账户 → 完整可审计 ledger → 自动复盘**。

- 设计：`V2_ARCHITECTURE.md`
- 计划：`V2_PHASE1_PLAN.md`
- 配置：`config/v2_config.json`

## 铁律
- **V1（`../trader_v1`）完全不动**：只读、不 import、不共用账户/ledger/状态/记忆。
- Phase-1 **禁止真实资金**（`allow_real_trading=false`）。
- 无未来数据泄漏（point-in-time）。
- Hermes 是唯一决策者；**禁止 Agent 投票决定交易**；宏观新闻/单根 K 线不得直接触发交易。

## 状态
Phase-1 建设进行中：Module 1–5 已就位；**Module 6（BROKER_DEMO 执行接线）已开启**（demo-only，详见 `research/MODULE_6_REPORT.md`）。
