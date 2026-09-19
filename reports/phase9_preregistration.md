# PHASE 9 预注册文件 — P1–P7 探测器冻结声明（PHASE 9A PRE-REGISTRATION LOCK）

> 生成：2026-09-05 07:13 (Asia/Shanghai) · 冻结时间 UTC：2026-09-04T23:03:07Z
> 状态：**FROZEN**（本文件与 registry 一致即冻结；任何改动 → 新版本 V2 + 重新 Gate）
> 权威机器文件：`research/phase9/registry/phase9_detector_registry.yaml`（27 探测器 × 27 字段，全展开）
> 配套：`reports/phase9_framework.md` · `reports/phase9_data_audit.md` · `research/registry/hypothesis_registry.yaml`
> Gate：`reports/phase9_gate.md`

---

## 1. 目的

把 Phase 9 Framework 中的七族探测器 P1–P7 从“研究概念”转换为**完全可执行、完全可复现、
完全冻结的实验注册表**。所有参数、阈值、时段、基线、成本、FDR 族、重叠规则在 DISCOVERY 前锁定。
本文件之后：**禁止 Alpha discovery、大规模参数扫描、策略优化、阈值搜索、挑选最好结果、按结果改规则**，
直到 Research Gate 放行。

## 2. 历史 REJECT 接入（防换名重包装）

`research/registry/hypothesis_registry.yaml` 固化 Phase 1–8 全部终审：
- **REJECTED（方向）**：H1 动量、H2 均值回复、H3 突破、H5 趋势 regime、H6 session 方向、
  H7/H8 交互、H9 压缩条件动量(15-240m)、H10 多周期、Phase 4 微观方向(≥5m/M1)、
  Phase 6 状态方向、Phase 8 蜡烛增量预测（DESCRIPTIVE_ONLY）。
- **SUPPORTED_NON_DIRECTIONAL（信息层）**：vol/activity/spread→vol（IC 0.60/-0.24 双源）、
  execution/vol-timing、Phase 7 日程簇聚——一律禁止直接当方向信号。
- 每个 P 族在 map 中声明 `historical_equivalents` + `required_differentiation`；
  统计前不满足差异化者 → `REDUNDANT_WITH_EXISTING_RESEARCH` 自动 REJECT（audit C10 强制）。

## 3. 冻结探测器清单（27 个；P1–6 = 22 ≤ 36；P7 = 5 ≤ 12）

| 族 | 数量 | 探测器（layer@scale） | 攻击优先级(framework §16) |
|---|---|---|---|
| P1 Price dynamics | 3 | disp_z@30s(T) · disp_z@3m(M1) · accel_jerk@1m(M1) | 低（预算最小） |
| P2 Impulse/Failed move | 5 | fail/hold@10s(T) · fail/hold@30s(T) · fail@1m_M1 | **高** |
| P3 Acceptance/Rejection | 4 | accept/reject@3m(M1) · accept/reject@5m(M1) | **高** |
| P4 Momentum decay | 3 | exhaust_fade@10s(T) · @30s(T) · @1m_M1 | 中（须 tick 精度） |
| P5 Compression→release | 4 | release@30s(T) · @1m/3m/5m(M1)（≤5m 限定） | **高** |
| P6 Vol×structure | 3 | hi_act_dir@1m · burst_spread_fade@3m · contraction_spike@10m（≤12 combos） | 中 |
| P7 Tick sequence | 5 | qpressure@10s/30s/1m_agg(T) · impact_fade/hold@30s(T) | **高** |

T = TICK 层（FXTM tick，10s–3m 主战场）；M1 = M1+ 层（FXTM 2026 + DUKA 2023-24 跨期跨源）。
每个探测器在 registry 中携带 27 个冻结字段（数学定义/特征/数据字段/回看/采样/阈值/方向/
信号时间戳/入场/执行假设/出场/持期/重叠/最小有效样本/成本/基线/四段时段/跨期/跨源/FDR/
拒绝标准/placebo/shuffle/扰动/子段）。

## 4. 阈值冻结规则（无数据窥探）

**z 型阈值**：闭式阶梯，仅依赖“每交易日窗口数”，与行情无关：
z(wpd) = max(2.0, Φ⁻¹(1 − 7.5/wpd))，目标 ≈15 个 |z| 事件/日（高斯假设，双尾），下限 2.0σ。

| 尺度 | 窗口数/日 | z 阈值 |
|---|---|---|
| 10s | 8640 | 3.13 |
| 30s | 2880 | 2.79 |
| 1m | 1440 | 2.56 |
| 2m | 720 | 2.31 |
| 3m | 480 | 2.15 |
| ≥5m | ≤288 | 2.00（下限） |

