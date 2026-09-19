# EXECUTION PATHWAY — 原生 API 执行通道方案（OANDA v20）
> 状态: 方案定案 · 待用户一次性免费动作(注册 demo + 生成 token)
> 关联: architecture/v1_trading_system/01_EXECUTION_DATA_GAP.md(原判定 FXTM=GAP)
> 2026-09-07 核验更新: **FXTM 仍无原生 API, 但发现合规替代执行经纪商 = OANDA(v20 REST)**

---

## 1. 为什么选 OANDA(证据, E2 web 实证 2026-09-07)
| 项 | 证据 |
|---|---|
| 原生交易 API | developer.oanda.com/rest-live-v20: Order/Trade/Position/Account/Pricing/Transaction 全端点, place/modify/close orders |
| 无 MT5 中间层 | v20 是直连 OANDA fxTrade 交易引擎的 REST API; MT5 只是其可选前端之一(非必需) |
| XAU/USD 黄金 | OANDA 官方提供 Metals CFDs(XAU_USD); 市场数据含 2005 起历史 |
| 免费 demo | 官方文档明确 "Try a free demo account"; demo = practice 环境, 虚拟资金 |
| 认证 | 个人 access token(AMP 生成), 非账号密码直传 |
| 杠杆/账户 | 零售标准账户; demo 环境同构 → 满足 P3 Demo Exec 阶段 |
| 对比 FXTM | FXTM 官网无任何 API 产品页(原核验 E2) → 维持 FXTM=EXECUTION DATA GAP 判定 |

## 2. 通道分层更新(hf_money_access_lab T 表修订)
| Tier | 通道 | 成本 | 状态 |
|---|---|---|---|
| T0 | FXTM retail MT5(现状) | 1.6-1.7bps 实测 | 研究数据; 执行=GAP |
| **T0.5** | **OANDA v20 demo(新)** | 0(免费 demo); live 点差~1bps 级(标准账户, 需开户核实) | **执行通道首选**; 待用户注册 |
| T1 | ECN/STP pro(Pepperstone 类) | 0.2-0.6bps | 备选; 待核验 |
| T2 | CME GC 期货(IBKR) | $2-5/边 | 远期; 需资金门槛 |

## 3. 需要用户的一次性动作(免费, ~10 分钟)
1. 注册 OANDA 免费 demo 账户: https://fxtrade.oanda.com (demo/practice 注册)
2. 登录 fxTrade → My Services → Manage API Access → 生成 personal access token
3. 把 token + account_id 存入本地环境(不写入仓库; 提供方式任选: 环境变量/单独 .env 不入 git)

⚠️ 不要求真实资金: demo 账户 = 虚拟资金, 满足 V1 的 Paper/Demo 阶段且不触发"真实资金授权"红线。

## 4. 接入架构(与 V1 主蓝图一致, 不改总架构)
```
OANDA v20 (demo)  ← Broker API 层(新: broker_oanda.py 适配器)
   ├─ REST: https://api-fxpractice.oanda.com (demo 端点)
   ├─ 认证: Authorization: Bearer <token>
   ├─ 行情: /v3/instruments/XAU_USD/candles (已收盘 bar, 补现有 feed)
   ├─ 下单: /v3/accounts/{id}/orders (market/limit/stop + SL/TP 同单)
   ├─ 持仓: /v3/accounts/{id}/openTrades, /positions
   └─ 成交反馈: /v3/accounts/{id}/trades/{id}/orders (close), transactions
        ↓
   Execution Engine 适配(paper 模式可切换 demo 模式, 默认仍 paper)
        ↓
   Position State Machine(现有, 不变) → ledger(现有) → Dashboard(账户/持仓变真实)
```

## 5. 阶段门映射(V1 §10)
| 阶段 | 状态 |
|---|---|
| P0 Research / P1 Simulation / P2 Paper | 已完成/运行中(不依赖 OANDA) |
| **P3 Demo Exec** | **OANDA demo 解锁 = 此阶段入口**; 小单实测 latency/slippage/reject |
| P4 Execution Validation | demo 完整闭环 |
| Real | 仍需用户明确书面授权 + 真账户(非 demo) |

## 6. 风险与诚实标注
- [UNKNOWN] OANDA demo 的 XAU_USD 点差/滑点/最小单位: 注册后实测, 不猜
- OANDA 标准账户点差高于 ECN(行业常识级): 若实测成本吃掉 edge → 维持 NO MONEY 结论,
  不因"能下单了"就声称能赚钱(正确性 ≠ 盈利)
- demo 成交乐观性: demo 流动性好于真实 retail → 真实资金前须重测(标注于 Execution Validation)
- 本方案不违反: 不花用户钱/不改总架构/不绕过 Risk/不进入真实资金

## 7. 下一步(阻塞点 = 用户一次性动作)
1. [用户] 注册 OANDA demo + 生成 token(见 §3)
2. [自动] broker_oanda.py 适配器(读 env, fail-closed: 无 token 不发单)
3. [自动] P3: demo 小单测量(latency/slippage/spread/reject) → RQ-07 校准
4. [自动] 完整闭环: Hermes 决策 → OANDA demo 执行 → 真实成交反馈 → 记忆
