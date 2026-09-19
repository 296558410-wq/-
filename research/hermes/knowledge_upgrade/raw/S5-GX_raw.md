web_search 确认不可用（provider disabled），web_fetch 部分可用——已成功核验两个 Wikipedia 锚点（E2）。全部学术文献按规则降级处理：标注 E1（无法取回）/E3（高置信训练知识、未逐页核验，给全作者+年份+出处）。以下为完整侦察报告。

---

# S5-GX 侦察报告：黄金微观结构 × HFT/做市真实利润机制（知识任务）

**会话约束声明**：`web_search` 在本会话被禁用（无 provider），已尝试 BIS 与 Wikipedia 直抓。外部证据等级重定义：**E1** = 本次会话无法取回外部来源（纯训练知识）；**E2** = 本次 web_fetch 直接核验（Wikipedia 两页，fetched 2026-09-07）；**E3** = 确信存在的真实文献（作者+年份+出处，URL 未能本会话核验）。证据上限 E3，凡标 E1 处数值请主系统视作待核。

---

## ① 机制卡（8 条，建议编为 MECH-12..19）

**MECH-12｜价格发现主源在 COMEX 期货（GC），伦敦 OTC/LBMA 滞后跟随**
Claim: 日内价格发现由 GC 电子盘主导，OTC dealer 报价与 LBMA 定盘以 GC+EFP 基准盯市。| Mechanism: CLOB 聚合订单流+24h 连续+杠杆投机/套保流集中，信息先达期货；Garbade-Silber 逻辑。| Why: OTC 双边报价由 dealer 半手工维护，更新频率与信息承载低于中央簿。| Observable variables: 领先滞后、basis——当前数据**不能**（无 GC 数据）。| Required data: GC tick/分钟+真 spot mid。| Timescale: 秒–分钟（亚秒需 L2）。| Expected payoff: 领先时段价差+基准套利。| Execution dependency: 交易所直连+清算资格。| Cost sensitivity: 中（手续费+跨洋 colo 延迟）。| Evidence: Garbade & Silber 1983；多篇 futures-lead 共识 E3。| Counter-evidence: 伦敦上午/定盘窗 OTC 短暂主导；2020-03 basis 脱钩（见 MECH-13）。| Applicable: 期货/现货双轨商品。| XAUUSD relevance: 核心结构，当前数据**不能观察**。| **Inferred** | Status: UNVERIFIED(E3)。

**MECH-13｜Basis/EFP 收敛套利：常态真利润，挤压期结构性断裂**
Claim: GC−伦敦 spot−carry 价差被套利钉在租借率附近，银行/MM 赚 basis 收敛+EFP 流动性费。| Mechanism: 期现套利者吸收基差偏离；交割通道是收敛的物理保障。| Why: 黄金可借贷、类货币定价（GOFO/contango 结构，E2：Wikipedia London bullion market 确认"黄金按利率差定价、常态正 contango"）。| Observable variables: 基差、租借率——**不能**（无 GC/租赁数据）。| Required data: GC+spot+GOFO/lease。| Timescale: 分钟–日。| Expected payoff: 常态为 carry 级小利；挤压期巨大。| Execution dependency: 实物交割/EFP 通道+清算线。| Cost sensitivity: 高（仓储/运输/精炼）。| Evidence: 2020-03 记录级期货溢价（峰值约 US$60-80/oz，E1 数值待核）；CME 2020-04 紧急规则允许交割伦敦 400oz 条（E3 报道级）。| Counter-evidence: 该套利**恰恰在危机时失效**——瑞士精炼厂停产+航空中断+COMEX 规格限制阻断反向交割，basis 不收敛，做市商库存亏损。| Applicable: 有实物交割约束的期货-现货对。| XAUUSD relevance: 解释 2020-03 大波动根源；数据**不能观察**。| **Inferred** | Status: UNVERIFIED(E3)。

