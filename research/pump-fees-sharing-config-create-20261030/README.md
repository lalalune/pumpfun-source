# pump_fees `create_fee_sharing_config`: authorization, idempotency, graduation and pool branches

## Problem

`create_fee_sharing_config` is how a coin enters fee sharing. It creates the
1024-byte `SharingConfig` PDA (`init_if_needed`) and CPIs into pump
`extend_account` + `migrate_bonding_curve_creator`. For a graduated coin it
also CPIs into pump_amm `extend_account` + `migrate_pool_coin_creator`. No
existing research packet and no open PR measures this handler. The repo
scripts `fees_sharing_create_differential.py` / `fees_sharing_update_differential.py`
need the missing `imported-lab` tree, so they do not run.

This packet asks whether the original `pump_fees` image and the rebuilt
candidate behave the same at the handler's decision points:

* who may create (pump `Global.admin_set_creator_authority` or the coin creator)
* what happens when a sharing config already exists (any `version`, version 0, bad discriminator, short account, pre-funded system account)
* when the coin counts as "graduated" (all four curve reserves zero) and how the pool is checked
* the curve size that pump `extend_account` starts from
* account-shape errors on mint / curve / Global, and a payer that cannot fund rent

## Method

`producer.py` builds synthetic state in a fresh in-process LiteSVM (solders
0.27.1) per case and per image: fixed keypair seeds, fixed clock
(`unix_timestamp = 1700000000`), and no wall time or paths in the results. The
pump_fees image under test is the only thing that differs between the two
sides. pump and pump_amm are the original deployed images
(`evidence/original/{pump,pump_amm}/deployed.so`) on both sides and serve only
as CPI dependencies. Defaults: a 151-byte pump BondingCurve with non-zero
reserves and creator `CREATOR`; a 740-byte pump Global with
`admin_set_creator_authority = ADMIN` at bytes 418..450; an SPL mint. For a
graduated coin the AMM Pool is the `["pool", 0u16, pool-authority(mint), mint, WSOL]`
PDA, 261 bytes, with `coin_creator = POOL_CREATOR`.

Each case runs

* `c1`: `create_fee_sharing_config` (the measured step)
* `c2`: the same instruction again, only if `c1` succeeded

For every step the receipt records the transaction sha256, error, full logs,
decoded events, lamport deltas, post-state sha256 of the payer, sharing config,
curve and pool, the decoded sharing config / curve / pool, and compute units.
"Match" means that all of these except compute units are equal on both images.
Compute units are compared separately.

## Result

**55 cases, 83 steps. All 55 cases match on behavior, and compute units are
identical in every step.** `behavior_mismatch_cases = []` and
`cu_mismatch_cases = []` in `runtime/report.json.gz`.

Columns: c1 outcome (custom error code or ok); number of pump / pump_amm CPIs
at depth 2 in c1; stored version and admin after c1; curve length (and pool
length) after c1; lamport deltas in c1 for payer / sharing_config /
bonding_curve (/ pool); c1 CU (same on both images); c2.

