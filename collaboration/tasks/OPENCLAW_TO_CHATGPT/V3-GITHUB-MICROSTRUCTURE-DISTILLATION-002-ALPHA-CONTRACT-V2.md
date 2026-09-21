# V3 ALPHA CONTRACT v2

- Task: **V3-HFT-GITHUB-DISTILLATION-002** (research infrastructure)
- Mode: AUDIT / READ-ONLY on market data. No orders. No changes to V1/V2/OpenClaw/foundation.
- Supersedes the informal single-layer "alpha" notion used before.
- Evaluation chain (mandatory for every future claim):

```text
Gross Edge -> Execution Cost -> Adverse Selection -> Slippage -> Commission -> Latency -> NET EXECUTABLE EDGE
```

> **Prediction accuracy is NOT alpha.** A model that is "right" more often than not is worthless
> unless the net executable edge survives the chain above.

---

## Level A — Prediction Alpha

The model answers only: *does the next short interval move in direction d?*

Required outputs: `P(up)`, `P(down)`, `expected_return`, `expected_move`.

**This layer cannot produce a trade signal by itself.** It is an input to Level B/C only.
Accuracy, R², AUC are diagnostics here — never a verdict.

## Level B — Microstructure Alpha

Inputs: spread, bid/ask imbalance, microprice, OFI, trade imbalance, queue pressure,
arrival intensity, cancellation intensity, volatility state, adverse selection.

Output: `gross_microstructure_edge`.

Data gate: on the current FXTM **L1-quote-only** feed, `microprice`, `true_ofi`, `size_imbalance`,
`queue_pressure`, `trade_imbalance`, `vpin`, `kyle_lambda` are **DATA_GAP**
(see `hypotheses/data_state_machine.md`). Only `spread`, `mid`, `volatility_state`,
`arrival_rate`, and the explicitly-named `OFI_PROXY` / `FLOW_PROXY` are computable today.

## Level C — Execution Alpha

Decides *whether the opportunity is worth executing*. Required outputs:

| term | symbol | current status |
|---|---|---|
| expected spread cost | `E[spread_cost]` | MEASURED (0.343 bp median) |
| expected slippage | `E[slippage]` | PARTIAL (calibration, signed) |
| expected commission | `E[commission]` | MEASURED (0.22 USD/RT) |
| expected latency loss | `E[latency_cost]` | PARTIAL (RTT ≈ 273–279 ms measured) |
| expected adverse selection | `E[AS]` | PARTIAL (markout-based) |
| expected fill probability | `E[P(fill)]` | **DATA_GAP** (no L2 queue) |
| **net executable edge** | `NET_EXECUTABLE_EDGE` | = gross − all of the above |

```text
NET_EXECUTABLE_EDGE = Gross Edge
                    - spread_cost - commission - slippage
                    - latency_cost - adverse_selection - impact
```

**Only Level C may gate a Hermes decision.** Level A or B passing alone is `WAIT`.

---

## Tradability rule (frozen before testing)

```text
EXPECTED_GROSS_EDGE  >  EXPECTED_TOTAL_COST + SAFETY_MARGIN
AND  P(NET_EDGE > 0) > threshold
```

Initial research threshold: `NET_EDGE_MIN = +0.10 USD/RT`. Frozen before measurement; must not be
changed after seeing results. Cost anchor: **0.914 bp / RT** (the old 0.314 bp model is deprecated
and must not be restored).

## Non-negotiable modelling rules

- No Transformer, no LSTM, no large DL search.
- No feature mining without pre-registration.
- No back-modifying features from TEST results.
- No "keep tuning because one result looked nice".
- No accuracy-based verdicts.
- Overlapping horizons: always report `effective_n`; use block bootstrap / block permutation.
- Unmeasurable term => `DATA_GAP`, never `0`, never silently a proxy (unless named `*_PROXY`).

## Pre-declared diagnostic references (NOT alpha candidates)

Two declared, non-searched rules used only to classify failure modes:
`momentum_sign` = sign(r1), `reversal_sign` = −sign(r1), fixed horizon 1 s, fixed cost 0.914 bp.
They are diagnostics; they are not entered into any multiple-testing family as alpha.
