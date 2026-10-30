# w12b01-hop-gep: swap_hop `&Global` complete_fill argument by source spelling

Target: 0x5b3b0 `multi_hop_curve::swap_hop` (`programs/pump/src/multi_hop_curve_swap.rs`), pinned at 18,584 B.
Base: main 20a1ae9c0 (baseline 0.99913, 18 slots; Pump Main 1033/1033 of 1035).

**Status:** swap_hop is a normalized and raw match on main since #2766 (w12b09, the
`(allowed, global)` tuple spelling, merged as 0b5fc0d5d). This lane reached the same binary in
parallel with the two helper spellings below. Neither was landed: after #2766 they are neutral.
On main 70f27048e, the `v3cc` spelling in place of the tuple (`edits/v3cc_on_tuple.py`) builds
the same candidate as main (sha cc795ce731592a48): 1034/1034, no losses, no gains. It is offered
as the more ordinary spelling, because it reuses an existing helper instead of returning a
reference out of a block. Merging it would need a steward's `land.py --allow-neutral`.

## Result

| build | change | bytes | ratio | slots | normalized / raw | losses | candidate sha |
|---|---|---:|---:|---:|---|---|---|
| main 20a1ae9c0 | - | 18,584 | 0.99913 | 18 | 1033 / 1033 | - | 4eb9dc9e542e9b9a |
| `v1` | `let global: &Global = &a.global;` before the allowed block, `complete_fill(global, ..)` | 18,584 | 0.99913 | 18 | byte-identical | - | 4eb9dc9e542e9b9a |
| **`v3cc`** | **line 599 `let allowed = crate::trade::v3_can_cross(&a.global,c,&a.user.key());` (`v3_can_cross` made `pub(crate)`)** | **18,584** | **1.0** | **0** | **1034 / 1034** | **none** | **cbd9bf08d09967f7** |
| `wlok` | line 599 `let allowed = whitelist_ok(&a.global,a.user.key(),c);` with a plain module-level `fn whitelist_ok(global:&Global,user:Pubkey,curve:&BondingCurve)->bool` | 18,584 | 1.0 | 0 | 1034 / 1034 | none | cbd9bf08d09967f7 |

Both spellings give swap_hop a normalized and raw match with zero losses (`measure.sh` against
baseline 20a1ae9c0; admin_cto unchanged at 0.43919 / 27,400 B). They build the same binary as the
other w12 spellings that reached the match at the same time: the `(allowed, global)` tuple of
w12b09 (#2766), the local `whitelist_ok(&Global, &Pubkey, &Account<BondingCurve>)` helper of
w12b07 (#2780), the 1-tuple of w12b14 and the `#[cold] fn global_of` of w12b06. The bytes are
identical, so the choice between them is only about which source is the most plausible.
`v3cc` reuses the helper that `trade_v3`'s buy already calls for the same check (whether a buy
may cross the curve's real reserves), so it needs no new item. The diff is in `edits/v3cc.py`:

```rust
// multi_hop_curve_swap.rs line 599
let allowed = crate::trade::v3_can_cross(&a.global,c,&a.user.key()); require!(allowed,PumpError::NotEnoughTokensToBuy);
// trade_v3.rs line 432
pub(crate) fn v3_can_cross(global:&Global,curve:&BondingCurve,user:&Pubkey)->bool{!v3_fee_exempt(global,curve,user)}
```

## Mechanism (three layers)

1. **llc / MachineSink.** The original computes `ldxdw r2,[r10-0xb28]; add64 r2,8` at the top of the
   complete_fill block, right after the whitelist memcmp test. llc puts it there whenever the IR
   defines `gep %box, 8` in the over-reserves block bb57 or the memcmp block bb58: MachineSink sinks
   the ADD to the top of the call block bb64. Oracle on main's post-opt IR (`edits/g57.py`,
   `edits/g58.py`): both give 1.0 / 0 slots. The GEP was the only residual on main.
2. **opt / InstCombine sinking.** InstCombine sinks an instruction into its single user's block only
   when that block's unique predecessor is the instruction's block. In rustc's pre-opt IR bb64's
   only predecessor is already bb58 (MIR jump threading resolved the `&&`/`require!` join). So a
   `gep +8` in bb58 is sunk into bb64 by the first InstCombine. A `gep +8` in bb57 cannot be sunk
   and survives to llc. Pre-opt oracle (rustc `-Cno-prepopulate-passes` capture, hybrid144
   `opt -O3`, llc): call argument = a bb57 GEP gives 1.0 / 0 (`edits/pre_g57.py`); call argument =
   bb58's `%666` (the whitelist's +8 GEP) gives 0.99913 / 18 (`edits/pre_g58.py`).
