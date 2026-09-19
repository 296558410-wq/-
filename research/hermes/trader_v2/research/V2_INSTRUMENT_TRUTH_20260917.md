# V2 INSTRUMENT TRUTH — 20260917 (P0-01)

沿真实调用链逐字段确认（修前/修后）。

| field | producer | consumer | 修前 symbol | 修后 symbol | source | timestamp | price space |
|---|---|---|---|---|---|---|---|
| `agent1.data_quality.sources.history` | agent1 | observers | **"yahoo"(硬编码, 谎)** | 实际选中源 (local_fxtm) | router | retrieval_ts | — |
| `agent1.price_basis.primary` | agent1 | context | **"GC=F@yahoo"(谎)** | `XAUUSD@{src}` | router | generated_utc | XAUUSD |
| `agent1.price_basis.primary_last` | agent1 | context→Hermes | 实际=local_fxtm XAUUSD | 同（现诚实标注 XAUUSD） | local_fxtm | 15m last_bar_ts | XAUUSD |
| `agent1.price_basis.basis_usd` | agent1 | context | `primary − sina现货` | `source_basis_usd`(同值) | local_fxtm vs sina | — | XAUUSD源间 |
| `context.market.instrument` | context | Hermes/ctx | **"GC_F"** | **"XAUUSD"** | — | — | — |
| `decision.instrument` | hermes | ledger/observer | **"GC_F"** | **"XAUUSD"** | — | ts | — |
| `agent2.instrument.instrument` | agent2 | ctx | **"GC_F"** | **"XAUUSD"** | — | snapshot_ts | — |
| `plan.entry/sl/tp` | hermes.build_plan | execution | 数值=local_fxtm XAUUSD | 同（标注 XAUUSD） | primary_last | ts | XAUUSD |
| router hist fallback (`yahoo`) | router | agent1 | **GC=F 期货（换标的!）** | **XAUUSD=X** | yahoo | last_bar_ts | XAUUSD |
| execution fill | broker (FXTM) | ledger | XAUUSD | XAUUSD | fxtm tick | fill | XAUUSD |

**根因**: 配置/标注声称 `GC=F`，实际 router 主序列 = `local_fxtm`（XAUUSD 现货）。属**语义伪装**（§3.1 禁止）。
**修后**: 全链路 instrument 一律 `XAUUSD`；`GC=F` 仅存在于 `reference_market` 与 quote 符号表（gold_comex），不再作为 signal/execution 标的。
