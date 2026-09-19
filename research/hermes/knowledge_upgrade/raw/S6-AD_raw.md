web_search 在本次会话被禁用（无 provider），已明确记录。改用 web_fetch 验证核心一手来源：arXiv 1 篇验证成功（E2）；NBER 抓取页返回非对应内容（JS 渲染错位，无法核验编号），故 NBER 记忆编号标记 E1 并以期刊卷期为准。其余全部按"训练知识 + E 级标注"降级处理，遵守证据上限 E3。以下为侦察报告。

---

# S6-AD 全局对抗侦察报告（XAUUSD 零售 feed 知识库压力测试）

**方法声明：** web_search 不可用（provider 禁用，2026-09-07 实测）。降级路径：web_fetch 验证（E2）+ 训练知识（E1，附高置信期刊/URL 模式）+ 聚合推理（≤E3）。凡无法验证者显式标注。

---

## ① 反例 / 失败模式卡（10 条）

**C1｜order flow 预测价格：真实但短暂、且强样本绑定**
Claim: order flow（含 imbalance）对价格有短期可测影响，但"可预测"≠"可交易 OOS"，长于数分钟的预测力普遍衰减。Mechanism: 信息攫取与库存效应的瞬时冲击 + 冲击后均值回归（transient impact）。
Evidence: Cont, Kukanov & Stoikov (2014, Quant. Finance, E2-已抓取 arXiv:1011.6402)：NYSE TAQ 50 股，短区间价格变动主由 best bid/ask 的 OFI 驱动，斜率∝1/深度——仅限短区间与集中撮合市。
Counter-evidence: Evans & Lyons (2002, JPE, E1) 外汇日频 order flow 预测，被 Rime, Sarno & Sojli (2010, JIE, E1) 反证：引入宏观信息后 flow 的 OOS 预测力弱且短暂；Sager & Taylor (2006, IJFE, E1) 指 flow 是信息 proxy 而非独立机制。冲击瞬时性综述见 Bouchaud et al. (2009, E1)。
Applicable markets: 美股 TAQ / EBS 外汇；XAUUSD relevance: 零售黄金 feed 无 signed flow，imbalance 不可重构，任何"flow 预测"只能做到 Proxy 级且窗口≤分钟。
Direct|Proxy|Inferred|Unknown: Proxy。
Current status: 已发表、短窗内广泛复现；OOS/跨期稳健性差（E1-E2）。

**C2｜做市盈利可持续：库存与逆选择是内禀成本，尾部一票清零**
Claim: 名义做市盈利（收 spread）不可外推为可持续策略；逆选择 + 库存尾部风险使多数做市商在应激期亏损退出。Mechanism: Glosten-Milgrom 型逆选择 + 存货风险非对称；市场冲击时 MM 被迫提供流动性给知情单。
Evidence: Kirilenko, Kyle, Samadi & Tuzun (2017, JF 72(3), E1)：2010-05-06 闪崩日 HFT 净买入并日内亏损离场——"提供流动性"在应激中不盈利。
Counter-evidence: 2015-01-15 SNB 取消 EURCHF 下限：Alpari UK 破产、FXCM 濒临清算（E1，广泛报道）；2020-03 COMEX-LBMA 价差曾>60-70 USD/oz，做市/套利资本集体失效（物流约束，E1）。显示 MM 盈亏的"利润"是尾部期权的短腿。
Applicable markets: 外汇/贵金属 OTC、期货；XAUUSD relevance: 直接适用——黄金做市 edge 的期望收益必须显式扣除应激跳跃（2011-08、2013-06、2020-03 均出现闪崩级 move）。
Direct|Proxy|Inferred|Unknown: Inferred。
Current status: 已发表支撑核心机制；行业事件证实尾部（E1）。