3. **MIR / ReferencePropagation.** `complete_fill(global, ..)` with `global: &Global` is a
   coercion site. With distinct lifetimes, typeck inserts a reborrow `&*global`. ReferencePropagation
   sees through the SSA `&((*box_ptr).0)` binding and rewrites the reborrow into a fresh
   `&((*box_ptr).0: Global)` in the call block, so the binding in bb57 becomes dead. Every
   `&PLACE`-derived local behaves the same way, which is why hoisted bindings were byte-identical
   (`v1`; optimized MIR in `t/v1/module.mir`: bb57 `_203 = &((*_697).0)` dead, bb64
   `_219 = &((*_697).0)` passed to the call).

**What works:** the bb57 `&Global` must be an argument of a call that the MIR inliner skips but
LLVM inlines. A non-generic local fn without `#[inline]` is MIR-inlined only if it is
cross-crate-inlinable, which requires zero calls in its optimized MIR. The Pubkey compare leaves
a `raw_eq` intrinsic call terminator, so `v3_can_cross` and `whitelist_ok` stay calls in MIR.
The `&a.global` argument is then materialized in bb57, before the mayhem test, as in the original,
which also loads `a.global` first there. The CGSCC inliner inlines the helper. EarlyCSE (with
MemorySSA) merges the two `a.global` box loads and replaces the call-site `gep +8` with the bb57
one. InstCombine folds the whitelist address to `+0x288` and cannot sink the remaining `+8` GEP.

## Tools (`tools/`)

- `capir.py --src <crate> --work <w> --out <o> [--mir] [--extra=-Cno-prepopulate-passes]`: an
  identity build that also emits `module.ll` (post-opt, or pre-opt with the extra flag) and
  optionally `module.mir`. It goes through fastbuild's build slots. Its candidate.so equals
  measure.sh's.
- `orc.py <module.ll> [--edit e.py] [--opt]`: extracts swap_hop, runs `opt -O3` first with
  `--opt` (pre-opt modules, about 90 s on this loaded machine), runs llc and prints
  bytes/ratio/slots against the original window. It reproduces main exactly (0.99913 / 18) from
  both the post-opt and the pre-opt captures.
- `gepwhere.py <sh.ll>`: prints the block that defines complete_fill's `&Global` argument and the
  call block's predecessors. Use it to tell at once whether a spelling moved the GEP.
- `trial.sh NAME edit.py [W]`: copies the crate, applies the edit (line count kept), runs a capture
  build, then prints target_metric, the oracle and gepwhere.

## Ledger keys

- `0x5b3b0-w12-20a1ae9-refprop-rematerializes-global-reborrow-at-call-v1` (analyzed)
- `0x5b3b0-w12-20a1ae9-preopt-oracle-gep8-bb57-vs-bb58-v1` (analyzed)
- `0x5b3b0-w12-20a1ae9-allowed-via-trade-v3-can-cross-helper-v1` (raw-match)
- `0x5b3b0-w12-20a1ae9-allowed-via-plain-whitelist-ok-helper-v1` (raw-match)
