# Pump Fees: buyback-vault initialization → sweep chains and referral withdraw sequences

Program: `pump_fees` (`pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`).
Images: original `evidence/original/pump_fees/deployed.so`
(sha256 `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`) and the
rebuilt candidate (sha256 `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`).

## Problem

The existing harnesses run these handlers one instruction at a time on state
written directly into accounts:

- `scripts/fees_buyback_differential.py` runs `sweep_buyback` and the vault setters.
- `scripts/fees_withdraw_differential.py` runs single `withdraw` calls.

Open research PR #1907 (`pump-fees-authority-transition-sequences-20261029`)
sweeps only a pre-written native vault. Its README lists `initialize_buyback`,
non-native sweeps and `withdraw` as not exercised.

This packet measures those paths as **chains on persistent state**. A vault is
created by `initialize_buyback`, funded by real SPL Token / Token-2022
`TransferChecked` and System transfers, re-authorized, and swept. The referral
vault is funded, withdrawn, refunded and withdrawn again, in native mode and in
token mode (legacy SPL, WSOL, Token-2022). Each case runs on one LiteSVM per
image, so each step sees the state left by the earlier steps.

## Result

**No divergence.** All 40 cases (173 transactions) match between the original
and the rebuild. The compared fields are:

- error and Anchor error code/number
- return data
- emitted events (`Program data:`)
- every `Program log:` line, including the `AnchorError thrown in <file>:<line>` text
- lamports, owner, length, sha256, token amount/owner and decoded `BuybackVault`
  fields of every watched account after each step
- final bytes of every watched account

Compute units are recorded but not compared. They are also equal in all 173
steps.

| family | cases | steps | what is measured |
|---|---:|---:|---|
| `i-*` | 9 | 19 | `initialize_buyback`: index bounds, re-init, prefunded vault address, pre-existing vault ATA, Token-2022 mint, mint/token-program mismatch, third-party payer |
| `s-*` | 14 | 83 | init → `update_buyback_authority` → `sweep_buyback` on legacy SPL, WSOL and Token-2022; vault-lamport sweeps; rate limit after init; missing ATAs; uninitialized indices; same-transaction chains; global authority move |
| `w-*` | 14 | 56 | `withdraw` native ladder at the rent floor, same-transaction fund/withdraw, per-user isolation, token ladders (legacy, WSOL, Token-2022), missing Option accounts, owner/mint constraints, clock values |
| `x-*` | 3 | 15 | Token-2022 mint with a transfer fee (100 bps, maximum 5,000): init → deposit → sweep, and withdraw ladders |

Outcome counts over the 173 original-image steps (the candidate has the same
counts): ok 116, `NothingToWithdraw` (6036) 17, `NotAuthorized` (6016) 14,
`AccountNotInitialized` (3012) 8, `InvalidBuybackIndex` (6026) 4,
`ClaimRateLimitExceeded` (6027) 2, `ConstraintTokenOwner` (2015) 2,
`ConstraintTokenMint` (2014) 2, custom error 0 (account in use) 2,
`IncorrectProgramId` 2, `IncompleteTokenAccounts` (6035) 1,
`ConstraintAccountIsNone` (2020) 1, `AccountNotSystemOwned` (3011) 1,
`InvalidArgument` 1.

## Measured behavior (identical on both images)

### `initialize_buyback`

- It creates a 208-byte `BuybackVault` with 2,338,560 lamports. The stored
  authority is the **zero key**, and every counter and `claim_rate_limit` is 0.
  A legacy SPL vault ATA is 165 bytes with 2,039,280 lamports. A Token-2022
  vault ATA is 170 bytes with 2,074,080 lamports. Measured costs: 44,014 CU
  for legacy, 47,483 CU for WSOL and 47,425 CU for Token-2022.
- Index bound: 7 succeeds. 8 and 255 fail with `InvalidBuybackIndex` (6026)
  (log `Left: 8`, `Right: 8`). The check runs **after** Anchor has created the
  vault and its ATA in the same instruction. The ATA program logs (`Create`,
  `InitializeAccount3`) appear before the error, and the failed call costs
  45,764 CU for index 8 and 50,312 CU for index 255. The transaction rolls
  back, and no vault 8 or 255 account remains.
