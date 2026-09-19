# G1 STATE-MACHINE CONFORMANCE REPORT（R1' · 2026-09-05）

> 裁决 #2 硬检查：状态机 spec→implementation 逐项对照（G/ρ/s_in/s_out/kill-switch/min-hold/
> priority/recovery）。实现：research/r1prime/machine.py；参数单一来源 params.yaml [machine]。
> 测试：tests/test_r1prime.py::test_sm_*（7 场景）全部 PASS；全库 89/89。

## Spec ↔ Code 对照表
| Spec 项 | Spec 值（STATE_MACHINE_SPEC §4 / params） | Code | 一致 |
|---|---|---|---|
| ρ (REDUCED 乘数) | 0.5 | params machine.rho → mu=0.5 | ✅ |
| h_red（RED→FULL 滞后） | 3 clear 日 | machine.run REDUCED 分支 | ✅ |
| s_in（STOP 进入连续触发） | 2 日 | FULL/REDUCED 分支 gate_run≥2 | ✅ |
| s_out（STOP→FULL 滞后） | 3 clear 日 | STOPPED 分支（churn 时 5） | ✅ |
| s_out_churn | 5 | churn 分支 | ✅ |
| min_hold | STOP 2 日 / RED 1 日 | i−since ≥ min_hold | ✅ |
| churn_window | 3 日（恢复后再触发） | on_reentry 判定 | ✅ |
| STOP 双条件 | G s_in 日 + vf≥q90(trailing500) | gate_run≥s_in & vf_high | ✅（I-a） |
| kill-switch | 21d cum ≤−8% 或 5d vol ≥3×target | evaluate.kill_series | ✅ |
| priority | B > A > C | 腿分离执行（v1 无组合） | ✅ |
| recovery（正常） | 信号 clear s_out/h_red 日 | clear_run 计数 | ✅ |
| recovery（kill 后） | 走常规 STOPPED 退出（I-c） | 同上 | ✅ |
| missing-data | 信号 NaN → 不触发 | features NaN → gate 0 处理 | ✅ |

## 场景测试（合成信号，确定性）
1. REDUCED 进入（gate 1 日）与退出（3 clear 日）✅
2. STOPPED 需 2 连续 gate 日 + vf_high；min-hold 2；退出 3 clear 日 ✅
3. vf_high 单独不触发（需 gate）✅
4. kill 无条件 STOPPED ✅
5. churn：退出后 3 日内再进入 → 下次退出需 5 clear 日（I-b）✅
6. 无 gate/vf/kill → 全 FULL（恒 1.0 暴露）✅（隐含于 3）
7. μ 映射：FULL=1 / REDUCED=ρ / STOPPED=0 ✅

## 一致性声明
- 状态机作为单一整体在 params.yaml 冻结（含被委托解释 I-a/I-b/I-c）；代码不含任何未注册分支参数。
- 组合层（A+B 等）未实现——按 FINAL_PREREG §4 判定形态，v1 只做单腿，杜绝组合污染。
