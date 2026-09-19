# G1 IMPLEMENTATION AUDIT（R1' · 2026-09-05）

> 范围：实验代码正确性审计（无 Discovery 判定）。代码：`research/r1prime/`（data/features/machine/
> evaluate/metrics/replay_phase5/run_g1/params.yaml）。测试：`tests/test_r1prime.py`（9 项）+ 全库 89/89 通过。

## 代码清单与职责
| 模块 | 职责 | 冻结依据 |
|---|---|---|
| params.yaml | 机器可读参数（唯一来源；sha 锁定） | FINAL_PREREG + STATE_MACHINE_SPEC §4 |
| data.py | H1 registry 载入 / 日聚合（Phase 5 口径） | FINAL_PREREG §1 |
| replay_phase5.py | Phase 5 voltarget 逐字节复刻（对拍基准） | FINAL_PREREG §1 对拍验收 |
| features.py | trailing-only 状态变量 + 信号 G/A_gate/vf_high/adpc_target | FINAL_PREREG §3 + params |
| machine.py | FULL/REDUCED/STOPPED 状态机（整体冻结） | STATE_MACHINE_SPEC §3/§4 |
| evaluate.py | A/B/C 腿暴露与日收益（Phase 5 语义对齐） | BASELINES + 注册解释 I1–I4 |
| metrics.py | 12 维度量子集（G1 所需：return/DD/sharpe/MAR/VaR/ES/exposure） | FINAL_PREREG §7 |

## 注册解释（pre-hoc 冻结，无数据使用；G1 引入的规格补全）
- I1：A/B kill-switch 作用于各自基线序列（AT / FVT daily），避免循环依赖。
- I2：B carrier = FVT（Phase 5 精确 H1 机制）；日收盘门控 μ 乘于次日全部 bar 的 FVT size。
- I3：A base = AT（size 1）；μ∈{1,0}。
- I4：C 比较 FR / FVT / ADP-C；ADP-C 与 FVT 同 H1 机制，唯一差异 = 目标档（按前日收盘 rv 状态
  三档 {0.05,0.10,0.15}，切换点 = trailing q33/q66，params.yaml adpc）→ 同频同成本，Δ 纯归因自适应目标。
- I-a：STOPPED 进入要求 vf_high 出现于 s_in 个连续 gate 日的第 s_in 日。
- I-b：churn = 退出后 churn_window_days 内再进入；下次 STOPPED 退出需 s_out_churn=5 个 clear 日；完成后解除。
- I-c：kill 强制 STOPPED；释放走常规 STOPPED 退出路径。
- I-d：warm-up/缺口 NaN 语义与 Phase 5 逐位一致（groupby-sum skipna），保证对拍与引擎等价。

## 裁决硬检查对照（#1–#10）
1. FVT 对拍：**通过（0.0 误差）** → 见 fvt_replay_comparison。
2. 状态机 spec→code 逐项：G/ρ/s_in/s_out/kill/min-hold/priority/recovery 全部参数化于 params.yaml，
   单测覆盖进入/保持/退出/恢复/churn/kill/优先级（7 场景）→ 见 state_machine_conformance。
3. Adaptive 更新 trailing-only：滚动分位（窗口 ≤b−1，shift 后比较）+ 最小样本缺失即不触发 → 代码 +
   截断检验（见 tsleak_truncation_evidence）。
4. 未来截断重算：截断后历史 state/decision 不变（0.0 差异，121 公共日）→ 见 tsleak_truncation_evidence。
5. 无未注册参数：全部数值在 params.yaml 且 sha 锁定；新增仅为被委托冻结项（I1–I4、ADP-C 切换点），
   pre-hoc、零数据使用 → drift 见 registry_drift_evidence。
6. 基线暴露/机会/收益/DD 基础输出：AT/FVT 全窗描述性指标已出（见本审计末表）——"减少暴露≠变好"
   由 12 维判定结构保证（Discovery 阶段执行）。
7. B-N1 无替代标签：E 保持 q95(252) 原义；无双 feed 满足 → NOT TESTABLE；E2 仅敏感性（注册于
   FINAL_PREREG §2/params label）。
8. DUKA 159 日仅按 pre-reg 一次性跨期使用（非 same-feed cross-period OOS 表述）。
9. FXTM↔DUKA = dual-role（异 feed 异期），gate_report §"跨期/跨 feed 命名声明"沿用。
10. G1 通过后 A/B-N2/C Discovery 方可启动（本审计为 G1 交付）。

## 基线描述性输出（全窗，1× 成本；非 Discovery 判定）
| 窗 | AT ann_vol / Sharpe / maxDD | FVT ann_vol / Sharpe / maxDD | 与 phase5 json 一致 |
|---|---|---|---|
| FXTM H1 239d | 0.343 / 0.405 / −27.9% | 0.108 / 0.446 / −12.9% | ✅（0.0 误差） |
| DUKA H1 159d | 0.158 / 3.754 / −6.5% | 0.159 / 2.852 / −6.5% | ✅（0.0 误差） |

注：AT（满仓）在 DUKA 平滑牛市 Sharpe 3.75 —— 任何门控/降险腿必须证明其净价值与机会成本权衡，
不得以"少暴露"冒充"变好"（12 维判定 + opportunity cost 入账强制）。