- A second init of the same index fails with custom error 0 (account already
  in use) at 7,015 CU. This happens with the same mint or a different one
  (WSOL after a legacy mint).
- A vault address that already holds 5,000,000 lamports is initialized and
  keeps all 5,000,000 lamports. An address that holds 1 lamport is topped up
  to 2,338,560.
- A vault ATA that already exists with 777 tokens is accepted by
  `init_if_needed` (18,487 CU) and keeps its 777 tokens.
- A legacy mint passed with Token-2022 as `token_program`, or a Token-2022
  mint passed with SPL Token, fails with `IncorrectProgramId` inside the ATA
  program. A correct init afterwards succeeds.
- When `payer` = OTHER, OTHER pays rent and becomes neither the authority nor
  a valid sweeper (`NotAuthorized`).
- In one transaction, init 3 (Token-2022) followed by init 8 fails at
  instruction 1 with 6026, and vault 3 is rolled back. Init 1 + init 2 in one
  transaction succeeds (100,497 CU).

### `sweep_buyback` after `initialize_buyback`

- Every sweep against a fresh vault fails with `NotAuthorized` (6016),
  including a sweep by the global authority. This holds for legacy (8,711 CU),
  WSOL (8,709 CU) and Token-2022 (8,821 CU). After `update_buyback_authority`
  sets the authority to OTHER, OTHER's sweep moves all 1,000,000 vault tokens
  to the destination ATA, while AUTH still gets 6016.
- Because `claim_rate_limit` is 0 after init, a second sweep in the same
  second succeeds. It moves 0 tokens and still emits one event. After 7 more
  tokens arrive, the next sweep moves 7.
- Counters: legacy SPL and Token-2022 sweeps add to `total_claimed_token2`,
  and WSOL sweeps add to `total_claimed_token1`. `last_claimed` becomes the
  clock (1,700,000,000).
- Vault-PDA lamports above the 208-byte rent minimum are swept to the
  `destination` wallet. With 3,000,000 lamports sent to the vault, the sweep
  pays 3,000,000 lamports. A later 1-lamport deposit pays 1, and
  `total_claimed` becomes 3,000,001. On a WSOL vault with 2,000,000 extra PDA
  lamports and 5,000,000 WSOL, one sweep pays 2,000,000 lamports to the
  wallet (`total_claimed`) and 5,000,000 WSOL to the destination WSOL ATA
  (`total_claimed_token1`).
- If `update_buyback_claim_rate_limit` sets the rate to 60 after init, the
  first sweep succeeds. Sweeps at +0 s and +60 s fail with 6027, and +61 s
  succeeds.
- A destination without an ATA fails with `AccountNotInitialized` (3012) on
  `destination_ata`. A mint whose vault ATA was never created (WSOL or
  Token-2022 on a legacy-mint vault) fails with 3012 on `buyback_vault_ata`.
  Sweeps of uninitialized indices 1 and 8, and both vault setters on
  index 8, fail with 3012 on `buyback_vault`, before the index check.
- Setting the vault authority back to the zero key blocks OTHER again (6016),
  and setting it to THIRD lets THIRD sweep.
- After the global authority moves AUTH → OTHER, AUTH can no longer set the
  vault authority (6016 on `fee_program_global`). OTHER can set it and sweep.
- In one transaction, init + set authority + deposit + sweep succeeds
  (99,354 CU). Init + zero-authority sweep fails at instruction 1, and the
  init is rolled back, so a later init succeeds.
- Vaults 0 and 1 are independent. The authority set on vault 1 does not
  authorize a sweep of vault 0.

### `withdraw` (referral vault)

- Native mode pays `lamports - minimum_balance(0)`, where
  minimum_balance(0) = 890,880. A missing vault, 5 lamports and exactly 890,880
  lamports all give `NothingToWithdraw` (6036). At 890,881 the withdraw pays 1
  lamport and leaves 890,880. A second withdraw then gives 6036.
- In one transaction, fund + withdraw pays the funded amount. Withdraw + fund
  and withdraw + withdraw fail as a whole with 6036 when the vault is at the
  floor.
