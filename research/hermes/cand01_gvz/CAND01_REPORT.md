# CAND-01 GVZ 信息含量正式检验报告（中文, 2026-09-06, 预注册 c23b046）

## 0. 任务
HERMES-13 CAND-01 正式检验：公开黄金期权波动代理 GVZ 是否在已确认的 activity→vol 信息层之外,
含 XAUUSD 未来已实现波动的增量信息。只答信息含量; 阳性 ≠ alpha。结论:**UNPROVEN**。

## 1. 链条审计结论（逐层独立）
Claim(黄金期权 IV 有非摩擦信息) ← E3 级(文献); Evidence(XAUUSD 直接证据) ← 本检验首次;
Mechanism ← 未建立; Asset/Gold(XAUUSD spot 适用) ← 仅经 GLD options 代理; Proxy(GVZ) ← 合法但有限;
Observability(XAUUSD IV 直接观测) ← 无(缺失); Testability ← 可测(已测); 下游(Economic value) ← LEVEL 1-2。

## 2. 数据
GVZCLS(FRED, 2008-2026) × XAUUSD 日 RV 面板(W11, DUKA 1-min, 2023-01..2026-08, 573 合并日)。
决策 22:00 UTC d; 目标 = 未来 5/10/20 交易日 log RV。GVZ proxy 纪律全程执行。

## 3. 主结果
- 原始(B vs 点滞后基线 A): OOS ΔR² +0.24/+0.29/+0.32 (h5/10/20), DM-HAC t≈2.7-2.9 —— 看似强。
- **混淆测试(A2 = A + 本地平滑 RV21/63)**: corr(GVZ, rv21)=0.50, corr(GVZ, rv63)=0.65;
  原始增益 60-75% 由平滑表示解释; 残余 OOS ΔR² = **+0.074/+0.100/+0.122** —— 存在但中等偏小。
- 与早前 1-2d 结果(+0.017/+0.062)方向一致 → 跨 1-20d 一致的正残余。

## 4. 审计
regime: 样本不足 UNKNOWN。方向(月频, n=35): GVZ −0.07 (null), VRP +0.28 无推断力 → REJECTED。
R1 风险态(AUC, 识别 5d 高波动态): A 0.736 → A2(本地平滑) 0.769 → B 0.797 —— GVZ 边际 +0.029,
本地平滑 vol 已提供大部分价值 → LEVEL 2 轻微支持。

## 5. Kill 汇总
KILL-07(方向空) 命中; KILL-02/06(控制后/冗余) 部分命中(大幅缩水但残余>0); KILL-04 UNKNOWN;
其余未命中。未被杀死, 亦未确证。

## 6. 判定
**最终分类: UNPROVEN。** GVZ level 主体 = 平滑的黄金波动状态表示(corr 0.5-0.65, 非期权特有);
残余增量(+0.07..+0.12 ΔR² OOS @5-20d)真实但小、机制不明、重叠窗推断未全量硬化。方向 = REJECTED。
经济层级 = LEVEL 1-2(统计 + 轻度风险态); GVZ 只配作 R1 的**附加**风险态输入(AUC +0.029), 不是主输入,
更不是 alpha。曲面/skew/事件邻近重定价维度 = DATA_GAP(不在 GVZ 观测面; 不购买数据)。

## 7. 地图影响
Gold Options 任务结论细化: "GVZ 增量" 现可解释为主体平滑表示 + 小残余; 单点日频 GVZ 方向性研究
关闭; 剩余开放 = 曲面/事件维度(DATA_GAP)与 R1 附加输入评估。GVZ≠XAUUSD IV 纪律维持。

## 8. 纪律
预注册冻结先行(c23b046)并 commit; manifest C01-C10b PASS; 无新数据购买/无优化/无策略/无 frozen
registry 修改; 确定性代码 run_cand01.py + run_cand01_supp.py → RESULTS.json/SUPP。
