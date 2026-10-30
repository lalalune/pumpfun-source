# pump_fees `withdraw` `InterfaceAccount<TokenAccount>` decoding: Token-2022 layout boundaries (length, account type, state and COption tags, TLV, owner)

## Problem

`withdraw` (`programs/pump-fees/src/withdrawal.rs`) declares `vault_ata` and `user_ata` as `Option<InterfaceAccount<'info, token_interface::TokenAccount>>`. Both carry the constraints `token::mint`, `token::authority` and `token::token_program`.

Anchor decodes both accounts with the spl-token-2022 account unpacker that is linked into pump_fees. `withdraw_token` then reads the decoded `vault_ata.amount` and CPIs `transfer_checked` into the token program (`programs/pump-fees/src/instructions/withdraw.rs`).

The decoder is library code, so the reconstruction must link a version that behaves the same. The existing withdraw measurements use only real token-program layouts: a 165-byte base account, and a Token-2022 account with TransferFeeAmount. They are in `research/pump-fees-buyback-init-withdraw-sequences-20261030`. No existing packet or open PR measures this decoder at the following boundaries:

- account length around 165 / 166 / 355;
- the account-type byte at offset 165;
- the state byte;
- the COption tags of delegate, is_native and close_authority;
- the TLV area;
- the legacy SPL Token owner.

## Method

- **Transaction.** Each case is one `withdraw` transaction in token mode, run on a fresh LiteSVM per image.
- **Varied input.** Only the bytes (or the owner) of `vault_ata` or `user_ata` change between cases.
- **Fixed accounts.**
  - USER signs.
  - The referral vault PDA holds 1,000,000 lamports.
  - The quote mint is an 82-byte Token-2022 mint, or an SPL Token mint in the `o-token-*` cases. It has 6 decimals.
  - `vault_ata` holds 1,000,000 units unless stated.
  - `user_ata` holds 0.
  - Both token accounts hold 3,000,000 lamports.
- **Token programs.** SPL Token and Token-2022 are the programs bundled with LiteSVM (solders 0.27.1), identical on both sides. Only the pump_fees image differs.
- **Determinism.** Fixed keypair seeds and a fixed clock (unix 1,700,000,000).
- **What is compared.** The error, the full log list (minus the runtime `consumed` lines), and the token amount, length and sha256 of both token accounts after the transaction. Compute units are compared separately.

| image | sha256 |
|---|---|
| original `evidence/original/pump_fees/deployed.so` | `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e` |
| candidate (rebuild) | `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900` |

The candidate was built by `scripts/build_partial_candidate.py` with platform-tools v1.44 / cargo-build-sbf 2.1.21. Source tree `7eb3b25ef7ee45dcba86f2af79344297e98a091d`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.

## Result

**46 cases. The original and the rebuild match in all 46: same error, same logs, same compute units and same token-account bytes afterwards. There is no divergence.**

Outcomes (identical on both images):

| outcome | cases |
|---|---|
| success | 18 |
| ProgramError InvalidAccountData (pump_fees account decoding) | 15 |
| SPL Token CPI: invalid account data | 3 |
| Token-2022 CPI: custom error 0x11 (account frozen) | 2 |
| 2015 ConstraintTokenOwner | 2 |
| ProgramError UninitializedAccount | 1 |
| 6036 NothingToWithdraw | 1 |
| 2014 ConstraintTokenMint | 1 |
| 2021 ConstraintTokenTokenProgram | 1 |
| 3007 AccountOwnedByWrongProgram | 1 |
| transaction InsufficientFundsForRent (account index 1) | 1 |

"vault / user bytes" is the length of `vault_ata` / `user_ata`. "user received" is the change in `user_ata`'s token amount.

