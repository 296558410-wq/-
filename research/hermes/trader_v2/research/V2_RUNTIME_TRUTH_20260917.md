# V2 RUNTIME TRUTH — 20260917

- **目的**: 在修复前，以**实际运行代码 + 运行时证据**确立 V2 的真实数据/执行链路（配置文件/注释/README 与实际不同者，以代码与运行证据为准，并记录 drift）。
- **基线**: audit commit `42e8b5843b74c681f1259a17e23bdee05b5c6c79`; BASE_COMMIT `7fe4828eab194ec3fc6c32351662b6b40dfc7176`; branch `fix/v2-full-system-repair-20260917`。
- **只读**: 本文只记录事实，不改代码。

## 0. 调用链（实际）

```
Windows Task \OpenClaw\hermes-v2-cycle  (IgnoreNew, ExecTimeLimit PT15M, StartWhenAvailable 缺省=false)
  └─ env: V2_DATA_ROUTER_ENABLED=true (setdefault)  →  C:\AIQuant\.venv\Scripts\python.exe runtime/v2_scheduled_cycle.py
      └─ (_gate) trading_hours.status() → armed?  → 子进程 shadow_run.py cycle --minutes 1440 --new
          └─ shadow_run.run_cycle:
             Agent1.build → market_data.snapshot_history("GC=F") → [router ON] data_sources.history("GC=F",tf)
             Agent2.build → sources/router.macro(...)
             hermes.run → context.build_context(冻结) → discovery.discover → gate → build_plan(price=ctx.market.primary_last)
             [price_space opt] → ADP.process(execution_plan?) → executor.open()
             reconcile_broker_closes → replay(ledger) → _account_match → run_state/metrics
```

## 1. 逐项事实

| 问题 | 事实（证据） |
|---|---|
| **实际 instrument** | **声明 `GC_F`**（`v2_config.market_data.primary_instrument="GC=F"`, `instrument_marking.instrument="GC_F"`, decision `"instrument":"GC_F"`, manifest `market_data_source="yahoo GC=F + …"`）。**运行实际 = `local_fxtm` XAUUSD 现货**（router 历史主源）。证据：`data_cache/router_cache.json` → `hist:GC=F:15m {source:"local_fxtm", n:706}`；`data_cache/router_audit.jsonl` history 行 **755/781 selected_source=local_fxtm，0 yahoo**。 |
| **主价格来源** | `ctx.market.primary_last = a1.price_basis.primary_last = features 15m last_close`，其 bars 来自 **`data_sources/local_bars.build_bars`**（`C:\AIQuant\data\live_fxtm\ticks_*.parquet` 的 XAUUSD bid/ask mid）。`local_bars.py:47` 硬编码 `"symbol":"XAUUSD"`。 |
| **Agent1 bars** | 5m/15m/60m/4h/1d 全经 router；`registry.HISTORY_SOURCES` = **local_fxtm(primary) → yahoo(secondary)**（`registry.py:6-12`）。`router.history` 对 `local_fxtm` **不传 symbol**（`router.py:55-56`）→ 即使调用方请求 `GC=F` 也返回 XAUUSD。 |
| **Agent2 数据** | `router.macro`：`yahoo_kv:DX-Y.NYB`(DXY)、`yahoo_kv:^TNX`(UST10Y)、`yahoo_kv:^VIX`、CFTC COT、BLS、news(wallstcn/cnbc)。`gold_macro_state` 仅由 DXY/UST10Y/VIX change_pct + 中国 ETF 流决定（`agent2.py:220-247`）。TIP/BLS/COT/WGC/央行/政策利率 不进 state。 |
| **Hermes 字段** | 用 `ctx.market.primary_last`（local XAUUSD last_close）、`a1.timeframes.*`（结构/突破/ATR/range）、`a2.gold_macro_state`、`a2.macro.usd/rates`、`a2.geopolitics.events`、`a2.narrative_vs_flow`。 |
| **execution 价格** | `plan.entry/stop_loss/take_profit`（源自 `= price = primary_last = local XAUUSD`）→ 经 `price_space`（可选）→ `executor.open(side, mid, sl, tp)`。Broker 以 **XAUUSD 现货 tick** 市价成交（`fxtm_demo_adapter.place_market_order`）。 |
| **basis 到底是什么** | Agent1: `price_basis.basis_usd = primary_last − gold_spot(sina)` = **本地 XAUUSD tick 现货 − sina XAUUSD 现货**（两个**现货源**之差，非 COMEX/现货基差）。price_space 用 `basis = spot − gc`（符号相反）。 |
| **单位** | USD/oz，2 位小数（price_dp=2, tick 0.01），contract 100oz，min_lot 0.01。 |
| **timestamp 含义** | `generated_utc`=快照写入时刻；`quotes.*.retrieval_ts`=取回时刻；`quotes.*.data_ts`=行情自身时刻（sina 为 "HH:MM:SS" 文本）；`*_bar.last_bar_ts`=bar 起始 epoch；`decision.ts`=Hermes 决策写出时刻；`basis_ts/basis_age`=价格空间腿时刻/年龄。 |
| **是否共享 V1 数据** | **是**：`local_bars` 读取 `C:\AIQuant\data\live_fxtm`（V1 采集器 `hermes-tick-collect` 写）。 |
| **隐式 fallback** | router：源失败 → cache/last_valid（`router.py:82-97,151-172`）；`yahoo` 为 history secondary；agent2 `_safe` 哨兵；news `default=[]`。 |
| **旧 cache** | `data_cache/router_cache.json`（单槽 LWW，含陈旧 hist 项，如 `hist:XAUUSD:15m bar 1789600500`）；`data_cache/router_audit.jsonl`（41MB）。 |
| **env 强制 override** | `V2_DATA_ROUTER_ENABLED=true`（scheduler setdefault），且 `config/data_router.enabled=true`。 |

