# Pump Main v2 trades on a token-quote curve: Token-2022 transfer-fee parsing, fee arithmetic and quote-ATA admission, before the fee CPI

Program: Pump Main (`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`).
Images:
- original `evidence/original/pump/deployed.so`: sha256 `7a19affa…f7b02d`, 10,485,715 bytes;
- rebuild `candidate.so`: sha256 `1cbf63ae…ab81c6`, 1,934,176 bytes, source tree `33e7c004`.

The full hashes are in `runtime/report.json.gz`.

## Question

On a bonding curve whose `quote_mint` is an SPL Token or Token-2022 mint (not native SOL), `buy_v2`,
`buy_exact_quote_in_v2` and `sell_v2` do the following before they CPI into pump_fees `get_fees_with_quote_mint`:

1. Admit six quote token accounts: curve, user, creator vault, user volume accumulator, fee recipient and
   buyback recipient (`admit_associated_token_account` / `check_token_account`). Four of them may be
   created through the ATA program; the curve account may not.
2. For the two buys only, read the quote mint's Token-2022 `TransferFeeConfig` TLV extension and choose the
   older or newer fee by the current epoch. `buy_v2` then grosses the quote up
   (`pre_fee_amount`). `buy_exact_quote_in_v2` subtracts the fee from the input (`post_fee_amount`) and
   requires a non-zero remainder.

Do the original and the rebuild behave the same in these areas?
- the parser edges and the epoch choice;
- the fee-arithmetic boundaries: 0 / 1 / 9,999 / 10,000 / 10,001 / 65,535 bps, maximum-fee caps, and results
  near u64::MAX;
- the quote-ATA admission errors.

None of this is measured by the existing `research/` packets or by the open `research/` PRs.
- `scripts/pump_sell_v2_differential.py` sets transfer fees only for `sell_v2`, which reads the fee after the CPI.
- `scripts/pump_buy_v2_differential.py` has Token-2022 quote cases but no TransferFeeConfig.
- The native-SOL v2 paths are in `pump-trade-pre-fee-cpi-validation-20261030`, from an earlier run of this
  account.

## Result

**77 cases. Behavior matches in 77/77.** The compared fields are the transaction bytes, error, whether the
fee CPI was reached, the ATA-create count, return data, events, inner instructions and the after-state of
every account.

- By handler: `buy_v2` 54, `buy_exact_quote_in_v2` 15, `sell_v2` 8.
- 35 cases pass every pre-CPI check and reach the fee CPI on both images.
- 42 cases stop at the same check, with the same error, on both images.
- Compute units are equal in 44/77 cases. The other 33 cases are exactly the cases that log an
  `AnchorError thrown in <file>:<line>` site. In them the original's site is `programs/pump/src/…` and the
  rebuild's is `src/…` at the same line. No other log line differs.
  - 28 cases differ by **+14 CU**. This is the source-path effect already reported by
    `pump-global-admin-sequences`.
  - 5 cases differ by **+118 CU**. All 5 are `AccountTypeNotSupported` (6010), at `buy_v2.rs:81`, `:109` and
    `:121`.
  - The same `require_keys_eq!` helper with `MintDoesNotMatchBondingCurve` (6004), at `buy_v2.rs:88` and
    `:116`, costs +14 CU. The extra 104 CU therefore follows the error code, not the call site. This packet does
    not identify the cause.

The behavior below was measured on both images. It records what the program does today; it does not judge it.

### Parser

- A Token-2022 mint of exactly 82 bytes has no fee.
- Malformed mint data is rejected with `InvalidAccountData` during account deserialization, at about 11.2k CU
  and before the handler and Pump's parser run. This covers:
  - a 166-byte mint (account type only);
  - non-zero padding in bytes 82..165;
  - account type 2.
- Pump's parser returns `UnsupportedQuoteMint` (`transfer_fee.rs:31`) for:
  - a TransferFeeConfig of length 107;
  - a duplicated TransferFeeConfig;
  - an entry whose length runs past the end;
  - 3 trailing bytes.
- The parser accepts:
  - a config of length 109;
  - 1 trailing byte;
  - another extension before the config;
  - a zero-tag terminator. A terminator placed before the config hides it, so the fee is 0
    (79,376 CU, against 79,738 CU with the fee).

### Epoch choice

The newer fee applies when `epoch >= newer.epoch`.
- In the test the newer fee is 10,001 bps and becomes active at epoch 5. Epoch 4 reaches the CPI with the
  older 100 bps; epochs 5 and 6 fail with `Overflow`.
- When the older fee is the invalid one and the newer epoch is u64::MAX, epoch 0 fails.

