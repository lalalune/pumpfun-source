# w12b05-hop-irshape: exact-IR target for swap_hop (0x5b3b0)

Lane `w12b05-hop-irshape`, wave 12, pool b. Target: `multi_hop_curve::swap_hop` at 0x5b3b0,
pinned at 18,584 B. Base: main 20a1ae9c0 (baseline sha 8cd7695c..., 1033/1033 of 1035).

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

Trials and their outcomes are in the ledger under lane `w12b05-hop-irshape`.
