数据与来源收集完毕。web_search 整体不可用（provider 禁用），已按纪律降级为"直接抓取已知权威 URL + 训练知识"；成功核实 3 个一手来源（BIS QR 2016-12、NBER w20721、GFXC FX Global Code 2024-12），Almgren-Chriss 原始 PDF 被 403（标 E1）。以下是完整侦察报告。

---

# S2-EX 侦察报告：LEVEL 2 EXECUTION KNOWLEDGE
**任务**：为什么有理论 edge 的信号在真实执行成本下变负 EV —— 机制层知识升级（不做策略、不写回测）
**背景锚点**：XAUUSD 零售 CFD feed（无 L2/队列/成交流）；retail 往返≈1.7bps；已测可提取上界≈0.1bps/笔
**证据等级**：E1=仅训练知识（无法在线核实）；E2=URL 已抓取、间接相关或作者归属部分来自记忆；E3=URL 已抓取、一手内容直接核实（外部证据上限 E3）

---

## ① 机制卡（≤8 条，每条 6 行）

### MECH-C1｜中点价回测幻觉：taker 被强制吃整个价差（成本地板）
**Claim:** 用 mid 价撮合的"信号 alpha"不可实现——retail taker 买入成交在 ask、卖出在 bid，每笔往返被扣除全额报价价差，信号必须先穿透这层固定税。
**Mechanism:** 回测成交价=mid（或 best bid/ask 的有利侧）；真实成交价=mid±(半价差+加价+费)。EV 偏移=−(round-trip cost)/2 每笔每边，与预测方向无关，是纯平移。
**Why it happens:** 报价价差是流动性提供者的补偿（见 MECH-C2），retail 无渠道以 mid 成交；CFD 经纪商把佣金隐藏进加价价差（spread markup），等价于固定 per-trade 税。
**Observable variables:** backtest fill price vs 实际 fill price 差；bid/ask quote 记录；成交时点 spread 宽度 | **Required data:** 逐笔真实成交价（非 mid 重建）；broker spread markup 表。
**Expected timescale:** 每笔立即生效 | **Expected payoff:** 净 EV = 毛 EV − 往返成本 ≈ 0.1bps(上界) − 1.7bps < 0 | **Execution dependency:** 完全依赖执行方式（taker 全额付税）。
**Cost sensitivity:** 一阶线性敏感（成本直接线性扣除） | **Evidence:** Novy-Marx & Velikov NBER WP20721(E3)：计入成本后多数 anomaly 失去显著性；成本削减策略(尤其 buy/hold spread)是唯一高效解 | **Counter-evidence:** 低频、低换手、长持有的 edge 可存活（Frazzini-Israel-Moskowitz, E1） | **Applicable markets:** 所有做市制市场 | **XAUUSD relevance:** 直接命中：1.7bps vs 0.1bps 即此机制的算术 | **Direct | Status: SUPPORTED_EXT**（机制外部铁证；本 feed 未做逐笔核对→feed 级 UNVERIFIED）

### MECH-C2｜成交条件性逆向选择：赢家诅咒（Glosten–Milgrom）
**Claim:** 被成交本身是坏消息——对手方（做市商/知情者）只在对你有利时才不愿成交、对你不利时才成交；于是"预测对的交易"和"能被成交的交易"系统性负相关。
**Mechanism:** 价差 = 逆向选择补偿 + 存货成本 + 处理成本。你下买单，若价格即将下跌，做市商急于卖给你（成交率高）；若价格即将上涨，做市商撤单/加宽（成交率低）。可实现 alpha < 回测 alpha。
**Why it happens:** 对手方拥有你不掌握的信息或更快的信息处理；成交选择不是随机的——fill 事件载荷着方向信息（selection bias on fills）。
**Observable variables:** fill 后短期价格条件分布（fill 后 1–60s 价格相对 fill 价的漂移）；成交率 vs 信号强度 | **Required data:** 逐笔成交+时间戳（本 feed 无成交流→需真实账户 fill 日志）。
**Expected timescale:** fill 后毫秒–分钟级劣化 | **Expected payoff:** 把"每笔 0.1bps 可提取上界"进一步打折 | **Execution dependency:** 弱——taker 模式也无法豁免（对手就是你的对手）。
**Cost sensitivity:** 非线性——信号越短周期、越拥挤，逆向选择占比越高 | **Evidence:** Glosten & Milgrom 1985(E1)；Baron-Brogaard-Kirilenko(E1)实证 HFT 利润主要来自对慢盘的逆向选择 | **Counter-evidence:** 大单边宏观事件（如 NFP）中方向信号可能快于 dealer 调整 | **Applicable markets:** 所有订单驱动/做市市场 | **XAUUSD relevance:** retail CFD 对手方=经纪商/其上游 LP，流动性事件中直接体现为"滑点总在不利侧" | **Proxy | Status: SUPPORTED_EXT**