### `buy_v2` gross-up (`transfer_fee.rs:66`, `Overflow`)

- These settings reach the CPI:
  - 0, 1 and 9,999 bps;
  - 10,000 bps with maximum fee 0;
  - 100 bps with maximum fee 0 or 1.
- These settings fail:
  - 10,000 bps with maximum fee u64::MAX (quote + max overflows);
  - 10,001 bps;
  - 65,535 bps. **65,535 bps fails even with maximum fee 0**, because `10,000 − bps` is computed before the
    cap.
- A quote of about 4.0e18:
  - passes at 5,000 bps;
  - fails at 9,000 bps uncapped;
  - passes at 9,000 bps with maximum fee 1;
  - fails at 10,000 bps when quote + maximum fee exceeds u64::MAX.

### `buy_exact_quote_in_v2` post-fee (`transfer_fee.rs:56` / `buy_v2.rs:873`)

- At 100 bps, the fee on an input of 1 rounds up to 1, so the case fails with `BuyNotEnoughSolToCoverFees`.
  Input 2 passes.
- 10,000 bps uncapped fails with `BuyNotEnoughSolToCoverFees`.
- 10,000 bps with maximum fee 999,999 on an input of 1,000,000 passes.
- 10,001 bps fails with `Overflow`, because the fee is larger than the input.
- **65,535 bps with maximum fee 0 reaches the CPI.** Here the cap hides the invalid rate, unlike in `buy_v2`.
- Input u64::MAX at 9,999 bps passes.

### `sell_v2`

A 10,001 bps config and a length-107 config both reach the CPI, because `sell_v2` reads the fee only after it.

### Quote ATA admission (SPL Token quote mint)

- These reach the CPI:
  - all six accounts present (108,277 CU for `buy_v2`);
  - only the creator-vault account missing (1 create, 145,603 CU);
  - four accounts missing (4 creates, 233,581 CU).
- Under the default 200,000 CU limit with four accounts missing, both images stop after 3 creates, at exactly
  200,000 CU. `buy_v2` ends in `ProgramFailedToComplete` and `sell_v2` in `ComputationalBudgetExceeded`.
- A missing curve quote account gives `AccountNotInitialized` (`buy_v2.rs:60`).
- A missing user quote account gives `AccountTypeNotSupported` (`:109`); it is never created.
- The user quote account is checked only for owner program, mint and owner. A non-ATA token account owned by
  the user is accepted.
- When the Token-2022 program is passed for an SPL mint, the curve quote ATA is derived under Token-2022, so the
  error is `AccountNotInitialized`.
- Wrong-key fee-recipient and volume-accumulator ATAs fail at the Anchor seeds constraint (`ConstraintSeeds`).
- `complete` and the fee-recipient check both run before quote-ATA admission:
  - `spl-complete-and-curve-ata-missing` gives `BondingCurveComplete`;
  - `spl-fee-recipient-stranger-and-ata-missing` gives `NotAuthorized`.
- With a Token-2022 transfer-fee quote mint, four ATA creates cost 189,426 CU.

## Cases

The stop is the same on both images in every row. "fee CPI reached" means the trade passed every pre-CPI
check, and the fee-program slot, which holds the image under test, rejected the call with
`DeclaredProgramIdMismatch`. Unless the case name contains `default-cu-limit`, the transaction starts with
`SetComputeUnitLimit(1,400,000)`.

