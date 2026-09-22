# Timestamp Alignment Policy

Task: **V3-HFT-MICROSTRUCTURE-DATA-SOURCE-AUDIT-001** (task §十四).

This policy governs any future attempt to align a **candidate external source** with the
FXTM V3 feed. It is a *relationship audit*, never an alpha search.

## 1. Applicability

The alignment experiment is **applicable only if** a candidate source passes the
relevance gate in `execution_relevance_matrix.md` (i.e. it is claimed to be the same
liquidity/execution pool as FXTM retail XAUUSD).

**Current status: NOT APPLICABLE / `DATA_GAP`.**
No candidate was found that is claimed to be FXTM's own execution pool:
* FXTM's own L2 is realtime-only (no history) and its sizes are a constant synthetic ladder
  → nothing to align against historically;
* CME/COMEX and LBMA/OTC are `AUXILIARY_ONLY` by construction;
* vendor spot-FX/gold L2 belongs to other venues.
No alignment experiment was therefore run, and no alignment claim is made.

## 2. Rules (binding when it does apply)

```text
1. Unit + timezone must be DECLARED (ms/us/ns; UTC). No silent inference
   (microstructure/timestamp_unit_guard.py). A missing unit => DATA_INVALID.
2. No future information may be used anywhere.
3. Alignment is measured on the FIRST REAL event at or after the target time — never interpolated.
4. Report the response/lag structure at: 0 ms, 100 ms, 250 ms, 500 ms, 1 s, 5 s.
5. Report: timestamp alignment, price correlation, lead/lag, spread relationship,
   event timing, price response.
6. The output is a SOURCE RELATIONSHIP AUDIT only.
7. It is FORBIDDEN to tune parameters, or to keep mining because one lag looked best.
   Best-lag selection is itself a multiple-testing problem and is banned here.
8. Clock discipline: if the two sources use different clocks/servers, the offset must be
   estimated and reported; an unestimated offset => DATA_GAP, not an assumption.
```

## 3. Minimum reporting table (to be filled only if applicable)

| lag | n | price correlation | lead/lag sign | spread ratio | note |
|---|---|---|---|---|---|
| 0 ms | DATA_GAP | DATA_GAP | DATA_GAP | DATA_GAP | not applicable (no qualifying source) |
| 100 ms | DATA_GAP | DATA_GAP | DATA_GAP | DATA_GAP | — |
| 250 ms | DATA_GAP | DATA_GAP | DATA_GAP | DATA_GAP | — |
| 500 ms | DATA_GAP | DATA_GAP | DATA_GAP | DATA_GAP | — |
| 1 s | DATA_GAP | DATA_GAP | DATA_GAP | DATA_GAP | — |
| 5 s | DATA_GAP | DATA_GAP | DATA_GAP | DATA_GAP | — |

**A correlation between gold prices is NOT an execution link.** Only same-pool, same-venue,
same-execution-environment evidence counts as alignment.
