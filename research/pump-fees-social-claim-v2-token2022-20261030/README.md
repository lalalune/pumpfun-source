# Pump Fees `claim_social_fee_pda_v2` with Token-2022 quote mints and extensions (original vs rebuild)

## Problem

`claim_social_fee_pda_v2` moves the whole token balance of the social-fee PDA's
quote ATA to the recipient's ATA with a `transfer_checked` CPI into the
caller-supplied quote token program. Before the CPI it checks the two ATAs:
canonical address, the create-if-missing branch for the recipient, and token
program ownership. After the CPI it writes the `SocialFeePdaClaimed` event and
the PDA counters.

Earlier coverage left out Token-2022 extensions:

- `research/pump-fees-social-claim-sequences-20261030` used legacy SPL mints only.
  Its README says: "Token-2022 was not used".
- `scripts/fees_social_claim_v2_differential.py` sends Token-2022 inputs only
  with the 82-byte base mint and 165-byte base account layout (no TLV
  extensions). It covers program pairing, frozen and uninitialized patches,
  and the missing ATA.

This packet runs the handler against Token-2022 mints and accounts that carry
extensions:

- TransferFeeConfig and TransferFeeAmount
- NonTransferable
- DefaultAccountState(Frozen)
- TransferHook
- MemoTransfer
- CpiGuard
- ImmutableOwner

It also runs the create-if-missing branch with extension mints, and claim
sequences that mix fee, plain and legacy mints on one social PDA. Every case
runs on the original image and on the rebuild.

## Images

| image | sha256 |
|---|---|
| original `evidence/original/pump_fees/deployed.so` | `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e` |
| rebuild (`scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `7eb3b25ef7ee45dcba86f2af79344297e98a091d`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`) | `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900` |

Only pump_fees is swapped. Token-2022, the Associated Token Account program and
Memo are the LiteSVM built-ins of solders 0.27.1, and both images use the same
ones.

## Result

**40 cases, 92 transactions. All 40 cases match between original and rebuild.**

Per step, the producer compares:

- error, Anchor error code and number, return data
- `Program data:` events and every `Program log:` line
- lamports, owner, length and sha256 of each watched account
- token amount, account state, TransferFeeAmount `withheld`
- decoded SocialFeePda counters

It also compares the final account bytes. Compute units are equal on every
step. `mismatched_cases = []` and `cu_mismatched_cases = []` in
`runtime/report.json.gz`.

Behaviour that both images share (measured, identical on both):

1. **Transfer-fee mints: the event and counters record the gross amount.** The
   recipient receives the amount minus the Token-2022 fee. The fee stays
   withheld in the recipient ATA. In the event, `amount_claimed`,
   `recipient_balance_after` (= `before + amount`) and the PDA's
   `total_stable_claimed` all use the pre-fee amount.
   - `f-fee-100bps-cap-5000`: the event says 5,000,000. The recipient ATA holds
     4,995,000 with 5,000 withheld.
   - `f-fee-10000bps`: the recipient ATA holds 0 with 5,000,000 withheld. The
     event still reports `recipient_balance_after` = 5,000,000.
   - `f-fee-100bps-amount-1`: the recipient receives 0 and 1 is withheld.
   - Rounding is ceiling: 99 → 1 withheld, 101 → 2, and at 1 bps 10,001 → 2.
   - A 0 bps fee or a max fee of 0 moves the full amount.
2. **Self-recipient.** With recipient = social PDA (`f-fee-social-is-recipient`)
   the source and destination ATA are the same account. Token-2022 moves
   nothing and charges no fee: 5,000,000 before and after, 0 withheld. The
   event reports `recipient_balance_before` 5,000,000 and
   `recipient_balance_after` 10,000,000. `total_stable_claimed` becomes
   5,000,000.
3. **Withheld tokens in the source ATA are not claimed.** The handler reads the
   token `amount`, not withheld tokens. In `f-fee-twice-lifetime`, the second
   claim moves 1,995,000. The 5,000 withheld by the deposit stays in the social
   PDA's ATA.
4. **The create-if-missing branch needs a writable authority.** The IDL marks
   `social_claim_authority` read-only. With that flag the ATA-creation CPI
   fails with `PrivilegeEscalation` (`m-recipient-ata-missing-auth-readonly`).
   When the authority is passed writable, the branch creates the recipient ATA:
   - 170 B for a plain Token-2022 mint (92,646 CU).
   - 182 B with TransferFeeAmount for a transfer-fee mint.
   - For a DefaultAccountState(Frozen) mint, the ATA is created frozen and the
     transfer fails (Token-2022 error 17, "Account is frozen").
