# OPENCLAW-UPGRADE-POSTVERIFY-001 — OpenClaw 2026.9.5 升级后验收

- **Task**: OPENCLAW-UPGRADE-POSTVERIFY-001（READ_ONLY / POST-UPGRADE-VERIFY）
- **Timestamp**: 2026-09-21 21:34–21:40 GMT+8 (= 2026-09-21T13:34–13:40Z)
- **Host**: DESKTOP-LQ0B8O3 · Windows 10.0.26200 (x64) · node v24.21.0
- **Mode**: 全程只读；未 update / 未 rollback / 未 repair / 未重启任何服务 / 未改配置 / 未动 V1·V2·V3 / 未 order_send / 未启动任何 calibration 或 expansion
- **Verdict**: **FAIL** — 版本未达到目标（仍为 2026.9.4）。**未发现任何升级破坏**（系统本身健康）。

```
OPENCLAW_CLI_VERSION       = 2026.9.4 (3a9d69d)
OPENCLAW_GATEWAY_VERSION   = 2026.9.4
OPENCLAW_PACKAGE_VERSION   = 2026.9.4
OPENCLAW_INSTALL_PATH      = C:\Users\surface\dtlopenclaw\tools\openclaw\node_modules\openclaw
OPENCLAW_CHANNEL           = stable (default)
OPENCLAW_INSTALL_KIND      = package (npm)
VERSION_MATCH              = NO   (目标 2026.9.5；实际 2026.9.4 → §二 触发 STATUS=FAIL)
```

## FAIL 原因（唯一）

任务书 §二：`CLI/Gateway/Package` 必须为 **2026.9.5**，否则 `STATUS = FAIL`，且不得自行升级。
实测三者均为 **2026.9.4**，且**升级其实从未执行**：
- install 目录 `LastWriteTime = 2026-09-21 10:12:00`、`dist\index.js = 2026-09-21 10:11:44`（无新写入）
- Gateway 进程启动时间 = `2026-09-21 10:13:38 / 10:13:57`（早于本次验收，晚于安装时间；**即进程加载的就是 2026.9.4 的安装**——已按要求不只凭 package.json 判断）
- `openclaw update status`：`channel=stable`、`latestVersion=null`、`available=false`（registry 检查超时）

> 说明：这是"**还没升级**"，不是"升级失败/被破坏"。系统各部件均为健康状态（见下）。

## 三、Gateway 验收

```
GATEWAY_HEALTH  = OK
GATEWAY_PROCESS = pid 43988 (gateway --port 18789)  |  supervisor: pid 20680 (--task-supervisor) → pid 60252 (job-anchor)
GATEWAY_PORT    = 18789 LISTENING (pid 43988) ; loopback ESTABLISHED ; http://127.0.0.1:18789/ → 200
service/task    = Windows Task "OpenClaw Gateway" (\ , State=Running, LastResult 267009=0x41301 running)
command line    = node --max-old-space-size=8192 ...\openclaw\dist\index.js gateway --port 18789
running code    = 上述 dist（package.json=2026.9.4）  ← 与 CLI/Package 一致
auth            = 已启用（token），status 报 reachable ~865ms
```

## 四、Dashboard 验收

```
DASHBOARD_HEALTH = OK
  127.0.0.1:18789            → 200
  V1 dashboard 127.0.0.1:8787 → 200
  V2 dashboard 127.0.0.1:8788 → 200
  V3 dashboard 127.0.0.1:8790 → 200
```

## 五、V1 验收

```
V1_HEALTH               = OK
V1_CODE_INTEGRITY       = PASS（无源码变更；仅 run_state/runtime 产物正常滚动）
V1_SCHEDULER            = OpenClaw cron `hermes-trader-m15-cycle`(cd47547e…) 正常（最近一次 running/ok）
V1_ENTRYPOINT           = research/hermes/trader_v1（trader_core/engine 未改）
V1_WORKFLOW_LATEST      = 2026-09-21 21:35:30（新鲜）
V1_LEDGER_HEALTH        = OK（plan_ledger.jsonl / state_package_latest.json 正常更新）
V1_MT5_CONNECTION_SAFETY_PIN = 存在（C:\AIQuant\research\hermes\trader_v3\state\V1_MT5_CONNECTION_SAFETY_PIN.json, 2026-09-20 20:59:43）→ 继续保留
V1_MT5_INSTANCE         = C:\Program Files\ForexTime (FXTM) MT5 （pid 1348）
V1_MAGIC                = 90002（broker_mt5_demo.py: MAGIC = 90002）
V1_STRATEGY_UNTOUCHED   = TRUE     V1_TRADING_LOGIC_UNTOUCHED = TRUE
```
注：V1 的 ledger 为 plan_ledger/state_package 形式，非 V2/V3 式 sha256 hash-chain；任务书要求的"sha256 chain"在 V1 无对应物 → 记入 DATA_GAPS（非异常）。