**MECH-14｜做市真实利润=价差−逆向选择−库存成本；分布右偏厚尾，多数参与者微利/亏损**
Claim: "做市稳定赚钱"是叙事；实证为极端异质性+集中度。| Mechanism: 被动双边挂单赚半价差，但被知情流/宏观跳变击中即亏损；利润集中少数。| Why: MM 是逆向选择受体，最优报价在信息劣势下只能赚"不中毒的薄利"。| Observable variables: 需成交级数据——**不能**。| Required data: L1/L2+成交+公司级账户（不可能）。| Timescale: 日-月利润分布。| Expected payoff: 方差极大。| Execution dependency: 低延迟+风控。| Cost sensitivity: 极高（尾部一次=数月利润）。| Evidence: Baron, Brogaard, Hagströmer & Kirilenko（E-mini HFT 公司样本，2012 WP/2019 JFQA）：盈利集中、多数公司利润微薄、存在显著亏损日 E3。| Counter-evidence: SNB 2015-01-15 瑞郎脱钩杀死一批 FX MM 与零售经纪（Alpari UK 破产，E3）；2020-03 MM 大额撤单。| Applicable: 所有做市。| XAUUSD relevance: 主系统若按"MM 恒赚"建模属叙事偏差；feed **不能观察**。| **Inferred** | Status: UNVERIFIED(E3)。

**MECH-15｜队列优先/回扣套利：equities maker-taker 特有，XAUUSD 结构上基本不存在（被高估机制）**
Claim: "排队抢优先+吃回扣"是美股/部分期货叙事；CME 金属**无 maker 回扣**（双边收费+量折扣），OTC 黄金无中央簿无队列。| Mechanism: 价格-时间优先存在但无回扣激励；GC tick=10¢/oz=US$10/口，抢头寸收益低于股指/国债。| Why: 机制移植需 maker-taker 费用表+深中央簿，两者在黄金链条均缺位。| Observable variables: 队列/深度——**不能**。| Required data: L2+费用表。| Timescale: —。| Expected payoff: 趋近 0（在此结构）。| Execution dependency: —。| Cost sensitivity: 高（无回扣补贴时 latency 投入不划算）。| Evidence: Budish-Cramton-Shim 2015 QJE 主张的延迟套利租金集中于**股票/期货/ETF 复合体**（含 GC-GLD 腿），而非 OTC 现货 E3。| Counter-evidence: 真正的黄金延迟套利在 GC↔GLD↔dealer 报价之间（见 MECH-16），不是簿内队列游戏。| Applicable: 美股/有回扣期货。| XAUUSD relevance: **可迁移性判断：此机制应降权**。| **Direct**（判断本身） | Status: UNVERIFIED(E3)。

**MECH-16｜延迟套利真实版：GC/GLD（全自动）↔ 伦敦 OTC dealer 报价（半自动/人工）→ 跳变后打 stale 报价**
Claim: 黄金上可持续的 HFT 利润源是跨层报价更新速度差，不是簿内速度差。| Mechanism: 新闻/期货跳变后，dealer 的 OTC 或零售报价滞后数百 ms-数秒，HFT 抢先成交。| Why: OTC 报价链（交易员确认、last look 决策、人工干预）天然慢于 CLOB。| Observable variables: 需双数据源比对——当前**不能**（无 GC tick 对照，FXTM feed 本身即 dealer 输出）。| Required data: GC/GLD tick + 独立 OTC/零售 quote。| Timescale: ms–s。| Expected payoff: 中；被 last look 侵蚀。| Execution dependency: 与 dealer 的信用/主经纪关系。| Cost sensitivity: 中。| Evidence: FX 电子化文献：King, Osler & Rime 2013；BIS Markets Committee 电子交易报告（2016）E3；黄金专项量化 E1。| Counter-evidence: **Last look** 允许 dealer 在窗口内拒单——OTC 侧自带对冲，吃掉该套利相当部分（FX Global Code 2017 起规范收窄，E3）。| Applicable: 半自动 OTC 品种。| XAUUSD relevance: 最接近"真实机制"的一类，但 feed 上不可直接观察。| **Inferred** | Status: UNVERIFIED(E3)。