| case | token program | vault / user bytes | result (both images) | user received | CU (both images) | orig = rebuild |
|---|---|---|---|---|---|---|
| `l-165-base` | token22 | 165 / 165 | success | 1,000,000 | 30,809 | yes |
| `l-164` | token22 | 164 / 165 | ProgramError InvalidAccountData | 0 | 4,559 | yes |
| `l-166-type-account` | token22 | 166 / 165 | ProgramError InvalidAccountData | 0 | 4,764 | yes |
| `l-167-type-account` | token22 | 167 / 165 | success | 1,000,000 | 30,863 | yes |
| `l-170-type-account` | token22 | 170 / 165 | success | 1,000,000 | 30,913 | yes |
| `l-355-multisig-length` | token22 | 355 / 165 | ProgramError InvalidAccountData | 0 | 4,558 | yes |
| `l-356-type-account` | token22 | 356 / 165 | success | 1,000,000 | 30,914 | yes |
| `l-166-zero-type` | token22 | 166 / 165 | ProgramError InvalidAccountData | 0 | 4,764 | yes |
| `t-type-0` | token22 | 170 / 165 | ProgramError InvalidAccountData | 0 | 4,766 | yes |
| `t-type-1` | token22 | 170 / 165 | ProgramError InvalidAccountData | 0 | 4,766 | yes |
| `t-type-3` | token22 | 170 / 165 | ProgramError InvalidAccountData | 0 | 4,766 | yes |
| `t-type-255` | token22 | 170 / 165 | ProgramError InvalidAccountData | 0 | 4,766 | yes |
| `s-state-0` | token22 | 165 / 165 | ProgramError UninitializedAccount | 0 | 4,861 | yes |
| `s-state-2-frozen` | token22 | 165 / 165 | Token-2022 CPI: custom program error: 0x11 | 0 | 20,409 | yes |
| `s-state-3` | token22 | 165 / 165 | ProgramError InvalidAccountData | 0 | 4,593 | yes |
| `s-delegate-tag-2` | token22 | 165 / 165 | ProgramError InvalidAccountData | 0 | 4,579 | yes |
| `s-native-tag-1` | token22 | 165 / 165 | TransactionErrorInsufficientFundsForRent { account_index: 1 } | 0 | 30,864 | yes |
| `s-native-tag-2` | token22 | 165 / 165 | ProgramError InvalidAccountData | 0 | 4,591 | yes |
| `s-close-tag-2` | token22 | 165 / 165 | ProgramError InvalidAccountData | 0 | 4,604 | yes |
| `s-delegate-tag-1` | token22 | 165 / 165 | success | 1,000,000 | 30,849 | yes |
| `e-immutable-owner` | token22 | 170 / 165 | success | 1,000,000 | 30,929 | yes |
| `e-transfer-fee-amount` | token22 | 178 / 165 | success | 1,000,000 | 30,929 | yes |
| `e-mint-extension-in-account` | token22 | 278 / 165 | success | 1,000,000 | 30,902 | yes |
| `e-unknown-type-65535` | token22 | 170 / 165 | success | 1,000,000 | 30,885 | yes |
| `e-length-past-end` | token22 | 172 / 165 | success | 1,000,000 | 30,929 | yes |
| `e-partial-header-2` | token22 | 168 / 165 | success | 1,000,000 | 30,863 | yes |
| `e-duplicate` | token22 | 174 / 165 | success | 1,000,000 | 31,031 | yes |
| `e-entry-then-garbage` | token22 | 173 / 165 | success | 1,000,000 | 30,965 | yes |
| `a-amount-0` | token22 | 165 / 165 | 6036 NothingToWithdraw | 0 | 18,648 | yes |
| `a-amount-u64-max` | token22 | 165 / 165 | success | 18,446,744,073,709,551,615 | 30,809 | yes |
| `a-amount-1-extended` | token22 | 170 / 165 | success | 1 | 30,929 | yes |
| `a-mint-field-other` | token22 | 165 / 165 | 2014 ConstraintTokenMint | 0 | 11,823 | yes |
| `a-owner-field-user` | token22 | 165 / 165 | 2015 ConstraintTokenOwner | 0 | 11,785 | yes |
| `a-owner-field-other-extended` | token22 | 170 / 165 | 2015 ConstraintTokenOwner | 0 | 11,791 | yes |
| `u-user-170-type-account` | token22 | 165 / 170 | success | 1,000,000 | 30,913 | yes |
| `u-user-166-type-account` | token22 | 165 / 166 | ProgramError InvalidAccountData | 0 | 5,306 | yes |
| `u-user-unknown-ext` | token22 | 165 / 170 | success | 1,000,000 | 30,885 | yes |
| `u-user-state-2-frozen` | token22 | 165 / 165 | Token-2022 CPI: custom program error: 0x11 | 0 | 20,968 | yes |
| `u-user-type-1` | token22 | 165 / 170 | ProgramError InvalidAccountData | 0 | 5,308 | yes |
| `o-token-165-base` | token | 165 / 165 | success | 1,000,000 | 35,295 | yes |
| `o-token-170-type-account` | token | 170 / 165 | SPL Token CPI: invalid account data for instruction | 0 | 20,725 | yes |
| `o-token-166-type-account` | token | 166 / 165 | ProgramError InvalidAccountData | 0 | 4,712 | yes |
| `o-token-immutable-owner` | token | 170 / 165 | SPL Token CPI: invalid account data for instruction | 0 | 20,725 | yes |
| `o-token-user-170` | token | 165 / 170 | SPL Token CPI: invalid account data for instruction | 0 | 22,254 | yes |
| `o-system-owned-vault` | token22 | 165 / 165 | 3007 AccountOwnedByWrongProgram | 0 | 6,475 | yes |
| `o-token-owned-vault-t22-program` | token22 | 165 / 165 | 2021 ConstraintTokenTokenProgram | 0 | 11,964 | yes |