## 2. 关键 drift（代码/运行 vs 文档/配置）

1. **声明 GC=F，运行 XAUUSD 现货**（P0-01）。
2. **Router 文档称“默认 OFF/走 legacy”，运行常开**（P0-02）。
3. `agent1.data_quality.sources.history` 硬编码 `"yahoo"`（实为 local_fxtm）。
4. `research/REGRESSION_REPORT.md`/`source_connectivity_matrix.py` 的“本地 tick 为主源/默认 false”表述与 config 冲突。
5. Dashboard README “PAPER/不触网” vs 实际 BROKER_DEMO + live MT5 探测。

## 3. 对既有“价格空间修复”的重新定性（P0-01）

- 旧命名 `GC signal → XAUUSD execution` **与实际运行路径不符**：运行时 signal 与 execution **同为 XAUUSD 现货**（来源不同：本地采集 vs broker/sina）。
- 因此 `price_space` 的 `basis` 实为**现货源间价差**；其“换算”效果 = 把本地采集价对齐到 sina/broker 现货。机制自洽、经验上有效，但**命名/语义需按 §5/§6 重定义**。
- 处置（后续 commit）：统一 `instrument=XAUUSD`；若保留 `GC_F` 仅作 `reference_market` 且**必须有 PIT GC 才可用**，否则不得出现。

## 4. 结论（修复靶点）

- P0-01 instrument/price-space 语义（§5/§6）
- P0-02 router 唯一数据入口 + 消除隐式 override（§7）
- P0-03 Agent2 fail-closed（§8）
- P0-04 freshness 基于 data_ts + health 进入决策链（§9/§10）
- P0-05 cache as-of/PIT（§11）
- P1 宏观完整性/发布时刻/news 失败可见（§15–17）
- 执行/Broker/Risk 使用 execution space（§21–23）、replay 输入快照（§24）、dashboard（§26–27）、LLM 依赖审计（§28）、failure injection（§29）、shadow run（§34–35）、二次审计（§36）
