# pump_fees `crank_donation_fee_pda`: sequences through the donation relay

## Question

`crank_donation_fee_pda` moves whatever a donation PDA holds into the
donation-relay program (`RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu`,
`donate_pubkey_config_id_with_payer_v1`) and then updates
`total_donated` / `last_crank_ts` on the PDA. No existing `research/` packet
runs this handler: `pump-fees-donation-create-sequences-20261030` stops at
creation because it did not load the relay. `scripts/fees_donation_crank_probe.py`
holds single-transaction cases, but it reads a fixture from
`research/imported-lab/`, which is no longer in the tree, so it does not run on
current main.

This packet loads the captured relay ELF
(`evidence/dependencies/donation_relay/deployed.so`) together with the captured
SPL Token and Associated Token ELFs. It runs **multi-step sequences** on the
original and the rebuilt pump_fees image. Each sequence is a fresh LiteSVM.
Inside it, SOL or tokens are funded, flags change, the clock moves and relay
state is pre-seeded between cranks. The point is the account-state transitions
across cranks, which single-shot cases cannot show:

- the native (WSOL) path: PDA lamports above rent-exempt(218) are moved into the
  PDA's WSOL ATA and `SyncNative` runs;
- the SPL path: the ATA balance is used and PDA lamports are ignored;
- the disable flag (bit 3, value 8) set and cleared between cranks;
- `total_donated` reaching `u64::MAX`, then overflowing *after* the relay CPI;
- several donation PDAs sharing one relay debouncer/epoch tracker (same
  `config_id` and quote mint);
- relay state that already exists and is wrong (config, mint, state byte, totals);
- cranker (payer) balances around the rent of the accounts that `init_if_needed`
  creates;
- whitelist changes for a mint that has a freeze authority.

## Result

**56 sequences, 77 crank transactions: the original and the rebuilt image are
identical in all 56.** For every crank the comparison covers the transaction
error, the full log list, compute units, inner instructions and the
before/after bytes of the donation PDA, the PDA ATA, the epoch tracker, the
debouncer, the debouncer ATA and the cranker. No crank differs, so no
divergence is reported.

Measured behaviour (identical on both images):

- **The donation ATA is created before the disable check.** With flag 8 set and
  no ATA, the transaction logs the ATA `Create` and then fails with
  `FeatureDeactivated` (6021) at 43,222 CU. When the ATA already exists, the
  same failure costs 21,509 CU (`flag-8-toggle`). The whole transaction reverts,
  so no ATA is left behind. Flags `0xF7` (every bit except 8) do not block.
- **Unsynced WSOL in the ATA is not donated.** `n-ata-unsynced`: the ATA holds
  4,321 lamports above its reserve with token amount 0, and the PDA has no
  excess. `SyncNative` is called only when the PDA itself has excess, so the
  crank logs `Nothing to donate` and the ATA ends at 2,043,601 lamports.
  `n-ata-plus-excess`: 100 synced tokens plus a PDA excess of 900 are donated
  together (1,000).
- **Funds that arrive while the crank is disabled are kept.** In
  `flag-8-then-unsynced`, 400 + 600 lamports arrive during two blocked cranks.
  After the flag is cleared, one crank donates 1,000 and the next logs
  `Nothing to donate`.
- **`total_donated` overflow fails after the relay has run.** With
  `total_donated = 2^64-1`, the relay CPI runs (its event is logged), and then
  pump_fees fails with `ShareCalculationOverflow` (6015) at 137,535 CU. The
  whole transaction reverts. The PDA keeps its 1,000 lamport excess and the
  relay accounts are not created. `total-max-minus-1` reaches exactly
  18446744073709551615 and then overflows on the next 1-lamport crank;
  `spl-overflow` does the same on the SPL path. With nothing to donate, a crank
  at `2^64-1` returns ok (`total-max-empty`).
- **`last_crank_ts` is overwritten unconditionally.** A stored value in the
  future, or a clock moved backwards, is replaced by the current
  `unix_timestamp`. Two cranks in the same second both succeed
  (`ts-same-second`, 10 then 30).
- **Relay accounts are keyed by `(config_id, quote_mint)`, not by donation PDA.**
  Two donation PDAs with the same config accumulate into one debouncer
  (`shared-debouncer`: PDA totals 1,000 and 3,000, debouncer 4,000). Different
  configs get separate relay accounts (`split-config`). If the debouncer is
  pushed to `2^64-1` by PDA b1, the next crank from PDA b2 fails inside the relay
  with `ArithmeticOverflow` (6008) (`shared-debouncer-overflow`).
