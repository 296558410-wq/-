# V2 BROKER PRECHECK REPORT — 20260917 (P1-C)

## 实测规格（MT5 symbol_info, V2 独立实例 fxtm_demo_01, 只读）
见 `research/V2_BROKER_SPEC_20260917.md`。关键实测值：
digits=2, point=0.01, tick_size=0.01, contract_size=100.0, volume_min=0.01, volume_step=0.01,
volume_max=100.0, **stops_level=0**, freeze_level=0, filling_mode=1, execution_mode=2, trade_mode=4(FULL)。
（config 假设 max_lot=0.05 属本地风险上限，broker 实际 volume_max=100；两者独立。）

## 订单预校验（发送前 fail-closed）
`execution/broker_validate.precheck_order`：
- 方向边: SELL: SL>entry, TP<entry ; BUY: SL<entry, TP>entry
- 相对市价: 有效一侧；`distance >= stops_level`
- tick/digits（默认 0.01）
任一不满足 → **PRECHECK_REJECT（不下单）**。

## 接入
`BrokerDemoExecutor.open()` 在 `place_market_order` 之前调用预校验（用实测 spec + 实时 tick）。
预校验失败 → 本地拒绝（`PRECHECK_REJECT`），**绝不把无效价送 broker** → 杜绝历史 `BROKER_REJECT_10016`。

## 测试
`tests/test_broker_validate.py` 9/9（valid BUY/SELL、错侧、过近、市价错侧、off-tick、缺价）。

## 说明
- 本阶段 **未发送任何订单**（`BROKER_ORDER_SENT=FALSE`）；broker spec probe 只读。
- 未做 broker dry-run 真实发单（§21 允许“最小隔离测试”，但为安全本阶段仅做本地纯校验 + 只读实测；真实 dry-run 建议在 Shadow 阶段以独立小账户进行）。
