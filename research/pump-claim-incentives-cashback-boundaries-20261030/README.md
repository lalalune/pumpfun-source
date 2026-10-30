# Pump Main claim handlers: token incentives and cashback (original vs rebuild)

## Question

Do the original Pump Main image and the rebuild behave the same on the three claim handlers:
`claim_token_incentives`, `claim_cashback` and `claim_cashback_v2`? The cases cover:

- the incentive token transfer and its account constraints;
- `record_claim`;
- the overflow, truncation and panic exits reached from a claim;
- the cashback rent floor;
- the v2 token-quote branch.

## Why this is not covered yet

These repository harnesses exercise the handlers:

- `scripts/pump_claim_token_incentives_differential.py`
- `pump_claim_boundary_differential.py`
- `pump_claim_panic_differential.py`
- `pump_claim_token_incentives_8099_verify.py`
- `pump_cashback_differential.py`
- `pump_cashback_accept_differential.py`

Each one loads `research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json`, either directly or through `pump_claim_token_incentives_differential.py` / `pump_trade_fixture.py`. That file is not in the git tree, so none of them can be rerun from a checkout.

`scripts/pump_volume_sync_differential.py` already varies the shared volume-accumulator day arithmetic through `sync_user_volume_accumulator`. This packet keeps roll-over cases to the ones a claim needs.

`tests/test_token_incentives_captured.py` does run `claim_token_incentives` (and `sync_user_volume_accumulator`) on the original ELF. It compares the original against the recovered host model `programs/pump/recovered/token_incentives_host.rs`, not against the rebuilt `programs/pump/src` image. No repository test runs `claim_cashback` or `claim_cashback_v2`; `test_legacy_cashback_captured.py` covers only the cashback credited by trades.

This packet adds the original-vs-rebuild comparison.

No existing `research/` folder or open PR covers these three instructions. The companion packet `pump-token-incentive-schedule-boundaries-20261030` covers the admin setter, `admin_update_token_incentives`.

## Setup

- **Images.** Original: `evidence/original/pump/deployed.so`, sha256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, 10,485,715 bytes. Rebuild: sha256 `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633`, 1,934,648 bytes. It was built by `scripts/build_partial_candidate.py` with platform-tools v1.44 / cargo-build-sbf 2.1.21, from source tree `97a2a2a383ba1bc5c5af08429de150e6124f0fc1`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.
- **Loader and simulator.** Each image is loaded with the upgradeable-loader layout (program account plus programdata) in an in-process LiteSVM (solders 0.27.1). System, SPL Token, Token-2022 and ATA are LiteSVM built-ins. There is no network.
- **State.** All accounts are synthetic, built from the upstream IDL layout (`evidence/upstream/pump.json`; discriminators and account counts are asserted).
  - `GlobalVolumeAccumulator`: 600 bytes, start 1,800,000,000, 86,400-second days, end start + 10 days unless stated otherwise.
  - `UserVolumeAccumulator`: 137 bytes, funded at rent(137) = 1,844,400 lamports unless stated otherwise.
  - Keys come from fixed seeds. The clock is fixed per case. Each case is one signed transaction.
- **Recording.** The full initial account set and instruction list of every case is in `runtime/plan.json.gz`. Receipts in `runtime/receipts-upgradeable.jsonl.gz` hold, per image:
  - the transaction bytes, the error and the complete logs;
  - the `Program data` events and the `msg!` lines logged by Pump itself;
  - the panic message text, with the file:line location stripped;
  - the inner instructions, the full after-state of every non-program account, and the compute units.
- **Behavior equality.** Equal transaction, error, events, Pump messages, panic text, inner instructions and after-state.

## Result

**All 60 cases behave identically on the original and the rebuild:** 0 behavior mismatches and 0 outcome mismatches. 32 cases succeed and 28 fail, with the same error or panic on both images.

Compute units are equal in 47 cases; 46 have byte-identical logs. The other 13 differ only in compute units and in the source path printed for the error or panic site:

