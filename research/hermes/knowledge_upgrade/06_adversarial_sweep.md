# 06_ADVERSARIAL_SWEEP — 全局对抗扫描审核（OpenClaw 主控压缩 S6-AD）
> 确保知识库不是"支持证据收集器"。完整 Claim 卡: 07_CORE_CLAIMS.yaml (KU-C34/C35, 各卡 counter_evidence)。
> 原始: raw/S6-AD_raw.md。

## 最强反证（审核采纳，10 卡核心）
1. **order flow 预测价格**：真实但短暂+强样本绑定（Cont 短窗 vs Rime-Sarno-Sojli FX OOS 弱）。
2. **做市盈利可持续**：库存+逆选择是内禀成本，尾部一票清零（Kirilenko 闪崩日 HFT 亏损；SNB 2015；2020-03）。
3. **HFT 整体盈利**：聚合幻觉——极端集中、多数亏钱、2013 后利润压缩（Baron-Brogaard-Kirilenko 2019 JFQA）。
4. **行为异象扣成本存活**：动量崩盘+发表后衰减 58%（Daniel-Moskowitz；McLean-Pontiff）。
5. **波动率择时 alpha**：集中于 GFC 少数月份，换估计量消失（Cederburg et al. WP，发表状态 UNKNOWN）。
6. **条件/状态策略 OOS**：Meese-Rogoff 传统——宏观条件模型 OOS 打不过随机游走。
7. **微观 edge 可扩展性**：容量小+拥挤+发表即衰减三连。
8. **feed 失真**：零售报价是"零售商的内部市场"（A/B-book），失真度本身不可测=结构性 UNKNOWN。
9. **proxy 系统性错误**：activity/volume/quote 替换 signed flow → 伪回归（本地纪律的外部证据版）。
10. **迁移失败四类根因**：regime artifact / data snooping / cost 漏算 / feed 失真（KU-C35，入库存必查门槛）。

## 迁移失败经典案例（审核采纳）
股权 TAQ flow→FX/gold 失败；动量→日股缺失+崩溃；tick-rule/LOB 特征→快市/FX 失败；vol-managed→再评估收缩；
学术异象→实盘扣费（Hou-Xue-Zhang 复现率 ~35%，本身有方法论争议标 UNKNOWN）。

## Proxy 错误清单（对照本地纪律，S6 外部证据版）
1. activity ≠ order flow（tick-rule 误率 15-30% 伪造 imbalance）
2. volume ≠ signed flow（标量无方向）
3. vol/spread 变动 ≠ 信息到达/流动性提供（幽灵流动性）
4. COT/OI ≠ 资金流（周频滞后混套保）
5. 隐含波动 ≠ 预期物理波动（含 VRP；bid-ask bounce 污染 RV——需 TSRV 去噪）

## 值得等待的免费可观察方向（审核结论：无 Direct 级新变量）
1. **quote-event imbalance**（KU-C34）：报价刷新方向构造 signed proxy——较优 Proxy，可本地自测。
2. 微观噪声状态变量（签名图斜率/方差比）——Proxy→状态分类，稳健但机制意义弱。
3. 跨盘基差/相关性对齐诊断（XAUUSD vs EURUSD/DXY/白银免费 tick）——2020-03 式脱锚报警器，仅诊断不预测。
**结论：signed flow/深度/队列/真实 OTC 成交均不可免费获得；三条方向全是 proxy 升级，价值在降低代理失真。**

## 来源可信度审核备注
- 主控抽查：Baron-Brogaard-Kirilenko "Risk and Return in High Frequency Trading"（Crossref 确认，SSRN 2433118→JFQA 2019）✓
- Rime-Sarno-Sojli（Crossref 确认存在）✓；Novy-Marx-Velikov NBER w20721（S2 直抓 E3）✓
- NBER 工作页编号抓取失败（JS 渲染）——已降级只引期刊卷期，处置正确。
- 全库外部证据 ≤ E3；无一冒充 XAUUSD 已证明。审核通过。
