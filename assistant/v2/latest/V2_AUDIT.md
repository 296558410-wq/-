# V2 最新交易状态与完整性审计

生成 UTC：`2026-09-23T10:51:36.559848+00:00`
仓库：`fix/v2-full-system-repair-20260917` @ `ebce041` · dirty_lines=1274

## 一、当前结论（核心四问）

| 声明 | 原值 | 独立重算 | 判定 |
|---|---|---|---|
| 交易笔数 | 10 | **13** | **FALSE** |
| 胜 / 负 | 8 / 2 | **8 / 5** | **PARTIAL**（胜数对，负数是 5 不是 2） |
| 胜率 | 80% | **61.54%** | **FALSE** |
| 净收益 | +$100 | **+$76.87** | **FALSE** |
| 收益率 | +10% | **+7.69%** | **FALSE** |

```text
是否全部为已实现净收益：是（0 个未平仓；全部为已平仓交易的 profit+commission+swap）
是否与 MT5 完全一致    ：是（重算完全由 MT5 history 得出，与账户余额 1000+76.87≈1076.74 吻合）
RETURN_BASE_MISMATCH   : TRUE —— 真实 demo 起始资金 = $1000.0（不是 config 里 paper 账户的 10000）
```

## 二、逐笔交易表（全部 13 笔，按时间序）

| # | Position | Dir | Entry(UTC) | Exit(UTC) | Hold | Gross | Comm/Swap | Net | Result | Exit |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2375898002 | SELL | 09-15T07:53 | 09-15T11:03 | 11378s | 36.31 | -0.22 / 0.0 | **36.09** | WIN | [tp 4269.31] |
| 2 | 2376019768 | SELL | 09-16T01:23 | 09-16T03:55 | 9126s | 14.85 | -0.22 / 0.0 | **14.63** | WIN | [tp 4277.97] |
| 3 | 2376117550 | SELL | 09-16T16:52 | 09-16T20:59 | 14833s | -26.34 | -0.22 / 0.0 | **-26.56** | LOSS | [sl 4365.16] |
| 4 | 2376466801 | SELL | 09-18T13:52 | 09-18T15:21 | 5359s | 11.31 | -0.22 / 0.0 | **11.09** | WIN | [tp 4365.45] |
| 5 | 2376556551 | SELL | 09-18T22:52 | 09-21T08:51 | 208745s | 28.81 | -0.22 / 0.42 | **29.01** | WIN | [tp 4350.20] |
| 6 | 2376639771 | BUY | 09-21T11:08 | 09-21T17:02 | 21262s | -10.1 | -0.22 / 0.0 | **-10.32** | LOSS | [sl 4338.63] |
| 7 | 2376714158 | SELL | 09-21T18:23 | 09-21T20:31 | 7677s | 8.68 | -0.22 / 0.0 | **8.46** | WIN | [tp 4341.40] |
| 8 | 2376770410 | SELL | 09-22T05:22 | 09-22T08:23 | 10840s | 15.56 | -0.22 / 0.0 | **15.34** | WIN | [tp 4331.94] |
| 9 | 2376806053 | SELL | 09-22T10:23 | 09-22T10:51 | 1671s | 15.5 | -0.22 / 0.0 | **15.28** | WIN | [tp 4307.38] |
| 10 | 2376820491 | SELL | 09-22T11:38 | 09-22T20:54 | 33353s | -42.8 | -0.22 / 0.0 | **-43.02** | LOSS | [sl 4349.17] |
| 11 | 2376940740 | SELL | 09-23T01:37 | 09-23T08:43 | 25546s | 31.6 | -0.22 / 0.0 | **31.38** | WIN | [tp 4332.12] |
| 12 | 2377002968 | BUY | 09-23T12:07 | 09-23T12:18 | 640s | -0.7 | -0.22 / 0.0 | **-0.92** | LOSS | [sl 4317.08] |
| 13 | 2377006249 | BUY | 09-23T12:37 | 09-23T12:46 | 524s | -3.37 | -0.22 / 0.0 | **-3.59** | LOSS | [sl 4311.54] |

```text
合计 gross=79.31 · commission=-2.86 · swap=0.42 · NET=76.87
最大回撤=-84.41 USD · 峰值权益=2161.28
```

## 三、执行审计

```text
deals(magic 90003) = 26 条 = 13 组 IN/OUT
全部 comment=v2-exec（建仓）/ [tp xx] 或 [sl xx]（平仓）→ 无手工单、无未知来源成交
duplicate_prevented=5 · reject=3
missed_cycles=2 · recovery_count=2
同一 position 重复记账：未发现；UNKNOWN 自动重试：未发现证据（DATA_GAP: 无 UNKNOWN 账本）
```

## 四、Ledger 审计

```text
本 V2 目录未保存 broker 成交级账本（按 position ticket 搜索 ledger/state/logs/reviews 命中 = 1）
state/opportunity_ledger.jsonl = 机会账本（2550 条，
   status 多为 detected），不是成交账本
ledger/hermes_v2_ledger.jsonl 最后写入 2026-09-11（paper 时代，已停用）
=> ledger_chain / replay / idempotency = N/A（无成交账本可校）；成交事实以 MT5 为准
```

