# OPENCLAW-UPGRADE-PREFLIGHT-002 — 方案 A 执行前最终基线（READ_ONLY / PRE-UPGRADE FREEZE）

- **Task**: OPENCLAW-UPGRADE-PREFLIGHT-002
- **Plan A target**: `npm.cmd install openclaw@2026.9.5 --save-exact`
- **Timestamp**: 2026-09-21 21:43–21:48 GMT+8 (= 2026-09-21T13:43–13:48Z)
- **Mode**: READ_ONLY / PRE-UPGRADE FREEZE — **未执行安装**；未 install / update / ci / openclaw update（含 --dry-run）/ reinstall / rollback / repair / 任何重启；未改 `.npmrc` / `package.json` / lockfile / node_modules / V1·V2·V3 / scheduler；未 `order_send`；未 calibration / expansion / Demo Forward / LIVE
- **SYSTEM_STATE = UNCHANGED**
- **STATUS**: `READY`

---

## 一、核心字段

```text
CURRENT_VERSION            = 2026.9.4   (CLI / Gateway / Package 三者一致)
TARGET_VERSION             = 2026.9.5
TARGET_AVAILABLE           = TRUE

PACKAGE_JSON_SHA256_BEFORE = B3609ABA08756609354B62B02153F218E77D1424E2AD95E7936EB1E777AB27F3
NPMRC_SHA256_BEFORE        = 91848FE1B6F651D328BBA3021CE352118AB15024776EADAB469C024626B08D84
CLI_SHIM_SHA256_BEFORE     = A1559295754FE7E213C9BB7EACCF52095A31872AF7479887A513819F616B149E

NODE_VERSION               = v24.21.0
NPM_VERSION                = 11.19.0
NODE_PATH                  = C:\Users\surface\dtlopenclaw\tools\node-v24.21.0-win-x64\node.exe
NPM_PATH                   = C:\Users\surface\dtlopenclaw\tools\node-v24.21.0-win-x64\npm.cmd

TARGET_TARBALL             = https://mirrors.cloud.tencent.com/npm/openclaw/-/openclaw-2026.9.5.tgz
TARGET_INTEGRITY           = sha512-TCO/ImVLh5HkF4tdfo7iriIa7kT6iYkIr/jR5ZOkePGFGhUx5Oe7DE716Y1DzzG2teRAVDdCjgJDu1A24Yta7w==

CURRENT_DEPENDENCY_TREE    = openclaw-runtime@ C:\Users\surface\dtlopenclaw\tools\openclaw
                             └── openclaw@2026.9.4

GATEWAY_HEALTH             = OK
GATEWAY_PID                = 43988  (supervisor 20680 → job-anchor 60252)
GATEWAY_PORT               = 18789 (LISTENING / HTTP 200)

V1_HEALTH                  = OK
V2_HEALTH                  = OK
V3_HEALTH                  = OK

MT5_INSTANCE_COUNT         = 3
MT5_ISOLATION              = PASS

ORDER_SEND_CALLS           = 0
LIVE                       = FALSE

BACKUP_HASH_VALID          = TRUE
```

## 二、安装根目录冻结

```text
INSTALL_ROOT = C:\Users\surface\dtlopenclaw\tools\openclaw
```
目录清单（仅 3 项）：
```text
node_modules\   (dir,  2026-09-21 10:12:04)
.npmrc          (47 B,  2026-09-21 10:08:49)
package.json    (104 B, 2026-09-21 10:09:08)
LOCKFILE_PRESENT = FALSE   (无 package-lock.json)
```

## 三、package.json 冻结（完整）

```json
{
  "dependencies": {
    "openclaw": "2026.9.4"
  },
  "name": "openclaw-runtime",
  "private": true
}
```
```text
name                  = openclaw-runtime      (符合预期)
private               = true                  (符合预期)
dependencies.openclaw = 2026.9.4              (符合预期)
scripts               = (无)
engines               = (无)
PACKAGE_JSON_SHA256_BEFORE = B3609ABA08756609354B62B02153F218E77D1424E2AD95E7936EB1E777AB27F3
```
未修改。

## 四、npm 配置冻结

```text
INSTALL_ROOT\.npmrc 内容 = registry=https://mirrors.cloud.tencent.com/npm
NPM_REGISTRY_BEFORE = https://mirrors.cloud.tencent.com/npm   (符合预期)
NPMRC_SHA256_BEFORE = 91848FE1B6F651D328BBA3021CE352118AB15024776EADAB469C024626B08D84
```
无其他配置项。未修改 registry。

