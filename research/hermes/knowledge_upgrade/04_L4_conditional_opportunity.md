# 04_L4_CONDITIONAL_OPPORTUNITY — 审核后知识（OpenClaw 主控压缩 S4-CO）
> 本轮最重要升级：从"预测下一根 K 线"到"什么市场状态下交易机会的概率/收益分布突然有利"。
> Net EV = P(win)×AvgWin − P(loss)×AvgLoss − Cost。完整 Claim 卡: 07_CORE_CLAIMS.yaml (KU-C25..C29)。
> 原始: raw/S4-CO_raw.md。

## 什么状态变量真正改变收益分布（审核采纳，按稳健性排序）
1. **波动状态**（KU-C25，DIRECT）：可识别、稳健、条件化收益规模（非方向）。高波动态→条件波动↑尾部↑。
   价值=仓位/频率/持期的条件乘子。**方向 regime 事前不可识别 = 事后命名陷阱**（用全样本估计/平滑概率=前视）。
2. **日内时段状态**（KU-C26，DIRECT）：确定性节律、零识别延迟、零过拟合维度。时段×spread = 免费执行层条件信息。
3. **计划内宏观事件**（KU-C27，DIRECT）：公告日溢价存在（Savor-Wilson）但执行依赖致命；黄金对美元实际利率/通胀高敏感。
4. **流动性状态**（KU-C28，PROXY）：自指陷阱——机会(波动)与成本同时上升是结构性的；需 vol-adjusted 测度。
5. **VRP/vol-of-vol**（equity 已证 SUPPORTED_EXT；gold UNKNOWN——GVZ 短、符号不一致）。
6. **崩盘/偏度条件态**（KU-C24/C20 交叉）：momentum 崩溃态可部分预测（DM 择时），gold 避险=同期效应不可滞后交易。

## 反例/失败模式（最大陷阱清单）
1. **事后状态命名=前视偏差**（最大）：只允许 causal(filtered) 状态估计，验证必须滚动前推。
2. **滞后即失效**：gold 避险同期性——识别发生在条件优势消失后。
3. **状态激活时成本同涨**：Cost 必须建成状态内条件分布而非无条件常数。
4. **条件化=变相数据挖掘**：时段×波动×事件笛卡尔积 10^4-10^5 试验 → 需 t>3/deflated Sharpe（KU-C29）。
5. **状态切换滞后**：RV(20d) 对 vol 突变反应以周计 → 假切换双向磨损。
6. **方向子型过度细分**：2020-03 "risk-off→买金"混淆两种互斥子型（一般避险 vs 保证金挤兑）。

## 审核结论（与主系统自证收敛）
S4-CO 主结论与本地 Phase 1-9A 结论完全一致：activity→vol 稳健非方向；无条件方向不存在；
"形态条件化方向"证据最弱、过拟合最危险。**对 XAUUSD 最可落地 = 状态内执行与仓位调节（C1×C2×C3），
而非状态内方向预测** —— 即本地 drift 环 + R1 形态条件化方向的知识基础。

## 对 drift 环的输入（本层对 money_hunter 的直接贡献）
S4-CO 的条件变量体系为 microstructure_drift 环提供"哪些状态漂移有经济意义"的判据：
波动状态漂移=PROBABILITY/PAYOFF 通道；时段=OPP_FREQ；公告=执行层；流动性=COST(自指，须 vol-adjusted)。
与 ECONOMIC_RELEVANCE_RULES.md 的 5 通道映射一致，无需修改。
