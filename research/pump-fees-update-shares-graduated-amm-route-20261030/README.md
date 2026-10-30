# pump_fees update_fee_shares (v1): graduated pool slot, pump_amm WSOL transfer and legacy quote gate

## Question

`update_fee_shares` (v1, native-SOL quote) does several things before it pays the old team through
`pump::distribute_creator_fees` and stores the new list. The earlier v1 packet
(`pump-fees-update-shares-executable-rescale`) measured only the executable-holder rescale, on an
**active curve with non-zero reserves**. That curve skips the pre-payout routes. This packet measures
those routes on both pump_fees images:

1. **Legacy quote gate.** The curve's `quote_mint` at bytes [83,115) must be the zero key, otherwise
   `UnsupportedQuoteMint`. A curve shorter than 115 bytes counts as native.
2. **Check order** between the quote gate, `version != 1` (`FeeSharesAlreadyUpdated`) and the
   sharing-config admin check (`NotAuthorized`).
3. **Graduated curve** (`complete = 1`). `preprocess_remaining` requires the canonical WSOL pool PDA
   `pool(0, pool-authority(mint), mint, WSOL)` as the **last** remaining account (`ConstraintSeeds`
   otherwise). It strips that account. If the account is owned by pump_amm and is at least 287 bytes
   long, the u64 at [279,287) must be 0 (`PoolCreatorFeesNotSwept`).
4. **pump_amm route.** If all four curve reserves are 0 and the AMM coin-creator vault WSOL ATA is not
   System-owned, pump_fees first CPIs `pump_amm::transfer_creator_fees_to_pump`, which moves the ATA's
   WSOL into the pump creator vault. It then rescales and distributes.
5. The payout CPI is skipped when every stored holder is executable. New-share validation runs last.

## Result

**44 cases, 66 transaction steps. Original and rebuilt pump_fees match in all 44 cases.** Every
recorded field matches: error, full logs, decoded events, lamport deltas, account hashes and the
decoded sharing config. Compute units match in every step. There is no divergence.

What the cases measure (all values identical on both images):

- **Quote gate first.** A non-zero curve quote mint returns `UnsupportedQuoteMint` (6031) at 41,029 CU.
  It does so even when the config is also version 1 or the signer is wrong. Version 1 returns
  `FeeSharesAlreadyUpdated` (6024) even with the wrong signer. A wrong signer returns `NotAuthorized`
  (6016) before the graduated pool-slot check (`o-wrong-authority-graduated-no-slot`) and before the
  unswept-pool check (`g-pool-unswept-wrong-authority`).
- **Curve length.** Curves of 115, 114, 83 and 82 bytes all pass the gate and pay out. An 81-byte curve
  fails Anchor deserialization (`AccountDidNotDeserialize` 3003, 10,005 CU) before the handler runs.
- **Pool slot.** These all return `ConstraintSeeds` (2006): no pool slot, a wrong key, and the pool PDA
  placed first instead of last.
  - The pool account is accepted (stripped, then payout) when it is missing (no account at the PDA),
    owned by another program, or 286 bytes long. It is also accepted at 301 bytes with creator fees
    at 0.
  - `PoolCreatorFeesNotSwept` (6033) fires at 287 bytes with fees 1, at 301 bytes with fees 1, and at
    301 bytes with fees u64::MAX.
  - With only the pool slot, or with one holder missing, the result is `NotEnoughRemainingAccounts`
    (6013).
  - A graduated curve with non-zero reserves takes the same pool-slot path and pays out the same amounts.
- **AMM transfer.** With a zero-reserve curve and an existing AMM WSOL ATA holding 500,000,000, the
  AMM CPI runs and the ATA drops by 500,000,000. The payout then carries 1,500,000,000 lamports
  (`DistributeCreatorFeesEvent.distributed`), so A and B each receive 750,000,000. Other measured
  points:
  - an ATA with amount 0 still triggers the CPI;
  - an ATA with amount 1 moves 1 lamport;
  - with an empty pump vault the payout is 250,000,000 each;
  - with non-zero reserves, or with no ATA, the CPI is skipped;
  - a wrong-mint ATA fails inside SPL Token (custom error 11) under the AMM CPI.
