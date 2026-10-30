# Pump Main sells on historical (short) bonding-curve layouts: decode, realloc, rent top-up net of reserves, layout-only fields (original vs rebuild)

## Problem

The BondingCurve account grew over time. The Pump Main decoder picks a layout
from the account length (discriminator included):

| length | layout |
|---|---|
| < 49 | rejected (`InvalidAccountData`) |
| 49–80 | v0: reserves + `complete`, no creator |
| 81 | v1 |
| 82 | v2: + mayhem |
| 83–114 | v3: + cashback |
| 115–123 | v4: + quote mint |
| 124 | v5: + creator_fee_bps (offset 115), can_edit_creator_fee (offset 123) |
| 125–140 | v6: + is_holder_reward |
| 141–165 | v7 |
| ≥ 166 | v8 |

The legacy `sell` handler reads the curve through a length-preserving wrapper
(`LegacyCurve` in `programs/pump/src/sell.rs`). It also calls
`prepare_bonding_curve` (`extend_account.rs`), which tops the curve up to the
166-byte rent minimum, net of `real_quote_reserves` and reserved fees, and
reallocs it to 166 bytes. Unlike a buy, a sell pays SOL *out* of the curve.

The repository has length-mutation rows for sells
(`scripts/pump_legacy_sell_differential.py`: 16 lengths and low-rent rows;
`scripts/pump_sell_v2_differential.py`: 8 lengths). Both import
`scripts/pump_trade_fixture.py`, which reads
`research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json`.
That file is not in the repository tree, so those rows cannot be rerun from a
checkout. The buy side is in `pump-buy-historical-curve-layouts-20261030`. This
packet is the sell side, built so that it runs on its own. It compares the
original `evidence/original/pump/deployed.so` with the rebuild `candidate.so`.

## Method

- Same harness as `pump-buy-historical-curve-layouts-20261030`. Pump runs under
  the upgradeable loader (program account plus programdata). The pump_fees slot
  holds a 9-instruction SBPFv0 stub that `producer.py` generates in memory and
  that returns fees `(0, 95, 30)` bps (sha256 `b2b7a41f…6c93`). Both images see
  the same stub.
- One fresh LiteSVM per case, fixed clock, fixed-seed keys, synthetic IDL-layout
  state.
