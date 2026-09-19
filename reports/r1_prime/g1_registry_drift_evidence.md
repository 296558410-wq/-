# G1 REGISTRY DRIFT EVIDENCE（R1' · 2026-09-05）

> 裁决 #5/#21：G1 不得引入未注册参数；registry 被意外修改 → 立即停止。
> 证据（g1_evidence.json drift 段 + git）：

| 对象 | SHA-256 / commit | 状态 |
|---|---|---|
| research/r1prime/params.yaml（R1'_PARAMS_V1） | `1eb807d5e4c9ab26…`（全文 sha） | G1 冻结锚；代码只读此文件 |
| research/phase9/registry/phase9_detector_registry.yaml | `430ea42b39ba19df…`；git 最后修改 = `cf76214`（Phase 9A 锁） | ✅ 零漂移 |
| research/registry/hypothesis_registry.yaml | git 最后修改 = `cf76214` | ✅ 零漂移 |
| R1' 权威文档（registry/*.md） | 本轮 commit `7c91677` 起未再改动 | ✅ |

## 参数单一来源与防漂移
- 全部冻结数值唯一存放于 params.yaml；machine/features/evaluate 从之读取；代码内无重复字面量参数
  （容忍项：Phase 5 复刻所需的 vol 公式常量来自 params vol_forecast 段）。
- 测试 test_params_complete 校验关键值（registry_id / E=252 / ρ=0.5 / tiers）。
- 实现 drift 检查：run_g1 输出三个 sha；若 phase9 冻结物 sha 变化 → 立即停止（本证据确认未变）。

## G1 新增参数声明（被委托冻结项；全部 pre-hoc、零数据使用；已在审计 I1–I4/I-a–I-d 登记）
- ADP-C 三档目标与切换点（q33/q66 trailing500）——FINAL_PREREG §5 委托冻结，本 G1 完成取值。
- G 组合最终式 G = G4 ∨ (G1 ∧ a_t≥q70)（FINAL_PREREG §3 已注册）实现于 features.G。
- 状态机解释 I-a/I-b/I-c 与 kill 基线 I1 —— 语义补全，非新参数。
结论：**registry drift = PASS**；未引入任何未注册参数/阈值/状态/组合规则。
