# V3-HFT-DATA-EXECUTION-GAP-CLOSURE-001

- Mode: **AUDIT / READ-ONLY research infrastructure**. `ALPHA_SEARCH = OFF`, `MODEL_SEARCH = OFF`,
  `FEATURE_MINING = OFF`, `HYPOTHESIS_EXPANSION = OFF`.
- This task does **not** look for alpha and does **not** trade. It removes drift, ambiguity and
  un-observability from the V3 research base.
- Prior findings are **frozen, not rewritten** (task XXVII): 50 ms/200 ms/1 s/2 s remain COST BLOCKED.

## 0. FINAL STATUS

> ### `D — DUAL_BLOCKED`
> `COST_BLOCKED` (h ≤ 2 s: cost/typical-move ≥ 1.22) **+** `DATA_BLOCKED`
> (true OFI / bid-size / ask-size / microprice / L2 imbalance / trade flow / queue / VPIN /
> Kyle-λ / fill probability are all `DATA_GAP` on this L1-quote-only feed).
> `EXECUTABLE_ALPHA_CANDIDATE` **does not appear** — this task has no alpha mandate.

## 1. What was built (task V–XXXIV)

| capability | artifact |
|---|---|
| immutable snapshot + manifest | `data/snapshots/V3-SNAP-20260922T025312Z/`, `research/snapshot/V3_DATA_SNAPSHOT_V3-SNAP-20260922T025312Z.json` |
| duplicate triage | `research/snapshot/V3_DUP_TRIAGE_V3-SNAP-20260922T025312Z.json` |
| timestamp guard | `microstructure/timestamp_unit_guard.py` |
| canonical cost model | `execution/cost_model_v2.py` (version `CALIBRATION_20RT_20260921`) |
| locked markout | `microstructure/markout.py` |
| locked adverse selection | `microstructure/adverse_selection.py` |
| execution observability states | `execution/observability.py` |
| failure taxonomy (observability-gated) | `execution/execution_quality.py` |
| cost-to-move v2 (on snapshot) | `research/v3_markout/run_cost_to_move.py` → `cost_to_move_v2.json` |
| data contract v2 | `research/v3_data_contract_v2.md` |
| regression suite | `research/tests/test_gap_closure.py` — **27/27 PASS** |

Snapshot: **36 files, 7,285,000 rows**, manifest sha256 `a036a808d5d924a7a99c5941919971ff00ce9e28c804e8e91860b6ffd7fa61b5`.

## 2. Q1–Q15

**Q1 — Is the research snapshot truly immutable?** **YES.**
Copy-on-cut into `data/snapshots/<ID>/`, then read-only file attribute, plus per-file sha256 in the
manifest. `RESEARCH_SNAPSHOT_IMMUTABLE = TRUE`. Tests `test_snapshot_immutability` and
`test_snapshot_files_readonly` pass.

**Q2 — Can the live collector still contaminate research?** **NO.**
`LIVE_SOURCE_MUTABLE = TRUE` and the tail file is marked `EXPECTED_MUTABLE_SOURCE`
(`live_fxtm/ticks_20260921.parquet` was rewritten; `ticks_20260922.parquet` is new and still open).
Research reads **only** the snapshot (`run_cost_to_move.py` loads `data/snapshots/<ID>/`).

**Q3 — Are the 913 (now 1014) duplicates timestamp or event duplicates?**
`DUP_TIMESTAMP_COUNT = 1014`, `DUP_QUOTE_COUNT = 1014` (identical `ts,bid,ask`),
`DUP_EVENT_COUNT = 0` when the source file is included. The feed has **no event id**, so true event
identity cannot be proven: **`EVENT_IDENTITY = DATA_GAP`**. Nothing was deleted.

**Q4 — Is the timestamp unit locked forever?** **YES.**
`timestamp_unit_guard` requires an explicit unit (`ms|us|ns`); a missing unit raises
`DATA_INVALID` — no silent inference. Proven by
`test_ms_timestamp`, `test_us_timestamp`, `test_ns_timestamp`, `test_utc_conversion`,
`test_monotonicity`, `test_future_timestamp`, `test_timestamp_range`, `test_no_silent_inference`.
(1000 ms = 1_000_000 us = 1_000_000_000 ns = 1 second, all asserted.)

**Q5 — Is there exactly one canonical cost?** **YES.**
`cost_model_v2` with `COST_MODEL_VERSION = CALIBRATION_20RT_20260921`,
`REAL_RT_COST_BP = 0.914`, and six separate terms.

**Q6 — Has 0.314 bp left the current research path?** **YES.**
It exists only as `DEPRECATED = {"value_bp": 0.314, "status":
"HISTORICAL_INVALID_FOR_CURRENT_RESEARCH"}`; `assert_not_deprecated(0.314)` raises.

**Q7 — Is the slippage sign definition correct?** **YES.**
Slippage is **signed**; only the **unfavorable** part is a cost; `abs(slippage)` is forbidden.
Tests: favorable / unfavorable / zero × long / short, plus `test_only_unfavorable_slippage_is_cost`.