### MECH-C3｜Maker 侧经济学：排队位置、成交概率与被 pick-off
**Claim:** 若 retail 挂限价单充当 maker，则省下价差税但承担新税：排队靠后时只在价格穿过你时成交（被逆向选择），且无 L2/队列数据时完全无法管理排队位置——省下的税 < 新增的逆向选择损失。
**Mechanism:** 限价单 = 免费期权卖给市场：价格触及即成交；价格远离则持仓。队列尾部的单被成交当且仅当价格已移动到对你不利的位置（pick-off risk）。做市商靠 rebate+极低延迟+队列头位置存活；retail 三者皆无。
**Why it happens:** 价格触发你的挂单时，市场动量常常延续（momentum spillover）；无速度优势者无法在触发前撤单。
**Observable variables:** limit 单成交后价格续走概率；成交前等待时间；挂单距离 vs 成交率 | **Required data:** 订单簿队列快照+成交归属（本 feed 无 L2、无队列→结构性 DATA_GAP）。
**Expected timescale:** 秒–分钟级 | **Expected payoff:** maker 路径的期望税 = 逆向选择损失 − 价差节省，多数情形仍为负 | **Execution dependency:** 完全依赖（此机制即执行方式选择）。
**Cost sensitivity:** 高——挂单越近（省 spread 越多）逆向选择越强，存在内生最优距离 | **Evidence:** Hautsch & Huang 2012(E1)：排队位置决定成交概率与影响；Cont-Kukanov-Stoikov(E1)订单簿事件模型 | **Counter-evidence:** 深度贴水挂单做"被动抄底"在均值回归 regime 可正 EV（需可验证回归性，见 UNKNOWN-4） | **Applicable markets:** 有中央订单簿的市场；FX ECN/部分 CFD 内部撮合近似 | **XAUUSD relevance:** 中——本 feed 无法挂单进真实队列，maker 路径基本不可用/不可验证 | **Inferred | Status: UNVERIFIED**（机制成立，feed 级不可观测→倾向 DATA_GAP）

### MECH-C4｜冲击与紧迫性：Almgren–Chriss 型最优执行（规模-速度-成本三角）
**Claim:** 当信号持仓需要"现在立即成交"时，执行成本随速度与规模凸性上升；retail 单笔极小→市场冲击≈0，但正因如此，**固定 per-trade 价差税无法被规模摊薄**——小单吃不到冲击成本的规模经济。
**Mechanism:** 执行成本 = 价差税(固定) + 冲击(≈κ·σ·√(Q/V)，平方根律) + 机会成本(等待时价格漂走)。AC 框架把总成本写成 urgency 的凸函数；最优执行在"立即全成交"与"缓慢 TWAP"之间折中。retail 每笔 Q→0 ⇒ 冲击项→0，只剩固定项 ⇒ 成本/预期收益比反而最差。
**Why it happens:** 冲击随规模平方根增长（容纳大资金）而非线性——大资金成本占比随规模下降；retail 天然落在成本占比最高、无摊薄可能的区间。
**Observable variables:** 分片执行 vs 全量执行的价差（VWAP 差异）；订单大小 vs 成交均价偏移 | **Required data:** 真实成交滑点 vs 名义规模曲线（本 feed 逐笔滑点日志可建，规模维度受限）。
**Expected timescale:** 执行窗口分钟–小时 | **Expected payoff:** 确认"容量约束下限"：任何策略可提取总量 = 每笔可提取上界 × 笔数，且每笔都被 1.7bps 固定税碾压 | **Execution dependency:** 完全依赖。
**Cost sensitivity:** 对 per-trade 固定成本一阶敏感；对规模弱敏感（此即问题） | **Evidence:** Almgren & Chriss 2000(E1，原始 PDF 403 未验证)；Obizhaeva & Wang 2013(E1)；Tóth et al. 2011 平方根律(E1) | **Counter-evidence:** 大资金 institutional 可把成本压到 bps 以下(FIM 2018, E1)，但这与 retail 无关 | **Applicable markets:** 全部 | **XAUUSD relevance:** 高——直接框定"0.1bps 上界 × 笔数"的容量天花板 | **Direct | Status: SUPPORTED_EXT**