- Token mode moves the whole token balance (12,345, then 7 after a deposit)
  and does not touch vault-PDA lamports. With tokens at 0 and 1,000,000
  lamports in the PDA, token mode gives 6036. A following native withdraw pays
  109,120 lamports. This was measured the same way for legacy SPL (30,795 CU),
  WSOL (30,884 CU) and Token-2022 (26,309 CU).
- A native and a Token-2022 withdraw in one transaction both succeed and emit
  2 events.
- Option accounts:
  - `quote_mint` given without `vault_ata` gives `IncompleteTokenAccounts`
    (6035) from the handler.
  - Without `token_program`, Anchor's `ConstraintAccountIsNone` (2020) fires
    first.
  - A `user_ata` owned by another wallet gives `ConstraintTokenOwner` (2015).
  - A `quote_mint` that differs from the token accounts' mint gives
    `ConstraintTokenMint` (2014).
- OTHER cannot withdraw from USER's vault ATA (`ConstraintTokenOwner`, since
  the ATA's authority is USER's referral PDA, not OTHER's).
- A referral vault owned by pump_fees gives `AccountNotSystemOwned` (3011). A
  system-owned vault with 8 data bytes passes Anchor validation and then fails
  inside the System transfer CPI with `InvalidArgument`.
- `WithdrawEvent.timestamp` takes the clock unchanged at 0, -1 and 2^62
  (decoded 0, -1, 4,611,686,018,427,387,904). The event bytes are equal across
  images.

### Token-2022 transfer-fee mint (`x-*`)

The mint carries a `TransferFeeConfig` of 100 bps with a maximum fee of 5,000
in both fee slots. Both programs pass the vault's **gross** balance to
`transfer_checked`. The token program withholds the fee at the receiving
account, so the receiver gets the net amount. The event and vault counters
record the gross amount.

- `initialize_buyback` creates a 182-byte vault ATA (45,540 CU). A deposit of
  1,000,000 arrives as 995,000, with 5,000 withheld at the vault ATA.
- The sweep after the authority change moves 995,000. The destination
  receives 990,000, with 5,000 withheld there. `SweepBuybackEvent.token_amount`
  is 995,000 and `total_claimed_token2` is 995,000.
- A deposit of 100 arrives as 99. Its sweep emits 99 and the destination
  gains 98 (fee 1). `total_claimed_token2` becomes 995,099.
- A deposit of 1 arrives as 0 (fee 1). The next sweep moves 0, emits
  `token_amount` 0 and leaves the counter at 995,099.
- `withdraw` of 12,345 emits `amount` 12,345, and the user receives 12,221
  (124 withheld). A deposit of 7 arrives as 6. That withdraw emits 6, the
  user gains 5, and the next withdraw gives 6036.
- `withdraw` of 1 emits `amount` 1, and the user receives 0. A deposit of
  10,000,000 arrives as 9,995,000. Its withdraw emits 9,995,000, and the user
  receives 9,990,000 (fee capped at 5,000).

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "...", "candidate": "..."}'
```

`producer.py` checks every discriminator and account order it uses against
`evidence/upstream/pump_fees.json`. It then writes `runtime/receipts.jsonl.gz`
(one line per case: the full case input, per-step results for both images,
and final account bytes) and `runtime/report.json.gz` (summary, image sha256,
per-step outcomes and compute units). Fixed key seeds, a fixed clock,
`expire_blockhash` before each step and gzip `mtime=0` make the output
byte-identical across runs.

`verify.py` needs only this folder and the two images. It checks the image
sha256 values against the report, replays every case on both images, compares
each step and the final state with the receipt, and recomputes the match flags,
outcomes, compute units and counts in the report. It exits 0 on success and 1
on any difference. Two negative checks were run: swapping the images exits 1 on
the sha256 check, and changing one lamport value in one receipt step exits 1
(`s-vault-lamports-swept step 3 (sweep) original: replay differs from receipt`).

## Limits

- Token-2022 coverage uses a base-layout mint and one mint with only
  `TransferFeeConfig`. No transfer hooks, interest-bearing or other
  extensions are tested, and no epoch change between the two fee slots.
- `destination` is always a plain system wallet.
- Accounts are created by `initialize_buyback`, by the ATA program or as
  synthetic fixtures (mints, payer token accounts, referral vault token
  accounts). Nothing comes from mainnet snapshots.
- No pump or pump_amm CPI path is exercised.