| case | c1 | CPIs pump/amm | version, admin | curve (pool) len | deltas payer / sc / curve (/ pool) | c1 CU | c2 | orig vs rebuild |
|---|---|---|---|---|---|---|---|---|
| a-creator-pays | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159221 | ok, 23747 CU | match |
| a-global-admin-pays | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159187 | ok, 23747 CU | match |
| a-other-rejected | 6016 | 0/0 | - | 151 | -5000 / 0 / 0 | 27564 | - | match |
| a-other-rejected-admin-zero | 6016 | 0/0 | - | 151 | -5000 / 0 / 0 | 27564 | - | match |
| a-creator-is-also-admin | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159187 | ok, 23747 CU | match |
| a-admin-pays-admin-equals-other | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159187 | ok, 23747 CU | match |
| a-creator-pays-but-curve-creator-other | 6016 | 0/0 | - | 151 | -5000 / 0 / 0 | 27564 | - | match |
| e-existing-v2-noop | ok | 0/0 | 2, OTHER (kept) | 151 | -5000 / 0 / 0 | 23747 | ok, 23747 CU | match |
| e-existing-v1-noop | ok | 0/0 | 1, OTHER (kept) | 151 | -5000 / 0 / 0 | 23747 | ok, 23747 CU | match |
| e-existing-v255-noop | ok | 0/0 | 255, OTHER (kept) | 151 | -5000 / 0 / 0 | 23747 | ok, 23747 CU | match |
| e-existing-v2-noop-other-payer | ok | 0/0 | 2, OTHER (kept) | 151 | -5000 / 0 / 0 | 23747 | ok, 23747 CU | match |
| e-existing-v0-reinitialized | ok | 2/0 | 2, CREATOR (was OTHER) | 166 | -109400 / 0 / 104400 | 156360 | ok, 23747 CU | match |
| e-existing-v0-other-payer | 6016 | 0/0 | - | 151 | -5000 / 0 / 0 | 24703 | - | match |
| e-existing-bad-discriminator | 3002 | 0/0 | - | 151 | -5000 / 0 / 0 | 12508 | - | match |
| e-existing-len-109 | 3003 | 0/0 | - | 151 | -5000 / 0 / 0 | 12473 | - | match |
| e-prefunded-system-account (5000000 lamports) | ok | 2/0 | 2, CREATOR | 166 | -3127320 / 3017920 / 104400 | 162824 | ok, 23747 CU | match |
| e-prefunded-system-account-above-rent (50000000) | ok | 2/0 | 2, CREATOR | 166 | -109400 / 0 / 104400 | 160823 | ok, 23747 CU | match |
| r-graduated-no-pool | 6019 | 0/0 | - | 151 | -5000 / 0 / 0 | 27183 | - | match |
| r-only-vtr-zero | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159221 | ok, 23747 CU | match |
| r-three-zero-rsr-one | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159221 | ok, 23747 CU | match |
| r-three-zero-vtr-one | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159231 | ok, 23747 CU | match |
| r-complete-flag-not-graduation | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159221 | ok, 23747 CU | match |
| r-total-supply-zero-only | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159221 | ok, 23747 CU | match |
| p-pool-coin-creator-pays | ok | 2/2 | 2, POOL_CREATOR | 166 (301) | -8405720 / 8017920 / 104400 / 278400 | 290763 | ok, 26565 CU | match |
| p-pool-global-admin-pays | ok | 2/2 | 2, POOL_CREATOR | 166 (301) | -8405720 / 8017920 / 104400 / 278400 | 290728 | ok, 26565 CU | match |
| p-pool-curve-creator-rejected | 6016 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 35144 | - | match |
| p-pool-coin-creator-equals-curve-creator | ok | 2/2 | 2, CREATOR | 166 (301) | -8405720 / 8017920 / 104400 / 278400 | 290763 | ok, 26565 CU | match |
| p-pool-other-rejected | 6016 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 35144 | - | match |
| p-pool-wrong-base-mint | 6008 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 30314 | - | match |
| p-pool-wrong-creator | 6008 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 33400 | - | match |
| p-pool-key-not-pda | 6008 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 35049 | - | match |
| p-pool-bad-bump | 6008 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 34531 | - | match |
| p-pool-wrong-base-mint-other-payer | 6008 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 30314 | - | match |
| p-pool-without-amm-program | 6019 | 2/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 155296 | - | match |
| p-pool-wrong-owner | 3007 | 0/0 | - | 151 (261) | -5000 / 0 / 0 / 0 | 8290 | - | match |
| p-pool-on-active-curve-ignored | ok | 2/0 | 2, CREATOR | 166 (261) | -8127320 / 8017920 / 104400 / 0 | 162352 | ok, 26565 CU | match |
| p-pool-len-245 | 3003 | 0/0 | - | 151 (245) | -5000 / 0 / 0 / 0 | 8187 | - | match |
| p-pool-len-260 | 3003 | 0/0 | - | 151 (260) | -5000 / 0 / 0 / 0 | 8187 | - | match |
| p-pool-len-300 | ok | 2/2 | 2, POOL_CREATOR | 166 (301) | -8134280 / 8017920 / 104400 / 6960 | 290763 | ok, 26565 CU | match |
| s-curve-len-81 | 3003 | 0/0 | - | 81 | -5000 / 0 / 0 | 6975 | - | match |
| s-curve-len-82 | ok | 2/0 | 2, CREATOR | 166 | -8607560 / 8017920 / 584640 | 159221 | ok, 23747 CU | match |
| s-curve-len-150 | ok | 2/0 | 2, CREATOR | 166 | -8134280 / 8017920 / 111360 | 159221 | ok, 23747 CU | match |
| s-curve-len-151 | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159221 | ok, 23747 CU | match |
| s-curve-len-152 | ok | 2/0 | 2, CREATOR | 166 | -8120360 / 8017920 / 97440 | 159221 | ok, 23747 CU | match |
| s-curve-len-166 | ok | 2/0 | 2, CREATOR | 166 | -8022920 / 8017920 / 0 | 151242 | ok, 23747 CU | match |
| s-curve-len-200 | ok | 2/0 | 2, CREATOR | 200 | -8022920 / 8017920 / 0 | 151709 | ok, 23747 CU | match |
| s-curve-creator-is-sharing-pda | 6016 | 0/0 | - | 151 | -5000 / 0 / 0 | 27564 | - | match |
| x-mint-token-2022 | ok | 2/0 | 2, CREATOR | 166 | -8127320 / 8017920 / 104400 | 159273 | ok, 23773 CU | match |
| x-mint-system-owned | 3007 | 0/0 | - | 151 | -5000 / 0 / 0 | 8070 | - | match |
| x-curve-wrong-owner | 3007 | 0/0 | - | 151 | -5000 / 0 / 0 | 7280 | - | match |
| x-global-bad-discriminator | 3002 | 0/0 | - | 151 | -5000 / 0 / 0 | 5310 | - | match |
| x-global-len-450 | 3003 | 0/0 | - | 151 | -5000 / 0 / 0 | 5719 | - | match |
| x-global-len-739 | 3003 | 0/0 | - | 151 | -5000 / 0 / 0 | 5954 | - | match |
| x-global-wrong-owner | 3007 | 0/0 | - | 151 | -5000 / 0 / 0 | 5576 | - | match |
| x-payer-cannot-fund-rent (5000000 lamports) | system error 1 | 0/0 | - | 151 | -5000 / 0 / 0 | 13243 | - | match |