5. **Extension errors come from the Token-2022 CPI, not from pump_fees.** No
   pump_fees check runs first:

   | case | result |
   |---|---|
   | NonTransferable mint | Token-2022 error 37 |
   | recipient ATA requires memo | error 36 |
   | social ATA has CpiGuard | error 42 |
   | recipient ATA lacks TransferFeeAmount | error 13 |
   | TransferHook mint (pump_fees passes no hook accounts) | `MissingAccount` |
   | memo-required social ATA | succeeds |
   | CpiGuard on the recipient ATA | succeeds |
   | DefaultAccountState mint with both ATAs already initialized and unfrozen | succeeds |

6. **A failed claim does not start the rate-limit window.**
   - In `s-failed-nontransferable-keeps-window`, a P22 claim succeeds in the
     same second after a failed NonTransferable claim.
   - A successful claim of one mint does block a claim of another mint in the
     same second (`s-t22-then-legacy-same-second`).
   - `total_stable_claimed` adds the amounts of different mints together
     without regard to decimals: 5,000,000 TF100 + 3,000,000 P22 = 8,000,000.

## Cases

Families:

- **b**: base Token-2022 (6 cases)
- **m**: ATA presence and address (6)
- **p**: legacy control and a Token-2022 ATA owned by SPL Token (2)
- **f**: TransferFee (13)
- **x**: other extensions and account states (9)
- **s**: sequences (4)

Each case first runs `create_social_fee_pda` (not shown below). The second
column is the transaction label. "recipient ATA amount after" is the token
amount of the claim's `associated_recipient` after the step, with the
TransferFeeAmount withheld value in parentheses when the extension exists.

