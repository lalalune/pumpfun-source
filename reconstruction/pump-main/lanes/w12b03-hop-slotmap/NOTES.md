# w12b03-hop-slotmap: slot map of 0x5b3b0 `multi_hop_curve::swap_hop`

Base: main 20a1ae9c0 (baseline `unstripped.so` from `~/.cache/pumpfun-reconstruction/w11/current-baseline`,
1033/1033 of 1035). swap_hop is 18,584 B (= original), ratio 0.99913, slots_diff 18.

## 1. Every differing slot (`target_metric.py --slots 4000`, `win.py show`)

All 18 slots are contiguous, offsets +0x29f8..+0x2a80 inside the function (0x5dda8..0x5de30 absolute).
They form one residual class.

| slot | original | ours |
| --- | --- | --- |
| +0x29f8 | `ldxdw r2, [r10 - 0xb28]` | `ldxdw r1, [r10 - 0xa48]` |
| +0x2a00 | `add64 r2, 0x8` | `ldxdw r3, [r1 + 0x8]` |
| +0x2a08 | `ldxdw r1, [r10 - 0xa48]` | `ldxdw r1, [r10 - 0xb10]` |
| +0x2a10 | `ldxdw r3, [r1 + 0x8]` | `stxdw [r10 - 0xfd0], r1` |
| +0x2a18 | `ldxdw r1, [r10 - 0xb10]` | `stxdw [r10 - 0xfc8], r9` |
| +0x2a20 | `stxdw [r10 - 0xfd0], r1` | `ldxdw r1, [r10 - 0xb08]` |
| +0x2a28 | `stxdw [r10 - 0xfc8], r9` | `stxdw [r10 - 0xfd8], r1` |
| +0x2a30 | `ldxdw r1, [r10 - 0xb08]` | `ldxdw r1, [r10 - 0xa70]` |
| +0x2a38 | `stxdw [r10 - 0xfd8], r1` | `stxdw [r10 - 0xfe0], r1` |
| +0x2a40 | `ldxdw r1, [r10 - 0xa70]` | `ldxdw r1, [r10 - 0xad0]` |
| +0x2a48 | `stxdw [r10 - 0xfe0], r1` | `stxdw [r10 - 0xfe8], r1` |
| +0x2a50 | `ldxdw r1, [r10 - 0xad0]` | `ldxdw r1, [r10 - 0xab0]` |
| +0x2a58 | `stxdw [r10 - 0xfe8], r1` | `stxdw [r10 - 0xff0], r1` |
| +0x2a60 | `ldxdw r1, [r10 - 0xab0]` | `stxdw [r10 - 0xff8], r6` |
| +0x2a68 | `stxdw [r10 - 0xff0], r1` | `ldxdw r1, [r10 - 0xac8]` |
| +0x2a70 | `stxdw [r10 - 0xff8], r6` | `stxdw [r10 - 0x1000], r1` |
| +0x2a78 | `ldxdw r1, [r10 - 0xac8]` | `ldxdw r2, [r10 - 0xb28]` |
| +0x2a80 | `stxdw [r10 - 0x1000], r1` | `add64 r2, 0x8` |

Class **GEP placement (18/18 slots)**: the two instructions `ldxdw r2,[r10-0xb28]; add64 r2,8` (complete_fill's
`&Global` argument = global Box pointer + 8, the Box pointer being spilled at -0xb28) are the first two instructions
of the complete_fill block in the original, right after the whitelist `memcmp` test (`jeq r0,0,-0xd7` at +0x29f0).
Ours computes them just before `mov r1,r10; add r1,-0x6d0; mov r5,r10; ldxdw r4,[..]; call complete_fill`.
The 16 instructions between are identical and only shifted by two slots.

There is **no other class on main**. In particular the "r1/r2 load order of the shared Err store at the line-599
`require!`" class does not exist on main: it showed up only in w9r2-swaphop-frame's chained IR oracle on 2abb99ccb
(edits 1-4 there approximated source changes that later landed in a different form). Lanes that look for it on
main (errload) are looking for a residual that main does not have.

## 2. Minimal IR edit (llc oracle on main's post-opt IR, ~5 s)