**MECH-17｜零售 CFD 层利润 = 点差加价 + B-book 客户负偏现金流（行为租金，非市场结构利润）**
Claim: 零售经纪对手方是 dealer 自己；"HFT 策略打零售 feed"= 与 dealer 定价权对赌，不是与市场对赌。| Mechanism: 固定点差内已含 dealer markup；B-book 下客户亏损/爆仓/隔夜利息即 dealer 收入。| Why: 无真实流出的客户流是负和（成本+点差），dealer 赚期望。| Observable variables: feed 层面只能见价格路径。| Required data: 客户账户聚合（不可能）。| Timescale: 持续。| Expected payoff: dealer 侧确定；客户侧负偏。| Execution dependency: —。| Cost sensitivity: —。| Evidence: 2015 EURCHF 事件后多家零售经纪破产证明 B-book 尾部风险真实（E3 报道级）。| Counter-evidence: A-book 经纪（全对冲）利润来自佣金/点差差价，生存依赖客户交易量而非亏损。| Applicable: 所有零售 CFD/FX。| XAUUSD relevance: 直接警告：**在此 feed 上做市商级策略前提不成立**。| **Direct** | Status: UNVERIFIED(E3)。

**MECH-18｜LBMA 定盘拍卖窗（10:30/15:00 London）：可预测订单流+操纵史→可事件研究**
Claim: 电子单一定价拍卖（2015 起 ICE 运营，14 参与方，含算法做市商如 Jane Street——E2 核验）在窗口末端产生再平衡/套保流；历史证明窗口信息价值极高。| Mechanism: 不平衡迭代拍卖、买家付 20¢/oz 费用、参与者可"举旗"暂停（E2：Wikipedia Gold fixing 全细节核验）。| Why: 大量衍生品/ETF 以 LBMA 价为锚 → 拍卖前后出现锚定交易流。| Observable variables: 报价路径在 10:30/15:00 London 邻域的行为——**部分可观察**（代理事件研究，无拍卖簿）。| Required data: 现有 FXTM/DUKA 报价即可启动。| Timescale: 分钟–小时。| Expected payoff: 事件研究价值高，直接交易价值中。| Execution dependency: 无（仅研究）。| Cost sensitivity: 低。| Evidence: E2 核验——2012-06-28 Barclays 操纵案、2014-05 FCA £26M 罚款、2014-01 Deutsche Bank 退出；E3——2014-15 银行 WM/R FX 基准罚款总额约 US$10B+ 量级，同类基准脆弱性。| Counter-evidence: 监管后公开操纵显著下降；拍卖簿不可见使"预测净方向"难度高。| Applicable: 基准拍卖市场。| XAUUSD relevance: **主系统现有数据可做的少数真实结构研究之一**。| **Proxy** | Status: SUPPORTED_EXT（机制层面 E2）。

**MECH-19｜零售 feed（固定点差+volume≡0）上微观结构工具族结构性失效——是 DATA_GAP 不是暂时缺数据**
Claim: Roll/有效价差、Kyle λ、Amihud、VPIN、存货模型、簿失衡在 vol≡0+无成交+固定点差下**全部不可识别**。| Mechanism: 这些估计量都依赖成交价反弹、真实量或簿状态，feed 中这些字段不存在或恒为伪值。| Why: 数据是 dealer 的"产品输出"，非市场事件流。| Observable variables: 仍可观测——报价路径的波动聚类/跳跃/GARCH、时区结构、fix/新闻窗效应、停顿/缺口（dealer 行为代理）。| Required data: 现有即可。| Timescale: —。| Expected payoff: 转向 quote-path 统计学与事件研究，放弃结构推断。| Execution dependency: —。| Cost sensitivity: —。| Evidence: 微观结构教科书级依赖关系（E1 常识）。| Counter-evidence: DUKA 历史报价若来自可变点差 dealer，可恢复部分价差动态（**部分**缓解，但仍非真实市场）。| Applicable: 所有零售 CFD 数据。| XAUUSD relevance: 定义主系统研究的**能力边界**。| **Direct** | Status: DATA_GAP。

---

## ② 反例/失败模式：HFT 赚钱叙事 vs 实证

