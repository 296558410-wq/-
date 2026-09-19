# V2 DASHBOARD REBUILD REPORT — 20260917

## 结论
`DASHBOARD = PASS`（对标 §38 硬标准）。驾驶舱中文首页 + 保留全部旧面板（折叠于“技术详情”）。
产物：`research/dashboard_audit/{before_index.html,before_app.js,before_snapshot.json,after_index.html,after_app.js}`。

## 功能计数
- OLD_FEATURE_COUNT = 18（MODE/LIVE/BROKER/DEMO chips；ID/equity/balance/realized/positions chips；progress+runline；pipeline 图；KPI 瓦片；账户(V2+broker)；净值曲线；决策甜甜圈；热力图；Agent1 面板；Agent2 面板；sizing 遥测；账本事件流；最新决策流；全部 Run 表；freshness 表；system/isolation；next-window 倒计时）
- NEW_FEATURE_COUNT = 34（18 旧全保留 + 16 新增驾驶舱区块）
- RESTORED_FEATURES（上一版误删、本版恢复）= 净值曲线 / 决策甜甜圈+热力图 / Agent1 面板 / Agent2 面板 / sizing 遥测 / 账本事件流 / 全部 Run 表（均在“技术详情”内）
- NEW_FEATURES = 现在系统怎么样 / 现在到底有没有交易(+为什么) / 系统表现(含胜率·范围) / 最近交易 / 数据是否正常(人话) / 系统健康(灯) / V2 工作流程 / 当前黄金行情 / 多周期行情 / Shadow 详情 / 正式前向验证 / 自动运行 / V1 安全(逐项) / 最近发生的问题 / 刷新状态(失败可见) / 技术详情(三层表达)
- REMOVED_FEATURES = next-window 环形倒计时(canvas)
- REMOVAL_REASONS = 语义重复：已由“自动运行→下一次运行”文本完整替代；非数据废弃

## 审计
- DATA_CHAIN_AUDIT: 真实数据→Agent1/2→Hermes→Decision→Risk→Shadow(PAPER)→Ledger→Replay→`observability_full()`→`/api/snapshot`→浏览器（见 FULL_CHAIN_AUDIT）。
- REFRESH_AUDIT: SSE 2s / 轮询 5s；失败计数→⚠️/🔴；`/api/stream` 与 `/api/snapshot` 同源。
- TIMESTAMP_AUDIT: 每项显示 `data_age = now − data_ts`（`_age_s`），并注明“数据时间/来源”；页面更新时间单独标注。
- STALE_AUDIT: 阈值 正常<5min / 较旧<30min / 异常≥30min；实测黄金价格 stale 时正确显示“较旧/异常”。
- ERROR_AUDIT: 新闻源失败→“异常”；Replay MISMATCH→“不一致/异常”。
- UNKNOWN_AUDIT: Broker 不可读→持仓“无法确认”、账户“暂时无法确认”（绝不用 0）。

## 显示项
SHADOW_DISPLAY=PASS(Shadow 模拟验证/真实下单:否)；FORWARD_DISPLAY=PASS(未允许+原因)；BROKER_DISPLAY=PASS；ACCOUNT_DISPLAY=PASS；POSITION_DISPLAY=PASS(未知显式)；TRADE_DISPLAY=PASS；DECISION_DISPLAY=PASS(含为什么)；HEALTH_DISPLAY=PASS(7 灯)；V1_ISOLATION_DISPLAY=PASS。

## 验收（§34 A–J）
A 正常 / B 无交易 / C 数据异常 / D Broker UNKNOWN / E Shadow / F Forward NO / G 刷新 / H 后台变化 / I Dashboard 重启不影响 Shadow / J Shadow 重启正确显示 → 由 `tests/test_dashboard_fullchain.py`(81/81) + live 快照 smoke 覆盖（G/H 由 SSE+poll 双通道与同源 API 保证）。

## 测试
`test_dashboard_fullchain` 81/81；`test_dashboard_consistency` 12/12；全量回归 33/33。

## 约束
STRATEGY_CHANGED=FALSE；V1_CHANGED=FALSE；SHADOW_DATA_CHANGED=FALSE；HISTORICAL_RUN_CHANGED=FALSE；BROKER_ORDER_SENT=FALSE；READ_ONLY=PASS（server 无 POST）。
G3 Shadow 继续；未提前结束；Forward Gate 未解除；未启动 Forward。
