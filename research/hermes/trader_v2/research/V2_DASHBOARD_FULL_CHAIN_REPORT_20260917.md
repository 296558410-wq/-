# V2 DASHBOARD FULL-CHAIN REPORT — 20260917

## 结构（两层：人话 / 技术详情）
首页（中文）：V2 当前状态（系统状态·市场·数据·数据最新·当前判断·持仓·余额/权益·最后更新）／数据状态／当前交易判断（含“为什么没有交易”）／当前持仓／账户资金／系统健康／当前运行阶段（阶段·模式·真实下单·Forward Gate）／V1 安全状态／最近发生的问题／技术详情（折叠）。

## 后端统一状态源
`dashboard/datasource._observability()`：只读聚合，**不重算策略/PIT/风险**；所有未知显式表达（“暂无数据/无法确认/未知”）。
新增 `snap["observability"]`：`system_status / data_items / run_mode / stage / real_orders / forward_gate / last_decision / position_known / positions / v1_isolation / recent_problems / last_update / instrument`。

## §25 一致性测试（`tests/test_dashboard_fullchain.py` 37/37）
| 测试 | 结果 |
|---|---|
| 1 数据停止更新 → 较旧/异常（非正常） | PASS（`_obs_item` 阈值 + 顶部“数据最新”） |
| 2 数据源 ERROR → 异常（非 0） | PASS |
| 3 Broker UNKNOWN → 持仓=无法确认（非 0） | PASS（`position_known=False`） |
| 4 Replay FAIL → 不一致/异常 | PASS（`replay_status`→bad） |
| 5 Forward Gate=NO → “未允许” | PASS |
| 6 Shadow → 运行模式=Shadow 模拟验证 / 真实下单=否 | PASS |
| 7 V2 Dashboard 不读 V1 ledger/run_state | PASS（datasource 无 trader_v1 引用） |

## §26 更新及时性（实测）
- 后端快照：按需构建（SSE 每 2s / 轮询 3s）。
- `data_age = now − data_ts`（`_age_s`；未来 ts → “数据时间异常”）。
- 观测（本地快照）：黄金价格 age≈595s、技术数据≈1534s、宏观≈1176s（随 cycle 变化）。
- 未做浏览器端抓包测量（诚实标注；不写“实时”）。

## §28 只读隔离
`server.py` 仅 `GET`（无 POST/无下单/无改配置）；Dashboard OFF/ON 不影响 Shadow（独立进程读取）。

## §33 测试
`test_dashboard_fullchain` 37/37（unit+contract）；`test_dashboard_consistency` 12/12（既有，已更新）。

## 限制 / 未竟
- 未做浏览器端 E2E 截图/性能基准（§27 部分仅静态论证）。
- 数据项逐项 `received_ts`/`last_success_ts` 未全部可得 → 部分显示“暂无/未知”（不伪造）。
- Dashboard 仍起 MT5 只读子进程（≤30s）用于 Broker 账户；与“绝不触网”旧表述不符（显示层未改探测）。

## 与流水线关系
本任务**不影响 G3**：不改 Shadow ledger/decision/snapshot/run；不提前结束 G3；不解除 Forward Gate；不启动 Forward。
