# Pump Main quote-control administration lifecycle (original vs rebuild)

## Question

Do the original Pump Main image and the rebuild behave the same on the six quote-control administration instructions?

- `initialize_quote_control`
- `set_quote_control_admin`
- `set_quote_control_reserves_admin`
- `add_quote_control_mint`
- `remove_quote_control_mint`
- `set_quote_control_mint_reserves`

The cases cover:

- who may call each instruction;
- mint eligibility;
- account growth and the rent top-up up to the 256-entry cap;
- corrupt accounts;
- multi-instruction sequences.

## Why this is not covered yet

- `pump-instruction-decode-boundaries-20261030` covers only argument decoding and first-account checks of these instructions.
- `pump-global-admin-sequences-20261030` covers the separate Global quote-mint whitelist (`add_quote_mint` / `remove_quote_mint`).
- `pump-create-v2-*` packets read a QuoteControl account but never administer it.
- The repository harnesses (`scripts/pump_quote_control_differential.py`, `pump_quote_control_fresh_differential.py`) load `research/imported-lab/...`, which is not in the git tree, so they cannot be rerun from a checkout.
- `tests/test_quote_control_captured.py` runs these six instructions on the original ELF. It compares the original against the recovered host model `programs/pump/recovered/quote_control_host.rs`, not against the rebuilt `programs/pump/src` image.

This packet adds that original-vs-rebuild comparison, including the 256-entry growth and rent boundaries and multi-instruction sequences.

## Setup

- **Images.** Original: `evidence/original/pump/deployed.so`, sha256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, 10,485,715 bytes. Rebuild: sha256 `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633`, 1,934,648 bytes. It was built by `scripts/build_partial_candidate.py` with platform-tools v1.44 / cargo-build-sbf 2.1.21, from source tree `97a2a2a383ba1bc5c5af08429de150e6124f0fc1`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.
- **Loader and simulator.** Each image is loaded with the upgradeable-loader layout in an in-process LiteSVM (solders 0.27.1); System is the built-in. There is no network.
- **Synthetic state.** All built from the upstream IDL layout; discriminators and account counts are asserted.
  - Global: 1,088 bytes, `authority` = the fee payer.
  - QuoteControl: discriminator | admin | reserves_admin | 32 reserved | u32 count | 40-byte entries. Unless stated otherwise it holds 3 entries `m0=1000 m1=1001 m2=1002` in 2,108 bytes, with `admin` and `reserves_admin` set to two separate fixed-seed keypairs.
- **Keys and transactions.** Keys come from fixed seeds and the clock is fixed. Each case is one transaction signed by the payer plus the signers listed in the plan.
- **Recording and comparison.** As in the other Pump Main packets of this series. The receipts hold the transaction bytes, the error, all logs, events, Pump `msg!` lines, the inner instructions, the full after-state and the compute units. Behavior equality means all of those except compute units and logs.

## Result

**All 57 cases behave identically on the original and the rebuild:** 0 behavior mismatches and 0 outcome mismatches. 31 cases succeed and 26 fail, with the same error on both images.

Compute units and logs are byte-identical in 48 cases. The other 9 are the `require!` exits for errors 6066–6069 (cases 18–21, 32, 37–39, 47). In each of them the rebuild uses **14 CU less**, and the AnchorError site path differs: `programs/pump/src/quote_control/state.rs:<line>` in the original, `src/quote_control/state.rs:<line>` in the rebuild, with identical line numbers. The account-constraint `NotAuthorized` / `ConstraintMut` exits cost the same on both images.

Measured behavior worth noting. Each item holds on both images, and none of it is a divergence.

- **Roles.**
  - `set_quote_control_admin` accepts only `Global.authority`; the current quote-control admin is refused (case 7).
  - `set_quote_control_reserves_admin` accepts the admin or `Global.authority`, not the reserves admin itself (case 13).
  - `add` / `remove` accept the admin or `Global.authority`.
  - `set_quote_control_mint_reserves` accepts any of the three roles.
  - After `initialize_quote_control` both roles are the default key. `Global.authority` can administer immediately (cases 24 and 57), and any signer may pay for the initialization (case 5).
- **Growth.**
  - Up to 50 entries fit in the initial 2,108 bytes (case 25).
  - Entry 51 reallocs to 2,148 bytes. The admin pays exactly `rent(2148) − rent(2108)` = 278,400 lamports, giving an account balance of 15,840,960 (case 26).
  - With the account already funded, nothing is transferred (case 27).
  - One lamport short fails in the System transfer (custom 1, case 28).
  - The `authority` must be writable even when no realloc is needed (case 30, `ConstraintMut`).
  - Five adds in one transaction grow 48 → 53 entries, to 2,228 bytes (case 34).
  - The 256th entry is accepted (10,348 bytes, case 31) and the 257th fails 6066 (case 32).
  - A larger-than-needed account (4,000 bytes) is not resized (case 33).