### MECH-C5｜执行时点 × spread 动态：同一信号在不同成本 regime 成交
**Claim:** 信号预测方向 ≠ 预测"何时执行成本低"。若信号在新闻/开盘/隔夜展期/流动性枯竭时触发，恰逢 spread 展宽、深度变薄、经纪商加大滑点——同方向预测，EV 因执行时点而变号。
**Mechanism:** spread 是时变随机过程（事件风险升→做市商加宽价差+收缩深度）；触发类信号（突破、止损、挂单成交）在价格快速运动时入场=在成本最高 regime 入场。方向对但每笔多付 2–5× 价差税即吞掉 0.1bps 级 edge。
**Why it happens:** 执行成本与波动率/信息事件正相关，而绝大多数方向信号也在波动率升高时触发——信号触发概率与成本状态相关（双重选择）。
**Observable variables:** 各时段 spread 分布（均值/分位数）；信号触发时点 vs 当时 spread 的条件分布 | **Required data:** 带时间戳 bid/ask 全历史（本 feed 有报价流→可建，成本低）。
**Expected timescale:** 秒–日 | **Expected payoff:** 若触发时点 spread 条件均值 > 无条件均值，则回测净 EV 上偏 | **Execution dependency:** 高——定时/限价入场可规避坏 regime，但改变成交概率（见 MECH-C3）。
**Cost sensitivity:** 二阶敏感（成本项本身随机且与信号相关） | **Evidence:** BIS Moore-Schrimpf-Sushko 2016(E2)证实 FX 结构事件(SNB 2015)中零售通道被切断/收缩；业界普遍观测 news 时 spread 展宽(E1) | **Counter-evidence:** 若策略只在低波动时段交易（如亚盘后段）可部分规避 | **Applicable markets:** 全部 | **XAUUSD relevance:** 高——NFP/FOMC/开盘跳空/周末持仓是 CFD spread 与滑点的最坏 regime | **Proxy | Status: UNVERIFIED**（feed 报价流可验证，尚未做条件分布检验）

### MECH-C6｜Last look / requote / 拒单：负向选择的执行漏斗（MECH-05 扩展）
**Claim:** retail CFD/零售 FX 的执行链含 dealer 侧 last look：报价→你接受→dealer 在数毫秒–秒内选择成交或拒单（requote/reject/partial）。拒单非随机——当价格已对 dealer 不利时拒单率上升 ⇒ 你实际拿到的 fill 是被负向选择过的子样本。
**Mechanism:** dealer 持有订单期间价格向不利方向移动则拒绝成交（把逆向选择成本推回给客户）；客户被迫 requote 追价或在更差价位重下 ⇒ 有效执行价差 > 报价价差（"隐含加价"）。这在性质上与 MECH-C2 同源，但发生在协议层而非订单簿层。
**Why it happens:** 不对称信息/速度下 dealer 有单边期权：成交对自己有利的、拒绝不利的；FX Global Code 只要求披露与合理时间窗口，不禁止该机制。
**Observable variables:** 拒单/requote 率；拒绝后价格走向的条件分布（若拒绝后价格总朝原请求方向走=负向选择实证）；fill 延迟 | **Required data:** 真实账户订单状态机日志（accepted/rejected/requoted/partial）+ 同时刻报价流。**本 feed 无成交流 → 必须真实小单探针。**
**Expected timescale:** 每笔秒级 | **Expected payoff:** 使"可提取上界 0.1bps"再打折；高波动期折扣加深 | **Execution dependency:** 完全依赖（限价/市价/止损的拒单模式不同）。
**Cost sensitivity:** 高——波动率↑⇒拒单率↑⇒有效成本↑ | **Evidence:** GFXC FX Global Code 2024-12 更新(E3, 抓取核实存在, last-look 原则在 Execution 部分)；拒单条件选择的量化实证文献未能在线抓取(E1, 见 UNKNOWN-2) | **Counter-evidence:** 声誉约束与 Code 合规使多数正规经纪商 last look 窗口<100ms，零售低频影响或有限（未验证） | **Applicable markets:** 零售 FX/CFD、部分 ECN | **XAUUSD relevance:** 直接命中——retail XAUUSD CFD 是该机制的典型载体 | **Direct | Status: DATA_GAP**（机制有治理级证据，feed 级拒单行为不可观测、未探针）

