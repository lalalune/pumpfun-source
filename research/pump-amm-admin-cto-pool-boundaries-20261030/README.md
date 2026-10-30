# pump_amm admin_cto_pool: check order, holder-reward / cashback / quote gates, creator-fee bounds

## Question

`admin_cto_pool` (community takeover of a canonical Pump pool) replaces a pool's
`coin_creator` and optionally sets `creator_fee_bps`. Its only signer is the Pump
`pool-authority` PDA of the base mint, so in production it runs only through a Pump
CPI. No existing research packet measures it. This packet calls it directly on the
original image and on the rebuild. The cases cover each `require!` gate, the order in
which overlapping gates fire, the creator-fee bounds, the holder-reward / cashback
transitions, Borsh payload decoding, short GlobalConfig / Pool layouts and the
`prepare_pool` realloc.

Images:

| role | sha256 | provenance |
|---|---|---|
| original | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` | `evidence/original/pump_amm/deployed.so` |
| candidate | `384737bdc6c54cca4330fd5ce15f8c556a40a78afa6a93a69fe47d2b18527ab5` | `scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `755200a0d9fffe6f82a43fb65cc452d164f6e90b` |

## Setup

- A fresh `LiteSVM` (solders 0.27.1) per case with signature verification off. The
  transaction is signed only by the payer (fixed seed). The `pool_authority` meta is
  marked signer and is the real PDA `["pool-authority", base_mint]` under the Pump
  program id. No CPI other than the System transfer in `prepare_pool`.
- Synthetic accounts only. GlobalConfig is 949 bytes with `creator_fee_configurable`
  at offset 940 and `max_configurable_creator_fee_bps` at 941 (default 1 / 1000).
  Pool is 300 bytes, creator = pool-authority PDA, non-native quote mint, not
  mayhem / cashback / holder-reward, `creator_fee_bps` 50, `can_edit_creator_fee`
  1, `creator_fees` 0. Each receipt lists the parameters it changes (`params`).
- Compared per case: error, post-state (pool bytes and lamports), full log list and
  compute units.

## Result

| measure | value |
|---|---|
| cases | 46 |
| same error + same post-state | **46 / 46** |
| identical log list | 28 / 46 |
| identical log list after rewriting `thrown in programs/pump-amm/src/` -> `thrown in src/` and dropping CU lines | **46 / 46** |
| CU delta (candidate - original) histogram | 0: 28, **-18: 18** |
| original with the 18-byte path prefix removed (in-memory control, 245 sites) vs rebuild: same error/state, full logs, CU | **46 / 46** |

All 18 differences are AnchorErrors thrown in `admin_cto_pool.rs`. The error number
and line are the same on both images, and the only log difference is the 18-byte
file prefix `programs/pump-amm/`. The rebuild's crate is its own Cargo workspace, so
`file!()` is crate-relative. Each of these errors is a `require!` / `require_keys_eq!`
site and costs exactly 18 CU less on the rebuild, which is the length of the missing
prefix. Successes, Anchor account-constraint errors (2006, 3010), payload decode
errors (102) and account-decode errors cost the same CU on both images.

Control: `producer.py` also runs every case on an in-memory copy of the original in
which the 245 references to `programs/pump-amm/src/*.rs` strings are moved past the
18-byte prefix, with their length immediates lowered by 18. This control equals the
rebuild in all 46 cases: same error and state, identical full logs and identical CU
(`stripped_original_control` in the report). So the file-string length is the
whole difference on these paths. The companion packet
`pump-amm-liquidity-rounding-boundaries-20261030` uses the same control and finds
a larger, -122 CU effect at closure-built error sites in deposit/withdraw.

