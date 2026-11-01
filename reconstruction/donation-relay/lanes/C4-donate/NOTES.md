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

Results: all five handlers are strict, `programs/contracts/src/donation_handlers.rs` is gone from `.rodata`, and the five donate path strings are at their target offsets at the start of `.rodata`.

## What is left in `.rodata`, outside this cluster

Diffing candidate and target `.rodata` on this branch leaves these, none tied to `tools/donate` or the donate handlers:

- `tools/distribution/shared.rs` should disappear as a Location file (C1, C2).
- `events::v1`: the target has `donation_epoch_processed_exact.rs` before `bridge_donation_admitted.rs`.
- `admit_bridge_payment.rs`, `bridge_receiver_v1` and `recover_bridge_payment.rs` come right after `upsert_mint_whitelist.rs` in the target. They should follow once those bodies move out of `bridge_handlers.rs`, as the donate paths did.
- The account-name strings of the bridge structs sit later in the target, and `Unexpected length of input` sits earlier. Two small u32 table differences near `0xc78` and `0xce4` are unexplained.

## Tried and not needed

Nothing else was tried. The first change matched both functions, and `0x28e48` and `0x29ca8` were strict at once.
