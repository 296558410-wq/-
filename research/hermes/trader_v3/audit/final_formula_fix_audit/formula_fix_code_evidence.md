# Formula Fix 代码证据说明（code evidence）

> 目的：让审计者在**无法 checkout 历史 commit** 的情况下，仍能独立、可追溯地验证 Formula Fix 的代码改动。

## 1. 严格区分的血缘结构

```text
FORMULA FIX BASE
6170050dcd6397f29193effc4f0baaed9036e2ab      repo = C:\AIQuant        type = BASE        status = historical

FORMULA FIX CODE
4f6bd54c4a4963fb2885921fee1d7adb510c940a      repo = C:\AIQuant        type = CODE        status = historical

LOCAL AUDIT MATERIAL
4ac5a240e752c40ebd1a968350c6f3e95d176cd7      repo = C:\AIQuant        type = LOCAL_AUDIT status = historical

GITHUB MATERIAL HISTORY
461b980bcf4b11506073ed3424fbe5f9e4849e18      repo = staging           type = STAGING     status = historical
4ac9a541468110867940b9cb35cc7ed01ae00260      repo = staging           type = MATERIAL    status = historical
9ad4f4b39897e28fb89b934a064be49290b85da3      repo = staging           type = MATERIAL    status = historical

CURRENT GITHUB AUDIT MATERIAL
19281f29d4eafea4aabfa08993327d39ff53a36e      repo = GitHub repository type = CURRENT_AUDIT_MATERIAL status = CURRENT
```

**两条血缘必须分清**

```text
6170050 → 4f6bd54      = Formula-Fix 的代码血缘（CODE）
4f6bd54 → 4ac5a24      = 本地 audit/report 材料血缘（LOCAL_AUDIT）
9ad4f4b → 19281f2      = GitHub 上的审计材料 metadata 修正（不涉及业务代码）
```

> ⚠️ **绝对不得把 `4ac5a24` 记为 Formula-Fix 的 CODE commit。** 它是 LOCAL_AUDIT。

## 2. Git object availability（关键）

```text
Git object availability = unavailable
```

在**当前 GitHub 仓库**（`https://github.com/296558410-wq/-.git`）的对象库中：

```text
6170050 -> NOT_PRESENT_IN_CURRENT_GITHUB_OBJECT_DATABASE
4f6bd54 -> NOT_PRESENT_IN_CURRENT_GITHUB_OBJECT_DATABASE
4ac5a24 -> NOT_PRESENT_IN_CURRENT_GITHUB_OBJECT_DATABASE
```

原因：这三个 commit 属于**本地 `C:\AIQuant` 仓库**，只把**产物/材料**推送到了 GitHub，
未推送该仓库的历史对象（也**未**伪造任何 commit）。
因此审计者**不能**在 GitHub 上 `git checkout 4f6bd54` —— 这是跨仓库事实，非隐瞒。

## 3. 实际 Formula-Fix 代码改动（BASE → CODE，6 个文件）

```text
MODIFIED  research/hermes/trader_v3/foundation/calibration_pilot.py
ADDED     research/hermes/trader_v3/foundation/pnl_accounting.py
ADDED     research/hermes/trader_v3/foundation/tests/test_v3_formula_fix.py
ADDED     research/hermes/trader_v3/audit/v3_formula_fix_recompute.py
ADDED     research/hermes/trader_v3/audit/v3_formula_fix_summary.json
ADDED     research/hermes/trader_v3/audit/v3_formula_fix_comparison.csv
```

## 4. Patch 的范围语义（重要，避免混淆）

```text
PATCH : git_diff_formula_fix.patch
范围  : BASE → LOCAL_AUDIT   （12 个文件；**更宽的审计证据集**）
并非  : CODE commit 的 HEAD~1 → HEAD （那只有 6 个文件）
```

之所以用 BASE→LOCAL_AUDIT：它一次性覆盖"代码改动 + 本地审计/报告材料"的全部证据。

**血缘证明**（见 `patch_verification.json`）：

```text
patch_generated_from_base_to_final = TRUE
changed_files_verified             = TRUE
方法 : 逐个 hunk 头 `index <old>..<new>` 与 Git 对象库 BASE:<path> / LOCAL_AUDIT:<path> blob 哈希 12/12 比对
新增文件语义 : base_exists=false, index_old=0000000, base_blob=null, base_blob_status=NOT_APPLICABLE_NEW_FILE
修改文件语义 : calibration_pilot.py  base_blob=26b4558a3bf3…, index_old=26b4558, match=true
反例排除 : 文件集(12) ≠ LOCAL_AUDIT 的 HEAD~1→HEAD 文件集(6)
```

### 4.1 已修正的旧 artifact 缺陷（诚实披露）

```text
(A) patch 编码损伤
    previous_patch_sha256 : 5ba0f8b3574caf72dd7faad3782077c362138cd2731db272216d66872047e490
    缺陷                  : 由 PowerShell 文本管道(Out-File)生成 -> 非 ASCII 字节损坏(mojibake)，行数 2970 vs 真实 2985
    处理                  : 已用 Python 原始字节重新生成（git stdout 直写）
    新 patch sha256       : 7962bff9309cbfdf9de3bf7d9e05c17c3ac76b8a6a94fa46d42d0273dfdc7241

(B) 新增文件 blob 语义错误
    旧值 : 新增文件的 base_blob 被填为 BASE commit SHA（6170050dcd63…）
    处理 : 改为 base_blob = null，base_blob_status = "NOT_APPLICABLE_NEW_FILE"
```

## 5. 审计者如何自行验证（无需 checkout）

1. `git_diff_formula_fix.patch` 的每个 `diff --git a/<path> b/<path>` 与 `changed_files.txt` 比对；
2. 取 patch 的 `index <old>..<new>`，与 `patch_verification.json.per_file_index_provenance[]` 的 `base_blob/final_blob` 比对；
3. 若拿到本地 `C:\AIQuant` 仓库，可复算：
   `git -C C:\AIQuant diff 6170050 4ac5a24 -- research/hermes/trader_v3/`
   → 规范化后应与本 patch 逐字节一致（sha256 `7962bff9…`）；
   代码范围可单独复算：`git -C C:\AIQuant diff 6170050 4f6bd54 -- research/hermes/trader_v3/`（6 文件）。

## 6. 声明

```text
未伪造任何 commit；
未把历史 commit 描述为当前 commit（历史节点均标注 historical，见 commit_lineage.json）；
未把 LOCAL_AUDIT(4ac5a24) 记为 CODE；
Git object availability = unavailable 已如实声明。
```