## 六、V2 验收

```
V2_HEALTH            = OK
V2_SCHEDULER         = Windows Task `hermes-v2-cycle`（\OpenClaw\）State=Ready
V2_CODE_INTEGRITY    = PASS（无源码变更；仅 research/runs 与 data_cache 证据文件正常累积）
V2_RUN               = V2-PAPER-20260920-200702-f507  status=RUNNING  last_completed 2026-09-21T13:22:38Z
V2_LEDGER            = OK（ledger_status=OK）
V2_REPLAY            = MATCH（replay_status=MATCH）
V2_EXECUTION_SAFETY  = ExecutionGuard 生效（最近: DEC-ctx_8270de4d5d9a / DEC-ctx_919ec6ea6019 = REJECTED:POSITION_BUSY，单仓约束正常）
V2_CONFIG_INTEGRITY  = OK — execution.backend=fxtm_demo, execution_mode=BROKER_DEMO, live_trading=false,
                       broker_demo_enabled=true, isolation.allow_real_trading=false（符合当前阶段，未因验收改变）
V2_MT5_INSTANCE      = C:\AIQuant\mt5_instances\fxtm_demo_01 （pid 36460）
V2_MAGIC             = 90003（execution/fxtm_demo_adapter.py: MAGIC = 90003）
```

## 七、V3 验收

```
V3_HEALTH              = OK
V3_CODE_INTEGRITY      = PASS（无源码变更；audit/ 与 state/ 为既有审计产物）
V3_CALIBRATION_STATUS  = PASS, n_samples=20, PILOT_DONE={status:PASS,n:20}
V3_LIVE_ALLOWED        = NO
V3_ORDER_SEND_ALLOWED  = NO
V3_FORWARD_ALLOWED     = NO
CALIBRATION_AUTO_STOP  = TRUE
WAIT_FOR_AUDIT         = TRUE
EXPANSION              = LOCKED
V3_MT5_INSTANCE        = C:\AIQuant\mt5_instances\fxtm_demo_v3calib （pid 49300）
V3_MAGIC               = 90004（foundation/calibration_pilot.py: MAGIC = 90004）
```
未启动 V3-HFT-CALIBRATION-FORMULA-FIX-001（本任务只验证；该 fix 已在前序任务完成并静置 WAIT_FOR_AUDIT）。

## 八、三实例 MT5 隔离

```
MT5_INSTANCE_COUNT = 3
MT5_ISOLATION      = PASS
  V1  C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe   pid 1348    MAGIC 90002
  V2  C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe   pid 36460   MAGIC 90003
  V3  C:\AIQuant\mt5_instances\fxtm_demo_v3calib\terminal64.exe pid 49300 MAGIC 90004
UNMAPPED        = 0
ORPHAN          = 0
GHOST_INSTANCE  = 0   （无 fxtm_demo_v3 幽灵）
```
未启停任何 MT5。

## 九、Scheduler 完整性

```
V1 = OpenClaw cron `hermes-trader-m15-cycle`        (cd47547e-ae38-4b36-a585-8b041ee826bb)  ok
V2 = Windows Task `\OpenClaw\hermes-v2-cycle`        Ready
V3 = Windows Task `\OpenClaw\v3-calibration-pilot`   Ready（一次性，已完成，保持 WAIT_FOR_AUDIT）
V1 scheduler ≠ V2 scheduler ≠ V3 calibration  → 三者互不相同
其他：hermes-tick-collect Ready / hermes-v2-observer Ready / collab-task-bus ok / v2-broker-demo-forward ok
```
未修改任何 scheduler。

## 十、OpenClaw 配置完整性（对比升级前快照）

```
OPENCLAW_CONFIG_INTEGRITY = PASS
```
| 文件 | BEFORE | AFTER | 结果 |
|---|---|---|---|
| openclaw.json | 752CB0EAA683 | 752CB0EAA683 | **MATCH** |
| install_config.json | EC5C6F1FBCA3 | EC5C6F1FBCA3 | **MATCH** |
| gateway.cmd | C2C354B420E8 | C2C354B420E8 | **MATCH** |
| gateway.vbs | 7D5331009808 | 7D5331009808 | **MATCH** |
| node_modules/openclaw/package.json | A234B616A049 | A234B616A049 | **MATCH** |
| OpenClaw Gateway task XML | (snapshot) | (live export) | **同** (task_xml_same=True) |

无字段级差异 → 无需 BEFORE/AFTER 变更列表。

## 十一、V1/V2/V3 文件完整性

