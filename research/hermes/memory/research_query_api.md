# RESEARCH QUERY API（研究知识查询接口）

> 生成：2026-09-05 · HERMES-08 · 允许 OpenClaw（或未来任何会话）用结构化查询回答
> "这个机制我们研究过吗？" 答案来自**结构化 memory 文件**，非模型记忆。

---

## 查询方式

所有答案从 `research/hermes/memory/*.yaml` + `research/hermes/global_intelligence/*.yaml` 检索，
不依赖模型记忆。

## 支持的标准查询（每个都有对应文件）

| 查询 | 检索位置 | 返回 |
|---|---|---|
| "这个机制研究过吗？" | claim_registry + mechanisms.yaml | NEW / DUPLICATE / EXTENSION / REVISION |
| "为什么以前失败？" | failure_memory.yaml | 失败类型（统计/成本/数据/执行/方法学）+ FL 编号 |
| "有没有反证？" | contradiction_registry | CONTRA-xx + 双方证据 |
| "最强证据在哪？" | claim_registry + evidence_history | 证据等级 E0-E6 + 升级链 |
| "缺什么数据？" | dead_end_index + reopen_conditions | DATA_UNLOCK 触发条件 |
| "什么时候值得重开？" | reopen_conditions | 数据/基础设施/方法论触发 |
| "这个方向该不该再研究？" | dead_end_index | DE-xx + reopen_condition |
| "现在最值得研究什么？" | knowledge_graph + research_queue | 两个"有肉"簇（R1 + RQ-05） |
| "这个观点后来发生了什么？" | research_lineage | LIN-xx 谱系链 |

## 去重判定（RESEARCH_DUPLICATION_ENGINE）

新研究请求到达时，按序检查：
1. 是否已研究过 → `claim_registry` 命中 → DUPLICATE/EXTENSION
2. 是否换名重包装 → `hypothesis_registry` redundancy map → DUPLICATE
3. 是否换资产重跑已否机制 → `dead_end_index` → DUPLICATE（除非 reopen_condition）
4. 是否存在已知反证 → `contradiction_registry` → CONTRADICTION
5. 否则 → NEW

## 查询示例

**Q**: "跨资产 lead-lag 值得研究吗？"
**A**: CL-10 = CONTRADICTED（rahulsp 2026，DXY→黄金无预测性）；DE 未列但见 claim_registry。
仅 COMEX 套利链保留，需期货数据（DATA_GAP）。

**Q**: "波动率择时有效吗？"
**A**: CONTRA-01 = CONFLICTED；单因子 OOS+净成本失败，多因子+净额+成本优化+平滑才存活；
映射本地 R1'（无条件日级降险 REJECTED）→ 走向"形态条件化"。

**Q**: "还有没有方向 alpha 机会？"
**A**: CL-03 = REJECTED（已测空间）；≤1m 需 DUKA tick（DATA GAP，非 REJECTED）。

---

## 维护纪律

- 答案永远来自 yaml 文件，不来自模型记忆。
- 新发现 → 更新对应 yaml + 记录 LAST_REVIEWED + VALID_AT_TIME。
- 不因时间自动删除旧结论；旧结论标 SUPERSEDED_BY / CONTRADICTED_BY。
