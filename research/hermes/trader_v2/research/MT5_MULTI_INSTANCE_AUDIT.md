# MT5 多实例并行启动 —— 审计与可行性（Phase 1–2）

> 日期: 2026-09-11 · 原则: **MT5_EXISTING = READ_ONLY**（未关闭/未重启/未登录/未改配置/未改账户）。
> **未下单；未连接 broker；未启动第二实例的登录。** 现有实例全程未受影响（复核 PID 不变）。

## Phase 1 — 现有 MT5 只读识别
| 项 | 值 |
|---|---|
| executable | `C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe` |
| 数据目录 | `%APPDATA%\MetaQuotes\Terminal\158904DFD898D640E9B813D10F9EB397`（origin.txt → 上述安装目录） |
| 是否运行 | **是** |
| PID | **1348**（StartTime 2026/9/9 06:20:57） |
| 登录账户 | **********（来自本机 `.env.mt5_demo`，密码不显示；该终端即 V1 使用的 demo） |
| Server | `ForexTimeFXTM-Demo01` |
| 是否存在 EA | MQL5\Experts 有 98 个文件（存在 EA/脚本资产） |
| 是否存在运行策略 | 只读不可判定（`accounts.dat` 加密）；V1 由 **Python `MetaTrader5` 库驱动**（外部进程），非终端内 EA |
| 控制台会话 | `surface`（ID 1，运行中）→ 有 GUI |
| 数据目录内容 | bases / config / logs / MQL5 / Tester / temp / llm-agent |

## Phase 2 — 独立实例（已创建）
- 目录：`C:\AIQuant\mt5_instances\fxtm_demo_01\`
- 方法：**robocopy 复制"程序目录"**（不复制/不覆盖数据目录）；含 `terminal64.exe` (121.7MB) 等。
- 计划运行方式：`terminal64.exe /portable`（官方支持的独立数据目录 = 该文件夹自身）→ 与现有实例**进程/数据目录/账户**三者隔离。
- **尚未启动**（见阻断项）。

## 阻断项（必须由你处理）
1. **凭据缺失**：`FXTM_DEMO_LOGIN / FXTM_DEMO_PASSWORD / FXTM_DEMO_SERVER / FXTM_DEMO_INVESTOR` 均 **NOT SET**。无法自动登录新 Demo（也绝不允许把凭据写进代码/config/日志）。
2. **登录是交互式的**：MT5 无官方命令行传账号密码的登录方式；全新 portable 实例首次启动会弹出登录框，需 GUI 输入（或预先由你手工登录一次并保存）。

## 风险与安全评估
- 现有实例与测试实例：**不同进程 + 不同数据目录 + 不同账户** → 理论互不影响；`/portable` 是不干扰的官方隔离方式。
- 唯一需警惕：若 `/portable` 未被遵守（旧 build）→ 可能回落到共享数据目录。**启动后必须立即核验**：测试实例是否在自身文件夹生成数据（而非 `%APPDATA%` 新建 hash 目录）；一旦发现抢占迹象 → **立即 kill 测试实例并停止**。
- 本实例为 **Demo（虚拟资金）**；即便如此仍不启动登录/下单，待你确认。

## Phase 2B — 并存验证（已执行，未登录）
**结果: `MULTI_INSTANCE_PROCESS_ISOLATION_PASS`**

启动命令: `C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe /portable`（未输入任何凭据、未登录、未下单）。

| 检查 | 结果 |
|---|---|
| 原 MT5 进程 | PID **1348** RUNNING（StartTime 2026/9/9 06:20:57 **未变**） |
| 测试 MT5 进程 | PID **10816**（≠1348）RUNNING（20:40:17 起） |
| 测试实例数据目录 | **`C:\AIQuant\mt5_instances\fxtm_demo_01\`**（Config/ logs/ MQL5/ Bases/ Profiles/ 实际写在此） |
| 是否使用原数据目录 | **否**（`158904...` 未被触碰） |
| APPDATA 出现的新目录 `5F32...` | 仅 `origin.txt`(→AIQuant 副本) + `portable.txt` + 空 `liveupdate/` = **portable 注册存根，非数据目录** |
| 双实例并存观察 | 两进程同时运行 ≥35s 稳定 |
| broker 登录 / 订单 | **无**（全新实例未登录；orders=0） |
| 原实例是否被影响 | **否**（PID/启动时间/数据目录全程不变） |

收尾: 已**关闭测试实例（PID 10816）**；原实例 1348 继续运行。副本文件夹保留（备后续登录/校准实验，**未入 git**）。

## Phase 3–6 — 登录 + 只读验证（已执行）
凭据来源：**Windows 用户级环境变量** `FXTM_DEMO_*`（未落任何文件/git/日志）。
方法：`MetaTrader5.initialize(path="C:\AIQuant\mt5_instances\fxtm_demo_01\terminal64.exe", portable=True, login/password/server)`
→ **先校验绑定目标=data_path 含 `fxtm_demo_01` 才登录**（否则拒绝）。

| 验证项 | 结果 |
|---|---|
| 实例启动 | ✅ 测试终端 RUNNING（数据目录 `C:\AIQuant\mt5_instances\fxtm_demo_01`） |
| 绑定目标校验 | ✅ data_path = 测试目录（**非** V1 的 `158904...`） |
| 登录 | ✅ 成功（`16*****24` @ `ForexTimeFXTM-Demo01`） |
| 账户类型 | ✅ trade_mode=0 (**DEMO**) |
| balance / equity / margin_free | 2033.65 / 2033.65 / 2033.65 USD，leverage 500 |
| 黄金 symbol | ✅ 实际品种名 = **`XAUUSD`**（另有 XAUEUR/XAUAUD/XAUCNH/XAUGBP/XAUJPY） |
| 行情 | ✅ XAUUSD bid **4362.61** / ask **4362.75** / spread **0.14** / time 1789141728 |
| 订单 | **0**（未下任何单，未改 SL/TP，未平仓） |
| V1 终端 | ✅ PID 1348 全程不变 |

备注：终端级 `trade_allowed=False`（Algo 未开）—— 不影响只读；下单仍需三重安全门（当前未满足）。测试实例**保持登录运行**（供后续 Paper vs Demo 校准）。

## 当前状态
- Phase 1 ✅ / Phase 2 ✅ / Phase 2B ✅ / Phase 3–4 ✅（已登录）/ Phase 6 ✅（行情）/ Phase 7 未触发。
- 订单 0；未修改 SL/TP；**V1 零修改**。
