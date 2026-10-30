# Pump Main admin_cto: validation boundaries and curve-only outcomes (original vs rebuild)

## Question

Do the original Pump Main image and the rebuild behave the same on `admin_cto`, the community takeover that replaces a bonding curve's creator?

The packet measures the handler's validation layer and its curve-only outcomes:

- mayhem, holder-reward and new-creator rules;
- creator-fee rules;
- the unswept-fee guard;
- the outgoing creator's vault payout.

## Why this is not covered yet

`scripts/pump_admin_cto_differential.py` imports `scripts/pump_validate_admin.py`. That script reads `research/imported-lab/analysis/pump_fun/config-snapshot.json`, which is not in the git tree, so the harness cannot be rerun from a checkout.

No `tests/test_*_captured.py` covers `admin_cto`, and no existing `research/` folder or open PR does either. The pump_fees packets cover the separate `admin_cto_sharing_config` of the fees program.

## Setup

- **Images.** Original: `evidence/original/pump/deployed.so`, sha256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, 10,485,715 bytes. Rebuild: sha256 `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633`, 1,934,648 bytes. It was built by `scripts/build_partial_candidate.py` with platform-tools v1.44 / cargo-build-sbf 2.1.21, from source tree `97a2a2a383ba1bc5c5af08429de150e6124f0fc1`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.
- **Loader and simulator.** Each image is loaded with the upgradeable-loader layout in an in-process LiteSVM (solders 0.27.1). The pump_amm and pump_fees program ids are filled with the same in-memory no-op SBPFv0 program (`noop_stub()` in producer.py). System, SPL Token and ATA are LiteSVM built-ins. There is no network.
- **Global.** Synthetic, 1,088 bytes:
  - `admin_set_creator_authority` at offset 418 = the fee payer;
  - `creator_fee_configurable` at 1045 = 1;
  - `max_configurable_creator_fee_bps` at 1046 = 500;
  - `is_holder_reward_enabled` at 1086 = 1.
- **BondingCurve.** Synthetic, 166 bytes, creator `CREATOR`, either native quote or a non-whitelisted SPL quote mint (`tq-*`).
- **What no case has.** No case has a canonical pump_amm pool or a pump_fees sharing config. Every success therefore ends on the logged curve-only path, and the stubs are never invoked.
- **Determinism.** Keys come from fixed seeds and the clock is fixed.
- **Recording and comparison.** As in the other Pump Main packets of this series. Behavior equality means equal tx, error, events, Pump `msg!` lines, panic text, inner instructions and full after-state.

## Result

**All 34 cases behave identically on the original and the rebuild:** 0 behavior mismatches and 0 outcome mismatches. 14 cases succeed and 20 fail, with the same error on both images.

Compute units differ in 31 of the 34 cases. They are equal only for the three account-constraint exits (cases 19, 21, 33).

- **Validation and `require!` exits (17 cases).** The rebuild uses 22–47 CU less. In cases 4–5 (`InvalidCreator` for the holder-rewards / sharing-config PDA, admin_cto.rs:312) it uses **136 CU less**. The AnchorError site path differs (`programs/pump/src/...` vs `src/...`, same line).
- **Successful curve-only takeovers (14 cases).** Only the CU count differs. The rebuild costs 1–10 CU **more** in 11 of them (−1 to −10). It costs 1 CU less in case 25 and 8 CU less in cases 26 and 28, the token-quote takeovers with a fee.

Measured behavior worth noting. Each item holds on both images, and none of it is a divergence.

- **Validation order.**
  - The mayhem check precedes everything, including holder conversion and the unswept-fee guard (cases 7–9).
  - The `creator_fee == 0` guard (6095) comes after validation (case 18).
  - A read-only system-owned `current_creator` is rejected with 6092 in the old-creator collection step (case 22, vault funded).
- **New-creator rules.**
  - `new_creator` equal to the current creator is accepted, with the curve unchanged (case 6).
  - The holder-rewards PDA and the sharing-config PDA are refused as `new_creator` (6019).
