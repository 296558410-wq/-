# MODULE_5_PRE_AUDIT — Hermes V2 实时 Paper Shadow Run（前置审计）

> BASE_COMMIT: `1a389d0`。本模块只做「受控实时 Paper 运行」，不改 Agent/Hermes 策略、阈值、成本、风控；不下 broker/demo/live 单；不动 V1。

## 1–6. 实际入口
| 模块 | 入口 | 说明 |
|---|---|---|
| Agent1 | `agents/technical/agent1.py: build(cycle)` → `state/agent1_latest.json` | 确定性技术快照(无 LLM) |
| Agent2 | `agents/macro_global/agent2.py: build(cycle)` → `state/agent2_latest.json` | 宏观/地缘/资金流快照(无 LLM) |
| Hermes | `hermes/hermes.py: run(cycle)` → `state/hermes_decision_latest.json` | 读 agent1/agent2 → discovery → gate → decision |
| Paper Loop | `runtime/shadow_run.py: run_cycle(run_id)` | Agent1→Agent2→Hermes→freeze→Paper→Ledger→Replay |
| Ledger | `ledger/ledger.py: append_event/verify_ledger`（每 run 独立文件 `research/runs/<run_id>/ledger.jsonl`） | append-only |
| Replay | `ledger/replay.py: replay(path, "PAPER")/conservation` | 在线 checkpoint 对账 |

## 7. 时间周期
Agent1=15m, Agent2=60m, Hermes=15m, Paper/PnL 随决策; run 窗口默认 1440 min(一个交易日)。

## 8. 输入数据来源
行情: Yahoo GC=F(主序列, point-in-time, 剔除未收盘) + sina/tencent/eastmoney 现价回退; 宏观: CFTC COT / BLS / ECB / Treasury; 新闻: wallstreetcn / CNBC RSS。均为当时可见时间戳。

## 9. 输出数据结构
Decision Contract（同 Module 4）：`decision_id/decision/symbol/side/entry_reference/SL/TP/reason/confidence/context_hash/input_hash/strategy_version`；RAW(原始 Hermes 输出, 全字段) + FROZEN(normalize+冻结) 双份保存于 `research/runs/<run_id>/decisions/`。

## 10. 失败时的行为
Agent1 失败→该轮标 `agent1_error`，**不得伪装新数据**；Agent2 失败→标 data_gap；Hermes 失败→不产生 Paper Order（记 SYSTEM 失败）；Ledger 写入失败/校验失败→**NO EXECUTION** 并 block。Paper!=Replay → `PAPER_REPLAY_MISMATCH` → RUN_BLOCKED。

## 11. 重启后的行为
run_state/ACTIVE/manifest/ledger/timeline 全部落盘；重启后读回同一 run_id 与已处理窗口集合，继续。

## 12. 避免重复决策
按 `decision_window`(15m 桶)+`input_hash` 去重：同窗口已处理 → `skipped_duplicate`，不再产生 Decision。

## 13. 避免重复执行
去重键在决策前判定；Paper 未执行则不写 EXECUTION_* 事件；`duplicate_skips` 计数留痕。

## 14. Paper-only 保证
启动调用 `assert_paper_only()`（config: execution_mode=PAPER, live_trading=false, broker.enabled=false, broker_demo_enabled=false），任一不符 → REFUSE_TO_START；不可用参数/环境变量绕过；每事件带 `execution_mode=PAPER`。

## 15. V1 隔离
代码 0 处引用 V1(`trader_v1/live_fxtm`)；不读 V1 ledger/account；不碰 V1 MT5(PID 1348)；独立 state/ledger/account。
