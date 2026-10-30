# Pump Fees: authority-transition, FeeConfig layout-transition and size-boundary sequences

## Problem

The `scripts/fees_*_differential.py` suites check each Pump Fees handler as a
single instruction on fresh synthetic state. Each case gets its own account
image, so they never check what a later instruction sees after an earlier one
changed authority, tier vectors or account size. They also compare events and
errors but not `Program log:` text. This packet runs **chains** of
transactions on one persistent LiteSVM per image (original
`evidence/original/pump_fees/deployed.so` and rebuilt candidate). Every step is
compared between the two images.

Images (sha256, recorded in `runtime/report.json.gz`):

- original `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`
- candidate `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`

## Cases

59 cases, 239 transactions (250 instructions; 11 transactions carry two
instructions), each run on both images. Signers come from fixed seeds (213 to 216).
Initial accounts are synthetic: FeeProgramGlobal (338 bytes, authority AUTH),
BuybackVaults index 0 and 1 (208 bytes, stored authority AUTH unless stated),
and FeeConfig (admin AUTH, normal tiers `(0:1,2,3),(100:4,5,6)`, stable
`(0:7,8,9)`, flat `11,22,33`, exotic `44,55,66`, 4097 bytes unless stated).

- `g-*` (16): FeeProgramGlobal `set_authority` / `set_disable_flags` /
  `set_claim_rate_limit` / `set_social_claim_authority` chains: transfer then
  old/new holder, round trip, three holders, self-transfer, zero key,
  same-transaction transfer + act (both orders, old/new signer), double
  transfer in one transaction, social-claim authority acting as admin, flags
  255, repeated identical setters, failing tail instruction.
- `c-*` (20): FeeConfig `update_admin` chains (old/new admin, zero key, round
  trip, PDA as admin, same-transaction transfer + upsert, double transfer).
  Independence of global authority and config admin. Tier-vector
  transitions: grow normal ahead of stable/exotic, shrink 30 to 1, upsert
  replace/append/gap/unsorted, failing updates after a valid one,
  `extend_fee_config` then fill to the tier cap. Fee queries
  (`get_fees_with_quote_mint`) are interleaved.
- `b-*` (8): `update_buyback_authority` / `update_buyback_claim_rate_limit`
  chains: vault-authority transfer then each holder, global transfer then
  vault setters, vault stored authority different from the global one, rate
  0 / -1 / i64 max / i64 min, index/vault mismatch, zero key, same
  transaction global transfer + vault setter, flags 255.
- `s-*` (7): `sweep_buyback` of a native-WSOL vault (vault PDA 1e9 lamports,
  vault ATA 1,000,000 tokens, destination ATA of THIRD, clock fixed at unix
  1,700,000,000 with optional per-step clock): sweep by the stored vault
  authority vs the global authority, before/after either transfer,
  same-transaction transfer + sweep, consecutive sweeps across the rate
  limit (+0, +59, +60, +61, +120, +121 s), rate 0 and -1.
- `v-*` (8): FeeConfig account sizes 2512, 4072, 4073, 4096, 4097, each with the
  same 10-step chain (query USDC / a mint of 32 bytes 0x4d ("mint77") / the second normal quote mint,
  `update_stable_fee_config`, `set_exotic_flat_fees`, query again). Also an
  underfunded (1 lamport) 4072 resize, an underfunded 2512 extend, and empty
  normal tiers.

Compared per step: transaction error, Anchor error code and number, return
data, `Program data:` events, `Program log:` lines, and lamports/owner/length/
sha256 of the watched accounts (global, FeeConfig, two vaults, and in `s-*`
the two token accounts) plus a decode of the FeeConfig bytes. Final
account bytes are compared too. Compute units are recorded but not compared.

## Result

**54 of 59 cases match on every compared field. 5 cases (12 steps) diverge.**
In all 12 steps the error, return data, events and account state agree. Only
the panic location text in the program log and the compute units differ.

### Divergence: panic location path in fee queries with an empty tier vector

When a fee query picks a tier vector that is empty, both images fail with
`ProgramFailedToComplete` after an index-out-of-bounds panic. The panic
location string differs:

- original: `Program log: panicked at pump-fees-math/src/lib.rs:49:23:` +
  `index out of bounds: the len is 0 but the index is 0`
- candidate: `Program log: panicked at programs/pump-fees/pump-fees-math/src/lib.rs:49:23:` +
  the same message

The candidate uses 16 more compute units in every one of the 12 steps:
4597 vs 4613 (×7), 4659 vs 4675 (×3), 4558 vs 4574, 4533 vs 4549. In the
other 227 steps the compute units are identical. The divergent steps:

