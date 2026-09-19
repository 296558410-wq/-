# HERMES GLOBAL RESEARCH ARCHITECTURE（全球研究架构）

> 生成：2026-09-05 · HERMES-03 · 本文件是整个 Global Research Scout 体系的入口索引。
> 机器可读真相在 `research/hermes/global_intelligence/*.yaml`；叙事分析在 `reports/`。

---

## 体系结构

```
research/hermes/
├── global_intelligence/          # 机器可读注册表（真相源）
│   ├── sources.yaml              # 10 个来源（含质量评级 SRC-01..10）
│   ├── mechanisms.yaml           # 11 个机制（MECH-01..11）
│   ├── contradictions.yaml       # 4 条矛盾（CONTRA-01..04）
│   ├── failures.yaml             # 4 条失败情报（FL-19..22，与既有 FL-* 去重）
│   ├── research_queue.yaml       # 5 个研究队列项（RQ-01..05，冻结评分）
│   └── research_lineage.yaml     # 2 条研究谱系（LIN-01..02）
└── reports/                      # 叙事报告
    ├── HERMES_GLOBAL_SCAN_REPORT.md        # 10 个发现完整分析链
    ├── HERMES_MECHANISM_LIBRARY_REPORT.md  # 机制库叙事
    ├── HERMES_CONTRADICTION_REPORT.md      # 矛盾库叙事
    ├── HERMES_XAUUSD_RESEARCH_QUEUE.md     # 队列叙事
    ├── HERMES_ADVERSARIAL_INTELLIGENCE.md  # 5 个对抗自审
    ├── HERMES_OPENCLAW_HANDOFF.md          # 向 OpenClaw 提交的机会
    ├── HERMES_VALUE_DISCOVERY_REPORT.md    # 价值发现漏斗
    ├── HERMES_SOURCE_MAP.md                # 来源地图
    └── HERMES-03_SELF_AUDIT.md             # 自审
```

## 与既有 global_intelligence 层的关系（去重）

既有层（OpenClaw 早前建）：`research/global_intelligence/`（evidence_registry EXT-*、research_ideas RID-*、source_quality、global_sources、mechanism_library）。

HERMES-03 增量（`research/hermes/global_intelligence/`）：
- **净新增**：contradictions.yaml（矛盾库，既有层完全空白）、failures.yaml（失败情报）、research_lineage.yaml（谱系）。
- **扩展**：mechanisms.yaml（MECH-* 相对 RID-* 的深化，标注 REDUNDANT/EXTENSION/NEW）、sources.yaml、research_queue.yaml。
- **纪律**：MECH-* 与 RID-* 逐条去重（如 MECH-07 标 REDUNDANT 因 RID-001/P7 已覆盖）。

## 证据等级（继承 source_quality.yaml，E0-E6）

外部资料最多 E2/E3，一律"XAUUSD 未验证"。交易结论只依赖 E4-E6。

## 价值发现漏斗（VALUE DISCOVERY RATE）

30+ 原始结果 → 去重 10 条高质量 → 7 条 XAUUSD 相关 → 5 个研究候选 → 3 个 HOT 机会（全部风险/执行/方法论层）。

## 核心洞察（本轮最重要的一个结论）

全球证据（vol-timing 争议链、成本 regime 依赖、LLM 搜索强度泄漏）与本地 XAUUSD 研究结论
（方向 alpha 已死、vol 信息非方向、R1' 无条件降险被否）**互相印证**：价值在风险/执行/方法论层。
这本身就是最高价值的研究情报——它独立验证了研究方向没有跑偏。
