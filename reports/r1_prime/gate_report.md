# R1' PRE-REGISTRATION GATE REPORT（阶段 2 · 2026-09-05）

> 六项审计（宪章 §25）逐项执行。判定：**GATE PASS（CONDITIONAL）** ——
> A、C、B-N2 腿放行至 DISCOVERY；B-N1 腿挂数据前置条件 D1/D2（未满足前不启动 N1 段）。
> 审计均为文档/静态/只读；无任何行情计算、回测或参数搜索。

---

## 1. Registry Audit —— PASS
- Phase 9A 冻结物零漂移：`phase9_detector_registry.yaml` 与 `hypothesis_registry.yaml` 最后修改
  commit = `cf76214`（锁）✓；本轮 R1' 文件全部独立新增，未触碰冻结文件。
- R1' 文件链齐备且互引一致：MECHANISM_DEFINITION / NOVELTY_MAP / PREREGISTRATION_DRAFT /
  PREREGISTRATION_REVIEW / STATE_MACHINE_SPEC / DECISION_BASELINES / DATA_WINDOW_AND_LABEL_AUDIT /
  SELF_AUDIT / FINAL_PREREGISTRATION（research/registry/）✓；knowledge_map KD-R1A/B/C 已登记（状态将更新为
  PREREGISTERED）✓。
- YAML 可解析性：knowledge_map 等 yaml 文件 parse OK ✓。

## 2. Reproducibility Audit —— PASS（计划级，实现门控）
- 冻结版规定：确定性种子、manifest（git sha + registry version + dataset id + seed + 数据版本）、
  复现脚本、Phase 5 FVT 对拍验收（ann_vol/sharpe/max_dd ≤2%，cost ≤5%）✓。
- 实验代码尚未编写 → 对拍与确定性以 DISCOVERY 前验收脚本为强制前置（conditional gate item G1）。

## 3. ts-leak Audit —— PASS（规格级；实现级强制）
- 规格静态检查：状态变量全部 ≤t 收盘（FINAL PREREG §3）；决策 t 生成、t+1 开盘执行；E/E2 标签
  与决策路径隔离（E 确认分量仅事后分类，宪章 §10）；切分索引确定性 ✓。
- 实现级：ts-leak 冒烟 + 截断重算一致性为 DISCOVERY 强制前置（G1，与 §2 同项）。

## 4. Data Availability Audit —— PASS（CONDITIONAL；盘点为只读事实）
| 需求 | 现状（只读盘点 2026-09-05） | 判定 |
|---|---|---|
| FXTM H1 主窗 + 239 日 / 143/48/48 切分 | 注册数据 v001 确认（4505 rows；2025-11-30→2026-09-04） | ✅ READY（A/B-N2/C 用） |
| DUKA H1 跨期（159 日） | 注册 v001 确认（3816 rows） | ✅ READY（一次性跨期） |
| E 标签 q95(252) 同 feed 扩展历史 — FXTM | staging_mt5 H1/M1 server 保留期 = 2025-12-01 起；无同 feed 更早源 | ❌ **D1：FXTM N1 = NOT TESTABLE（同 feed 历史不可得；不收缩 252）** |
| E 标签 q95(252) 同 feed 扩展历史 — DUKA | staging_duka 最早 2023-01-01（2023-09-01 前 ~168 交易日 <252） | ❌ **D2：DUKA N1 = DATA GAP（需下载延伸至 2022-07 前 ≥252 交易日；下载进行中 KD-U01）** |
| E2（DD-episode）标签 | 各窗自身日收益序列可算 | ✅ READY（敏感性用） |
| Phase 5 FVT 对拍数据 | 同数据集 + phase5_voltarget.json | ✅ READY |

## 5. Parameter Freeze Audit —— PASS
- FINAL_PREREGISTRATION §3–§8 逐项给出确定值/函数/规则；全文件 TBD/待定/FIXME/placeholder 命中 = 0 ✓。
- Hidden-DoF Register（§9）明确禁变清单；adaptive 变化仅限 §5 规则内 ✓。

## 6. Safety Audit —— PASS
- MT5 READ ONLY fail-closed：tools/mt5_readonly.py + configs/mt5_research_readonly.env 在位 ✓；
  本阶段未连接终端；R1' 无任何交易调用路径（无代码）。
- 无真实交易/无 push/无凭据/无破坏性操作；git 本地提交纪律 ✓。

---

## Gate 条件项（DISCOVERY 放行前必须满足）
- **G1（实现门控）**：实验代码通过 测试/lint + FVT 对拍验收 + ts-leak 冒烟 + registry drift 检查。
- **G2（N1 数据前置）**：D1 —— FXTM N1 保持 NOT TESTABLE（除非出现并注册同 feed 更早源）；
  D2 —— DUKA 扩展历史注册（≥252 交易日先于 2023-09-01）后 DUKA N1 方可执行。
- G1 满足后：A、C、B-N2 进入 DISCOVERY；N1 段在 D2 满足前不启动；N1 NOT TESTABLE 状态如实记录，
  不强行 REJECT（宪章 §29/§30 同则）。

## 跨期/跨 feed 命名声明（宪章 §29/§30）
FXTM 2026 vs DUKA 2023-24 同时改变 feed 与 period → 不称纯 cross-period/cross-feed；
同 feed 跨期与同期跨 feed 在当前注册数据下均无满足条件样本 → **NOT TESTABLE（如实登记）**，
DUKA 腿按 dual-role（异 feed 异期一次性复验）处理。