- USDC query on a 2512- or 4072-byte FeeConfig (cases
  `v-size-2512-stable-then-exotic`, `v-size-4072-stable-then-exotic`,
  `v-size-4072-underfunded-exotic-resize`, `v-size-2512-underfunded-extend`).
  It panics before and after a successful `update_stable_fee_config`, and
  after `set_exotic_flat_fees` resizes the account to 4097 bytes.
- WSOL and zero-key quote queries with empty normal tiers on a 4097-byte
  FeeConfig (`v-empty-normal-tiers-queries`).

### Size boundaries (both images agree)

- 2512 and 4072 bytes behave alike, and 4073 and 4096 behave alike. On
  2512/4072, the USDC query panics even though stable tier bytes are
  present, and the mint77 query returns flat fees `11,22,33`, not the
  exotic `44,55,66` that sits in the bytes. On 4073/4096 the USDC query
  returns the stable tier `7,8,9`, and the mint77 query still returns flat
  `11,22,33`. Only at 4097 does the mint77 query return exotic `44,55,66`.
- On 2512/4072, `update_stable_fee_config(0:13,14,15)` succeeds and emits
  its event. The tier is written into the bytes, but the next USDC query
  still panics. After `set_exotic_flat_fees` resizes to 4097, the decoded
  stable count is 0, so the tier written earlier is gone. On 4073/4096 the
  same tier survives the resize (USDC query returns `13,14,15`).
- `set_exotic_flat_fees` on a 4072-byte account holding 1 lamport resizes
  it to 4097 and leaves it at 29,406,000 lamports. `extend_fee_config` on
  a funded 2512-byte account moves it to 4097 bytes and +11,031,600
  lamports. A second extend succeeds with no event and no change. Extend on
  a 1-lamport 2512 account fails with `InsufficientFundsForRent`.
- On a 2512-byte account, the first write (`update_admin` or
  `upsert_fee_tiers`) re-serializes with stable count 0 and exotic `0,0,0`.
  `upsert_stable_fee_tiers` of 40 tiers then fails with
  `BorshIoError("failed to write whole buffer")`, a serializer error rather
  than a FeeError code. After extend the same upsert succeeds (end offset
  3297).

### Authority transitions (both images agree)

- After `set_authority` AUTH→OTHER, AUTH gets `NotAuthorized` (6016) on
  every global setter, including reclaiming. OTHER succeeds. In a three-holder
  chain, only the last holder can act.
- `set_authority` to the zero key fails with `InvalidAdmin` (6001), and
  AUTH keeps control. `update_admin` to the zero key **succeeds**. After that,
  AUTH gets `InvalidAdmin` on `set_exotic_flat_fees`, `upsert_fee_tiers` and
  `update_admin`. `update_admin` to the FeeConfig PDA also succeeds, and AUTH
  then gets `InvalidAdmin`.
- Within one transaction, the second instruction sees the first: "transfer
  then new holder acts" succeeds for both the global authority and the
  config admin. "Transfer then old holder acts" fails and rolls back the
  transfer, and the old holder then acts successfully. "New holder acts
  then transfer" fails (measured for the global authority). Two transfers in one transaction (AUTH→OTHER→THIRD)
  leave THIRD in control.
- The social-claim authority set to OTHER cannot call any global setter
  (`NotAuthorized`). `disable_flags` = 255 (set, or present at start) does
  not block any global setter.
- The global authority and the FeeConfig admin are independent. Moving one
  does not grant or remove the other (`InvalidAdmin` / `NotAuthorized`).

### Buyback vault setters (both images agree)

- Both setters are authorized by the **FeeProgramGlobal authority**, not
  by the vault's stored authority. After `update_buyback_authority` AUTH→OTHER
  on vault 0, AUTH can still set the vault 0 rate limit, and OTHER gets
  `NotAuthorized` (6016) on both setters. The vault bytes after that
  transfer equal those of a vault created with authority OTHER (sha256
  `1151e01f…`). With the stored authority OTHER from the start, OTHER gets
  `NotAuthorized` and AUTH succeeds.
- After the global `set_authority` AUTH→OTHER, AUTH gets `NotAuthorized` on
  the vault setters and OTHER succeeds on vaults 0 and 1. In one
  transaction, global transfer + new holder's vault setter succeeds.
- `update_buyback_authority` to the zero key succeeds (unlike
  `set_authority`). Rate limits 0, -1, i64 max and i64 min are all
  accepted. Neither setter emits a `Program data:` event in any step.
- An index that does not match the vault PDA fails with `ConstraintSeeds`
  (2006) in both directions. `disable_flags` = 255 does not block either
  setter.

### Buyback sweep (both images agree)

