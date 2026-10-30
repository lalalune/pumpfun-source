# Pump Main v2 trades on token-quote bonding curves: rent top-up with no reserved lamports, realloc by layout (original vs rebuild)

## Problem

Before trading, `buy_v2`, `buy_exact_quote_in_v2` and `sell_v2` call
`prepare_bonding_curve` → `fund_bonding_curve_rent`
(`programs/pump/src/extend_account.rs`). That function tops the curve up to
the 166-byte rent minimum and reallocs accounts shorter than 166 bytes.

The lamports that count as available depend on the quote:

- **Native-SOL curve:** lamports minus `real_quote_reserves` and the reserved
  fees.
- **Token-quote curve** (`quote_mint` set; the quote sits in the curve's quote
  token account): `reserved = 0`, so every lamport counts.

The native-SOL side is measured in `pump-buy-historical-curve-layouts-20261030`
and `pump-sell-historical-curve-layouts-20261030`. The existing token-quote
packets (`pump-v2-token-quote-transfer-fee-boundaries-20261030` and the v2
token-quote trade packets) use one 166-byte curve that holds exactly the
166-byte rent. None of them varies the curve's length or its lamports.

This packet runs the v2 handlers on token-quote curves of every layout that
carries `quote_mint` (115–180 bytes) and around the 166-byte rent minimum. It
compares the original `evidence/original/pump/deployed.so` with the rebuild
`candidate.so`.

## Method

- Harness from `pump-v2-token-quote-fee-routing-20261030`:
  - Pump runs under the upgradeable loader.
  - SPL Token, Token-2022 and ATA are LiteSVM built-ins.
  - SetComputeUnitLimit is 1,400,000.
  - The pump_fees slot holds a generated 9-instruction SBPFv0 stub that
    returns fees `(0, 95, 30)` bps.
  - Each case gets a fresh LiteSVM, a fixed clock and fixed-seed keys.
- Quote mint:
  - Token-2022 with TransferFeeConfig 100 bps (`t22-*` cases)
  - SPL Token (`spl-*` cases)
- The curve is the 166-byte layout (virtual reserves 1,073,000,000,000,000 /
  30,000,000,000) cut to the case length, or zero-padded to 180.
- Lamports: unless the case name says otherwise, the curve holds its
  own-length rent minimum ((128 + length) × 6,960).
- Real quote reserves: 0 for buys. 10^10 quote units for sells, held in the
  curve's quote account, not in its lamports.
- `buy_v2` buys 10^9 tokens. `sell_v2` sells 10^9 tokens.
  `buy_exact_quote_in_v2` spends 10^6 quote units (min out 1).
- 32 cases:
  - 7 lengths × `buy_v2` / `sell_v2`
  - 2 `buy_exact_quote_in_v2`
  - 9 lamport variants
  - 3 SPL-quote cases
  - 2 cases at 114 bytes
  - 2 two-instruction transactions

## Results (32 cases, `runtime/report.json.gz`)

**Behavior: the original and the rebuild match in all 32 cases.** The
transaction, error, events, inner instructions, return data and every account
after-state are byte-identical. 29 cases succeed. 3 fail with the same error
on both images.

Compute units are equal in 2 cases (the 114-byte account-constraint failures).
The other 30 differ (original minus rebuild):

| delta | cases | where |
|---|---|---|
| −2 | 14 | every successful `buy_v2` / `buy_exact_quote_in_v2` |
| −3 | 13 | every successful `sell_v2` |
| −6 | 2 | two-instruction transactions (`buy_v2` + `sell_v2`) |
| +14 | 1 | `Overflow` AnchorError site path (`programs/pump/src/…` vs `src/…`) |

Only the outer `consumed` line (and the AnchorError site line) differ in the
logs. The −2 / −3 was not located.

### Measured behavior (identical on both images)

- **Real quote reserves do not reduce the available lamports.** A token-quote
  curve with `real_quote_reserves` 10^10 and lamports equal to its own-length
  rent gets the same top-up from `buy_v2` (rqr 0) and `sell_v2` (rqr 10^10).
  On a native-SOL curve the lamports are netted against rqr: in
  `pump-sell-historical-curve-layouts-20261030`, a native curve holding only
  rqr lamports receives the full 2,046,240. Here the top-up is the rent gap,
  6,960 × (166 − length):

  | length | 115 | 123 | 124 | 141 | 165 | 166 | 180 |
  |---|---|---|---|---|---|---|---|
  | curve lamport delta (buy_v2, sell_v2) | 354,960 | 299,280 | 292,320 | 174,000 | 6,960 | 0 | 0 |

  After every trade the curve holds exactly 2,046,240 lamports (the 166-byte
  rent) and is 166 bytes long. The quote never touches its lamports. The
  180-byte curve keeps 180 bytes and 2,143,680 lamports.
- **The lamport boundary is exact.**
  - At 166 bytes:
    - Lamports = rent − 1: top-up 1 (`buy_v2` and `sell_v2`).
    - Lamports = 1: top-up 2,046,239 (also with the SPL quote).
  - At 115 bytes:
    - Lamports = 166-byte rent: no top-up; the account is still reallocated
      to 166 bytes.
    - Lamports = 166-byte rent + 1: no top-up; the curve keeps 2,046,241.
- **`buy_exact_quote_in_v2`** on 115 and 141 bytes: same top-up as `buy_v2`
  (354,960 / 174,000). The curve's quote account gets 977,777. The user gets
  34,970,648,484 tokens.
- **SPL Token quote** (115 bytes): same lamport deltas as Token-2022. The quote
  routing has no transfer fee (fee recipient and buyback 133 each, creator
  vault 84). Token-2022 gives 131 / 131 / 83.
- **Lamports below rent with `rqr` = 0 on `sell_v2`** stop with `Overflow` at
  lib.rs:2535 (`real_quote_reserves.checked_sub(quote)`), and the curve is
  unchanged.
- **114 bytes** (the `quote_mint` field is cut off) decodes as a native-SOL
  curve. `buy_v2` and `sell_v2` with the Token-2022 quote account list fail
  with `MintDoesNotMatchBondingCurve` (no AnchorError site, CU equal), and the
  curve keeps 114 bytes.
- **In one transaction** (115 bytes), `buy_v2` then `sell_v2` and `sell_v2`
  then `buy_v2` pay one top-up of 354,960 between them.
- **Other lamport flows.** Every successful case also funds the creator vault
  rent (890,880) and creates the user-volume accumulator (1,844,400), both
  paid by the user.

## Files

- `producer.py`: case plan, fee stub generator, LiteSVM runner, report.
- `verify.py`: replays `runtime/plan.json.gz` on both images using only this
  folder (it imports the runner from `producer.py`). It compares every receipt
  and the recomputed summary with the recorded ones and checks both image
  sha256 values against the report.
- `runtime/plan.json.gz`: the 32 cases with their full initial account set.
- `runtime/receipts-upgradeable.jsonl.gz`: 64 receipts (32 cases × 2 images).
- `runtime/report.json.gz`: image sha256 values. Per case: the stop,
  AnchorError site, CU, decoded TradeEvent, the curve after-state (lamports,
  length, quote mint, reserves), lamport deltas and quote-token deltas.

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
- Only lengths ≥ 114. Shorter layouts cannot hold a quote mint.
- pump_fees is a fixed-answer stub. Token programs are LiteSVM's built-ins.
- The −2 / −3 / −6 CU on successful v2 trades was not located.