- The curve is the 166-byte layout (virtual reserves 1,073,000,000,000,000 /
  30,000,000,000; real token reserves 793,100,000,000,000; real quote reserves
  `rqr` = 10,000,000,000), cut to the case length; the 180-byte case is
  zero-padded. Unless the case name says otherwise, the curve holds its
  own-length rent minimum plus `rqr` ((128 + length) × 6,960 + 10^10 lamports
  under LiteSVM's default rent). The user holds 10^12 tokens and sells 10^9
  (min out 0).
- Below length 81 the layout has no creator. Those cases pass the creator vault
  of the default key.
- 54 cases:
  - 16 `sell` lengths (48–180)
  - 8 lamport / `rqr` variants
  - 6 layout-flag variants (mayhem, cashback, complete)
  - 5 Global `creator_fee_configurable` = 1 cases (curve `creator_fee_bps` 500)
    on lengths 115 / 123 / 124 / 141 / 166
  - 6 error-path cases on short curves
  - 9 `sell_v2` (native SOL)
  - 4 two-instruction transactions (600,000 CU limit)

## Results (54 cases, `runtime/report.json.gz`)

**Behavior: the original and the rebuild match in all 54 cases.** The
transaction, error, events, inner instructions, return data and every account
after-state (including the reallocated curve bytes) are byte-identical. 39
cases succeed. 15 fail with the same error on both images.

Compute units are equal in 35 cases. The other 19 differ (original minus
rebuild):

| delta | cases | where |
|---|---|---|
| +14 | 11 | AnchorError site: `programs/pump/src/…` in the original, `src/…` in the rebuild (`Overflow`, `NotAuthorized`, `BondingCurveComplete`, `TooLittleSolReceived`, `SellZeroAmount`, `InvalidBondingCurveV2`, `InvalidCashbackAccumulator`) |
| +118 | 1 | `NotEnoughTokensToSell` (lib.rs:972) |
| −3 | 6 | every successful `sell_v2` on a curve with a creator (lengths 81, 83, 115, 141, 166, plus the 81-byte rent-166 variant); only the outer `consumed` line differs |
| −4 | 1 | `sell` then `sell_v2` in one transaction |

`sell_v2` on the 49-byte curve (no creator) costs the same on both images
(89,009). The −3 was not located further.

### Measured behavior (identical on both images)

- **Length 48** fails with `InvalidAccountData` for both `sell` and `sell_v2`
  (no AnchorError site, CU equal). **Length 49** is the shortest curve that
  sells.
- **A sell on a curve shorter than 166 bytes reallocs it to 166 bytes, even
  through `LegacyCurve`.** The seller pays the rent difference. The sell output
  (27,958 lamports) leaves the curve in the same transaction. Curve lamport
  delta = 6,960 × (166 − length) − 27,958:

  | length | 49 | 80 | 81 | 82 | 83 | 114 | 115 | 123 | 124 | 125 | 140 | 141 | 165 | 166 | 180 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | curve delta | 786,362 | 570,602 | 563,642 | 556,682 | 549,722 | 333,962 | 327,002 | 271,322 | 264,362 | 257,402 | 153,002 | 146,042 | −20,998 | −27,958 | −27,958 |

  After the sell, every curve of 49–166 bytes has 10,002,018,282 lamports
  (`rqr` 9,999,972,042 + 166-byte rent 2,046,240) and is 166 bytes long. The
  180-byte curve stays 180 bytes and gets no top-up.
- **The top-up is net of `real_quote_reserves`.** On an 81-byte curve:
  - Lamports = 166-byte rent + `rqr`: top-up 0 (curve delta −27,958).
  - One lamport less: top-up 1 (delta −27,957).
  - Lamports = `rqr` only: top-up 2,046,240 (delta +2,018,282). The 166-byte
    curve holding `rqr` only behaves the same.
  - Lamports = `rqr` − 1: the top-up is still 2,046,240. The available balance
    saturates at 0, so the missing lamport is not charged. The curve ends at
    10,002,018,281, one lamport below `rqr` + rent.
  - A 49-byte curve that already holds the 166-byte rent + `rqr` gets no
    top-up. The seller nets +22,692 (27,958 − 266 fee − 5,000 tx fee).
- **`rqr` smaller than the sell output** (`rqr` 0 or 1,000) stops with
  `Overflow` at lib.rs:1037. The curve keeps 81 bytes and its lamports.
- **v0 curves (49–80 bytes) have no creator.** The sell charges no creator fee
  (event `creator_fee` 0). The new tail bytes after the realloc are zero.
- **Creator vault rent.** With a creator (≥ 81 bytes), the vault (absent
  before) receives 890,964 = 890,880 zero-byte rent minimum + 84 creator fee.
  The seller funds the rent.
- **Layout flags survive the realloc.**
  - An 82-byte curve with mayhem = 1 keeps byte 81 = 1. The whole 266 fee goes
    to the reserved recipient.
  - Passing the reserved recipient for a non-mayhem 81-byte curve fails with
    `NotAuthorized` (fee_recipient.rs:35).
  - An 83-byte curve with cashback = 1 keeps byte 82 = 1. With the user-volume
    accumulator as remaining[0], the 84 creator fee goes to the accumulator,
    which is created with 1,844,400 rent; the event `creator_fee` is 0. With
    the default remaining list (curve-v2 PDA first), it fails with
    `InvalidCashbackAccumulator` (sell.rs:33).
- **`creator_fee_bps` takes effect from length 124 on.** With Global
  `creator_fee_configurable` = 1 and curve `creator_fee_bps` 500:
  - Lengths 115 and 123 charge the stub's 30 bps: creator fee 84. These
    lengths decode as v4, which has no creator_fee_bps. At 123 bytes all 8
    bytes of the field (offsets 115–122) are present, but the v5 layout also
    needs the can_edit_creator_fee byte at offset 123.
  - Lengths 124, 141 and 166 charge 500 bps: creator fee 1,398.
- **Error paths on short curves** leave the curve at its original length and
  lamports:
  - `TooLittleSolReceived` (lib.rs:1012)
  - `SellZeroAmount` (lib.rs:970)
  - `NotEnoughTokensToSell` (lib.rs:972)
  - wrong fee recipient → `NotAuthorized`
  - creator-key vault on a v0 curve → `ConstraintSeeds`
  - empty remaining list → `InvalidBondingCurveV2` (sell.rs:126)
  - `complete` = 1 → `BondingCurveComplete` (lib.rs:968; `sell_v2`:
    sell_v2.rs:243)
- **`sell_v2`** gives the same curve deltas as `sell` on lengths 49, 81, 83,
  115, 141 and 166. It also creates the user-volume accumulator (1,844,400
  rent paid by the seller).
- **In one transaction**, a second sell after the realloc pays no further
  top-up. The curve delta is 6,960 × (166 − length) − 2 × 27,958 (81 bytes:
  535,684; 49 bytes: 758,404). `sell` then `sell_v2` on 81 bytes gives the
  same 535,684. `sell` then `buy` on 81 bytes leaves the curve at
  10,002,046,241 = `rqr` 10,000,000,001 + 2,046,240.

## Files

- `producer.py`: case plan, fee stub generator, LiteSVM runner, report.
- `verify.py`: replays `runtime/plan.json.gz` on both images using only this
  folder (it imports the runner from `producer.py`). It compares every receipt
  and the recomputed summary with the recorded ones and checks both image
  sha256 values against the report.
- `runtime/plan.json.gz`: the 54 cases with their full initial account set.
- `runtime/receipts-upgradeable.jsonl.gz`: 108 receipts (54 cases × 2 images).
- `runtime/report.json.gz`: image sha256 values. Per case: the stop,
  AnchorError site on each image, CU, decoded TradeEvent, the curve after-state
  (length, lamports, reserves, creator, bytes from offset 81) and labelled
  lamport deltas.

Images: original sha256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
(10,485,715 B). Candidate sha256
`e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633` (1,934,648 B),
built with `scripts/build_partial_candidate.py` (platform-tools v1.44,
cargo-build-sbf 2.1.21) from `programs/pump`, source tree
`97a2a2a383ba1bc5c5af08429de150e6124f0fc1`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.

## Reproduce

```
python3 producer.py --root <repo> --out . \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
python3 verify.py \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

Requires python3 and solders 0.27.1 (LiteSVM). No network. Two producer runs
give byte-identical `runtime/` files. `verify.py` exits 0.

## Limits

- Short curves are made by cutting today's 166-byte layout. They are not copies
  of historical mainnet accounts.
- Native-SOL quote only. Token-quote curves (`quote_mint` set, where the
  top-up reserves nothing) are not covered.
- pump_fees is a fixed-answer stub.
- The −3 / −4 CU on successful `sell_v2` was not located.