### What the measurements show (same on both images)

- **Length.**
  - 164 bytes is rejected (4,559 CU).
  - 166 bytes with type byte 2 is rejected (4,764 CU), and so is 166 bytes with type byte 0.
  - 167, 170 and 356 bytes with type 2 are accepted, so the smallest accepted extended account here is 167 bytes.
  - 355 bytes is rejected at 4,558 CU.
- **Account-type byte.** At 170 bytes, type bytes 0, 1, 3 and 255 are rejected (4,766 CU). Only 2 is accepted. Type 1 (Mint) in `user_ata` is rejected the same way (5,308 CU).
- **State and COption tags.**
  - State 0 gives UninitializedAccount. State 3 and tag 2 on delegate, is_native or close_authority give InvalidAccountData. All of these fail in pump_fees' decoding, before any CPI.
  - State 2 (Frozen) passes pump_fees' decoding. Token-2022 then rejects the transfer with custom error 0x11, for a frozen vault and for a frozen user account alike.
  - is_native tag 1 on the non-native mint passes decoding, and the Token-2022 CPI returns success. The transaction is then rejected by the runtime with InsufficientFundsForRent on account index 1, and no token amount changes.
  - delegate tag 1 is accepted.
- **TLV area.** pump_fees accepts all eight vault `e-*` layouts:
  - an unknown type 65535;
  - a mint-side extension in an account;
  - a length past the end;
  - a 2-byte partial header;
  - a duplicate entry;
  - trailing garbage;
  - two valid extensions.

  The bundled Token-2022 program also completes the transfer for all eight. `user_ata` with an unknown extension is accepted as well.
- **Amount and constraints.**
  - A vault amount of 0 gives 6036 NothingToWithdraw (18,648 CU).
  - An amount of u64::MAX, larger than the mint supply, is transferred in full.
  - Mint and owner fields that do not match give 2014 / 2015 after decoding, including on an extended 170-byte layout.
- **SPL Token owner.**
  - pump_fees decodes an SPL-Token-owned account with the Token-2022 rules. A 170-byte type-2 layout and an ImmutableOwner layout pass pump_fees and are rejected by the SPL Token program in the CPI ("invalid account data for instruction", 20,725 CU). A 170-byte `user_ata` behaves the same way (22,254 CU).
  - A 166-byte layout is rejected by pump_fees itself (4,712 CU).
- **Owner checks.** A System-owned vault gives 3007. An SPL-Token-owned vault passed with Token-2022 as `token_program` gives 2021.

## Reproduce

```
python3 producer.py --root <repo> \
  --images '{"original":"<repo>/evidence/original/pump_fees/deployed.so","candidate":"<candidate.so>"}' \
  --out .
python3 verify.py --images '{"original":"<repo>/evidence/original/pump_fees/deployed.so","candidate":"<candidate.so>"}'
```

- **Producer.** `producer.py` writes `runtime/receipts.jsonl.gz` (the full per-image result of every case, including logs) and `runtime/report.json.gz` (the per-case summary behind the tables). Two runs produce byte-identical files.
- **Verify.** `verify.py` runs from the packet folder and does the following:
  1. checks `MANIFEST.json`;
  2. checks both image sha256 values against the report;
  3. re-runs all 46 cases;
  4. requires receipts and report that are byte-identical to the stored ones.

  It exits 0 on success and 1 on failure.
- **Environment.** Python 3 with solders 0.27.1 (`solders.litesvm`). No network.

## Limits

- **One host.** Only `withdraw` was run. The buyback handlers' `InterfaceAccount<TokenAccount>` slots use `associated_token::*` constraints and were not exercised here.
- **Token programs.** The token programs are the ones LiteSVM bundles, not mainnet's. The CPI outcomes (0x11, SPL Token invalid account data, the native-tag rent failure) describe those programs and are the same on both sides.
- **Library behavior.** The packet records the behavior of pump_fees' linked decoder. It does not state which spl-token-2022 version either image links.
- **Sibling packet.** The mint-side decoder is measured in `pump-fees-token2022-mint-decode-boundaries-20261030`.
