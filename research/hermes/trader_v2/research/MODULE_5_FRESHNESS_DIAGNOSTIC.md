# MODULE 5 — FRESHNESS 只读诊断报告

> 诊断对象：`V2-PAPER-20260911-132414-2684` 首轮 Hermes 决策读到 `agent1 freshness=unknown / agent2 freshness=unknown`。
> **本报告为纯只读诊断；未修改任何运行代码/配置/数据，未重启/停止/重跑 run，未制造 TRADE。**

## 结论速览
`unknown` 来自 **`hermes/context.py` 的 ROOT 路径多算了一级**：它去 `C:\AIQuant\research\hermes\state\` 读 agent 快照，
而 Agent1/Agent2 实际把快照写到 `C:\AIQuant\research\hermes\trader_v2\state\`。
读不到文件 → `a1={}/a2={}` → `generated_utc/snapshot_ts = None` → `_freshness(None) = "unknown"`。
**第一处 `unknown` = `context.py::_freshness()`（因上游路径取错，而非字段名错）。** 分类 = **B（metadata propagation / 路径解析缺陷）**。

## 1. Agent1
```
raw freshness (agent1_latest.json @ trader_v2/state):  generated_utc = 2026-09-11T13:24:41Z  → 存在
context freshness (ctx_db6251a5f780.json):             generated_utc = null, freshness = "unknown"
Hermes-visible freshness:                              "unknown" → gate 直接 WAIT
读取路径(错误): C:\AIQuant\research\hermes\state\agent1_latest.json  (不存在)
真实路径:      C:\AIQuant\research\hermes\trader_v2\state\agent1_latest.json (存在)
```

## 2. Agent2
```
raw freshness (agent2_latest.json @ trader_v2/state):  snapshot_ts = 2026-09-11T13:25:03Z  → 存在
context freshness:                                     generated_utc = null, freshness = "unknown"
Hermes-visible freshness:                              "unknown" → WAIT
读取路径(错误): C:\AIQuant\research\hermes\state\agent2_latest.json  (不存在)
真实路径:      C:\AIQuant\research\hermes\trader_v2\state\agent2_latest.json (存在)
```

## 3. 字段链（第一个 unknown 的位置）
```
Agent1 source(data_ts 21:22, retrieval_ts)
  → raw  state/agent1_latest.json.generated_utc          ✅ present (trader_v2/state)
  → normalized/context  ctx["agent1"]["generated_utc"]   ❌ null   ← 读错目录
  → ctx["agent1"]["freshness"] = "unknown"               ← ★ 第一处 unknown
  → Hermes gate  f1 = ctx["agent1"]["freshness"]         = "unknown"
  → verdict WAIT  ("数据不新鲜(a1=unknown, a2=unknown)")
Agent2 同链，字段名为 snapshot_ts。
```

## 4. Hermes 实际读取的字段
`hermes/hermes.py::gate()`：`f1 = ctx["agent1"]["freshness"]`、`f2 = ctx["agent2"]["freshness"]`；任一 ∈ {expired, unknown} → WAIT。
**字段名正确**；问题不在读哪个字段，而在 context 造这个字段时上游就是 null。

## 5. 根因分类
**情况 B** —— Agent1/Agent2 raw **有** freshness（时间戳存在），context 侧丢失。
精确成因：`context.py` 顶部 `ROOT = Path(__file__).resolve().parents[2]`
（`.../trader_v2/hermes/context.py` → parents[2] = `.../research/hermes`，多算一级，应为 `parents[1]` = `.../trader_v2`）。
连带证据：
- `CONFIG = .../research/hermes/config/v2_config.json`（不存在）→ `config_hash` = `sha256("")` = `e3b0c442…`（≠ manifest 的 `eec4330c…`）。
- `decision_contexts` 被写到 `.../research/hermes/state/decision_contexts/`（而非 `trader_v2/state/`）。
- `hermes.py` 同样 `ROOT = HERE.parents[1]`（HERE=.../trader_v2/hermes）→ 也指向 `.../research/hermes`，其 `opportunity_ledger / hermes_memory / hermes_state / hermes_decision_latest / decision_contexts` 均落在 `research/hermes/state/`。

## 6. 是否首轮初始化问题
**否。是系统性（永久）问题。** 证据：Agent1/Agent2 只写 `trader_v2/state/`，context 只读 `research/hermes/state/`（无 agent1/agent2 文件），两条路径永久不交汇 → 每个窗口都会 `unknown`。（当前仅在 13:15 窗口有决策；按确定性路径可断定后续窗口同样 unknown。）

## 7. 时间一致性（只读）
context 里 `decision_timestamp - source_timestamp` / `observed_timestamp` **当前无法计算**（source ts 为 null）。
但**原始**时间戳其实存在且健康：agent1_generated=13:24:41Z、agent2_snapshot=13:25:03Z、decision=13:25:03Z（同一轮内，均新鲜）。修复路径后即可算出真实 age。

## 8. 当前 Run 是否受影响
- **安全性/数据完整性：未受影响。** 仍 PAPER；无 broker/live 单；ledger verify PASS；Paper==Replay（replay_match=true）；无重复执行。
- **决策有效性：受影响。** 因 gate 第一道即 `unknown`，该 run 在修复前**结构性无法产生 TRADE**（只会 WAIT）。这属于"实验条件缺陷"，不是数据损坏。

## 9. 是否需要修复 / 建议方案（**仅建议，不执行**）
需要修复（属真实缺陷），但**本次不修**。建议（下次经批准，新 commit + 新 run_id）：
1. `hermes/context.py`：`ROOT = Path(__file__).resolve().parents[2]` → `parents[1]`（= trader_v2）。
2. `hermes/hermes.py`：`ROOT = HERE.parents[1]` → `HERE.parent`（= trader_v2）；使 Hermes 自身 state 落回 `trader_v2/state`。
3. 复核 `execution/hermes_paper_loop.py` 默认决策文件路径随之一致。
4. 修复后按 §八 流程：新 commit → 新 run_id → 新 Run。
5. 存量 `research/hermes/state/`（含 20:09 与 21:25 的 `ctx_*.json` 等）为**历史/错误目录产物**，是否清理请示用户，**本报告不删**。

---
### 附：诊断命令（只读，均已执行）
- `context` 模块 `ROOT/STATE/CONFIG/CTX_DIR` 解析与存在性检查
- `research/runs/<run_id>/timeline.jsonl`、`run_manifest.json`
- `state/decision_contexts`（trader_v2）为空；`research/hermes/state/decision_contexts/ctx_db6251a5f780.json`（错误目录）中 freshness=unknown
- Agent1/Agent2 真实快照时间戳存在性
