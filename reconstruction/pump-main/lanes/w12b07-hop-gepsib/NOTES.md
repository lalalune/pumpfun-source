# w12b07-hop-gepsib: swap_hop &Global GEP via a sibling idiom

Target: 0x5b3b0 `multi_hop_curve::swap_hop` (`programs/pump/src/multi_hop_curve_swap.rs`), pinned at 18,584 B.
Base: main 20a1ae9c0 (swap_hop 0.99913, 18 differing slots; Pump Main 1033/1035 normalized, 1033 raw).

**Status:** not landed. PR #2780 was closed as superseded by #2766 (w12b09-hop-hillclimb), which
landed first through land.py with the same result. #2766 routes a `&Global` binding through a
tuple so that ReferencePropagation cannot see it. This lane reaches the same bytes with a
different spelling: a plain helper that takes `&Global`, as the byte-matched siblings do.
Branch `swarm/w12b07-hop-gepsib` keeps this spelling as an alternative. Both spellings build
the same swap_hop window, normalized and raw equal, at 18,584 B.

## Result

| build | swap_hop bytes | ratio | slots | normalized_equal | raw_equal |
| --- | ---: | ---: | ---: | --- | --- |
| main 20a1ae9c0 | 18,584 | 0.99913 | 18 | no | no |
| this lane (whitelist_ok helper) | 18,584 | 1.0 | 0 | yes | yes |

Full program (measure.sh against `$BASE` = main 20a1ae9c0): 1034/1035 normalized, 1034 raw,
0 normalized losses, 0 raw losses, gains `0x5b3b0` (normalized and raw). Unstripped sha256
`cbd9bf08d09967f71921acaf2b89ad576abd96654a192834a268cd1e18f59269`. admin_cto is unchanged
(0.43919, 27,400 B).

## Change

```rust
fn whitelist_ok(global: &Global, user: &Pubkey, curve: &Account<BondingCurve>) -> bool { !curve.is_mayhem_mode && *user != global.whitelist_pda }
...
let allowed = whitelist_ok(&a.global,&a.user.key(),c); require!(allowed,PumpError::NotEnoughTokensToBuy);
```

The helper sits on a blank layout-pad line next to `pool_before`/`complete_fill`, and the
line-599 `require!` keeps its line. The helper has no line-dependent sites, and LLVM inlines it
(single call site), so the program gains no symbol.

## Mechanism

The residual was the placement of `ldxdw r2,[r10-0xb28]; add64 r2,8`, the complete_fill `&Global`
argument. The original computes it at the top of the complete_fill block, right after the
whitelist memcmp test. Ours computed it just before the call.

1. IR oracle on main's post-opt IR (`llc`, the same pipeline as the identity build): defining
   `%_218 = gep %_618, 8` in bb57 (the over-reserves block, right after the `a.global` Box load)
   or in bb58 (the memcmp block) gives a full masked match, 1.0 with 0 slots. MachineSink sinks
   the def into the top of the complete_fill block (bb64), which is what the original shows.
2. In source, the GEP must survive `opt` outside bb64:
   - A `&Global` binding does not survive: MIR ReferencePropagation re-derives `(*box).account`
     at each use, so the binding is dead. See w12b04/w12b08 in the ledger.
   - A GEP in bb58 is sunk by InstCombine, because bb64's unique predecessor is bb58.
   - A GEP in bb57 is not sunk by InstCombine, because bb64 is not a direct successor of bb57.
3. Sibling idiom: byte-matched Pump Main handlers that test the global and then pass `&global`
   to a helper show the same block-top `reload; add 8` in the original:
   - `trade::v3_trade_fees` (+0x80120): `get_fees(&a.global, ..)` after the whitelist test.
   - `create_v2::execute` (+0x21e60): `nested_create::walk(.., &a.global)` after
     `pump_quote::global_quote(mint, &a.global)`.
   - `trade::v3_execute_buy` (+0x84068): `accrue_fees(&a.global, ..)`.

   In create_v2 and trade_v3, the global test is a plain helper that takes `&Global`
   (`global_quote`, `v3_can_cross`). In rustc 1.79 a local non-generic fn whose MIR contains a
   call is not cross-crate-inlinable, so the MIR inliner keeps it as a call. The deref coercion
   `&a.global -> &Global` is therefore a real call argument, materialized in the test block
   (bb57). LLVM inlines the helper and CSEs complete_fill's later `gep box,8` into that argument.
   The GEP then stays in bb57 through InstCombine, and MachineSink puts it at the top of the
   complete_fill block.

Shown in `var/b2/out/fn.ll`: `%_204 = gep %_619, 8` is defined in the over-reserves block and
used directly by the complete_fill call.

## Trials

| key | change | result |
| --- | --- | --- |
| oracle-gep-def-overreserves-bb57 | llc: move `%_218` to bb57 / bb58 | 1.0 / 0 slots (both) |
| whitelist-ok-helper-takes-Global | plain helper `whitelist_ok(&a.global,&a.user.key(),c)` | swap_hop 1.0 / 0 slots, raw equal |

b1 (a typed `&Global` binding passed to complete_fill) was dropped. It duplicates w12b04/w12b08
(byte-identical to main).

Ledger keys: `0x5b3b0-w12-20a1ae9-oracle-gep-def-overreserves-bb57-v1`,
`0x5b3b0-w12-20a1ae9-whitelist-ok-helper-takes-Global-v1`.

## Reusable rule (for admin_cto and other windows)

In this toolchain (rustc 1.79), a local, non-generic, plain fn (no `#[inline]`) whose
optimized MIR contains any call (an intrinsic such as `raw_eq` counts) is not
cross-crate-inlinable. The MIR inliner therefore never inlines it. Any reference argument
built at its call site (a deref coercion such as `&a.global -> &Global`, or a field
borrow) becomes a real MIR value in the calling block. ReferencePropagation and GVN cannot
re-derive that value at later uses, and LLVM still inlines the helper.

Use this when the original materializes an address or GEP in an earlier block than its use.
Placement rules:
- InstCombine sinks a value whose only users sit in the unique-predecessor successor block.
- InstCombine does not sink a value whose users are two or more blocks down.
- In the second case, MachineSink places the value at the top of the use block.
