# Hermes V2 · 控制面板（Control Panel）

> 只读 · PAPER · localhost:8788 · **绝不触碰 V1（`research/money_hunter/dashboard` 的 8787）**

## 为什么比 V1 面板更强

| 维度 | V1 面板 (8787) | V2 面板 (8788) |
|---|---|---|
| 数据更新 | 服务端渲染 + 前端 10s 轮询 | **SSE 实时推送**（变更即推，2s 心跳）+ 轮询兜底 |
| 架构 | 单文件 http.server + 字符串拼 HTML | FastAPI + 独立数据层 + 前后端分离 SPA |
| 数据面 | 行情/MT5 demo 账户/持仓 | Run/Manifest/Metrics/Ledger/Timeline/Decisions/Sizing/双 Agent/安全隔离 |
| 可视化 | K 线 + 表格 | Canvas 净值曲线(渐变+辉光)、决策热力图、占比条、实时脉冲、分级卡片 |
| 安全表达 | 弱 | 顶部常驻安全徽章（MODE/LIVE/BROKER/DEMO/V1 isolated）+ 完整性告警 |
| 仓位 | 无 | **逐 TRADE sizing 遥测**（raw→floor→min/max→notional→risk，含 verdict/reason） |
| 隔离 | 与交易同仓 | 独立目录、独立端口、纯只读、不 import V1、不触网、不下单 |

## 目录
```
trader_v2/dashboard/
├── datasource.py         # 只读聚合层 → snapshot dict
├── server.py             # FastAPI: /  /api/snapshot  /api/stream(SSE)
├── static/
│   ├── index.html        # 面板骨架
│   ├── style.css         # 深色玻璃拟态 + 渐变/脉冲
│   └── app.js            # SSE 接入 + Canvas 渲染
├── run_v2_dashboard.cmd  # 一键启动
└── README.md
```

## 运行
```
C:\AIQuant\.venv\Scripts\python.exe C:\AIQuant\research\hermes\trader_v2\dashboard\server.py
# 或双击 run_v2_dashboard.cmd
# → http://127.0.0.1:8788
```
端口可用环境变量 `V2_DASH_PORT` 覆盖（**禁止设为 8787**，server 会直接拒绝）。

## 数据来源（全部只读）
```
state/runs/ACTIVE.json                         活动 run
research/runs/<rid>/run_manifest.json          冻结版本/commit/config_hash
research/runs/<rid>/run_state.json             status/counters/failures/windows
research/runs/<rid>/metrics.json               finalize 后
research/runs/<rid>/ledger.jsonl               DECISION/EXECUTION/FILL/POSITION/PNL/ACCOUNT...
research/runs/<rid>/timeline.jsonl             agent1/agent2/hermes/exec 时间线
research/runs/<rid>/decisions/*.raw.json       Hermes 决策
research/runs/<rid>/paper_account.json         账户
state/agent1_latest.json  state/agent2_latest.json
config/v2_config.json                          contract/risk/execution 安全字段
```

## 面板分区
1. 顶栏：品牌 + LIVE 脉冲 + 安全徽章（MODE/LIVE/BROKER/DEMO/V1）+ 24h 进度条
2. KPI：Equity / realized PnL / Cycles / TRADE / WAIT / REJECT / 持仓 / dedup
3. 账户净值曲线（Canvas：网格 + 渐变填充 + 辉光折线 + 末点）
4. 决策节奏：15m window 热力图 + TRADE/WAIT/REJECT 占比条
5. Agent1：多周期表 + 现价 + regime/vol + 候选
6. Agent2：宏观(USD/10Y/real) + 叙事vs资金流 + 数据缺口 + 冲突
7. Sizing 遥测表：raw / floor / tgtR / actR / notional / status / reason（超风险标红）
8. 决策流：最近 Hermes 决策卡（方向/入场/SL/TP/置信）
9. Ledger 事件表 + 系统/新鲜度/失败计数/隔离

## 设计原则
- **诚实**：无数据即显示"暂无"，绝不编造持仓/盈亏/时间戳。
- **只读**：数据层无写操作；面板不产生任何交易副作用。
- **隔离**：不 import trader_v1；端口独立；V1 与 8787 完全不受影响。
- **实时**：SSE 变更推送；断线自动回退轮询。