- **Holder rewards.**
  - A holder-reward coin cannot get a new creator (6083), but it can be "re-converted" (case 14), even with Global holder rewards disabled (case 16).
  - A fresh conversion with holder rewards disabled fails 6084 (case 15).
  - A conversion sets the creator to the holder-rewards PDA and `is_holder_reward = 1`.
- **Creator fee.**
  - On a native-SOL curve any fee is refused with 6091 (case 17).
  - On a non-whitelisted token quote, 1..=500 is accepted and stored in `creator_fee_bps` (cases 26, 28); 0 and 501 fail 6078.
  - A cashback coin refuses a fee (6080) unless it is converted to holder rewards in the same call (case 32: accepted, fee 100 stored).
  - `can_edit_creator_fee` stays 0 in every success.
- **Outgoing creator payout.** With the creator vault holding 1,000,000 lamports above rent(0), the old creator receives exactly 1,000,000. This holds also when the creator account did not exist before (cases 23–24).

"curve after" below is the decoded BondingCurve after the transaction: creator / is_holder_reward / creator_fee_bps / can_edit_creator_fee. NEWC is the new creator and HOLDER_PDA the `[b"holder-rewards", mint]` PDA. "(unchanged)" means rolled back or unchanged.

## Per-case results

| # | case | outcome (both images) | curve after: creator / holder_reward / creator_fee_bps / can_edit | old creator lamports delta | CU original | CU rebuild | orig - rebuild |
|---|---|---|---|---|---|---|---|
| 1 | `native-new-creator` | ok:No creator fee to collect; No canonical pump pool for this mint; curve only | NEWC / 0 / 0 / 0 | 0 | 67475 | 67480 | -5 |
| 2 | `native-no-new-creator` | error:CtoNewCreatorRequired | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59643 | 59615 | 28 |
| 3 | `native-new-default` | error:CreatorShouldNotBeZero | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 60173 | 60142 | 31 |
| 4 | `native-new-holder-pda` | error:InvalidCreator | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59699 | 59563 | 136 |
| 5 | `native-new-sharing-pda` | error:InvalidCreator | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59726 | 59590 | 136 |
| 6 | `native-new-same-creator` | ok:No creator fee to collect; No canonical pump pool for this mint; curve only | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 67475 | 67480 | -5 |
| 7 | `mayhem` | error:CtoNotAllowedForMayhemCoin | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59641 | 59618 | 23 |
| 8 | `mayhem-holder` | error:CtoNotAllowedForMayhemCoin | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59623 | 59601 | 22 |
| 9 | `mayhem-unswept` | error:CtoNotAllowedForMayhemCoin | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59641 | 59618 | 23 |
| 10 | `holder-convert` | ok:No creator fee to collect; No canonical pump pool for this mint; curve only | HOLDER_PDA / 1 / 0 / 0 | 0 | 67356 | 67360 | -4 |
| 11 | `holder-convert-with-new` | error:CtoNewCreatorNotAllowed | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59682 | 59654 | 28 |
| 12 | `holder-false-explicit` | ok:No creator fee to collect; No canonical pump pool for this mint; curve only | NEWC / 0 / 0 / 0 | 0 | 67484 | 67489 | -5 |
| 13 | `holder-curve-new-creator` | error:HolderRewardCreatorImmutable | CREATOR / 1 / 0 / 0 (unchanged) | 0 | 59668 | 59639 | 29 |
| 14 | `holder-curve-reconvert` | ok:No canonical pump pool for this mint; curve only | HOLDER_PDA / 1 / 0 / 0 | 0 | 66472 | 66473 | -1 |
| 15 | `holder-disabled` | error:HolderRewardDisabled | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59620 | 59591 | 29 |
| 16 | `holder-disabled-holder-curve` | ok:No canonical pump pool for this mint; curve only | HOLDER_PDA / 1 / 0 / 0 | 0 | 66471 | 66472 | -1 |
| 17 | `native-fee` | error:CreatorFeeNotConfigurableForQuote | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 59850 | 59805 | 45 |
| 18 | `unswept` | error:CreatorFeesNotSwept | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 60577 | 60550 | 27 |
| 19 | `not-authority` | error:NotAuthorized | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 14441 | 14441 | 0 |
| 20 | `cashback-coin-new` | ok:No creator fee to collect; No canonical pump pool for this mint; curve only | NEWC / 0 / 0 / 0 | 0 | 67475 | 67479 | -4 |
| 21 | `current-creator-mismatch` | error:InvalidCreator | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 20599 | 20599 | 0 |
| 22 | `creator-not-writable` | error:CtoCreatorAccountNotWritable | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 60618 | 60591 | 27 |
| 23 | `creator-absent-vault-funded` | ok:No canonical pump pool for this mint; curve only | NEWC / 0 / 0 / 0 | 1000000 | 74890 | 74897 | -7 |
| 24 | `creator-vault-funded` | ok:No canonical pump pool for this mint; curve only | NEWC / 0 / 0 / 0 | 1000000 | 74890 | 74897 | -7 |
| 25 | `curve-creator-default` | ok:No canonical pump pool for this mint; curve only | NEWC / 0 / 0 / 0 | 0 | 66462 | 66461 | 1 |
| 26 | `tq-fee-100` | ok:No canonical pump pool for this mint; curve only | NEWC / 0 / 100 / 0 | 0 | 95223 | 95215 | 8 |
| 27 | `tq-fee-0` | error:CreatorFeeBpsOutOfRange | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 62826 | 62781 | 45 |
| 28 | `tq-fee-max` | ok:No canonical pump pool for this mint; curve only | NEWC / 0 / 500 / 0 | 0 | 95223 | 95215 | 8 |
| 29 | `tq-fee-max-plus-1` | error:CreatorFeeBpsOutOfRange | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 62826 | 62781 | 45 |
| 30 | `tq-fee-not-configurable` | error:CreatorFeeNotConfigurable | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 62793 | 62747 | 46 |
| 31 | `tq-cashback-fee` | error:CreatorFeeNotAllowedForCashbackCoin | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 62818 | 62771 | 47 |
| 32 | `tq-holder-cashback-fee` | ok:No canonical pump pool for this mint; curve only | HOLDER_PDA / 1 / 100 / 0 | 0 | 95086 | 95092 | -6 |
| 33 | `tq-quote-mismatch` | error:MintDoesNotMatchBondingCurve | CREATOR / 0 / 0 / 0 (unchanged) | 0 | 14022 | 14022 | 0 |
| 34 | `tq-no-fee` | ok:No canonical pump pool for this mint; curve only | NEWC / 0 / 0 / 0 | 0 | 95182 | 95192 | -10 |

The per-case notes, the outcome strings and the log-line classification are in `runtime/report.json.gz`, under `loaders.upgradeable.cases`.

## Reproduce

```
python3 producer.py --root <repo checkout> \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' \
  --out <this folder>
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
```

`producer.py` is deterministic. Two runs into different folders produced byte-identical `plan.json.gz`, `receipts-upgradeable.jsonl.gz` and `report.json.gz`.

`verify.py` reads only this folder and the two images, and exits 0 or 1:

1. checks both image sha256 values against the report;
2. checks the receipt file's sha256;
3. replays all 34 cases on both images and requires every receipt to be identical;
4. recomputes the summary.

Passing the rebuild in the `original` slot exits 1 with an image sha256 mismatch.

## Files

- `producer.py`: the case plan, execution and summary. `verify.py` imports its execution code.
- `verify.py`: the independent re-check.
- `runtime/plan.json.gz`: the initial accounts and instructions of every case.
- `runtime/receipts-upgradeable.jsonl.gz`: 68 receipts (34 cases × 2 images).
- `runtime/report.json.gz`: image hashes, the summary and per-case rows.
- `MANIFEST.json`: sha256 and size of every file except itself.
