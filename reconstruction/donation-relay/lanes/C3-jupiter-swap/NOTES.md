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

## swap_then_distribute (0x1ec18): exact

The whole 5,960 B came down to where the `u64` payload of `swap_observed`'s result is loaded. With `?` the MIR
builds a `ControlFlow` and LLVM merges both arms' loads of `_49+8` into one load before the branch (`_139.1`, with
`_138.cast = ptrtoint`), so `ldxdw r0, [r10-0x20]` sits before the tag test and takes r0 for the rest of the block.
The target loads it twice, once in each arm. An explicit
`match swap_observed(..) {Ok(total)=>total,Err(error)=>return Err(error)}` gives exactly that.
Result: 549 of 571, 789,496 B, no losses.

`just_swap` keeps `?` and is exact with it: the same MIR shape leaves its two payload loads in their arms. So the `match`
in `swap_then_distribute` may not be the original spelling, but the bytes are equal and nothing else in the function moves.

## Where it stands

All three cluster functions are normalized-equal and `strict` true, with the Mac route and the Linux route. This is not
byte identity: no raw byte comparison at the final address has passed and `whole_elf_equal` is false.

| route, this branch | functions | `.text` bytes | ratio | strict | losses |
|---|---:|---:|---:|---:|---|
| Mac hybrid, `measure.sh` | 549 | 789,496 | 0.92676 | 531 | none |
| Linux v1.54, `linux-build.sh` (142 s) | 551 | 790,216 | 0.92761 | 522 | none |

Linux adds 0xb3278 and 0xbcac0, as the brief predicted. Its strict count is lower because same-named generics pair by address
and come out in another order on that host. Checked: the 16 functions strict on Mac but not on Linux are all `try_accounts`, and each
reports a callee pair among the same-bodied `Signer::try_accounts` instances (0x10970, 0x109f0). Five go the other way and are strict only
on Linux, among them `just_swap` and both `Account::reload` instances. None of the three cluster functions is affected.

Scratch merge of this tip with C1 (c0e7d2635), C6 (0fd6a1bfa) and C5 (ddba01c1e) on the Mac route: 564 of 571, 832,952 B, 0.97777,
no losses, all three still strict, and the two Jupiter functions at their final addresses (0x11668, 0x11f80). The only conflict is
`bridge_handlers.rs`, which C5 deletes: its `admit_bridge_payment.rs` already has the same `with_values` at line 83, so take C5's side.

## For whoever finishes the layout

- `swap_then_distribute` and `just_swap` still live in `settlement_handlers.rs`. The target's order is donate handlers, `close_epoch`,
  the distribute handlers, `just_swap`, `swap_then_distribute`, `upsert_mint_whitelist`, admit, recover, then `tools::checks`, so they belong in
  `instructions/v1/relayer_only/distribute/just_swap.rs` and `swap_then_distribute.rs`. I did not move them: C1 and C2 are still editing
  that file next to them, and the move only changes the order once the rest of `settlement_handlers.rs` moves too.
- Keep `swap_then_distribute`'s `match` through any such move, and re-measure 0x1ec18 if `distribute`'s signature changes.

## General lessons from this lane

- An out-of-line `with_values::<T>` needs a second caller. Until then the inliner takes it into the only caller and that function
  looks far bigger than the target, so check `xref.py` on the target's instance before reshaping the caller.
- A read placed right after two reloads can show up as `mov64 rX, rY` on a failure path, because the load forwards from the earlier read.
- If a `Result` payload is loaded before the tag test where the target loads it in each arm, try `match` in place of `?`.
