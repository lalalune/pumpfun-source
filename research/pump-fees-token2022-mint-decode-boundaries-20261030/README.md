# pump_fees `InterfaceAccount<Mint>` decoding: Token-2022 layout boundaries (length, account type, padding, TLV, base-field tags, owner)

## Problem

Every pump_fees handler that takes a mint declares it as
`InterfaceAccount<'info, anchor_spl::token_interface::Mint>`. Examples are
`programs/pump-fees/src/sharing_admin.rs` (`admin_cto_sharing_config`),
`sharing_update.rs`, `create_fee_sharing_config.rs` and `buyback/mod.rs`.
Anchor checks that the account owner is SPL Token or Token-2022. It then decodes
the bytes with the spl-token-2022 mint unpacker that is linked into the
pump_fees binary.

That decoder is library code, so the reconstruction only reproduces it if it
links the same library version with the same behavior. Existing measurements
cover four mint inputs only:

- a base 82-byte mint;
- an 81-byte mint;
- an uninitialized mint;
- a Token-2022 mint with a valid TransferFeeConfig.

They are in `research/pump-fees-admin-cto-sharing-direct-20261030` and
`research/pump-fees-buyback-init-withdraw-sequences-20261030`. No existing
packet or open PR measures the extended-layout boundaries:

- account length around 82 / 165 / 166 / 355;
- the account-type byte at offset 165;
- the padding bytes [82, 165);
- the TLV extension area;
- the COption / bool tags of the base fields;
- the same layouts under the legacy SPL Token owner.

## Method

- **Host.** The host is `admin_cto_sharing_config`, called directly. It makes no CPI, so only the pump_fees image is loaded.
- **Varied input.** Each case changes exactly one input: the bytes and owner of the `mint` account. Every other account is canonical:
  - pump `Global`: 1,088 bytes, `admin_set_creator_authority = AUTH`;
  - SharingConfig: version 1, Active, admin OTHER, one shareholder, 1,024 bytes;
  - argument: `Some(THIRD)`.
- **Signing.** `pool_authority` is a pump PDA and cannot sign. Transactions therefore run with LiteSVM signature verification off. The wallets that can sign still sign.
- **Isolation.** Each case is one transaction on a fresh LiteSVM per image. The same case runs on both images.
- **Determinism.** Fixed keypair seeds, fixed clock (unix 1,700,000,000).
- **What is compared.** The error, the full log list (minus the runtime `consumed` lines), the SharingConfig bytes after the transaction, and whether the mint bytes changed. Compute units are compared separately.
- **Extended mint layout.** The 82-byte base, zero padding to 165, an account-type byte at 165, then TLV entries (u16 type, u16 length, value).

| image | sha256 |
|---|---|
| original `evidence/original/pump_fees/deployed.so` | `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e` |
| candidate (rebuild) | `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900` |

The candidate was built by `scripts/build_partial_candidate.py` with platform-tools v1.44 / cargo-build-sbf 2.1.21. Source tree `7eb3b25ef7ee45dcba86f2af79344297e98a091d`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.

## Result

**55 cases. The original and the rebuild match in all 55: same error, same logs, same compute units and same resulting state. There is no divergence.**

- **29 successes.** Each one resets the SharingConfig to version 2 with admin THIRD.
- **26 failures.** Each one leaves the SharingConfig unchanged at version 1. The breakdown:
  - 23 are `ProgramError InvalidAccountData`;
  - 2 are `ProgramError UninitializedAccount`;
  - 1 is `3007 AccountOwnedByWrongProgram`.
- **The mint.** The mint account bytes are unchanged in all 55 cases.
- **Error attribution.** Every failure log names `caused by account: mint`.