```
V1_CODE_INTEGRITY = PASS
V2_CODE_INTEGRITY = PASS
V3_CODE_INTEGRITY = PASS
```
- 升级窗口（2026-09-21 10:12 之后）**未发现任何源码文件（*.py 等）被修改**；仅以下**运行时产物**正常滚动（与 OpenClaw 升级无关，属引擎自身运行）：
  - `trader_v1\memory\reviews\RV-TP-20260921T1147Z-*.json`
  - `trader_v2\research\runs\V2-PAPER-20260920-200702-f507\inputs|decisions\DEC-*`
  - `trader_v2\data_cache\evidence_raw\ev_news_2026*`
- C:\AIQuant HEAD = `4f6bd54`（V3 formula fix，前序任务产物，未变）
- ⚠️ 工作区存在**大量非本任务产生的既有未提交改动**（V1/V2 run_state 等 1162 项）——按 §十六 **未覆盖、未清理、未提交**。

## 十二、安全验收

```
V1_ORDER_SEND = FALSE
V2_ORDER_SEND = FALSE
V3_ORDER_SEND = FALSE
LIVE          = FALSE
V3_LIVE_ALLOWED = NO   V3_ORDER_SEND_ALLOWED = NO   V3_FORWARD_ALLOWED = NO
EXPANSION     = LOCKED
ORDER_SEND_CALLS = 0   （本次验收全程只读）
```

## 十三、升级后运行稳定性

仅观察，未重启任何服务：Gateway 127.0.0.1:18789 持续 reachable（连续两次探测 200）；Dashboard 200；V1 cron 正常滚动（workflow_latest 21:35:30）；V2 run RUNNING 且 ledger OK；V3 静置 PASS/AUTO_STOP；三 MT5 全部在且映射正确、无幽灵。观测期内**无异常**。

## 十四、最终判定

```
STATUS = FAIL
```
依据 §二/§十四：`CLI = Gateway = Package = 2026.9.4 ≠ 2026.9.5` → `VERSION_MATCH = NO` → **FAIL**（除此之外，§十四 PASS 的其余条件全部满足：Gateway/Dashboard/V1/V2/V3 = OK、MT5_COUNT=3、MT5_ISOLATION=PASS、integrity=PASS、ORDER_SEND=0、LIVE=FALSE、V3 三门=NO、EXPANSION=LOCKED）。

**未发现升级破坏、服务异常、隔离破坏、文件异常或安全门异常。**

## DATA_GAPS / ANOMALIES

```
DATA_GAPS:
  - openclaw update status 的 registry 检查超时（fetch-timeout 3500ms @ registry.npmjs.org）
    → 无法本地确认 2026.9.5 是否存在于 registry（"目标 2026.9.5" 来自任务书）
  - install 的 npm lockfile 缺失（deps.status=unknown, reason="lockfile missing"）
  - V1 无 V2/V3 式 sha256 hash-chain ledger（V1 使用 plan_ledger/state_package 形式）→ §五该项不适用
ANOMALIES: []（无）
```

---

```
OPENCLAW_CLI_VERSION       = 2026.9.4
OPENCLAW_GATEWAY_VERSION   = 2026.9.4
OPENCLAW_PACKAGE_VERSION   = 2026.9.4
VERSION_MATCH              = NO
GATEWAY_HEALTH             = OK
GATEWAY_PROCESS            = pid 43988 (supervisor 20680 → anchor 60252)
GATEWAY_PORT               = 18789 LISTENING / loopback OK / HTTP 200
DASHBOARD_HEALTH           = OK
V1_HEALTH                  = OK
V1_CODE_INTEGRITY          = PASS
V1_SCHEDULER               = OK
V2_HEALTH                  = OK
V2_CODE_INTEGRITY          = PASS
V2_SCHEDULER               = OK
V2_LEDGER                  = OK
V2_REPLAY                  = MATCH
V2_EXECUTION_SAFETY        = OK (ExecutionGuard / POSITION_BUSY)
V3_HEALTH                  = OK
V3_CODE_INTEGRITY          = PASS
V3_CALIBRATION_STATUS      = PASS (n=20, AUTO_STOP=TRUE)
V3_LIVE_ALLOWED            = NO
V3_ORDER_SEND_ALLOWED      = NO
V3_FORWARD_ALLOWED         = NO
MT5_INSTANCE_COUNT         = 3
MT5_ISOLATION              = PASS
UNMAPPED                   = 0
ORPHAN                     = 0
GHOST_INSTANCE             = 0
OPENCLAW_CONFIG_INTEGRITY  = PASS
ORDER_SEND_CALLS           = 0
LIVE                       = FALSE
DATA_GAPS                  = 3 (registry timeout / lockfile missing / V1 无 hash-chain ledger)
ANOMALIES                  = []
STATUS                     = FAIL   (原因: 版本仍 2026.9.4，未升级到 2026.9.5)

WAIT_FOR_CHATGPT_AUDIT
```

