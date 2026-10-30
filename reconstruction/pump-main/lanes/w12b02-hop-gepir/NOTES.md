# w12b02-hop-gepir: why the complete_fill `&Global` GEP lands in the call block

Target: 0x5b3b0 `multi_hop_curve::swap_hop`, main 20a1ae9c0 / e61df0357 (programs identical):
18,584 B, ratio 0.99913, 18 differing slots. All 18 come from where `ldxdw r2,[r10-0xb28]; add64 r2,8` is placed.
That pair computes `&Global` (Box<Account<Global>> pointer + 8), the first argument of `complete_fill`. The original has
it at the top of the block that follows the whitelist memcmp test (+0x29f8). Ours has it right before the call (+0x2a78).

## Oracles (no build slot needed)

| oracle | change | bytes | ratio | slots |
|---|---|---:|---:|---:|
| llc on main post-opt IR (`ref_equal` true) | none | 18,584 | 0.99913 | 18 |
| g1: llc | `%_218 = gep %_618,8` moved into bb58 (memcmp block) | 18,584 | **1.0** | **0** |
| g2: llc | moved into bb57 (over-reserves block, after the box load) | 18,584 | **1.0** | **0** |
| g3: llc | moved to the end of bb58 | 18,584 | **1.0** | **0** |
| g4: llc | moved to the top of bb64 (call block) | 18,584 | 0.99913 | 18 |
| P1: pre-opt + SDK `opt default<O3>` + llc | call arg = the whitelist chain's inner `gep box,8` in bb58 | 18,584 | 0.99913 | 18 |
| P2: pre-opt + opt + llc | fresh `gep box,8` in bb57, used by the call | 18,584 | **1.0** | **0** |
| P3: pre-opt + opt + llc | whitelist chain's inner `gep box,8` moved to bb57 and shared with the call | 18,584 | **1.0** | **0** |

On the v5 base, the GEP placement is the only residual left: any post-opt IR that defines the GEP outside the
call block reaches a normalized match. MachineSink then sinks the out-of-block definition to the top of bb64,
and that is the original's slot pattern.

The pre-opt pipeline (rustc `-Cno-prepopulate-passes` capture, then
`toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin/opt -passes='default<O3>'`, then SDK `llc -O3 -mattr=+store-imm,+jmp-ext`)
reproduces main's swap_hop byte for byte.

## Mechanism: which pass moves it

1. **MIR re-projection.** GVN and ReferencePropagation rewrite every deref or reborrow of an SSA `&Global` local back
   to `&((*box).0)`. A function argument is a coercion site, so `complete_fill(global, ..)` reborrows `&*global`.
   That reborrow is re-projected into a fresh `&((*_697).0: Global)` at the call site, in bb64, wherever `global` was bound.
   - The emitted MIR of `let global: &Global = &a.global; .. complete_fill(global, ..)` shows `_219 = &((*_697).0: Global)` in bb64.
   - The binding `_203` stays dead in that MIR; only debuginfo keeps it.
2. **LLVM, when the box pointer is the same SSA value** (`global` binding).
   - The first EarlyCSE merges the call-argument GEP into the whitelist chain's inner `gep box,8` in the memcmp block bb58
     (`gep(gep(box,8),640)`).
   - The first InstCombine then folds the chain into `gep box,648`. That leaves `gep box,8` with one use, in bb64.
   - InstCombine sinks it into bb64 (`tryToSinkInstruction`), because bb64's unique predecessor is bb58.
   - print-after-all trace: CSE'd into bb58 by `EarlyCSEPass`, then sunk to bb64 by the next `InstCombinePass`.
3. **LLVM, on main.** The call site reloads the box pointer (`%_620`). The first EarlyCSE does not merge that load.
   By the second EarlyCSE (after inlining), InstCombine has already folded the whitelist chain, so the call-site GEP
   is created in bb64 and never moves.

## IR shape that matches

The pre-opt IR needs a `gep box,8` in bb57 (before the mayhem branch) that is still live when the first EarlyCSE runs.
The complete_fill call must use it, either directly or because its call-site GEP is CSE'd into it.
InstCombine cannot sink a bb57 definition into bb64, since bb64's unique predecessor is bb58.
A definition in bb58 is always sunk.

## Rust spellings derived from it

- `s10`: `let global: &Global = &a.global;` shares the box pointer with the call's re-projected argument.
  - The whitelist reference is computed before the mayhem test: `let whitelist = &global.whitelist_pda;`.
  - It is compared by reference, `&user != whitelist`. That borrows the local, which makes it non-SSA, so MIR cannot re-project it.
  - The chain's inner `gep box,8` therefore lives in bb57 (oracle P3).
- `s1`: a block-local `#[inline(always)] fn allowed(global:&Global,user,c)->Result<()>` holds the `require!` on line 599.
  - Its cost keeps the MIR inliner off, so LLVM's AlwaysInliner inlines it, and its `&Global` argument is a bb57 GEP (oracle P2).

Results of these builds are below and in the ledger (`0x5b3b0-w12-e61df03-gepir-*`).
