# w12b02-hop-gepir: pass-level trace of the swap_hop complete_fill `&Global` GEP

Target: 0x5b3b0 `multi_hop_curve::swap_hop`. Base: main 20a1ae9c0 / e61df0357 (programs identical),
18,584 B, ratio 0.99913, 18 differing slots, all from the placement of `ldxdw r2,[r10-0xb28]; add64 r2,8`.
That pair is the `&Global` (Box<Account<Global>> pointer + 8) passed to `complete_fill`.

**Status: resolved on main by #2766** (lane w12b09-hop-hillclimb, tuple spelling `let (allowed, global) = {..; (cond, global)}`):
swap_hop now has a normalized and raw match at 18,584 B, 1034/1034.

This lane traced the same residual IR-first. The w12b05 and w12b09 notes on main already cover the llc oracle and
the MIR ReferencePropagation cause. What this note adds:
- which LLVM passes move the GEP, in both the main case and the shared-box case;
- pre-opt oracles run through the full `opt` pipeline.

## Oracles

| oracle | change | bytes | ratio | slots |
|---|---|---:|---:|---:|
| llc on main post-opt IR (`ref_equal` true) | none | 18,584 | 0.99913 | 18 |
| llc g1 / g3 | `%_218 = gep %_618,8` moved into bb58 (after the whitelist gep / before the `br`) | 18,584 | 1.0 | 0 |
| llc g2 | moved into bb57, right after the `%_618` box load | 18,584 | 1.0 | 0 |
| llc g4 | moved to the top of bb64 (call block) | 18,584 | 0.99913 | 18 |
| pre-opt P1 | call arg = the whitelist chain's inner `gep %_618,8` in bb58 | 18,584 | 0.99913 | 18 |
| pre-opt P2 | fresh `gep %_618,8` in bb57, used by the call | 18,584 | **1.0** | **0** |
| pre-opt P3 | whitelist chain's inner gep moved to bb57 and shared with the call | 18,584 | **1.0** | **0** |

The pre-opt pipeline has three steps:
1. a rustc `-Cno-prepopulate-passes` capture;
2. `toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin/opt -passes='default<O3>'` on the whole module;
3. SDK `llc -O3 -mattr=+store-imm,+jmp-ext`.

It reproduces main's swap_hop byte for byte (`ref_equal` true), so pre-opt IR edits are measured through every LLVM pass.

## Which pass moves it (opt `-print-after-all -filter-print-funcs=<swap_hop>`)

**Main (`complete_fill(&a.global, ..)`).**
- rustc's IR reloads the Box pointer at the call (`%_620 = load ptr, ptr %a` in bb64) and computes `%_218 = gep %_620,8` there.
- The whitelist test has its own chain in bb58: `gep(gep(%_618,8),640)`.
- EarlyCSE #1 does not merge `%_620` into `%_618`.
- InstCombine #1 folds the bb58 chain into `gep %_618,648`.
- EarlyCSE #2, after inlining, merges the loads, but no `gep %_618,8` is left to CSE with.
- The GEP never leaves bb64.

**`let global: &Global = &a.global; .. complete_fill(global, ..)`** (byte-identical to main; same as w12b04 v1 and w12b06):
- In MIR, ReferencePropagation rewrites the call-site reborrow to `_219 = &((*_697).0: Global)` in bb64.
  It also rewrites the whitelist read to a projection from `_697`, which leaves the binding `_203` dead.
- Both GEPs now share the box SSA value, so EarlyCSE #1 merges the call-arg GEP into the whitelist chain's inner
  `gep box,8` in bb58.
- InstCombine #1 folds the chain to `gep box,648`. It then sinks the single-use `gep box,8` to the top of bb64
  (`tryToSinkInstruction`), because bb64's unique predecessor is bb58.

**Matching shape.** A `gep box,8` defined in bb57, before the mayhem branch, and used by the call.
- InstCombine cannot sink it: it only sinks into a block whose unique predecessor is the defining block, and bb64's is bb58.
- MachineSink later walks the `add` from bb57 to bb58 to the top of bb64. That is the original's slot pattern.
- #2766's tuple field hides `global` from ReferencePropagation, so its bb57 GEP is the call argument.

Traces and oracles: `~/.cache/pumpfun-reconstruction/lanes/w12b02-hop-gepir/trace/{base,e1}.trace.gz` and `orc/`.

## Spellings not finished

Two source trials were cancelled once #2766 landed, before they were measured:
- `s10`: whitelist reference bound in bb57 and compared as `&user != whitelist`, to make it non-SSA.
- `s1`: a `#[inline(always)] fn allowed(global,user,c)->Result<()>` holding the line-599 `require!`, kept out of MIR inlining by its cost.

`s10`'s borrow is probably undone before GVN, by ReferencePropagation followed by SimplifyLocals. This matches the
byte-identical results of w12b03 (`complete_fill(&global,..)`) and w12b14 (`*&global`), but it was not built here.

Ledger keys: `0x5b3b0-w12-e61df03-gepir-*`.
