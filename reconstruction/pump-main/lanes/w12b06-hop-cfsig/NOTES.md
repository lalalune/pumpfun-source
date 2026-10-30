# w12b06-hop-cfsig: complete_fill's `&Global` argument (swap_hop 0x5b3b0)

Target: `multi_hop_curve::swap_hop` at 0x5b3b0, pinned at 18,584 B
(`programs/pump/src/multi_hop_curve_swap.rs`, lines 599-600).
Base: main 20a1ae9c0 (origin/main e61df0357, `programs/` identical): 0.99913, 18 differing slots.
Angle: change how swap_hop hands `&a.global` to `complete_fill` so that the `+8` address is
computed in the whitelist block, as in the original.

## Result

| trial | line 599-600 change | bytes | ratio | slots | norm / raw | losses |
| --- | --- | ---: | ---: | ---: | --- | --- |
| main | `let allowed = { let global = &*a.global; ... }`, `complete_fill(&a.global, ..)` | 18,584 | 0.99913 | 18 | 1033 / 1033 | - |
| t1 | `let global: &Global = &a.global;` before `allowed`, `complete_fill(global, ..)` | 18,584 | 0.99913 | 18 | byte-identical to main | none |
| t2 | `let (allowed, global): (bool, &Global) = { let global: &Global = &a.global; ..; (cond, global) }` | 18,584 | 0.99913 | 18 | byte-identical to main | none |
| **t3** | `#[cold] fn global_of<'a>(a: &'a MultiHopCurve<'_>) -> &'a Global { &a.global } let global = global_of(a);` and `complete_fill(global, ..)` | **18,584** | **1.0** | **0** | **1034 / 1034** | **none** |

t3's unstripped sha256 starts `cbd9bf08d09967f7`, the same binary as lane w12b09-hop-hillclimb's
unannotated tuple spelling (PR #2766). Both spellings give the same bytes. #2766 was already in the
landing queue and landed as 0b5fc0d5d (main 70f27048e: 1034/1034, swap_hop 1.0/0). t3 was not
landed. It is recorded here as an alternative spelling that does not depend on the tuple.

## Oracle: the GEP is the only residual

`llc` on main's post-opt IR (`orc.py` from the w9r2/w12b05 oracle, about 7 s on the full module),
with `%_218 = getelementptr inbounds i8, ptr %_618, i64 8` (complete_fill's `&Global` argument)
moved out of the call block bb64:

| placement | ratio | slots |
| --- | ---: | ---: |
| bb64, before the call (main) | 0.99913 | 18 |
| bb57, right after `%_618 = load ptr, ptr %ctx.8.val` | 1.0 | 0 |
| bb58, after the whitelist `gep %_618, 648` | 1.0 | 0 |
| bb58, after the memcmp `icmp` | 1.0 | 0 |

With the GEP in either earlier block, MachineSink moves the `add64 r2, 8` to the top of bb64,
which is the original's `ldxdw r2,[r10-0xb28]; add64 r2,8` right after the memcmp test (+0x29f8).

## Mechanism

1. **Why t1 fails (MIR evidence, `-Zdump-mir=swap_hop` on an experiment copy).** Passing a `&Global`
   local to a `&Global` parameter is a coercion site, and rustc inserts a reborrow:
   `_466 = &(*_434)` with `_434 = &((*_1643).0: Global)`. MIR `ReferencePropagation` (pass 005-009)
   rewrites the reborrow to `_466 = &((*_1643).0: Global)`. The address is then recomputed in the call
   block, and the binding's own GEP is dead. Any `&T` local that is initialized from a place and passed
   to a `&T` parameter is re-derived at the call this way.
2. **Why t2 fails.** The type annotation `(bool, &Global)` makes the block's tail tuple a coercion site,
   so the tuple field is again a reborrow `&*global`. RefProp rewrites it to `&PLACE` in the
   tuple-construction block, which comes after the memcmp, and InstCombine then sinks that GEP into the
   call block, whose unique predecessor is the memcmp block. Without the annotation (#2766) the field is
   a plain copy and the trick works.
3. **Why t3 works.** The MIR inliner refuses `#[cold]` callees (`check_codegen_attributes`: "cold"), so at
   RefProp time `global` is a call result, not a `&PLACE`, and the reborrow stays tied to it. LLVM's
   inliner then inlines the tiny helper, so the `+8` GEP sits in the over-reserves block bb57 next to the
   `a.global` load. InstCombine cannot sink it, because bb64's unique predecessor is bb58, not bb57.
   The whitelist `gep(global, 640)` folds into `gep(box, 648)` as before. In codegen, MachineSink places
   the add at the top of bb64. No `global_of` symbol remains in the binary.

General rule for other lanes: to keep an address computed early, the reference must be opaque at
MIR RefProp time. Two ways work: a non-MIR-inlined call result (a `#[cold]` helper that LLVM still
inlines), or a tuple-field copy with no coercion. A typed `let x: &T = &place` binding does not work:
RefProp sees through it at every use that derefs or reborrows it.

## Rejected interface variants (by reasoning; complete_fill is byte-matched)

- complete_fill taking `&Account<Global>` / `&Box<Account<Global>>`, reordered parameters, or a method
  on the curve would all change complete_fill's own body or its register assignment, and so lose its
  matched window. A method on `Global` (`self` first) has the same ABI as today's call. Called as
  `a.global.complete_fill(..)`, its autoderef is computed at the call site, so it behaves like main.

Ledger keys: `0x5b3b0-w12-20a1ae9-cfsig-ir-oracle-gep-in-bb57-bb58-v1`,
`0x5b3b0-w12-20a1ae9-cfsig-typed-global-ref-bound-before-allowed-passed-to-complete-fill-v1`,
`0x5b3b0-w12-20a1ae9-cfsig-allowed-block-returns-bool-and-global-tuple-v1`,
`0x5b3b0-w12-20a1ae9-cfsig-cold-helper-global-of-opaque-to-mir-inliner-v1`.