| orig - rebuild CU | cases | where |
|---|---|---|
| +118 | 2 | `Truncation` (volume_accumulator.rs:103) and v1 `Overflow` (claim_token_incentives.rs:252): AnchorError site path |
| +14 | 6 | four `require!` exits in the v2 token branch (cases 53, 55–57), plus two panics: the `record_claim` unwrap (case 12) and the stable-claimed overflow (case 52) |
| +11 | 3 | panics at volume_accumulator.rs:436 (negative timestamps) and :186 (v2 native claimed overflow) |
| −90 | 2 | `index out of bounds` panics at volume_accumulator.rs:429 and :78: **the rebuild costs 90 CU more** |

In every one of these cases the original prints `programs/pump/src/...` and the rebuild prints `src/...`. The line:column values are identical, and so is the panic text.

The −90 CU on the two index-out-of-bounds panics is the only place in this packet where the rebuild is more expensive. Its cause was not determined here.

Measured behavior worth noting. Each item holds on both images, and none of it is a divergence.

- **`claim_token_incentives` (A).**
  - `user` is not a signer: the payer claims for any user, and the tokens go to that user's ATA.
  - A missing ATA is created at the payer's cost. In `ti-user-is-payer` the payer pays 2,044,280 lamports: rent(165) = 2,039,280 plus the 5,000 fee.
- **`claim_token_incentives` (B).**
  - With `seconds_in_a_day = 0` (case 16), or with the last update after `end_day` (case 14), there is no roll-over. A previously stored `total_unclaimed_tokens` is still paid out.
  - `needs_claim` stays 1 there because `current_sol_volume` is still 50.
- **`claim_token_incentives` (C).**
  - Before `start_time` (case 6), a stored `total_claimed_tokens` 9 / `has_total_claimed_tokens` 1 is reset to 0 / 0. The case logs "No tokens to claim".
- **`claim_token_incentives` (D).**
  - The roll-over product `user_volume * supply / day_volume` exits with `Truncation` (6025) when the result exceeds u64. A result of exactly u64::MAX is paid (case 9).
  - Adding the roll-over to an unclaimed u64::MAX panics with "Unexpected overflow".
  - A `total_claimed_tokens` overflow panics in `record_claim` *after* the token CPI. The whole transaction is rolled back (case 12).
- **`claim_token_incentives` (E).**
  - The day arrays have 30 slots. A synthetic 40-day range (`update_schedule` caps the range below 30 days) panics with "index out of bounds: the len is 30 but the index is 30". It panics both when now is on day 30 (case 17) and when the roll-over reads day 30 (case 18).
  - A negative clock or a negative `last_update_timestamp` panics with "SVM is 64-bit".
- **`claim_cashback` v1 vs `claim_cashback_v2` native.**
  - The same `total_cashback_claimed` overflow is error 6024 `Overflow` in v1 (case 35) and the panic "Overflowing total cashback claimed" in v2 (case 43).
  - Both pay `lamports - rent(data_len)` with saturation. Below rent the claim is a no-op that logs "No cashback to claim".
  - A 106-byte accumulator (the struct size) works; 105 bytes fails `AccountDidNotDeserialize`.
- **Native rent floor in LiteSVM.**
  - LiteSVM accepted a v1 payout of rent(0) − 1 = 890,879 lamports to a previously absent `user` account (case 37).
  - The packet makes no claim about the cluster's rent-state check.
- **`claim_cashback_v2` token branch (A).**
  - The destination only needs to be a token account of `quote_token_program` whose token-level owner is `user`. A non-ATA account is paid (case 58).
  - An owner other than `user` fails 6076 `InvalidCashbackRecipient`.
  - A missing destination fails `AccountTypeNotSupported`, at the owner check.
- **`claim_cashback_v2` token branch (B).**
  - An absent or empty accumulator quote ATA logs "No cashback to claim".
  - `quote_token_program = System` reaches `InvalidQuoteTokenProgram` only when the accumulator quote ATA is also derived with that program id (case 53). Otherwise the PDA seed constraint fails first (case 54).
