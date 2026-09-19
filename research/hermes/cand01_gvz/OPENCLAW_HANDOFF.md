# OPENCLAW HANDOFF — CAND-01 GVZ（2026-09-06）

CURRENT_BELIEF: "GVZ 增量 vol 信息 = UNPROVEN。主体 = 平滑本地 vol 的表示(corr 0.50/0.65); 控平滑后残余 OOS ΔR² +0.07..+0.12 @5-20d(小, 机制不明); 方向 REJECTED; 经济 LEVEL 1-2(仅 R1 附加输入, AUC +0.029)"
EVIDENCE: "RESULTS.json + RESULTS_SUPP.json + 各 audit yaml（混淆测试: 60-75% 增益为平滑表示; R1 AUC A0.736/A2 0.769/B 0.797; regime UNKNOWN; 月频方向 null）"
STRONGEST_POSITIVE: "残余增量跨 1-20d 一致为正(控全本地信息后 +0.017..+0.122 ΔR² 谱)——GVZ 非纯冗余, 但期权特有性未建立"
STRONGEST_NEGATIVE: "方向 ≈ 0; 增益主体(60-75%)是本地平滑 vol 即可复制的表示; regime 不可判"
STRONGEST_COUNTER_EVIDENCE: "corr(GVZ, rv63)=0.65 + A2(零期权数据)已达 R1 AUC 0.769 → '期权信息'的大部分是已实现波动的回声"
KILLED_HYPOTHESES: ["GVZ 方向信息（REJECTED）", "GVZ 为纯冗余（证伪: 残余>0, 但弱）——半杀", "GVZ 作为主要 R1 风险态源（降级: 附加输入）"]
SURVIVING_HYPOTHESES: ["GVZ 携带小量非平滑残余 vol 信息(机制不明; UNPROVEN)", "曲面/skew/事件维度含 GVZ 不可见信息(DATA_GAP)"]
DATA_GAPS: "XAUUSD 专属 IV / 曲面 / skew / term / 日内 IV / 事件邻近重定价(D5/D7)"
NEXT_HIGHEST_VALUE_RESEARCH: "机会/风险分离结构检验(合并队列); D5/D7 解锁评估; GVZ 单点不再投入"
WHY: "GVZ 层信息增益已耗尽(主体冗余+小残余); 下一层信息在曲面/事件维度"
WHAT_NOT_TO_RESEARCH: "GVZ 单点任何新变换; GVZ 方向; VRP 收割(无通道); 期权数据购买"
CURRENT_RESEARCH_LEVEL: "正式检验完成(UNPROVEN); RQ-07 不适用(无交易候选)"
REVIEW_REQUEST: ["1. 接受 CAND-01 UNPROVEN 判定?", "2. GVZ 是否正式登记为 R1 附加风险态候选(仅当 R1 重启时评估)?", "3. D5 曲面 / D7 日历解锁评估是否启动?", "4. SI-CAND01-001 outcome 更新为 UNPROVEN 确认"]