- `sweep_buyback` is authorized by the vault's **stored** authority, not by
  the global authority. This is the opposite of the two vault setters
  above. With stored authority OTHER (set at the start or by
  `update_buyback_authority`), AUTH gets `NotAuthorized` and OTHER
  succeeds. After the global `set_authority` AUTH→OTHER, OTHER gets
  `NotAuthorized` and AUTH (still the stored authority) succeeds. In one
  transaction, `update_buyback_authority` AUTH→OTHER + OTHER sweep
  succeeds, and the following AUTH sweep gets `NotAuthorized`.
- A successful first sweep moves the destination ATA from 2,039,280 to
  3,039,280 lamports and the vault ATA from 3,039,280 to 2,039,280. The
  vault PDA goes from 1,000,000,000 to 2,338,560 lamports, the stored
  `total_claimed` becomes 997,661,440 and `last_claimed` becomes
  1,700,000,000.
- Rate limit 60: sweeps at +0, +59 and +60 s fail with
  `ClaimRateLimitExceeded` (6027), and +61 s succeeds (`last_claimed`
  1,700,000,061, nothing left to move, event still emitted). Then +120 and
  +121 s (59 and 60 s after the last success) fail. Rate 0 and rate -1 both
  allow a second sweep in the same second.

### FeeConfig tier transitions (both images agree)

- Growing normal tiers re-serializes stable and exotic after them (5 normal
  tiers: end offset 337, stable/exotic intact). Tier thresholds are
  inclusive: with a tier at 400, cap 399 returns `8,8,8` and cap 400
  returns `9,9,9`. After an upsert at offset 1 truncates to a tier at 50,
  cap 49 returns tier 0 and cap 50 returns `6,6,6`.
- Shrinking does not zero the old tail: 30 normal tiers → 1 leaves 121
  non-zero bytes after the new end offset 1337. Two tiers → 1 leaves 5 or 6.
  Queries read only the new layout.
- Upsert at offset = len appends, offset len+1 fails `OffsetNotContinuous`
  (6004), and an empty upsert fails `NoFeeTiers` (6002). An upsert below or
  equal to the kept prefix fails `FeeTiersNotSorted` (6005). The cap is 50:
  upsert to 51 or update with 51 tiers fails `TooManyFeeTiers` (6003), and
  replacing tier 49 at offset 49 succeeds. With 50 normal + 50 stable tiers
  the serialized end is exactly 4097.
- A failed `update_fee_config` (`InvalidFeeTotal` 6006, `FeeTiersNotSorted`)
  after a valid one leaves the valid tiers in place (query returns `6,6,6`).
  `update_fee_config` and `update_stable_fee_config` keep exotic
  `100,200,300`.

Outcome totals over 239 steps (original = candidate): ok 178,
`NotAuthorized` 21, `InvalidAdmin` 10, `ProgramFailedToComplete` (panic)
12, `ClaimRateLimitExceeded` 5, `FeeTiersNotSorted` 3, `NoFeeTiers` 2, `TooManyFeeTiers` 2,
`ConstraintSeeds` 2, `OffsetNotContinuous` 1, `InvalidFeeTotal` 1,
`BorshIoError` 1, `InsufficientFundsForRent` 1.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "...", "candidate": "..."}'
```

`producer.py` is deterministic: two runs give byte-identical
`runtime/receipts.jsonl.gz` and `runtime/report.json.gz`. It derives the
Anchor discriminators locally and checks them against
`evidence/upstream/pump_fees.json` under `--root`. `verify.py` uses only the
packet files and the two images. It checks the image sha256 against the
report, replays every case on each image, and requires each step's result
and final account bytes to equal the receipt. It then recomputes the match
flags, the compute-unit lists and the mismatched-case list. `--images` also
accepts a path to a file containing the JSON object.

## Limits

- All state is synthetic. No captured mainnet FeeConfig or FeeProgramGlobal
  account was used, so this packet makes no claim about the deployed
  account's size or contents.
- Sizes measured: 2512, 4072, 4073, 4096, 4097 only. The layout split
  between 4072/4073 and 4096/4097 is shown by behavior, not by reading the
  binary.
- The divergence is reported as measured log text and compute units only.
  The packet does not identify which build setting produces the different
  panic path, and it contains no source change.
- Only the global setters, the two buyback-vault setters, `sweep_buyback`
  (native WSOL vault only, one destination), `update_admin`,
  `extend_fee_config`, the upsert/update tier handlers and
  `get_fees_with_quote_mint` are exercised. `initialize_buyback`, non-native
  sweeps, social claim, withdraw and sharing handlers are not.
- The token programs are LiteSVM's built-in SPL Token / Associated Token
  programs, not the captured dependency binaries.
