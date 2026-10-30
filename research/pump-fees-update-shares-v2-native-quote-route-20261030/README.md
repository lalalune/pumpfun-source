# pump_fees update_fee_shares_v2 on a native-quote curve: quote check order, WSOL pool slot, AMM v2 transfer

## Question

`update_fee_shares_v2` has two payout preparations. On a curve whose stored `quote_mint` (bytes
[83,115)) is a non-zero SPL mint, it uses the paired holder+ATA stride; the token-quote packet
(`pump-fees-update-shares-v2-token-quote-rescale`) measured that. When the stored quote is the zero key
(a **native** curve), the handler takes a different route:

1. `version != 1` (`FeeSharesAlreadyUpdated`), then the admin check (`NotAuthorized`).
2. The passed `quote_mint` must be WSOL (`InvalidQuoteMint` otherwise). Before the handler runs,
   Anchor seed-checks the `pump_creator_vault_ata` account against the **passed** quote mint.
3. `preprocess_remaining` with the WSOL pool PDA on a complete curve.
4. If all four reserves are 0 and the AMM coin-creator vault WSOL ATA is not System-owned, a CPI to
   `pump_amm::transfer_creator_fees_to_pump_v2`.
5. The **single-stride** (holders only) executable rescale, then `pump::distribute_creator_fees_v2`
   (skipped when no holder survives), then the new-share validation.

This packet measures that native route on both pump_fees images. The check order differs from v1
`update_fee_shares`, where the quote gate runs before the version check. The v1 route is measured in
the companion packet `pump-fees-update-shares-graduated-amm-route-20261030`.

## Result

**39 cases, 59 transaction steps. Original and rebuilt pump_fees match in all 39 cases.** Every
recorded field matches: error, full logs, decoded events, lamport deltas, account hashes and the
decoded sharing config. Compute units match in every step. There is no divergence.

What the cases measure (all values identical on both images):

- **Check order (v2 native).** With a non-WSOL quote mint passed:
  - a version-1 config still fails with `FeeSharesAlreadyUpdated` (6024);
  - a wrong signer still fails with `NotAuthorized` (6016);
  - otherwise the result is `InvalidQuoteMint` (6034, 50,989 CU), also on a graduated curve without a
    pool slot.

  So the order is version, then authority, then quote, then pool slot. In v1 the quote gate comes
  first.
- **Account-level seed check first.** If the non-WSOL quote mint is passed but the creator-vault and
  AMM ATA slots are the WSOL ATAs, Anchor fails `pump_creator_vault_ata` with `ConstraintSeeds` (2006)
  at 27,438 CU, before any handler check.
- **Curve length.** 114-byte and 82-byte curves count as native and pay out. An 81-byte curve fails
  deserialization (3003).
- **Single stride.** Passing six remaining accounts (holders plus repeated holder keys, as if they
  were ATA partners) for three holders still pays A and B 500,000,000 each. The extra accounts are
  ignored after the rescale. With one holder missing, the result is `NotEnoughRemainingAccounts`
  (6013).
- **Pool slot.** These match the v1 route:
  - `ConstraintSeeds` for no slot, a wrong key, or the pool first;
  - accepted when the pool is missing, foreign-owned or 286 bytes long;
  - `PoolCreatorFeesNotSwept` (6033) at 287 and 301 bytes with fees 1.
- **AMM v2 transfer with WSOL.** A funded AMM WSOL ATA (500,000,000) is drained into the pump creator
  vault's **lamports**. The payout is 1,500,000,000 (750,000,000 each).
  - The pump creator-vault WSOL ATA is untouched: its lamport delta is 0 whether it is absent, holds
    0 or holds 7.
  - With all holders executable, the moved 500,000,000 stays in the creator vault.
  - An invalid new total (6014) reverts everything after both CPIs ran (234,302 CU).
- **State transition.** Each successful u1 sets `admin_revoked`, and the follow-up u2 fails with
  `SharingConfigAdminRevoked` (6009) in all 20 successful cases.

### Per-case table (u1 = measured update; deltas in lamports; u1 CU is identical on both images)

