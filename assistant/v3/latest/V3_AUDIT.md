# V3 状态审计报告

生成时间（UTC）：`2026-09-23 10:41:29.363967+00:00`
仓库：`fix/v2-full-system-repair-20260917` @ `ebce041` · worktree_clean=`False`

## 一、当前结论

* 现在是 **1 / 10**
* 是否已完成 10/10：**否**
* 是否已形成 TEST snapshot：**否（TEST_SNAPSHOT = NOT_CREATED）**
* 是否允许进入下一阶段：**不允许（继续收集）**
* 是否存在污染 / 提前实验：**未发现**
* 最终状态：**TEST_COLLECTION_WAIT**

## 二、Session 表

| ID | Start | End | Tick | Valid | Reason |
|---|---|---|---|---|---|
| TEST-S001 | 2026-09-22 07:21:08.832000+00:00 | 2026-09-23 10:39:06.758000+00:00 | 232746 | VALID | tick_count >= 200000 |

```text
session 定义：CONTIGUOUS_SEGMENT，相邻断档 > 3000s 切分；门槛 200000 ticks
TEST_START = 2026-09-22T06:20:00Z
已过去 28.36 小时 · TEST 起点后事件数 232746
最后事件时间 = 2026-09-23 10:39:06.758000+00:00
```

## 三、安全状态

| gate | 值 |
|---|---|
| ORDER_SEND | 0 |
| CALIBRATION | 0 |
| FORWARD | NO |
| LIVE | NO |
| EXPANSION | LOCKED |
| ALPHA_SEARCH | OFF |
| MODEL_TRAINING | OFF |
| FEATURE_MINING | OFF |
| DATA_SNAPSHOT | IMMUTABLE |
| COST_MODEL | CANONICAL |
| V1_CHANGED | False |
| V2_CHANGED | False |
| V3_STRATEGY_CHANGED | False |

MT5 实例：[{"ProcessId": 49300, "ExecutablePath": "C:\\AIQuant\\mt5_instances\\fxtm_demo_v3calib\\terminal64.exe", "CreationDate": "/Date(1789908661485)/"}, {"ProcessId": 64100, "ExecutablePath": "C:\\Program Files\\ForexTime (FXTM) MT5\\terminal64.exe", "CreationDate": "/Date(1790058769100)/"}, {"ProcessId": 50800, "ExecutablePath": "C:\\AIQuant\\mt5_instances\\fxtm_demo_01\\terminal64.exe", "CreationDate": "/Date(1790079731404)/"}]
计划任务：[{"TaskName": "hermes-tick-collect", "State": 3}, {"TaskName": "hermes-v2-cycle", "State": 3}, {"TaskName": "hermes-v2-observer", "State": 3}, {"TaskName": "v3-calibration-pilot", "State": 3}]

## 四、数据完整性

```text
dup_timestamp      = 101
dup_quote          = N/A_COLUMNS_NOT_LOADED
dup_event          = DATA_GAP (no event id in feed)
monotonic          = True
out_of_order       = 0
TEST 数据尾部      = 仍在追加（live 可写）；freeze snapshot 未创建 → 无 immutable 与 mutable 混淆问题
immutable snapshot = 1 个已存在目录 ['V3-SNAP-20260922T025312Z']
snapshot manifest  = C:\AIQuant\research\hermes\trader_v3\research\snapshot\V3_DATA_SNAPSHOT_V3-SNAP-20260922T025312Z.json (exists=True)
事件身份           = DATA_GAP（feed 无 event id，不可证明唯一性）
```

## 五、协议完整性

```text
preregistration_sha256 = e273be091fc38cda0274cd2fededaeb28c2a11cd3398db770a6023d54faf5dc3
model_spec_hash        = a98717dc424b0acaf0f33c01707dff6be540e2c941ee7a4da9fa803a4d31b53c
cost_model_hash        = 6f116cfb2d63bedf6e364e9b5a6c6e15f194f91114e9d0c1780fa4d869cdf0aa
feature_schema_hash    = 2b99c68b3a4a126e27301efbc03c68f6b485fc85565cefcc2a7301a77cc271fc
statistical_plan_hash  = e3ab9ece0eb23155e57d752002a99bcea1ed15c69b49a17a06df0873562bcc69
文档复算 22 份，不匹配 []
PROTOCOL_INTEGRITY     = PASS
```

冻结常量复核：horizons=[5000, 10000, 30000, 60000, 300000] · cost anchor=0.914 bp ·
purge/embargo=300000s · FDR=BH q=0.05 m=20 ·
bootstrap=moving block 2000, block=max(50,10*rho), seed 20260922

## 六、提前实验检查

```text
ALPHA_EXPERIMENT_STARTED   = False
ALPHA_EXPERIMENT_AUTHORIZED= False
PREMATURE_TESTING          = False
证据（TEST_START 后新增的实验类文件）= NONE
进程证据                            = NONE
```

## 七、已知限制（沿用既有结论，未产生新结论）

```text
DATA_GAP            : TRUE_OFI, TRUE_TRADE_FLOW, QUEUE, HISTORICAL_L2, FILL_PROBABILITY, IMPACT (L1), OPPORTUNITY_COST (no fill model)
COST_LIMITATION     : round-trip 0.914 bp vs median short-horizon move; cost/median-move > 1 for h <= 2 s
SIGNAL_LIMITATION   : measured gross edge below cost; best gross approx +0.096 bp
EXECUTION_LIMITATION: retail taker only; passive/queue branch PARKED (no fill probability)
本任务不产生任何新的"有/无 Alpha"结论。
```

## 八、阻塞项

```text
BLOCKERS = ['TEST sessions 1/10 (collection in progress)']
```

## 九、最终状态

```text
TEST_COLLECTION_WAIT
```

```text
NO STRATEGY CHANGE
NO ORDER
NO ALPHA EXPERIMENT
NO V1/V2 CHANGE
```
