# CHATGPT-TASK-V3-HFT-CALIBRATION-FORMULA-FIX-001-RESULT (FINAL)

> **STATUS: PASS** — V3-only minimal repair of the calibration net_pnl formula
> (`v3-calibration-netpnl-1` → `v3-calibration-netpnl-2`) plus the confirmed
> observability DATA_GAPs of `V3-HFT-CALIBRATION-PILOT-001`.
> The 20/20 frozen run, its ledger and all broker facts are **byte-identical**
> (4/4 baseline SHA256 re-verified after the work). Validation is exclusively
> **offline recompute of the old data with the new formula**.
> **NO order_send anywhere in this task** (no broker write of any kind).
> `EXPANSION=LOCKED  LIVE=FALSE  ORDER_SEND=FALSE`.

```text
TASK_ID    = V3-HFT-CALIBRATION-FORMULA-FIX-001
STATUS     = PASS
STARTED_AT = 2026-09-21T07:11:13Z  (15:11 GMT+8)
FINISHED_AT= 2026-09-21T07:18:00Z  (15:18 GMT+8)

LOCAL_HEAD = 4f6bd54c4a4963fb2885921fee1d7adb510c940a   (C:\AIQuant, branch fix/v2-full-system-repair-20260917)
REMOTE_HEAD= 06745eabbca52934b3e3e1737ebf4ee7dc8a0e15   (staging main, first landing of this report)

FILES_CHANGED = research/hermes/trader_v3/foundation/calibration_pilot.py
FILES_CREATED = research/hermes/trader_v3/foundation/pnl_accounting.py
                research/hermes/trader_v3/foundation/tests/test_v3_formula_fix.py
                research/hermes/trader_v3/audit/v3_formula_fix_recompute.py
                research/hermes/trader_v3/audit/v3_formula_fix_comparison.csv
                research/hermes/trader_v3/audit/v3_formula_fix_summary.json
FILES_DELETED = (none)

V1_UNTOUCHED = TRUE
V2_UNTOUCHED = TRUE
V3_UNTOUCHED = FALSE (intended, V3-only: calibration_pilot + new foundation helper)
             V3_ALPHA_UNTOUCHED = TRUE (no Alpha feature / decision / strategy field added)
HERMES_UNTOUCHED = TRUE (no Hermes decision path, no scheduler, no config touched)

BROKER_ORDER_SENT = FALSE   (0 order_send; broker accessed read-only, not at all by the fix)
```

## 0. The mandatory report block

```text
STATUS: PASS

BUGS_FIXED: 6 (all in foundation/calibration_pilot.py::_round_trip net_pnl path)
  1 double-charged spread (fill price already contains bid/ask)
  2 double-charged entry/exit slippage (already inside the fill price)
  3 abs() cost-ised favourable slippage -> signed terms only
  4 MT5 commission<0 (cost) subtracted as `- comm` -> sign inverted (2x|comm| error)
  5 broker realized P&L / execution cost / model(theoretical) P&L now separated explicitly
  6 units taken from the broker symbol spec (contract_size x volume), cross-checked vs
    tick value / tick size, account-currency conversion explicit

TESTS: 9/9 PASS (+ existing foundation suite 28/28 PASS, unchanged)
  A PASS  spread not double charged (corrected -0.18 vs old -0.36)
  B PASS  favourable slippage stays favourable (corrected +0.06 vs old -0.36)
  C PASS  commission<0 reduces net (0.78 vs old 1.04 = sign inversion)
  D PASS  commission=0 -> net == gross
  E PASS  swap=0 -> net == gross+fees ; swap=-0.5 shifts net by -0.50
  F PASS  LONG and SHORT both correct (mirror symmetric)
  G PASS  contract_size/volume scaling (u=1.0 / 10.0 / 0.1); tick-metadata mismatch flagged DATA_GAP
  H PASS  frozen 20 round trips recompute offline (old formula reproduced 20/20)
  I PASS  broker realized P&L reconciles with independent broker facts (-7.44 == balance delta)

OLD_NET:       mean -0.137500 USD / round-trip  (total -2.750)
CORRECTED_NET: mean -0.372000 USD / round-trip  (total -7.440)
BROKER_NET:    mean -0.372000 USD / round-trip  (total -7.440)

OLD_ERROR:       +4.690000 USD total  (+0.234500 / round-trip, model too optimistic)
CORRECTED_ERROR: +0.0000000000000371 USD total (+1.86e-15 / round-trip)

MAX_RESIDUAL:  8.003597784522753e-13 USD
MEAN_RESIDUAL: 3.0740687773089803e-13 USD

RAW_DATA_IMMUTABLE: TRUE  (4/4 baseline SHA256 identical, see §5)
ORDER_SENT: FALSE
LIVE: FALSE
EXPANSION: LOCKED

V1_UNTOUCHED: TRUE
V2_UNTOUCHED: TRUE
V3_ALPHA_UNTOUCHED: TRUE

GIT_COMMIT: 4f6bd54c4a4963fb2885921fee1d7adb510c940a
REMOTE_SYNC: 06745eabbca52934b3e3e1737ebf4ee7dc8a0e15  (local HEAD == origin/main, verified)
REPORT_COMMIT: 06745eabbca52934b3e3e1737ebf4ee7dc8a0e15  (staging commit that first carried this report)
```

