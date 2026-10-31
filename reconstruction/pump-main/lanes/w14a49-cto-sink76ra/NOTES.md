# w14a49-cto-sink76ra: the sink76 "RA cascade" is an edge-block artefact; the E334 placement is worth +0.0075 at 27,400 B with no cascade

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a36-cto-blockplace (#3325) next_idea 1. Bases: main 28ab23a (0.65488), then 0fbf8da (0.65578, 3,279 slots).
Ledger approach `sink76ra`, keys `0x22a10-w14-<sha7>-sink76ra-*`. Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a49-cto-sink76ra/`.

## 1. Where sink76's loss comes from (tools/sinkx.py, tools/edge19h.py)

`tools/sinkx.py m.ll out.ll A BC` generalises w14a36's `sink76.py`: the 7-byte target piece memcpy (A) and the 9-byte
piece via `_48.sroa.11` (BC) are each kept in `bb76` (`76`), sunk to `bb22` + top of `bb19` (`s19`), `bb22` + end of
`bb19` (`e22`), `bb22` + a new block on the `bb19 -> bb26` (shared+holder) edge (`s19h`, = sink76), or all three arms
(`all`). Post-opt IR (rx.py `m.ll`) -> release llc -> rx tokens; 28ab23a main is 0.65488.

| A \ BC | 76 | s19 | e22 | s19h | all |
| --- | ---: | ---: | ---: | ---: | ---: |
| 76 | 0.65488 (main) | 0.65479 @27,432 | 0.65479 @27,432 | 0.63683 @27,256 * | 0.63585 @27,288 * |
| s19 | 0.65479 @27,432 | 0.6541 @27,464 | 0.6541 @27,464 | 0.63585 @27,288 * | 0.63546 @27,320 * |
| s19h | 0.63683 @27,256 * | 0.63585 @27,288 * | 0.63585 @27,288 * | **0.60691 @27,272 * (sink76)** | 0.63436 @27,312 * |

`*` = errseq `330 338 334 410`. The order flips exactly when the `bb19 -> bb26` edge gets its own block, whatever it
holds. `tools/edge19h.py` with only an empty `asm sideeffect ""` in that block (all copies left in `bb76`) gives the flip
and the cascade too: 0.63661 @27,224 (-176 B). So the cascade is caused by splitting the shared+holder edge (the `bb19`
phi constants for `bb26` move off `bb19`), not by where the target copies are. Moving the copies alone (`s19`, `e22`)
neither flips the order nor cascades.

## 2. IR bound: split the fee-Some exit edge instead (tools/split1.py, tools/split76.py)

Splitting `bb58.i -> bb76` (validate's fee-Some exit, the original's +0x1800 block) with a non-foldable empty block:

| split edge(s) into `bb76` | 28ab23a | 0fbf8da |
| --- | ---: | ---: |
| none (main) | 0.65488 / 3,279 | 0.65578 / 3,279 |
| `bb58.i` (fee Some) | **0.66237 @27,400, 3,224 slots** | **0.66327 @27,400, 3,224 slots** |
| `bb45.i` (fee None, new) | 0.66127 @27,392 | |
| `bb58.i` + `bb45.i` | 0.66117 @27,400, 3,178 slots | |
| `bb58.i` + `bb44.i` | 0.66227 @27,408 | |
| `bb44.i` (fee None, holder) | 0.63062 (order `410 330 338 334`) | |
| all three | 0.65169 @27,392 | |

fm/sk on 28ab23a: main 0.70252/0.78250, `bb58.i` split 0.70911/0.78969. The `bb58.i` split reproduces w14a36's
placement-only bound (+0.0075) at the pinned size, with one local RA change (`bb54.i` reloads the cashback flag
instead of `mov r1,r9`). So the bound for "original E334 placement with main's RA" is **0.66327 on 0fbf8da**.

Edge blocks that fold (byte-identical to main): empty, a lone `lifetime.end`, a lone `lifetime.start` (0.65339, a
stack-colouring change only). The block must hold an instruction that survives to MachineBlockPlacement.

## 3. What the original's split block is

Original +0x1800 (fee-Some exit) and +0x10e8 (a fee-None exit) are tail-duplicated copies of `bb76`: both start with the
same spill stores (`stxdw [r10-0x918],r4; stxdw [r10-0x948],r3`), then a fee-tag phi constant (`mov64 r7,1` for Some;
`r7=0` at +0x1108 for None), then the shared test. `r7` is spilled to `[r10-0x8e8]` at the join (+0x1998) and is the fee
tag read at +0x4b80 (line-757 store) and +0x4dc8 (`pargs.2` tag for `admin_cto_pool`). The fee argument's own entry spill
`[r10-0x918]` is reused for the target piece at +0x1800, so in the original the argument tag dies in validate and later
code reads a re-materialised `Option` tag (the fee value stays the argument's `[r10-0x930]`).

IR probes of that (tools/ftag.py, tools/ftag2.py; phi of constants in `bb76`):

| probe (28ab23a) | ratio | bytes | fm | sk |
| --- | ---: | ---: | ---: | ---: |
| tag phi for the line-757 test | 0.56946 | 27,432 | 0.69521 | 0.78174 |
| + `bb58.i` split | 0.57695 | 27,432 | 0.70180 | 0.78922 |
| tag phi for the 757 test and the CPI tag argument | 0.60045 | 27,232 | 0.67468 | 0.76063 |
| + `bb58.i` split | 0.58171 | 27,352 | 0.68396 | **0.79310** |

The last one has the best skeleton seen here, but adds a spill slot (TCF clone run 8 B lower: orig `[r10-0xaf8]`, main
2808, probe 2816), so every frame-relative token in segs 69/72 misses.

## 4. Branch weights do not give the original order (tools/bw.py)

`!prof` on `bb54.i` (fee_configurable, currently the zero heuristic 12:20) and `bb58.i` (range): best 0.65648 @27,416
(bb54 4:1, order `330 334 338 410`); 0.65518 @27,400 (1:2 + 1:2, order unchanged). No weight gives `330 338 334 410`.
