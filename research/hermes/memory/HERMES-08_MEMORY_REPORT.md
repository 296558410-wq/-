# HERMES-08 MEMORY REPORT（研究记忆引擎报告）

> 生成：2026-09-05 · 把 HERMES-01..07 的研究状态固化为可查询的长期记忆引擎。

---

## 0. 架构（两层记忆）

| 层 | 位置 | 角色 |
|---|---|---|
| **真相源（文件）** | `research/hermes/memory/*.yaml` + `global_intelligence/*.yaml` | 版本化、可查询、OpenClaw 可读的完整研究状态 |
| **索引（内置）** | Hermes memory 工具 | 紧凑指针（指向文件真相源 + 顶层结论），非重复全部细节 |

> 关键设计：内置 memory 只有 2200 字符预算，**不能**装下七轮全部研究状态；
> 所以它是"索引"，文件是"真相源"。查询走文件，不靠模型记忆。

## 1. 已建立的结构

| 文件 | 内容 | 规模 |
|---|---|---|
| claim_registry.yaml | 15 条 claim，统一状态词汇 | CL-01..15 |
| failure_memory.yaml | 25 条失败，按 5 类（统计/成本/数据/执行/方法学） | FL-01..25 |
| contradiction_registry.yaml | 8 条矛盾 + 5 谱系 + 证据升级史 | CONTRA-01..08, LIN-01..05 |
| dead_end_index.yaml | 9 个死胡同 + 重开条件 | DE-01..09 |
| knowledge_graph.yaml | 统一图谱（6 簇） | 全量索引 |
| research_query_api.md | 标准查询接口 | 9 类查询 |
| （既有） | mechanisms/accessibility/queue/lineage 等 | HERMES-03..07 |

## 2. 四个关键区分（§14 纪律，已落实）

| 区分 | 落地 |
|---|---|
| CURRENTLY_BEST-SUPPORTED ≠ UNIVERSALLY_TRUE | CL-01/02 CONFIRMED 仍限定 FXTM+DUKA 双源 |
| ACCESSIBLE ≠ PROVEN | CL-06 支持但"XAUUSD 未验证" |
| INACCESSIBLE ≠ NO VALUE | CL-08/09 保留理解价值 D |
| DATA_GAP ≠ REJECTED | CL-11/12 + DE 的重开条件明确 |

## 3. 时间版本（§6）

- CL-05（Moreira-Muir）保留 `STATUS_AT_TIME`：2017 SUPPORTED → 2020 UNCERTAIN → 2021 CONTRADICTED → 2026 条件极窄。
- 这是"研究知识非静态"的实证：结论随时间演变，旧状态不删。

## 4. 证据升级史（§7）

- LBMA 定盘：E1 二手博客 → E2 一手 IOSCO PDF（HERMES-06）
- 参数化 look-ahead：E2 论文 → E4 论文+代码（HERMES-05）
- activity→vol：E4 单源 → E5 双源（本地）

## 5. 反重复研究能力（§3 + §11）

新研究请求 → 先查 claim_registry（已研究？）→ hypothesis_registry（换名？）→ dead_end_index（换资产？）→
contradiction_registry（已有反证？）→ 否则 NEW。9 个死胡同各有 REOPEN_CONDITION，满足才重开。

## 6. 最终答案（这张记忆引擎里最核心的一条）

七轮研究收敛：**XAUUSD 里唯一可及、且成本后可能仍有经济价值的层 = 风险/成本择时（R1），
外加方法论严谨（RQ-05）保证不制造假 alpha。** 其余（方向/执行/跨资产/期权）是"已否/不可及/缺数据"。

---

## 状态：READY（Global Quant Research Memory Engine 已建立）

- 15 claim + 25 failure + 8 contradiction + 9 dead end + 5 lineage 全部固化，可查询。
- 不靠模型记忆（模型记忆会遗忘/漂移），靠结构化文件 + 版本控制。
- 未删旧结论（SUPERSEDED/CONTRADICTED 标记而非删除）。