**C3｜HFT 整体盈利：极端集中 + 毛利/净利鸿沟 + 逐年压缩**
Claim: "HFT 整体赚钱"是聚合幻觉；盈利集中于极少数公司，多数 HFT 亏钱，且行业利润 2013 后显著压缩。Mechanism: 速度军备竞赛下的固定成本上升 + 拥挤侵蚀边际。
Evidence: Baron, Brogaard & Kirilenko (2019, JFQA 54(3), E1)：E-mini 上 HFT 单交易员毛利约 $2.9M/年但方差极大，多数交易员净亏，利润集中于尾部少数。
Counter-evidence: ESMA (2014) 欧盟 HFT 收入高度集中（E1）；Budish, Cramton & Shim (2015, QJE 130(4), E1)：军备竞赛为负和博弈，社会浪费。行业侧：Tabb Group 等估 HFT 股票利润 2013-2017 近腰斩（E1，行业媒体级）。
Applicable markets: 美股、E-mini、欧股；XAUUSD relevance: 零售 gold feed 上任何人都不具备与 CME/伦敦 tier-1 同速条件，C3 意味着"快钱"维度直接判负。
Direct|Proxy|Inferred|Unknown: Inferred。
Current status: 已发表 + 行业报告一致（E1）。

**C4｜行为异象扣成本后存活：动量崩盘 + 发表后衰减 + 成本吞噬**
Claim: 动量/处置/过度反应等异象在扣除交易成本、考虑崩盘与发表后套利后，可交易残值大幅缩水甚至归零。Mechanism: 异象收益 = 风险补偿 + 套利限制租金 + 数据挖掘残留；发表即被套利侵蚀。
Evidence: Daniel & Moskowitz (2016, JFE 122(2), E1)：动量崩盘（2009、1932）——条件性负偏度使趋势策略尾部灾难；McLean & Pontiff (2016, JF 71(1), E1)：97 个异象发表后收益衰减约 58%，OOS 衰减 26%。
Counter-evidence: 处置效应在散户中稳健（Odean 1998, JF, E1），但 Feng & Seasholes (2005, E1) 显示 sophistication/经验显著削弱之；机构与期货情境中弱/反向。Asness (2014, JPM, E1)：动量扣机构级成本仍存活，但散户级成本下非如此。
Applicable markets: 股票/期货/商品；XAUUSD relevance: 零售 gold 点差+隔夜利息成本量级（≥2×spread/往返）高于任何可存活异象的扣费残值，行为层知识只宜做状态判断而非 alpha。
Direct|Proxy|Inferred|Unknown: Inferred。
Current status: 成本侧结论已发表、争议小；动量净残值正负取决于执行层级（E1）。

**C5｜波动率择时：in-sample alpha 高度集中在少数月份，OOS 不稳**
Claim: "低波动月加杠杆/高波动月降仓"的择时 alpha 对样本期、波动估计量与成本极敏感，多数为风险控制而非 alpha。Mechanism: 波动聚集与 beta 时变的机械耦合，被误读为择时能力。
Evidence: Moreira & Muir (2017, JF, E1) 报波动管理组合显著 alpha。
Counter-evidence: Cederburg, O'Doherty, Wang & Yan（WP 2017+，E1，发表状态 UNKNOWN）再评估：alpha 主要来自 GFC 少数高波动月份，更换估计量/排除极端期后大幅消失；Liu 等后续检验亦示脆弱（E1）。
Applicable markets: 美股因子组合；XAUUSD relevance: 黄金波动率择时同样面临"alpha 来自 2020-03/2011 少数区间"的怀疑——本地纪律应把 vol 信号当仓位管理而非收益源。
Direct|Proxy|Inferred|Unknown: Inferred。
Current status: 正反双方均未定谳（争议中，UNKNOWN 终态）。

**C6｜条件/状态策略 OOS 稳健性：条件变量本身的状态依赖即失效源**
Claim: 以状态（regime/macro/vol 态）为条件的策略，其条件变量关系 OOS 不稳定，样本外多为随机游走级表现。Mechanism: 预测回归参数不稳定 + 状态识别滞后 + 条件变量是内生价格的函数。
Evidence: Meese & Rogoff (1983, E1) 开山：宏观基本面模型 OOS 打不过随机游走；FX 预测回归此后数十年无根本改善（Rossi 2013 综述，E1）。
Counter-evidence: Engel, Mark & West (2007, E1) 仅在极长 horizon/面板设定找到微弱 OOS 证据——强化"条件宏观→汇价"窗口极窄。状态切换 FX/商品模型的 OOS 失败是教科书级（E1）。
Applicable markets: FX、商品；XAUUSD relevance: 直接击中——黄金状态变量（实际利率、美元、避险态）的预测内容随 regime 翻转，本地知识库必须把"条件机会"标为 Inferred 且需滚动 OOS 门槛。
Direct|Proxy|Inferred|Unknown: Inferred。
Current status: 已发表共识（FX OOS 弱）；具体条件策略因变量而异（E1）。