- **Relay-side errors propagate unchanged:** wrong debouncer/epoch PDA ->
  `ConstraintSeeds` (2006); stored config differs -> `InvalidConfigId` (6002);
  stored mint differs -> `InvalidMint` (6006); state byte 2 ->
  `AccountDidNotDeserialize` (3003); state byte 0 -> the relay re-initialises the
  debouncer and its stored total of 55 is replaced (`relay-debouncer-state-0`,
  total after = 1,000).
- **Cranker balance:** with 0 lamports, the donation-ATA creation fails
  (Custom 1, 22,652 CU). With exactly 2,039,280 lamports (ATA rent) or one more,
  the donation ATA is funded but the relay's `init_if_needed` fails (Custom 1,
  88,141 CU). Once the accounts exist, a cranker with 0 lamports succeeds
  (`payer-after-init`).
- **Mint policy:** a quote mint with a freeze authority is rejected by the relay
  with `MintNotSafeForDonation` (6031) unless it is in the relay mint whitelist.
  It is accepted while listed and rejected again after the whitelist is emptied
  (`spl-whitelist-removed`). A frozen donation ATA fails in SPL Token (Custom 17).

Compute units for the first native crank, which creates the ATA, epoch tracker,
debouncer and debouncer ATA: 148,029. A later crank with all accounts in place:
102,339. A crank with nothing to donate and an existing ATA: 21,747.

## Images

| side | sha256 |
|---|---|
| original `evidence/original/pump_fees/deployed.so` | `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e` |
| rebuilt candidate (`scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `7eb3b25ef7ee45dcba86f2af79344297e98a091d`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`) | `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900` |
| dependency `evidence/dependencies/donation_relay/deployed.so` | `367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563` |
| dependency `evidence/dependencies/spl_token/deployed.so` | `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697` |
| dependency `evidence/dependencies/associated_token/deployed.so` | `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d` |

## Cases

The CU, `total_donated` and debouncer total columns are the original image's
values; the candidate's values are equal in every row (last column). For a
failed crank the "after" columns show the reverted (unchanged) state, and `-`
means the account does not exist.