**Q8 — Is the commission sign definition correct?** **YES.**
Documented conversion: broker statement carries cost as negative; research/ledger carry cost as a
positive entry that is subtracted. `test_commission_convention` passes.

**Q9 — Is the markout formula explicit?** **YES.**
`LONG: EXECUTION_MARKOUT = future_mid − entry_execution_price`;
`SHORT: entry_execution_price − future_mid`; plus `MID_MARKOUT` and `COST_ADJUSTED_MARKOUT`.
Direction tests pass. Measured (long, on snapshot, cost 0.914 bp):

| h | MID_MARKOUT median | EXEC median | COST-ADJ median | mean (mid) | std |
|---|---|---|---|---|---|
| 100 ms | 0.000 | −0.195 | −0.914 | +1.257 | 13.75 |
| 1 s | 0.000 | −0.195 | −0.914 | +1.257 | 13.75 |
| 30 s | −0.045 | −0.230 | −0.959 | +1.262 | 13.92 |

**Q10 — Is the Adverse Selection sign explicit?** **YES.**
`LONG_AS = entry_execution_price − future_mid`; `SHORT_AS = future_mid − entry_execution_price`;
**AS > 0 = price moved against the fill**. `AS = −EXECUTION_MARKOUT` (asserted).
The 4-case manual matrix (`LONG/SHORT × up/down`) returns **PASS**.

**Q11 — Does the AS mean still suffer censoring contamination?** **NO (resolved).**
Censored samples are `HORIZON_CENSORED` and **excluded**, never set to 0; `censored_n` is reported
(1 at 1 s, 30 at 30 s). Mean and median are reported together with std/p10/p25/p75/p90/effective_n.
Measured long AS: `median = +0.185…+0.230 bp` (adverse) but `mean = −1.05 bp` —
i.e. **the central tendency is mildly adverse while the mean is tail-driven (favorable tails)**;
`TAIL_EFFECT_bp` is reported separately, so the mean is never read alone.

**Q12 — Which of TYPE5/6/7 are actually observable today?** **NONE.**
Fill is assumed perfect, and slippage/latency are not injected, so
`TYPE5/TYPE6/TYPE7 = NOT_TESTED` (never 0). Only `TYPE1_DIRECTION_WRONG` and
`TYPE2_SPREAD_ERASED_EDGE` are `CONFIRMED`.

**Q13 — What can L1 still research?**
spread, mid, quote dynamics, tick-flow **proxy**, short-horizon return, volatility, spread regime,
quote arrival, markout, and conditional adverse selection.

**Q14 — What can only L2 solve?**
true OFI, queue imbalance, queue position, true trade flow, fill probability, L2 liquidity
withdrawal, cancellation pressure, microprice.

**Q15 — What should the next stage be?** *(evidence only; the decision belongs to ChatGPT)*
The evidence is: (a) **h ≤ 2 s is COST_BLOCKED** (cost/move 1.22–1.72); (b) **h ≥ 5 s is
RESEARCHABLE but not TRADEABLE** (no alpha demonstrated, only "cost does not exceed typical move");
(c) every Level-B microstructure quantity is `DATA_GAP`. Therefore the next stage can only be
**(i) continue L1 research restricted to h ≥ 5 s**, or **(ii) acquire L2 / size / trade-flow data**,
or **(iii) accept COST_BLOCKED for the short horizons**. It cannot be a Level-B microstructure test
on the present feed.

## 3. Cost-to-move v2 (task XXIX, computed on the snapshot)

| horizon | median \|move\| | p75 | p90 | cost | cost/move | effective_n | status |
|---|---|---|---|---|---|---|---|
| 50 ms | 0.536 | — | — | 0.914 | 1.704 | 4,239,246 | RESEARCH_BLOCKED_BY_COST |
| 100 ms | 0.536 | — | — | 0.914 | 1.706 | 4,239,246 | RESEARCH_BLOCKED_BY_COST |
| 200 ms | 0.532 | — | — | 0.914 | 1.717 | 4,239,246 | RESEARCH_BLOCKED_BY_COST |
| 500 ms | 0.580 | — | — | 0.914 | 1.576 | 2,255,278 | RESEARCH_BLOCKED_BY_COST |
| 1 s | 0.638 | — | — | 0.914 | 1.432 | 1,127,639 | RESEARCH_BLOCKED_BY_COST |
| 2 s | 0.749 | — | — | 0.914 | 1.221 | 563,819 | RESEARCH_BLOCKED_BY_COST |
| 5 s | 1.037 | — | — | 0.914 | 0.881 | 225,527 | RESEARCHABLE |
| 10 s | 1.414 | — | — | 0.914 | 0.647 | 112,763 | RESEARCHABLE |
| 30 s | 2.383 | — | — | 0.914 | 0.384 | 37,587 | RESEARCHABLE |
| 1 min | 2.845 | — | — | 0.914 | 0.321 | 18,793 | RESEARCHABLE |
| 5 min | 5.425 | — | — | 0.914 | 0.169 | 3,758 | RESEARCHABLE |

