# V3 CURRENT_STATE — 总控接管时的既有工作分类

生成：2026-09-17 · Owner：V3 总控（OpenClaw main）· 依据：任务书 §三十五

## 0. 隔离确认
- V1 `research/hermes/trader_v1`：**未连/未改**；V2 `research/hermes/trader_v2`：**未连/未改**。
- V3 权威路径 = `C:\AIQuant\research\hermes\trader_v3`（入 Git）。
- 研究数据工作区（room）= `C:\Users\surface\HermesWorkspaces\v3`（**不入 Git**，按其 sha256 登记入 Artifact Registry）。
- V3 独立 MT5：`C:\AIQuant\mt5_instances\fxtm_demo_v3`（magic 90004，只读）。`order_send` 代码层拦截。

## 1. 分类（FROZEN / VALID / HISTORICAL / TRANSITIONAL / INVALID / ALREADY_RUN_ONCE / DATA_GAP）

| 对象 | 分类 | 说明 |
|---|---|---|
| `duka_assembled_v1`（7 tick 文件 / 15,563,968 行） | **FROZEN** | Data Registry 已锁 sha256；缺口已登记 |
| `V3_DATA_SPEC.md` v1 | **FROZEN** | 字段/时间语义/能力边界冻结 |
| `V3_RESOLUTION_AUDIT.md`（feed 分辨率 p50=152ms） | **FROZEN** | 修正历史错误数字 777ms→152ms |
| `V3_MULTIPLE_TESTING_LEDGER.yaml`（F1-F8/48） | **FROZEN**（batch1） | 跑数前冻结 |
| `V3_ADVERSARIAL_AUDIT.md`（G 框架 17 攻击） | **VALID（常设）** | 无 KEEP 主张被提交 |
| `V3_ALPHA_MAP.md` v0（24 族） | **VALID（骨架）** | 方向类 KEEP=0 |
| `p2_net_edge_gate.py` | **FROZEN（工具）** | 唯一冻结哈希 `c364f060…`（96,353B/1580 行） |
| 旧 `p2_net_edge_gate.py@5f51c5ba…` | **HISTORICAL** | 上签字快照，不得删、不得冒充新冻结版 |
| `A000_2s_momentum_z25` | **ALREADY_RUN_ONCE / INADMISSIBLE** | 真实结果 mean −1.9252bp, n=5242, FAIL；计入 F7 累计分母 |
| R-31 真数据跑（taker/passive/sublatency） | **HISTORICAL / PRE-C31 结论** | 旧 P2 latency 实现；不作最终 latency-axis 结论 |
| C-31-1..5（工具落地） | **COMPLETE** | 见 `.p2_r31_33333/P2_R31_FIX_33333.md` |
| 跨市场 DXY→gold（CL-10/CONTRA-08） | **REJECT（CONTRADICTED）** | 原样重跑=自动 REJECT |
| XAG/GC/COMEX lead-lag | **DATA_GAP** | 第二市场同精度数据未到位 |
| `bid_vol`/`ask_vol`（tick）/ candle `vol` | **DATA_GAP(field_unusable)** | 317/403 个取值、买卖近半相等 → 禁作 size/liquidity 代理 |
| ML（F Agent） | **BLOCKED** | 前置=≥1 方向 KEEP；当前 0 |
| V3 MT5 独立账号 | **DATA_GAP** | 复用 demo 凭据；只读、永不发单 |

## 2. 关键已确认事实（带来源）
- 点差实测 p50 **1.6449 bp = 0.347 USD/oz**（`measured_duka_p50`）；房间旧假设 0.20 USD ≈ 偏乐观 2×。
- feed 活跃区间 p50 = **152ms**；延迟档 50/100ms = **UNRESOLVABLE**，250/500ms = **RESOLVABLE_WEAK**，1000ms = RESOLVABLE。
- **无任何一天覆盖满 24h**；每日 `21:00–22:59 UTC` 结构性缺口（~35% 日有数据）。
- tick 与 candle **同源**（非独立第二源）；candle 行有 x2/x3 重复，消费方必先去重。
- A000（2s 动量 z>2.5 / 30s hold）：两独立时段（2023H2/2024Q1）均负 → **FAIL**。

## 3. 阶段/Gate（详见 state/V3_PROJECT_STATE.json）
- **G0 = PASS_WITH_DATA_GAP**（G0-A/B/C 完成，缺口已登记）
- **G1 = INSUFFICIENT_EVIDENCE**（C-31 待 2 项终裁 + §20.10 三读 + co-sign）
- G2/G4/G5/G6 未开；G3（G 审计）常设运行；G8 进行中。

## 4. 未决（需决策或裁定，非阻塞其它）
1. C-31 §3.1：`frac_same_fill_tick` vs `changed` 列命名/判据。
2. C-31 §3.2：生效基 `signals` vs `ticks`。
3. `VALID_DAY` 定义冻结（提案 `hours>=21 AND n_ticks>=1000`）。
4. `bid_vol/ask_vol` provenance（需 DUKA bi5 字段文档）。
5. C4 入场券口径改写（仅在 `hours_covered>=21` 子集上要求 match_rate≥0.99）—— 需批准。

> 引用任何数字必须带 **来源 + 基线名 + tag + sha256**。聊天里的数字不是证据。
