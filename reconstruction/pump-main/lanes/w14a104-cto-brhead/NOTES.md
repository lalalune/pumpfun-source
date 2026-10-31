# w14a104-cto-brhead: the head half of Br (validate 284-298), notes only

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 963d1eefb (0.67226, M 2,244, jM 2,271) and main 13fe4536b (0.67256, M 2,245, jM 2,271).
Continuation of w14a97-cto-brhead (no PR). Companions: w14a98-cto-brtarget (target half), w14a101-cto-mirorder296.
Ledger: approach `brhead`, keys `0x22a10-w14-963d1ee-brhead-*` and `0x22a10-w14-13fe453-brhead-*`.

**Result so far: no landable change; the best zero-loss measurement is main.** But the 289 half of the head is
source-reachable, and on top of it the remaining Br head is an IR-order question, priced below.

## 1. The 289 piece is one plain spelling: `h289`

`if st.holder_reward&&!holder{..289..}` (use validate's `holder` bool instead of re-testing `hopt==Some(true)`)
gives Br's `bb7.i -> bb10.i` fallthrough (Err289 glued after the hr=1 holder test). It is byte-identical to w14a83's
`s289G` (Try on an if-expression), so that is the mechanism behind s289G too.

| base | M | jM | ratio @ bytes |
| --- | ---: | ---: | --- |
| main 963d1ee | 2,244 | 2,271 | 0.67226 @ 27,400 |
| h289 on 963d1ee | 2,230 | **2,341** | 0.66806 @ 27,400 |
| main 13fe453 | 2,245 | 2,271 | 0.67256 @ 27,400 |
| h289 on 13fe453 | 2,231 | **2,341** | 0.66836 @ 27,400 |

h289 changes only orig chunk 0x800 (-14 M / +57 jM); every other chunk is unchanged, so RA outside validate is
untouched. The -14 is jump distances: the head is now in Br order up to bb12.i (hr=0 holder test), which still falls
into the enabled test.

## 2. Head-only bound (task step 1)

`relayn.run_rev` on the 963d1ee main capture, placement only (main's RA). None of the head-only subsets gains:

| layout | M | jM | bytes |
| --- | ---: | ---: | ---: |
| main | 2,244 | 2,271 | 27,400 |
| task head subset (bb10 bb3.i30 bb16 bb22 bb17 bb3.i23 exit24) | 2,192 | 2,302 | 27,416 |
| bb7->bb10 only (a1) | 2,213 | 2,341 | 27,400 |
| bb7->bb10 + bb14->bb16->bb22 (a3) | 2,215 | 2,273 | 27,400 |
| a1 + bb14 next (a4) | 2,214 | 2,349 | 27,408 |
| full Br (a87 Bspec, misaliased) | 2,258 | 2,375 | 27,416 |

So the head half alone is not worth +14 M; it is worth jM only. This agrees with w14a98's unit table.

## 3. On the h289 capture: what the rest of the head is worth (real llc, RA recomputed unless noted)

Names are h289's IR names: bb12.i = hr=0 holder test, bb13.i = holder_enabled test, bb15.i = Err296,
bb20.i = holder arm (298 test), bb21.i = non-holder arm (306 tag test), bb25.i = Err306.

| probe (13fe453 h289 unless noted) | M | jM | bytes | ratio |
| --- | ---: | ---: | ---: | --- |
| h289 | 2,231 | 2,341 | 27,400 | 0.66836 |
| relay, full Br (963d1ee, main RA, placement only) | 2,270 | 2,383 | 27,416 | 0.67984 |
| relay, target piece only: bb12->bb21->bb25 (963d1ee) | 2,248 | 2,359 | 27,400 | 0.67346 |
| IR order: bb21.i after bb12.i, bb25.i after bb21.i, bb20.i after bb13.i (**no weights**) | **2,249** | 2,359 | 27,392 | 0.67386 |
| IR order bb21>bb12, bb20>bb13 + !prof 1:1 on bb12.i and bb21.i | **2,263** | 2,380 | **27,400** | **0.67795** |
| same weights without the IR moves (963d1ee) | 2,241 | 2,359 | 27,408 | 0.67126 |
| IR moves without weights, bb21>bb12 + bb20>bb13 | 2,208 | 2,317 | 27,400 | 0.66147 |
| single weights bb12.i 1:1 or bb21.i 1:1 (963d1ee) | 2,204 / 2,203 | | 27,408 | |

- The IR-order route (row 4) needs **no branch weights**: on BPF, a block that ends in a conditional branch is glued to
  its IR successor (w14a78 sec. 2), so putting bb21.i right after bb12.i and bb25.i right after bb21.i gives both
  fallthroughs by itself. It is +4 M at -8 B over main, so it would land with an M-neutral +8 B knob.
- The weights route (row 5, +18 M at 27,400) needs the holder and tag tests at 50/50, i.e. the original's `and 1`
  tests. Every holder-bool spelling that produces `and 1` falls into the and-1 RA basin (section 4).

## 4. Spelling table (963d1ee unless noted; seq.py checked)

| spelling | result |
| --- | --- |
| 289 `if hr&&!holder` (h289) / s289G / e3c (holder bool param) | **2,230 @ 27,400** (identical); Br 289 piece |
| 289 `if hr&&hopt!=Some(true)` | identical to main |
| 289 `if hr{if !holder{..}}`, `match (hr,holder)`, `match hr{true=>289,false=>296}` | outline basin 0.425 @ 26,976 |
| 289 `if hr{match hopt{Some(true)=>{},_=>289}}` | 0.507 @ 27,256 |
| `match holder{false=>289,true=>296}`, `match holder{true=>{},false=>289}` | 0.580 @ 26,984 |
| 296 nested `if holder{if !hr&&!en{..}}` / 296 inside `let target=if holder{` | outline basin 0.428 (on h289: identical / 0.434) |
| h289 + 296 operand orders `!hr&&holder&&!en`, `!(hr\|\|en)&&holder`, `!hr&&!en&&holder` | outline basin 0.415-0.419 |
| h289 + `holder&&!(hr\|\|en)`, `..&&true`, nested-if | identical to h289 |
| h289 + `holder&&!en&&!hr` | 0.648 @ 27,416 |
| h289 + `hopt==Some(true)&&..` at 296, `if hopt==Some(true)` at 298 | 0.534 / 0.426 |
| h289 + `holder&&!(hr\|en)`, `holder&!hr&!en` | 0.576 / 0.534 |
| h289 + holder arm as closure / nested fn `hold()` at 296-298 (`if holder` or `if !holder`) | outline basin 0.433 @ 26,960 |
| h289 + target `match hopt{Some(true)=>..,_=>..}` / `Some(false)\|None` first | 0.486 / 0.505 |
| h289 + `let target=if !holder{else}else{holder}` | 2,229 (same layout) |
| h289 + let-else 298 / let-else 306 / t1 / tu8 | eq / 2,215 / 2,226 @ 27,408 / 2,203 @ 27,416 |
| h289 + target as `match holder{true if !hr&&!en=>Err296, true=>.., false=>..}` (also `!(hr\|\|en)` guard, `(holder,hr\|\|en)` tuple) | outline basin 0.414-0.434 |
| h289 + holder target as `Option<Pubkey>` then `if let` | 0.580 @ 26,992 |
| validate-local holder via `unwrap_or(false)`, `unwrap_or_default`, `is_some_and`, `matches!`, `if let` | and-1 basin 0.533-0.540 @ ~26,850 |
| e3b/e3d (holder bool param via unwrap_or/matches!) | 0.545 @ 27,232 |

The outline basin is the original's to_string shape (h289+in298 outlines exactly the two non-holder-arm to_strings,
307 and 312, as the original does) but with a global frame/RA cascade (0x2000-0x4000 chunks -86..-180 M).

## 5. Why the head stops at h289 (mechanism)

Three rules fix the head, and source can only reach the first:

1. **rustc first-reference order.** A block is appended when a codegened terminator first names it. Err296 is named
   by the enabled test (MIR bb14), and bb14 always comes before the target's holder join (bb19) in RPO. So Err296 and
   the 296 chain are always created before the target arms (bb21/bb20). Operand order, `!`/`==false`, nesting, guards
   and the `holder&&!(hr||en)` forms cannot change this. The only exception is a form that tests holder once
   (296 inside the holder arm), and that form triggers rule 3.
2. **BPI zero heuristic.** Our holder test is `icmp eq (and hopt,-3),0` (12:20). bb12.i is not glued, because its IR
   successor is bb7.i. So MBP lays out the holder side first. The original's `and 1` tests are 50/50.
   Every spelling that yields `and 1` (`unwrap_or(false)`, `matches!`, `is_some_and`, `if let`, bool param via those)
   falls into the and-1 RA basin (0.53-0.55).
3. **Outline basin = the LLVM inliner's cold-callsite rule.** Without a profile, a call site whose BFI frequency is below
   2% of the caller's entry gets the cold threshold (45), and to_string is then not inlined. BFI of validate, from
   `opt sroa,early-cse,simplifycfg,instcombine + print<block-freq>`:

| sites | h289 (inlined) | h289 + 296 inside holder arm (outlined) |
| --- | ---: | ---: |
| non-holder arm entry | 0.117 | 0.070 |
| 307 to_string block | 0.0220 | 0.0132 |
| 312 to_string block | 0.0223 | 0.0134 |

   Main stays inlined only because BFI treats the target's second `holder` test as independent of the 296 chain's
   first one. That counts the non-holder arm about 1.7x too often, and the 307/312 sites end up just 10% above the
   2% line. Any single-holder-test structure (nest/in298/closure/nested fn/match guard) drops them below it, which
   outlines 307/312 exactly as the original does. Each of those forms then moves frame and RA everywhere (the outline
   basin, 0.41-0.43).
   - For a single-test structure to stay inlined, the non-holder arm needs about 1.5x more frequency from some other
     branch. The mayhem test's error side gets 0.625, because a bool test against 0 favours the nonzero side.

## Next ideas

1. Find a rustc first-reference order that puts the non-holder arm's tag test (bb21) and its Err306 block right after
   the hr=0 holder test, without nesting 296 into the holder arm (nesting outlines 307/312). Then repay +8 B.
2. `tools/irscan.py` single-move IR-order scan on the h289 capture (see SUMMARY.json for its best moves).

## Tools (`tools/`, experiment only)

`trial.sh`/`q.sh`/`defs.py` (source spelling -> raw-IR capture -> rx -> sc + seq), `hv.py` (relay variants),
`prof.py`/`profrun.py` (!prof weights on post-opt IR + llc), `irmv.py` (move post-opt IR blocks + llc; run
`opt -passes=instnamer` on m.ll first), `irscan.py` (all single moves, 4 workers), `jdist.py` (jM-matched pairs with
different jump offsets in a chunk). They use w14a97's sc.py/relayn.py/seq.py/rx.py from the lane's cache dir.