## 五、Node / npm 冻结

```text
node --version → v24.21.0
npm  --version → 11.19.0
NODE_PATH = C:\Users\surface\dtlopenclaw\tools\node-v24.21.0-win-x64\node.exe
NPM_PATH  = C:\Users\surface\dtlopenclaw\tools\node-v24.21.0-win-x64\npm.cmd   (实际使用的 npm.cmd)
(npm.ps1 存在但受 PowerShell 执行策略限制不可用；本任务统一使用 npm.cmd)
```

## 六、目标包只读验证（当前 .npmrc / 当前实际 registry）

```text
$ npm.cmd view openclaw@2026.9.5 version
→ 2026.9.5
$ npm.cmd view openclaw@2026.9.5 dist.tarball
→ https://mirrors.cloud.tencent.com/npm/openclaw/-/openclaw-2026.9.5.tgz
$ npm.cmd view openclaw@2026.9.5 dist.integrity
→ sha512-TCO/ImVLh5HkF4tdfo7iriIa7kT6iYkIr/jR5ZOkePGFGhUx5Oe7DE716Y1DzzG2teRAVDdCjgJDu1A24Yta7w==

TARGET_VERSION   = 2026.9.5
TARGET_AVAILABLE = TRUE
```
未下载、未安装、未切换 registry。

## 七、当前依赖树冻结

```text
$ npm.cmd ls openclaw --depth=0
openclaw-runtime@ C:\Users\surface\dtlopenclaw\tools\openclaw
`-- openclaw@2026.9.4

$ npm.cmd ls --depth=0
openclaw-runtime@ C:\Users\surface\dtlopenclaw\tools\openclaw
`-- openclaw@2026.9.4
```
确认 `openclaw = 2026.9.4`；该 runtime 是**单一依赖**的私有包（只有 openclaw 一个直接依赖）。

## 八、当前 OpenClaw 实际运行版本

```text
CLI     = 2026.9.4  (openclaw --version → "OpenClaw 2026.9.4 (3a9d69d)")
Gateway = 2026.9.4
Package = 2026.9.4
```
Gateway 实际加载路径仍为：
```text
C:\Users\surface\dtlopenclaw\tools\openclaw\node_modules\openclaw\dist\index.js
```
未重启 Gateway。

## 九、CLI shim 冻结

```text
路径 = C:\Users\surface\.openclaw\tmp\agent-cli\openclaw.cmd
内容：
@echo off
setlocal DisableDelayedExpansion
C:\Users\surface\dtlopenclaw\tools\node-v24.21.0-win-x64\node.exe --max-old-space-size=8192 C:\Users\surface\dtlopenclaw\tools\openclaw\node_modules\openclaw\dist\index.js %*

CLI_SHIM_SHA256_BEFORE = A1559295754FE7E213C9BB7EACCF52095A31872AF7479887A513819F616B149E
形态确认：→ node ...\openclaw\dist\index.js %*   (dist shim，非 package-manager global shim)
```
未修改 shim。

## 十、Gateway 服务冻结

```text
Scheduled Task : "OpenClaw Gateway" (TaskPath \, State=Running, LastRunTime 2026-09-21 10:13:38, LastTaskResult 267009)
gateway.cmd    : C:\Users\surface\.openclaw\gateway.cmd  sha256 C2C354B420E8BB92D7837D272475419DD04442733928944D5FE3BB915C217EA0
gateway.vbs    : C:\Users\surface\.openclaw\gateway.vbs  sha256 7D5331009808BC8E4E9247BEB793234A9C7A1CA7ABB55E7783CFC34DA3372642
install path   : C:\Users\surface\dtlopenclaw\tools\openclaw\node_modules\openclaw
node executable: C:\Users\surface\dtlopenclaw\tools\node-v24.21.0-win-x64\node.exe
GATEWAY_PID (supervisor)      = 20680   (gateway --port 18789 --task-supervisor)
JOB_ANCHOR_PID                = 60252   (process/supervisor/service-child-windows-job-anchor.js)
18789 LISTENER PID            = 43988   (gateway --port 18789)
command line                  = node --max-old-space-size=8192 <install>\dist\index.js gateway --port 18789

GATEWAY_HEALTH = OK
PORT_18789     = LISTENING (pid 43988)
HTTP           = 200
```
未重启。

## 十一、OpenClaw 配置基线（备份有效性）

