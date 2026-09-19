# V2 INSTRUMENT CONTRACT (P0-01)

## 定义（强制）
```
execution_instrument = XAUUSD
signal_instrument    = XAUUSD
reference_market     = GC=F   (可选; 仅交叉校验; 须独立 PIT contract)
```

## 一致点（全部必须为 XAUUSD）
`instrument_marking.instrument`, `market_data.primary_instrument`, `context.market.instrument`,
`decision.instrument`, `agent2.instrument.instrument`, `plan` 价格, ledger `symbol`, execution symbol。

## 禁止（语义伪装）
- `instrument=GC=F` 而 `source=local_fxtm`（GC 标签 + XAUUSD 数据）
- `symbol=GC=F` 而实际数据 XAUUSD
- router fallback 把 XAUUSD 请求换成 GC=F 期货

## GC=F 允许的位置
仅 `market_data.reference_instrument` / `symbols.gold_comex`（quote 参考）与 `reference_market` 元数据。
若未来以 GC=F 作 signal，必须显式取到 PIT GC=F 且单独标注，不得与 XAUUSD 混用。

## 校验
`tests/test_instrument_contract.py`（config + 静态契约 + router fallback + price_space 常量）。
