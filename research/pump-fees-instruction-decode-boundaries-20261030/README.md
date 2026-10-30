# Pump Fees: dispatch, Borsh decoding and first-account checks for all 31 IDL instructions

This packet measures how the Pump Fees program (`pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`) handles malformed
or minimal input. Each step runs on both images:

- **Original:** `evidence/original/pump_fees/deployed.so`, sha256 `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`.
- **Rebuild:** sha256 `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`. It was built with
  `scripts/build_partial_candidate.py` (platform-tools v1.44 / cargo-build-sbf 2.1.21) from source tree
  `476838a67af2e9cfce5d4a1f44b83436c6335836`.

The existing `scripts/fees_*_differential.py` harnesses start from well-formed instruction data with handler-specific
fixtures. Only `fees_deprecated_differential.py` sends random argument bytes, and only to the two deprecated
instructions. Before this packet, the following were unmeasured: the dispatcher, every Borsh argument-decode error
path, and the first account check that fails for each instruction.

## Cases

The packet has 32 cases: one per IDL instruction (31) plus one for the Anchor dispatcher. Together they hold 333
steps, which gives 666 receipts. Every step runs in a fresh LiteSVM. Only the pump_fees image is loaded, so no step
reaches a CPI. The payer key comes from a fixed seed (231), and every other key is either derived from sha256 or
resolved from the IDL.

- **Dispatcher (14 steps):** empty data; 1-, 4- and 7-byte prefixes of a real discriminator; all-zero and all-0xff
  8-byte discriminators; the Anchor event-CPI tag with no accounts, with an unsigned event authority, and with the
  payer as signer; the Anchor IDL-instruction tag; 7-byte prefixes of both tags.
- **Argument decoding, with no accounts:** after a successful decode Anchor stops at `AccountNotEnoughKeys` (3005),
  and a decode failure gives `InstructionDidNotDeserialize` (102). The step tells the two apart. The variants are:
  - discriminator only;
  - valid args, then one trailing byte;
  - the last byte removed;
  - `bool`, `Option` and `OptionBool` tags set to 2;
  - `Option` = None, both without and with the stale body left in place;
  - an omitted `OptionBool` tail;
  - vec/string length 0, length 1 with no body, a 3-byte length prefix, and length 0xffffffff;
  - for `user_id`: invalid UTF-8, and length 3 with only 2 body bytes.
- **Length bisection:** for every length-0xffffffff step that panics, the producer bisects on the original image to
  find the smallest declared length that panics. It then adds the two neighbouring lengths as steps, and both images
  run them.
- **Account checks, with valid args:**
  - one account short (unfunded keys);
  - all accounts unfunded;
  - the payer in every slot;
  - IDL-resolved keys (payer for signers, fixed addresses, const-seed PDAs, the program id; the rest unfunded);
  - IDL-resolved keys plus one extra account.

## Results

**Behavior matches in all 333 steps.** The compared fields are the tx bytes, error, return data, events, inner
instructions, payer lamports, and the state of every account the step touched.

**Logs and CU also match in all 333 steps** (`log_or_cu_mismatch_steps` is empty). That includes the 12 steps that
log `AnchorError thrown in <file>:<line>`:

- `lib.rs:183` and `lib.rs:188`, the deprecated instructions;
- `extend_fee_config.rs:40`.

In each of these steps both images log the same `programs/pump-fees/src/...` path and line.

No step succeeds: with no FeeConfig, FeeProgramGlobal or pump state, every step fails on both images.

### Decoding (both images)

| variant | outcome (steps) |
|---|---|
| `disc-only` | 102 x22, 3005 x7 (the 7 instructions without args), 6023 x2 (deprecated) |
| `valid-args` | 3005 x29, 6023 x2 |
| `trailing-byte` | 3005 x29, 6023 x2 |
| `last-byte-removed` | 102 x21, 3005 x1 (`get_fees`) |
| `*-bool-tag-2` | 102 x2 |
| `*-opt-tag-2` | 102 x1 |
| `*-optbool-tag-2` | 102 x1 |
| `*-none` | 3005 x1 |
| `*-none-with-stale-body` | 3005 x1 |
| `*-omitted` (OptionBool) | 3005 x1 |
| `*-len-0` | 3005 x9 |
| `*-len-1-no-body` | 102 x9 |
| `*-len-3-bytes` | 102 x9 |
| `*-len-max` (0xffffffff) | 102 x6 (vec), ProgramFailedToComplete x3 (string) |
| `*-len-bisected-neighbour` | 102 x3, ProgramFailedToComplete x3 |
| `user_id-invalid-utf8` | 102 x3 |
| `user_id-len-3-only-2-body-bytes` | 102 x3 |

