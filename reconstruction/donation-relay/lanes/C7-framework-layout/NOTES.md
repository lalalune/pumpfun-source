# C7-framework-layout notes

Base: origin/swarm/w20-relay-scout at dfcbfc6ae (545 of 571, 776,384 B, 0.91137, zero losses).

## 0x1590, third with_values instance: matched (normalized)

The target's three instances: 0x638 (1992 B: swap_observed, admit handler, exact distribution),
0xe00 (1936 B: the bps-sum sites, `(u32, u32)` with the second argument const-propagated), 0x1590 (1992 B: 13 try_accounts
closures and __idl_set_buffer, Anchor's `(usize, usize)` space and capacity checks). 0x638 and 0x1590 have identical listings, callees
included, because `usize` and `u64` both format through `core::fmt::num::imp::<impl u64>::_fmt`, so they are `(u64, u64)` and `(usize, usize)`.

On the scout tip `(u64, u64)` had one caller, swap_observed, and LLVM inlined it there. The target's admit handler has a with_values on the
line 83 mismatch (`InputAmountMismatch`, 0x1785, line 0x53). Writing it as `.with_values((amounts.gross_amount, amount))` gives the
instance a second caller, it stops being inlined and the third instance appears: 546 of 571, 778,376 B, 0.91371, zero losses, gain 0x1590.

## `#[access_control]`: the reversed wrappers

The target's `relay::*` wrappers are not in `#[program]` order: `donate_*`, recover, then entrypoint and the allocator shims, then
exact_after, exact_non_swap, non_swap, after, just_swap, swap_then_distribute, close, admit, which is reverse IDL order. Those eight are
exactly the instructions that start with `check_relayer`, and `#[access_control(check_relayer(&ctx.accounts.signer))]` expands to that same
statement. Written that way they get their DefIds when the attribute expands, later and in reverse, and the wrappers come out in the target's order.
No function changed: no gains, no losses, and their symbol hashes are unchanged. Order breaks on the Mac went from 60 to 40.

## Direct `borsh` references: the `Unexpected length of input` string

This is crate link order, not a symbol hash. The target's rlibs run `solana_pubkey, borsh, solana_sha256_hasher, serde_core, std`. Ours ran
`solana_pubkey, solana_sha256_hasher, serde_core, borsh, std`, because `codec/wire.rs` said `use borsh::BorshDeserialize` and so loaded `borsh`
before `anchor_lang`: rustc allocates crate numbers on first reference, and the link line is the reverse of the postorder over those numbers.
With `use anchor_lang::prelude::*` and `AnchorDeserialize`/`AnchorSerialize` there, all 27 rlibs on the link line are in the target's relative order for
the crates checked and the string leaves the `.rodata` diff. No gains, no losses.