**C7｜微观 edge 可扩展性：容量小 + 拥挤 + 发表即衰减三连**
Claim: 微观结构 edge 与容量负相关极陡；学术上报出的 LOB/flow 特征在规模、扣费、发表后三层衰减。Mechanism: 策略收益来自对倒流对手盘的稀缺性——规模越大越暴露给自己；套利者竞争使可观测特征失效。
Evidence: McLean & Pontiff (2016, E1) 衰减效应普适；LOB ML 基准（如 FI-2010, Ntakaris et al., E1）论文精度普遍在真实延迟/扣费下不可复现（社区共识级，E1）。
Counter-evidence: 队列优先类策略必须 co-location + 专用队列位，容量以"每分钟若干手"计（E1 行业常识）；Budish et al. (2015, E1) 证明速度租金是纯零和再分配——可扩展性与零和性互斥。
Applicable markets: 美股、期货、加密；XAUUSD relevance: 零售 feed（无深度/无优先权）上可提取的 edge 天然是全部策略中容量最小、最先被自己规模杀死的一类。
Direct|Proxy|Inferred|Unknown: Inferred。
Current status: 结构性结论稳健（E1）；具体容量数字 UNKNOWN。

**C8｜Feed 失真失败模式：零售报价不是"市场"，是零售商的内部市场**
Claim: 零售 A/B-book 报价流中的价格活动部分是做市商内化产物，与真实银行间 signed flow 无因果链——在此之上构建的任何 flow 叙事都是失真喂入。Mechanism: 零售经纪商可内化（B-book）订单，不进入 interbank/LBMA/CME；报价可含自身风险管理的伪 activity。
Evidence: 零售外汇/CFD 行业 A/B-book 模型为公开行业事实（E1，监管披露与行业文献；FINMA/FCA 案例级证据）。
Counter-evidence: 存在 A-book（真传递）经纪商，且报价通常锚定真实 interbank 流——失真程度不可观测 = 结构性 UNKNOWN。黄金 OTC 本身无 consolidated tape（LBMA 报告级滞后），本地纪律不能假设 feed 保真。
Applicable markets: 零售 FX/CFD/黄金 CFD；XAUUSD relevance: 本任务的全部研究对象（零售 XAUUSD feed）直接落在此卡内——知识库每一条"机制"都需标注 feed 失真容忍度。
Direct|Proxy|Inferred|Unknown: Unknown（失真度本身不可测）。
Current status: 行业事实（E1）；量化失真程度无公开测量。

**C9｜"看似机制实则 proxy"系统性错误：activity/volume/quote 替换 signed flow**
Claim: 无方向 feed 上最常见的系统性错误是用 activity（tick 数/成交笔数/成交量/价差变化）替代 signed flow，并在统计上伪造出"flow 预测力"。Mechanism: 方向缺失时任何代理都混入噪声成分（bid-ask bounce、新闻到达、做市商自我对冲），回归显著性是噪声自相关产物。
Evidence: Lee-Ready/tick-rule 分类准确率在电子化快市降至约 70-85%，误分类制造伪负自相关与伪 imbalance 信号（Odders-White 2000, E1; Chakrabarty et al. 2007, JBF, E1）。
Counter-evidence: 高频下 tick 方向与报价刷新存在真实信息成分（Cont et al. 2014, E2），但需真 signed 数据才能分离——无 signed flow 时任何"flow 代理回归"都应默认是伪回归。
Applicable markets: 全电子市场；XAUUSD relevance: 直接对照本地纪律（activity≠order flow、volume≠signed flow）——此卡即该纪律的外部证据版。
Direct|Proxy|Inferred|Unknown: Proxy（且高危）。
Current status: 已发表（E1）；本地纪律正确。