| case | error | site (line) | CU original | CU rebuild |
|---|---|---|---|---|
| non-canonical-creator | 6028 OnlyCanonicalPumpPoolsCanHaveCoinCreator | :64 | 11245 | 11227 |
| non-canonical-and-mayhem | 6028 | :64 | 11246 | 11228 |
| mayhem | 6075 CtoNotAllowedForMayhemPool | :68 | 11254 | 11236 |
| mayhem-and-holder-wrong | 6075 | :68 | 11253 | 11235 |
| holder-pool-to-normal | 6074 HolderRewardCreatorImmutable | :77 | 12831 | 12813 |
| holder-pool-to-normal-hr-key | 6074 | :77 | 12831 | 12813 |
| holder-pool-holder-wrong-cc | 6074 | :77 | 12855 | 12837 |
| holder-wrong-cc | 6076 InvalidHolderRewardCoinCreator | :83 | 13358 | 13340 |
| quote-wsol-fee | 6077 CreatorFeeNotConfigurableForQuote | :99 | 12906 | 12888 |
| quote-usdc-fee | 6077 | :99 | 12956 | 12938 |
| quote-wsol-fee-0-not-configurable | 6077 | :99 | 12905 | 12887 |
| cashback-fee | 6071 CreatorFeeNotAllowedForCashbackCoin | :103 | 12933 | 12915 |
| fee-not-configurable | 6068 CreatorFeeNotConfigurable | :107 | 12919 | 12901 |
| fee-max-plus-1 | 6069 CreatorFeeBpsOutOfRange | :111 | 12957 | 12939 |
| fee-0 | 6069 | :111 | 12955 | 12937 |
| fee-max-0 | 6069 | :111 | 12957 | 12939 |
| creator-fees-and-fee-oor | 6069 | :111 | 12957 | 12939 |
| creator-fees-1 | 6081 CreatorFeesNotSwept | :121 | 12844 | 12826 |

### Behavior (identical on both images)

- Check order (measured where two gates overlap): non-canonical creator (6028)
  fires before mayhem (6075). Mayhem fires before the holder-reward key check. The
  creator-fee bounds (6069) fire before the `creator_fees == 0` sweep check (6081).
  A WSOL quote with fee 0 and `creator_fee_configurable` = 0 fails on the quote
  gate (6077) first.
- Creator-fee range: `1 ..= max_configurable_creator_fee_bps`. Fee 1 and fee 1000
  are stored, while 0 and 1001 fail with 6069, and `max = 0` rejects every fee. With
  `max = 2^64-1`, fee `2^64-1` is accepted and stored as `creator_fee_bps`
  (`fee-u64-max`). With no fee argument, the configurable flag is not read
  (`no-fee-not-configurable` succeeds).
- Quote gate: WSOL and USDC quote pools reject any fee argument (6077) and accept
  the takeover without one.
- Cashback: a cashback pool rejects a fee (6071) and keeps `is_cashback_coin` = 1
  without one. With `is_holder_reward` = true and the holder-rewards PDA as the new
  creator, the fee is accepted and `is_cashback_coin` is cleared
  (`cashback-holder-fee`: fee 1, holder 1, cashback 0).
- Holder reward: a holder-reward pool can only move to the holder-rewards PDA with
  `is_holder_reward` = true. Every other combination fails with 6074 at line 77,
  including the PDA key with the flag false. A non-holder pool asking for holder
  reward with any other key fails with 6076.
- Every success sets `can_edit_creator_fee` to 0. `coin_creator` takes the argument
  as given (`cc-arbitrary-key` writes the quote mint's key).
- Layout tolerance: GlobalConfig at 940 or 941 bytes is accepted (no fee argument).
  Pools of 286 and 270 bytes are accepted and reallocated to 287 bytes (18,889 /
  18,862 CU against 18,265 for a 300-byte pool). A 287-byte pool is not reallocated.
  A GlobalConfig with a zeroed discriminator fails with `InvalidAccountData`, and
  a bool byte 2 in GlobalConfig (offset 940) or Pool (offset 270) fails with a
  Borsh `Invalid bool representation: 2`.
- Payload decoding: an empty payload, a missing Option, Option tag 2, bool 2 and a
  truncated u64 all fail with 102 InstructionDidNotDeserialize. Trailing bytes after
  a complete payload are ignored.
- Signer: the pool-authority meta unsigned gives 3010 AccountNotSigner. Any other key
  in that slot gives 2006 ConstraintSeeds.

## Files

- `producer.py` builds the accounts, runs the 46 cases on both images and writes
  `runtime/receipts.jsonl.gz` (full logs and post-state per case) and
  `runtime/report.json.gz` (summary, per-case table, image sha256s).
- `verify.py` checks the image sha256s, re-runs all cases through `producer.produce`
  and requires byte-identical receipts.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}' --out <packet>
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}'
```

Two producer runs in separate processes gave byte-identical `runtime/` files. `--root`
is accepted for the common packet interface, and no repository file is read
besides the two images.