| case | step | outcome (orig = rebuild) | match | event amount_claimed | event recipient_balance_after | recipient ATA amount after (withheld) | PDA total_stable_claimed | CU orig / rebuild |
|---|---|---|---|---|---|---|---|---|
| b-t22-plain-claim | v2 P22 | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 57995 / 57995 |
| b-t22-plain-claim | v2 P22 again +60 | ok — No fees available to claim | yes | — | — | 5000000 | 5000000 | 42373 / 42373 |
| b-t22-zero-decimals | v2 P22D0 | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 42995 / 42995 |
| b-t22-amount-1 | v2 P22 1 token | ok | yes | 1 | 1 | 1 | 1 | 57995 / 57995 |
| b-t22-amount-u64-max | v2 P22 u64 max | ok | yes | 18446744073709551615 | 18446744073709551615 | 18446744073709551615 | 18446744073709551615 | 57995 / 57995 |
| b-t22-empty | v2 P22 empty | ok — No fees available to claim | yes | — | — | 0 | 0 | 42372 / 42372 |
| b-t22-empty | v2 P22 empty again | ok — No fees available to claim | yes | — | — | 0 | 0 | 42372 / 42372 |
| b-t22-recipient-holds-balance | v2 P22 (recipient holds 777) | ok | yes | 5000000 | 5000777 | 5000777 | 5000000 | 57995 / 57995 |
| m-recipient-ata-missing-auth-readonly | v2 P22, recipient ATA missing, authority read-only | PrivilegeEscalation | yes | — | — | — | 0 | 49218 / 49218 |
| m-recipient-ata-missing-auth-writable | v2 P22, recipient ATA missing, authority writable | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 92646 / 92646 |
| m-recipient-ata-missing-auth-writable | v2 P22 +60 (ATA now exists) | ok — No fees available to claim | yes | — | — | 5000000 | 5000000 | 42373 / 42373 |
| m-recipient-ata-missing-tf-mint | v2 TF100, recipient ATA missing, authority writable | ok | yes | 5000000 | 5000000 | 4995000 (5000) | 5000000 | 70890 / 70890 |
| m-recipient-ata-missing-default-frozen | v2 DF, recipient ATA missing, authority writable | token-2022 error 17 — Error: Account is frozen | yes | — | — | — | 0 | 87251 / 87251 |
| m-social-ata-missing | v2 P22, social ATA missing | AccountNotInitialized | yes | — | — | 0 | 0 | 35653 / 35653 |
| m-recipient-ata-noncanonical | v2 P22, recipient slot = OTHER-owned ATA | ConstraintSeeds | yes | — | — | 0 | 0 | 21508 / 21508 |
| p-legacy-mint-control | v2 LEG with SPL Token | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 47281 / 47281 |
| p-t22-ata-owned-by-legacy | v2 P22, social ATA account owned by SPL Token | AccountTypeNotSupported | yes | — | — | 0 | 0 | 36065 / 36065 |
| f-fee-100bps-cap-5000 | v2 TF100 5,000,000 | ok | yes | 5000000 | 5000000 | 4995000 (5000) | 5000000 | 44220 / 44220 |
| f-fee-100bps-below-cap | v2 TF100 123,456 | ok | yes | 123456 | 123456 | 122221 (1235) | 123456 | 44219 / 44219 |
| f-fee-100bps-amount-1 | v2 TF100 1 token | ok | yes | 1 | 1 | 0 (1) | 1 | 44226 / 44226 |
| f-fee-100bps-amount-99 | v2 TF100 99 tokens | ok | yes | 99 | 99 | 98 (1) | 99 | 44219 / 44219 |
| f-fee-100bps-amount-101 | v2 TF100 101 tokens | ok | yes | 101 | 101 | 99 (2) | 101 | 44219 / 44219 |
| f-fee-0bps | v2 TF0 | ok | yes | 5000000 | 5000000 | 5000000 (0) | 5000000 | 40790 / 40790 |
| f-fee-10000bps | v2 TF10000 | ok | yes | 5000000 | 5000000 | 0 (5000000) | 5000000 | 41219 / 41219 |
| f-fee-max-0 | v2 TFMAX0 | ok | yes | 5000000 | 5000000 | 5000000 (0) | 5000000 | 41058 / 41058 |
| f-fee-1bps-ceil | v2 TF1 10,001 tokens | ok | yes | 10001 | 10001 | 9999 (2) | 10001 | 44219 / 44219 |
| f-fee-recipient-holds-balance | v2 TF100 (recipient holds 1,000,000) | ok | yes | 5000000 | 6000000 | 5995000 (5000) | 5000000 | 44220 / 44220 |
| f-fee-recipient-lacks-fee-amount-ext | v2 TF100, recipient ATA without TransferFeeAmount | token-2022 error 13 — Error: Invalid account state for operation | yes | — | — | 0 | 0 | 31929 / 31929 |
| f-fee-twice-lifetime | v2 TF100 | ok | yes | 5000000 | 5000000 | 4995000 (5000) | 5000000 | 44220 / 44220 |
| f-fee-twice-lifetime | deposit 2,000,000 into social ATA | ok | yes | — | — | — | 5000000 | 2942 / 2942 |
| f-fee-twice-lifetime | v2 TF100 +59 | ok — Claim rate limit exceeded | yes | — | — | 4995000 (5000) | 5000000 | 21201 / 21201 |
| f-fee-twice-lifetime | v2 TF100 +60 | ok | yes | 1995000 | 6990000 | 6985000 (10000) | 6995000 | 44221 / 44221 |
| f-fee-social-is-recipient | v2 TF100 recipient = social PDA | ok | yes | 5000000 | 10000000 | 5000000 (0) | 5000000 | 46369 / 46369 |
| x-transfer-hook | v2 HOOK (hook program not passed) | MissingAccount | yes | — | — | 0 | 0 | 35486 / 35486 |
| x-nontransferable | v2 NT | token-2022 error 37 — Transfer is disabled for this mint | yes | — | — | 0 | 0 | 27238 / 27238 |
| x-default-frozen-existing-thawed-dst | v2 DF (both ATAs initialized, unfrozen) | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 58379 / 58379 |
| x-recipient-frozen | v2 P22 recipient frozen | token-2022 error 17 — Error: Account is frozen | yes | — | — | 0 | 0 | 45653 / 45653 |
| x-source-frozen | v2 P22 social ATA frozen | token-2022 error 17 — Error: Account is frozen | yes | — | — | 0 | 0 | 44980 / 44980 |
| x-recipient-memo-required | v2 P22 recipient requires memo | token-2022 error 36 — Error: No memo in previous instruction; required for recipient to rece | yes | — | — | 0 | 0 | 45962 / 45962 |
| x-source-memo-required | v2 P22 social ATA requires memo | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 58097 / 58097 |
| x-source-cpi-guard | v2 P22 social ATA has CpiGuard | token-2022 error 42 — CPI Guard is enabled, and a program attempted to transfer user funds w | yes | — | — | 0 | 0 | 45696 / 45696 |
| x-recipient-cpi-guard | v2 P22 recipient has CpiGuard | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 58097 / 58097 |
| s-t22-then-legacy-same-second | v2 P22 | ok | yes | 5000000 | 5000000 | 5000000 | 5000000 | 57995 / 57995 |
| s-t22-then-legacy-same-second | v2 LEG same second | ok — Claim rate limit exceeded | yes | — | — | 0 | 5000000 | 21053 / 21053 |
| s-t22-then-legacy-same-second | v2 LEG +60 | ok | yes | 700000 | 700000 | 700000 | 5700000 | 47282 / 47282 |
| s-fee-then-plain-lifetime | v2 TF100 | ok | yes | 5000000 | 5000000 | 4995000 (5000) | 5000000 | 44220 / 44220 |
| s-fee-then-plain-lifetime | v2 P22 +60 | ok | yes | 3000000 | 3000000 | 3000000 | 8000000 | 57996 / 57996 |
| s-failed-nontransferable-keeps-window | v2 NT | token-2022 error 37 — Transfer is disabled for this mint | yes | — | — | 0 | 0 | 27238 / 27238 |
| s-failed-nontransferable-keeps-window | v2 P22 same second | ok | yes | 3000000 | 3000000 | 3000000 | 3000000 | 57995 / 57995 |
| s-rate-zero-double-fee-claim | v2 TF100 + v2 TF100 in one tx | ok — No fees available to claim | yes | 5000000 | 5000000 | 4995000 (5000) | 5000000 | 71518 / 71518 |
| s-rate-zero-double-fee-claim | deposit 1,000,000 | ok | yes | — | — | — | 5000000 | 2942 / 2942 |
| s-rate-zero-double-fee-claim | v2 TF100 same second (rate 0) | ok | yes | 995000 | 5990000 | 5985000 (10000) | 5995000 | 44210 / 44210 |

