# 01_L1_MICROSTRUCTURE — 审核后知识（OpenClaw 主控压缩 S1-MS + S6-AD）
> 核心问题："价格为什么在某一瞬间移动？" — 参与者行为→订单流→流动性→冲击→持续/反转→可观察。
> 完整 Claim 卡: 07_CORE_CLAIMS.yaml (KU-C01..C10)。原始: raw/S1-MS_raw.md, raw/S6-AD_raw.md。

## 机制链（何者在何时移动价格）
1. **主动成交（aggressor）** 是即时价格变化的触发器（KU-C01）——但注意反例：大量 mid 变动发生在无成交时（撤单/挂单移动）。成交不可见 ⇒ 本 feed 只能 Proxy。
2. **做市商/流动性提供者** 是价格的"看门人"：spread=逆向选择+库存+处理成本（KU-C02）；冲击=永久(信息)+临时(库存)成分（KU-C04）。
3. **订单簿供需失衡（OFI）** 短区间线性驱动价格（KU-C03）——同步性强于预测性，且需完整 LOB。
4. **流动性真空** 是极端移动的机制（KU-C06）：零售 feed 上唯一可见指纹 = spread 爆炸 + bid/ask 断层 + 停顿/缺口。
5. **库存压力/dealer 报价管理** 在电子化后弱化、在 B-book 零售结构中被对冲隐藏（KU-C08 反例侧）。

## 被纠正/降级的常见叙事
- **VPIN/流毒性作为预警器**：Andersen-Bondarenko 反证有力（KU-C05）→ 已从"工具"降为"有争议概念"。
- **队列/竞速/延迟套利**：equities 集中式 LOB 机制；在 OTC 黄金/零售报价无载体（KU-C07）→ S5-GX 建议降权 MECH-15。
- **做市稳定赚钱**：实证是极端异质性 + 厚尾 + 尾部一次清零（KU-C08/C09）→ "MM 恒赚"=叙事偏差。

## XAUUSD feed 可观测性判定（S1-MS 全局前提，审核通过）
FXTM 零售 feed = B-book 两档报价流（无成交/无 volume/无 LOB/无 aggressor）；spread 含零售加价=政策变量。
DUKA ≈ ECN 报价但仍无成交/深度。
⇒ 依赖 trade/L2/queue 的机制**不可直接观测**；可做的是 quote-path 统计（波动聚类/跳跃/时段/spread 断层/fix 与新闻窗）。
审核备注：S5-GX MECH-19 将这一点形式化为"结构性失效=DATA_GAP 非暂时缺数据"（KU-C10）——本层最硬结论。

## 留给本地的可测问题（观察级，非策略）
- U1/U5: 纯报价流能否构造可靠的 aggressor/OFI 代理（quote-event imbalance，KU-C34）→ 可本地自测。
- U3: FXTM/DUKA 报价中 COMEX→现货领先滞后是否可捕捉（需 GC 参照，DATA GAP）。
- U4: 流动性真空的事前指纹除 spread 外还有无其他（UNKNOWN）。