### MECH-C7｜延迟租金与过期报价：速度不对称决定谁先死
**Claim:** 你的"信号"若建立在价格微观结构上，存在比你快 1–100ms 的参与者（HFT/LP）已把它套利完毕；对 retail 秒级信号，风险不是被抢跑，而是**你在用已过期报价成交**——broker 报价流相对真实市场的延迟使你的 fill 基准本身有偏。
**Mechanism:** 延迟套利者监控跨市场价差，在报价更新前以旧价成交（stale quote sniping）；venue 用 latency floor/speed bump 抑制之。retail 端：feed 延迟→你的回测成交时点与真实价格不同步→"在旧价位成交"等价于被系统性多付/少得半个 tick 级成本。
**Why it happens:** 信息以光速传播、人以毫秒反应；执行基础设施的延迟差 = 可货币化的信息租金（Budish-Cramton-Shim 拍卖设计论证）。
**Observable variables:** feed 报价相对参照源延迟；成交价相对你看到报价的漂移 | **Required data:** 双源报价时间戳对齐（需外部参照源，见 UNKNOWN-5）。
**Expected timescale:** 毫秒–秒 | **Expected payoff:** 对 0.1bps 级上界：哪怕 0.05bps 的系统性基准偏差都不可容忍 | **Execution dependency:** 中——timing 敏感策略致命，慢策略免疫但需证明。
**Cost sensitivity:** 中——以固定偏差形式叠加 | **Evidence:** Budish-Cramton-Shim 2015(E1)；BIS 2016(E2)证实 FX interdealer 2013 起引入 speed bump/latency floor 抑制 HFT 饱和 | **Counter-evidence:** 零售 CFD 报价由 broker 集中生成，内部一致性高，跨市场抢跑需先穿透 broker 风控（大概率无利可图） | **Applicable markets:** 电子市场普遍 | **XAUUSD relevance:** 中——真正风险是"feed 即真相"假设，若 broker 报价是其自身合成价则 MECH-C7 退化为 MECH-C2/C6 | **Proxy | Status: UNVERIFIED**

### MECH-C8｜换手复利税与隔夜/展期摩擦：edge 的乘法死亡
**Claim:** per-trade 成本对总收益是乘性的：年化成本 = 往返成本 × 年换手。给定每笔可提取上界 0.1bps，任何要求高换手的策略直接数学性死亡；叠加 XAUUSD 隔夜 swap/周末展期/三倍 swap，持仓成本与方向无关地累积。
**Mechanism:** 设每笔净 edge=+0.1bps、成本=−1.7bps ⇒ 每笔 −1.6bps；年化 = −1.6bps × N。要让年化净收益为正，需要毛 edge 极大或换手极低——而低换手与"0.1bps 级上界来自微观结构提取"天然矛盾（edge 来源决定最小持仓期）。
**Why it happens:** 成本是每笔固定税（无规模摊薄，MECH-C4），swap 是时间税；两者对"高频小 edge"策略构成乘法碾压，对"低频大 edge"策略构成加法负担——前者在本命题下无解。
**Observable variables:** 年换手率；平均持仓期；swap/展期费用表；每笔成本实际分布 | **Required data:** 已具备大部分（费用表+换手统计），缺每笔真实成本分布（见 MECH-C5/C6）。
**Expected timescale:** 周–年 | **Expected payoff:** 直接的可行性判定：换手 N 的盈亏平衡毛 edge = 1.7bps·N/收益笔数 | **Execution dependency:** 高（换手即执行次数）。
**Cost sensitivity:** 一阶敏感于 N 与 swap | **Evidence:** Novy-Marx & Velikov(E3)：月单边换手>50% 的策略几乎全部净成本后失效——换手是首要 killer | **Counter-evidence:** 极低频宏观持仓可绕开（但那时"0.1bps 上界"命题不再适用，edge 来源完全不同） | **Applicable markets:** 全部 | **XAUUSD relevance:** 高——周末持仓费+隔夜 swap 是 CFD 特有附加时间税，XAUUSD 尤甚（仓储费传导） | **Direct | Status: SUPPORTED_EXT**（换手-成本乘性关系外部铁证；swap 项为 feed 特有未验证）

