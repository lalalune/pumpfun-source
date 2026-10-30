# pump_amm `sweep_protocol_fee` / `sweep_creator_fee`: recipient validation, reserve cover, empty bucket and overflow paths

## Question

`instructions/sweep_fees.rs::execute` sweeps one accrued-fee bucket of a pool to a recipient
ATA, in these steps:

1. `prepare_pool` resizes legacy pools to 287 bytes.
2. `recipient != default` (l.91).
3. The recipient is checked: for the protocol bucket by
   `validate_protocol_fee_recipient` (`swap/mod.rs:152-166`: `binary_search` over
   `protocol_fee_recipients`, or the reserved recipients for mayhem pools); for the creator
   bucket it must equal `creator_vault(pool.coin_creator)` (l.113).
4. `available_quote_reserves` (vault >= protocol_fees + creator_fees, `pool.rs:405-418`).
5. `take_accrued_fees` (zero the bucket, `virtual_quote_reserves += amount`,
   `pool.rs:476-486`).
6. Empty bucket: log `Nothing to sweep for fee bucket N` and return. Otherwise create the
   ATA if needed and transfer.

The multi-hop chain packets sweep inside longer sequences on their success paths. These
single-sweep edges were not measured on their own: recipient validation, unsorted
recipient lists, the empty-bucket return, the reserve-cover check, accounting overflow,
account constraints and legacy pool lengths. This packet measures them in the original
image and the rebuild.

## Images

| image | sha256 |
|---|---|
| original `evidence/original/pump_amm/deployed.so` | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` |
| rebuild `<candidate.so>` (`scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `755200a0d9fffe6f82a43fb65cc452d164f6e90b`, repo commit `1e04f5b34aa33c53f2b20b4200ba4ba266b4203e`) | `384737bdc6c54cca4330fd5ce15f8c556a40a78afa6a93a69fe47d2b18527ab5` |

## Setup

Each case starts from a fresh LiteSVM (solders 0.27.1). The setup has:

- a synthetic 949-byte GlobalConfig with eight ascending protocol recipients
  (`0x41..` to `0x48..`), a `reserved_fee_recipient` and seven `reserved_fee_recipients`;
- a synthetic Pool PDA (index 0) whose `protocol_fees`, `creator_fees`,
  `virtual_quote_reserves`, `is_mayhem_mode` and `coin_creator` are written directly;
- a plain SPL Token quote mint and pool quote vault;
- LiteSVM's built-in SPL Token and Associated Token programs.

Unless a case says otherwise, the defaults are: protocol fees 1,000, creator fees 500,
vault 1,000,000, and an 8-byte instruction (no args).

For each case the producer records:

- the error, CU and full logs;
- the full Pool bytes and lamports;
- the vault and recipient-ATA balances;
- payer lamports.

## Results (43 cases)

| measure | value |
|---|---|
| cases / successful sweeps (incl. empty-bucket returns) | 43 / 22 |
| same error **and** same post-state | **43 / 43** |
| logs identical (exact) | 26 / 43 |
| logs identical after normalizing `programs/pump-amm/src/` -> `src/` | 43 / 43 |
| CU delta (rebuild - original) histogram | 0: 26, -18: 17 |
| control: original with the 18-byte path prefix stripped (245 sites) - CU / logs / error+state equal to rebuild | 43 / 43, 43 / 43, 43 / 43 |

Every success, every Anchor-generated constraint error (InvalidQuoteMint, InvalidPoolQuoteTokenAccount,
the `recipient_token_account` seeds check) and the Borsh decode error has the same CU in
both images. All 17 CU differences are −18, on AnchorError sites that log a file name:

| site (rebuild) | error | cases | original CU -> rebuild CU |
|---|---|---|---|
| `sweep_fees.rs:91` (`require_keys_neq!`) | InvalidProtocolFeeRecipient | p-recipient-default, p-recipient-default-listed | 12,294 -> 12,276 |
| `sweep_fees.rs:91` | InvalidProtocolFeeRecipient | c-recipient-default | 12,297 -> 12,279 |
| `swap/mod.rs:164` | InvalidProtocolFeeRecipient | p-recipient-stranger, p-recipient-reserved-nonmayhem, p-unsorted-config-miss | 13,648 -> 13,630 |
| `swap/mod.rs:164` | InvalidProtocolFeeRecipient | p-recipient-creator-vault 13,695; p-unsorted-config-miss-0 12,195; p-mayhem-normal-recipient 12,238 | each -18 |
| `sweep_fees.rs:113` (`require_keys_eq!`) | ConstraintSeeds | c-protocol-recipient, c-coin-creator-itself 14,100; c-old-vault-after-change 15,600 | each -18 |
| `state/pool.rs:417` | Overflow (vault < fees) | p-cover-minus-1, p-empty-cover-fails 12,061; c-cover-minus-1 14,944 | each -18 |
| `state/pool.rs:408` | Overflow (fee sum) | p-fee-sum-overflow 12,059 | -18 |
| `state/pool.rs:484` | Overflow (vqr + amount) | p-vqr-add-overflow 12,097 | -18 |

