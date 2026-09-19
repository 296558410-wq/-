# FXTM Direct Broker API —— 可行性调查报告

> 日期: 2026-09-11 · 方法: **仅官方/公开资料检索**（未连接 FXTM、未启动 MT5、未抓包/未逆向）。
> 结论: **DIRECT_API_NOT_AVAILABLE** —— FXTM 不提供对零售客户开放的官方直连交易 API。

## 调查方法（合规）
- 官方站点检索（fxtm.com / forextime.com）、官方帮助中心、公开搜索结果。
- 对比同类经纪商（FXCM）以确认"是否存在该类 API"的行业惯例与判据。
- **禁止**：逆向 MT5 协议、抓包破解、绕过认证、模拟私有协议 —— 全程未做。

## 关键证据
1. 关键词 `"FXTM" FIX API OR "REST API" trading` → **No results found**（无任何 FXTM 官方 API 条目）。
2. `site:fxtm.com api` → 仅命中 FXTM **Affiliate Portal**（联盟后台），**无开发者/交易 API 页面**。
3. FXTM 官网为 MT4/MT5 **经纪商**：其程序化交易入口 = MetaTrader 平台（EA/指标），无官方 REST/FIX/WebSocket 交易 API。
4. 搜索结果中出现的 "MetaTrader REST/WS API" 实为**第三方桥**（MetaApi.cloud、API2Trade），**非 FXTM 官方/授权**接口 → 按本任务约束排除。
5. 对比：FXCM 提供官方 **FIX / Java / ForexConnect / REST** API（需机构/最低余额）—— 说明行业确有此类 API，但 **FXTM 不提供**。

## 结论与阻塞
- **FXTM 没有对零售/当前 Demo 账户开放的官方直连交易 API**；唯一官方程序化路径是 MetaTrader（需终端，即 `Hermes → MT5 → FXTM`）。
- MT5 的 Web API / Manager API 属**经纪商服务端**能力，不开放给零售客户；FIX 未在 FXTM 公开。
- 因此"完全绕过 MT5 直连 FXTM"**当前不可行**。**未实现任何私有协议适配器**。

## 可选路径（供决策，本轮均未实施）
| 方案 | 说明 | 是否满足"官方/授权" |
|---|---|---|
| A. 维持 MT5 通道 | 即 V1 现状（终端驱动） | ✅ 官方（但需 MT5） |
| B. 换有官方 API 的券商 | 如 **OANDA v20 REST**（与早前 V2 设想一致）、FXCM FIX/ForexConnect | ✅ 官方（换券商） |
| C. 第三方桥（MetaApi/API2Trade） | 免终端直连 MT5 账户 | ❌ 非官方/未授权 → 排除 |

## 未执行 / 未产生
- 未执行 `execution/fxtm_direct_adapter.py`（不存在——因无官方 API，未创建）。
- 代码未对 FXTM 发起任何连接；未产生任何订单；未启动 MT5。
- 模块 2 的 `FXTMDemoAdapter` 仍 **DISABLED**（安全门未满足）。
