# CRAWLER ARCHITECTURE（爬虫架构 / 深挖方法论）

> 生成：2026-09-05 · HERMES-05 · 本文件是 Hermes 作为"研究盗猎者"的**方法论**，不是代码库声明。
> 诚实声明：Hermes 无独立持久爬虫进程；深挖通过工具层（web_search / web_extract / curl 公开 API）执行，
> 下列架构是**施加在每次深挖上的纪律**，而非已部署的软件。

---

## 0. 能力边界（诚实）

| 能力 | 实现方式 | 状态 |
|---|---|---|
| 搜索引擎发现 | web_search（后端可切） | ✅ |
| 页面提取 | web_extract（HTML→markdown，含 PDF URL） | ✅（偶发 keyless 超时） |
| 公开 API | curl（GitHub API / arxiv API 等） | ✅ **最可靠** |
| 静态 JSON/文档 | curl | ✅ |
| HEADLESS BROWSER | 无 | ❌ 不用于研究爬取（除非必要） |
| 持久 URL frontier / 递归爬虫 | 无 | ❌（按需手动，非自动） |

**关键实证（本轮）**：GitHub 页面 HTML 提取超时，但 `api.github.com` 公开 JSON 成功 →
印证优先级 **静态/公开 API > HTML 抓取 > 浏览器**。

## 1. 优先级原则（STATIC > API > JSON > DOC > BROWSER）

1. 静态公开文件（arxiv PDF/HTML、论文 PDF、原始 JSON）
2. 公开 API（GitHub API、arxiv API、Crossref/Semantic Scholar API）
3. 公开 JSON/结构化数据
4. 公开文档
5. HEADLESS BROWSER（最后手段，仅动态内容必需时）

## 2. Crawl 纪律（每条深挖链强制）

| 项 | 规则 |
|---|---|
| crawl budget | 每条链 ≤ 5-8 请求；命中高价值后收敛，不无限扩展 |
| rate limiting | 请求间留间隔；curl 用 `-m` 超时；不并发轰炸同一 host |
| cache / dedup | 同 URL 不重复抓；同机制多来源合并（HERMES-03 已实践） |
| domain allowlist | 优先学术/官方域（arxiv/github/nber/bis/fed/ssrn/jstor/院校） |
| depth limit | 论文→作者→代码→数据→反证，5 层封顶 |
| content-size limit | 提取用 char_limit 截断，全文落盘，不整页进上下文 |
| request logging | 每链记录 SOURCE/URL/accessed date/depth |
| access restriction | 遇 403/paywall/CAPTCHA → 记 ACCESS_RESTRICTED，停，不绕过 |

## 3. 深挖链模板（DEEP CRAWL PATH）

```
表面入口（搜索命中）
  ↓ 识别实体（作者/机构/论文/repo/数据集）
  ↓ 反向链（该 claim 引用了什么）
  ↓ 前向链（谁引用了它）
  ↓ 作者链（作者其它工作 / GitHub / 主页）
  ↓ 复现链（replication / code / data）
  ↓ 反证链（criticism / contradiction / failed replication / 后续修订）
  ↓ 证据图（实体 + 关系）
```

## 4. 代码考古检查清单（不轻信 README）

- repository structure 是否匹配论文声称（有对应目录/模块）
- README claim vs 实际 source（`cad/` 目录 vs "Context-Aware Decoding" 声称）
- tests/ 是否存在（可复现性信号）
- data/ 与 results/ 是否说明（数据依赖、复现产物）
- notebooks 是否有手工调参痕迹
- license / 活跃度（commit/pushed date）
- issue tracker（已知失败/未复现步骤）

## 5. 学术考古检查清单

一篇重要论文之后自动做：BACKWARD（引用）/ FORWARD（被引）/ AUTHOR / REPLICATION /
CONTRADICTION / CODE / DATA 七向搜索。目标是"围绕 claim 的整个生态"，不是"这篇论文说了什么"。

## 6. 反证优先级（STATUS = INCOMPLETE 规则）

任何高价值 claim 至少主动找 1 条 replication + 1 条 criticism/contradiction；
若只找到支持材料 → 标 `INCOMPLETE`，不写"事实"。

---

## 本轮真实深挖演示（1 条完整链，实证能力）

**链：参数化 look-ahead（FINCAD）**
```
arxiv:2605.24564 摘要（入口，HERMES-04 已记）
  ↓ 前向/版本：arxiv HTML v2（7 天前更新）
  ↓ 代码：github.com/waylonli/FinCAD（MIT, EMNLP 2026 Main）
  ↓ 代码考古（curl GitHub API）：cad/ + adapters.py + tests/ + benchmark/ + results/
       → 结构确证论文"Context-Aware Decoding + inference-time"声称
  ↓ 作者链：waylonli（GitHub 作者本人）
  ↓ 生态：czyssrs/LLM_X_papers + TongjiFinLab/awesome-time-series-forecasting（阅读清单）
  ↓ 反证：无直接反证（新失败模式的识别，非可交易 claim）
```
**depth reached: 5 层（摘要→版本→代码→考古→生态）**；**request count: ~5**；**access restriction: 0**。

> 这一条链证明了：搜索命中只是入口；真正的价值（代码、作者、生态、复现）在入口之后。