## 1. What was wrong (confirmed by V3-HFT-COST-BRIDGE-AUDIT-001)

Frozen line (`v3-calibration-netpnl-1`):

```python
s["net_pnl"] = (s["gross_pnl"] - spread
                - abs(s["slippage_price"] or 0) - abs(s["exit_slippage_price"] or 0)
                - (comm if comm is not None else 0))
```

| # | defect | effect on the 20/20 run |
|---|---|---|
| 1 | `- spread`: the order is priced at the executable side (buy@ask / sell@bid), so the spread is **already inside** `gross_pnl = exit_fill - entry_fill` | +0.1800 USD/RT spurious cost |
| 2 | `- abs(slippage)` both legs: the fill **is** the executed price, slippage is already inside it | +0.0255 USD/RT spurious cost |
| 3 | `abs()` makes a **favourable** fill a cost (V3CAL-00 exit filled +0.30 better than its reference) | included above |
| 4 | `- comm` with MT5 `commission = -0.22/RT` (negative = cost) **adds** 0.22 instead of charging it | −0.4400 USD/RT error (2×|comm|) |
| 5 | realised broker P&L, execution cost and theoretical P&L were one conflated number | no decomposition, not auditable |
| 6 | no spec-based unit reconstruction (`gross` was dead code multiplying by a `volume` key that was never set) | units were implicit |

Net: old model reported **−0.1375/RT** while the broker realised **−0.3720/RT**; the whole
**+0.2345/RT** gap was a pure accounting artifact (no real cost was ever unaccounted).

## 2. The repaired formula (`v3-calibration-netpnl-2`, foundation/pnl_accounting.py)

```text
u                     = contract_size × volume                      # broker spec, USD per 1.0 price
gross_pnl_price       = signed(exit_fill − entry_fill)              # spread+slippage ALREADY inside
gross_pnl_usd         = gross_pnl_price × u
fees_usd              = commission + swap                           # broker sign, commission<0 == cost
CORRECTED_NET (net_pnl)= gross_pnl_usd + fees_usd                   # broker-anchored rebuild

BROKER_REALIZED_NET   = Σ deal.profit + Σ deal.commission + Σ deal.swap   # ANCHOR (never modelled)
residual              = CORRECTED_NET − BROKER_REALIZED_NET               # reconciliation
THEORETICAL_NET       = mid_to_mid_gross + fees_usd          # DIAGNOSTIC ONLY
EXECUTION_FRICTION    = mid_to_mid_gross − actual_gross      # signed, + = cost
   = (entry_fill − entry_mid) + (exit_mid − exit_fill)  [direction-signed] × u
   = FRICTION_SPREAD (half-spreads) + FRICTION_SLIPPAGE (exact, additive)
identity: CORRECTED_NET = THEORETICAL_NET − EXECUTION_FRICTION   (asserted)
```

Spread/slippage are now reported as **diagnostics with**
`spread_slippage_basis = EMBEDDED_IN_FILL_PRICE_NOT_DEDUCTED`; they are never deducted
a second time and never presented as broker P&L. The theoretical number is explicitly
labelled `DIAGNOSTIC_ONLY`.

## 3. Old vs new, all 20 round trips (offline recompute)

