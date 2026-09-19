# V2 DASHBOARD FULL-CHAIN AUDIT — 20260917

只读审计（不改策略/引擎）。逐层：真实来源 / 更新时间 / 最后成功 / 失败处理 / Dashboard 显示。

| 层 | 真实来源 | 更新时间 | 失败处理 | Dashboard 显示 |
|---|---|---|---|---|
| 数据源 | Yahoo/Sina/Tencent/Eastmoney/CFTC/BLS/news（router） | 每 cycle | cache/last_valid；失败入 gaps | 数据状态项（正常/较旧/异常/暂无 + 时间 + 来源） |
| Router | `data_cache/router_audit.jsonl` + `last_selected()` | 每取数 | audit 可见；source_id/fallback_level | 技术详情（Router 启/停） |
| Agent1 | `state/agent1_latest.json` | 每 cycle | `data_quality.gaps` | 数据状态·技术数据（age 取最新 bar） |
| Agent2 | `state/agent2_latest.json` | 每 cycle | `data_gaps` / `news_status` / `macro_completeness` | 数据状态·宏观/新闻；最近问题 |
| Hermes | `run_state.last_decision` | 每 cycle | gate WAIT/REJECT | 当前交易判断 + 为什么没有交易 |
| Decision | `decisions/*.raw.json` | 每 cycle | — | 技术详情（decision_id） |
| Risk | executor sizing（FLOOR_TO_STEP） | 每 TRADE | RISK_LIMIT 拒绝 | 技术详情 |
| Broker Precheck | `broker_validate` | 每 TRADE | PRECHECK_REJECT（不发单） | 系统健康·Broker |
| Shadow Execution | PAPER（RUN_META.shadow） | 每 TRADE | 无 broker 调用 | 当前运行阶段（Shadow 模拟验证 / 真实下单：否） |
| Position | `broker_account`（仅 BROKER_DEMO 探测） | ≤30s | 不可读 → **无法确认** | 当前持仓（无/未知） |
| Ledger | `run_dir/ledger.jsonl` | 每 cycle | 截断→BLOCK | 系统健康·账本 |
| Replay | `timeline.replay_match` | 每 cycle | MISMATCH→异常 | 系统健康·Replay（一致/不一致） |
| Scheduler | `state/v2_run_health.json` | 每 15m | missed/duplicate 计数 | 系统健康·调度器 |
| Health | 上述聚合（`dashboard/datasource._observability`） | 每快照 | 显式未知 | 系统健康（🟢/🟡/🔴 + 展开） |
| Dashboard Backend | `datasource.build_snapshot`（只读） | SSE 2s / 轮询 3s | 失败计数 → 刷新状态警示 | 顶部“系统最后更新” + 刷新状态 |

## 关键审计结论（修复前 → 修复后）
1. **模式误标**：BROKER_DEMO 显示为 PAPER/虚拟账户 → 修复：`mode_info` + 中文运行模式（Shadow 模拟验证/Forward/实盘）。
2. **sizing 硬编码 $10,000** → 修复：来自实际账户；缺失显式标记。
3. **fake-zero PnL / 持仓** → 修复：未知显式（“无法确认/未知”），不用 0 掩盖。
4. **无统一状态源** → 修复：新增 `observability` 统一聚合（只读；不重算策略/PIT/风险）。
5. **技术名词堆砌** → 修复：首页中文；技术细节折叠。
6. **无“为什么没有交易”** → 修复：当前交易判断卡（数据项 ✓/✗ + 结论）。
7. **无刷新失败可见** → 修复：顶部刷新状态（连续失败→🔴）。

## 未改（保持只读）
Dashboard 无任何下单/改单/改策略/启动 forward 能力（`server.py` 仅 GET；无 POST）。
