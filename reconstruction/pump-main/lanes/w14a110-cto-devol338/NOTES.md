# w14a110-cto-devol338: replacing the line-338 `read_volatile` placeholder (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 963d1eefb (0.67226, 3,123 slots, M 2,244). Continues w14a94/w14a100/w14a103-cto-devol338 (died in setup)
and w14a99-cto-feeexitstore (b0 capture). Ledger: approach `devol338`, keys `0x22a10-w14-963d1ee-devol338-*`.

Oracle: w14a99's raw-IR captures (`ir/m0.ll` = main, `eq_main: true`; `ir/b0.ll` = main minus the line-338
`read_volatile`), `rx.py` (opt -O3 + llc), then w14a98's `sub.border2` content-mapped B / Br (w14a87 relayout with
`Bspec963.txt`), `sc.py` M and `fbound.py` fR/rfR/rfjR. `tools/tbl.py` prints the grid, `tools/irk.py` makes the
post-opt IR kinds from `rx/m/m.ll`.

## (a) b0 x {B, Br}: the original-like validate order does not make the placeholder redundant

| base | post | ratio | M | bytes | jM | fR | rfR | rfjR | errseq 7-10 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| main | - | 0.67226 | 2,244 | 27,400 | 2,271 | 2,290 | 2,622 | 2,620 | 330 338 334 410 |
| main | B | 0.68014 | 2,272 | 27,440 | 2,387 | 2,328 | 2,663 | 2,750 | 330 338 334 410 |
| main | Br | 0.68055 | 2,272 | 27,408 | 2,385 | 2,328 | 2,662 | 2,748 | 330 338 334 410 |
| b0 | - | 0.66547 | 2,221 | 27,392 | 2,249 | 2,267 | 2,597 | 2,590 | 330 338 410 334 |
| b0 | B | 0.67365 | 2,250 | 27,432 | 2,365 | 2,306 | 2,639 | 2,720 | 330 338 410 334 |
| b0 | Br | 0.67406 | 2,250 | 27,400 | 2,363 | 2,306 | 2,638 | 2,718 | 330 338 410 334 |

- b0+Br is 22 M below main+Br (and 24 rfR below). B's moves do not touch E334/E410, so without the edge block E334
  still chains after 410. B and the placeholder are additive (+28 and +23), not substitutes.

## (b) post-opt IR instruction-kind screen of the fee-Some exit block `bb65.i` (main 963d1ee)

`bb65.i` (preds `bb62.i`, the 338 range test) branches to the join `bb76`. Each kind replaces main's
`load volatile i8, ptr %holder_key` there.

| kind | content of the edge | ratio | M | bytes | errseq | +Br M @ bytes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| main | volatile `ldxb` of holder_key | 0.67226 | 2,244 | 27,400 | 330 338 334 410 | 2,272 @ 27,408 |
| e0 | empty block (= b0) | 0.66547 | 2,221 | 27,392 | 330 338 410 334 | 2,250 @ 27,400 |
| **s_st1** | `store i64 1` into `st`+32 (CtoState.max_fee) | **0.67226** | **2,244** | 27,400 | 330 338 334 410 | 2,272 @ 27,408 |
| **s_stb** | `store i8 1` into `st`+40 | **0.67226** | **2,244** | 27,400 | 330 338 334 410 | 2,272 @ 27,408 |
| s_st | `store i64 f` into `st`+32 | 0.67156 | 2,242 | 27,408 | 330 338 334 410 | 2,271 @ 27,416 |
| c7only | an extra copy of the 7 B target join memcpy (bb76 copy kept) | 0.67166 | 2,243 | 27,424 | 330 338 334 410 | 2,272 @ 27,432 |
| c7 | the 7 B target join memcpy sunk into all three preds (edges split) | 0.66367 | 2,217 | 27,440 | 330 338 410 334 | 2,246 @ 27,448 |
| c9 | the 9 B target join memcpy sunk into all three preds | 0.6537 | 2,185 | 27,472 | 330 338 410 334 | 2,214 @ 27,480 |
| f1 | fee-tag phi `[0,1,0]` in bb76 feeding the curve-store test (`mov r7,1` = original data flow) | 0.58931 | 1,968 | 27,424 | 330 338 410 334 | 1,997 |
| f1i | f1 as an i1 phi | 0.58931 | 1,968 | 27,424 | | |
| f1b | f1 also as the admin_cto_pool fee-tag arg | 0.54112 | 1,806 | 27,392 | | |
| f1v | f1 with the volatile load kept | 0.59581 | 1,990 | 27,432 | 330 338 334 410 | |

- Only a one-instruction store of a constant into an escaped stack alloca ties the placeholder (token-identical to
  main). Any value-carrying kind (store of `f`, a join-piece copy) costs 1-59 M; the phi-of-constants that the
  original's `mov r7,1` comes from costs 276 M (its live range across execute recolours everything).
- So the faithful data flow (fee tag known per exit) is the most expensive kind on main's RA, and the cheap kinds
  are pure filler. A source spelling must leave a single surviving, value-free instruction on that edge.
