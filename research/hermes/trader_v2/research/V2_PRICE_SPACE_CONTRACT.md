# V2 PRICE SPACE CONTRACT (P0-01 重定义)

## 空间定义
```
signal_price_space    = XAUUSD
execution_price_space = XAUUSD
reference_price_space = GC=F  (仅交叉校验; 不参与 signal/execution)
```

## 转换
- 同 instrument → **identity**：`execution_price = signal_price`，`basis = 0`。
- 仅当 signal 来源与 execution 参考来源为**同标的、不同源**，且满足 `PIT & fresh & validated` 时，允许：
  ```
  source_basis_usd = exec_reference_price - signal_price      # 命名: source_basis, 非 GC_SPOT_BASIS
  execution_price  = signal_price + source_basis_usd
  ```
- 必须记录：`signal_source, execution_source, signal_ts, execution_reference_ts, basis_ts, basis_age, basis_source, basis_source_hash`。

## Fail-closed
`basis missing / stale / abnormal / timestamp invalid` → **TRADE FORBIDDEN**（仅 WAIT/BLOCK）。

## 现状
`execution/price_space.py` 已重定义（`price_space/2.0.0-source-basis`；`SIGNAL=EXECUTION=XAUUSD`，`REFERENCE=GC=F`），
且 `config/price_space.json enabled=false`（未认证前不启用；启用需重认证）。禁止重新打开旧 `GC→spot` 实现。
