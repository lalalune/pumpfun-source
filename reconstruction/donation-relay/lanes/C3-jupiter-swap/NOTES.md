# C3-jupiter-swap lane notes

Base: `origin/swarm/w20-relay-scout` (dfcbfc6ae), 545 of 571, 776,384 B, 91.137%.

## invoke_jupiter (0x11668): exact

The metas closure is a struct literal, not `AccountMeta::new` / `new_readonly`:
`AccountMeta {pubkey:*a.key,is_signer:a.key==&authority,is_writable:a.is_writable}`.
Result: 546 of 571, 778,712 B, no losses.

## swap_observed (0x11f80): exact, and 0x1590 with it

Two source facts:

1. `output.amount` is read right after the two reloads, before the input side is checked
   (`let after_output=output.amount;`). The target forwards `before_output` into that read on the
   path where `output.reload()` failed, which is why it has `mov64 r4, r3` before the merge.
2. `with_values::<(u64,u64)>` has to stay out of line. The skeleton had one caller, so it was inlined
   (the 4,848 B against 2,832 B). The target has three callers: swap_observed, admit line 83 and the
   exact line 148. Adding `.with_values((amounts.gross_amount,amount))` at admit line 83 is enough. It
   is what the target does there (`r3=gross`, `r4=amount` at 0x20580+0x1010).

This also closes 0x1590, the third `with_values` instance from C7: the (u64,u64) instance is 0x638, and
the 14 try_accounts closures use the (usize,usize) one, which the scorer now pairs with 0x1590.
Result: 548 of 571, 783,536 B, no losses.