- **All holders executable** (`[X 10000]`). The payout CPI is skipped. With an AMM transfer, the
  500,000,000 moved by the AMM **stays in the pump creator vault** (+500,000,000), and the list is
  replaced. With an empty vault, pump logs `Insufficient fees for distribution` and the update still
  succeeds.
- **Ordering of the last check.** An invalid new total (`[J 9999]`) fails with `InvalidShareTotal`
  (6014) **after** both the AMM and pump CPIs ran (221,406 CU). The whole transaction reverts, with
  0 lamport and token deltas.
- **State transition.** Every successful u1 sets `admin_revoked = 1`. The follow-up u2 then fails with
  `SharingConfigAdminRevoked` (6009) in all 22 successful cases.

### Per-case table (u1 = measured update; deltas in lamports; u1 CU is identical on both images)

Holders: `A`, `B` and `J` are plain wallets. `X` is the SPL Token program (executable). Most cases use
the old list `[A 2500, X 5000, B 2500]`. `-no-exec` cases use `[A 5000, B 5000]`. The new list is
`[J 10000]` unless noted. The pump creator vault holds 1,000,000,000 above rent unless noted.

| case | u1 result | AMM CPI | pump CPI | creator vault Δ | AMM WSOL ATA Δ | holder Δ | u1 CU (orig = cand) | u2 | match |
|---|---|---|---|---|---|---|---|---|---|
| `g-no-pool-slot` | ConstraintSeeds (2006) | no | no | 0 | 0 | - | 46,314 | - | match |
| `g-no-pool-slot-no-exec` | ConstraintSeeds (2006) | no | no | 0 | 0 | - | 46,157 | - | match |
| `g-pool-wrong-key` | ConstraintSeeds (2006) | no | no | 0 | 0 | - | 46,572 | - | match |
| `g-pool-missing-account` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 132,510 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-swept` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 132,544 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-swept-no-exec` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 131,893 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-unswept-1` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | - | 46,103 | - | match |
| `g-pool-unswept-u64-max` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | - | 46,103 | - | match |
| `g-pool-unswept-no-exec` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | - | 45,946 | - | match |
| `g-pool-len-287-unswept` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | - | 46,103 | - | match |
| `g-pool-len-286-unswept` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 132,540 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-foreign-owner-unswept` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 132,510 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-first-not-last` | ConstraintSeeds (2006) | no | no | 0 | 0 | - | 46,572 | - | match |
| `g-pool-only-no-holders` | NotEnoughRemainingAccounts (6013) | no | no | 0 | 0 | - | 46,118 | - | match |
| `g-pool-swept-nonzero-reserves` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 132,502 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-swept-missing-last-holder` | NotEnoughRemainingAccounts (6013) | no | no | 0 | 0 | - | 46,714 | - | match |
| `g-pool-swept-all-executable` | ok | no | no | 0 | 0 | - | 56,243 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-swept-zero-vault` | ok | no | yes | 0 | 0 | - | 122,028 | SharingConfigAdminRevoked (6009) | match |
| `g-pool-unswept-wrong-authority` | NotAuthorized (6016) | no | no | 0 | 0 | - | 41,346 | - | match |
| `a-amm-ata-funded` | ok | yes | yes | -1,000,000,000 | -500,000,000 | A +750,000,000, B +750,000,000 | 230,826 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-no-exec` | ok | yes | yes | -1,000,000,000 | -500,000,000 | A +750,000,000, B +750,000,000 | 230,175 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-empty` | ok | yes | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 230,826 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-one-lamport` | ok | yes | yes | -999,999,999 | -1 | A +500,000,000, B +500,000,000 | 230,826 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-pump-vault-empty` | ok | yes | yes | 0 | -500,000,000 | A +250,000,000, B +250,000,000 | 230,828 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-nonzero-reserves` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 127,534 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-absent-zero-reserves` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 127,576 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-wrong-mint` | error (11) | yes | no | 0 | 0 | - | 115,514 | - | match |
| `a-amm-ata-funded-all-executable` | ok | yes | no | 500,000,000 | -500,000,000 | - | 154,526 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-graduated-swept` | ok | yes | yes | -1,000,000,000 | -500,000,000 | A +750,000,000, B +750,000,000 | 235,794 | SharingConfigAdminRevoked (6009) | match |
| `a-amm-ata-funded-graduated-unswept` | PoolCreatorFeesNotSwept (6033) | no | no | 0 | 0 | - | 46,103 | - | match |
| `a-amm-ata-funded-graduated-no-slot` | ConstraintSeeds (2006) | no | no | 0 | 0 | - | 46,314 | - | match |
| `a-amm-ata-funded-invalid-new` | InvalidShareTotal (6014) | yes | yes | 0 | 0 | - | 221,406 | - | match |
| `c-curve-other-quote` | UnsupportedQuoteMint (6031) | no | no | 0 | 0 | - | 41,029 | - | match |
| `c-curve-other-quote-version-1` | UnsupportedQuoteMint (6031) | no | no | 0 | 0 | - | 41,029 | - | match |
| `c-curve-other-quote-wrong-authority` | UnsupportedQuoteMint (6031) | no | no | 0 | 0 | - | 41,029 | - | match |
| `c-curve-len-115` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 127,319 | SharingConfigAdminRevoked (6009) | match |
| `c-curve-len-114` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 127,208 | SharingConfigAdminRevoked (6009) | match |
| `c-curve-len-83` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 127,208 | SharingConfigAdminRevoked (6009) | match |
| `c-curve-len-82` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 127,180 | SharingConfigAdminRevoked (6009) | match |
| `c-curve-len-81` | AccountDidNotDeserialize (3003) | no | no | 0 | 0 | - | 10,005 | - | match |
| `c-curve-len-114-graduated-swept` | ok | no | yes | -1,000,000,000 | 0 | A +500,000,000, B +500,000,000 | 132,218 | SharingConfigAdminRevoked (6009) | match |
| `o-version-1-graduated-no-slot` | FeeSharesAlreadyUpdated (6024) | no | no | 0 | 0 | - | 41,047 | - | match |
| `o-version-1-wrong-authority` | FeeSharesAlreadyUpdated (6024) | no | no | 0 | 0 | - | 41,047 | - | match |
| `o-wrong-authority-graduated-no-slot` | NotAuthorized (6016) | no | no | 0 | 0 | - | 41,088 | - | match |

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
  - a 200-byte BondingCurve whose creator is the sharing config;
  - a SharingConfig v2;
  - the pump creator vault;
  - an optional 301-byte (or 286/287-byte) pool at the WSOL pool PDA;
  - an optional WSOL ATA for the AMM coin-creator vault, with `is_native = Some(rent)` and
    lamports = rent + amount.
- **Step u2** runs only after a successful u1. It is a system transfer of 10,000,000 lamports to the
  creator vault followed by a second `update_fee_shares`.

## Files

- `producer.py`: case table, LiteSVM runner, report builder.
- `verify.py`: re-executes every receipt on both images.
- `runtime/receipts.jsonl.gz`: one row per case, with full per-step receipts for both images.
- `runtime/report.json.gz`: image hashes, counts, mismatch lists and the per-case summary.
- `MANIFEST.json`: sha256 and size of every other file.

## Reproduce

From the repository root (`<candidate.so>` = the rebuilt pump_fees image):

```
python3 research/pump-fees-update-shares-graduated-amm-route-20261030/producer.py --root . \
  --images '{"original": "evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' \
  --out research/pump-fees-update-shares-graduated-amm-route-20261030
cd research/pump-fees-update-shares-graduated-amm-route-20261030
python3 verify.py --images '{"original": "../../evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

The producer is deterministic: two runs give byte-identical `runtime/` files. `verify.py` performs these
checks and exits 0 only when all of them pass, 1 otherwise:

1. the MANIFEST hashes;
2. the four image hashes against the report;
3. a replay of all 44 cases on both images, which must give the same receipts, compute units included;
4. a rebuild of the report summary from the replay.