| # | case | stop (both images) | site (original; rebuild drops `programs/pump/`) | CU original | CU rebuild | Δ | ATA creates |
|---|---|---|---|---:|---:|---:|---:|
| 1 | `buy_v2/t22-no-extensions-82-bytes` | fee CPI reached |  | 78,751 | 78,751 | +0 | 0 |
| 2 | `buy_v2/t22-transfer-fee-100bps` | fee CPI reached |  | 79,738 | 79,738 | +0 | 0 |
| 3 | `buy_v2/t22-account-type-only-166-bytes` | InvalidAccountData |  | 11,149 | 11,149 | +0 | 0 |
| 4 | `buy_v2/t22-account-type-and-1-byte` | fee CPI reached |  | 79,373 | 79,373 | +0 | 0 |
| 5 | `buy_v2/t22-terminator-before-config` | fee CPI reached |  | 79,376 | 79,376 | +0 | 0 |
| 6 | `buy_v2/t22-other-extension-then-config` | fee CPI reached |  | 79,761 | 79,761 | +0 | 0 |
| 7 | `buy_v2/t22-config-length-107` | UnsupportedQuoteMint | `util/transfer_fee.rs:31` | 76,180 | 76,166 | +14 | 0 |
| 8 | `buy_v2/t22-config-length-109` | fee CPI reached |  | 79,738 | 79,738 | +0 | 0 |
| 9 | `buy_v2/t22-config-duplicated` | UnsupportedQuoteMint | `util/transfer_fee.rs:31` | 76,219 | 76,205 | +14 | 0 |
| 10 | `buy_v2/t22-entry-length-past-end` | UnsupportedQuoteMint | `util/transfer_fee.rs:31` | 76,178 | 76,164 | +14 | 0 |
| 11 | `buy_v2/t22-trailing-3-bytes` | UnsupportedQuoteMint | `util/transfer_fee.rs:31` | 76,213 | 76,199 | +14 | 0 |
| 12 | `buy_v2/t22-trailing-1-byte` | fee CPI reached |  | 79,738 | 79,738 | +0 | 0 |
| 13 | `buy_v2/t22-nonzero-padding` | InvalidAccountData |  | 11,238 | 11,238 | +0 | 0 |
| 14 | `buy_v2/t22-account-type-2` | InvalidAccountData |  | 11,241 | 11,241 | +0 | 0 |
| 15 | `buy_v2/t22-tag-0-only-entry` | fee CPI reached |  | 79,376 | 79,376 | +0 | 0 |
| 16 | `buy_v2/epoch-4-newer-at-5` | fee CPI reached |  | 79,735 | 79,735 | +0 | 0 |
| 17 | `buy_v2/epoch-5-newer-at-5` | Overflow | `util/transfer_fee.rs:66` | 76,775 | 76,761 | +14 | 0 |
| 18 | `buy_v2/epoch-6-newer-at-5` | Overflow | `util/transfer_fee.rs:66` | 76,775 | 76,761 | +14 | 0 |
| 19 | `buy_v2/epoch-0-newer-at-u64-max` | Overflow | `util/transfer_fee.rs:66` | 76,772 | 76,758 | +14 | 0 |
| 20 | `buy_v2/bps-0` | fee CPI reached |  | 79,439 | 79,439 | +0 | 0 |
| 21 | `buy_v2/bps-1` | fee CPI reached |  | 79,738 | 79,738 | +0 | 0 |
| 22 | `buy_v2/bps-9999` | fee CPI reached |  | 79,738 | 79,738 | +0 | 0 |
| 23 | `buy_v2/bps-10000-max-fee-0` | fee CPI reached |  | 79,453 | 79,453 | +0 | 0 |
| 24 | `buy_v2/bps-10000-max-fee-u64` | Overflow | `util/transfer_fee.rs:66` | 76,780 | 76,766 | +14 | 0 |
| 25 | `buy_v2/bps-10001` | Overflow | `util/transfer_fee.rs:66` | 76,775 | 76,761 | +14 | 0 |
| 26 | `buy_v2/bps-65535` | Overflow | `util/transfer_fee.rs:66` | 76,775 | 76,761 | +14 | 0 |
| 27 | `buy_v2/bps-65535-max-fee-0` | Overflow | `util/transfer_fee.rs:66` | 76,775 | 76,761 | +14 | 0 |
| 28 | `buy_v2/bps-100-max-fee-0` | fee CPI reached |  | 79,746 | 79,746 | +0 | 0 |
| 29 | `buy_v2/bps-100-max-fee-1` | fee CPI reached |  | 79,746 | 79,746 | +0 | 0 |
| 30 | `buy_v2/near-u64-bps-5000` | fee CPI reached |  | 80,037 | 80,037 | +0 | 0 |
| 31 | `buy_v2/near-u64-bps-9000-uncapped` | Overflow | `util/transfer_fee.rs:66` | 77,273 | 77,259 | +14 | 0 |
| 32 | `buy_v2/near-u64-bps-9000-max-fee-1` | fee CPI reached |  | 80,045 | 80,045 | +0 | 0 |
| 33 | `buy_v2/near-u64-bps-10000-max-fee-near-limit` | Overflow | `util/transfer_fee.rs:66` | 76,993 | 76,979 | +14 | 0 |
| 34 | `buy_v2/t22-create-4-atas` | fee CPI reached |  | 189,426 | 189,426 | +0 | 4 |
| 35 | `buy_exact_quote_in_v2/t22-transfer-fee-100bps` | fee CPI reached |  | 79,283 | 79,283 | +0 | 0 |
| 36 | `buy_exact_quote_in_v2/input-1-bps-100` | BuyNotEnoughSolToCoverFees | `buy_v2.rs:873` | 77,954 | 77,940 | +14 | 0 |
| 37 | `buy_exact_quote_in_v2/input-2-bps-100` | fee CPI reached |  | 79,290 | 79,290 | +0 | 0 |
| 38 | `buy_exact_quote_in_v2/input-1-bps-0` | fee CPI reached |  | 79,016 | 79,016 | +0 | 0 |
| 39 | `buy_exact_quote_in_v2/bps-10000-uncapped` | BuyNotEnoughSolToCoverFees | `buy_v2.rs:873` | 77,947 | 77,933 | +14 | 0 |
| 40 | `buy_exact_quote_in_v2/bps-10000-max-fee-999999` | fee CPI reached |  | 79,285 | 79,285 | +0 | 0 |
| 41 | `buy_exact_quote_in_v2/bps-10001` | Overflow | `util/transfer_fee.rs:56` | 76,618 | 76,604 | +14 | 0 |
| 42 | `buy_exact_quote_in_v2/bps-65535-max-fee-0` | fee CPI reached |  | 79,285 | 79,285 | +0 | 0 |
| 43 | `buy_exact_quote_in_v2/input-u64-max-bps-9999` | fee CPI reached |  | 79,268 | 79,268 | +0 | 0 |
| 44 | `buy_exact_quote_in_v2/t22-config-length-107` | UnsupportedQuoteMint | `util/transfer_fee.rs:31` | 76,183 | 76,169 | +14 | 0 |
| 45 | `buy_exact_quote_in_v2/epoch-5-newer-at-5` | Overflow | `util/transfer_fee.rs:56` | 76,618 | 76,604 | +14 | 0 |
| 46 | `buy_v2/spl-all-atas-present` | fee CPI reached |  | 108,277 | 108,277 | +0 | 0 |
| 47 | `buy_v2/spl-default-cu-limit-all-present` | fee CPI reached |  | 108,127 | 108,127 | +0 | 0 |
| 48 | `buy_v2/spl-create-4-atas` | fee CPI reached |  | 233,581 | 233,581 | +0 | 4 |
| 49 | `buy_v2/spl-create-4-atas-default-cu-limit` | ProgramFailedToComplete |  | 200,000 | 200,000 | +0 | 3 |
| 50 | `buy_v2/spl-create-vault-ata-only` | fee CPI reached |  | 145,603 | 145,603 | +0 | 1 |
| 51 | `buy_v2/spl-curve-ata-missing` | AccountNotInitialized | `buy_v2.rs:60` | 83,883 | 83,869 | +14 | 0 |
| 52 | `buy_v2/spl-user-ata-missing` | AccountTypeNotSupported | `buy_v2.rs:109` | 84,749 | 84,631 | +118 | 0 |
| 53 | `buy_v2/spl-user-ata-wrong-mint` | MintDoesNotMatchBondingCurve | `buy_v2.rs:116` | 85,130 | 85,116 | +14 | 0 |
| 54 | `buy_v2/spl-user-ata-wrong-owner` | AccountTypeNotSupported | `buy_v2.rs:121` | 85,145 | 85,027 | +118 | 0 |
| 55 | `buy_v2/spl-user-quote-account-non-ata` | fee CPI reached |  | 108,277 | 108,277 | +0 | 0 |
| 56 | `buy_v2/spl-curve-ata-wrong-mint` | MintDoesNotMatchBondingCurve | `buy_v2.rs:88` | 84,710 | 84,696 | +14 | 0 |
| 57 | `buy_v2/spl-vault-ata-owned-by-token22` | AccountTypeNotSupported | `buy_v2.rs:81` | 92,877 | 92,759 | +118 | 0 |
| 58 | `buy_v2/spl-fee-recipient-ata-wrong-key` | ConstraintSeeds |  | 31,186 | 31,186 | +0 | 0 |
| 59 | `buy_v2/spl-uva-ata-wrong-key` | ConstraintSeeds |  | 69,950 | 69,950 | +0 | 0 |
| 60 | `buy_v2/spl-quote-program-token22` | AccountNotInitialized | `buy_v2.rs:60` | 63,074 | 63,060 | +14 | 0 |
| 61 | `buy_v2/spl-quote-mint-other` | MintDoesNotMatchBondingCurve |  | 29,505 | 29,505 | +0 | 0 |
| 62 | `buy_v2/spl-quote-mint-wsol` | MintDoesNotMatchBondingCurve |  | 31,005 | 31,005 | +0 | 0 |
| 63 | `buy_v2/spl-complete-and-curve-ata-missing` | BondingCurveComplete | `buy_v2.rs:345` | 75,813 | 75,799 | +14 | 0 |
| 64 | `buy_v2/spl-fee-recipient-stranger-and-ata-missing` | NotAuthorized | `fee_recipient.rs:35` | 69,994 | 69,980 | +14 | 0 |
| 65 | `buy_v2/spl-buyback-stranger` | BuybackFeeRecipientNotAuthorized | `lib.rs:1884` | 76,129 | 76,115 | +14 | 0 |
| 66 | `buy_exact_quote_in_v2/spl-all-atas-present` | fee CPI reached |  | 107,849 | 107,849 | +0 | 0 |
| 67 | `buy_exact_quote_in_v2/spl-create-4-atas` | fee CPI reached |  | 233,153 | 233,153 | +0 | 4 |
| 68 | `buy_exact_quote_in_v2/spl-curve-ata-missing` | AccountNotInitialized | `buy_v2.rs:60` | 83,881 | 83,867 | +14 | 0 |
| 69 | `buy_exact_quote_in_v2/spl-user-ata-wrong-owner` | AccountTypeNotSupported | `buy_v2.rs:121` | 85,144 | 85,026 | +118 | 0 |
| 70 | `sell_v2/spl-all-atas-present` | fee CPI reached |  | 105,395 | 105,395 | +0 | 0 |
| 71 | `sell_v2/spl-create-4-atas` | fee CPI reached |  | 230,699 | 230,699 | +0 | 4 |
| 72 | `sell_v2/spl-create-4-atas-default-cu-limit` | ComputationalBudgetExceeded |  | 200,000 | 200,000 | +0 | 3 |
| 73 | `sell_v2/spl-curve-ata-missing` | AccountNotInitialized | `buy_v2.rs:60` | 81,092 | 81,078 | +14 | 0 |
| 74 | `sell_v2/spl-user-ata-wrong-mint` | MintDoesNotMatchBondingCurve | `buy_v2.rs:116` | 82,339 | 82,325 | +14 | 0 |
| 75 | `sell_v2/spl-vault-ata-owned-by-token22` | AccountTypeNotSupported | `buy_v2.rs:81` | 90,087 | 89,969 | +118 | 0 |
| 76 | `sell_v2/t22-transfer-fee-10001bps` | fee CPI reached |  | 75,737 | 75,737 | +0 | 0 |
| 77 | `sell_v2/t22-config-length-107` | fee CPI reached |  | 75,737 | 75,737 | +0 | 0 |