IR: main's post-opt module (an `--emit=llvm-ir` build of 20a1ae9c0 gives a `candidate.so` identical to the baseline).
`oracle/orc.py` (adapted from w9r2-swaphop-frame) runs `llc -O3 -mattr=+store-imm,+jmp-ext` on it; unedited it
reproduces main's swap_hop byte for byte (`ref_equal: true`).

In main's IR the argument is `%_218 = getelementptr inbounds i8, ptr %_618, i64 8` in `bb64` (the complete_fill
block; its only predecessor is the memcmp block `bb58`). `%_618` (`a.global`'s Box pointer) is loaded in `bb57`
(the `base > reserves` block that also copies the user key and tests `is_mayhem_mode`).

| edit (`oracle/gepx.py`, `POS=`) | bytes | ratio | slots_diff |
| --- | ---: | ---: | ---: |
| none (main) | 18,584 | 0.99913 | 18 |
| `%_218` moved to bb57, right after the `%_618` load (`b57top`) | 18,584 | **1.0** | **0** |
| `%_218` moved to the end of bb57 (`b57end`) | 18,584 | **1.0** | **0** |
| `%_218` moved to the top of bb58 (`b58top`) / after the memcmp icmp (`b58end`, = `gep58.py`) | 18,584 | **1.0** | **0** |
| `%_618` load and `%_218` both moved into bb56 (before the `if base > reserves`) | 18,592 | 0.98579 | - |

So defining the GEP in any block that strictly dominates bb64, after the `%_618` load and inside the
`base > reserves` arm, gives the whole function. Mechanism: MachineSink sinks the GEP into bb64 and inserts it at the
block top; greedy then reloads `%_618` from -0xb28 right there (`ldxdw r2,[r10-0xb28]; add64 r2,8`). A GEP defined in
bb64 itself is placed by the DAG scheduler next to the call (main).

## 3. Why the source bindings tried so far are byte-identical

- `let global = &*a.global` is `&Account<Global>`, so the `+8` (Account::deref) is done by deref coercion at the
  complete_fill call.
- `let global: &Global = &a.global; .. complete_fill(global, ..)` (w12b04 v1, ledger
  `0x5b3b0-w12-e61df03-global-ref-Global-bind-before-allowed-into-complete-fill-v1`): its print-changed dump shows the
  re-projection happens in **MIR**, not LLVM: after EarlyCSE `%global = gep %_619, 8` sits in bb57 with **no uses**, and
  the complete_fill argument is a fresh `%_219 = gep %_619, 8` emitted by rustc in bb64. The `&T` argument gets a
  coercion reborrow `&(*global)`, and MIR ReferencePropagation (rustc 1.79) collapses it into `&((*box_ptr).0)` at the
  call site because `global` is an SSA local pointing at a stable place. The GEP is then in bb64 with the call, so ISel
  places it as on main.

## 4. Source trials (this lane)

| trial | source (lines 599-600) | result |
| --- | --- | --- |
| s2 | `let global: &Global = &a.global; let allowed = {..global.whitelist_pda}; ..` and `complete_fill(&global, ..)` (borrow the binding so it is not SSA for ReferencePropagation) | byte-identical to main (`candidate.so` sha 4eb9dc9e…, 0.99913/18). Its post-opt IR differs from main only by the GEP's position inside bb64: it sits at the very top, before `lifetime.start`, which is InstCombine's sink point, as in w12b04 v1. So the extra borrow does not keep the reference opaque. This is consistent with the call-site reborrow still being re-derived from the box pointer, after which EarlyCSE/InstCombine move that GEP to the top of bb64; this build's MIR was not kept, so the MIR pass is not confirmed. |

Ledger: `0x5b3b0-w12-20a1ae9-slotmap-gep-only-oracle-v1` (analyzed), `0x5b3b0-w12-20a1ae9-refprop-borrowed-global-binding-v1` (rejected).

## 5. Outcome

w12b09-hop-hillclimb (#2766) found the working form: it carries the `&Global` out of the whitelist block in a tuple
field, `let (allowed, global) = { let global: &Global = &a.global; ..; (.., global) }`, and passes `complete_fill(global, ..)`.
`Use(Copy(_tup.1))` is not a local, so ReferencePropagation cannot see through it, and the GEP stays in the
`base > reserves` block. This is the IR the oracle above asks for, and it gives swap_hop a normalized and raw match
(1034/1034, zero losses). No swap_hop residual is left for this angle.