`audit/v3_formula_fix_comparison.csv` / `v3_formula_fix_summary.json`
(inputs: frozen ledger + frozen registry + frozen broker probe; **no broker call**).

| trade | side | old_net | corrected_net | broker_realized_net | old_error | corrected_error |
|---|---|---|---|---|---|---|
| V3CAL-00 | LONG | -0.160000 | **-0.100000** | -0.10 | -0.060000 | +8.0e-13 |
| V3CAL-01 | SHORT | -0.150000 | **-0.410000** | -0.41 | +0.260000 | +4.0e-13 |
| V3CAL-02 | LONG | -0.120000 | **-0.370000** | -0.37 | +0.250000 | -5.5e-13 |
| V3CAL-03 | SHORT | -0.180000 | **-0.440000** | -0.44 | +0.260000 | -2.5e-13 |
| V3CAL-04 | LONG | -0.140000 | **-0.400000** | -0.40 | +0.260000 | -2.9e-13 |
| V3CAL-05 | SHORT | -0.140000 | **-0.400000** | -0.40 | +0.260000 | -2.9e-13 |
| V3CAL-06 | LONG | -0.140000 | **-0.400000** | -0.40 | +0.260000 | -2.9e-13 |
| V3CAL-07 | SHORT | -0.150000 | **-0.400000** | -0.40 | +0.250000 | -2.9e-13 |
| V3CAL-08 | LONG | -0.150000 | **-0.400000** | -0.40 | +0.250000 | -2.9e-13 |
| V3CAL-09 | SHORT | -0.140000 | **-0.400000** | -0.40 | +0.260000 | -2.9e-13 |
| V3CAL-10 | LONG | -0.180000 | **-0.420000** | -0.42 | +0.240000 | +1.8e-13 |
| V3CAL-11 | SHORT | -0.140000 | **-0.400000** | -0.40 | +0.260000 | +6.2e-13 |
| V3CAL-12 | LONG | -0.120000 | **-0.300000** | -0.30 | +0.180000 | +7.3e-14 |
| V3CAL-13 | SHORT | -0.060000 | **-0.300000** | -0.30 | +0.240000 | +7.3e-14 |
| V3CAL-14 | LONG | -0.060000 | **-0.320000** | -0.32 | +0.260000 | -3.6e-13 |
| V3CAL-15 | SHORT | -0.140000 | **-0.400000** | -0.40 | +0.260000 | +6.2e-13 |
| V3CAL-16 | LONG | -0.200000 | **-0.420000** | -0.42 | +0.220000 | +1.8e-13 |
| V3CAL-17 | SHORT | -0.120000 | **-0.380000** | -0.38 | +0.260000 | +1.5e-13 |
| V3CAL-18 | LONG | -0.090000 | **-0.350000** | -0.35 | +0.260000 | -1.1e-13 |
| V3CAL-19 | SHORT | -0.170000 | **-0.430000** | -0.43 | +0.260000 | -3.6e-14 |

```text
OLD_MODEL_NET_MEAN   = -0.137500    CORRECTED_MODEL_NET_MEAN = -0.372000    BROKER_NET_MEAN = -0.372000
OLD_TOTAL_ERROR      = +4.690000    CORRECTED_TOTAL_ERROR   = +3.71e-14
MAX_ABS_RESIDUAL     = 8.00e-13     MEAN_ABS_RESIDUAL       = 3.07e-13
BROKER gross -3.04 + commission -4.40 + swap 0.00 = -7.44  (== balance delta 5000 -> 4992.56)
```

Broker facts were **not** adjusted to lower the residual: `broker_realized_net` comes from
`deal.profit/commission/swap` only. `old_formula_reproduced = TRUE` for 20/20, i.e. the OLD
number is exactly the published one — the defect is reproducible, not re-interpreted.

## 4. How it was validated (no orders)

1. `foundation/tests/test_v3_formula_fix.py` — 9 independent cases (A–I), exit 0 on success.
   H/I read only the frozen artifacts and assert the old formula reproduces the published
   data and the corrected formula reconciles to the broker within 1e-6 USD.