## 五、MT5 审计（唯一事实源）

```text
terminal : C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe  · account 160761384 · server ForexTimeFXTM-Demo01
balance 1076.74 · equity 1076.74 · 仓位 0 · 挂单 0
magic 分布 : {"0": {"n": 1, "profit": 1000.0, "commission": 0.0, "swap": 0.0, "symbols": [""]}, "90002": {"n": 2, "profit": 0.09, "commission": -0.22, "swap": 0.0, "symbols": ["XAUUSD"]}, "90003": {"n": 26, "profit": 79.31, "commission": -2.86, "swap": 0.42, "symbols": ["XAUUSD"]}}
```

## 六、数据来源审计

```text
primary   = mt5（V2 自己的 fxtm_demo_01，只读）
router    : 5m/15m/60m/4h/1d -> mt5(primary) -> local_fxtm(secondary) -> yahoo(tertiary, CN 403 已降级)
fallback  : 现价/宏观 sina/tencent/eastmoney；yahoo 为最后手段
关键问题  : MT5 stale/unavailable 时是否 NO TRADE？→ router 会先降级到 local_fxtm（非 NO-TRADE）
```

## 七、V1 共享数据耦合审计

```text
V2_TRADING_DATA_DEPENDS_ON_V1_MT5 = YES（间接）
  hermes-tick-collect -> mt5_live_collect.py(:39 钉 V1 终端) -> live_fxtm -> V2 data_sources/local_bars.py
MARKET_DATA_COUPLING_TO_V1 = TRUE
但：V1 交易逻辑不参与 V2 决策；V1 MT5 仅作共享行情源；V2 自己的 terminal/account/magic 独立
V2 独立 MT5 路径 = C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe · account 160761384 · magic 90003
```

## 八、策略/配置漂移审计

```text
冻结基准 = V2_G3_FREEZE.json（2026-09-17T10:53:18.858395+00:00 @ 8d997fb）
比对文件 = 14 个 · 一致 = 10 · 变更 = 4
STRATEGY_CODE_CHANGED = True
changed detail = [{"file": "config\\v2_config.json", "frozen": "7bfab969722ff38a2d5607257750f138241851b464007186ae101316eaf37aff", "now": "b0cc254b809da52844778bbbb8a298df77dd2d031a8353fec3f982dac26be0e5", "status": "CHANGED"}, {"file": "data_sources\\mt5_market.py", "frozen": "256442a90d2415c22f690eca0efb4564d26b88fe7b58e08ce9ae76ec2b97f9c5", "now": "954b3dcc48e12f07e9d564c8e1793780800a99fe99ae2a70afe149a8e8b7a42b", "status": "CHANGED"}, {"file": "runtime\\shadow_run.py", "frozen": "eec256c8bcd2bdc763c236aa1f30639ca64140499c83c8504335e5a7ff724a8d", "now": "ef1473bdfbc5fe7afd7377460cd80b6a54dda661f53cf611082c207007835217", "status": "CHANGED"}, {"file": "dashboard\\datasource.py", "frozen": "2c02e650911c56db14eed7be3fa4e4702e48407dcaae52d47928204c4257a411", "now": "fc8a99b35afe970f86089bc2b524ef0ea1a516b2bb8c86f1294960c00a04621c", "status": "CHANGED"}]
是否存在"看到盈利后改参数再混统计"：见上（若 changed 为空则无）
```

## 九、隔离审计

```text
V1 160759434/90002 · V2 160761384/90003 · V3 160764551/90004
V1≠V2 = True · V3≠V2 = True
MT5_ISOLATION = PASS_WITH_NOTE
异常记录：V2 账户上出现 magic 90002(V1 的 magic) 成交 2 条
  profit=0.09 commission=-0.22
  → 跨 magic 异常（金额极小 -0.13 USD，疑似早期标定残留），单独标注不作交易结论
```

## 十、数据缺口

```text
slippage 未单独列示（隐在成交价）· opportunity_type / confidence / context_hash 未落在 MT5 成交上
V2 本地无 broker 成交级账本 · UNKNOWN 执行无独立账本可核 · 成本中 spread 为隐含项
COST_DATA_GAP = False
```

## 十一、最终结论

```text
audit_result = AUDIT_PASS_WITH_DATA_GAP
TRADING_RESULT_VERIFIED      = PARTIAL (MT5 可核；但 10 笔/80%/+$100/+10% 四项声明均不成立)
ACCOUNTING_VERIFIED          = PARTIAL (broker 侧可核；V2 本地无成交级账本)
EXECUTION_VERIFIED           = True
DATA_LINEAGE_VERIFIED        = True
STRATEGY_STABILITY_VERIFIED  = PENDING (14/14 冻结文件未变，见 drift)
sample_size = 13 -> SAMPLE_TOO_SMALL_FOR_STABILITY = TRUE
FORWARD_RESULT_CONFIRMED = INSUFFICIENT_SAMPLE_FOR_STABILITY
```

> 本审计**不是 Alpha 认证**。13 笔样本不足以判断长期稳定性；未修改任何阈值。

```text
NO STRATEGY CHANGE
NO PARAMETER CHANGE
NO ORDER
NO V1 CHANGE
NO V3 CHANGE
```