---

## ② 反例 / 失败模式：edge 死于成本的量化实证

**1. Anomaly 全集净成本检验（最直接的量化死刑）**
- Novy-Marx & Velikov (NBER 20721, 2014；RFS 2016)：系统性检验大样本 anomaly，**计入交易成本后多数不再显著**；单边月换手 >50% 的策略几乎全部失效；成本削减（尤其 buy/hold spread——不主动交易出已持有的信号股）是唯一普遍有效缓解。要点：**不是"预测错"，是"换手×成本"杀死显著性**；且作者明示成本加剧 data-snooping 担忧（显著性是靠成本滤出来的假象）。E3，URL: nber.org/papers/w20721。→ 直接映射：XAUUSD retail 往返 1.7bps ≈ 权益市场 17× 的机构成本量级，若 anomaly 在 ~10bps 成本下批量死亡，则 1.7bps 下的存活窗口必然要求 edge 有数量级优势——而实测上界仅 0.1bps。

**2. 换手-显著性崩溃的具体阈值（同上文）**：>50%/月单边换手 → net spread 显著性消失。换算到日频交易=天文换手，任何"日频、每笔 0.1bps"的提取计划都落在已证死亡的参数区内。E3。

**3. 流动性改善 = 可预测性消失（成本边界的时间反证）**
- Chordia, Roll & Subrahmanyam (JFE 2008, E1)：美股 tick 十进制化后 spread 骤降，同期短周期收益可预测性（自相关、反转策略收益）同步衰减——**套利成本下降会吃掉套利机会**，反向证明"残留的可预测性≈被成本保护的残余"。推论：若某天 XAUUSD retail spread 从 1.7bps 降至 0.3bps，现存 0.1bps 级 edge 也会同步缩水——edge 与成本同源共灭。

**4. FX 技术规则的外样本死亡**
- Levich & Thomas (1993) 发现 FX 技术规则毛收益为正；Neely & Weller 系列（2003 后）在计入真实成本、外样本与数据窥探修正后**不再可获利**。E1。同类：Ito, Koibuchi, Sato & Shimizu（东京 3am 时段 FX 季节性）——找到日内收益规律，但**扣除 bid-ask 后无法盈利**（E1，URL 未能核实→见 UNKNOWN-1）。模式总结：**FX 微观结构文献里"找到规律"是常态，"扣成本后仍盈利"是罕见例外**。

**5. 零售通道被结构性收缩（feed 层失败模式）**
- BIS (Moore, Schrimpf & Sushko, QR 2016-12, E2)：SNB 弃欧郎后银行大幅收缩对零售经纪/零售聚合商的 prime brokerage 敞口，零售通道被迫转向 prime-of-prime（再叠一层 LP 成本与拒单层）；PB 提费、砍客户。→ 结构性含义：**retail feed 的成本与拒单不是常数，危机时会阶跃恶化，且恶化方向对你最不利**（你需要流动性时它最贵）。

**6. 速度军备的租金证据（谁在抽税）**
- Budish-Cramton-Shim (AER 2015, E1) 论证延迟套利租金规模之大足以驱动军备竞赛；Baron-Brogaard-Kirilenko (E1) 显示 HFT 利润的主体来自对慢参与者的逆向选择。BIS 2016 (E2) 证实 FX 平台 2013 起靠 speed bump 抑制——**当最快的参与者需要被限速时，说明"快"本身就是可货币化的税源**；你作为链上最慢端，处于税源的支付侧。

**7. 反例（edge 确实存活的少数条件——用于对照，非本命题出路）**
- Frazzini, Israel & Moskowitz（"Trading Costs", E1）：价值因子在机构级执行成本（含冲击、融资）下**净收益仍为正**——但前提：持仓数月–数年、容量大、换手低、成本 ~bps 级且可被规模摊薄。对照零售 CFD：持仓期与容量约束全不满足。→ 结论反证：**edge 存活条件与 retail 结构互斥**。

---

## ③ UNKNOWN 清单（≤5，不猜）