- **`claim_cashback_v2` with a native quote mint.** With the native quote mint, `quote_token_program` is used only as a PDA seed and is not compared with the token program ids: Token-2022 is accepted (case 46).

"accumulator after" below is the decoded `UserVolumeAccumulator` after the transaction. For failing cases it is the unchanged initial state, because the transaction is rolled back.

"user lamports delta" is the change of `user`. For `ti-user-is-payer` that is also the fee payer.

"token-program custom N" is the SPL Token error: 1 = insufficient funds, 14 = overflow (the destination holds 1 unit), 17 = account frozen.

14 variants were trimmed to stay at 60 cases. They are listed in `DROPPED` in producer.py; each repeats a path that another case covers.

## Per-case results

| # | case | outcome (both images) | user lamports delta | dest token delta | accumulator after (unclaimed / claimed / volume / needs_claim / has_claimed) | CU original | CU rebuild | orig - rebuild |
|---|---|---|---|---|---|---|---|---|
| 1 | `ti-spl-rollover-50pct` | ok:paid | 0 | 500000 | 0 / 500000 / 0 / 0 / 1 | 57009 | 57009 | 0 |
| 2 | `ti-spl-rollover-existing-ata` | ok:paid | 0 | 500000 | 0 / 500000 / 0 / 0 / 1 | 31482 | 31482 | 0 |
| 3 | `ti-spl-pool-short-by-1` | token-program custom 1 | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 49105 | 49105 | 0 |
| 4 | `ti-t22-rollover-50pct` | ok:paid | 0 | 500000 | 0 / 500000 / 0 / 0 / 1 | 54470 | 54470 | 0 |
| 5 | `ti-same-day-no-rollover` | ok:No tokens to claim | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 43069 | 43069 | 0 |
| 6 | `ti-before-start` | ok:No tokens to claim | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 43012 | 43012 | 0 |
| 7 | `ti-before-start-with-unclaimed` | ok:paid | 0 | 1234 | 0 / 1234 / 0 / 0 / 1 | 56672 | 56672 | 0 |
| 8 | `ti-rounding-down` | ok:paid | 0 | 333333 | 0 / 333333 / 0 / 0 / 1 | 57009 | 57009 | 0 |
| 9 | `ti-result-u64max` | ok:paid | 0 | 18446744073709551615 | 0 / 18446744073709551615 / 0 / 0 / 1 | 57466 | 57466 | 0 |
| 10 | `ti-truncation` | error:Truncation | 0 | 0 | 0 / 0 / 2 / 1 / 0 | 43895 | 43777 | 118 |
| 11 | `ti-unclaimed-add-overflow` | panic:Unexpected overflow | 0 | 0 | 18446744073709551615 / 0 / 50 / 1 / 0 | 43325 | 43325 | 0 |
| 12 | `ti-claimed-add-overflow` | panic:called `Option::unwrap()` on a `None` value | 0 | 0 | 0 / 18446744073709551605 / 50 / 1 / 1 | 52073 | 52059 | 14 |
| 13 | `ti-claimed-add-max` | ok:paid | 0 | 500000 | 0 / 18446744073709551615 / 0 / 0 / 1 | 57010 | 57010 | 0 |
| 14 | `ti-last-after-end-day` | ok:paid | 0 | 77 | 0 / 77 / 50 / 1 / 1 | 56702 | 56702 | 0 |
| 15 | `ti-now-after-end` | ok:paid | 0 | 500000 | 0 / 500000 / 0 / 0 / 1 | 56981 | 56981 | 0 |
| 16 | `ti-secs-zero` | ok:paid | 0 | 55 | 0 / 55 / 50 / 1 / 1 | 56669 | 56669 | 0 |
| 17 | `ti-current-day-30` | panic:index out of bounds: the len is 30 but the index is 30 | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 43620 | 43710 | -90 |
| 18 | `ti-last-day-30` | panic:index out of bounds: the len is 30 but the index is 30 | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 43327 | 43417 | -90 |
| 19 | `ti-negative-now` | panic:SVM is 64-bit: TryFromIntError(()) | 0 | 0 | 5 / 0 / 50 / 1 / 0 | 43303 | 43292 | 11 |
| 20 | `ti-negative-last` | panic:SVM is 64-bit: TryFromIntError(()) | 0 | 0 | 5 / 0 / 50 / 1 / 0 | 43313 | 43302 | 11 |
| 21 | `ti-stored-user-differs` | ok:paid | 0 | 500000 | 0 / 500000 / 0 / 0 / 1 | 57009 | 57009 | 0 |
| 22 | `ti-uva-absent` | error:AccountNotInitialized | 0 | 0 | absent | 7251 | 7251 | 0 |
| 23 | `ti-uva-of-other-user` | error:ConstraintSeeds | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 41941 | 41941 | 0 |
| 24 | `ti-gva-mint-mismatch` | error:InvalidIncentiveMint | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 43071 | 43071 | 0 |
| 25 | `ti-token-program-mismatch` | runtime IncorrectProgramId | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 22552 | 22552 | 0 |
| 26 | `ti-user-ata-not-canonical` | error:AccountNotAssociatedTokenAccount | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 10588 | 10588 | 0 |
| 27 | `ti-pool-not-canonical` | error:ConstraintAssociated | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 40464 | 40464 | 0 |
| 28 | `ti-pool-frozen` | token-program custom 17 | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 49099 | 49099 | 0 |
| 29 | `ti-user-is-payer` | ok:paid | -2044280 | 500000 | 0 / 500000 / 0 / 0 / 1 | 61187 | 61187 | 0 |
| 30 | `ti-claim-twice` | ok:No tokens to claim | 0 | 500000 | 0 / 500000 / 0 / 0 / 1 | 74553 | 74553 | 0 |
| 31 | `ti-gva-short-543` | error:AccountDidNotDeserialize | 0 | 0 | 0 / 0 / 50 / 1 / 0 | 6694 | 6694 | 0 |
| 32 | `cb-v1-exact-rent` | ok:No cashback to claim | 0 |  | cashback claimed 0, stable claimed 0 | 7089 | 7089 | 0 |
| 33 | `cb-v1-rent-plus-1` | ok:paid | 1 |  | cashback claimed 1, stable claimed 0 | 12210 | 12210 | 0 |
| 34 | `cb-v1-below-rent` | ok:No cashback to claim | 0 |  | cashback claimed 0, stable claimed 0 | 7087 | 7087 | 0 |
| 35 | `cb-v1-claimed-overflow` | error:Overflow | 0 |  | cashback claimed 18446744073709551614, stable claimed 0 | 7880 | 7762 | 118 |
| 36 | `cb-v1-claimed-reaches-max` | ok:paid | 2 |  | cashback claimed 18446744073709551615, stable claimed 0 | 12210 | 12210 | 0 |
| 37 | `cb-v1-user-absent-below-rent` | ok:paid | 890879 |  | cashback claimed 890879, stable claimed 0 | 12210 | 12210 | 0 |
| 38 | `cb-v1-user-absent-exact-rent` | ok:paid | 890880 |  | cashback claimed 890880, stable claimed 0 | 12210 | 12210 | 0 |
| 39 | `cb-v1-length-106` | ok:paid | 1000 |  | cashback claimed 1000, stable claimed 0 | 12210 | 12210 | 0 |
| 40 | `cb-v1-length-105` | error:AccountDidNotDeserialize | 0 |  | absent | 3671 | 3671 | 0 |
| 41 | `cb-v1-twice` | ok:No cashback to claim | 9999 |  | cashback claimed 9999, stable claimed 0 | 19299 | 19299 | 0 |
| 42 | `cb-v2n-exact-rent` | ok:No cashback to claim | 0 | 0 | cashback claimed 0, stable claimed 0 | 10182 | 10182 | 0 |
| 43 | `cb-v2n-claimed-overflow` | panic:Overflowing total cashback claimed | 0 | 0 | cashback claimed 18446744073709551614, stable claimed 0 | 10439 | 10428 | 11 |
| 44 | `cb-v2n-user-absent-exact-rent` | ok:paid | 890880 | 0 | cashback claimed 890880, stable claimed 0 | 15008 | 15008 | 0 |
| 45 | `cb-v1-other-user-pda` | error:ConstraintSeeds | 0 |  | cashback claimed 0, stable claimed 0 | 5751 | 5751 | 0 |
| 46 | `cb-v2n-mint-is-wsol-t22-program` | ok:paid | 1000 | 0 | cashback claimed 1000, stable claimed 0 | 16508 | 16508 | 0 |
| 47 | `cb-v2-spl-pays-balance` | ok:paid | 0 | 5000 | cashback claimed 0, stable claimed 5000 | 24038 | 24038 | 0 |
| 48 | `cb-v2-spl-pool-zero` | ok:No cashback to claim | 0 | 0 | cashback claimed 0, stable claimed 0 | 10035 | 10035 | 0 |
| 49 | `cb-v2-t22-pays-balance` | ok:paid | 0 | 5000 | cashback claimed 0, stable claimed 5000 | 19482 | 19482 | 0 |
| 50 | `cb-v2-spl-pool-absent` | ok:No cashback to claim | 0 | 0 | cashback claimed 0, stable claimed 0 | 9737 | 9737 | 0 |
| 51 | `cb-v2-spl-pool-u64max` | token-program custom 14 | 0 | 0 | cashback claimed 0, stable claimed 0 | 18023 | 18023 | 0 |
| 52 | `cb-v2-spl-stable-claimed-overflow` | panic:Overflowing total stable cashback claimed | 0 | 0 | cashback claimed 0, stable claimed 18446744073709546616 | 19475 | 19461 | 14 |
| 53 | `cb-v2-bad-token-program` | error:InvalidQuoteTokenProgram | 0 | 0 | cashback claimed 0, stable claimed 0 | 11778 | 11764 | 14 |
| 54 | `cb-v2-bad-token-program-seeds` | error:ConstraintSeeds | 0 | 0 | cashback claimed 0, stable claimed 0 | 10237 | 10237 | 0 |
| 55 | `cb-v2-mint-owner-mismatch` | error:AccountTypeNotSupported | 0 | 0 | cashback claimed 0, stable claimed 0 | 10985 | 10971 | 14 |
| 56 | `cb-v2-recipient-other-owner` | error:InvalidCashbackRecipient | 0 | 0 | cashback claimed 0, stable claimed 0 | 11705 | 11691 | 14 |
| 57 | `cb-v2-dest-absent` | error:AccountTypeNotSupported | 0 | 0 | cashback claimed 0, stable claimed 0 | 11365 | 11351 | 14 |
| 58 | `cb-v2-dest-non-ata` | ok:paid | 0 | 5000 | cashback claimed 0, stable claimed 5000 | 24038 | 24038 | 0 |
| 59 | `cb-v2-pool-garbage` | error:InvalidAccountData | 0 | 0 | cashback claimed 0, stable claimed 0 | 9882 | 9882 | 0 |
| 60 | `cb-v2-native-then-token` | ok:paid | 3000 | 0 | cashback claimed 3000, stable claimed 5000 | 39046 | 39046 | 0 |

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
3. replays all 60 cases on both images and requires every receipt to be identical;
4. recomputes the summary.

Passing the rebuild in the `original` slot exits 1 with an image sha256 mismatch.

## Files

- `producer.py`: the case plan, execution and summary. `verify.py` imports its execution code.
- `verify.py`: the independent re-check.
- `runtime/plan.json.gz`: the initial accounts and instructions of every case.
- `runtime/receipts-upgradeable.jsonl.gz`: 120 receipts (60 cases × 2 images).
- `runtime/report.json.gz`: image hashes, the summary and per-case rows.
- `MANIFEST.json`: sha256 and size of every file except itself.
