# V3_DATA_SPEC — DUKA 黄金 tick 数据规格（第一版）

**Owner**: `1`（Phase 1 / G0-A 数据接入复验）
**日期**: 2026-09-17
**定位**: 任务书 §十七 A 交付物。**本文件只描述数据是什么**，不含任何策略结论、不含任何 Alpha 判定。
**数据状态**: 研究数据源，**不等同于最终 Broker execution feed**（赵先生 §一 指令）。

---

## 0. 本轮推翻了什么（自我更正，先记）

上一轮我报「`candles_*.parquet` 盘上不存在 → C4 物理阻塞」。**该结论作废**，是我把探针指错了目录：

- 我查的是 `C:\AIQuant\data\staging_duka\assembled\`（那里确实只有 7 个 `ticks_*.parquet`）；
- 实际 candles 在**父目录** `C:\AIQuant\data\staging_duka\`，共 **179 个 `candles_YYYYMM.parquet`，2010-01 ~ 2026-08**，**覆盖全部 7 个 tick 月份**。
- `g0a_ingest_verify.py` 的 `--candles` 默认值也指向 `assembled\candles_*.parquet`（同样指错），所以它当时报 `DATA_GAP / 未提供 candles glob`。**这是工具默认值缺陷 + 我未验证默认值的双重失误，不是数据缺失。**

教训（登记）：**报「物理不存在」之前必须先扫父目录与同级目录**；「glob 匹配为空」≠「文件不存在」。

---

## 1. 数据版本与 source hash

### 1.1 tick（assembled 目录）

路径 `C:\AIQuant\data\staging_duka\assembled\ticks_*.parquet`
总计 **7 文件 / 15,563,968 行**，跨度 `2023-09-01T22:00:00.238Z .. 2026-08-04T20:59:58.419Z`（UTC）。

| 文件 | 字节 | sha256 |
|---|---|---|
| ticks_202309.parquet | 17,360,876 | `c3bb05b0c4d5aaae460db515db45ba81bf1ac2ff4d78f95f48e719240b714a5c` |
| ticks_202310.parquet | 15,351,863 | `ff3ef8fa9fb1c87cb72c5abbdd7b9825a18a0b01fdf44af370f65cf58b4c54f1` |
| ticks_202311.parquet | 20,758,885 | `bd8121f5b973d7c25e2f20448a5b520084c263e8897321b148ea6e1432c08dd7` |
| ticks_202401.parquet | 19,317,011 | `69fc58ee228d54d256828eaf46cb96f5440ceaa6bff6bc88bc74cf09331c4958` |
| ticks_202402.parquet | 21,593,397 | `057c79dec8819e1f2c09ce612c3dd630e41219d315cbc21dadc93f6300958d75` |
| ticks_202403.parquet | 39,455,533 | `24cf560e1910099397c91f462646ca3c7f21f4a8c43768f76060535bbb21f8c4` |
| ticks_202608.parquet | 9,888,184 | `f1ee1e2b7bdd69f6d3930977d5dc87a374b194d1d1384ebc65e26090d45dc8d7` |

**数据集版本号（约定）** `duka_assembled_v1` = 上表 7 个 sha256 的有序拼接。

同目录 `assembled_summary.json` 逐月记录 `dropped: 0`（清洗阶段零丢行）。
跨度缺口：`2023-12` 整月 0 行，`2024-04 ~ 2026-07` 整段 0 行，`2026-08` 只到 08-04。

### 1.2 candle（父目录，非 assembled）

路径 `C:\AIQuant\data\staging_duka\candles_*.parquet` —— **179 文件 / 2010-01 ~ 2026-08**。
每个 tick 月份都有对应 candle 文件（202309/202310/202311/202401/202402/202403/202608 全部存在）。
本规格**只声明其存在与 schema**；逐文件 sha256 尚未全量落账（179 文件，留待冻结时一次性记入）。

---

## 2. 字段规格

### 2.1 tick —— 实为 **L1 报价（quote）流水，不含成交**

| 列 | 类型 | 实测语义 | 可用性 |
|---|---|---|---|
| `ts_utc` | int64 | UTC 毫秒时间戳；202309 文件内**严格单调递增**，重复时间戳 0 | 可用 |
| `bid` | float64 | 买价，USD/oz，3 位小数 | 可用 |
| `ask` | float64 | 卖价，USD/oz，3 位小数 | 可用 |
| `bid_vol` | int64 | 见 §2.3 —— **不可用作挂单量/流动性代理** | **禁用（fail-closed）** |
| `ask_vol` | int64 | 同上 | **禁用（fail-closed）** |

**重要**：`bid_vol`/`ask_vol` **不是成交量**。本 feed **没有带方向的成交流（aggressor side）**，因此任务书 §五 C 的 `signed flow` / `true signed trade volume` 在本数据上**不可测量**，只能做**报价型 OFI**。任务书 §五「Quote OFI ≠ Trade OFI」的禁令在此得到数据层印证。

### 2.2 candle

| 列 | 类型 | 实测语义 |
|---|---|---|
| `day` | str | `YYYY-MM-DD`，**UTC 日**（见 §3.1） |
| `sec` | int64 | 该日内的**秒偏移**，实测网格 = **60 秒**，0 ~ 86340，每日 1440 个 |
| `open/close/low/high` | int64 | USD/oz **× 1000**（整数定点）。已验证：BID/ASK 中位价差 = 347 → 0.347 USD/oz，与 tick 实测完全一致 |
| `vol` | int64 | ~1.0e9 量级（与 tick 侧 `bid_vol` 同量级，provenance 未明，**同判禁用**） |
| `side` | str | `BID` / `ASK` —— candle **分买卖两侧各一套 OHLC** |

### 2.3 `bid_vol` / `ask_vol` 判定为**不可用**（本轮新发现）

全量 15,563,968 行统计：

- 取值数：`bid_vol` **317 个**、`ask_vol` **403 个** —— 15.6M 行只有几百个不同取值；
- 值域窄：`9.2535e8 ~ 1.0069e9`（±4% 带内），众数 `956016770`；
- `bid_vol == ask_vol` 的行占 **47.67%**。

一个真正的 L1 挂单量不可能在 15.6M 行里只有 317 个取值、且买卖两侧近半相等、且值域只有 ±4%。
**结论：该字段无法支撑任务书 §五 「liquidity withdrawal / replenishment」「quote imbalance（按量）」任何一类研究。**
按房间 fail-closed 纪律，**在 provenance 查清并申报之前，一律不得作为 size / liquidity 代理使用**；引用必须写明 `DATA_GAP(field_unusable)`，**不得填 0**。

**连带影响**：赵先生 §五 标为「只能作为代理」的四个项中，**`liquidity withdrawal`、`liquidity replenishment` 从「代理」降为 `DATA_GAP`**；`trade intensity`、`volume` 仍可用 **tick count** 代理（但必须写明「tick 数代理，非成交量」）。
这比 §五 的边界更严，是需要赵先生确认的**收紧**。

---

## 3. 时间语义

### 3.1 candle 的 `day` = UTC 日（假设已证伪到只剩一个）

用 202402 月做窗口假设检验（tick 按 `(ts − offset)` 归日，与 candle 日高低点比，容差 2bp）：

| 假设 | 可比日 | match_rate |
|---|---|---|
| **UTC 日（offset 0h）** | 24 | **0.8750** |
| broker 日 offset 20h | 24 | 0.0417 |
| broker 日 offset 21h | 21 | 0.0476 |
| broker 日 offset 22h | 19 | 0.0000 |
| broker 日 offset 23h | 22 | 0.0000 |

**判定：candle `day` 是 UTC 日**，与 tick 的 `ts_utc` 可直接对齐，**无需时区换算**。

### 3.2 tick 与 candle 同源（已证）

C4 比对中，绝大多数日 `dh_bp = dl_bp = 0.000000`（分位 25/50/75 全为 0），即 candle 高低点与 tick 高低点**逐位相等**。差异只出现在 tick 日内覆盖不全的日子（§4.2）。**两者是同一 feed 的两个聚合层，不是两个独立源。**
→ **推论：candle 可以作为 tick 的「完整性预言机」（oracle），但不能作为「独立第二数据源」。**任何「双源交叉验证」的主张若只用了 tick+candle，**不成立**。

---

## 4. 覆盖与缺口

### 4.1 日历级（1069 日，2023-09-01 ~ 2026-08-04）

| status | 天数 | 含义 |
|---|---|---|
| `GAP_ZERO_TICK` | **801** | 日历上应有交易但盘上 0 tick |
| `CLOSED_WEEKEND` | 128 | 周末休市 |
| `OK` | 121 | 有数据且覆盖较全 |
| `THIN` | 19 | 有数据但极薄 |
| 合计 | 1069 | 其中**有数据 140 日**，逐月分布见 `coverage_summary.txt` |

### 4.2 **没有任何一天是完整的 24 小时**（本轮硬化）

逐日 × 逐小时（hour 0..23）实测，**140 个有数据日中，满 24 小时的天数 = 0**。

- 「缺 1 小时」的日子：缺 `h=21` 的 33 天、缺 `h=22` 的 28 天；
- 「缺 2 小时」：缺 `(22,23)` 的 11 天、缺 `(0,22)` 的 1 天；
- 小时存在率：`h=00..20` 各约 98~109/140；**`h=21` 仅 49/140、`h=22` 仅 49/140**；`h=23` 99/140。

**结论：本 feed 在 `21:00 ~ 22:59 UTC` 存在结构性缺口**（约等于每日结算 / 日切窗口），仅 35% 的日子有数据。任何跨越该窗口的 horizon / holding 分析都会踩到这段。这不是随机缺失，是**系统性缺口**。

### 4.3 candle 侧缺陷：**行重复**

candle 每个 `(day, side)` 的行数只有 1440 / 2880 / 4320 三种，但**distinct `sec` 恒为 1440**：

- 2880 = 每根 1 分钟 bar **重复 2 次**；4320 = **重复 3 次**；1440 = 无重复；
- 重复行的 `open/high/low/close/vol` **逐字段完全相同**（`open` 不一致组数 0、`high` 不一致组数 0）；
- 成因推测：逐日下载拼接时重复 append。

**处理规定**：读 candle 前**必须**先按 `(day, side, sec)` 去重。`high/low` 取 max/min 时不受影响（故 C4 数值不受污染），但 `count` / `vol` 求和类统计**会被放大 2~3 倍**。**这是必须写进任何 candle 消费方的一条硬规则。**

---

## 5. C4 同源高低点交叉核对（真实数据首次落地）

工具：`.g0a_real/c4_highlow_probe.py`（就地实跑，只读原始 parquet）
口径：tick 侧取当日 `bid` 的 max/min；candle 侧取 `side=BID` 当日 `high/low ÷ 1000`；容差 **2bp**，分母 = `(tick_hi + tick_lo)/2`。

### 5.1 结果

| 指标 | 值 |
|---|---|
| 双边可比日数 | **135** |
| MATCH | 108 |
| MISMATCH | 27 |
| **match_rate** | **0.8000** |
| P0 入场券阈值 | 0.99 |
| **判定** | **REVIEW（未过阈值）** |

`dh_bp` 分位：p25/p50/p75 全为 **0.000000**，max 151.45；
`dl_bp` 分位：p25/p50/p75 全为 **0.000000**，max 209.89。
→ **多数日逐位相等，少数日单边偏大**，是典型的「窗口不一致」而非「feed 不一致」形态。

### 5.2 残差归因：MISMATCH **全部**落在 tick 覆盖不全的日子

把 27 个 MISMATCH 日与 `hours_covered` 交叉：

| hours_covered | MATCH | MISMATCH |
|---|---|---|
| 23 | 60 | 0 |
| 22 | 11 | 1 |
| 21 | 12 | 0 |
| ≤20 | 25 | 26 |

- MISMATCH 的 `hours_covered` 中位数 **12**；MATCH 的中位数 **23**；
- **`hours_covered ≥ 21` 的 84 个可比日中，83 MATCH / 1 MISMATCH → match_rate `0.9881`**；
- 方向恒为 `candle_hi ≥ tick_hi` 且 `candle_lo ≤ tick_lo`（candle 窗口是 tick 窗口的超集）——**candle 覆盖完整日，tick 缺小时，缺掉的小时里正好落着当日极值**。

**判定：C4 未过 99% 的原因不是 feed 不一致（同源已证），而是 tick 逐日覆盖不全。**
**没有任何一个 `hours_covered ≥ 24` 却 MISMATCH 的日子**（0 例）。

### 5.3 这条结论的用法

- **candle = 完整日预言机**：可用它反推某日 tick 是否漏掉了极值 → 比 `hours_covered` 更直接；
- **但 candle 不能当独立源**（§3.2）；
- **C4 在 P0 入场券里应改写为**「在 `hours_covered ≥ 21` 的子集上 match_rate ≥ 0.99」，而不是在全体日上——否则它测的是覆盖缺口，不是数据一致性。**该改写需要赵先生批准**（改的是验收口径本身）。

---

## 6. 成本基线的数据侧交叉印证

tick 侧实测往返点差：**p50 = 1.644904 bp = 0.347 USD/oz**，p95 2.761194，p99 7.36114（样本 210,000）。
candle 侧独立聚合：BID/ASK 同 `(day, sec)` 的 open 价差中位数 = **347**（×1000 定点）= **0.347 USD/oz**。

**两者逐位吻合。** 但按 §3.2，这是**同源复核**、**不是第二数据源** —— 仍记 **单源**。
成本数字引用必须带基线名 `measured_duka_p50`，且不得据此宣称「已双源验证」。

另：逐小时点差非均匀 —— `22h` p99 4.87bp、`23h` p99 10.66bp，显著高于其余时段（p95 多在 1.85~2.5bp）。**结合 §4.2 的结构性缺口，21:00~23:00 UTC 这一段要么单列、要么剔除，不得混入总体中位数。**

---

## 7. 能力边界（本文件冻结，严于任务书 §五）

| 层级 | 项 |
|---|---|
| **可直接研究** | bid/ask 收益、spread、spread 扩张/收缩、tick 方向、报价更新强度、micro-price、**报价型** OFI、报价失衡（按价，**非按量**）、tick count、已实现波动 |
| **只能代理** | trade intensity（= tick count 代理）、volume（= tick count 代理）；机制证据只能算**代理证据** |
| **`DATA_GAP`（本轮新增，原列「代理」）** | liquidity withdrawal、liquidity replenishment（因 §2.3 `bid_vol/ask_vol` 不可用） |
| **禁止宣称可测** | true order-book depth、queue position、aggressor-side flow、true signed trade volume、customer flow、market-maker inventory、options flow |

**Quote OFI ≠ Trade OFI** —— 所有报告必须严格区分，措辞不得混用。

---

## 8. 待登记项（我这条线自提，供 registry 取号）

1. **`VALID_DAY` 定义（必须事前冻结，否则挑哪几天就是 forking path）**
   提议：`VALID_DAY := hours_covered ≥ 21 AND n_ticks ≥ 1000`。
   依据：`hours_covered ≥ 21` 的子集上 C4 match_rate = **0.9881**（vs 全体 0.8000）；`hours_covered ≤ 2` 的 24 天属噪声日，应剔除。阈值 `1000` 为待议下限，我**不自作主张定死**，请登记时一并冻结。
2. **`21:00~22:59 UTC` 结构性缺口处置**（单列 / 剔除 / 单列后另报）—— 需事前定，不得看完结果再定。
3. **candle 去重规则** `(day, side, sec)` —— 建议直接写成硬约束，无争议。
4. **`bid_vol`/`ask_vol` provenance 追查** —— 若赵先生能提供 DUKA bi5 原始字段映射文档，可复核 §2.3；在查清前维持禁用。
5. **`served` 字段（tick 侧）无 provenance** —— 本轮未列为阻塞，但引用任何「成交量」类主张前必须回溯。

---

## 9. 本文件明确**不**主张的事

- 不主张 DUKA 可交易性（赵先生 §一：研究数据源 ≠ 最终 Broker execution feed）；
- 不主张已完成双源验证（tick/candle 同源）；
- 不主张任何 Alpha 有无（本文件零市场结论）；
- 不主张 `hours_covered` 就是「有效交易日」的最终定义（见 §8.1，待登记）。

**引用本文件任何数字时必须带**：`V3_DATA_SPEC v1` + `duka_assembled_v1` + 具体节号。
