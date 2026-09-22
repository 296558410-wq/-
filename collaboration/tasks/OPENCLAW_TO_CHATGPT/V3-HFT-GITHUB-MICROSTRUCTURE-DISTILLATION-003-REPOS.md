# Repository Cards — Index (18 carded)

Full 14-item cards live in `../parts/group_{A,B,C}.md`. This index is the machine-checkable summary.

| slug | group | EVIDENCE_LEVEL | TRANSFERABILITY | negative type | sharpest warning |
|---|---|---|---|---|---|
| `RobertN1D/XAUUSD-GOLD-SCALPER-MT5-EA-FREE-SOURCE-CODE` | A | E1 | B | SYNTHETIC_DATA_DEPENDENCE | 11-generator ranker with NO backtest; its only order-flow term is a broker-synthetic DOM the author says to disable |
| `NadirAliOfficial/snipe-fx-ea` | A | E4 | B | COST_TYPE_FAILURE | expected payoff a CONSTANT ~-0.31/trade across all 36 real-tick passes (PF<=0.23); entry is an execution defect |
| `NadirAliOfficial/trillex-10s-ea` | A | E1 | B | SYNTHETIC_TICK_FAILURE | unevidenced signal tested on generated ticks + 10^n lot ladder (10,000-lot cap) |
| `n30dyn4m1c/gold-pro-scalper` | A | E1 | B | NO_PUBLISHED_EVIDENCE | well-reasoned cost gate but no published results; predecessor's OHLC-profitable -> Every-Tick-losing is the trap |
| `Sandyyy123/xauusd-scalper-research` | A | E1 | D | FICTIONAL_FILL_MODEL | bar-touch fills at exact SL/TP with ZERO spread on a 20-min gold scalp; proprietary licence |
| `mahmoud20138/OrderFlow-Scalper` | A | E1 | B | SYNTHETIC_DATA_DEPENDENCE | unvalidated pipeline on a synthetic DOM with inferred aggressor flags; ships defaulted to BTCUSD |
| `Leotaby/Market-Making-Simulator` | B | E2 | C | TAUTOLOGICAL_ADVERSE_SELECTION | AS is an injected post-fill drift; author states no real LOB/feed/queue/latency |
| `diegourda/Statistical-Arb-MM` | B | E1 | C | CLAIM_INFLATION | '30% AS reduction' produced by an engine-free, non-markout toy on data that does not exist |
| `tfrmma/realistic-mm-backtester` | B | E3 | B | UNFALSIFIED_EDGE | genuine FIFO queue/latency/fees/OOS framework but no published OOS result; cancel inference unidentifiable |
| `KlishevDA/Market-Microstructure-and-Latency-Effects-in-L2-Market-Making` | B | E3 | B | QUEUE_ASSUMPTION_FAILURE | fills hinge on an uncalibrated 'rho' luck parameter; single 600s session; no fees |
| `xiaohany-cmu-S26/lob-fill-engine` | B | E3 | B | MODEL_DEPENDENT_LABEL | rigorous purge/embargo/uniqueness fill-probability protocol, but stops at P(fill) - no economic closure |
| `siddhantsingh-1/execution-aware-alpha-backtester` | C | E4 | B | COST_ERASED_ALPHA | OOS IC 0.473, gross +$1.48M, cost $13.11M, net -$11.64M; edge 9.11bps < 10.3bps round-trip |
| `snowkings/QIP_adverse_selection` | C | E4 | B | EXECUTION_FAILURE | +0.29 tick midpoint move vs 1.08 tick spread; negative at every delay and horizon; no CI implied (clustered) |
| `himagna16/kalshi-microstructure` | C | E4 | B | COST_ERASED_ALPHA | 'inefficient at the mid, efficient at the touch'; naive taker momentum dies at 10.7c break-even; passive maker -$913 |
| `aryansiwach/execution-market-microstructure` | C | E3 | B | REGIME_DEPENDENT_COST | realised spread turns NEGATIVE for small caps under stress; IS never reaches zero for large orders |
| `gelatotrade/implementation-shortfall-hyperliquid` | C | E3 | B | DATA_INTEGRITY_FAILURE | Perold 4-term IS incl. Opportunity on the UNFILLED fraction; namespace collision silently overwrote data |
| `Trumplus/AAPL-Limit-Order-Fill-Probability-Forecast` | C | E3 | C | MODEL_DEPENDENT_LABEL | AUC ~0.72 ceiling for 5s fills; queue position dominates fill probability - which FXTM cannot observe |
| `AshJha0/electronic-trading` | C | E4_ENGINEERING_E1_MARKET | B | CALIBRATION_GAP | 'calibration of eta,gamma_p,A,k to any real market is NOT verified'; AC omits the epsilon*X cost term |

## Verified but not carded (HTTP 200, kept for completeness)

Group C reported 19 slugs verified / 8 carded; the 11 not carded are listed in `../parts/group_C.md` §4
(`Weichong515/Algo-Trading-14`, `KBenBec/quant-microstructure-hft-`, `furlong-cp/QueueEdge`,
`FrionicSaddly/perp-quant-bot`, `ishabh-24/markout`, `ferflorespr/quant-backtest-execution-engine`,
`FETKlOkAn2/crypto-quant-platform`, `xuxingjiankr-cpu/perception-xalpha-lite`, `FatihHekim0glu/algo-system`,
`srgangaram-swe/AlphaForge`).

**Searches returning nothing usable (valid negative results):** `latency+discount+backtest` (0),
`backtest+profit+real+tick+failure` (0), `predictive+R2+contemporaneous+R2+trading` (0),
`tail+risk+dominated+PnL+strategy` (0), `expected+net+return+label+trading` (0),
`gross+net+pnl+attribution+trading` (0), `microstructure+forex+execution+cost` (0);
`cost+aware+loss+trading` returned 2 spam hits; `HFT+failed` 1 irrelevant hit.
