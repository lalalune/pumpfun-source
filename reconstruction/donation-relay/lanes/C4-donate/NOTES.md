# C4-donate: `donate_shared`, the signed transfer core, the five donate Locations

Baseline: `origin/swarm/w20-relay-scout` at `dfcbfc6ae`, 545 of 571 functions, 776,384 of 851,888 `.text` bytes, strict 527.
All figures are `relay/tools/measure.sh` on the Mac route: normalized matches, not byte identity. No function is at its final address yet.

| step | commit | functions | `.text` bytes | strict | losses |
|---|---|---:|---:|---:|---|
| baseline | `dfcbfc6ae` | 545 | 776,384 | 527 | none |
| core takes `SignedDonationArgs` | `bc748be5f` | 547 | 785,336 | 529 | none |
| handlers moved to the instruction files | `8a24b2221` | 547 | 785,336 | 535 | none |

## What fixed `0x28e48` and `0x29ca8`

Both took the same one change. The deployed core reads its arguments from a separate, smaller struct:

```rust
pub struct SignedDonationArgs {pub config_id:[u8;32],pub amount:u64,pub tip_bps:u16,pub epoch_tracker_bump:u8,pub debouncer_bump:u8}
```

- `0x29ca8` reads `config_id` at `r3+0x0` and the bumps at `r3+0x2a` and `r3+0x2b`. With the skeleton's `DonationArgs`, whose `String` comes first, those were `r3+0x18`, `r3+0x42`, `r3+0x43`. That was the whole difference (same 5,272 B).
- `0x28e48` builds the 0x30-byte struct on its own stack at `r10-0x88`, which is the 160 B the skeleton was short.
- `donate_shared` keeps `DonationArgs` with the message. The `donate_with_seeds(ctx, args, signer_seeds)` signature is otherwise unchanged. C5 merged this commit and reached admit with it.

## The five Locations

The target's `message.clone()` panic Locations pin the handler bodies to the instruction files:

| file under `instructions/v1/public_api/donate/` | line | col | handler |
|---|---:|---:|---|
| `donate.rs` | 116 | 34 | `0x12a90` |
| `donate_native.rs` | 165 | 34 | `0x13448` |
| `donate_native_pubkey_config_id.rs` | 159 | 34 | `0x14b58` |
| `donate_pubkey_config_id.rs` | 118 | 34 | `0x16268` |
| `donate_pubkey_config_id_with_payer.rs` | 129 | 34 | `0x16c20` |

- Column 34 is `clone` in `                message: message.clone(),`, a 16-space field. That depth is natural inside `impl X { fn f(..) { donate_shared(.., DonationArgs { .. }) } }`, one level deeper than a free function gives, so the handlers are inherent functions. The impl form is a reading of that column, not something the bytes prove.
- Comment lines fill the gap between each struct and its handler, as the files already do before the macros. The original text in those gaps is unknown. Only the coordinate is pinned.
- `donation_handlers.rs` is deleted and `lib.rs` keeps its line count, so `lib.rs:36:1` still holds.

Results: all five handlers are strict and `programs/contracts/src/donation_handlers.rs` is gone from `.rodata`. The five donate path strings are in target order. Three are at their exact target offsets (`0x0`, `0xe5`, `0x140`). `donate_native.rs` and `donate_pubkey_config_id.rs` are `0x34` late only because of the extra `tools/distribution/shared.rs` path at `0x2a1`, which is the first `.rodata` difference on this branch.

## Checks

These cover `0x28e48`, `0x29ca8` and the five handlers, on the source of `8a24b2221`. Later commits on this branch change only this file.

- **Mac route (`measure.sh`):** 547 of 571 functions, 785,336 B, strict 535, zero losses.
- **Linux route (`linux-build.sh`, official v1.54 archive, 138 s):** 549 of 571, 786,056 B, strict 526. All seven are matched and strict. `0xb3278` and `0xbcac0` match there as the brief predicted.
- **Raw bytes, both routes:** every instruction slot of the seven is identical except call immediates and `lddw` immediates, which hold addresses. So these are not yet raw-identical in place: that needs the rest of `.text` and `.rodata` to land at the target's addresses.
- **Trial merge, not pushed:** this branch with C5 `1faf3dca8`, C6 `e4b092a10`, C1 `c0e7d2635` and C3 `e8f417e91` gave 562 of 571, 822,544 B, strict 549, zero losses on the Mac route. The only conflict was C3's line 83 next to the core call in `bridge_handlers.rs`, and C5 already holds both changes.

`whole_elf_equal` is false on every build above.

### For C7: strict is lower on Linux

16 functions are strict on the Mac and not on Linux: 11 `try_accounts` with `call 0x10970->0x10520` and 5 IDL functions with `call 0x109f0->0x104a0`. Target `0x10970` and `0x109f0` are two 128 B `<Signer as Accounts<B>>::try_accounts` instances, and on Linux callers reach the instance paired with the other one. I did not determine whether that is the scorer's pairing or a real swap of the two instances, and it is not caused by this lane's change.

## What is left in `.rodata`, outside this cluster

Diffing candidate and target `.rodata` on this branch leaves these, none tied to `tools/donate` or the donate handlers:

- `tools/distribution/shared.rs` should disappear as a Location file (C1, C2).
- `events::v1`: the target has `donation_epoch_processed_exact.rs` before `bridge_donation_admitted.rs`.
- `admit_bridge_payment.rs`, `bridge_receiver_v1` and `recover_bridge_payment.rs` come right after `upsert_mint_whitelist.rs` in the target. They should follow once those bodies move out of `bridge_handlers.rs`, as the donate paths did.
- The account-name strings of the bridge structs sit later in the target, and `Unexpected length of input` sits earlier.
- The u32 differences near `.rodata` `0xc78` and `0xce4` are `ErrorCode` constants, ordered by first use. `0` (`InvalidAdmin`) is used by recover, which still comes too early here, and `13` is used by the open `0x24ec0`, so these should follow C2 and the bridge move. That is a reading of the references, not a build result.

## Tried and not needed

Nothing else was tried. The first change matched both functions, and `0x28e48` and `0x29ca8` were strict at once.
