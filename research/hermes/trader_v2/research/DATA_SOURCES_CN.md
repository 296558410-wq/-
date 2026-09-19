# V2 数据源可达性（中国大陆网络直连实测）

> 测试时间：2026-09-11 19:40–19:43 CST（本机 DESKTOP-LQ0B8O3，无代理）。方法：真取内容校验。
> 结论：**V2 可以完全靠中国大陆可直连的源采集**；只有 FRED 不可达（用替代）。

## A. 行情 / 价格（首选国内源，快且稳）
| 用途 | 源 | 端点/代码 | 实测 |
|---|---|---|---|
| 伦敦金现货 | 新浪 | `hq.sinajs.cn/list=hf_XAU`（需 Referer） | ✅ 200 / 实盘价 |
| 纽约金 COMEX | 新浪 | `hf_GC` | ✅ |
| 白银 | 新浪/腾讯 | `hf_SI` | ✅ |
| 黄金/GLD | 腾讯 | `qt.gtimg.cn/q=usGLD` | ✅ |
| 美元指数 | 东方财富 | `push2.eastmoney.com/...secid=100.UDI` | ✅ 实盘 |
| COMEX金 | 东方财富 | `secid=101.GC00Y` | ✅ |
| 纳指 | 东方财富 | `secid=100.NDX` | ✅ |

## B. 行情补全 / 历史 K 线（Yahoo 直连可用）
| 用途 | 源 | 端点 | 实测 |
|---|---|---|---|
| 历史 K 线（M5/M15/H1/H4/D1） | Yahoo chart | `/v8/finance/chart/<sym>?range=..&interval=..` | ✅ |
| 美元指数 DXY | Yahoo | `DX-Y.NYB` | ✅ |
| VIX | Yahoo | `^VIX` | ✅ |
| 美债 10Y | Yahoo | `^TNX` | ✅ |
| 黄金 | Yahoo | `GC=F` | ✅ |
| GLD | Yahoo | `GLD` | ✅ |
> 注：Yahoo 的 `/v7/finance/quote` 需鉴权（401），但 **`/v8/finance/chart` 无需鉴权**，用它取价与历史。
> `XAUUSD=X` 在 Yahoo 404 → 现货金用新浪 `hf_XAU`。

## C. 宏观 / 官方
| 用途 | 源 | 实测 |
|---|---|---|
| 美国国债收益率/财政数据 | `home.treasury.gov` | ✅ 200 |
| 欧央行 | `ecb.europa.eu` | ✅ 200 |
| 央行/利率/经济日历 | 东财财经日历 `data.eastmoney.com/cjsj/`；金十 `rili.jin10.com` | ✅ 200 |

## D. 黄金资金流
| 用途 | 源 | 实测 |
|---|---|---|
| COT 持仓报告 | `cftc.gov` | ✅ 200 |
| SPDR GLD 持仓/历史 | `spdrgoldshares.com/usa/historical-data/` | ✅ 200 |
| iShares GLD | `ishares.com/us/products/239561/ishares-gold-trust-fund` | ✅ 200 |
| 上海黄金交易所（在岸溢价） | `sge.com.cn/sjzx/mrhq` | ✅ 200（页内数据） |

## E. 新闻 / 地缘
| 用途 | 源 | 实测 |
|---|---|---|
| 全球快讯(JSON) | 华尔街见闻 `api-one.wallstcn.com/apiv1/content/lives?channel=global-channel` | ✅ JSON |
| 英文快讯 | CNBC RSS `search.cnbc.com/rs/...` | ✅ XML |
| 外汇/黄金新闻 | `fxstreet.com` | ✅ 200 |
| 中文快讯 | 金十 `jin10.com`；东财 | ✅ |

## F. 不可达（需替代）
- **FRED**（`fred.stlouisfed.org`）→ 超时（大陆常见）。替代：Yahoo `^TNX` + 美国财政部 + 东财宏观。
- Stooq `xauusd` → 404（代码问题，非墙）；Yahoo/国内源已覆盖。
- 已弃：`cdn-rili.jin10.com`（DNS 失败）→ 用 `rili.jin10.com`。

## 设计结论
1. **多源 + 回退**：价格按 `新浪 → 腾讯 → 东财 → Yahoo` 依次回退；任一家挂掉不中断。
2. 每个数据点记录 `data_timestamp(发布时刻) / retrieval_ts / source / source_version`（point-in-time 纪律）。
3. 全部走 `requests`（已在 `.venv`），无需额外付费/Key；Yahoo 用 chart 接口免鉴权。