Error codes: 6016 NotAuthorized, 6019 AmmAccountsRequiredForGraduatedCoin,
6008 InvalidPool, 3002 AccountDiscriminatorMismatch, 3003
AccountDidNotDeserialize, 3007 AccountOwnedByWrongProgram. "system error 1" is
the System Program's custom error 1 inside the init, with the log
`Transfer: insufficient lamports 4995000, need 8017920`. A failed step's
-5000 payer delta is the transaction fee only.

### What the measurements show (both images)

1. **Authorization.** On an active curve, the payer must be
   `Global.admin_set_creator_authority` or `curve.creator`. Any other payer
   gets 6016, and so does an all-zero admin field. When the admin pays, the
   stored admin and single shareholder are still `curve.creator`
   (a-global-admin-pays). On a graduated coin the creator check uses
   `pool.coin_creator`, not the curve creator: the curve creator is rejected
   with 6016 (p-pool-curve-creator-rejected), and the stored admin/shareholder
   becomes `POOL_CREATOR`. A curve whose creator is already the sharing-config
   PDA rejects the real creator with 6016 (s-curve-creator-is-sharing-pda).
2. **Idempotency is version-based.** Any stored `version != 0` (1, 2 and 255
   were measured) returns Ok after 23747 CU. It makes no CPI, changes no
   state, and does not check the payer: `OTHER` succeeds
   (e-existing-v2-noop-other-payer). Every successful c1 is followed by a c2
   no-op of 23747 CU (26565 CU when a pool account is passed). A stored
   `version == 0` account with a valid discriminator is rewritten: admin
   OTHER -> CREATOR, version 2, and both pump CPIs run. That rewrite still
   requires an authorized payer (e-existing-v0-other-payer: 6016). A bad
   discriminator gives 3002, and a 109-byte account gives 3003.