- **Trailing bytes:** accepted by all 29 non-deprecated instructions.
- **Last byte removed:** accepted only by `get_fees`. Its last argument is `is_new_quote_mint: OptionBool`, and
  omitting that byte is also accepted. In every other instruction that takes arguments, it gives 102.
- **`Option` = None:** in `admin_cto_sharing_config.new_admin`, both forms decode — with the stale 32-byte body
  left after the 0 tag, and without it.
- **Vec length prefixes:** `vec<FeeTier>` and `vec<Shareholder>` with length 0xffffffff and no body give 102.
- **String length prefixes:** `user_id: String` panics with `memory allocation failed, out of memory`
  (ProgramFailedToComplete) when the declared length is large. In all three string instructions
  (`create_social_fee_pda`, `claim_social_fee_pda`, `claim_social_fee_pda_v2`), the bisected boundary is the same on
  both images:
  - declared length 32030 with no body gives 102;
  - declared length 32031 panics.

  The panic leaves no state change. It is a different error class from 102 for the same kind of malformed input.

### Dispatcher (both images)

| dispatcher step | outcome |
|---|---|
| `empty-data`, `one-byte`, `four-bytes`, `seven-bytes` | 101 InstructionFallbackNotFound (1197 CU) |
| `zero-disc`, `ff-disc` | 101 (1299 CU) |
| `zero-disc-with-account` | 101 (1594 CU) |
| `event-cpi-tag-no-accounts` | NotEnoughAccountKeys (ProgramError, not an AnchorError) |
| `event-cpi-tag-unsigned-event-authority` | 2002 ConstraintSigner on `event_authority` |
| `event-cpi-tag-payer-signer` | 2006 ConstraintSeeds on `event_authority` |
| `idl-tag-no-accounts` | 102 |
| `idl-tag-create-payload` | 3005, blaming account `to` |
| `event-cpi-tag-seven-bytes`, `idl-tag-seven-bytes` | 101 |

- **IDL instruction:** both images contain Anchor's IDL-instruction handler. The tag alone does not decode (102),
  and a well-formed `IdlCreateAccount` payload reaches account parsing (3005, `to`).
- **Short data:** data shorter than 8 bytes always returns 101, never 102.

### First failing account (both images)

The "no accounts" column is the account that 3005 names with valid args. The other columns give the error code and
the account named in the log.

