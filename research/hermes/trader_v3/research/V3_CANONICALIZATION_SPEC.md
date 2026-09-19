# V3 CANONICALIZATION SPEC (v1) — C-31 产物确定性规范化

目的：把**仅含运行时 metadata / 序列化差异**的产物规范为逐字节可复现的 canonical artifact。
**前提（已证）**：`p2_summary` 的 d5adab91… vs 3cd637e7… 差异**只有** `provenance/mtime`（F/G），
**0 个研究语义字段差异**（见 `tools/v3_c31_diff.py` 输出 BUCKETS {F/G:1}, SEMANTIC_FIELD_DIFFS 0）。
若存在 A/B/C/D 或语义字段差异，**禁止**用本规范化掩盖，C-31 保持 NOT_FROZEN。

## 规则（事前固定，不得事后调整）
1. **JSON key ordering**：`sort_keys=True`，`separators=(",", ":")`，`ensure_ascii=False`。
2. **numeric formatting**：保留原值；仅将 `-0.0` 归一为 `0.0`；浮点用默认 repr（同值即同字节）。
3. **timestamp policy**：排除所有墙钟/运行时刻字段（`ROOM` 无关）。排除键集：
   `mtime, generated_utc, generated_at, ts, timestamp, runtime_ms, duration_ms, elapsed_ms, elapsed,
    host, hostname, machine, cwd, wall_clock, run_ts`。
   —— **保留** `provenance.sha256`（工具身份，确定性）。
4. **path normalization**：绝对路径前缀 `C:/Users/surface/HermesWorkspaces/v3` → `<ROOM>`（含反斜杠变体）。
5. **volatile metadata exclusion**：见第 3 条键集（只删这些，其余一律保留）。
6. **encoding**：UTF-8（无 BOM）。
7. **newline policy**：统一 `\n`，文件末尾恰好一个换行。
8. **CSV**：CRLF/CR → LF；路径规范化；末尾 `\n`；**不改数值、不改行序**。

## 适用对象
- `p2_summary_*.json`（JSON 规则）
- `p2_trades_*.csv`、`p2_latency_ladder_*.csv`（CSV 规则）

## 复现要求（§20.10）
同一冻结工具 + 同参数 + 同输入跑 3 次（before/mid/after），经本规范化后**三份产物逐字节一致**；
否则 C-31 保持 NOT_FROZEN。

## 边界
- 本规范化**不改变**任何研究语义（trade count / fill tick / return / gross / cost / net / latency verdict /
  population / period / effective N / pass-fail）。
- 工具自身哈希（`provenance.sha256`）保留，故 canonical artifact 仍绑定冻结工具身份。