3. **Rent.** A sharing config costs the payer 8017920 lamports, the rent
   minimum for 1024 bytes. A system account pre-funded with 5000000 lamports
   is topped up by 3017920. One pre-funded with 50000000 needs no transfer.
4. **Graduation** requires all four reserves to be zero. With any one of them
   non-zero (r-only-vtr-zero, r-three-zero-rsr-one, r-three-zero-vtr-one) the
   coin takes the curve path. The curve path also ignores `complete = 1` and
   `token_total_supply = 0`. A graduated coin with no pool gets 6019 before
   any CPI.
5. **Pool checks.** Owner (3007) and deserialization (3003 at 245 and 260
   bytes; 261 and 300 pass) fail during account loading. The handler then
   returns 6008 for a wrong `base_mint`, for `creator != pool-authority`, and
   for a failed PDA re-derivation (both a wrong key and a wrong bump). c1 CU
   rises in that order: 30314, 33400, 35049 / 34531. These checks come before
   the payer check: a wrong pool gives 6008 even when the payer is
   unauthorized (p-pool-wrong-base-mint-other-payer). If the pool is valid
   but the pump_amm program / event authority are omitted, **both pump CPIs
   run first** and then 6019 is raised, 155296 CU into the transaction. The
   whole transaction reverts: the curve stays at 151 bytes with creator
   `CREATOR`. On a successful graduated create, pump_amm grows the pool to
   301 bytes (278400 lamports from a 261-byte pool, 6960 from 300 bytes) and
   sets `pool.coin_creator` to the sharing config. A pool passed for an
   active curve is not validated (its base mint was wrong in this case), but
   it is written into the event's `pool` field.
6. **Curve size.** pump `extend_account` grows every measured curve length
   from 82 to 152 bytes to 166 and charges the rent difference to the payer: 584640 at 82, 111360 at
   150, 104400 at 151, 97440 at 152. Curves of 166 and 200 bytes are left
   unchanged. An 81-byte curve, which ends exactly at the creator field, fails
   pump_fees deserialization with 3003.
7. **Account shapes.** Each case breaks one account, and the Anchor log names
   that account (Global, mint, sharing_config, bonding_curve or pool).
   Global needs at least 740 bytes: 739 and 450 give 3003, and 740 is the
   default that passes. A Token-2022-owned mint is accepted (159273 CU, which
   is 52 CU more than with SPL).

## Reproduce

```
python3 producer.py --root <repo> \
  --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' \
  --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

`verify.py` checks MANIFEST.json, checks that the four image sha256 values
match `runtime/report.json.gz`, re-executes every case from the receipts on
both images, and compares every recorded field, compute units included. It
also rebuilds the report counts and summary. Exit code 0 means everything
matched. It finds the pump / pump_amm dependency images under `--root`, an
ancestor `evidence/original/`, or the directory next to the original image.

Image sha256 (recorded in the report):

* original pump_fees `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`
* candidate pump_fees `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`
* pump dependency `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
* pump_amm dependency `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`

## Files

* `producer.py`: case table, LiteSVM runner, writes `runtime/`
* `verify.py`: independent replay and comparison
* `runtime/receipts.jsonl.gz`: one row per case with full per-step receipts for both images
* `runtime/report.json.gz`: image hashes, counts, mismatch lists, per-step summary
* `MANIFEST.json`: sha256 and size of every other file

## Limits

All state is synthetic. The pump Global is the 740-byte fixed-field layout
with only `initialized` and `admin_set_creator_authority` set. The pool uses
index 0 and a WSOL quote. pump and pump_amm are fixed to the original images
on both sides, so this packet measures the pump_fees image only.
