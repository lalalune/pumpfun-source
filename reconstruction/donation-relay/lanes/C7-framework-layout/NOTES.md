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