1. **东京 3am 类 FX 日内规律文献的确切出处与数字**（Ito et al.）——E1 记忆，无法在线核实 URL。
2. **Last look 拒单条件选择性的量化实证**（拒单后价格是否系统朝请求方向走）——仅知 GFXC 治理文本(E3)，拒单行为学术/行业量化研究未抓取到。
3. **XAUUSD retail CFD 有效价差 vs 报价价差的真实差距**（requote+滑点+拒单折算后的"隐含加价"）——需真实账户探针，本 feed 无成交流，属结构性 DATA_GAP。
4. **0.1bps/笔上界的统计显著性与其 regime 依赖**（该上界是否只在低波动/深流动性时段存在？在 MECH-C5 坏 regime 中是否归零？）——主系统内部数据问题，侦察无权访问。
5. **本 broker feed 报价相对真实 XAUUSD 市场的延迟与合成性质**（独立实时源报价 vs broker 报价对齐）——决定 MECH-C7 是实质风险还是退化为 MECH-C2/C6。

---

## ④ 来源列表

**E3（已抓取一手核实）**
- Novy-Marx & Velikov, "A Taxonomy of Anomalies and their Trading Costs", NBER WP 20721（2014，刊于 RFS 2016）— https://www.nber.org/papers/w20721 —— 换手>50%/月 anomaly 净成本失效；成本削减策略有效性。
- Global Foreign Exchange Committee (GFXC), "FX Global Code"（2021 版，**2024-12 更新**）— https://www.globalfxc.org/fx-global-code/ —— last look/执行行为治理框架存在；强制披露而非禁止。

**E2（URL 已抓取，间接相关/作者归属部分来自记忆）**
- Moore, Schrimpf & Sushko, "Downsized FX markets: causes and implications", BIS Quarterly Review 2016-12 — https://www.bis.org/publ/qtrpdf/r_qt1612e.htm —— PB 收缩、prime-of-prime、speed bump/latency floor(2013 起)、SNB 后零售通道收缩、HFT 饱和。（注意：抓取页面正文未显示作者行，作者归属来自训练知识，特此标注。）

**E1（训练知识，URL 未能在线核实——web_search 全禁用；尝试的 almgren PDF 返回 403）**
- Almgren & Chriss, "Optimal Execution of Portfolio Transactions", Journal of Risk 3(2) 2000（NYU cims PDF 403，未验证）。
- Glosten & Milgrom, "Bid, Ask and Transaction Prices in a Specialist Market with Heterogeneously Informed Traders", Econometrica 1985。
- Obizhaeva & Wang, "Optimal Trading Strategy and Supply/Demand Dynamics", J. Financial Markets 2013。
- Tóth, Lempérière, Deremble, de Lataillade, Kockelkoren & Bouchaud, "Anomalous Price Impact and the Critical Nature of Liquidity in Financial Markets"（平方根律）, 2011。
- Hautsch & Huang, "The Market Impact of a Limit Order", J. Economic Dynamics & Control 2012。
- Cont, Kukanov & Stoikov, "The Price Impact of Order Book Events", 2014。
- Budish, Cramton & Shim, "The High-Frequency Trading Arms Race", AER 2015。
- Baron, Brogaard & Kirilenko, "Risk and Return in High-Frequency Trading", 2012/2019。
- Chordia, Roll & Subrahmanyam, "Liquidity and Market Efficiency", JFE 2008。
- Levich & Thomas, "The Significance of Technical Trading-Rule Profits in the Foreign Exchange Market", JIMF 1993；Neely & Weller 外样本修正系列 2003–2011。
- Ito, Koibuchi, Sato & Shimizu, "Can you make money in the Tokyo foreign exchange market at 3 a.m.?"（RIETI/CIRJE, ~2012，具体出处未核实）。
- Frazzini, Israel & Moskowitz, "Trading Costs", SSRN 2299698（2012/2018 更新）。

**工具状态声明**：`web_search` 全程不可用（provider 禁用）→ 按纪律以"已知 URL 直抓 + 训练知识标 E1"完成；全部外部证据 ≤ E3；E1 条目均已显式标注，未伪装成在线验证。

---

**给主系统的三个可执行结论**：(1) 0.1bps 上界 vs 1.7bps 往返的缺口不是参数误差而是机制必然——唯一存活路径是极低换手或规避 taker 税的执行结构（MECH-C1/C8）；(2) 最大未量化变量是"隐含加价"（拒单/requote/滑点，MECH-C6），只需真实小单探针即可测，建议优先；(3) 任何回测显著性必须先过"换手×成本"乘法检验（N-M-V 的 buy/hold 逻辑对 CFD 即"减少不必要平仓"）。