| 叙事 | 实证反例 | 标注 |
|---|---|---|
| "HFT/做市普遍稳定盈利" | Baron et al.（E-mini 样本）：盈利高度集中、多数公司微利、有显著亏损日；幸存者偏差使公开印象失真 | E3 |
| "做市=无风险收价差" | 库存与尾部风险：SNB 2015 脱钩（Alpari UK 破产）；2020-03 MM 撤单、黄金 spread 展宽 10-50× 量级 | E3/E1 |
| "延迟套利=免费午餐" | 租金被军备竞赛耗散（Budish et al. 2015：连续拍卖制造延迟套利租金，社会浪费）；last look 拒单对冲 OTC 侧 | E3 |
| "黄金 HFT 利润与股指同构" | 黄金 80%+ OTC 不可见、无中央簿队列、dealer 关系+信用门槛 → 队列跳跃/回扣工具失效；可迁移机制只剩跨层 stale-quote 打单（MECH-16） | Inferred |
| "Flash crash 是 HFT 造成" | Kirilenko-Kyle-Samadi-Tuzun（2017 JF）：HFT 非肇因，但关键时刻撤流动性、放大波动 | E3 |
| "零售 feed≈真实市场降采样" | feed 是 dealer 产品：真实 spread ×10-100 时固定点差纹丝不动、vol≡0、缺口/停顿；结构推断=照镜子看路况 | Direct |
| "操纵是旧时代故事" | 基准脆弱性持续：2014 Barclays £26M（E2 核验）；FX WM/R 罚款 ~US$10B+ 总量（2014-15）；贵金属 spoofing 起诉至今（CFTC v. Sarao 同族，E3） | E2/E3 |

**可迁移性核心判断**：对主系统的 XAUUSD 问题——在"OTC 现货+无 L2/无成交流"结构里，**真创造钱的机制**是：① dealer/银行层价差+库存对冲生意（MECH-14，不可见）；② 跨市场基准/套利（MECH-13/16，需 GC 数据）；③ 零售层行为租金（MECH-17，与策略研究无关）。**论文故事类**：队列优先/回扣套利（MECH-15）——结构上在此市场无载体。

---

## ③ 零售 CFD feed 结构性不可观察清单（相对真实市场）

| # | 失真项 | 能否从当前数据观察 |
|---|---|---|
| 1 | 真实 bid-ask 动态（与波动/库存风险联动）→ 固定点差无信息 | 不能 |
| 2 | 深度、簿不平衡、队列位置 | 不能 |
| 3 | 成交量、成交流、signed flow、time&sales | 不能（vol≡0） |
| 4 | 有效价差/Roll/实现价差（需成交价反弹） | 不能 |
| 5 | 信息冲击率（Kyle λ）、Amihud 非流动性 | 不能（无真实量） |
| 6 | 毒流/VPIN | 不能 |
| 7 | dealer 存货、对冲行为、B/A-book 比例 | 不能（商业机密） |
| 8 | 成交概率/fill rate/last look 拒绝 | 部分（从滑点与止损执行质量反推，Proxy） |
| 9 | 期货-现货 basis、期限结构、GOFO/租借率 | 不能（无 GC/租赁数据） |
| 10 | 与真实市场同步性与延迟 | 部分（已知事件时刻比对响应延迟；无独立真值则不能绝对化） |
| 11 | 波动聚类、跳跃、时区/时段结构 | **能**（纯统计，Proxy） |
| 12 | LBMA fix 窗（10:30/15:00 London）、宏观发布窗事件研究 | **能**（事件时刻已知） |
| 13 | 报价停顿/gap/重复报价/点差冻结 → dealer 行为代理 | **能**（Proxy 性质） |

---

## ④ UNKNOWN（≤5）

