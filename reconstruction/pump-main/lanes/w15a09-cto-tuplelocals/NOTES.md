# w15a09-cto-tuplelocals: per-field respelling of the execute tuples (exhausted) + creator-early binding

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base main 90300f9
(0.67346, 3,124 slots; unchanged on ed47ac7 / d421912, admin_cto.rs identical). Continues w14a144-cto-vinarm (#3621, #3633)
next idea 1: apply the proven `tuple -> per-arm let mut` respelling (pl2) to the execute tuples it did not cover. Ledger
approach `tuplelocals`, keys `0x22a10-w15-90300f9-tuplelocals-*`.

## Method

w14a144's raw-IR oracle (capture with `--emit=llvm-ir -C no-prepopulate-passes` through fastbuild, SDK `opt -O3`, `llc`
like fastbuild; `eq_main` true on the `none` capture). One gene per tuple field and per arm form (`tools/tg.py`: exact
single-occurrence replacements, line count kept). Each variant is ranked by ratio, difflib M / fM / rfjM (w14a108 `fr.py`)
and **true LCS** (w14a128 `lcs.py`, rfj mask; main 3,007). `tools/run1.sh <name> <genes> <slot>` captures and scores one;
`tools/batch.sh` runs a list on one slot; `tools/rec3.py` records rows; `tools/tab3.py` builds `screen_table.md`.
Each capture is ~22 s (it is a full rustc compile), so at most 2 ran at a time.

## Result: no per-field respelling gains at the pinned size (93 variants)

Full table: `screen_table.md`. Summary by tuple field:

| field / tuple | forms tried | best | verdict |
| --- | --- | --- | --- |
| cashback (6-tuple + hop) | per-arm `let mut` (c1, c4, c5), deferred per arm (c2, c6, A5), third tree-tuple field (c3) | c1..c6 all converge on one 27,264 B code, M 1,882, true-LCS rfj 2,995 (-12) | lose. The per-arm cashback phi is orig-like (orig stores cashback per validate exit in `[r10-0x958]`), but it frees `!holder`'s live range and RA changes in 0x2800-0x3800 (-247 unmasked LCS tokens there) |
| target | deferred from `let vt=validate()?` (t1, t3), tree-tuple field (t2), all fields per arm (A1-A4, A6, A7) | t1 rfj 3,002 | lose (-0.30 ratio: whole-frame shift, not frame-only) |
| sharing_update | deferred (s1), tree-tuple field (s2), payload computed before validate (f5) | s1 = f5 = main bytes; s2 0.67266 @27,416 | neutral / lose |
| collect_old | mut local (k2), deferred (k3), value computed before (f1) / after (f2) validate | f1 0.594 | lose (k2/k3 = w14a144 pl7 collapse) |
| skip | mut local (k1), deferred (k4), `!(shared&&holder)` after (f3) / before (f4) the tree | k1 = k4 = 0.67346 tie (7 slots at 0x17d0 rescheduled, LCS -1) | neutral |
| tree arm form | `match (shared,holder)` (m1), `match shared` (m2), `shared&&holder` chain (m3), `!shared` first (m4) | m1 = m2 = m4 = main bytes | neutral; m3 loses |
| outer `Ok::<_,Error>((..))?` hop | field subsets (o1, o2), extra fields (o3, o4), orders (o5-o7), identity map (o8), `(mut target,..)` (h1) | o3/o4/o6/o7/o8/h1 = main bytes; o1 tie | the hop's field order and set are irrelevant to codegen |
| inner 6-tuple block | drop `_holder` (q1), 7 orders (q2-q8) | q1-q5, q7 = main bytes | neutral; `sharing_update` before `target` (q6, q8) = 0.67316 (pre-pl2 value) |
| pargs | bound inside the pool arm (p1), deferred (p2), split locals (p3), mut field (p4) | all = main bytes | no effect |
| vo1 + frame permutations (w14a144 idea) | vo1 re-priced, vo1 / vo1c / vo1d x hop subsets and orders | vo1co7 0.55299 @27,288 | vo1's true-LCS rfj is 2,989 (-18): its gap is skeleton, not a permutation. Hop orders do not move its frame at all |