**Cause.** The original logs `AnchorError thrown in programs/pump-amm/src/...`, while the
rebuild logs `... thrown in src/...`. `programs/pump-amm/Cargo.toml` has its own
`[workspace]`, so `file!()` is crate-relative in the `build_partial_candidate` build. A
control image is the original with all 245 path-string references moved past the
18-byte prefix (nothing else changed). It reproduces the rebuild's CU, logs, error and
state in 43/43 cases. No instruction-level difference appears in the sweep handler or
the pool accounting helpers it calls.

### Behaviour pinned (identical in both images)

- **Protocol recipient lookup is a binary search.**
  - Recipients 0, 3 and 7 of the ascending list succeed (52,321 / 52,276 / 56,775 CU).
  - With an unsorted list (`[r7, r1..r6, r0]`), `r1` is still found (61,277 CU). But `r7`,
    stored at slot 0, and `r0`, stored at slot 7, are rejected with 6013
    InvalidProtocolFeeRecipient, although both are in the list.
  - The default pubkey is rejected at l.91 before the lookup, even when the list holds it.
  - The reserved recipient and the creator vault are rejected on non-mayhem pools.
- **Mayhem pools** accept only `reserved_fee_recipient` (56,688 CU) or an entry of
  `reserved_fee_recipients`: index 0 at 52,215 CU, index 6 at 61,377 CU. A normal protocol
  recipient is rejected. An `is_mayhem_mode` byte of 2 fails pool deserialization with
  `BorshIoError("Invalid bool representation: 2")` at 9,486 CU.
- **Creator bucket.**
  - Only `creator_vault(pool.coin_creator)` is accepted: 58,212 CU, and 58,213 CU on a
    mayhem pool.
  - The coin creator itself and a protocol recipient give ConstraintSeeds at l.113.
  - After `coin_creator` changes, the old creator's vault is rejected (ConstraintSeeds).
- **Empty bucket.** `protocol_fees = 0` logs `Nothing to sweep for fee bucket 0` and
  succeeds at 12,249 CU with no transfer and no ATA created. The creator bucket logs
  `... bucket 1` at 15,131 CU.
- **Reserve cover is checked before the empty-bucket return.** With `protocol_fees = 0`,
  `creator_fees = 10` and vault 9, a protocol sweep fails with Overflow (`pool.rs:417`)
  instead of returning "Nothing to sweep".
  - Vault = fees exactly (1,500) succeeds; 1,499 fails.
  - `protocol_fees = 2^64-1` with `creator_fees = 1` fails on the fee sum (`pool.rs:408`).
  - `protocol_fees = 2^64-1` alone, with a full vault, sweeps all 18,446,744,073,709,551,615.
- **Accounting.**
  - A sweep zeroes the bucket and adds the amount to `virtual_quote_reserves`: 0 -> 1,000,
    and -1,500 -> -500.
  - The i128 addition overflows exactly at `2^127 - 1000 + 1000`: a start of 2^127-1001
    succeeds and ends at i128::MAX, while 2^127-1000 fails at `pool.rs:484`.
- **Existing recipient ATA.** With the ATA already holding 7, the sweep skips creation and
  costs 26,749 CU instead of 52,321; the ATA ends at 1,007.
- **Account constraints.** A wrong `quote_mint` gives InvalidQuoteMint (8,851 CU) and a
  wrong pool vault gives InvalidPoolQuoteTokenAccount (8,923 CU). A non-ATA
  `recipient_token_account` gives ConstraintSeeds (10,595 CU, no file path, CU equal).
- **Legacy pool lengths.**
  - A 300-byte pool sweeps normally and stays 300 bytes.
  - 286-, 279- and 243-byte pools deserialize with both buckets read as 0. The payer
    reallocates them to 287 bytes, and they return "Nothing to sweep" (12,873 / 12,873 /
    12,716 CU).
  - In the 286- and 279-byte fixtures the bytes at offsets 271..279 still held
    `protocol_fees = 1,000`. The legacy decode ignores them, and the pool is written back
    with offsets 271..287 all zero.

Per-case numbers: `runtime/report.json.gz` (`cases`). Full receipts with logs and post-state:
`runtime/receipts.jsonl.gz`.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}'
```

`verify.py` checks both image sha256s against `runtime/report.json.gz`. It then re-runs
the 43 cases and the stripped-prefix control, and requires the receipts and the
recomputed report to be byte-identical. It exits 0 on PASS and 1 otherwise. Two
producer runs gave byte-identical runtime files.

## Files

- `producer.py` — case list, LiteSVM runner, stripped-prefix control, report.
- `verify.py` — independent re-run and byte comparison.
- `runtime/receipts.jsonl.gz` — one receipt per case (both images, plus the control CU).
- `runtime/report.json.gz` — summary and per-case table.
- `MANIFEST.json` — sha256 and size of every other file.
