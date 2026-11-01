# C5-bridge-handlers: admit and recover handler bodies

Baseline: `origin/swarm/w20-relay-scout` at `dfcbfc6ae`, 545 of 571 functions, 776,384 of 851,888 `.text` bytes, strict 527.
All figures are `relay/tools/measure.sh` on the Mac route unless marked Linux: normalized matches, not byte identity. No function is at its final address yet, and `whole_elf_equal` is false.

| step | commit | functions | `.text` bytes | strict | `.rodata` common / edits | losses |
|---|---|---:|---:|---:|---:|---|
| baseline | `dfcbfc6ae` | 545 | 776,384 | 527 | | none |
| recover body, `0x21608` | `d62876a48` | 546 | 780,712 | 527 | | none |
| merge C4's `SignedDonationArgs`, admit seeds at the call | not separate | 548 | 789,664 | 529 | | none |
| admit line 83 `with_values`, `0x20580` | `1faf3dca8` | 550 | 795,888 | 531 | 22,231 / 22 | none |
| same source, Linux | `1faf3dca8` | 552 | 796,608 | 523 | | none |
| merge C4's handler move | `afe1b2869` | 550 | 795,888 | 537 | 22,643 / 16 | none |
| bridge handlers into their instruction modules, modules reordered | `ddba01c1e` | 550 | 795,888 | 537 | 23,042 / 10 | none |
| event and state modules reordered | `36f255cac` | 550 | 795,888 | 538 | 23,074 / 4 | none |

`.rodata` target size is 23,104 B. "Common" and "edits" come from `difflib.SequenceMatcher` over the two sections, without autojunk.

Both cluster functions are normalized-exact with `ratio 1.0`. On Linux both report `strict: true` (see below for the Mac).

## What fixed recover, `0x21608`

Three source changes, each confirmed by a build:

1. **The balance check adds and subtracts `amount`.** The target tests `receiver_before < amount`, then `receiver_before - amount != reloaded`, then the overflow of `destination_before + amount`, then the sum against the reloaded destination:

   ```rust
   if receiver_before.checked_sub(amount)!=Some(accounts.receiver_token_account.amount) || destination_before.checked_add(amount)!=Some(accounts.destination_token_account.amount) {..}
   ```

   This also moved `amount` to a spill slot and `accounts` to `r8`, as in the target.
2. **The seeds are a slice, with the outer array at the call.** The target's frame has the outer array at `-0x10`, the `TransferChecked` temp at `-0xd0`, the `CpiContext` at `-0x1e8`, the bump at `-0x1e9` and the inner array at `-0x220`. The outer array is written after the account clones.

   ```rust
   let seeds:&[&[u8]]=&[b"bridge_receiver_v1",source_id.as_ref(),&[receiver_bump]];
   anchor_spl::token::transfer_checked(CpiContext::new_with_signer(program,TransferChecked {..},&[seeds]),amount,decimals)?;
   ```

   Reading from these two builds: slots run from the top of the frame downward in reverse order of temp creation, so the frame gives away the order in which the source creates its temps. A single `signer_seeds` binding with all the arrays put the outer array at the bottom instead.
3. **The program state decodes in one expression.**

   ```rust
   let state=UpgradeableLoaderState::try_deserialize_unchecked(&mut &accounts.program.try_borrow_data()?[..])?;
   ```

   With `let data=..try_borrow_data()?;` in a block, code and size were already right, but the `&mut &data[..]` slice sat at `-0xd0` and the borrow error temp at `-0x1e8`, where the target has `-0x220` and `-0xd0`. The temp form makes their lifetimes overlap, so stack colouring assigns the slots as deployed.

## What fixed admit, `0x20580`

1. **C4's `SignedDonationArgs`.** The target passes a 0x30-byte struct with no `message` to `0x29ca8`. This is merged from `swarm/w20-relay-C4-donate`.
2. **The seeds go inline in the call's argument position**, after the context and the args:

   ```rust
   donate_with_seeds(SignedDonationContext {..},SignedDonationArgs {..},&[&[b"bridge_receiver_v1",source_id.as_ref(),&[receiver_bump]]])?;
   ```