2. `audit/v3_formula_fix_recompute.py` — writes the comparison CSV + summary JSON.
3. Integrated check of the **modified pilot path** itself (throwaway mock broker, temp
   ledger, no broker I/O, not committed): LONG `net_pnl = +0.600000` vs `broker_realized_net
   = +0.600000`, SHORT `-1.399999` vs `-1.400000`, residual ~1.6e-13,
   `accounting_reconciliation = PASS`, ledger hash-chain OK, `volume=0.01`,
   `price_unit_usd=1.0`, `hold_actual_ms≈102` (monotonic, was 0/1000/2000 quantised).
4. Regression: the pre-existing foundation suite is untouched and still **28/28 PASS**.

## 5. Historical-data protection (re-verified AFTER the change)

| artifact | expected SHA256 | actual | result |
|---|---|---|---|
| `data/hft_ledger/v3_calibration_ledger.jsonl` | FC8FD01E…06750C | FC8FD01E…06750C | UNCHANGED |
| `data/calibration/PILOT_DONE` | DEC80E9F…8339C6 | DEC80E9F…8339C6 | UNCHANGED |
| `data/calibration/registry.jsonl` | 7AD9596C…6F4F25 | 7AD9596C…6F4F25 | UNCHANGED |
| `audit/_probe_broker_out.json` | F76782CE…5D70CA0 | F76782CE…5D70CA0 | UNCHANGED |

No broker fact, ledger line or registry row was overwritten, deleted, regenerated or
re-sent. The fixed code only affects **future** runs.

## 6. Observability added (V3 calibration only)

`entry_fill_price` (was written under the wrong key → `registry.jsonl` had `null`),
`entry_bid/ask`, `exit_bid/ask`, `exit_tick_age_ms`/`tick_age_ms`, `hold_actual_ms`
(now monotonic, legacy value kept as `hold_actual_ms_tick_stamp`), `broker_*` deal facts
(theorem timestamps + server offset), `broker_gross_profit`, `broker_realized_net`,
`reconciliation_residual`, `price_unit_usd`, `unit_status`, `net_pnl_status`,
`gross_pnl_usd`, `fees_usd`, `theoretical_net`, `execution_friction`,
`friction_spread/friction_slippage`. **No Alpha feature or decision field was added.**

## 7. DATA_GAP (unchanged / newly documented — not repaired here)

1. **exit-side bid/ask are not in the frozen ledger** (only the executable side). The
   friction/theoretical split of the historical 20 therefore uses the previous audit CSV
   as *supplementary* (`exit_quote_source=AUDIT_CSV_SUPPLEMENTARY`); on new runs the pilot
   now stores `exit_bid/exit_ask`. `CORRECTED_NET`/`BROKER_REALIZED_NET` never depend on it.
2. **`tick.age` for the historical 20 is unrecoverable** (computed in code, never
   persisted); now recorded for future runs.
3. **broker `trade_tick_value = 0.1` is inconsistent with `contract_size = 100`**
   (`unit_status = DATA_GAP_TICK_VALUE_INCONSISTENT` on all 20). The accounting uses
   `contract_size × volume`, verified 20/20 against `deal.profit`; the tick metadata is
   reported, never used. No FX conversion needed (profit ccy == account ccy == USD).
4. No independent tick/quote source covers the 2026-09-20T23:05:42–23:06:13Z window
   (pre-existing; unchanged).
5. Historical `registry.jsonl` keeps `entry_fill_price: null` — the frozen record is
   immutable by instruction; the corrected value is recoverable from the ledger and is
   written properly from now on.
6. Sample size n=20 (statistical, not a defect) — **no expansion attempted**.

## 8. Scope discipline

* No Alpha research, no model training, no GPU model, no strategy/entry/exit/parameter work.
* No Hermes decision path, no scheduler/cron/config change, no dashboard change.
* No V1/V2 file touched; no new calibration order; `ORDER_SEND=FALSE` throughout.
* No HALT was required: the repair fit entirely inside V3 calibration code.

## 9. Next

```text
NEXT_RECOMMENDATION = WAIT_FOR_CHATGPT_AUDIT.
  (research suggestion only; the decision belongs to the user)
  - independent audit of the v2 accounting definition (esp. friction decomposition and
    the tick-value DATA_GAP);
  - keep EXPANSION=LOCKED until that audit closes; calibration expansion / Alpha / demo
    forward remain separate, explicitly authorised tasks.
```

`EXPANSION=LOCKED  LIVE=FALSE  ORDER_SEND=FALSE  V1/V2 UNTOUCHED`
