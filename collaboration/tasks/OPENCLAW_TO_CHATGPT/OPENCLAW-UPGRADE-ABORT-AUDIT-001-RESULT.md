# OPENCLAW-UPGRADE-ABORT-AUDIT-001 — 失败安装残留审计

- **Task**: OPENCLAW-UPGRADE-ABORT-AUDIT-001（READ_ONLY）
- **被审计命令**: `npm install openclaw@2026.9.5 --save-exact`
- **执行位置**: `C:\Users\surface\dtlopenclaw\tools\openclaw`
- **失败时间**: 2026-09-21T13:46:00.662Z 起始（= 21:46 GMT+8），npm exit code **1**
- **审计时间**: 2026-09-21 21:50–21:53 GMT+8
- **Mode**: 严格只读 —— 未 install / update / ci / openclaw update / rollback / repair / restart；未改 PATH / npm 配置；未删 node_modules / lockfile；未改 package.json / V1·V2·V3 / MT5 / scheduler
- **最终状态**: `WAIT_FOR_CHATGPT_AUDIT`

---

## 一、判定（核心）

```text
INSTALL_FAILED    = TRUE     ← npm 在 openclaw@2026.9.5 的 preinstall 脚本阶段失败并中止
PARTIAL_INSTALL   = FALSE    ← 未留下半安装的包 / 元数据
NO_INSTALL_CHANGE = TRUE     ← 安装根目录的**文件内容**未发生任何持久变化
EFFECTIVE_TREE_CHANGE = NONE （仅两个目录的 mtime 被触碰，无文件内容变化）
```

**npm 失败根因（debug log 原文）**
```text
1328 info run openclaw@2026.9.5 preinstall node_modules/openclaw node scripts/preinstall-package-manager-warning.mjs
1330 info run openclaw@2026.9.5 preinstall { code: 1, signal: null }
1337 error command C:\Windows\system32\cmd.exe /d /s /c node scripts/preinstall-package-manager-warning.mjs
1338 error 'node' 不是内部或外部命令，也不是可运行的程序或批处理文件
1334 error code 1
1335 error path C:\Users\surface\dtlopenclaw\tools\openclaw\node_modules\openclaw
1349 verbose exit 1
```
→ 目标包 **2026.9.5 tarball 下载成功**（`http fetch GET 200 …/openclaw-2026.9.5.tgz`），但 npm 在跑 2026.9.5 自带的 **preinstall 钩子**时，用 `cmd.exe /c node …` 启动，而该 spawned 环境里 **`node` 不在 PATH** → 脚本 exit 1 → npm 中止并回滚。
回滚期间出现清理告警（非致命、未改变内容）：
```text
1331 warn cleanup Failed to remove some directories [ … node_modules\openai … EPERM: operation not permitted, rmdir … ]
```

## 二、逐项检查（对照 PREFLIGHT-002 的 BEFORE 基线）

| # | 检查项 | 结果 | 判定 |
|---|---|---|---|
| 1 | `package.json` 仍为 openclaw 2026.9.4 | 内容 `{dependencies.openclaw: "2026.9.4", name:"openclaw-runtime", private:true}` | **未变** |
| 2 | 是否出现 `package-lock.json` | **不存在**（LOCKFILE_PRESENT=FALSE） | **未新增** |
| 3 | `.npmrc` 是否变化 | `registry=https://mirrors.cloud.tencent.com/npm` | **未变** |
| 4 | CLI shim 是否变化 | 内容同前 | **未变** |
| 5 | `node_modules\openclaw` 版本 | **2026.9.4**；目录 mtime 2026-09-21 10:12:00 | **未变** |
| 6 | `node_modules` 是否半安装/不完整 | 依赖树完整；`dist\index.js` 存在；`npm ls openclaw --depth=0` → `openclaw@2026.9.4`；递归扫描"21:45 之后被修改的文件"= **0 个** | **完整** |
| 7 | npm debug log | 存在，见 §三 | — |
| 8 | 当前 CLI | `OpenClaw 2026.9.4 (3a9d69d)` | 正常 |
| 9 | Gateway 版本与健康 | **2026.9.4**，Running，HTTP 200 | 正常 |
| 10 | Gateway PID / 18789 listener | pid **43988**（supervisor 20680 → job-anchor 60252）；18789 LISTENING = 43988 | 正常 |