3. **Line 83 carries the compared values:** `.with_values((amounts.gross_amount,amount))`. That is `require_eq!`'s shape. It accounts for the target's `with_values` call at `0x1020` and fixed the register assignment of `amount` (`r7`, spilled across the donate call). It also gains `0x1590`, which C3 and C7 reached with the same edit.

## Where the handlers live

The target's local functions give the module order. Hand-written functions come first and derive output later, and each group follows the module tree, which is a reading of the layout rather than of rustc:

- handlers: `.. upsert_mint_whitelist` `0x20360`, admit `0x20580`, recover `0x21608`, `tools::checks` `0x226f0`
- `try_accounts`: `.. upsert_mint_whitelist` `0x6e098`, admit `0x702d0`, recover `0x7aa00`
- event `serialize`: closed, just_swapped, processed, processed_exact, made, bridge_donation_admitted, bridge_payment_recovered
- account `try_serialize`: debouncer, distribution, epoch_tracker, mint_whitelist, swap_receipt, bridge_membership

So `lib.rs` now declares `relayer_only { close_donation_epoch; distribute {..}; upsert_mint_whitelist; admit_bridge_payment; } recover_bridge_payment;`, with `events` and `state::v1` in the orders above, and the handlers moved from `bridge_handlers.rs` into `instructions/v1/relayer_only/admit_bridge_payment.rs` and `instructions/v1/recover_bridge_payment.rs`. `bridge_handlers.rs` is deleted.

The errors keep literal lines through `bridge_error!`, so the placement in the file is not pinned by these two functions. Nothing in either function has a `Location`, so the handler signature (free function or inherent) is not pinned by the bytes either.

## What `.rodata` still differs in

Four edits, none tied to this cluster:

- `programs/contracts/src/tools/distribution/shared.rs`, in the candidate only, from three `Location`s at `91:45`, `118:54` and `134:13`. Those are the only `Location` difference left against the target (C1, C2).
- `\r\0\0\0` at target `0xce4`, one `ErrorCode` constant. C4's notes tie code 13 to the open `0x24ec0` (C2). Not checked by a build here.
- `Unexpected length of input`, at `0x3fe5` in the target and later here. `borsh::de::unexpected_eof_to_unexpected_length_of_input` is also out of order, and it is a symbol-sorted upstream instance, so this is probably the host hash. See the Linux result below.

## Mac and Linux

On the Mac, recover reports `strict: false`, `call 0x4ea0->0x5120`. That is not a source difference. The two `Account<T>::reload` instances (classic and interface `TokenAccount`) have equal bodies, and their order follows the symbol hash, which depends on the host. Recover calls the classic one, as the target does: the callee's own `try_deserialize_unchecked` pairs with the target's `0xa21c8`. On Linux the pairs line up, and `0x4ea0`, `0x5120`, `0x20580` and `0x21608` are all `strict: true`.

## Merging

`swarm/w20-relay-C3-jupiter-swap` and `swarm/w20-relay-C7-framework-layout` edit one line of `bridge_handlers.rs`, the same `with_values`. Merging them gives a modify/delete conflict: keep the deletion, because the edit is already in `admit_bridge_payment.rs`. Dry-run merges against C1, C4 and C6 are clean.

## Tried and not kept

- `let signer_seeds:&[&[&[u8]];1]=&[&[..]];` in recover: 4,344 B, with the outer array at the bottom of the frame.
- `{let data=..;deserialize(&mut &data[..])?}` in recover: 4,328 B, 5 tokens off, the two frame slots above.
- The skeleton's `checked_sub` of the reloaded amounts and `accounts.destination_token_account.amount.checked_sub(destination_before)`: 4,296 B, with no overflow check on the destination side.