| instruction | no accounts | unfunded keys | payer in every slot | IDL-resolved keys |
|---|---|---|---|---|
| `admin_cto_sharing_config` | `pool_authority` | 3010 `pool_authority` | 3007 `global` | 3012 `global` |
| `claim_social_fee_pda` | `recipient` | 3012 `social_fee_pda` | 3007 `social_fee_pda` | 3012 `social_fee_pda` |
| `claim_social_fee_pda_v2` | `recipient` | 3012 `social_fee_pda` | 3007 `social_fee_pda` | 3012 `social_fee_pda` |
| `crank_donation_fee_pda` | `event_authority` | 3008 `program` | 3008 `program` | 3012 `fee_program_global` |
| `create_donation_fee_pda` | `event_authority` | 3008 `program` | 3008 `program` | 3012 `fee_program_global` |
| `create_fee_sharing_config` | `event_authority` | 3008 `program` | 3008 `program` | 3012 `global` |
| `create_social_fee_pda` | `payer` | 3010 `payer` | 3008 `system_program` | 3012 `fee_program_global` |
| `extend_fee_config` | `fee_config` | 3010 `user` | 3008 `system_program` | 6028 (handler body, `extend_fee_config.rs:40`) |
| `get_fees` | `fee_config` | 3012 `fee_config` | 3007 `fee_config` | 3012 `fee_config` |
| `get_fees_with_quote_mint` | `fee_config` | 3012 `fee_config` | 3007 `fee_config` | 3012 `fee_config` |
| `initialize_buyback` | `payer` | 3010 `payer` | 3008 `system_program` | 3012 `mint` |
| `initialize_fee_config` | `admin` | 3010 `admin` | 3008 `system_program` | 2006 `fee_config` |
| `initialize_fee_program_global` | `authority` | 3010 `authority` | 3007 `pump_global` | 3012 `pump_global` |
| `revoke_fee_sharing_authority` | 6023 | 6023 | 6023 | - (no IDL accounts) |
| `set_authority` | `authority` | 3010 `authority` | 3007 `fee_program_global` | 3012 `fee_program_global` |
| `set_claim_rate_limit` | `authority` | 3010 `authority` | 3007 `fee_program_global` | 3012 `fee_program_global` |
| `set_disable_flags` | `authority` | 3010 `authority` | 3007 `fee_program_global` | 3012 `fee_program_global` |
| `set_exotic_flat_fees` | `fee_config` | 3012 `fee_config` | 3007 `fee_config` | 3012 `fee_config` |
| `set_social_claim_authority` | `authority` | 3010 `authority` | 3007 `fee_program_global` | 3012 `fee_program_global` |
| `sweep_buyback` | `destination` | 3010 `authority` | 3007 `buyback_vault` | 3012 `buyback_vault` |
| `transfer_fee_sharing_authority` | 6023 | 6023 | 6023 | - (no IDL accounts) |
| `update_admin` | `admin` | 3010 `admin` | 3007 `fee_config` | 3012 `fee_config` |
| `update_buyback_authority` | `authority` | 3010 `authority` | 3007 `fee_program_global` | 3012 `fee_program_global` |
| `update_buyback_claim_rate_limit` | `authority` | 3010 `authority` | 3007 `fee_program_global` | 3012 `fee_program_global` |
| `update_fee_config` | `fee_config` | 3012 `fee_config` | 3007 `fee_config` | 3012 `fee_config` |
| `update_fee_shares` | `event_authority` | 3008 `program` | 3008 `program` | 3012 `global` |
| `update_fee_shares_v2` | `event_authority` | 3008 `program` | 3008 `program` | 3012 `global` |
| `update_stable_fee_config` | `fee_config` | 3012 `fee_config` | 3007 `fee_config` | 3012 `fee_config` |
| `upsert_fee_tiers` | `fee_config` | 3012 `fee_config` | 3007 `fee_config` | 3012 `fee_config` |
| `upsert_stable_fee_tiers` | `fee_config` | 3012 `fee_config` | 3007 `fee_config` | 3012 `fee_config` |
| `withdraw` | `user` | 3010 `user` | 3007 `quote_mint` | 3012 `quote_mint` |

Over all instructions, the account-check variants come out as follows:

| variant | outcome (steps) |
|---|---|
| `one-account-short` | 3008 x5, 3010 x15, 3012 x9 |
| `unfunded-accounts` | 3008 x5, 3010 x15, 3012 x9, 6023 x2 |
| `payer-every-slot` | 3007 x20, 3008 x9, 6023 x2 |
| `idl-resolved` | 2006 x1, 3012 x27, 6028 x1 |
| `idl-resolved-extra-account` | 2006 x1, 3012 x27, 6028 x1 |

- **One account short:** gives the same error as passing every account, in all 29 instructions with accounts. The
  check that fails comes before the missing last account.
- **Extra trailing account:** does not change the outcome in any of the 29 IDL-resolved steps.
- **Event-CPI instructions:** the 5 instructions that list `event_authority`/`program` first (the
  sharing-config and donation instructions and `update_fee_shares*`) fail on `program` (3008 InvalidProgramId) for
  both unfunded keys and the payer. They fail there before any signer or owner check.
- **Deprecated instructions:** `revoke_fee_sharing_authority` and `transfer_fee_sharing_authority` return 6023 for
  every payload and account shape tested.

## Files

- `producer.py`: builds `runtime/plan.json.gz` from `evidence/upstream/pump_fees.json`, bisects the string-length
  boundary, runs every step on both images, and writes `runtime/receipts.jsonl.gz` (one line per step, holding both
  images' receipts with logs and CU) and `runtime/report.json.gz`.
- `verify.py`: needs only the packet files and the two images. It checks:
  - MANIFEST, with no unlisted files;
  - the image sha256 values against the report;
  - a replay of the whole plan on both images, requiring byte-equal receipts;
  - a recomputation of the report;
  - that the 32030/32031 boundary holds on both images.

  It exits 0 on success and 1 on any difference.

## Reproduce

From the repository root:

```
python3 research/pump-fees-instruction-decode-boundaries-20261030/producer.py --root . \
  --images '{"original": "evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' \
  --out research/pump-fees-instruction-decode-boundaries-20261030
cd research/pump-fees-instruction-decode-boundaries-20261030
python3 verify.py --images '{"original": "../../evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

Two producer runs gave byte-identical `runtime/` files. Running the plan takes about 1.5 minutes per run (solders
0.27.1 LiteSVM).
