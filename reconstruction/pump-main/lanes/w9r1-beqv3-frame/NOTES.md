# w9r1-beqv3-frame: buy_exact_quote_in_v3 (0x1489f8)

Target: `0x1489f8` `trade::buy_exact_quote` body (programs/pump/src/trade_v3.rs), 7,856 B.

Residual on main 255a0fd2e: same size, 10 differing slots, tail stack-slot swap
(original spill slots at r10-0x148..0x160 and temporaries at -0x80..-0x90; ours swapped).

## Result

The fix from open PR #2377 (wave 7, `w7r1-buyexactquote-hillclimb`, built on fb25fce02)
still closes the window after #2168 moved the handler to its `#[program]` position.
This branch is that change rebased onto current main and re-verified.

| metric | main 255a0fd2e | this branch |
| --- | --- | --- |
| target ratio / slots_diff / bytes | 0.9895 / 10 / 7856 | normalized match / 0 / 7856 |
| official normalized / raw | 1031 / 337 | 1032 / 337 |
| gains / losses / raw losses | | 0x1489f8 / none / none |
| unstripped sha256 | 9467216956a4a1da... | 6de8bcdcb64b4eae986d0e75535ce163cc5307351f77f68eeb4bd31dddd203ef |

ELF size unchanged (2,665,736 B); `fit_owned` is inlined, so `ordered.ld` needs no regeneration.
Raw stays at 337 because the target still sits after the admin_cto/swap_hop -96 B shift.

## Mechanism

`Some(post)=>fit_owned(.., post, ..)`: moving `post` by value into a plain (non-`#[inline]`)
forwarding helper makes the match binding SSA in MIR; the address-taken `PostComplete` alloca
belongs to the helper and receives lifetime markers from the LLVM inliner at the call site.
StackColoring then no longer merges `fees` (the `TradeFees` borrowed by `v3_emit_buy`) into
the 64-byte group, so the `v3_execute_buy` result returns to r10-0x90 and the spill slots to
-0x148..-0x160. The helper only forwards to `fit_post_complete`, so behaviour is unchanged.

Ledger: attempt c9325c7a8c0442908af68ca317a59427
(`0x1489f8-main-255a0fd-pr2377-fit-owned-rebase-v1`).
