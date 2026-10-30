# w12b05-hop-irshape: exact-IR target for swap_hop (0x5b3b0)

Lane `w12b05-hop-irshape`, wave 12, pool b. Target: `multi_hop_curve::swap_hop` at 0x5b3b0,
pinned at 18,584 B. Base: main 20a1ae9c0 (baseline sha 8cd7695c..., 1033/1033 of 1035).

**Status:** swap_hop is matched on main (normalized and raw) since #2766 (w12b09-hop-hillclimb,
merge 0b5fc0d5d), which uses the mechanism described here. This lane landed no source change.

## Result 1: the exact-IR target is ONE instruction move (oracle, 0 slots)

On main 20a1ae9c0's post-optimization IR, `llc` reproduces the baseline swap_hop exactly
(`ref_equal: true`, 0.99913 / 18 slots). The **only** IR change needed to reproduce the
**original** swap_hop bytes (ratio 1.0, `slots_diff` 0, 18,584 B; call and lddw immediates masked)
is the definition point of the `&Global` argument of `complete_fill`:

```llvm
bb57:                                  ; the `if base > reserves {` block, line 599 starts here
  %_618 = load ptr, ptr %ctx.8.val     ; a.global (the Box<Account<Global>> pointer)
  ...  a.user.key() memcpy into %user, load c.is_mayhem_mode, br bb58 / bb59
bb58:                                  ; whitelist memcmp block
  %_870 = getelementptr inbounds i8, ptr %_618, i64 648    ; &global.whitelist_pda
  %298 = call i32 @memcmp(%user, %_870, 32)
  br i1 %.not, label %bb60 (599 error), label %bb64
bb64:                                  ; complete_fill block
  %_218 = getelementptr inbounds i8, ptr %_618, i64 8      ; <-- &Global for complete_fill
  call fastcc void @complete_fill(..., ptr %_218, ...)
```

Main defines `%_218` in bb64 (rustc's initial IR already puts it there, and any earlier copy is
sunk to the top of bb64 by InstCombine). Moving that single GEP to **any** position in bb57 (after
the `%_618` load) or in bb58 gives the exact original bytes. At the top of bb64 it gives main's
18 slots. Positions tested (all 18,584 B):

| `%_218` defined at | ratio | slots_diff |
| --- | ---: | ---: |
| bb64, before the call (main) | 0.99913 | 18 |
| bb64 top (where InstCombine sinks it) | 0.99913 | 18 |
| bb58 top / after memcmp / before the `br` | 1.0 | 0 |
| bb57 right after the `%_618` load / before the mayhem `br` | 1.0 | 0 |

So the older "0.99956/2" oracle figure (lane w9r2-swaphop-frame, on 2abb99ccb) is out of date:
on current main there is no second residual: with this one move nothing else differs, so the
r1/r2 Error reload order at the line-599 `require!` (thought to be a separate residual) is
resolved by the same move.

Reproduce (about 1 s per oracle run on the reduced module):

```bash
OUT=~/.cache/pumpfun-reconstruction/lanes/<lane>
python3 tools/capir.py --src <crate> --work $OUT/work_ir --out $OUT/ir0       # one build, emits module.ll
python3 tools/reduce.py $OUT/ir0/module.ll $OUT/ir0/hop.ll                   # keep only swap_hop's body
python3 tools/orc.py $OUT/ir0/hop.ll --name base --ref <baseline unstripped.so>   # 0.99913/18, ref_equal
python3 tools/orc.py $OUT/ir0/hop.ll --edit tools/edit_exact_gep218.py --name exact  # 1.0 / 0
```

(`tools/` here are copies of the w9r2-swaphop-frame oracle with this lane's paths, plus
`reduce.py`, which turns every other define into a declare and drops aliases, so `llc` only
compiles swap_hop.)

## What the Rust spelling must do

Get the `&Account<Global> -> &Global` deref (`+8`) for `complete_fill` evaluated in a block that
precedes the complete_fill block (bb57 or bb58), in a form that neither MIR nor InstCombine moves
back to the call:

- InstCombine sinks a single-block-use instruction into that block only when the block's unique
  predecessor is the defining block. bb64's unique predecessor is bb58, so a GEP that is defined
  in **bb57** and used only in bb64 would stay. A GEP defined in bb58 is sunk.
- `let global = &*a.global;` is `&Account<Global>` (a.global is `Box<Account<'info, Global>>`), so
  the `+8` deref coercion is re-emitted at the call (`s_bindB`, byte-identical; ledger
  `...-irshape-bindB-account-ref-analysis-v1`).
- A GEP defined before the `if base > reserves` branch (bb56) is too early: oracle 0.98164 / 242
  slots (`p_bb56`).

### Why every plain `&Global` binding is byte-identical (pass trace)

`s_bindC1` (`let global: &Global = &a.global;` before the allowed block, whitelist through
`global`, `complete_fill(global, ..)`) built with `-Cllvm-args=-print-changed=quiet
-Cllvm-args=-filter-print-funcs=<swap_hop>` in a scratch copy:

| after pass | bb57 | bb58 (whitelist) | bb64 (complete_fill) |
| --- | --- | --- | --- |
| rustc output | `%global = gep %box, 8` (dead) | `gep %box, 8` then `+640` | `%_219 = gep %box, 8` |
| EarlyCSE | (deleted, no uses) | `%250 = gep %box, 8` | CSE'd into bb58's `%250` |
| InstCombine | | `gep %box, 648` | `%250` sunk to the top of bb64 |

The binding is dead in rustc's own IR: MIR ReferencePropagation rewrites both the deref
`(*global).whitelist_pda` and the call-argument reborrow `&(*global)` back to the place
`(*box).account`, so each use gets a fresh `gep %box, 8`. EarlyCSE then merges the bb64 copy into
the dominating bb58 copy, and once InstCombine folds the whitelist GEP to `+648`, the bb58 copy's
only user is bb64 and InstCombine sinks it there (bb64's unique predecessor is bb58).

So the spelling must give the call a `&Global` that MIR cannot see through, computed in bb57.
The lanes that did this (ledger rows of 2026-10-30 12:33-12:41 UTC) all reach the
normalized+raw match:

- w12b09-hop-hillclimb (#2766): `let (allowed, global) = { let global: &Global = &a.global; ..;
  (cond, global) };` (a tuple field hides the reference from ReferencePropagation);
- w12b14-hop-stitch: `let (global,): (&Global,) = (&a.global,);` (same mechanism);
- w12b07-hop-gepsib (#2780): a plain local `fn whitelist_ok(global: &Global, ..)`, which the MIR
  inliner does not inline (local, non-generic, not `#[inline]`), so the coercion is a real call
  argument in bb57;
- w12b06-hop-cfsig: `#[cold] fn global_of(a) -> &Global` (the MIR inliner refuses cold callees).

## Full IR delta of a landed-form spelling (checked)

Scratch IR build of the #2766 tuple spelling on main 20a1ae9c0 (`s_tuple09`): target_metric
1.0 / 0 slots at 18,584 B; `score.py` against the 20a1ae9c0 baseline gives 1034 normalized /
1034 raw, no losses, gain 0x5b3b0 (normalized and raw). Its post-opt swap_hop IR, aligned by
name-free block signatures (`tools/blkdiff.py`) against main's IR with only the oracle move
applied, differs in exactly one more place:

1. `gep %box, 8` is defined in bb57 right after the `a.global` load (the intended change);
2. the shared Err sink block (phis of the line-599 `AnchorError` and the `complete_fill` Err,
   then the store to `%_0`) is placed right after the complete_fill blocks instead of near the end
   of the function, and its two phi operands are in the opposite order.

Item 2 does not change the code. Main's IR with only item 1 already gives the exact original
bytes, and so does the tuple IR (`llc` output equals its own build, `ref_equal`). So the
complete delta from main to the original swap_hop is the single GEP definition point, and the
earlier "r1/r2 Err reload order at line 599" residual was a side effect of that GEP.

Trials and their outcomes are in the ledger under lane `w12b05-hop-irshape`.
