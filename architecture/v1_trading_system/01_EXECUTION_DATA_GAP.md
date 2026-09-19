# EXECUTION DATA GAP — 经纪商 API 核验证据附录（2026-09-07）
> 主文档: architecture/v1_trading_system/00_ARCHITECTURE_MASTER.md §2
> 判定: **FXTM (ForexTime/Exinity) 无可靠原生直接交易 API → EXECUTION DATA GAP**
> 核验纪律: web_search 无 provider(与 scout 报告一致) → 用 web_fetch(官网/Bing/DDG) 实证。
> 证据等级: E2 = 本次实证核验; E1 = 既有知识未联网核验; UNKNOWN = 不可判定, 不猜。

## 判定结论(单句)
FXTM 当前零售账户通道(212070422 @ ForexTimeFXTM-Live01)只有 MT5 终端路径;
官网无任何原生交易 API 产品; 第三方桥=MT5 之上包装, 违反 H1。
**在找到并核验"原生 API 经纪商"之前, 执行层保持 DATA GAP, 不假装可直接交易。**

## 证据链
1. [E2] fxtm.com / forextime.com 全站检索 "API trading / FIX / REST": 无 API 产品页。
   - 直接抓取 fxtm.com/en/、/en/api/、/forextime-api、/forextime-fix-api、/en/help/ → 全部重定向至首页
     (官网为 JS SPA, 正文不可静态抓取; 404 于不存在路径)。
   - Bing "FXTM ForexTime trading API REST FIX official" (~10,400 结果): 前 10 页命中全部为
     登录/平台/帮助/投资/加盟/集团页(forextime.com, forextimeng.com, fxtmforex.net, exinity.com, partners.fxtmportal.com)。
     **无一为交易 API 产品/文档页。**
2. [E2] 对照组: FXCM(同类零售经纪商)有官方页面 fxcm.com/markets/algorithmic-trading/api-trading,
   提供 3 个免费 API(FIX/Java/ForexConnect)直连其交易服务器 → 证明"零售经纪商提供原生 API"是行业
   存在形态, FXTM 无对等物 = 结构性缺失而非行业惯例如此。
3. [E2] 第三方桥(MetaApi metaapi.cloud / API2Trade api2trade.com 等)存在且宣传 MT4/5 REST/WS:
   本质 = 终端/协议之上包装层 + 云托管 + 订阅费 → (a) 仍以 MT5 为执行中间层, 违反 H1;
   (b) 增加第三方故障/合规面; (c) 付费。不采用。记录在案供未来复核(若其直连经纪商服务器协议则另论, UNKNOWN)。
4. [E1] MT5 Python API(mt5 库, 现有采集器所用) = 本地 MT5 终端自动化: 需终端常驻+登录, 走终端-服务器
   协议 → 属"MT5 作为执行中间层", 违反 H1 执行层要求。**研究数据用途合规(现状), 执行用途不采用。**
5. [E1] MetaTrader 5 存在官方 Web API/Gateway 形态(供经纪商/机构), 但通常不向零售客户开放;
   FXTM 是否开放 = UNKNOWN(未见公开文档, 不猜)。即便存在, gateway 仍属 MetaTrader 生态中间层, 需单独评估是否符合 H1 精神。

## 候选替代(仅清单, 待逐一核验, 不承诺; 均涉及开户/API 权限 → 按宪章 C 类(付费/需批准)上报)
| 候选方向 | 形态 | 需核验点 | 与 hf_money_access_lab 关系 |
|---|---|---|---|
| 有官方 API 的零售/ECN 经纪商(类 FXCM/OANDA/IG) | 原生 REST/FIX, XAUUSD CFD | 产品存在性/账户可达/成本/合规 | 其 T1 通道(ECN/STP pro)同轨 |
| CME GC 期货(IBKR 类经纪商) | 原生 API, 真 L2 | 佣金/最低资金/开户 | 其 T2 通道同轨; 数据侧 Databento GC 已有 $25 pilot 路径 |
| FXTM 机构/白标 FIX(若存在) | FIX | 存在性 UNKNOWN; 非零售可达 | — |

## 什么不算 API(用户明示)
- MT5 Server 名称(如 ForexTimeFXTM-Live01) ✗
- MT5 登录接口(initialize/login) ✗
- 网页/MyFXTM 后台接口 ✗
- 第三方 MT5 桥(MetaApi/API2Trade) ✗ (除非未来核验为直连服务器协议)

## 下一步(DoD: 先核验后宣布)
1. 候选经纪商官网 API 文档逐家核验(免费, 同本次方法)。
2. 结论入 STATE.md 的 DATA GATE 队列, 待用户批准方向(涉及开户/预算, 宪章 C 类, 不自动进行)。
3. 执行层研发在 P0-P2(Simulation/Paper) 不受此 gap 阻塞(见主文档 §10)。
