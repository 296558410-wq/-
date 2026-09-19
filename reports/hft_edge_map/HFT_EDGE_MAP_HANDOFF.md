# HFT EDGE MAP HANDOFF — 交接与裁决请求（v2, 2026-09-06）

## v1 → v2 变更说明（为什么重跑）
- v1 提交于 2026-09-05 23:17（f0663a7）；**HERMES-10 反证于 2026-09-06 08:06 入库**（1076e46，
  contradiction_registry CONTRA-09），直接命中 v1 中 "risk/cost timing = 最可接近盈利方向" 的表述。
- v2 触发点 = 该 CONTRADICTION_REVIEW：vol/成本择时盈利 WEAKENED（JFE 成本归零 + Elsevier 2000 后消失），
  R1 定位改为风险管理输入。同时按 HARD RULES 补齐：每机制 EVIDENCE_CONVERGENCE（新文件）、
  八类瓶颈显式识别、TOP 5 上限纪律、五桶最终建议。
- v2 未触碰任何 frozen registry（hypothesis_registry / phase9_detector_registry / REPRESENTATION_REGISTRY /
  R1' 冻结文件）；只更新 reports/hft_edge_map/ + knowledge_map.yaml 的 KD-HFT-MAP 条目（登记点，非冻结物）。

## 本任务完成状态（STOP 条件）
- [x] 机制宇宙（25 机制 × 10 字段价值拆解 + duplicate/dead-end/contradiction/data-gap 标记；去重后 22 条独立线）→ MECHANISM_UNIVERSE.yaml
- [x] 证据融合（每机制 PRIMARY/REPLICATION/COUNTER/LOCAL/HERMES/GRADE + INDEPENDENT_EVIDENCE_COUNT）→ **EVIDENCE_CONVERGENCE.yaml（新增）**
- [x] 可及性矩阵（4 级分类 + 原因码 + v2 信息层限定）→ ACCESSIBILITY_MATRIX.yaml
- [x] 可观测性矩阵（4 级 + proxy 纪律 + HERMES-10 proxy 失败警示）→ OBSERVABILITY_MATRIX.yaml
- [x] 本地研究映射（浪费/未研究/缺数据/值得投入 + CONFLICT 记录）→ LOCAL_RESEARCH_MAPPING.yaml
- [x] Hermes 情报映射（KNOWN/FAILURE/CONTRADICTION/DATA GAP/INACCESSIBLE/REOPEN；CONF-1/2 记录 + CONF-3 修正）→ 各 YAML + LOCAL_RESEARCH_MAPPING.hermes_crossref
- [x] Top Research Questions（9 字段 + EVIDENCE_CONVERGENCE + 反证；5/5 合格, 上限非配额）→ **TOP_RESEARCH_QUESTIONS.yaml（替代 v1 TOP5_RESEARCH_QUESTIONS.yaml）**
- [x] 研究组合 TIER 0-4（四维独立 + UNKNOWN，无黑箱分；vol-timing 无条件版入 TIER 4）→ HFT_RESEARCH_PORTFOLIO.yaml
- [x] 系统蓝图（8 层 + 成本瓶颈显式化）→ HFT_SYSTEM_BLUEPRINT.md
- [x] 系统瓶颈（八类显式识别 + BN-1..9 + 机会 vs 瓶颈排序）→ SYSTEM_BOTTLENECKS.yaml
- [x] 总图叙述（12 问 + 五桶最终建议）→ XAUUSD_HFT_EDGE_MAP.md
- [x] knowledge_map KD-HFT-MAP 条目更新（v2）

## 核心结论（一句话版）
- 方向层（无条件 M1+ 15-240m）在已测空间无成本后价值——关闭（v1 不变）；
- 微观结构层价值最高但结构性不可观测/不可及——INACCESSIBLE，不投入（v1 不变）；
- **v2 修正**：vol/成本择时 = CONFIRMED INFORMATION（E5）但 **PROFITABLE TIMING = WEAKENED**（HERMES-10）；
  可及的是中间层信息/风险/成本输入（成本状态 / 事件时间 / 切换先行 / 流动性窗 / fix 窗），不是盈利 edge；
- **价值与可观测性负相关**（第一结构事实）+ **信息可预测 ≠ 盈利可接近**（v2 第二结构事实）。

## 证据与诚实声明（写入即冻结）
- 无任何机制达到 E6（XAUUSD OOS+成本+执行后）；"无当前可及机制有足够证据进入立即研究" 对**盈利 edge 层成立**。
- Top 反证：0 降级 / 1 条件（RQ-H4）/ 4 完整——只是"值得一问"，不是"有肉"。
- 本图所有 KEEP/可及/稳定表述 ≠ edge 存在；唯一 E5 确认 = 非方向 vol/activity/spread 信息（风险层输入）。
- 实验声称边界：FXTM 2026 单窗 / DUKA 2023-24 静态窗；不外推；≤1m 候选 PASS 需 DUKA tick。
- 本任务无新增 hypothesis 实验、无修改 frozen registry、无策略、无交易、无参数优化、无收益声称。

## 请求人工裁决（STOP，不自动进入任何实验/Top 1）
1. **Top 5 采纳范围**：全部/部分/修改？（RQ-H1/H3 建议优先；H2 需日历接入授权；H4 需 W1 审计；H5 零成本描述）
2. **数据解锁优先级**：DUKA tick（KD-U01）、D2（252 日）、事件日历 —— 是否启动某项获取流程？
3. **RQ-07 执行模拟器立项**：同意作为纯工程项排在 TIER 1 实验后？
4. **TIER 1 四项若采纳**：各自须走 kickoff → manifest → research_gate → rlap_audit → PASS 后才可执行（无 skip/force 路径）。
5. **知识地图更新**：KD-HFT-MAP v2 条目更新是否批准（本提交已写入 research/registry/knowledge_map.yaml）。

## 文件清单
reports/hft_edge_map/：XAUUSD_HFT_EDGE_MAP.md · MECHANISM_UNIVERSE.yaml · **EVIDENCE_CONVERGENCE.yaml** ·
ACCESSIBILITY_MATRIX.yaml · OBSERVABILITY_MATRIX.yaml · LOCAL_RESEARCH_MAPPING.yaml ·
HFT_RESEARCH_PORTFOLIO.yaml · **TOP_RESEARCH_QUESTIONS.yaml**（v1 TOP5_RESEARCH_QUESTIONS.yaml 已由本文件取代删除）·
HFT_SYSTEM_BLUEPRINT.md · SYSTEM_BOTTLENECKS.yaml · HFT_EDGE_MAP_HANDOFF.md
knowledge_map: KD-HFT-MAP（v2）