Holders: `A`, `B` and `J` are plain wallets. `X` is the SPL Token program (executable). Most cases use
the old list `[A 2500, X 5000, B 2500]`. `-no-exec` cases use `[A 5000, B 5000]`. The new list is
`[J 10000]` unless noted. The pump creator vault holds 1,000,000,000 above rent unless noted.

| case | u1 result | AMM CPI | pump CPI | creator vault Δ | AMM WSOL ATA Δ | pump vault WSOL ATA Δ | holder Δ | u1 CU (orig = cand) | u2 | match |
|---|---|---|---|---|---|---|---|---|---|---|
| `r-native-exec-middle` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 137,175 | SharingConfigAdminRevoked (6009) | match |
| `r-native-no-exec` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 136,349 | SharingConfigAdminRevoked (6009) | match |
| `r-native-all-executable` | ok | no | no | 0 | 0 | 0 | - | 53,296 | SharingConfigAdminRevoked (6009) | match |
| `r-native-with-ata-partners` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 137,452 | SharingConfigAdminRevoked (6009) | match |
| `r-native-missing-last-holder` | NotEnoughRemainingAccounts (6013) | no | no | 0 | 0 | 0 | - | 43,761 | - | match |
| `r-native-zero-vault` | ok | no | yes | 0 | 0 | 0 | - | 126,670 | SharingConfigAdminRevoked (6009) | match |
| `q-other-quote-passed` | InvalidQuoteMint (6034) | no | no | 0 | 0 | 0 | - | 50,989 | - | match |
| `q-other-quote-wsol-atas` | ConstraintSeeds (2006) | no | no | 0 | 0 | 0 | - | 27,438 | - | match |
| `q-other-quote-graduated-no-slot` | InvalidQuoteMint (6034) | no | no | 0 | 0 | 0 | - | 50,989 | - | match |
| `q-other-quote-version-1` | FeeSharesAlreadyUpdated (6024) | no | no | 0 | 0 | 0 | - | 50,270 | - | match |
| `q-other-quote-wrong-authority` | NotAuthorized (6016) | no | no | 0 | 0 | 0 | - | 50,310 | - | match |
| `q-curve-len-114` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 136,832 | SharingConfigAdminRevoked (6009) | match |
| `q-curve-len-82` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 136,804 | SharingConfigAdminRevoked (6009) | match |
| `q-curve-len-81` | AccountDidNotDeserialize (3003) | no | no | 0 | 0 | 0 | - | 10,246 | - | match |
| `o-version-1-wrong-authority` | FeeSharesAlreadyUpdated (6024) | no | no | 0 | 0 | 0 | - | 42,770 | - | match |
| `o-wrong-authority-graduated-no-slot` | NotAuthorized (6016) | no | no | 0 | 0 | 0 | - | 42,810 | - | match |
| `g-no-pool-slot` | ConstraintSeeds (2006) | no | no | 0 | 0 | 0 | - | 48,202 | - | match |
| `g-pool-wrong-key` | ConstraintSeeds (2006) | no | no | 0 | 0 | 0 | - | 48,460 | - | match |
| `g-pool-missing-account` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 142,143 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-swept` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 142,177 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-unswept-1` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | 0 | - | 47,991 | - | match |
| `g-pool-len-287-unswept` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | 0 | - | 47,991 | - | match |
| `g-pool-len-286-unswept` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 142,173 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-foreign-owner-unswept` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 142,143 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-first-not-last` | ConstraintSeeds (2006) | no | no | 0 | 0 | 0 | - | 48,460 | - | match |
| `g-pool-other-quote-passed` | InvalidQuoteMint (6034) | no | no | 0 | 0 | 0 | - | 51,247 | - | match |
| `g-pool-other-quote-wsol-atas` | ConstraintSeeds (2006) | no | no | 0 | 0 | 0 | - | 27,696 | - | match |
| `a-amm-ata-funded` | ok | yes | yes | -1,000,000,000 | -500,000,000 | 0 | A +750,000,000, B +750,000,000 | 243,720 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-no-exec` | ok | yes | yes | -1,000,000,000 | -500,000,000 | 0 | A +750,000,000, B +750,000,000 | 242,894 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-empty` | ok | yes | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 243,720 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-pump-vault-ata-exists` | ok | yes | yes | -1,000,000,000 | -500,000,000 | 0 | A +750,000,000, B +750,000,000 | 243,720 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-pump-vault-ata-holds` | ok | yes | yes | -1,000,000,000 | -500,000,000 | 0 | A +750,000,000, B +750,000,000 | 243,720 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-pump-vault-empty` | ok | yes | yes | 0 | -500,000,000 | 0 | A +250,000,000, B +250,000,000 | 243,722 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-nonzero-reserves` | ok | no | yes | -1,000,000,000 | 0 | 0 | A +500,000,000, B +500,000,000 | 137,175 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-wrong-mint` | error (11) | yes | no | 0 | 0 | 0 | - | 120,660 | - | match |
| `a-amm-ata-funded-all-executable` | ok | yes | no | 500,000,000 | -500,000,000 | 0 | - | 159,841 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-graduated-swept` | ok | yes | yes | -1,000,000,000 | -500,000,000 | 0 | A +750,000,000, B +750,000,000 | 248,688 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-graduated-unswept` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | 0 | - | 47,991 | - | match |
| `a-amm-ata-funded-invalid-new` | InvalidShareTotal (6014) | yes | yes | 0 | 0 | 0 | - | 234,302 | - | match |

## Setup

- **pump_fees under test:**
  - original `evidence/original/pump_fees/deployed.so`, sha256
    `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`;
  - rebuilt candidate, sha256 `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`. It was
    built by `scripts/build_partial_candidate.py` (platform-tools v1.44 / cargo-build-sbf 2.1.21) from
    source tree `476838a67af2e9cfce5d4a1f44b83436c6335836` (repo commit
    `094a06f18df738d41e77070c1a009e135671ac1a`).
- **CPI dependencies, identical on both sides:**
  - `evidence/original/pump/deployed.so` (`7a19affa…f7b02d`);
  - `evidence/original/pump_amm/deployed.so` (`6a7ad345…4d8ff7`).
- **Synthetic state.** The keypairs use fixed seeds and the clock is fixed. Each case and image gets a
  fresh LiteSVM (solders 0.27.1, log limit off). Accounts:
  - a 740-byte pump Global;
  - a 200-byte BondingCurve with quote_mint = zero key, whose creator is the sharing config;
  - a SharingConfig v2;
  - the pump creator vault;
  - an optional pool at the WSOL pool PDA;
  - optional WSOL ATAs for the AMM coin-creator vault and the pump creator vault, with
    `is_native = Some(rent)` and lamports = rent + amount.
- **Other quote mint.** "Other quote" is a plain SPL mint. Unless the case pins the ATA slots to
  WSOL (`-wsol-atas`), they are derived from the passed quote mint.
- **Step u2** runs only after a successful u1. It is a system transfer of 10,000,000 lamports to the
  creator vault followed by a second `update_fee_shares_v2`.

## Files

- `producer.py`: case table, LiteSVM runner, report builder.
- `verify.py`: re-executes every receipt on both images.
- `runtime/receipts.jsonl.gz`: one row per case, with full per-step receipts for both images.
- `runtime/report.json.gz`: image hashes, counts, mismatch lists and the per-case summary.
- `MANIFEST.json`: sha256 and size of every other file.

## Reproduce

From the repository root (`<candidate.so>` = the rebuilt pump_fees image):

```
python3 research/pump-fees-update-shares-v2-native-quote-route-20261030/producer.py --root . \
  --images '{"original": "evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' \
  --out research/pump-fees-update-shares-v2-native-quote-route-20261030
cd research/pump-fees-update-shares-v2-native-quote-route-20261030
python3 verify.py --images '{"original": "../../evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

The producer is deterministic: two runs give byte-identical `runtime/` files. `verify.py` performs these
checks and exits 0 only when all of them pass, 1 otherwise:

1. the MANIFEST hashes;
2. the four image hashes against the report;
3. a replay of all 39 cases on both images, which must give the same receipts, compute units included;
4. a rebuild of the report summary from the replay.
