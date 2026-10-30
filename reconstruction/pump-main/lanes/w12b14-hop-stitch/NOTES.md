# w12b14-hop-stitch: swap_hop (0x5b3b0) integrator / stitcher

Target: `multi_hop_curve::swap_hop` (`programs/pump/src/multi_hop_curve_swap.rs`), pinned at 18,584 B.
Base: main 20a1ae9c0 (baseline sha 8cd7695c…), swap_hop 0.99913 / 18 slots.

## Finding 1: the GEP move alone is a full match on current main (IR oracle)

The brief's 0.99956/2 oracle number came from lane w9r2-swaphop-frame on an older base. On the current
main post-opt IR (`--emit=llvm-ir`, llc -O3 +store-imm,+jmp-ext reproduces main's swap_hop bytes), moving
only the complete_fill `&Global` argument GEP out of the call block gives **ratio 1.0, 0 slots, 18,584 B**:

| edit on main post-opt IR | bytes | ratio | slots |
| --- | ---: | ---: | ---: |
| none (reproduces main) | 18584 | 0.99913 | 18 |
| `%_218 = gep %_618, 8` moved into bb58 after `%_870` (memcmp block) | 18584 | 1.0 | 0 |
| moved into bb58 after the memcmp icmp | 18584 | 1.0 | 0 |
| moved into bb57 right after `%_618 = load` (box ptr load, before user key copy) | 18584 | 1.0 | 0 |
| moved to the top of bb64 (before `lifetime.start(112, %_217)`) | 18584 | 0.99913 | 18 |

So the r1/r2 Error-reload order at line 599 is already right on main; the GEP placement is the only residual.
llc's MachineSink sinks a cross-block GEP to the top of the call block (orig `ldxdw r2,[r10-0xb28]; add64 r2,8`
right after the memcmp `jeq`). A GEP that is already in the call block is scheduled next to the call.
InstCombine can only sink a single-use instruction into a user block whose unique predecessor is its own
block. bb64's unique predecessor is bb58, so a GEP in bb57 survives opt. A GEP in bb58 would be sunk.

## Finding 2: why `let global: &Global = &a.global` binding attempts are byte-identical

Captured MIR (`--emit=mir`) of the variant `let global: &Global = &a.global; ... complete_fill(global, ...)`
(the w12b04 v1 trial, byte-identical to main):

```
bb57: _203 = &((*_697).0: Global);          // the binding, in the over-reserves block
bb58: _869 = &((((*_697).0: Global).16: Pubkey).0: [u8; 32]);   // whitelist, rebuilt from _697
bb64: _219 = &((*_697).0: Global);           // complete_fill arg, rebuilt from the Box raw ptr _697
      _218 = complete_fill(move _219, ...)
```

The call argument is a reborrow `&*global` (coercion site). MIR **ReferencePropagation** collapses
`&(*_203)` to `&((*_697).0)`, which rebuilds the address at the call site. `_203` is then dead, so
the GEP is back in the call block before LLVM sees it. Any spelling where the argument is a reborrow of an
SSA reference local (or a copy of one) is rebuilt the same way.

To keep the GEP in bb57, the argument must reach the call through something ReferencePropagation cannot see
through: a field of an aggregate (`(t.0)`), a borrowed (non-SSA) local, or an enum payload.

## Finding 3: LLVM keeps an early GEP (pre-opt oracle)

Pre-opt capture (`-Cno-prepopulate-passes`) of the w12b04 v1 variant, then the hybrid144 `opt -passes=default<O3>`
and llc:

| pre-opt edit | bytes | ratio | slots |
| --- | ---: | ---: | ---: |
| none (reproduces the real build of that variant = main) | 18584 | 0.99913 | 18 |
| complete_fill arg `%_219` (bb64) replaced by the dead bb57 `%global` GEP | 18584 | 1.0 | 0 |

So once MIR hands LLVM the early GEP as the argument, no LLVM pass moves it.

## Source trials (measure.sh, base 20a1ae9c0 = e61df0357 programs/)

| trial | spelling (line 599-600) | swap_hop | normalized/raw | sha |
| --- | --- | --- | --- | --- |
| v1tuple | `let (global,): (&Global,) = (&a.global,); let allowed = { let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda };` + `complete_fill(global,..)` | **1.0 / 0 slots, 18,584 B, normalized+raw match** | 1034/1034, 0 losses | cbd9bf08d09967f7 |
| v2refref | `let global: &Global = &a.global;` + `complete_fill(*&global,..)` | 0.99913 / 18 (byte-identical to main) | 1033/1033 | 8cd7695c3fc638fc |

v1tuple's binary is identical to w12b09's PR #2766 (`let (allowed, global) = { ...; (cond, global) };`), which
reached the same match first and is being landed by that lane. Either spelling works; #2766's is the more
natural one. `*&global` does not help: the local stays SSA for ReferencePropagation.

Ledger keys: `0x5b3b0-w12-20a1ae9-stitch-postopt-gep8-placement-4way-v1`,
`0x5b3b0-w12-20a1ae9-stitch-preopt-opt-o3-call-arg-bb57-global-v1`,
`0x5b3b0-w12-20a1ae9-stitch-mir-refprop-rebuilds-global-reborrow-v1`,
`0x5b3b0-w12-20a1ae9-stitch-one-tuple-global-binding-into-complete-fill-v1`,
`0x5b3b0-w12-20a1ae9-stitch-global-binding-deref-of-ref-arg-v1`.

## Outcome

w12b09's PR #2766 landed through land.py as 0b5fc0d5d. The baseline at main 70f27048e has swap_hop at
**1.0 / 0 slots / 18,584 B, normalized and raw equal**, and Pump Main at 1034/1034 (normalized/raw) of
1,035. The only unmatched window left is `admin_cto::execute` (0x22a10). The stitch angle is done: there was
one residual, and two lanes found it independently with byte-identical binaries (sha cbd9bf08…), so nothing
needed combining.
