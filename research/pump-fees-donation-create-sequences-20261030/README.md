# Pump Fees: `create_donation_fee_pda` route selection, curve quote bytes, disable flags and idempotency over persistent state

## Problem

`scripts/fees_donation_create_differential.py` checks `create_donation_fee_pda`
as single instructions. Its bonding-curve fixture has all reserve fields at
zero, so every case there takes the **graduated (pump_amm pool) route**.
Three things are never measured: the active-curve route, the curve
`quote_mint` bytes (offset 83..115), and what a later create sees after an
earlier transaction changed the PDA, the disable flags or the global
authority. `fees_donation_sequence.py` covers create -> deposit -> crank, but
it needs the donation-relay ELF and the `research/imported-lab` capture,
which is not in the tree.

This packet runs 47 **sequences** on a fresh LiteSVM per case and per image,
using the original `evidence/original/pump_fees/deployed.so` and the rebuilt
candidate. It compares every transaction between the two images. Only
pump_fees itself runs. The pump bonding curve, the pump_amm pool and the
sharing-config PDA are written as account images between steps. Those
writes are listed in each receipt as `state_write` steps.

Images (sha256, recorded in `runtime/report.json.gz`):

- original `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`
- candidate `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`

## Cases

There are 47 cases and 104 signed transactions per image. Keypairs come from
fixed seeds 213 to 216 (AUTH, OTHER, PAYER, THIRD). The clock is fixed at
unix 1,700,000,000 unless a case sets it. FeeProgramGlobal is 338 bytes with
authority AUTH and `disable_flags` 0. There are two SPL mints (A, B) and two
config ids (c1, c2). By default the curve is active (all reserve fields
1,000) with creator AUTH.

- `a-*` (21): active-curve route.
  - quote bytes zero / `0x46`×32 / WSOL
  - curve length 81, 82, 83, 114, 115, 116, 151
  - each of the five u64 curve fields set to 1 alone
  - `complete` = 1 with non-zero reserves
  - non-creator before creator
  - curve creator = sharing-config PDA
  - curve creator = zero key
- `b-*` (6): graduation and pool route.
  - create on the curve, then the curve is zeroed and a pool appears
  - pool index 1
  - pool quote mint differs from the curve quote bytes
  - missing pool, and pool owned by pump instead of pump_amm, each followed
    by a correct pool
  - graduated, then active again
- `c-*` (6): `disable_flags` via real `set_disable_flags` and `set_authority`.
  - bit 4 set -> create -> cleared -> create
  - bit 4 set on an existing PDA
  - flags 0xFB and 0xFF
  - authority moved to OTHER before the flag setters
  - `[set_disable_flags(4), create]` and `[create, set_disable_flags(4)]` in
    one transaction
- `d-*` (9): idempotency and multiplicity.
  - two creates in one transaction
  - re-create by non-creators
  - 2 mints × 2 config ids
  - System-transfer prefunds of 1,000,000 / 5,000,000 / 2×3,000,000 lamports
    before create
  - lamports donated after create
  - curve creator rotated after create
  - clock at 1,700,000,001, -5 and i64::MAX
- `e-*` (6): sharing-config route on a graduated pool whose `coin_creator`
  is the sharing PDA.
  - Active / Paused / revoked state transitions
  - status byte 2 and `admin_revoked` byte 2
  - admin rotated OTHER -> THIRD
  - PDA empty, then wrong owner, then wrong mint, then valid

Each transaction receipt records:

- the error
- compute units
- all program logs
- `Program data:` events, with `DonationFeePdaCreated` decoded
- the inner-instruction count
- return data
- lamport deltas of the four wallets
- lamports / owner / length / sha256 of FeeProgramGlobal and the four
  donation PDAs, plus a decode of each

## Result

**All 47 cases match.** In all 104 transaction pairs, these are identical:

- error
- events
- every log line, including the runtime `consumed` lines
- inner-instruction count
- return data
- balance deltas
- watched account state

Compute units are equal in all 104 pairs.

Outcomes per image (identical on both): 73 transactions succeed. The 31
failures are:

| Error | Transactions |
| --- | --- |
| 6016 `NotAuthorized` | 13 |
| 6021 `FeatureDeactivated` | 7 (one at instruction index 1) |
| 3003 `AccountDidNotDeserialize` | 3 |
| 6007 `InvalidSharingConfig` | 3 |
| 6008 `InvalidPool` | 2 |
| 6018 `SharingConfigNotActive` | 2 |
| 6009 `SharingConfigAdminRevoked` | 1 |

### Route selection (both images agree)

- **The curve route is taken when any of the first four u64 fields is
  non-zero.** These are the virtual/real token and quote reserves. With only
  field 0, 1, 2 or 3 set to 1, AUTH (curve creator) succeeds and OTHER (pool
  `coin_creator`) gets 6016. With only `token_total_supply` set to 1, the pool
  route is taken: AUTH gets 6016 and OTHER succeeds.
