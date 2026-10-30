# pump_fees `admin_cto_sharing_config`, called directly: constraint order, argument decoding, SharingConfig size and version boundaries, reset sequences

## Problem

`admin_cto_sharing_config` resets a coin's `SharingConfig`.

- `Some(admin)` sets status Active, `admin = admin`, `admin_revoked = false`, and a single shareholder `admin` at 10,000 bps.
- `None` sets status Paused, the zero admin, `admin_revoked = true`, and an empty shareholder list.
- Either way, `version` becomes 2.

The handler does no CPI. It is gated by these account constraints (`programs/pump-fees/src/sharing_admin.rs`):

- `pool_authority`: a signer, and the pump PDA `["pool-authority", mint]`.
- `authority`: a signer, equal to pump `Global.admin_set_creator_authority`.
- `sharing_config`: the PDA `["sharing-config", mint]` with its stored bump, satisfying `has_one = mint`.

In production only pump's `admin_cto` reaches it, by CPI, and that path always passes the canonical accounts. `scripts/fees_admin_cto_differential.py` measures it that way: the three original images, pump CPI, and the sharing-config contents varied.

This packet calls the handler as a top-level instruction against the pump_fees image alone. That reaches what the CPI path cannot:

- every account-constraint failure, and the order in which they fire;
- the `Option<Pubkey>` argument decoder;
- the pump `Global` length boundary;
- SharingConfig length, vec-length and invalid-enum boundaries;
- multi-step reset sequences;
- the interaction with `create_donation_fee_pda`, whose sharing route reads the `status`, `admin` and `admin_revoked` fields that this handler writes.

## Method

- **Programs:** LiteSVM (solders 0.27.1) with only pump_fees loaded, from either the original `evidence/original/pump_fees/deployed.so` or the rebuilt `candidate.so`.
- **Signatures:** `pool_authority` is a pump PDA and cannot sign. Every transaction therefore runs with signature verification off. The wallets that can sign do sign (`Transaction.new_unsigned` + `partial_sign`). Signer flags are still enforced by the program (cases `a-pa-not-signer` and `a-auth-not-signer`).
- **Fixtures:** pump `Global` is synthesized from `programs/pump-fees/idls/pump.json`. Its fixed fields need 740 bytes, and `admin_set_creator_authority` is at bytes 418..450. The default account is 1,088 bytes. SharingConfig defaults to 1,024 bytes, the `space` used by `create_fee_sharing_config`, with version 1, Active, admin OTHER and one shareholder.
- **Donation route:** for the `d-*` cases, a graduated curve plus a pump_amm pool whose `coin_creator` is the sharing PDA route `create_donation_fee_pda` to the sharing config.
- **Determinism:** fixed keypair seeds, a fixed clock (unix 1,700,000,000 unless a case sets it), and `expire_blockhash` before each transaction.
- **Recorded per transaction:** error, every log line, `Program data` events (ResetFeeSharingConfigEvent is decoded), inner-instruction count, return data, wallet lamport deltas, compute units, and the full SharingConfig and donation-PDA state (sha256 + decoded fields, including the count of non-zero bytes after the serialized vec).
- **Comparison:** behavior = everything except compute units and the runtime's `consumed` log lines. Those two are compared separately.

## Result

**60 cases, 74 transactions per image. Behavior mismatches: 0. Log or compute-unit differences: 0.** Every transaction gives the same error, logs (including `consumed` lines), events, state bytes and compute units on both images. The rebuild matches the original on every case.

### a: account constraints and arguments (one transaction each; both images agree)

| case | result | CU |
|---|---|---|
| `a-base-some` / `a-global-length-740` | success, 1 inner instruction (event CPI) | 30,447 |
| `a-base-none` | success | 29,826 |
| `a-new-admin-zero` (`Some(default)`) | 6001 InvalidAdmin | 20,531 |
| `a-new-admin-sharing-pda` (the PDA itself as admin) | success, admin = sharing PDA | 30,447 |
| `a-pa-not-signer` | 3010 AccountNotSigner | 3,632 |
| `a-pa-other-mint` | 2006 ConstraintSeeds | 10,889 |
| `a-auth-not-signer` | 3010 AccountNotSigner | 3,653 |
| `a-auth-mismatch` | 6016 NotAuthorized | 12,101 |
| `a-global-wrong-key` (a pump_fees-owned account) | 3007 AccountOwnedByWrongProgram | 4,363 |
| `a-global-bad-disc` | 3002 AccountDiscriminatorMismatch | 4,097 |
| `a-global-length-450` / `-739` | 3003 AccountDidNotDeserialize | 4,506 / 4,741 |
| `a-mint-b-for-sharing-a` | 2006 ConstraintSeeds (sharing seeds) | 9,389 |
| `a-mint-token2022-owner` | success | 30,473 |
| `a-mint-system-owner` | 3007 | 6,864 |
| `a-mint-uninitialized` | runtime UninitializedAccount | 5,135 |
| `a-mint-length-81` | runtime InvalidAccountData | 4,921 |
| `a-sharing-mint-field-b` | 6007 InvalidSharingConfig (`has_one`) | 14,138 |
| `a-sharing-bump-wrong` | 2006 ConstraintSeeds | 14,147 |
| `a-sharing-owner-pump` | 3007 | 6,019 |
| `a-sharing-bad-disc` | 3002 | 5,753 |
| `a-sharing-absent` | 3012 AccountNotInitialized | 5,508 |
| `a-event-wrong` | 2006 ConstraintSeeds | 20,275 |
| `a-program-wrong` | 3008 InvalidProgramId | 6,109 |
| `a-accounts-6` | 3005 AccountNotEnoughKeys | 5,518 |
| `a-arg-empty` / `a-arg-tag-2` / `a-arg-truncated` | 102 InstructionDidNotDeserialize | 3,492 / 3,754 / 3,498 |
| `a-arg-some-trailing` (one extra byte) | success, the extra byte is ignored | 30,447 |