**哈希对照（与 BEFORE 逐字比对）**
```text
PACKAGE_JSON_SHA256_BEFORE 期望 B3609ABA08756609354B62B02153F218E77D1424E2AD95E7936EB1E777AB27F3
PACKAGE_JSON_SHA256_NOW    B3609ABA08756609354B62B02153F218E77D1424E2AD95E7936EB1E777AB27F3   → MATCH
NPMRC_SHA256_BEFORE        期望 91848FE1B6F651D328BBA3021CE352118AB15024776EADAB469C024626B08D84
NPMRC_SHA256_NOW           91848FE1B6F651D328BBA3021CE352118AB15024776EADAB469C024626B08D84          → MATCH
CLI_SHIM_SHA256_BEFORE     期望 A1559295754FE7E213C9BB7EACCF52095A31872AF7479887A513819F616B149E
CLI_SHIM_SHA256_NOW        A1559295754FE7E213C9BB7EACCF52095A31872AF7479887A513819F616B149E         → MATCH
```

**安装根目录清单**
```text
node_modules\   (dir,  mtime 2026-09-21 21:49:37)   ← 目录 mtime 被触碰（见下）
.npmrc          (47 B, 2026-09-21 10:08:49)         ← 内容未变
package.json    (104 B,2026-09-21 10:09:08)         ← 内容未变
（无 package-lock.json）
```

**唯一的"被触碰"痕迹（内容无变化）**
```text
node_modules\            mtime 2026-09-21 21:49:37   （原 10:12:04）
node_modules\.bin\       mtime 2026-09-21 21:49:36   （其中文件全部仍为 10:11:59，未变）
node_modules\.package-lock.json  mtime 2026-09-21 10:12:04（未变）
```
递归扫描 `node_modules` 下"最后写入时间 > 2026-09-21 21:45"的**文件**：**0 个** → npm 的尝试性替换/回滚**没有改变任何文件内容**，只更新了目录时间戳。

**未发现残留临时/暂存件**：安装根目录内无 `*2026.9.5*` / `*.tmp*` / 安装暂存目录（命中的 `archive-staging.*` / `workspace-result-staging-*` 都是 openclaw 包自带源码文件名，非本次残留）。
**npm 缓存副作用（非安装目录内）**：`openclaw-2026.9.5.tgz` 已落 npm 缓存（`AppData\Local\npm-cache\_cacache`）——按本任务只读要求**未清理**。

## 三、npm debug log

```text
路径 = C:\Users\surface\AppData\Local\npm-cache\_logs\2026-09-21T13_46_00_662Z-debug-0.log
大小 = 155,301 B
exit = 1
```
关键行：见 §一 引用的 1328/1330/1337/1338/1334/1335/1349 及 1326（tarball 下载 200）。

## 四、交易系统安全检查

```text
V1 = HEALTHY    (cron hermes-trader-m15-cycle 正常；workflow_latest @ 2026-09-21 21:50:32)
V2 = HEALTHY    (run V2-PAPER-20260920-200702-f507 RUNNING；ledger OK；replay MATCH)
V3 = HEALTHY    (calibration PASS 20/20；AUTO_STOP=TRUE；WAIT_FOR_AUDIT=TRUE)

MT5_INSTANCE_COUNT = 3
MT5_ISOLATION      = PASS
  V1  C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe      pid 1348   MAGIC 90002
  V2  C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe      pid 36460  MAGIC 90003
  V3  C:\AIQuant\mt5_instances\fxtm_demo_v3calib\terminal64.exe pid 49300  MAGIC 90004
UNMAPPED = 0   ORPHAN = 0   GHOST = 0

ORDER_SEND_CALLS = 0
LIVE             = FALSE
V3_LIVE_ALLOWED       = NO
V3_ORDER_SEND_ALLOWED = NO
V3_FORWARD_ALLOWED    = NO
EXPANSION             = LOCKED
```
未重启任何 MT5；未重启 Gateway。

## 五、结论

```text
INSTALL_FAILED    = TRUE
PARTIAL_INSTALL   = FALSE
NO_INSTALL_CHANGE = TRUE
```
- npm 因 **preinstall 钩子找不到 `node`（PATH 缺失）** 而中止；**未完成** 2026.9.5 安装。
- 安装目录的管理文件（`package.json` / `.npmrc` / CLI shim）与 `node_modules\openclaw`（仍 2026.9.4）**逐字节未变**；**未生成** root `package-lock.json`；**无**半安装残留。
- 现状：**CLI = Gateway = Package = 2026.9.4**，运行正常（Gateway 18789/HTTP 200）。
- 仅记录，**未做任何修复/回滚/清理**。

> 供后续参考（不在本任务执行）：失败点是 npm spawn 的 `cmd.exe` 环境里 `node` 不在 PATH —— 执行时确保 node 可解析（例如把 `C:\Users\surface\dtlopenclaw\tools\node-v24.21.0-win-x64` 加入该会话 PATH，或用该目录下的 `node.exe` 前置），即可越过该 preinstall 钩子。是否处理由用户/审计决定。

---

```text
STATUS = INSTALL_FAILED / PARTIAL_INSTALL=FALSE / NO_INSTALL_CHANGE=TRUE
WAIT_FOR_CHATGPT_AUDIT
```
