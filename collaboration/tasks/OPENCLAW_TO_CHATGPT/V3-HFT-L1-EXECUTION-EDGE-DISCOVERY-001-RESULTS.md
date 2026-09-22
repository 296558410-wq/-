# Experiment Results — L1 Execution Edge

- SNAPSHOT V3-SNAP-20260922T025312Z · manifest sha256 `a036a808d5d924a7a99c5941919971ff00ce9e28c804e8e91860b6ffd7fa61b5`
- files 36 · ticks 7,285,000 · grid 4,239,246
- cost 0.914 bp · folds {'train': 1728000, 'val': 1209600, 'test': 1296001}

## Selected configurations (VAL selection, TEST evaluated once)

| h | family | model | n | eff_n | mean bp | median bp | win | boot CI |
|---|---|---|---|---|---|---|---|---|
| 5s | PRICE | ridge | 708 | 37 | -0.470606 | -0.446576 | 0.444915 | [None, None] |
| 10s | SPREAD | tree_depth3 | 92 | 2 | -6.287792 | -2.120264 | 0.358696 | [None, None] |
| 30s | SPREAD | logistic | 108 | 0 | 7.99465 | 1.467624 | 0.583333 | [None, None] |
| 60s | SPREAD | logistic | 234 | 1 | 12.011321 | 1.49924 | 0.641026 | [None, None] |
| 300s | SPREAD | ridge | 432 | 0 | 11.046354 | 1.777209 | 0.631944 | [None, None] |

## FDR

- total 196 · valid 35 · insufficient 161 · significant 35

## Tail vs central tendency

| h | median bp | mean bp | top1% | top5% | top10% |
|---|---|---|---|---|---|
| 5s | -0.446576 | -0.470606 | -0.871203 | -1.735794 | -2.332575 |
| 10s | -2.120264 | -6.287792 | -0.051657 | -0.186401 | -0.34032 |
| 30s | 1.467624 | 7.99465 | 0.108691 | 0.377629 | 0.616885 |
| 60s | 1.49924 | 12.011321 | 0.073498 | 0.304953 | 0.524404 |
| 300s | 1.777209 | 11.046354 | 0.076941 | 0.386488 | 0.711819 |

## Diagnostic on the positive result (§三十 checks)

- `corr(pred, spread_bp) = -0.999434` -> the predictor is the entry spread.
- `long_share ≈ 2.7865049564956914e-06` -> essentially all trades are SHORT.
- top10% share `0.700725` -> tail-dependent.
- the mechanical predictor `pred = -spread/2` produces 0 trades, so the 'edge' needs an amplified
  spread signal to cross the cost threshold; it is not a forecast of the future mid.