*(p75/p90 and exact medians: `research/v3_markout/cost_to_move_v2.json`.)*
**`RESEARCHABLE ≠ TRADEABLE`** (task XXVIII): 5 s+ means only that cost does not exceed the typical
move; it is **not** evidence of alpha.

## 4. Data Capability Matrix (task XXX)

| 能力 | 状态 |
|---|---|
| Bid / Ask / Spread / Mid | SUPPORTED |
| Tick direction | SUPPORTED |
| Commission | SUPPORTED |
| Markout | SUPPORTED |
| Latency | PARTIAL |
| Slippage | PARTIAL |
| OFI proxy | PARTIAL |
| Adverse Selection | PARTIAL |
| True OFI | DATA_GAP |
| Bid size / Ask size | DATA_GAP |
| Microprice | DATA_GAP |
| L2 imbalance | DATA_GAP |
| Trade flow | DATA_GAP |
| Queue position | DATA_GAP |
| VPIN | DATA_GAP |
| Kyle-λ | DATA_GAP |
| Fill probability | DATA_GAP |

## 5. L1 / L2 boundary (task XXXI)

**L1 can research:** spread, mid, quote dynamics, tick-flow proxy, short return, volatility,
spread regime, quote arrival, markout, conditional AS.
**L1 cannot reliably research:** true OFI, queue imbalance, queue position, true trade flow,
fill probability, L2 liquidity withdrawal, cancellation pressure.

**No external price source** (DUKA / Yahoo / Sina / Tencent / GC / GLD) may substitute FXTM's
executable bid/ask/spread/execution price; such feeds are auxiliary-only and must be explicitly marked.

## 6. Research Decision Matrix (task XXXVII)

| 项目 | 状态 | 证据 | 下一步 |
|---|---|---|---|
| 50 ms | RESEARCH_BLOCKED_BY_COST | cost/move 1.704 | stop on this venue |
| 200 ms | RESEARCH_BLOCKED_BY_COST | cost/move 1.717 | stop on this venue |
| 1 s | RESEARCH_BLOCKED_BY_COST | cost/move 1.432 | stop on this venue |
| 2 s | RESEARCH_BLOCKED_BY_COST | cost/move 1.221 | stop on this venue |
| 5 s | RESEARCHABLE | cost/move 0.881 | L1 research only; not tradeable |
| 30 s | RESEARCHABLE | cost/move 0.384 | L1 research only; not tradeable |
| 5 min | RESEARCHABLE | cost/move 0.169 | L1 research only; not tradeable |
| L1 Direction | NOT_SUPPORTED | 0/30 FDR in Discovery 001; cost > move ≤ 2 s | keep gated |
| OFI Proxy | PARTIAL | tick-rule only; cannot substitute true OFI | L2 required |
| True OFI | DATA_GAP | needs bid/ask sizes (identically 0) | L2 required |
| Markout | SUPPORTED | locked 3-variant definition; censoring-aware | standard diagnostic |
| Adverse Selection | PARTIAL | locked sign; median mildly adverse; mean tail-driven | conditional model later |
| Fill Probability | DATA_GAP | no L2 queue; interface only | L2/MBO required |
| Queue | DATA_GAP | no depth/queue data | L2/MBO required |
| Execution Cost | SUPPORTED | canonical 0.914 bp, versioned | use everywhere |

## 7. Impact on prior results (task XXXVIII)

No historical result changed: the cost anchor, the ≤2 s block, and the `NO_ALPHA` verdict are
unchanged. `timestamp` fix, censor fix and observability states are **infrastructure**, not
re-analysis. `STOP / COMPARE OLD VS NEW / REPORT IMPACT`: the only numeric deltas are
(a) duplicate count 913 → **1014** (the live feed kept appending) and
(b) AS mean → now censoring-free and reported beside the median. Neither alters a prior conclusion.
No model was re-run; no hypothesis was added.

## 8. Problems found, NOT fixed (task XXXIX)

No defect was found in MT5 routing, V1/V2 isolation, broker accounts, `order_send`, ledger integrity,
execution safety or the cost formula, so **no HALT was triggered**. Reported only:
`live_fxtm` appends (expected-mutable); 1014 cross-file duplicate timestamps (`EVENT_IDENTITY = DATA_GAP`);
pre-existing uncommitted FORMULA-FIX CSV enrichment (unrelated to this task).

## 9. Final safety acceptance (task XLII)

```text
ORDER_SEND = 0
CALIBRATION = 0
FORWARD = NO
LIVE = NO
EXPANSION = LOCKED

V1 = UNTOUCHED
V2 = UNTOUCHED
OPENCLAW = UNTOUCHED

MT5_INSTANCE_COUNT = 3
MT5_ISOLATION = PASS

ALPHA_SEARCH = OFF
MODEL_SEARCH = OFF
FEATURE_MINING = OFF
```

## 10. One-line conclusion

> Prediction, cost, slippage, latency, fill, markout, adverse selection and data gaps are now
> **separated and measurable**. Cost blocks h ≤ 2 s; data blocks every microstructure quantity.
> **No unknowns were disguised as zeros, proxies, or model assumptions.**