| case | mint owner | mint bytes | result (both images) | CU (both images) | orig = rebuild |
|---|---|---|---|---|---|
| `l-82-base` | token22 | 82 | success | 27,478 | yes |
| `l-83-zero-tail` | token22 | 83 | ProgramError InvalidAccountData | 5,057 | yes |
| `l-100-zero-tail` | token22 | 100 | ProgramError InvalidAccountData | 5,057 | yes |
| `l-164-zero-tail` | token22 | 164 | ProgramError InvalidAccountData | 5,057 | yes |
| `l-165-zero-tail` | token22 | 165 | ProgramError InvalidAccountData | 5,057 | yes |
| `l-166-type-mint` | token22 | 166 | ProgramError InvalidAccountData | 5,057 | yes |
| `l-167-type-mint-zero-tail` | token22 | 167 | success | 27,574 | yes |
| `l-168-type-mint-zero-tail` | token22 | 168 | success | 27,574 | yes |
| `l-169-type-mint-zero-tail` | token22 | 169 | success | 27,574 | yes |
| `l-170-type-mint-zero-tlv` | token22 | 170 | success | 27,574 | yes |
| `l-355-multisig-length` | token22 | 355 | ProgramError InvalidAccountData | 4,946 | yes |
| `l-354-type-mint` | token22 | 354 | success | 27,574 | yes |
| `l-356-type-mint` | token22 | 356 | success | 27,574 | yes |
| `l-10240-type-mint` | token22 | 10240 | success | 27,574 | yes |
| `t-type-0-uninitialized` | token22 | 170 | ProgramError InvalidAccountData | 5,149 | yes |
| `t-type-2-account` | token22 | 170 | ProgramError InvalidAccountData | 5,149 | yes |
| `t-type-3-invalid-3` | token22 | 170 | ProgramError InvalidAccountData | 5,149 | yes |
| `t-type-255-invalid-255` | token22 | 170 | ProgramError InvalidAccountData | 5,149 | yes |
| `t-type-2-with-tlv` | token22 | 278 | ProgramError InvalidAccountData | 5,149 | yes |
| `p-pad-82-nonzero` | token22 | 170 | ProgramError InvalidAccountData | 5,146 | yes |
| `p-pad-164-nonzero` | token22 | 170 | ProgramError InvalidAccountData | 5,146 | yes |
| `p-pad-164-nonzero-no-type` | token22 | 165 | ProgramError InvalidAccountData | 5,057 | yes |
| `e-transfer-fee-config` | token22 | 278 | success | 27,574 | yes |
| `e-close-authority` | token22 | 202 | success | 27,574 | yes |
| `e-two-extensions` | token22 | 314 | success | 27,574 | yes |
| `e-duplicate-extension` | token22 | 238 | success | 27,574 | yes |
| `e-account-extension-in-mint` | token22 | 178 | success | 27,574 | yes |
| `e-unknown-type-65535` | token22 | 170 | success | 27,574 | yes |
| `e-unknown-type-1000-len-4` | token22 | 174 | success | 27,574 | yes |
| `e-wrong-length-for-type` | token22 | 201 | success | 27,574 | yes |
| `e-length-past-end` | token22 | 186 | success | 27,574 | yes |
| `e-partial-header-1` | token22 | 167 | success | 27,574 | yes |
| `e-partial-header-2` | token22 | 168 | success | 27,574 | yes |
| `e-partial-header-3` | token22 | 169 | success | 27,574 | yes |
| `e-header-only` | token22 | 170 | success | 27,574 | yes |
| `e-zero-type-then-entry` | token22 | 206 | success | 27,574 | yes |
| `e-entry-then-garbage` | token22 | 205 | success | 27,574 | yes |
| `b-init-2` | token22 | 82 | ProgramError InvalidAccountData | 4,988 | yes |
| `b-init-0` | token22 | 82 | ProgramError UninitializedAccount | 5,166 | yes |
| `b-init-0-extended` | token22 | 170 | ProgramError UninitializedAccount | 5,166 | yes |
| `b-init-2-extended` | token22 | 170 | ProgramError InvalidAccountData | 4,988 | yes |
| `b-auth-tag-0` | token22 | 82 | success | 27,473 | yes |
| `b-auth-tag-2` | token22 | 82 | ProgramError InvalidAccountData | 4,969 | yes |
| `b-auth-tag-256` | token22 | 82 | ProgramError InvalidAccountData | 4,971 | yes |
| `b-freeze-tag-1` | token22 | 82 | success | 27,484 | yes |
| `b-freeze-tag-2` | token22 | 82 | ProgramError InvalidAccountData | 4,992 | yes |
| `b-decimals-255-supply-max` | token22 | 82 | success | 27,478 | yes |
| `o-token-82-base` | token | 82 | success | 27,452 | yes |
| `o-token-166-type-mint` | token | 166 | ProgramError InvalidAccountData | 5,031 | yes |
| `o-token-170-type-mint` | token | 170 | success | 27,548 | yes |
| `o-token-transfer-fee-config` | token | 278 | success | 27,548 | yes |
| `o-token-83-zero-tail` | token | 83 | ProgramError InvalidAccountData | 5,031 | yes |
| `o-token-355-multisig-length` | token | 355 | ProgramError InvalidAccountData | 4,920 | yes |
| `o-token-type-2` | token | 170 | ProgramError InvalidAccountData | 5,123 | yes |
| `o-system-166-type-mint` | system | 166 | 3007 AccountOwnedByWrongProgram | 6,864 | yes |