```text
BACKUP_DIR = C:\Users\surface\.openclaw\workspace\backups\OPENCLAW-UPGRADE-BACKUP-001_20260921\
BACKUP_AVAILABLE  = TRUE   (15 个文件：config / service / runtime / scheduler + 快照报告)
BACKUP_HASH_VALID = TRUE   (备份副本逐字节 == 当前 live 文件)
```
| 文件 | 备份 vs live | hash |
|---|---|---|
| openclaw.json | VALID | 752CB0EAA6831E19… |
| install_config.json | VALID | EC5C6F1FBCA37D67… |
| gateway.cmd | VALID | C2C354B420E8BB92… |
| gateway.vbs | VALID | 7D5331009808BC8E… |
未修改备份。

## 十二、交易系统安全基线

```text
V1 = HEALTHY   (cron hermes-trader-m15-cycle；workflow_latest @ 2026-09-21 21:35:30)
V2 = HEALTHY   (run V2-PAPER-20260920-200702-f507 RUNNING；ledger OK；replay MATCH；blocked=null)
V3 = HEALTHY   (calibration PASS 20/20；AUTO_STOP=TRUE；WAIT_FOR_AUDIT=TRUE)

MT5_INSTANCE_COUNT = 3
MT5_ISOLATION      = PASS
UNMAPPED           = 0
ORPHAN             = 0
GHOST              = 0
  V1  C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe      pid 1348   MAGIC 90002
  V2  C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe      pid 36460  MAGIC 90003
  V3  C:\AIQuant\mt5_instances\fxtm_demo_v3calib\terminal64.exe pid 49300  MAGIC 90004
```
未重启 MT5。

## 十三、交易安全门

```text
ORDER_SEND_CALLS = 0
LIVE             = FALSE
V3_LIVE_ALLOWED       = NO
V3_ORDER_SEND_ALLOWED = NO
V3_FORWARD_ALLOWED    = NO
EXPANSION             = LOCKED
V3 calibration        = 20/20, AUTO_STOP=TRUE, WAIT_FOR_AUDIT=TRUE
```

## 十四、V1/V2/V3 文件完整性

```text
V1_CODE_INTEGRITY = PASS
V2_CODE_INTEGRITY = PASS
V3_CODE_INTEGRITY = PASS
```
- 升级窗口（2026-09-21 10:12 之后）**未发现任何交易系统源码文件被修改**。
- 观察到的近期 `.py` 全部位于 `trader_v1\run_state\tmp\`（V1 引擎每轮自写的临时辅助脚本，如 `append_summary_1332Z.py` / `baserate_*.py` / `probe_*.py`）→ 属**运行时产物**，非源码改动。
- V2 的近期写入为 `research\runs\...\inputs|decisions|` 与 `data_cache\evidence_raw\`（运行时证据），V3 无新写入。
- C:\AIQuant HEAD = `4f6bd54`（未变）。
- **未清理**工作区既有未提交改动；**未提交**任何交易系统文件。

## 十五、npm install 预期变化边界

### 预期允许变化（方案 A 执行时）
```text
package.json        (pin 2026.9.4 → 2026.9.5，--save-exact)
node_modules        (openclaw 包内容替换)
lockfile            (package-lock.json 由 npm 生成)
package metadata    (包内 package.json / dist 产物)
```

### 不允许变化
```text
OpenClaw config · Gateway service definition · CLI shim
V1 · V2 · V3 · Hermes · MT5 · scheduler · trading state · ledger
```

## 十六、升级执行前最终判定

```text
TARGET_AVAILABLE  = TRUE
BACKUP_HASH_VALID = TRUE
GATEWAY_HEALTH    = OK
V1_HEALTH         = OK (HEALTHY)
V2_HEALTH         = OK (HEALTHY)
V3_HEALTH         = OK (HEALTHY)
MT5_ISOLATION     = PASS
ORDER_SEND_CALLS  = 0
LIVE              = FALSE
关键 BEFORE hash  = 已记录 (package.json / .npmrc / CLI shim / gateway.cmd / gateway.vbs / task.xml / config)
```

```
STATUS = READY
```

> 提示（不影响 READY，供执行者注意）：① 方案 A 会在 INSTALL_ROOT 生成此前缺失的 `package-lock.json`（属允许变化）；② 执行后需重启 `OpenClaw Gateway` 服务（会短暂中断本会话）才会加载新版本；③ 回滚目标 = 2026.9.4（把 pin 改回 + `npm.cmd install` + 重启服务），备份见 §十一。

---

```text
STATUS = READY
WAIT_FOR_CHATGPT_AUDIT
```