**C10｜迁移失败根因分类在 XAUUSD 的投射：四类全中**
Claim: 论文结果迁移到黄金零售 feed 的失败将来自四个可预注册的类别：regime artifact（黄金 2011-2013/2020-2021 结构断）、data snooping（同 feed 多轮搜索）、cost 漏算（点差/隔夜/滑点/展期）、feed 失真（C8）。Mechanism: 迁移默认"机制同构"，而实际四类误差叠加使 OOS 收益被系统性高估。
Evidence: McLean-Pontiff (E1) 与 Harvey-Liu-Zhu (2016, RFS, E1, t>3 门槛) 给出 snooping 定量基准；黄金样本含 2013-04 两日 -13% 与 2020-03 流动性真空（E1 市况事实）。
Counter-evidence: 迁移并非必然失败（同结构市场如 COMEX 期货微观研究部分可用，E1）——但无 signed flow 的 OTC 零售 feed 与学术样本结构差异最大。
Applicable markets: 黄金 OTC/期货；XAUUSD relevance: 本知识库所有五层知识的落地门槛——每条外部结论入库存前必须过四类检查。
Direct|Proxy|Inferred|Unknown: Inferred。
Current status: 分类学基于已发表证据（E1-E2）；"四类必查"为推荐纪律。

---

## ② 迁移失败经典案例（5 个）

**M1｜股权 TAQ order flow → FX/gold 现货 OOS 失败**（regime artifact + feed 失真）
Evans & Lyons (2002, JPE, E1) 的 flow 模型在引入宏观信息后 OOS 失效（Rime, Sarno & Sojli 2010, JIE, E1）；电子化外汇无 consolidated book、零售黄金 feed 无 signed flow——结构差异使"flow 预测"从 Direct 降为 Proxy/Unknown。

**M2｜股权动量 → 日本市场缺失 + 动量崩盘**（regime artifact + 数据 snooping 边界）
动量在日股长期缺失（Griffin, Ji & Martin 2003, E1；Asness 2014, E1），美国样本 2009/1932 动量崩盘（Daniel & Moskowitz 2016, JFE, E1）——同一"机制"在相邻市场/时期直接反转。

**M3｜tick-rule 分类与 LOB 特征 → 电子化期货/FX 市场**（feed 失真 + 结构差异）
在 dealer 市验证的分类规则迁移到快市后准确率跌至 70-85%，误分类伪造 flow 信号（Odders-White 2000, E1; Chakrabarty et al. 2007, E1）；LOB 队列机制在无中央限价簿的 OTC 黄金不成立。

**M4｜波动管理组合（股权）→ 商品/其他资产再评估**（cost 漏算 + 样本依赖）
Moreira-Muir 的 alpha 在再评估中收缩为少数危机月份贡献（Cederburg, O'Doherty, Wang & Yan, WP, E1）——迁移前必须重估"哪几个月在付钱"。

**M5｜学术异象 → 实盘扣费/做空约束后**（data snooping + cost 漏算 + 容量）
McLean-Pontiff (2016, E1)：发表后衰减 58%；Hou-Xue-Zhang (2020, RFS, E1) 复现率约 35%（本身有方法论争议，UNKNOWN）；零售黄金成本量级（点差+swap）高于多数异象残值。

---

## ③ Proxy 错误清单（5 条，对照本地纪律）

1. **trade/tick activity ≠ order flow**：无方向成交流不可逆推 signed flow；tick 规则分类误率 15-30% 会伪造 imbalance 自相关（Odders-White 2000；C9）。
2. **volume ≠ signed flow**：量是标量，买卖失衡才是驱动项；新闻/噪声时刻量增但不带信息方向（Cont et al. 2014 的 OFI 依赖方向标签，无标签即失效）。
3. **vol/价差变动 ≠ 信息到达 / 流动性提供**：价差收窄可能是 HFT 幽灵流动性（报价闪烁），成交量波动可能纯噪声；adverse-selection 分解（如 Huang-Stoll）依赖模型假设。
4. **COT/OI 仓位 ≠ 资金流**：黄金 COT 周频、滞后，且混入套保/掉期对冲头寸；OI 变动含展期机械成分——用其代表"聪明钱流"是经典误标。
5. **隐含波动（期权价）≠ 预期物理波动**：含方差风险溢价；零售 tick 的已实现波动被 bid-ask bounce 污染（需 TSRV/预平均去噪）——"波动率状态"若用错估计量，整个条件策略层漂移。

