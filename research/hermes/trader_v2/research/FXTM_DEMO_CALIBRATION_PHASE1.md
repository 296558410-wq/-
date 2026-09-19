# FXTM Demo Execution Calibration — Phase 1 报告（只读行情同步，不下单）

> 日期: 2026-09-11 · 目标: 同步 FXTM Demo 实际报价(bid/ask/spread)，为"Paper 模型 vs Demo 真实"校准提供基线。
> **只读；0 订单；未改 SL/TP；V1 终端零影响。**

## 方法
- 采集器 `execution/fxtm_demo_calibration.py`：附加到**测试实例**（数据目录含 `fxtm_demo_01`），逐秒读取 `XAUUSD` tick。
- 安全：
  - **只附加不登录**（终端已登录）；`initialize(path=<测试exe>, portable=True)`；若 data_path 不含 `fxtm_demo_01` → **拒绝**。
  - 模块自证**无写接口**（`assert_no_write_api()` 扫描实际调用模式，结果为空）。
  - 不触碰 V1 终端。

## 结果（XAUUSD，30 样本 / 30s）
| 指标 | 值 |
|---|---|
| 样本 | 30/30 成功 |
| spread（价） | min 0.13 / max 0.14 / **mean 0.1353** |
| spread（bps） | min 0.297 / max 0.32 / **mean 0.3093** |
| 首报价 | bid 4375.47 / ask 4375.60 |
| 末报价 | bid 4376.25 / ask 4376.38 |
| 账户 | DEMO=true，数据目录 `C:\AIQuant\mt5_instances\fxtm_demo_01` |
| 订单 | **0** |

## 校准含义（初步）
- Demo 实测 spread ≈ **0.31 bps**，与 Paper 模型默认 `spread_bps_typical=0.35` **同量级**（Paper 略保守）。
- **延迟说明**：本阶段 `latency_ms≈0` 是**本地 API 调用耗时**（IPC 读取缓存 tick），**非** broker 往返延迟；真实 RTT 需"下单→回报"才可以测（属后续"下单校准"阶段，需另行授权）。
- 行情时间戳来自终端 tick.time；PIT 纪律保持（仅记录当时收到值）。

## 产出
- `execution/fxtm_demo_calibration.py`（只读采集器）
- `tests/test_demo_calibration_readonly.py`（5/5 PASS）
- `state/demo_calibration/quotes_20260911T125221Z.jsonl` + `summary_*.json`
- `logs/test_demo_calibration_readonly.log`

## 状态
- Phase 1 ✅（只读行情同步完成）/ 未下单 / V1 零影响。
- 下一步（需你授权）：Phase 2 = 用**一个最小 Demo 市价单**测真实 fill/slippage/RTT/拒单，校准 Paper 模型（仍仅 Demo、仅最小单、完整记录）。