| case | sequence | per crank: result / CU / total_donated after / debouncer total after | orig = cand |
|---|---|---|---|
| `n-basic` | native: fund 1,000,000 then crank | ok / 148029 / 1000000 / 1000000 | yes |
| `n-empty-first` | native: crank with no excess, then fund and crank | ok / 43460 / 0 / -<br>ok / 126316 / 500000 / 500000 | yes |
| `n-repeat` | native: two cranks, second has nothing | ok / 148029 / 1000000 / 1000000<br>ok / 21747 / 1000000 / 1000000 | yes |
| `n-accumulate` | native: three funded cranks, clock moves | ok / 148029 / 1000000 / 1000000<br>ok / 102339 / 3500000 / 3500000<br>ok / 102339 / 3500001 / 3500001 | yes |
| `n-one-lamport` | native: excess of 1 lamport | ok / 148029 / 1 / 1 | yes |
| `n-large` | native: excess of 10^11 lamports | ok / 148029 / 100000000000 / 100000000000 | yes |
| `n-below-rent` | native: PDA holds rent - 1 (saturating excess = 0) | ok / 43458 / 0 / - | yes |
| `n-ata-tokens` | native: ATA already holds 777 synced WSOL, PDA has no excess | ok / 123815 / 777 / 777 | yes |
| `n-ata-unsynced` | native: ATA has 0 amount but 4,321 unsynced lamports, no PDA excess | ok / 21747 / 0 / - | yes |
| `n-ata-plus-excess` | native: ATA holds 100, PDA excess 900 | ok / 126316 / 1000 / 1000 | yes |
| `flag-8-set` | disable flag 8 set; the donation ATA init_if_needed runs before the flag check | Custom 6021 / 43222 / 0 / - | yes |
| `flag-8-toggle` | crank ok, flag 8 set, crank blocked, flag cleared, crank ok | ok / 148029 / 1000000 / 1000000<br>Custom 6021 / 21509 / 1000000 / 1000000<br>ok / 102339 / 3000000 / 3000000 | yes |
| `flag-others` | flags 0xF7 (all but bit 3) do not block | ok / 148029 / 1000000 / 1000000 | yes |
| `flag-ff` | flags 0xFF block | Custom 6021 / 43222 / 0 / - | yes |
| `flag-8-empty` | flag 8 with nothing to donate still errors | Custom 6021 / 43222 / 0 / - | yes |
| `total-max-minus-1` | total_donated = 2^64-2, donate 1 -> max, then donate 1 -> overflow | ok / 148029 / 18446744073709551615 / 1<br>Custom 6015 / 91845 / 18446744073709551615 / 1 | yes |
| `total-max` | total_donated = 2^64-1, donate 1,000 -> overflow after relay CPI | Custom 6015 / 137535 / 18446744073709551615 / - | yes |
| `total-max-empty` | total_donated = 2^64-1, nothing to donate -> early ok | ok / 43460 / 18446744073709551615 / - | yes |
| `ts-backwards` | last_crank_ts set in the future; crank overwrites it with current clock | ok / 148029 / 10 / 10 | yes |
| `ts-negative` | clock moved before stored ts, negative stored ts | ok / 148029 / 10 / 10 | yes |
| `ts-same-second` | two cranks in the same second (no debounce in pump_fees) | ok / 148029 / 10 / 10<br>ok / 102339 / 30 / 30 | yes |
| `two-crankers` | permissionless: different signers pay relay init then reuse | ok / 148029 / 1000 / 1000<br>ok / 102339 / 3000 / 3000 | yes |
| `payer-zero` | cranker has 0 lamports: ATA init fails | Custom 1 / 22652 / 0 / - | yes |
| `payer-ata-only` | cranker can fund the donation ATA but not relay accounts | Custom 1 / 88141 / 0 / - | yes |
| `payer-ata-plus-one` | cranker has ATA rent + 1 | Custom 1 / 88141 / 0 / - | yes |
| `payer-after-init` | first crank inits everything, then a 0-lamport cranker succeeds | ok / 148029 / 1000 / 1000<br>ok / 102339 / 2000 / 2000 | yes |
| `payer-zero-empty` | cranker has 0 lamports, ATA exists, nothing to donate | ok / 21747 / 0 / - | yes |
| `shared-debouncer` | two donation PDAs (base b1,b2) same config share epoch/debouncer | ok / 148029 / 1000 / 1000<br>ok / 118052 / 3000 / 4000 | yes |
| `split-config` | same base, configs c1/c2 use separate relay accounts | ok / 148029 / 1000 / 1000<br>ok / 154029 / 3000 / 3000 | yes |
| `swap-debouncer` | pass config c2 debouncer for a c1 donation PDA | Custom 2006 / 93596 / 0 / - | yes |
| `swap-epoch` | pass config c2 epoch tracker for a c1 donation PDA | Custom 2006 / 87764 / 0 / - | yes |
| `swap-ata` | pass b2 donation ATA for b1 donation PDA | ok / 142029 / 1000 / 1000<br>Custom 2015 / 9052 / 0 / 1000 | yes |
| `relay-epoch-5` | existing epoch tracker at epoch 5 | ok / 145234 / 1000 / 1000 | yes |
| `relay-debouncer-total` | existing debouncer total 10^9 | ok / 145235 / 1000 / 1000001000 | yes |
| `relay-debouncer-overflow` | existing debouncer total 2^64-1 -> relay overflow | Custom 6008 / 126563 / 0 / 18446744073709551615 | yes |
| `relay-debouncer-wrong-config` | debouncer stores config c2 | Custom 6002 / 123654 / 0 / 0 | yes |
| `relay-epoch-wrong-config` | epoch tracker stores config c2 | Custom 6002 / 123554 / 0 / - | yes |
| `relay-debouncer-wrong-mint` | debouncer stores the SPL quote mint | Custom 6006 / 124290 / 0 / 0 | yes |
| `relay-epoch-wrong-mint` | epoch tracker stores the SPL quote mint | Custom 6006 / 124318 / 0 / - | yes |
| `relay-debouncer-state-2` | debouncer state byte 2 | Custom 3003 / 93650 / 0 / 0 | yes |
| `relay-epoch-state-2` | epoch tracker state byte 2 | Custom 3003 / 87819 / 0 / - | yes |
| `relay-debouncer-state-0` | debouncer present but Uninitialized (re-initialised by relay) | ok / 145274 / 1000 / 1000 | yes |
| `spl-unlisted` | SPL quote, no freeze authority, not whitelisted | ok / 126530 / 1000 / 1000 | yes |
| `spl-listed` | SPL quote whitelisted | ok / 126419 / 1000 / 1000 | yes |
| `spl-freeze-unlisted` | SPL quote with freeze authority, not whitelisted | Custom 6031 / 104758 / 0 / - | yes |
| `spl-freeze-listed` | SPL quote with freeze authority, whitelisted | ok / 126437 / 1000 / 1000 | yes |
| `spl-no-ata` | SPL quote, no donation ATA yet: init then nothing to donate | ok / 38421 / 0 / -<br>ok / 126530 / 5 / 5 | yes |
| `spl-lamports-ignored` | SPL quote: SOL sent to the PDA is not donated | ok / 19704 / 0 / - | yes |
| `spl-repeat` | SPL quote: donate, refill, donate | ok / 126530 / 7 / 7<br>ok / 102549 / 9223372036854775815 / 9223372036854775815 | yes |
| `spl-overflow` | SPL quote: total 2^64-8, donate 7 ok then 1 overflows | ok / 126530 / 18446744073709551615 / 7<br>Custom 6015 / 92055 / 18446744073709551615 / 7 | yes |
| `spl-ata-frozen` | SPL quote: donation ATA frozen | Custom 17 / 105810 / 0 / - | yes |
| `spl-whitelist-removed` | freeze-authority mint: listed crank ok, whitelist emptied, next crank | ok / 126437 / 10 / 10<br>Custom 6031 / 80860 / 10 / 10 | yes |
| `debouncer-ata-balance` | relay debouncer ATA already holds 5,000 WSOL | ok / 129641 / 1000 / 1000 | yes |
| `shared-debouncer-overflow` | debouncer at 2^64-1001: b1 adds 1000, then b2 adds 1 -> relay overflow | ok / 145235 / 1000 / 18446744073709551615<br>Custom 6008 / 99380 / 0 / 18446744073709551615 | yes |
| `relay-epoch-max` | epoch tracker at 2^128-1 | ok / 145234 / 1000 / 1000 | yes |
| `flag-8-then-unsynced` | funded while disabled, then enabled: whole PDA excess donated once | Custom 6021 / 43222 / 0 / -<br>Custom 6021 / 43222 / 0 / -<br>ok / 148029 / 1000 / 1000<br>ok / 21747 / 1000 / 1000 | yes |

