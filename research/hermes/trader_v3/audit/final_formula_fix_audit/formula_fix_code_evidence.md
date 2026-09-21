# Formula Fix 代码证据说明（code evidence）

> 目的：让审计者在**无法 checkout 历史 commit** 的情况下，仍能独立、可追溯地验证 Formula Fix 的代码改动。

## 1. Formula Fix 代码证据来源

```text
来源仓库      : C:\AIQuant（本地研究工作仓库；**其 V3 变更未发布为 GitHub commit**）
BASE          : 6170050dcd6397f29193effc4f0baaed9036e2ab
FINAL         : 4ac5a240e752c40ebd1a968350c6f3e95d176cd7
分支          : fix/v2-full-system-repair-20260917
```

## 2. Git object availability（关键）

```text
Git object availability = unavailable
```

在**当前 GitHub 仓库**（staging，`https://github.com/296558410-wq/-.git`）的对象库中：

```text
6170050 -> NOT_PRESENT_IN_CURRENT_GITHUB_OBJECT_DATABASE
4f6bd54 -> NOT_PRESENT_IN_CURRENT_GITHUB_OBJECT_DATABASE
4ac5a24 -> NOT_PRESENT_IN_CURRENT_GITHUB_OBJECT_DATABASE
```

原因：这三个 commit 属于**本地 `C:\AIQuant` 仓库**，只把**产物/材料**推送到了 GitHub staging，
未推送该仓库的历史对象（也**未**伪造任何 commit）。

> 因此：审计者**不能**在 GitHub 上 `git checkout 4f6bd54`。这不是被隐瞒，而是跨仓库事实。

## 3. 可用的替代证据（这就是 patch 的意义）

```text
PATCH : git_diff_formula_fix.patch
含义  : BASE → FINAL 的实际 Git diff（不是 HEAD~1 → HEAD）
范围  : research/hermes/trader_v3/
```

**该 patch 已完成血缘证明**，见 `patch_verification.json`：

```text
patch_generated_from_base_to_final = TRUE
changed_files_verified             = TRUE
证明方法 : 逐个 hunk 头 `index <old>..<new>` 与 Git 对象库中的
           BASE:<path> / FINAL:<path> blob 哈希比对
结果     : 12/12 文件全部匹配（新增文件要求 old=0000000 且 BASE 无该路径）
反例排除 : 该 patch 的文件集 = 12 个 ≠ 4ac5a24 的 HEAD~1→HEAD 文件集（6 个）
           ⇒ 可排除"patch 实为 HEAD~1→HEAD"的可能
```

### 3.1 已修正的旧 artifact 缺陷（诚实披露）

```text
previous_patch_sha256 : 5ba0f8b3574caf72dd7faad3782077c362138cd2731db272216d66872047e490
缺陷                  : 早期 patch 由 PowerShell 文本管道(Out-File)生成 → 非 ASCII 字节被破坏
                        (mojibake)，行数 2970 而真实为 2985 → 不是可信证据
处理                  : 已用 Python 以**原始字节**重新生成（git stdout 直写，不经文本管道）
新 patch sha256       : 7962bff9309cbfdf9de3bf7d9e05c17c3ac76b8a6a94fa46d42d0273dfdc7241
```

## 4. 实际文件路径（BASE / FINAL 中的路径）

```text
MODIFIED  research/hermes/trader_v3/foundation/calibration_pilot.py
ADDED     research/hermes/trader_v3/foundation/pnl_accounting.py
ADDED     research/hermes/trader_v3/foundation/tests/test_v3_formula_fix.py
ADDED     research/hermes/trader_v3/audit/v3_formula_fix_recompute.py
ADDED     research/hermes/trader_v3/audit/v3_formula_fix_summary.json
ADDED     research/hermes/trader_v3/audit/v3_formula_fix_comparison.csv
ADDED     research/hermes/trader_v3/audit/v3_calibration_formula_fix_20trades.csv
ADDED     research/hermes/trader_v3/reports/V3-HFT-CALIBRATION-FORMULA-FIX-001-RESULT.md
ADDED     research/hermes/trader_v3/reports/V3-HFT-CALIBRATION-FORMULA-FIX-001-RESULT.json
ADDED     research/hermes/trader_v3/reports/v3_calibration_formula_fix_20trades.csv
ADDED     research/hermes/trader_v3/reports/v3_formula_fix_comparison.csv
ADDED     research/hermes/trader_v3/reports/v3_formula_fix_summary.json
```
（与 `changed_files.txt` / `git_diff_stat.txt` 一致；共 12 个文件）

## 5. 审计者如何自行验证（无需 checkout）

1. `git_diff_formula_fix.patch` 中每个 `diff --git a/<path> b/<path>` 与 `changed_files.txt` 比对；
2. 对任一文件取 patch 的 `index <old>..<new>`，与 `patch_verification.json.per_file_index_provenance[]` 的 `base_blob/final_blob` 比对；
3. 若拿到了本地 `C:\AIQuant` 仓库，可复算：
   `git -C C:\AIQuant diff 6170050 4ac5a24 -- research/hermes/trader_v3/`
   → 规范化后应与本 patch 逐字节一致（sha256 `7962bff9…`）。

## 6. 声明

```text
未伪造任何 commit；
未把历史 commit 描述为当前 commit（历史节点均标注 historical，见 commit_lineage.json）；
Git object availability = unavailable 已如实声明。
```
