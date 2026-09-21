# V3-HFT-CALIBRATION-FORMULA-FIX-002 — 最终审计材料包（INDEX）

> **任务ID**: `V3-HFT-CALIBRATION-FORMULA-FIX-002`（只读审计材料整理）
> **被审计任务**: `V3-HFT-CALIBRATION-FORMULA-FIX-001`
> **性质**: 把 FORMULA-FIX-001 的**真实证据**打包到 GitHub，供 ChatGPT 独立审计。
> **本次没有新订单**：`ORDER_SEND_CALLS = 0`、`NEW_CALIBRATION_ORDERS = 0`；未重跑 calibration pilot；未修改任何业务代码。

---

## 0. 一页速览（供审计快速定位）

| 项 | 值 |
|---|---|
| BASE_COMMIT | `6170050dcd6397f29193effc4f0baaed9036e2ab` |
| FINAL_CODE_COMMIT | `4f6bd54c4a4963fb2885921fee1d7adb510c940a` |
| FINAL_AUDIT_COMMIT (local) | `4ac5a240e752c40ebd1a968350c6f3e95d176cd7` |
| STAGING_COMMIT | `461b980bcf4b11506073ed3424fbe5f9e4849e18` |
| origin/main | `461b980bcf4b11506073ed3424fbe5f9e4849e18` |
| HEAD == origin/main | `TRUE` |
| Broker 真实净值（20 笔） | **-7.44 USD**（-0.372 USD/RT） |
| Corrected 公式结果 | **-7.44 USD**（-0.372 USD/RT） |
| 对平 | **20/20**（total_error 3.7e-14 USD） |
| 旧公式结果 | -2.75 USD（-0.1375 USD/RT）→ 系统性乐观 +0.2345 USD/RT |
| 安全 | ORDER_SEND_CALLS=0 · LIVE=FALSE · EXPANSION=LOCKED · V1/V2/OpenClaw UNTOUCHED |

---

## 1. 公式代码证据（必须能实际看到代码）

```text
OLD FORMULA FILE:
  research/hermes/trader_v3/foundation/calibration_pilot.py
  （BASE commit 6170050 的版本；其 _round_trip() 内联 net_pnl 计算）

CORRECTED FORMULA FILE:
  research/hermes/trader_v3/foundation/pnl_accounting.py      <-- 新增：纯函数、可单测
  research/hermes/trader_v3/foundation/calibration_pilot.py   <-- 改为调用 pnl_accounting

TEST FILE:
  research/hermes/trader_v3/foundation/tests/test_v3_formula_fix.py   (A–I, 9 tests)

OFFLINE RECOMPUTE SCRIPT:
  research/hermes/trader_v3/audit/v3_formula_fix_recompute.py
```

### 旧公式（BASE，错误）
```text
net = (fill - entry) * 方向符号
      - spread_cost          # 重复：成交价已含 bid/ask
      - entry_slippage       # 重复：已在成交价内
      - abs(exit_slippage)   # 符号错误：有利出场被成本化
      - commission           # 符号反转：commission<0 是成本
      + 其它
```

### 新公式（CORRECTED，公式版本 `v3-calibration-netpnl-2`）
```text
gross_pnl_usd = (exit_fill_price - entry_fill_price) * direction_sign * contract_size * volume
corrected_net_pnl = gross_pnl_usd + commission + swap
```

### 变量定义与约定
| 变量 | 定义 | 处理 |
|---|---|---|
| `entry_fill_price` / `exit_fill_price` | ledger ENTRY_FILL / EXIT_FILL 的实际成交价 | 直接使用；spread/slippage **已包含在内，不再单独扣** |
| `direction_sign` | LONG=+1 / SHORT=-1 | 由 side 决定 |
| `volume` | 手数 | 固定 0.01（实测 volume_min） |
| `contract_size` | `symbol_info("XAUUSD").trade_contract_size` | **100.0**（实测，非假设 1 lot=1 oz） |
| `tick_size` | `trade_tick_size` | 0.01（实测） |
| `tick_value` | `trade_tick_value` | 0.1（实测；与 contract_size 不自洽 → 见 DATA_GAP） |
| `commission` | MT5 deal.commission | **符号约定：负值=成本，直接相加，不反号** |
| `swap` | MT5 deal.swap | 直接相加（本批为 0） |
| `currency_profit` | 账户货币 | USD |
| spread / slippage | 诊断量 | 标注 `EMBEDDED_IN_FILL_PRICE_NOT_DEDUCTED`，**不计入 corrected** |

> 说明：本公式**不使用 tick_value**（用 contract_size × volume），因此 `TICK_VALUE_INCONSISTENT` 不影响 corrected 结果。

---

## 2. 审计材料索引