## Fixture

All accounts are synthetic and every key comes from a fixed seed; no captured
mainnet account is used.

- `FeeProgramGlobal` at its PDA (`fee-program-global`) with only `disable_flags`
  varied.
- `DonationFeePda` (218 bytes, version 1) at
  `["donation-fee-pda", base_mint, config_id]`, funded with exactly
  rent-exempt(218). "fund N" adds N lamports to the PDA (native path) or N
  tokens to its ATA (SPL path).
- WSOL mint (82 bytes, 9 decimals) and a synthetic 6-decimal SPL quote mint,
  optionally with a freeze authority.
- Relay `MintWhitelistV1` at `["mint_whitelist_v1"]`, empty unless a case lists
  the SPL mint. Pre-seeded `EpochTrackerV1` (90 bytes) / `DebouncerV1` (82 bytes)
  are written only where a case says so; otherwise the relay creates them.
- The transaction fee payer is separate from the crank `payer` signer, so
  cranker balances can be set freely.

## Files

- `producer.py` — builds the sequences, runs each one on both images, and
  writes `runtime/receipts.jsonl.gz` (every crank: error, logs, CU, inner
  instructions, account bytes before/after) and `runtime/report.json.gz` (image
  and dependency sha256, per-case match, decoded state). The output is
  byte-for-byte deterministic: two runs gave identical files.
- `verify.py` — checks the image and dependency sha256 values against the
  report, re-runs every sequence on both images, and compares the result with
  the stored receipts and report. Exit 0 = identical.

## Reproduce

```
python3 producer.py --root <repo> \
  --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' \
  --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

`verify.py` finds the dependency ELFs under the repository that contains the
original image (`--root <repo>` overrides this). Requires `solders` 0.27.1
(`solders.litesvm`).
