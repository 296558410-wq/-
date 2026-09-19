# DATA_HEALTH_REPORT — 数据健康门（Data Health Gate）

- 时间: 2026-09-14T11:14:52.758574+00:00  |  模式: router ENABLED（仅用于产出报告；生产默认 OFF）

```text
Agent1
XAUUSD 5m   FRESH
XAUUSD 15m  FRESH
XAUUSD 60m  FRESH
XAUUSD 4h   FRESH
XAUUSD 1d   STALE_BUT_VALID
technical_status = READY

Agent2
DXY              FRESH
UST10Y           FRESH
VIX              FRESH
DXY(macro)       MISSING
UST10Y(macro)    MISSING
RealRate(TIP)    MISSING
COT(Gold)        MISSING
BLS macro        MISSING
CN Gold ETF 518880 MISSING
CN Gold ETF 159934 MISSING
macro_status = PARTIAL
```

- stale: []
- missing: ['macro:yahoo_kv:DX-Y.NYB', 'macro:yahoo_kv:^TNX', 'macro:yahoo_kv:TIP', 'macro:cot:gold', 'macro:bls:macro', 'macro:emflow:518880', 'macro:emflow:159934']
- sources_down(cooldown): {}

状态语义: FRESH / STALE_BUT_VALID（陈旧但曾在有效期内，低频宏观仍可用，带 observed_at+age）/ MISSING / INVALID / SOURCE_DOWN。