---

## ④ 值得等待的免费可观察方向（3 个，均为 Proxy 级——明确：无 Direct 级新变量）

1. **报价事件失衡（quote-event imbalance）**：无成交方向也可从 best bid/ask 的刷新方向构造 signed 事件流（买价上修 vs 卖价下修），是 tick-rule 之外结构上更干净的方向代理；文献锚点即 Cont et al. (2014) 的事件框架（E2）。**Proxy（较优）**——本地纪律的"activity vs flow"在此有定量分界可做。
2. **微观噪声状态变量**：用签名图斜率 / 方差比 / bounce 幅度估计"噪声 regime"（Hansen-Lunde 2006, E1；Zhang-Lan-Mykland-TSRV 2005, E1），把伦敦薄市 vs 纽约重叠、数据商节流时段变成可标记状态——免费、纯 tick 派生。**Proxy→状态分类，机制意义弱但稳健**。
3. **跨盘基差与相关性对齐诊断**：零售 XAUUSD tick 与免费可得的相关市场 tick（EURUSD/DXY、COMEX 延迟报价、XAU 与白银联动）的对齐/背离可做"合成方向推断 + 市场状态（流动性真空/脱锚）标记"；2020-03 式基差 blowout 是可免费观测的 regime 报警器。**Proxy**，且仅诊断不预测。

**结论：无 Direct/机制级新免费变量——signed flow、深度、队列、真实 OTC 成交均不可免费获得。三条方向全部是 proxy 升级，价值在"降低现有代理的失真"而非"打开机制级空间"。**

---

## ⑤ 来源列表（E 级标注）

- **E2（web_fetch 实抓验证）**：Cont, Kukanov & Stoikov (2014) *The Price Impact of Order Book Events*, Quantitative Finance; arXiv:1011.6402 (https://arxiv.org/abs/1011.6402)。
- **E1（训练知识，高置信）**：Daniel & Moskowitz (2016, JFE)；McLean & Pontiff (2016, JF)；Harvey, Liu & Zhu (2016, RFS)；Hou, Xue & Zhang (2020, RFS)；Baron, Brogaard & Kirilenko (2019, JFQA)；Budish, Cramton & Shim (2015, QJE)；Kirilenko, Kyle, Samadi & Tuzun (2017, JF)；Moreira & Muir (2017, JF)；Cederburg, O'Doherty, Wang & Yan（WP，发表状态 UNKNOWN）；Meese & Rogoff (1983, JME)；Evans & Lyons (2002, JPE)；Rime, Sarno & Sojli (2010, JIE)；Sager & Taylor (2006, IJFE)；Odean (1998, JF)；Feng & Seasholes (2005, E1)；Odders-White (2000)；Chakrabarty, Li, Nguyen & Van Ness (2007, JBF)；Griffin, Ji & Martin (2003)；Asness (2014, JPM)；Hansen & Lunde (2006)；Zhang, Mykland & Aït-Sahalia (2005)；ESMA (2014) HFT 报告；NBER 工作页编号（w20410/w19205/w6982）抓取失败（JS 渲染错位），故 NBER 编号一律不引用，仅引期刊卷期。
- **E1（事件/行业事实级）**：SNB 2015-01-15 EURCHF 事件及 Alpari/FXCM；2020-03 COMEX-LBMA 基差 blowout；2013-04 黄金闪崩；2010-05-06 闪崩；零售 A/B-book 模型（FCA/FINMA 披露级）。
- **验证限制说明**：web_search 全程禁用；E1 条目未逐篇二次抓取，卷期信息来自训练知识（置信高但非逐字核对）；C5/C10 中发表状态不确定处已标 UNKNOWN。外部证据最高 E3，无虚构来源。