- **Removal.**
  - Removal keeps the order of the remaining entries (case 35).
  - It never shrinks the account: 51 → 50 entries stays at 2,148 bytes (case 40).
  - Removing the default key fails 6069 before the lookup (case 38).
- **Eligibility.** The default key, the SPL native mint and the Token-2022 native mint are refused with 6069 (cases 18–20). Initial reserves of 0 and u64::MAX are both accepted (cases 22–23).
- **Duplicate entries (synthetic).** `set_quote_control_mint_reserves` updates only the first matching entry (case 49).
- **Corrupt accounts.** A count field larger than the data (51 entries declared in 2,108 bytes) fails `AccountDidNotDeserialize` (case 50), as does a 107-byte account (case 51).

"quote control after" below is the decoded account after the transaction: data length / lamports / admin / reserves admin / entries. Entries are shown as `mN=reserves`, or as a summary when the list is long. NEW is the added mint. "(unchanged)" means the transaction was rolled back or changed nothing.

"system error ix N custom C" is a System-program error in instruction N: custom 0 = account already in use; custom 1 = insufficient lamports for the transfer.

## Per-case results

| # | case | outcome (both images) | quote control after: len / lamports / admin / reserves admin / entries | CU original | CU rebuild | orig - rebuild |
|---|---|---|---|---|---|---|
| 1 | `init` | ok | 2108 / 15562560 / default / default / empty | 10212 | 10212 | 0 |
| 2 | `init-twice` | system error ix 1 custom 0 | absent / not decodable | 18302 | 18302 | 0 |
| 3 | `init-existing` | system error ix 0 custom 0 | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 8090 | 8090 | 0 |
| 4 | `init-prefunded` | ok | 2108 / 15562560 / default / default / empty | 13799 | 13799 | 0 |
| 5 | `init-by-stranger` | ok | 2108 / 15562560 / default / default / empty | 10212 | 10212 | 0 |
| 6 | `admin-by-authority` | ok | 2108 / 15562560 / stranger / reserves / m0=1000 m1=1001 m2=1002 | 18568 | 18568 | 0 |
| 7 | `admin-by-admin` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 7944 | 7944 | 0 |
| 8 | `admin-by-stranger` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 7944 | 7944 | 0 |
| 9 | `admin-to-default` | ok | 2108 / 15562560 / default / reserves / m0=1000 m1=1001 m2=1002 | 18568 | 18568 | 0 |
| 10 | `admin-qc-absent` | error:AccountNotInitialized | absent / not decodable | 5285 | 5285 | 0 |
| 11 | `resadmin-by-authority` | ok | 2108 / 15562560 / admin / stranger / m0=1000 m1=1001 m2=1002 | 18589 | 18589 | 0 |
| 12 | `resadmin-by-admin` | ok | 2108 / 15562560 / admin / stranger / m0=1000 m1=1001 m2=1002 | 18556 | 18556 | 0 |
| 13 | `resadmin-by-reserves-admin` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 5903 | 5903 | 0 |
| 14 | `resadmin-by-stranger` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 5903 | 5903 | 0 |
| 15 | `add-by-admin` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 NEW=1000 | 19161 | 19161 | 0 |
| 16 | `add-by-authority` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 NEW=1000 | 19196 | 19196 | 0 |
| 17 | `add-by-reserves-admin` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 6209 | 6209 | 0 |
| 18 | `add-default-key` | error:QuoteMintNotEligibleForWhitelist | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 14613 | 14599 | 14 |
| 19 | `add-wsol` | error:QuoteMintNotEligibleForWhitelist | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 14642 | 14628 | 14 |
| 20 | `add-wsol-2022` | error:QuoteMintNotEligibleForWhitelist | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 14667 | 14653 | 14 |
| 21 | `add-duplicate` | error:QuoteMintAlreadyWhitelisted | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 15121 | 15107 | 14 |
| 22 | `add-reserves-zero` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 NEW=0 | 19161 | 19161 | 0 |
| 23 | `add-reserves-u64max` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 NEW=18446744073709551615 | 19161 | 19161 | 0 |
| 24 | `add-into-empty-after-init` | ok | 2108 / 15562560 / default / default / NEW=1000 | 28739 | 28739 | 0 |
| 25 | `add-50th` | ok | 2108 / 15562560 / admin / reserves / 50 entries, last NEW=1000 | 28177 | 28177 | 0 |
| 26 | `add-51st-realloc` | ok | 2148 / 15840960 / admin / reserves / 51 entries, last NEW=1000 | 30917 | 30917 | 0 |
| 27 | `add-51st-prefunded` | ok | 2148 / 15840960 / admin / reserves / 51 entries, last NEW=1000 | 28920 | 28920 | 0 |
| 28 | `add-51st-admin-short` | system error ix 0 custom 1 | 2108 / 15562560 / admin / reserves / 50 entries, last m49=1049 (unchanged) | 19418 | 19418 | 0 |
| 29 | `add-51st-authority-readonly` | error:ConstraintMut | 2108 / 15562560 / admin / reserves / 50 entries, last m49=1049 (unchanged) | 8968 | 8968 | 0 |
| 30 | `add-no-realloc-readonly` | error:ConstraintMut | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 6007 | 6007 | 0 |
| 31 | `add-256th` | ok | 10348 / 72912960 / admin / reserves / 256 entries, last NEW=1000 | 71271 | 71271 | 0 |
| 32 | `add-257th` | error:QuoteMintWhitelistFull | 10348 / 72912960 / admin / reserves / 256 entries, last m255=1255 (unchanged) | 38928 | 38914 | 14 |
| 33 | `add-into-oversized` | ok | 4000 / 28730880 / admin / reserves / m0=1000 m1=1001 m2=1002 NEW=1000 | 19161 | 19161 | 0 |
| 34 | `add-five-in-one-tx` | ok | 2228 / 16397760 / admin / reserves / 53 entries, last m904=1000 | 149497 | 149497 | 0 |
| 35 | `remove-middle` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m2=1002 | 18538 | 18538 | 0 |
| 36 | `remove-last` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 | 18567 | 18567 | 0 |
| 37 | `remove-absent` | error:QuoteMintNotWhitelisted | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 14166 | 14152 | 14 |
| 38 | `remove-default` | error:QuoteMintNotEligibleForWhitelist | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 14612 | 14598 | 14 |
| 39 | `remove-empty` | error:QuoteMintNotWhitelisted | 2108 / 15562560 / admin / reserves / empty (unchanged) | 13842 | 13828 | 14 |
| 40 | `remove-from-grown` | ok | 2148 / 15840960 / admin / reserves / 50 entries, last m50=1050 | 26525 | 26525 | 0 |
| 41 | `remove-by-stranger` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 6211 | 6211 | 0 |
| 42 | `remove-by-authority` | ok | 2108 / 15562560 / admin / reserves / m1=1001 m2=1002 | 18544 | 18544 | 0 |
| 43 | `reserves-by-reserves-admin` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=5555 m2=1002 | 18456 | 18456 | 0 |
| 44 | `reserves-by-admin` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=5555 m2=1002 | 18490 | 18490 | 0 |
| 45 | `reserves-by-authority` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=5555 m2=1002 | 18523 | 18523 | 0 |
| 46 | `reserves-by-stranger` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 5942 | 5942 | 0 |
| 47 | `reserves-absent-mint` | error:QuoteMintNotWhitelisted | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 13838 | 13824 | 14 |
| 48 | `reserves-u64max-then-zero` | ok | 2108 / 15562560 / admin / reserves / m0=0 m1=1001 m2=1002 | 36856 | 36856 | 0 |
| 49 | `reserves-duplicate-entries` | ok | 2108 / 15562560 / admin / reserves / NEW=7 m0=2 NEW=3 | 18428 | 18428 | 0 |
| 50 | `qc-count-exceeds-data` | error:AccountDidNotDeserialize | 2108 / 15562560 / admin / reserves / 51 entries, last 11111111111111111111111111111111=0 (unchanged) | 8646 | 8646 | 0 |
| 51 | `qc-short-header` | error:AccountDidNotDeserialize | absent / not decodable | 5427 | 5427 | 0 |
| 52 | `qc-wrong-owner` | error:AccountOwnedByWrongProgram | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 5810 | 5810 | 0 |
| 53 | `seq-rotate-then-old-admin-adds` | error:NotAuthorized | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 (unchanged) | 24777 | 24777 | 0 |
| 54 | `seq-rotate-then-new-admin-adds` | ok | 2108 / 15562560 / stranger / reserves / m0=1000 m1=1001 m2=1002 NEW=1000 | 37729 | 37729 | 0 |
| 55 | `seq-add-remove-add` | ok | 2108 / 15562560 / admin / reserves / m0=1000 m1=1001 m2=1002 NEW=2 | 57085 | 57085 | 0 |
| 56 | `seq-admin-sets-reserves-admin-then-reserves` | ok | 2108 / 15562560 / admin / stranger / m0=42 m1=1001 m2=1002 | 36984 | 36984 | 0 |
| 57 | `seq-init-full-lifecycle` | ok | 2108 / 15562560 / admin / reserves / NEW=20 | 82865 | 82865 | 0 |

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
3. replays all 57 cases on both images and requires every receipt to be identical;
4. recomputes the summary.

Passing the rebuild in the `original` slot exits 1 with an image sha256 mismatch.

## Files

- `producer.py`: the case plan, execution and summary. `verify.py` imports its execution code.
- `verify.py`: the independent re-check.
- `runtime/plan.json.gz`: the initial accounts and instructions of every case.
- `runtime/receipts-upgradeable.jsonl.gz`: 114 receipts (57 cases × 2 images).
- `runtime/report.json.gz`: image hashes, the summary and per-case rows.
- `MANIFEST.json`: sha256 and size of every file except itself.
