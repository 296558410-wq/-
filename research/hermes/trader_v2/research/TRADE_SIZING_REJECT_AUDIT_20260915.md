# 两笔 TRADE 的 sizing 拒绝审计 — V2 (2026-09-15, 只读)

## 结论（先说）
两笔 TRADE 被拒 = **sizing 取整 bug 的症状，不是策略问题**；**已于 2026-09-12 修复**（sizing v2），
当前修复版按新口径**不会**再因此拒单。两笔均为 **PAPER 模式**，**未产生任何 broker 订单**。

## 事件
run `V2-PAPER-20260911-133224-a17b`（2026-09-11, **PAPER**），61 决策，其中 2 笔 TRADE：

| 决策 | 时间(UTC) | 机会 | 方向 | entry | SL | TP | dist | conf | exp_R |
|---|---|---|---|---|---|---|---|---|---|
| DEC-ctx_feb7a04dfcd8 | 2026-09-11T13:52:52 | opp_fbo_short | SHORT | 4434.90 | 4452.64 | 4406.52 | 17.74 | 0.55 | 1.6 |
| DEC-ctx_90c83bcaca11 | 2026-09-11T14:07:53 | opp_fbo_short | SHORT | 4432.10 | 4449.83 | 4403.73 | 17.73 | 0.55 | 1.6 |

两笔 plan：`risk_per_trade_pct=1.0`，thesis="上破失败(影线越界未收)=流动性扫损"，counter_thesis="真突破前的最后一次回踩"。

## 账本证据链（a17b ledger）
```
DECISION(TRADE)  → EXECUTION_REQUEST(REQUESTED) → EXECUTION_RESPONSE(REJECTED, retcode=RISK_LIMIT,
   message="position_size 0.06 > max_lot 0.05") → ORDER_REJECTED(同 retcode/message)
```
两笔完全同因；`execution_mode=PAPER`；无 position_id / 无 broker order。

## 根因（算一遍）
- 合约 100 oz；SL 距 17.74；每 0.01 手风险 = 17.74 × 100 × 0.01 = **$17.74**。
- 风险预算 = equity × 1% = 10000 × 1% = **$100**。
- 期望手数 = 100 / (17.74×100) = **0.0564 手**。
- 旧口径 **round-nearest**：0.0564 → **0.06** → 超过 `max_lot=0.05`（**硬拒，不 clamp**）→ `RISK_LIMIT`。
- 即 **"死区"**：SL 距 ≲ 19–20pt 时算出的 0.056–0.059 会被四舍五入到 0.06 → 系统性拒单。

## 修复确认（2026-09-12 sizing v2）
- 现行口径：`qty = max(floor_to_step(risk_lots), min_lot)`，`max_lot` 仍硬拒、不 clamp。
- 同样两笔在现行口径：`floor_to_step(0.0564)=0.05 ≤ 0.05` → **ACCEPT**；实际风险 = 0.05 × 17.74 × 100 = **$88.7 ≤ $100**（在预算内）。
- 回归：`tests/test_sizing_floor.py` **34/34 PASS**（含 floor/min_lot/max_lot 硬拒/不许 clamp/risk≤equity）。

## 余留（诚实）
- 这 2 笔**从未真正成交** → 其"假设结果"不可知，**不构成任何 forward 证据**。
- 若想看这类 setup 的真实结果，需等修复版在真实数据下再次给出同类 TRADE 并成交。