Check order, from the combined cases:

- A wrong `pool_authority` together with a wrong authority gives 2006, so pool_authority is checked first (`a-order-pa-and-auth`).
- A wrong authority together with a sharing config whose mint field is wrong gives 6016, so the authority is checked first (`a-order-auth-and-sharing`).
- `Some(default)` together with a wrong sharing mint field gives 6007, so the account constraints run before the handler's InvalidAdmin check (`a-order-zero-admin-and-sharing`).
- The event-authority seed check runs after the sharing-config checks: `a-event-wrong` fails at 20,275 CU, later than every sharing-config failure.

### b: SharingConfig contents and size

- **Stored version.** Versions 0, 1, 2 and 255 all reset to 2. The event's `old_version` carries the stored byte (`b-version-*`).
- **Paused input.** A Paused config is reactivated by `Some` (`b-status-paused`).
- **Invalid enum and bool bytes.** A status byte of 2 or an `admin_revoked` byte of 2 fails deserialization with 3003, and the state is unchanged.
- **Size boundary.** On an 80-byte account with 0 holders:
  - `None` succeeds (29,295 CU).
  - `Some` needs 114 bytes. At 80 and 113 bytes it fails with 3004 AccountDidNotSerialize, and state is rolled back. The ResetFeeSharingConfigEvent `Program data` line is still present in the failed transaction's logs, because it is emitted before the exit serialization.
  - At 114 bytes `Some` succeeds.
- **Shrinking does not clear the tail.**
  - 10 stored holders with the tail filled with 0xAA, then `Some`: the vec length becomes 1, and 910 non-zero bytes remain after the serialized vec (`b-ten-holders-some`).
  - The same config with `None`: 944 non-zero bytes remain (`b-ten-holders-none`).
  - The default 1-holder config with `None`: the old holder's 34 bytes remain after the empty vec (`a-base-none`).
  - This is the same on both images. Borsh reads only up to the vec length, so the stale bytes are not read back.
- **Stored holders above the update limit.** 12 stored holders, more than the 10 that `update_fee_shares` accepts, still deserialize and reset (`b-twelve-holders-some`).
- **Bad vec length.** A vec length of `u32::MAX`, or a vec length that runs past the account end, gives 3003.

### c: sequences

- `Some(THIRD)`, `Some(PAYER)`, `None`, `Some(OTHER)`: each step succeeds, and each event's `old_version` is the previous step's 2. `Some` after `None` costs 29,914 CU against 30,447 from a 1-holder state.
- `None` twice: both succeed. The second costs 29,293 CU.
- Changing pump `Global.admin_set_creator_authority` from AUTH to OTHER between resets: AUTH is then rejected with 6016, and OTHER succeeds.
- Two resets in one transaction: the second wins (admin PAYER), and 2 events are logged.
- A reset followed by `Some(default)` in the same transaction: 6001, and the first reset is rolled back to the version-1 state.
- Mints A and B in one transaction: both reset.
- Event timestamps copy the clock unchanged at unix -7 and at i64::MAX.

### d: interaction with `create_donation_fee_pda` (sharing route)

- **After `None`.** The old admin OTHER and the fee-program authority AUTH both get 6016 from create. The stored admin is the zero key, so no payer can match.
- **After `Some(THIRD)`.** OTHER gets 6016, and THIRD creates the donation PDA (44,977 CU).
- **Reactivating a revoked config.** A revoked + Paused config rejects OTHER with 6009 SharingConfigAdminRevoked. `Some(OTHER)` clears both, and OTHER then creates.
- **Same transaction, reset first.** `Some(THIRD)` followed by THIRD's create succeeds (75,422 CU). The create reads the value written earlier in the transaction.
- **Same transaction, create first.** OTHER's create followed by `None` succeeds, and the PDA stays. A later create of a second config id by OTHER gets 6016.

## Files

- `producer.py` defines the cases and writes `runtime/receipts.jsonl.gz` (both images' full receipts per case) and `runtime/report.json.gz` (image sha256, receipts sha256, a per-case summary with errors and CU per transaction, and the mismatch lists).
- `verify.py` checks:
  - MANIFEST (file set and hashes);
  - the receipts hash;
  - the image sha256 against the report;
  - it then re-runs every case on both images, compares each to the stored receipt, and recomputes the summary.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "...", "candidate": "..."}'
```

Recorded image sha256:

- original: `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`
- candidate: `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`

Receipts sha256: `ee3d44cceefdbc473f27f7573088dd8bb41f138dbdf872d7005925e1b3978855`. Two producer runs gave byte-identical runtime files.

## Scope

- This packet measures behavior, not source identity.
- Signature verification is off only so that the PDA signer slot can be filled.
- It does not measure the pump-side `admin_cto` CPI path; `fees_admin_cto_differential.py` covers that.
