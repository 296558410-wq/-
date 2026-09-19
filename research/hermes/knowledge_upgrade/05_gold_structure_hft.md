# 05_GOLD_STRUCTURE_HFT — 审核后知识（OpenClaw 主控压缩 S5-GX）
> 核心问题：在黄金/OTC 结构里，高频/做市/流动性提供者到底怎么赚钱？哪些是真机制、哪些是论文故事？
> 完整 Claim 卡: 07_CORE_CLAIMS.yaml (KU-C30..C33, C10)。原始: raw/S5-GX_raw.md。

## 黄金三层市场结构（审核采纳）
1. **COMEX 期货(GC/MGC)**：CLOB、24h、价格发现主源（KU-C30，Garbade-Silber）；无 maker 回扣（双边收费）。
2. **伦敦 OTC/LBMA**：dealer 双边报价、内部化 >80%、T+2、last look；定盘=ICE 电子拍卖（KU-C33）。
3. **零售 CFD（FXTM 类）**：dealer 的"产品输出"——固定点差含 markup、B-book 客户负偏现金流=行为租金（KU-C32）。

## 真实赚钱机制 vs 论文故事（审核采纳的核心判断）
**真创造钱的机制**（在真实市场，非本 feed）：
- dealer/银行层价差+库存对冲生意（不可见，KU-C08）
- 跨市场基准/套利：basis/EFP 收敛（KU-C22/C30）+ 跨层 stale-quote 打单 GC↔OTC（KU-C31）
- 零售层行为租金（B-book，KU-C32，与策略研究无关）
- 基准拍卖窗事件流（KU-C33，部分可研究）

**论文故事类（结构上在此市场无载体）**：
- 队列优先/回扣套利（KU-C07/C15 降权）——CME 金属无 maker 回扣；OTC 无队列
- 簿内延迟套利——黄金链上没有集中簿内的速度游戏，只有跨层速度差

## 黄金特有反例/事件（审核采纳）
- 2020-03：期现脱锚（COMEX 溢价峰值 ~US$60-80/oz 待核）+ CME 紧急交割规则 → basis 收敛套利"恰恰在危机时失效"。
- 2015-01-15 SNB：瑞郎脱钩杀死 MM/零售经纪（Alpari UK 破产）→ 做市尾部一票清零。
- 2012-2014 LBMA 操纵史（Barclays/FCA £26M，E2 核验）→ 基准脆弱性持续。

## 零售 CFD feed 结构性不可观察清单（本层最硬输出，14 项失真）
不能观察：真实 bid-ask 动态/深度/簿失衡/队列/成交量/成交流/signed flow/T&S/有效价差/Roll/Kyle λ/Amihud/VPIN/dealer 存货/B-book 比例/成交概率/last look 拒绝/basis/GOFO。
能观察（Proxy）：波动聚类/跳跃/GARCH、时区时段结构、fix 与宏观窗事件研究、报价停顿/缺口/重复报价/点差冻结（dealer 行为代理）、已知事件响应延迟。
（完整表见 raw/S5-GX_raw.md ③；核心形式化 = KU-C10。）

## UNKNOWN
FXTM/DUKA feed 生成管线（时间戳=dealer 事件时间？单一 LP 合成？插值？）；GC↔伦敦领先滞后近年是否仍显著；
2020-03 峰值精确数值；GC 日均量与 OI 现值。
