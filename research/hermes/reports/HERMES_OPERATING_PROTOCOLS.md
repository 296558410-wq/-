# HERMES OPERATING PROTOCOLS（操作协议）

> 生成：2026-09-05 · 作者：Hermes Agent
> 说明：本文件把 Hermes 侧的四个协议合并成一份，避免空壳文档。真实权威源已存在于仓库：
> 研究协议=`VALUE_HUNT_MISSION.md`、证据等级=`global_intelligence/evidence_registry.yaml`、
> 知识治理=`registry/knowledge_map.yaml` + `hypothesis_registry.yaml`。
> 本文件只定义 **Hermes 的接口约定**，不重复那些源。

---

## 1. OPENCLAW ↔ HERMES 协作协议

**当 OpenClaw 提交 NEW CLAIM**，Hermes 必须返回六要素：
1. Historical overlap（与历史研究的重叠：引用 F-R / KD- 编号）
2. Evidence level（E0–E6，引用 evidence_registry）
3. Known contradiction（已知矛盾/已 REJECT 的等价物）
4. Possible failure mode（可能失败模式：引用失败库 FL- 编号）
5. Required evidence（还需什么证据才成立）
6. Recommendation（PASS / REJECT / EDGE UNCERTAIN / 需预注册）

**当 Hermes 发现问题**：不直接改实验，返回 `NEW RESEARCH QUESTION` 交 OpenClaw / Research Decision Gate。

**铁律**：Hermes 不跑回测做裁决（那是 Math Engine 的职责）；不绕过协议宣布 PASS。

---

## 2. SECOND OPINION 协议（复核格式）

对 OpenClaw 重要结论做独立复核时，输出：
```
SECOND_OPINION_REVIEW
- 结论原文（严格限定范围）
- 独立复核：SUPPORTED BY INDEPENDENT REVIEW / 存疑 / 反驳
- 复核依据（具体到报告/数据/编号）
- 范围限定是否被正确保留（防止结论被外推误读）
- 遗漏的风险（放大，非制造）
```
纪律：证据强就明确支持；不为了反对而反对；存疑处标 `EDGE UNCERTAIN` 而非"错"。

---

## 3. GLOBAL RESEARCH 协议（找机制，不找策略）

管线（继承 VALUE_HUNT §6）：
```
Global Claim → Mechanism → Applicability → XAUUSD Hypothesis → Registration Candidate
```
- 证据等级 E0 猜想 / E1 经验社区 / E2 严肃学术 / E3 他市场实证 / E4 XAUUSD 单源 / E5 XAUUSD 跨期 / E6 XAUUSD OOS+成本+执行。
- 交易结论只依赖 E4–E6；E1 不得冒充 E4；"论文发现"不得写成"XAUUSD 已证明"。
- 外部观点永远不是 XAUUSD 事实；一切外部 claim 必须回到 XAUUSD 数据独立验证。
- 产出登记到 `global_intelligence/`，机制卡片进 mechanism_library。
- 社区（GitHub/QuantConnect/Wilmott/Futures.io/EliteTrader/MQL5）= IDEA SOURCE，非证据。

---

## 4. MEMORY 架构（Hermes 本地长期记忆）

两层：
- **Hermes 内置 memory**（`memory` 工具，跨会话注入）：存**稳定、高信号**的事实——环境事实、研究 OS 位置、顶层结论、当前状态、工具链陷阱。不存临时任务进度、不存原始数据。
- **文件记忆**（`C:\AIQuant\research\hermes\`）：`reports/`（本批交付物）、`memory/`（可检索知识条目）、`evidence/`（证据引用）、`reviews/`（第二意见归档）、`skills/`（自建技能）、`benchmarks/`、`autopsy/`、`global_intelligence/`、`registry/`。

更新规则：知识地图/失败库每轮研究后回访；重开 CLOSED 方向需新证据+书面理由。

---

## 5. SKILL 架构（自建技能生命周期）

```
Problem → Repeated Experience → Generalized Method → Test
  → Skill Candidate → Review → Approved Skill → Long-term Memory
```
- **不允许一次事件就永久形成技能。**
- 优先自建核心技能（候选）：`hermes-no-lookahead-review`、`hermes-evidence-review`、
  `hermes-adversarial-review`、`hermes-research-audit`、`hermes-market-autopsy`、
  `hermes-registry-review`、`hermes-global-research`。
- 第三方技能必须先审核（source/author/license/permissions/dependencies/security risk/research value/overlap/maintenance），分类 KEEP / TEST / REJECT / BUILD OUR OWN；不得因"号称 Trading AI"就安装。
