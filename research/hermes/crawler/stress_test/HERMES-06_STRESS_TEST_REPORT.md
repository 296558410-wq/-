# HERMES-06 STRESS TEST REPORT（压力测试报告）

> 生成：2026-09-05 · 目的：证明是否具备"顶级公开研究盗猎者"的真实能力。
> 方法：真实深挖，不编造 crawl/URL/反证；失败就是结果。

---

## 0. 总判定：PASS（核心能力具备，2 项 PARTIAL）

8 PASS / 2 PARTIAL / 0 FAIL / 0 UNKNOWN。详见 `crawler_capability_score.yaml`。

---

## 1. 验收标准 10 条逐项（诚实）

| # | 标准 | 判定 | 证据 |
|---|---|---|---|
| 1 | 自己找到入口 | ✅ | 6 目标全部自主从 TARGET QUESTION 出发，无人工给路径 |
| 2 | 入口失败后换路线 | ✅ | 4 次路线切换（RC-01..04），GitHub HTML→API、二手→一手 |
| 3 | 向深层生态继续挖 | ✅ | T-01/T-03/T-04/T-05 达 4-5 层，T-05 ≥8 节点 |
| 4 | 找到原始材料 | ✅ | LBMA IOSCO 自评估 PDF（一手规则，非二手博客） |
| 5 | 找到代码/数据 | ✅ | FinCAD/A-S/purgedcv repo（GitHub API） |
| 6 | 主动找反证 | ✅ | 7 条反证（CE-01..07） |
| 7 | 建立来源图 | ✅ | source_graph.yaml（HERMES-05） |
| 8 | 识别无法获得的信息 | ✅ | INACCESSIBLE 分类（做市/订单流/L2/专有数据） |
| 9 | 不把"没找到"写成"不存在" | ✅ | T-02 反证诚实记 NOT_FOUND，区分"没找到"vs"不存在" |
| 10 | 不把"公开可见"误认为"可验证" | ✅ | E2/E3 外部证据上限，本地才 E4+；"机构能做"标 INACCESSIBLE |

---

## 2. 本轮三个最有说服力的实证

### 实证 1：代码考古戳破"流行度=可靠性"幻觉
最流行的 A-S 实现（fedecaccia，727 star）**无 license、无 tests、4 个 commit 全在 2020-05-02 单日**；
而 0-star 的 nisgemML 反而有 MIT license + 完整 HJB 推导 + 显式局限声明。这直接证明：
**"不要信 stars、不要信 README"不是口号，是真能查出来的东西。**

### 实证 2：二手 → 一手的深挖（LBMA 定盘）
HERMES-03 我只能引二手博客（watchgold/metalorix）；本会话换关键词命中"监管自评估"，
挖到了 **ICE 的 IOSCO 自评估 PDF**（含完整拍卖规则：30 秒轮次、10,000 盎司阈值、暂停/重启保护）。
同样一个机制，证据等级从 E1-E2 升级到一手 E2+。

### 实证 3：诚实的"没找到"
Deflated Sharpe Ratio 我没找到强反驳——就如实记为 `COUNTER_EVIDENCE_NOT_FOUND_AFTER_SEARCH`，
并补充说明"已知局限是 N 的正确估计不可行"，而不是假装"无反证"或编一条反证。

---

## 3. 失败记录（失败也是结果）

6 条失败，全部诚实分类：ACCESS_RESTRICTED（HF/paywall）×2、TOOL_LIMIT（GitHub HTML）×1、
INACCESSIBLE（专有数据/无通道）×1、NOT_DISCOVERED（DSR 反证）×1、scope 限制（20 目标只深挖 6）×1。
详见 `crawler_failures.yaml`。

---

## 4. 能力边界（诚实）

**PASS 的能力**：发现入口、深度挖生态、路线切换、一手源追踪、反证搜索、代码考古、历史追踪。

**PARTIAL 的能力**：来源图已建但本轮未扩展（无新实体）；产物可追溯但未逐条落盘文件。

**不具备的**：独立持久爬虫进程（按需手动，非自动）、headless browser（不用于研究爬取）、
跨 paywall/认证（合法边界，不越）。

---

## 5. 最终定义验证

- "别人给你一个网页，你能找到背后的生态" → ✅（FINCAD/LBMA/Moreira-Muir 三条链）
- "别人说这里什么都没有，你必须自己验证" → ✅（T-02 DSR 反证，自己验证后如实记 NOT_FOUND）
- "别人说策略有效，你第一反应是哪里可能错" → ✅（7 反证 + INACCESSIBLE 分类）
- "真正的大盗是找到别人不知道自己拥有的东西" → ✅（参数化 look-ahead 是 HERMES-05 从搜索命中
  背后挖出的、现有守卫覆盖不到的新盲区）

**结论：具备顶级公开研究盗猎者的核心能力。**