**非 z 固定阈值**（含依据，registry field 6）：
- 恢复比例 50%（failed-move 半数回撤经典定义）；衰减比 ≤0.5 / 0.7；|P|≥0.5 报价失衡且
  min(up,dn)≥3/5/10（流动性下限）；压缩 q_c=0.5×10 窗；释放 ≥0.8×ref_med；突破=收盘越 swing 极值
  （S=20）；accept/reject 确认 O=3 条；P6 状态切点 pct_act 0.8/0.9、rvol 1.0/0.5、spread_z 1.5；
  最小可交易位移 |D|≥0.30 USD（≈1.15× 往返成本）。
- 全部阈值带 ±1 邻域扰动检验（±10% / ±0.1z / ±5pp 等），≥4/5 邻域保持符号与显著。
- **任何“先看结果再定阈值”的探测器禁止进入本注册表**（本表 27 个全部为固定阈值 + 书面依据）。

## 5. 成本模型冻结（taker；mid PnL 禁止作为成功标准）

- 净期望 = 方向 mid 收益(持期) − 往返成本。FXTM：hs=0.08 + 滑点 0.10 → 往返 **0.26 USD**
  （~0.6bp @4391），延迟 1 tick。DUKA（bar 层）：hs=spread_level/2（0.155 / 0.35）+ 0.10 →
  往返 0.41 / 0.80 USD（~2–4bp @2023-24）。压力 ×1/×2/×3；先过 ×1 成本门。
- maker 假设标记为理想化，永不用于 PASS。

## 6. 时段冻结（UTC；独立日门槛已内建）

| 层 | DISCOVERY | VALIDATION（单次确认） | OOS（锁定一次性） | CROSS-PERIOD / CROSS-FEED |
|---|---|---|---|---|
| TICK (FXTM 23d) | 2026-08-04→08-26 | 2026-08-26→09-04 | **PENDING：DUKA tick**（窗内不可再切；≤1m 结论只能到 VALIDATION 级） | DUKA tick 2023-09..2024-03（待下载，Gate 7 前置） |
| M1 (FXTM 2026 + DUKA) | FXTM 05-26→08-03 | FXTM 08-04→08-17 | FXTM 08-18→09-04 | DUKA M1 2023-09-01→2024-03-16（异窗异源，双重角色已声明） |

日级门槛：≥15/23 正天数（FXTM tick 组合窗）；≥60/130（DUKA M1）。有效样本：D≥300 /
V≥150 / DUKA OOS 级 ≥1000 非重叠条目；低于阈值 → INSUFFICIENT_N → 至多 EDGE UNCERTAIN。
**禁止用 OOS 选参数**（本注册表无任何 OOS 拟合参数）。

## 7. 统计协议冻结（全部强制）

- 非重叠入场（同探测器相邻入场 ≥ 持期；同族同刻跨尺度去重取粗尺度；重叠 >30% → 联合 FDR 单元）。
- 日聚类 block bootstrap/permutation ≥1000；BH-FDR q=0.05 两层：族×层 + 整轮 VALIDATION 幸存集。
- 四防线：延迟信号(+1 tick/bar) · 反号信号（对称有效 → artifact REJECT）· placebo 事件（同活动桶
  非事件时点，95 分位）· shuffle（日块符号置换）。子段：周/月/日块 ≥3/4 符号一致 + 正天数门槛。
- 嵌套判定：对“同族最优简单基线”（B0–B8）ΔIC/ΔAUC 日块 bootstrap CI95>0，仅优于 random 者 REJECT。
- 每个 P 族的等价探针（≥5m 聚合复算 / 去条件版本）用于检出“换名重包装”，命中即自动 REJECT。

## 8. 判定输出

仅 **PASS / REJECT / EDGE UNCERTAIN** 三种 token；本流水线全域禁止主观/愿望性措辞
（含 promising / interesting / potential / looks good 等）。REJECT 触发条件见 registry field 23。

## 9. MT5 安全（REAL 账户防护）

- 现状：已检测到 **REAL 账户**（ForexTimeFXTM-Live01）；单一已装终端登录 live 账户，
  无法在本研究环境内切换 DEMO（需另装终端/另配 demo 凭据）→ 按指令建立只读模式：
  - `configs/mt5_research_readonly.env`：`MT5_RESEARCH_READONLY_MODE=1`（fail-closed 环境门）
  - `tools/mt5_readonly.py`：`ensure_mode()` + `enforce_readonly_mt5()`（将 order_send /
    account_update / calc_* 等置换为抛 `MT5ReadonlyViolation` 的函数）+ `audit_static()` 静态扫描
  - Phase 9 及以后任何触碰 MT5 的代码必须先过 guard；全仓静态扫描 0 命中（audit C11）。
- 只读数据拉取（copy_rates/copy_ticks/symbol_info）不受影响；本阶段未连接终端、未触碰数据。

## 10. 完成标准对照

14 项完成标准逐项状态见 `reports/phase9_gate.md`（audit 证据 `reports/phase9_gate_evidence.json`，
22/22 检查通过）。本文件与 registry 均为冻结物；DISCOVERY 未经 Research Gate 不得启动。