### What the measurements show (same on both images)

- **Length.**
  - 82 bytes is accepted.
  - 83, 100, 164 and 165 bytes (zero tail, no type byte) are rejected with InvalidAccountData at 5,057 CU.
  - 166 bytes is also rejected at 5,057 CU, even with account type 1 at offset 165.
  - 167, 168, 169 and 170 bytes with type 1 and a zero tail are accepted at 27,574 CU. So the smallest accepted extended mint here is 167 bytes, not 166.
  - 355 bytes is rejected at 4,946 CU. That is 111 CU below the 5,057 CU rejection, so it takes an earlier path.
  - 354, 356 and 10,240 bytes are accepted.
- **Account-type byte.** At 170 bytes, type bytes 0, 2, 3 and 255 are rejected at 5,149 CU. So is type 2 followed by a valid TransferFeeConfig entry. Only type 1 is accepted.
- **Padding.**
  - A non-zero byte at offset 82 or 164 of a 170-byte type-1 account is rejected at 5,146 CU.
  - At 165 bytes (no type byte) the same non-zero byte is rejected at 5,057 CU, the same cost as a zero tail.
- **TLV area.** It is not validated on this path. All 15 `e-*` cases are accepted at 27,574 CU, the same cost as an empty TLV area. They include:
  - unknown extension types 1000 and 65535;
  - an account-side extension (TransferFeeAmount) in a mint;
  - a declared length that does not fit the type (31 for MintCloseAuthority);
  - a declared length running past the account end;
  - 1–3 byte partial headers and a header without its value;
  - a duplicate extension;
  - trailing garbage.
- **Base-field tags.**
  - `is_initialized = 0` gives UninitializedAccount at 5,166 CU. `is_initialized = 2` gives InvalidAccountData at 4,988 CU. Both results are the same at 82 and 170 bytes.
  - `mint_authority` tags 0 and 1 are accepted. Tags 2 and 256 are rejected (4,969 / 4,971 CU).
  - `freeze_authority` tag 1 is accepted. Tag 2 is rejected (4,992 CU).
  - Decimals 255 with supply u64::MAX is accepted.
- **Owner.**
  - An account owned by legacy SPL Token is decoded with the same rules. 82 bytes, 170-byte type 1 and a TransferFeeConfig layout are accepted. 83 bytes, 166 bytes, 355 bytes and type 2 are rejected.
  - Each SPL Token path costs 26 CU less than the Token-2022 path with the same bytes: 27,452 vs 27,478; 27,548 vs 27,574; 5,031 vs 5,057; 4,920 vs 4,946; 5,123 vs 5,149 (type 2 at 170 bytes).
  - A System-owned account fails earlier with Anchor 3007 at 6,864 CU.

## Reproduce

```
python3 producer.py --root <repo> \
  --images '{"original":"<repo>/evidence/original/pump_fees/deployed.so","candidate":"<candidate.so>"}' \
  --out .
python3 verify.py --images '{"original":"<repo>/evidence/original/pump_fees/deployed.so","candidate":"<candidate.so>"}'
```

- **Producer.** `producer.py` writes `runtime/receipts.jsonl.gz` (the full per-image result of every case, including logs) and `runtime/report.json.gz` (the per-case summary used for the table above). Two runs produce byte-identical files.
- **Verify.** `verify.py` runs from the packet folder and does the following:
  1. checks `MANIFEST.json`;
  2. checks both image sha256 values against the report;
  3. re-runs all 55 cases;
  4. requires receipts and report that are byte-identical to the stored ones.

  It exits 0 on success and 1 on failure.
- **Environment.** Python 3 with solders 0.27.1 (`solders.litesvm`). No network.

## Limits

- **One host.** Only `admin_cto_sharing_config` was run. The other `InterfaceAccount<Mint>` slots use the same Anchor type but were not exercised here. Some add constraints, such as `mint::token_program` on `update_fee_shares_v2`'s `quote_mint`.
- **Synthetic layouts.** The Token-2022 and SPL Token programs are not loaded, so no token-program instruction runs. Most of these layouts cannot be produced by the real token programs; they test the decoder only.
- **Library behavior.** The packet records how pump_fees' linked decoder behaves. It does not state which spl-token-2022 version either image links.
- **Sibling packet.** The token-account decoder (`withdraw`) is measured in `pump-fees-token2022-account-decode-boundaries-20261030`.