## Fixtures

- The social PDA is user_id `12345`, platform 0 (`CA7eyVhVQP2xo9j7VxDqo2DZ6UabcVyb8R5TcpwRVDvW`). It is created by `create_social_fee_pda` on the first step of every case.
- `FeeProgramGlobal` is synthesized with authority = social claim authority = seed-223 key and `claim_rate_limit` 60 (0 in `s-rate-zero-double-fee-claim`).
- Mints are synthetic Token-2022 accounts: the 82-byte base mint, padding to 165 bytes, AccountType = Mint, then TLV extensions. TransferFee uses the same older and newer config at epoch 0. The `mints` map in the report lists every address, decimals and extension.
- Token accounts are 165-byte base accounts, then AccountType = Account and TLV entries:
  - ImmutableOwner, as the ATA program writes it;
  - TransferFeeAmount for fee mints;
  - NonTransferableAccount / TransferHookAccount, when the mint needs them;
  - MemoTransfer / CpiGuard, where the case says so.
- Token deposits in sequences are real Token-2022 `TransferChecked` instructions from the fee payer's ATA, so the fee is withheld the same way as on a live transfer.
- The claim transaction is `SetComputeUnitLimit(1,400,000)` + `claim_social_fee_pda_v2`. The account order and flags follow `evidence/upstream/pump_fees.json`. `producer.py` asserts the discriminators, account order and flags against that IDL. The only exception is the `auth_writable` cases, which mark `social_claim_authority` writable.
- One case from the first draft was dropped: a canonical ATA address whose token-account owner field names a different wallet. A Token-2022 ATA carries ImmutableOwner, so an ATA program cannot produce that layout.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

- `producer.py` is deterministic: fixed key seeds and clock values, gzip `mtime=0`, sorted JSON. Two runs give byte-identical `runtime/` files.
- `verify.py` needs only the packet files and the two images:
  1. It checks the image sha256 values against the report.
  2. It replays every recorded case on both images, using the replay code in `producer.py` and the case data stored in the receipts.
  3. It compares every step and the final account state with the receipts.
  4. It recomputes the match flags, outcomes, compute units and summary lists.

  It exits 0 on success and 1 on any difference.

## Files

| file | content |
|---|---|
| `producer.py` | case definitions, LiteSVM runner, report writer |
| `verify.py` | independent replay and consistency check |
| `runtime/receipts.jsonl.gz` | one line per case: case inputs, both images' per-step results, final account bytes |
| `runtime/report.json.gz` | image sha256, mint map, per-case outcomes and compute units, mismatch lists |
| `MANIFEST.json` | sha256 and size of every other file |
