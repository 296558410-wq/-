# 11_DATA_WATCHLIST — 最值得等待的数据/观测量（2026-09-07 审核定稿）
> 只列"若获得会真正改变研究空间"的项。免费优先；付费项保持 DATA_GATE 待批。
> 与 DATA_GAPS.md（money_hunter）分工：本文件是知识侧 watchlist，那边是执行侧登记。

## Tier 1 — 免费可得，优先行动
| # | 数据/观测量 | 解锁什么 | 路径 | 状态 |
|---|---|---|---|---|
| 1 | **MT5 Demo 真实成交日志**（fill/拒单/requote/slippage/latency） | 隐含加价实测（KU-C16/U2）；RQ-07 校准；0.1bps 上界实证 | 免费注册（同 S-09 动作） | 代码就绪，待用户一次性注册 |
| 2 | **quote-event imbalance 自测**（报价刷新方向 signed proxy） | aggressor 方向的最优免费代理是否可行（KU-C34） | 现有 FXTM/DUKA 报价流本地构造 | 可立即做（观察级） |
| 3 | **宏观事件日历 + fix 时刻表**（已知时间） | 事件窗/定盘窗研究（KU-C27/C33）；drift 环分层 | 免费公开 | 部分已有，可补全 |
| 4 | **跨盘免费 tick 对齐**（EURUSD/DXY/白银/GC 延迟报价） | 脱锚报警 + 合成方向推断 + 状态标记（S6-AD ④3） | 免费源 | 未接入 |
| 5 | **波动状态估计量升级**（TSRV/预平均去噪） | 修正 bid-ask bounce 污染的 RV → 条件层不漂移（S6-AD proxy 错误 5） | 本地计算 | 可做 |

## Tier 2 — 付费/数据门（非免费，保持待批，不主动买）
| # | 数据 | 解锁什么 | 成本 | 状态 |
|---|---|---|---|---|
| 6 | GC(COMEX) tick/分钟 + L2 | 价格发现领先滞后（KU-C30）、跨层套利观察（KU-C31）、真 signed flow 替代 | Databento GC MDP3 $25 | S-07 待批 |
| 7 | CME 期权持仓/链（OOF） | dealer gamma、VRP（KU-C27 相关） | 贵 | DATA_GATE(非 HF 优先) |
| 8 | CFTC COT 细分类（若需周频以上） | 行为/对冲压力（KU-C20/C23） | 免费周频已有；高频无 | 周频已够观察 |

## 明确不等的（结构性无解）
- 零售 A/B-book 内部数据、dealer 账户级流、真实 OTC 成交流 → 永久不可公开获得（KU-C32；CL-08 保持 INACCESSIBLE）。
- 当前 FXTM feed 的 volume≡0 不会变（除非换 feed/换经纪商 demo）。

## 审核注
Tier 1 #1 与 #2 是"不花钱、不换系统"就能把最大 UNKNOWN 缩小一半的两步；建议在观察环稳定后优先做 #2（纯本地），#1 等用户免费 demo 注册。