The combinations of the neutral ones (k1+o1, k4+o1, k1+q6) are ties or worse. **The respelling family is exhausted on
main 90300f9**: every field is either byte-identical, a tie, or collapses.

## New lead: binding the curve creator early (skeleton gain blocked by +120 B)

The shared non-holder arm's `target=a.bonding_curve.creator` becomes `target=creator` with the creator bound earlier:

| gene | binding | bytes | M | rfjM | true-LCS `---` / rfj |
| --- | --- | ---: | ---: | ---: | --- |
| main | | 27,400 | 2,248 | 2,810 | 2,253 / 3,007 |
| **g1** | `let creator=st.creator;` before `validate` | 27,520 | **2,250** | 2,820 | **2,255 / 3,014** |
| f6 / g6 | `let creator=a.bonding_curve.creator;` before `validate` | 27,528 | 2,246 | 2,817 | 2,251 / 3,015 |
| g2 / g7 / g9 | before `let hopt` / before `let cashback` / as `args.1` | 27,496 | 2,234 | 2,817 | 2,239 / 3,015 |
| g3 | at the start of the state block | 27,464 | 2,247 | 2,810 | 2,252 / 3,010 |
| f7 | after validate, before the tree | 27,440 | 2,247 | 2,810 | 2,252 / 3,010 |
| g4 | by reference | = main bytes | | | |

g1 is the only spelling that is better than main on every token metric, but the creator pieces stay live across validate
and cost 15 extra moves and reloads in 0x4f8-0x1af0 (+120 B). The rest of the function is main's code shifted by 0x78 with
the `[r10-0x8e0]`/`[r10-0x900]` spill slots swapped. The applicable negative size knobs from `sizeknobs-cto.json` each cost
10-15 M on main (s_dest_borrow -80 B M 2,234; cu_typed -32 B M 2,236; cu_fee_replace -8 B M 2,233; sh_prog_let -32 B
M 2,237; s_old_borrow, sh_accs_let and ev_reset_shared are worse). Pinned composites lose: X4 = g1 + s_dest_borrow + sh_prog_let
+ cu_fee_replace 0.66477 @27,400 (M 2,219, 3,057 slots); X2 = g3 + cu_typed + sh_prog_let 0.66717 @27,400 (M 2,227).

**For the outline lanes (w15a02 t312repay, w14a141): g1 and g3 are positive byte-repay knobs on the outline bases**
(`outline_bases.txt`, w14a144 `vr.sh` with `ed/ni.py`):

| gene | O (307+312 noinline): B / M | O312 (312 only): B / M |
| --- | --- | --- |
| none | 26,992 / 1,954 | 27,184 / 2,195 |
| g1 | 27,120 (+128) / **1,959 (+5)** | 27,304 (+120) / **2,198 (+3)** |
| g3 | 27,016 (+24) / **2,047 (+93)** | 27,248 (+64) / 2,195 (0) |
| f6 | 27,128 (+136) / 1,955 (+1) | 27,312 (+128) / 2,194 (-1) |
| f7 | 27,032 (+40) / 1,954 (0) | 27,224 (+40) / 2,195 (0) |

On O312 (needs +216 B) g1 repays 120 B and gains 3 M; g3 on base O gains 93 M for 24 B.

## Next ideas

1. g1 / g3 on the outline bases, with the remaining repay found among faithful data-flow forms (w15a02 owns the outline).
2. The original's validate head copies a 32 B stack value `[r10-0x6a0..0x688] -> [r10-0x518..0x500]` (orig 0x598-0x5d0)
   where ours loads `[r3+..]` directly. That copy, not a held register, is probably the faithful home for the creator/target
   bytes g1 keeps live. A form that makes the early creator a memory copy (not SSA pieces) would get g1's skeleton without its
   moves.
3. The per-arm cashback phi (c-family) is orig-like and shrinks the function by 136 B. It needs RA recovery in 0x2800-0x3800.
   The w14a84 RA ceiling tooling could price c1. c1 + g1 measured: 27,384 B, M 1,880, true-LCS rfj 3,005 (c1 + f6 27,392 B,
   rfj 3,006). The skeleton is nearly main's, but registers and frame are still c1's.