1. **FXTM/DUKA feed 的生成管线**：时间戳是 dealer 事件时间而非市场成交时间；报价是否由单一 LP 合成、是否插值平滑——决定第 11-13 项结论的解释边界。类型：Unknown。
2. **GC↔伦敦 spot 分钟级领先滞后是否在近年在黄金仍显著**（经典文献多为 2000s-2010s 数据）；需 GC 数据验证，当前无。类型：Unknown（E1）。
3. **2020-03-24 伦敦盘初黄金 flash 的确切触发订单与簿况**（幅度 ~US$80±、分钟级、V 型收复——报道级记忆，无权威事后分解报告可引）。类型：Unknown（E1）。
4. **LBMA 拍卖参与方（含 Jane Street 等算法做市商）是否在窗内/窗外系统获取稳定 alpha**——拍卖簿与参与者流量不可观察，无法证伪。类型：Unknown。
5. **零售 dealer 的 B/A-book 比例与对冲行为**（FXTM 自身）——商业机密；决定"客户流是否进真实市场"。类型：Unknown。

---

## ⑤ 来源列表

**E2（本会话 web_fetch 核验，2026-09-07）**
- Wikipedia: *Gold fixing* — en.wikipedia.org/wiki/Gold_fixing。核验内容：拍卖机制（10:30/15:00 London、不平衡迭代、买家 20¢/oz 费、"举旗"暂停）、当前 14 参与方名单（含 Jane Street、Koch、Marex 等）、1919 起源、Barclays 2012-06-28 操纵 + 2014 FCA £26M 罚款、2014 Deutsche Bank 退出。
- Wikipedia: *London bullion market* — en.wikipedia.org/wiki/London_bullion_market。核验内容：LBMA OTC 批发结构、BoE 监督、T+2 结算、黄金按利率差类货币定价、常态正 contango/借贷市场。

**E3（高置信训练知识，URL 未本会话核验；web_search 禁用故未逐页验证）**
- Garbade, K. & Silber, W. (1983). "Price Movements and Price Discovery in Futures and Cash Markets." *Review of Economics and Statistics* — 期现价格发现方法学基石。
- Baron, M., Brogaard, J., Hagströmer, B. & Kirilenko, A. (2012 WP/2019 JFQA). "Risk and Return in High-Frequency Trading" — E-mini HFT 盈利异质性/厚尾。
- Brogaard, J., Hendershott, T. & Riordan, R. (2014). "High-Frequency Trading and Price Discovery." *Review of Financial Studies*。
- Kirilenko, A., Kyle, A., Samadi, M. & Tuzun, T. (2017). "The Flash Crash: The Impact of High Frequency Trading on an Electronic Market." *Journal of Finance*。
- Budish, E., Cramton, P. & Shim, J. (2015). "The High-Frequency Trading Arms Race." *Quarterly Journal of Economics*。
- Menkveld, A. (2013). "High Frequency Trading and the New Market Makers." *Journal of Finance*。
- King, M., Osler, C. & Rime, D. (2013). "Foreign Exchange Market Structure, Players and Evolution."（FX 微观结构综述章）。
- BIS Markets Committee (2016). *Electronic trading in fixed income markets*（电子化/流动性报告）；FX Global Code (2017)（last look 规范）。
- CFTC v. Sarao（E-mini spoofing）；2014-15 六家银行 WM/R FX 基准罚款（总量 ~US$10B+ 量级）。

**E1（本会话无法取回/数值待核）**
- 2020-03 黄金期现溢价峰值幅度（~US$60-80/oz）、CME 2020-04 紧急交割规则细节、lease/GOFO 极端值、3-24 flash 细节；LBMA 成交调查口径日均 OTC 成交量数值；GC 日均成交量与 OI 现值。全部为量级/方向可信、精确数值待主系统核验。

---

**给主系统的一句话结论**：在此零售 CFD 数据上，"高频/做市怎么赚钱"的答案不是可复现策略而是能力边界——feed 能支撑的是 quote-path 统计（波动/跳跃/时段）、fix 与新闻窗事件研究、以及 dealer 行为代理检测；所有依赖簿、流、量的结构机制（队列、回扣、存货、毒流）在本数据集上结构性不可观察，且其中多数机制在真实黄金 OTC 结构里本就不存在或形态完全不同（OTC dealer 生意 + last look + 基准套利 + 行为租金才是真利润源）。

---

*侦察会话 S5-GX 结束。任务性质为知识侦察：无策略开发、无回测、无数据购买、无交易动作。*