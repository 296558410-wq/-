# V2 DATASOURCE DOMESTIC/MT5 REWIRE — 20260917

## 目标
数据层“全换国内/MT5”。Yahoo / CFTC / BLS / eastmoney 在本机**不可达**（403 / ConnectionError）；仅 **sina / tencent / 本地 MT5** 可达。

## 变更（数据层，不改策略）
- **新增 `data_sources/mt5_market.py`**：走 **V2 独立 MT5 实例**(fxtm_demo_01, 只读) 取 XAUUSD/XAGUSD 的 quote 与 history（copy_rates，PIT 剔除未收盘）。
- **registry**：`HISTORY_SOURCES = mt5 → local_fxtm → yahoo(降级)`；`QUOTE_SOURCES` 全国内：
  gold_spot=[mt5 XAUUSD, sina, tencent, local_fxtm]；silver=[mt5 XAGUSD, sina, tencent]；gold_comex=[sina,tencent]；
  dxy=[sina DINIW]；vix=[sina znb_VIX]；gld/tip/ust10y=[tencent usGLD/usTIP/usUST]。
- **router**：新增 `mt5` 分支（history/quote）。
- **adapters_market**：`q_sina` 支持 `DINIW`/`znb_*`；`q_tencent` 支持美股/ETF(`~`)格式。
- **agent2/sources**：新增 `macro_kv()`（经 Router，国内源）；`collect()` 改用国内：DXY=sina DINIW、UST10Y=tencent usUST(**7-10Y ETF 代理, 变更取反**)、VIX=sina znb_VIX、TIP=tencent usTIP、GLD=tencent usGLD；**COT/BLS/eastmoney=无国内源 → 显式 gap（不再打 403）**。
- 配置/面板标签更新（primary_source=mt5；宏观来源=国内）；`_age_s` 支持国内“YYYY-MM-DD HH:MM:SS”(北京时间)。

## 结果（实测）
- Agent1 主序列 now = **mt5**（`XAUUSD@mt5`，5 个周期无 error）。
- Agent2：DXY=100.20(sina)、UST10Y=usUST(反向)、VIX/TIP/GLD=国内；`macro_status=OK`；gaps: cot/bls=no_domestic_source、policy_rates、WGC、cb_purchases。
- 面板数据项来源显示：黄金价格 mt5 / 技术 mt5·local_fxtm / 宏观 sina·tencent / 新闻 wallstcn·cnbc / 资金流 暂无(eastmoney 不可达)。

## 测试 / 回归
`test_data_sources` 37/37（更新为 mt5-primary 契约）；`test_forward_gate` 8/8（门语义修正）；**全量回归 32/32 PASS**。一个真实 cycle：`WAIT / replay True / 无 error`。

## 行为/证据影响
- `BEHAVIOR_CHANGE=TRUE`（数据源变更，非策略）。
- 运行中 Shadow run `df35` 的后续决定将带**新 config_hash / 新数据版本** → G3 证据存在数据版本切换；如需“干净 G3”建议数据层稳定后**重启 G3 run**（待你定）。
- `FORWARD_VALIDATION_ALLOWED=NO`、未下单、未改 V1/历史 run。