| # | 文件 | 内容 |
|---|---|---|
| 1 | `README.md` | 本索引 + 证据关系 |
| 2 | `V3-HFT-CALIBRATION-FORMULA-FIX-001-RESULT.md` | 最终报告（与正式报告**逐字节一致**） |
| 3 | `V3-HFT-CALIBRATION-FORMULA-FIX-001-RESULT.json` | 最终报告（机器可读，A–K 结构） |
| 4 | `v3_calibration_formula_fix_20trades.csv` | 20 笔逐笔（含 **entry/exit order + deal id** / broker 事实 / 新旧净值 / observed_spread / 双边滑点 / hold_actual_ms / 规格与货币 / 对平 / evidence_status） |
| 5 | `broker_facts_20trades.json` | Broker 不可变事实导出（40 deal + 40 order + symbol spec，**无任何凭据**） |
| 6 | `git_diff_formula_fix.patch` | `git diff BASE FINAL -- research/hermes/trader_v3/` |
| 7 | `git_diff_stat.txt` | 同上 `--stat`（`git diff --stat BASE FINAL`） |
| 8 | `changed_files.txt` | 修改文件清单（name-status） |
| 9 | `commit_lineage.json` | BASE/CODE/AUDIT/STAGING 四 commit 的 parent·subject·changed files·purpose |
| 10 | `reconciliation_summary.json` | 20/20 对平汇总（broker vs corrected） |
| 11 | `reconciliation_method.md` | **计算路径**（证明非自证循环） |
| 12 | `test_results.md` | 9/9 + 28/28 测试证据与命令 |
| 13 | `safety_final.json` | 安全只读核查结果 |
| 14 | `data_gaps.md` | **DATA_GAP 完整披露**（DG-1..DG-6：DESCRIPTION / IMPACT / CAN_RECONSTRUCT / USED_IN_CORRECTED_PNL） |
| 15 | `SHA256SUMS.txt` | 本包全部材料哈希清单（含 data_gaps.md） |

---

## 3. 文件之间的证据关系（怎么串起来）

```text
                    BASE 6170050
                        │  (公式修复)
                        ▼
   code 4f6bd54 ──────────────────────────────► foundation/pnl_accounting.py  (corrected 公式)
        │            │                              foundation/calibration_pilot.py (接入)
        │            │                              foundation/tests/test_v3_formula_fix.py (A–I)
        │            │                              audit/v3_formula_fix_recompute.py  (离线重算)
        │            ▼
        │        audit/v3_formula_fix_summary.json  ──┐
        │        audit/v3_formula_fix_comparison.csv ─┤
        │                                             │  交叉得到
        ▼                                             ▼
   audit 4ac5a24 ──► 本材料包 ──►  v3_calibration_formula_fix_20trades.csv  (逐笔合并)
                        │                    ▲
                        │                    │ join by trade_id / deal ticket
                        │        broker_facts_20trades.json (独立事实源)
                        ▼
                 reconciliation_summary.json ◄── reconciliation_method.md (计算路径)
                        │
                        ▼
                 V3-HFT-...-RESULT.{md,json}  (结论)
                        │
                 git_diff_formula_fix.patch + changed_files.txt + commit_lineage.json
                        │   (证明改动范围只在 V3，且 commit 链无歧义)
                        ▼
                 safety_final.json + SHA256SUMS.txt  (安全与防篡改)
```

**独立性**：`broker_facts_20trades.json` 与 corrected 计算**无数据依赖**；对平是"独立算完再比"，不是复制（详见 `reconciliation_method.md`）。

---

## 4. Commit 链（从 Git 实际读取，非猜测）

| commit | 类型 | parent | subject | 作用 |
|---|---|---|---|---|
| `6170050` | BASE | — | `audit(v3): record base/audit commit metadata for V3-HFT-COST-BRIDGE-AUDIT-001` | 修复前状态 |
| `4f6bd54` | CODE | `6170050` | `fix(v3-calib): V3-HFT-CALIBRATION-FORMULA-FIX-001 broker-anchored net_pnl …` | **真正的公式修复** + 测试 + 重算产物（6 文件） |
| `4ac5a24` | AUDIT | `4f6bd54` | `report(v3-calib): FORMULA-FIX-001 canonical result (md+json) + section-6 20-trade table + reports/ copies` | 正式报告与 §六 表（6 文件） |
| `461b980` | STAGING | — | `report(v3-calib): FORMULA-FIX-001 canonical result (md+json) - A-K structure, …` | 报告发布到 GitHub staging |

完整展开见 `commit_lineage.json`。

---

## 5. 安全声明（本次整理任务）

```text
ORDER_SEND_CALLS = 0
NEW_CALIBRATION_ORDERS = 0
LIVE = FALSE
V3_ORDER_SEND_ALLOWED = NO / V3_LIVE_ALLOWED = NO / V3_FORWARD_ALLOWED = NO
EXPANSION = LOCKED
V1_UNTOUCHED = TRUE / V2_UNTOUCHED = TRUE / OPENCLAW_UNTOUCHED = TRUE
MT5_INSTANCE_COUNT = 3 / MT5_ISOLATION = PASS
```

本材料包**不含**任何 password / token / API key / `.env` / 私钥。

---

## 6. 反自证循环声明

corrected P&L 由 `(fill price, volume, contract_size, commission, swap)` **独立计算**，
再与 `broker_facts_20trades.json` 的 deal 事实比较；**不是读取 broker net 后回填**。
方法学见 `reconciliation_method.md`，可复算见 `test_results.md`（Test H）与 `v3_formula_fix_recompute.py`。
