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

## Integration, Mac route

This branch now merges C1 to C6 at their tips of 08:43. Conflicts resolved: `bridge_handlers.rs` stays deleted (C5 moved it, and the with_values edit from C3 and C7 is in
C5's admit module); `codec/wire.rs` keeps the anchor derives, plus C2's `Copy` on `ShareType`.
Result on the Mac route: 569 of 571 functions, 851,168 of 851,888 B, 0.99915, zero losses, strict 550. `.rodata` is byte-equal to the target
(23,104 B). `.dynstr` is equal. `.data.rel.ro` (8,880 B) and `.rel.dyn` (43,536 B) have the target's sizes but differ in addresses. `.text` is 720 B short, which is
exactly the two Linux-only functions 0xb3278 and 0xbcac0.

## Integration, Linux route (natural order, no script)

The same merged source at d60cb0935 on `linux-build.sh`, official v1.54 archive, 140 s: 571 of 571 functions, 851,888 of 851,888 B, ratio 1.0, strict 549, same_address 433.
Candidate 929,176 B, which is the deployed size. `.rodata`, `.dynsym` and `.dynstr` are byte-equal. `.data.rel.ro` and `.rel.dyn` hold function addresses and differ only through
`.text` order: `relchk.py` finds all 1,110 words of `.data.rel.ro` equal once pointers are compared by section and through the refined pairing (70 text, 400 rodata, 2 data).
So 0xb3278 and 0xbcac0 match on Linux as predicted, and `.text` order is what is left.

Not byte identity yet: `whole_elf_equal` is false on this natural-order build.

## mkorder2.py: why relay.compare's pairing is not enough for the script

`relay.compare` pairs by normalized body, first free. Identical bodies exist (the `(u64, u64)` and `(usize, usize)` with_values, two Signer::try_accounts, two Account::reload, finish_grow, and more), and a wrong pair
scores the same but puts the instance at the other's address. That is C4's "strict is lower on Linux". `mkorder2.py` resolves such groups from paired callers' k-th calls, paired callees, data content and
`.data.rel.ro` slots. On the Linux build it pairs 571 of 571 with zero conflicting callees. 8 pairs differ from relay.compare's. One group stays ambiguous: `<&T as Display>::fmt` at 0xaccf0 and 0xb84b0, which are in different rlibs and pair in address order.

## Whole ELF: byte-identical at source d60cb0935, on the Linux route with an ordered link

`cmp` of `candidate.so` with `relay/live/deployed.elf` reports no difference. Both are 929,176 B, sha256 `0985c3a02b9f02035e677b99d63b42b0484d0734e3e66e5e36fd4509dd600624`.
571 of 571 functions, strict 571, same address 571, raw same address 571. All six sections compared by `measure` are equal.

The script is `ordered.d60cb0935.ld`: 571 `.text` section selectors in the deployed order, generated by `mkorder2.py` from that source's natural Linux link map, and otherwise the stock layout.
It is target-derived link order, as the old packet's `ordered.ld` was. It contains no machine code. The natural-order link of the same source is not identical (same_address 433), so this identity depends on the script.
The source was scanned for asm!, global_asm!, include_bytes!, include_str!, black_box, volatile access, intrinsics, link_section, no_mangle and .incbin: no hits. There is no build.rs and no .cargo directory.

This run reused a persistent `/target` for dependency rlibs. The final crate itself was recompiled. A cold check on the tip is recorded below when it finishes.