## Method

- **Loader.** Both images are loaded under the upgradeable loader: a program account plus programdata, which is
  the mainnet layout.
  - Under LiteSVM's `add_program_from_file` (loader v2), a CPI that passes the Pump program account is charged
    by ELF size. That would add 34,206 CU to the original's fee-CPI cases.
  - This is a harness artifact documented in `pump-trade-pre-fee-cpi-validation-20261030`, so it is avoided
    here.
- **pump_fees slot.** pump_fees is not one of the two images, so the pump_fees address holds the image under
  test. The fee CPI then fails deterministically, which marks "every pre-CPI check passed". No trade completes,
  and every transaction is rolled back.
- **State.** All state is synthetic, built from the IDL and SPL layouts:
  - Global (1,088 bytes) and BondingCurve (166 bytes);
  - an SPL Token quote mint;
  - a Token-2022 quote mint with a TransferFeeConfig TLV entry;
  - quote token accounts. The Token-2022 ones carry TransferFeeAmount.
- **Programs.** SPL Token, Token-2022 and ATA are LiteSVM's built-in copies.
- **Determinism.** Keys come from fixed seeds and there is no network. The clock is fixed per case:
  - slot `1000 + index`;
  - a per-case epoch;
  - unix time `1,800,000,000 + index`.
- **Runtime files.**
  - `runtime/plan.json.gz`: the complete initial account set and the transaction of every case.
  - `runtime/receipts-upgradeable.jsonl.gz`: for each image and case, the transaction, error, logs, CU, inner
    instructions, ATA-create count, return data, events and account after-state hashes.
  - `runtime/report.json.gz`: the per-case comparison and the summary.

## Reproduce

```
python3 producer.py --root <pumpfun-source checkout> \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' \
  --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

- `producer.py` reads only `evidence/upstream/pump.json` from the repository, to check the instruction
  discriminators and account counts. Two runs produce byte-identical `runtime/` files.
- `verify.py` uses only this folder and the two images. It checks:
  1. the image sha256 values;
  2. the receipt-file sha256;
  3. all 154 receipts, replayed and compared byte for byte;
  4. the recomputed summary.
- `verify.py` exits 0 on success and 1 on any difference, including when the two images are swapped.

Requires Python 3 with `solders` 0.27.1 (`solders.litesvm`).