- `complete` = 1 with non-zero reserves still takes the curve route and
  succeeds.
- **The curve quote bytes are read only when the curve account is at least
  115 bytes.**
  - At 81 bytes the curve fails Anchor deserialization (3003).
  - At 82, 83 and 114 bytes the PDA records WSOL even though `0x46`×32 was
    written where it fits.
  - At 115, 116 and 151 bytes the PDA records `0x46`×32.
  - Zero quote bytes are stored as WSOL. On the pool route, the pool's
    `quote_mint` is recorded, not the curve bytes.
- On the pool route, a missing pool fails with 6008 (owner System vs
  pump_amm in the log), and so does a pump-owned pool. Pool index 1 succeeds
  at its own PDA address.
- If a graduated curve becomes active again, the curve route is used again
  (6016 for AUTH, then success).
- A curve creator equal to the zero key fails with 6016.
- A curve creator equal to the sharing PDA routes through the sharing
  config. The PDA then records the sharing **admin** (OTHER) as `creator`.

### Disable flag and authority order (both images agree)

- Only bit 4 blocks create. With flags 0xFB, create succeeds. With 0xFF it
  fails with 6021, after logging `CreateDonationFeePda is currently disabled`.
- **The flag check runs before the "already exists" check.** An existing
  PDA under flag 4 returns 6021, not the idempotent success. After the flag
  is cleared, the same call returns success with
  `donation_fee_pda already exists` and no event.
- After `set_authority` AUTH->OTHER, AUTH's `set_disable_flags` fails with
  6016, OTHER's succeeds, and the flag OTHER sets blocks AUTH's create.
- `[set_disable_flags(4), create]` in one transaction fails at instruction 1
  (6021) and rolls back the flag (flags 0 afterward).
- `[create, set_disable_flags(4)]` succeeds. The next create on the same PDA
  and the next create on a new PDA both fail with 6021.

### Idempotency and funding (both images agree)

- After a PDA exists, a create by **any** signer succeeds and changes no
  bytes, emits no event and charges only the 10,000-lamport fee. This was
  measured with OTHER, THIRD, the new curve creator after rotation, and
  AUTH after the pool `coin_creator` changed. The original `creator`,
  `quote_mint` and lamports stay unchanged. The "already exists" path costs
  22,342 CU (20,842 on the second config id).
- Two creates in one transaction produce one `DonationFeePdaCreated` event
  and one rent charge (2,408,160 lamports for 218 bytes).
- The payer's rent charge depends on prefunding:

  | Prefund before create | Payer (AUTH) pays | PDA lamports after |
  | --- | --- | --- |
  | 1,000,000 | 1,408,160 | 2,408,160 |
  | 5,000,000 | 0 | 5,000,000 |
  | 6,000,000 (2 transfers) | 0 | 6,000,000 |

  Lamports sent after creation are kept: 3,408,160 after the re-create.
- Each `(mint, config_id)` pair gets its own PDA. Four creates gave four
  PDAs, at 36,353 / 34,853 / 39,353 / 40,853 CU.
- The event `timestamp` is the clock's unix time without checks: it decoded
  as 1,700,000,001, -5 and 9,223,372,036,854,775,807.

### Sharing-config route (both images agree)

- With a revoked **and** paused config, a non-admin payer gets 6016. The
  admin gets 6009, and after un-revoking still gets 6018. So the order is
  admin -> revoked -> status.
- A status byte of 2 and an `admin_revoked` byte of 2 both fail
  deserialization (3003).
- After the admin rotates OTHER -> THIRD:
  - OTHER's create on a new config id fails with 6016.
  - THIRD's create succeeds and records THIRD.
  - The PDA created earlier keeps OTHER, and THIRD re-creating it is a
    no-op success.
- An empty sharing PDA, a wrong owner (pump_amm) and a wrong `mint` each
  fail with 6007. A valid config then succeeds.

## Scope and limits

- Only `create_donation_fee_pda`, `set_disable_flags` and `set_authority`
  run. `crank_donation_fee_pda` needs the donation-relay program, which this
  packet may not load.
- The curve, pool and sharing-config accounts are synthetic images written
  between transactions. The packet measures how pump_fees reads them, not
  how pump / pump_amm produce them.
- Programs are loaded with LiteSVM `add_program_from_file`.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "...", "candidate": "..."}'
```

`verify.py` does the following and exits 0 only if every check passes:

- checks MANIFEST.json and both image sha256 against `runtime/report.json.gz`
- replays every case on both images and compares each step with
  `runtime/receipts.jsonl.gz`
- recomputes the per-case summary

The producer is deterministic: three runs gave byte-identical runtime files.