---

## R1 — Updater Blocker Evidence

> **APPEND-ONLY**。原始审计内容与结论**未改动**：`STATUS = FAIL`（`CURRENT_VERSION = 2026.9.4` / `TARGET_VERSION = 2026.9.5` / `UPGRADE_EXECUTED = FALSE`）。未将 FAIL 改为 PASS。

### R1.1 Blocker
```text
UPDATER_BLOCKER = TRUE
BLOCKER_MESSAGE = Update refused: package manager owner is unknown; no changes were made.
UPDATER_ACTION  = NO_CHANGE
```
**这不是**升级失败后的回滚，**也不是**升级过程中损坏：
```text
UPGRADE_ATTEMPTED         = TRUE
UPGRADE_EXECUTED          = FALSE
FILES_MODIFIED_BY_UPDATER = FALSE
ROLLBACK_EXECUTED         = FALSE
REPAIR_EXECUTED           = FALSE
SYSTEM_STATE_CHANGED      = FALSE
```

### R1.2 安装形态（只读记录）
```text
INSTALL_ROOT = C:\Users\surface\dtlopenclaw\tools\openclaw
package.json 关键字段:
  name                  = openclaw-runtime
  private               = true
  dependencies.openclaw = 2026.9.4
CLI shim = C:\Users\surface\.openclaw\tmp\agent-cli\openclaw.cmd
  实测内容 = node.exe --max-old-space-size=8192 <INSTALL_ROOT>\node_modules\openclaw\dist\index.js %*
  → 直接调用本地 dist\index.js 的 shim；不是标准 package-manager global shim
```

### R1.3 updater 拒绝原因
```text
PACKAGE_MANAGER_OWNER = UNKNOWN
updater 建议（原文，仅记录，未执行）：
  Run this OpenClaw install through its active npm/pnpm/Bun global shim,
  or reinstall it with that package manager, then retry.
OWNER_UNKNOWN = TRUE
（不得解释为已完成重装）
```

### R1.4 目标版本存在性（只读，实际所用镜像）
```text
$ npm.cmd view openclaw@2026.9.5 version --registry=https://mirrors.cloud.tencent.com/npm
→ 2026.9.5

$ npm.cmd view openclaw dist-tags --json --registry=https://mirrors.cloud.tencent.com/npm
→ {"latest":"2026.9.5","beta":"2026.9.5","alpha":"2026.5.19-alpha.1","extended-stable":"2026.7.35"}

TARGET_VERSION_FOUND = TRUE
TARGET_VERSION       = 2026.9.5
DIST_TAG_LATEST      = 2026.9.5
```
未执行 install；未修改 registry；未修改 npm 配置。

### R1.5 对原 DATA_GAP 的澄清（不改写历史）
原始 `openclaw update status` 的 npm registry timeout 记录**保留**（当时真实发生）。
```text
CLARIFICATION:
  该 timeout 针对 registry.npmjs.org。
  当前安装环境实际使用/可访问的镜像是 mirrors.cloud.tencent.com/npm（见 INSTALL_ROOT\.npmrc）。
  该镜像已只读验证 2026.9.5 存在。
  → npmjs.org timeout ≠ target version unavailable
```
不删除原始记录，不改写历史。

### R1.6 lockfile 状态
```text
LOCKFILE_PRESENT = FALSE
```
INSTALL_ROOT 目录仅含 `.npmrc` / `package.json` / `node_modules`，无 `package-lock.json`。
本任务严格 READ_ONLY：未生成 lockfile，未执行 `npm install` / `npm ci` / `npm update`。
`lockfile missing` 属当前安装状态的一部分，不在本审计任务内修复。

### R1.7 安全复核（R1 时刻）
```text
V1_V2_V3_UNTOUCHED = TRUE
MT5_INSTANCE_COUNT = 3
MT5_ISOLATION      = PASS
ORDER_SEND_CALLS   = 0
LIVE               = FALSE
V3_LIVE_ALLOWED       = NO
V3_ORDER_SEND_ALLOWED = NO
V3_FORWARD_ALLOWED    = NO
EXPANSION             = LOCKED
Gateway version (现)  = 2026.9.4（未变）
```
未重启 Gateway / V1 / V2 / V3 / MT5；未执行升级；未执行方案 A / 方案 B；未执行 V3 formula fix / calibration expansion。

### R1.8 R1 结论
```text
STATUS           = FAIL   (保持原结论不变)
UPGRADE_EXECUTED = FALSE
UPDATER_BLOCKER  = TRUE
NEXT             = WAIT_FOR_CHATGPT_AUDIT
```
