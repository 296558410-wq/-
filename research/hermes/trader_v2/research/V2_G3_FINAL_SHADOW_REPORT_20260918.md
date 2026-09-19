# V2 G3 FINAL SHADOW REPORT — 20260918

## 数据层冻结版本
- freeze git: `8d997fb` · schema pit=`pit/1` · input_snapshot=`input_snapshot/1`
- versions: `{"strategy_version": "hermes2-prompt/0.1.0", "agent1_version": "agent1/0.1.0", "agent2_version": "agent2/0.2.0-pit", "hermes_version": "hermes2/0.1.0", "paper_engine_version": "paper/0.1.0", "ledger_version": "ledger/1"}`
- freeze清单: research/V2_G3_DATA_FREEZE_20260918.md

## 新 Shadow run
- run_id: `V2-PAPER-20260918-102531-8648`
- 开始: 2026-09-18T10:25:31.063126+00:00
- 结束: 2026-09-19T10:25:31.063126+00:00
- 已运行: 0.7 h (不足 24h)
- cycle 数: 2
- 决策: TRADE 1 / WAIT 1 / REJECT 0
- 执行: attempts 1 / executed 1 / rejected 0
- duplicate_skips: 0

## 每类 WAIT 原因（reason_code）
- TRADE_OK (证据通过门禁): 1
- PRICED_IN (已 priced-in): 1

## 数据源稳定性 / GAP
- 主行情: XAUUSD (router: mt5→local_fxtm→yahoo) + quotes/macro sina/tencent(国内) + reference GC=F
- 数据 GAP: ["central_bank_policy_rates:no_direct_api(placeholder)", "bls_macro:no_domestic_source(BLS 403)", "cot:no_domestic_source(CFTC 403)", "global_gold_etf_flows:WGC_JS(未取)", "central_bank_gold_purchases:no_source"]
- COT/BLS/东财资金流/WGC/央行购金/政策利率 = 无稳定国内源 → 显式 GAP（不填 0、不伪造）

## 证据链
- Replay MATCH: 2/2
- Ledger hash chain: PASS {"n": 10, "head": "be73c6a65e25e764d063be22c78922f4571c1598d66394098035bcc8c855d1c5"}
- Scheduler 漏周期: 0
- Agent1 失败: 0 · Agent2 失败: 0 · Hermes 失败: 0 · Ledger 失败: 0
- input_snapshot: 每 cycle 2/2
- Router provenance: per-cycle pit_cache source/source_hash (见 timeline + inputs/)

## 安全不变量
- execution_mode: BROKER_DEMO (PAPER=不连 broker 下单路径)
- BROKER_ORDER_SENT: FALSE
- FORWARD_VALIDATION_ALLOWED: YES (保持 NO)
- FORWARD_STARTED: FALSE
- V1 隔离(静态): PASS

## 20 项 PASS 条件（§九）
- 1_连续运行: FAIL
- 2_scheduler无漏周期: PASS
- 3_无stale_backfill: PASS
- 4_XAUUSD标的一致: PASS
- 5_PIT无未来数据: PASS
- 6_Router来源可追溯: PASS
- 7_Agent1_provenance: PASS
- 8_Agent2_provenance: PASS
- 9_Hermes_input_snapshot: PASS
- 10_WAIT可解释: PASS
- 11_Replay全MATCH: PASS
- 12_Ledger_hash_chain: PASS
- 13_无真实Broker单: FAIL
- 14_V1无变化: PASS
- 15_Dashboard与backend一致: PASS
- 16_stale_error_unknown未伪装: PASS
- 17_数据源失败显式暴露: PASS
- 18_无新策略修改: PASS
- 19_无未批准参数优化: PASS
- 20_单冻结版本样本: PASS

## FAIL / BLOCKED / UNKNOWN
- blocked: null
- hard_fail: ['13_无真实Broker单']
- 未决(P1 residual / 数据 GAP): COT/BLS/东财资金流/WGC/央行购金/政策利率

## G3 最终结论
**FAIL**
- 理由: 关键条件未过 ['13_无真实Broker单']

> 下一阶段: **不得自动进入 Forward**。G3 PASS → 等待人工确认 → G4。FORWARD_VALIDATION_ALLOWED 保持 NO。
