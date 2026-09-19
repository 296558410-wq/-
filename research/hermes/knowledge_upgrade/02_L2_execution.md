# 02_L2_EXECUTION — 审核后知识（OpenClaw 主控压缩 S2-EX）
> 核心命题：预测正确≠赚钱。signal→execution→fill→cost→realized P&L 每一层都能消灭 alpha。
> 完整 Claim 卡: 07_CORE_CLAIMS.yaml (KU-C11..C17)。原始: raw/S2-EX_raw.md。

## 为什么理论 edge 在真实成本下变负 EV（机制层答案）
1. **mid 回测幻觉/成本地板**（KU-C11）：taker 每笔往返付全额价差税，EV 偏移=纯平移，与预测方向无关。
   本地算术：0.1bps 上界 − 1.7bps 往返 < 0。证据：Novy-Marx-Velikov NBER w20721（E3 已核验）。
2. **成交条件性逆向选择/赢家诅咒**（KU-C12）：被成交本身是坏消息——对手只在将不利时成交。可实现 alpha < 回测 alpha。
3. **maker 侧 pick-off**（KU-C13）：省价差税但承担逆向选择；无队列管理能力=新税 > 省下的税。
4. **规模-成本三角**（KU-C14）：冲击∝√Q ⇒ retail 小单吃不到规模经济，固定税无法摊薄。
5. **执行时点×spread 状态双重选择**（KU-C15）：信号常在成本最高 regime 触发 → 回测净 EV 上偏。
6. **last look/requote/拒单漏斗**（KU-C16）：fill 是被负向选择过的子样本；隐含加价 > 报价价差。
7. **换手复利税**（KU-C17）：年化成本=往返×换手；0.1bps 上界下高换手数学性死亡。

## 成本数量级锚点（审核采纳）
- 学术异象：Novy-Marx-Velikov——换手 >50%/月 的 anomaly 净成本后失效；成本削减策略（buy/hold spread）唯一高效。
- 机构级：Frazzini-Israel-Moskowitz——价值因子机构级成本下净正（持仓数月-数年）→ 反证：edge 存活条件与 retail 结构互斥。
- FX 结构：BIS 2016（E2 核验）——SNB 后 PB 收缩、prime-of-prime 再加一层成本、speed bump 证明"快"=可货币化税源。
- 速度租金：Budish-Cramton-Shim（E1）+ Baron et al.（E1）——HFT 利润主体=对慢参与者逆向选择；retail 处于税源支付侧。

## 审核结论（OpenClaw）
- 0.1bps vs 1.7bps 缺口**不是参数误差而是机制必然**。唯一存活路径 = 极低换手 或 规避 taker 税的执行结构。
- 最大未量化变量 = **隐含加价**（拒单/requote/滑点，KU-C16）——只需真实小单探针即可测，建议优先（免费 demo 到位后）。
- 任何回测显著性必须先过"换手×成本"乘法检验。
- 反例对照：edge 确实存活的少数条件（低频/大容量/机构成本）与 retail 结构互斥——不是本命题的出路。

## UNKNOWN（不猜）
拒单条件选择性的量化实证、XAUUSD 隐含加价真实值、0.1bps 上界的 regime 依赖、feed 相对真实市场的延迟/合成性质。
