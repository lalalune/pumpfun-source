# Pump Main v3 trades on token-quote curves (SPL, USDC, WSOL, Token-2022): original vs rebuild

## Question

Do the deployed Pump Main program and the source rebuild behave the same when
`buy_v3`, `buy_exact_quote_in_v3` and `sell_v3` run on a curve whose
`quote_mint` is a token? In that case the v3 handlers:

- choose the fee source from the quote mint and the FeeConfig length
  (`programs/pump/src/util/fee.rs:182`). WSOL uses the SOL tiers. USDC uses
  `stable_fee_tiers`, but only when `data_len > 4072`. Any other mint uses
  `exotic_flat_fees` when `data_len > 4096` and one of its three fields is
  non-zero, and `flat_fees` otherwise;
- admit the buyback recipient as a token account (`trade_v3.rs:169`): owner
  program, mint, owner in the Global buyback list, canonical ATA;
- check the curve and user quote accounts (`buy_v2.rs` helpers);
- gross up Token-2022 transfer fees, and run the post-complete branch without
  subtracting `pool_migration_fee`, which is subtracted only for SOL;
- accrue fees on the curve (`BondingCurve.accrue_fees`: checked adds to
  `creator_fee` / `protocol_fees`, buyback split skipped on mayhem curves).

The companion packet `pump-v3-trade-boundaries-20261030` covers native-SOL
curves; this packet covers token quotes. No `research/` packet in the tree or in
open pull requests measures v3 token-quote trades. The repo's
`scripts/pump_v3_configured_fee_differential.py` and
`scripts/pump_v3_token_extensions_differential.py` sweep creator-fee overrides
and Token-2022 fee parameters on v3. Both read the captured fixture
`research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json`
through `scripts/pump_trade_fixture.py`, and that file is not tracked at
origin/main. This packet is self-contained: synthetic state built from the IDL
layouts. Fee-source selection by FeeConfig length, buyback admission and quote
account checks are not in those scripts.

## Setup

- Images: the original is `evidence/original/pump/deployed.so` (sha256
  `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, 10,485,715 bytes).
  The rebuild is the partial candidate built by `scripts/build_partial_candidate.py`
  (platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree
  `97a2a2a383ba1bc5c5af08429de150e6124f0fc1`, sha256
  `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633`, 1,934,648 bytes).
  Both hashes are recorded in `runtime/report.json.gz` and checked by `verify.py`.
- Pump runs under the upgradeable loader (program account plus programdata).
  SPL Token, Token-2022 and ATA are LiteSVM's (solders 0.27.1) built-ins.
  Every transaction starts with SetComputeUnitLimit(1,400,000). There is a
  fresh VM per case, a fixed clock, fixed-seed keys and no network.
- State: a 1,088-byte Global (buyback bps 5,000) and a 166-byte curve with
  virtual reserves 1,073,000,000,000,000 / 30,000,000,000, with `quote_mint` set
  to the case's mint.
  - Quote mints: an SPL mint, the USDC address `EPjF...Dt1v`, WSOL, and a
    Token-2022 mint with a TransferFeeConfig extension (100 bps, no maximum,
    unless the case changes it).
  - Quote token accounts exist for the curve, the user (10^15 units) and Global
    buyback recipient 0.
  - FeeConfig: by default 2,512 bytes, SOL tier 95 / 30 bps; most cases set
    flat fees to 90 / 20.
  - `*cross*` cases put the full supply in the curve's base ATA, as in the
    companion packet.
- Each case's initial accounts, instruction bytes and metas are in `runtime/plan.json.gz`.

## Result

**54 cases and 108 receipts. Behavior is identical in all 54 cases.** The
transaction bytes, error, return data, events (TradeEvent and
PostCompleteBuyEvent), inner instructions (token transfers) and the after-state
of every non-executable account match byte for byte between the two images.

- Stops: 30 successes and 24 failures. The failures are:
  - AccountTypeNotSupported 4 and MintDoesNotMatchBondingCurve 4;
  - AccountNotInitialized 3;
  - ConstraintSeeds 2, FeeTiersEmpty 2 and SPL Token error 1 (insufficient funds) 2;
  - Overflow 3;
  - BuyNotEnoughSolToCoverFees, BuybackFeeRecipientNotAuthorized,
    TooLittleSolReceived and TooMuchSolRequired, 1 each.
- Compute units are equal and logs are identical in 31 cases: 26 successes, the
  2 SPL Token failures, and 3 Anchor account-constraint failures that happen
  before the handler.
- **The 4 successful `buy_exact_quote_in_v3` cases cost the original more**
  (`spl/bxq` +4, `t22/bxq` +4, `t22/bxq-spend-100` +4, `spl/bxq-cross` +7). Only
  the `consumed` lines differ. Every successful `buy_v3` and `sell_v3` case has
  equal CU. This is the same pattern as the native-SOL packet.
- In the 19 handler-raised errors, the AnchorError site is `programs/pump/src/...`
  in the original and `src/...` in the rebuild (same lines). The original costs more:
  - +14 CU for most sites;
  - +13 for `trade_v3.rs:891`;
  - +118 for `trade_v3.rs:172` and `:188` and `buy_v2.rs:109` and `:121`
    (`require_keys_eq!`);
  - +119 for `util/fee.rs:162`.

  This packet does not determine the cause of the 118/119 CU gaps.

Measured behavior on both images (same values in each):

- **Fee source.** All of these trade 1,000,000,000,000 tokens for a curve
  quote of 27,985,075:
  - SPL quote mint: flat 90 / 20 bps. Length 4,096 with exotic 70 / 10 still
    uses flat. Length 4,097 uses exotic 70 / 10.
  - Length 4,097 with exotic `(lp 5, protocol 0, creator 0)` selects exotic
    because one field is non-zero, so the trade pays **0 / 0 bps**.
  - Exotic all zero falls back to flat. An empty SOL tier vector does not
    affect the SPL quote.
  - USDC: length 4,072 gives FeeTiersEmpty, even with a stable tier present.
    Length 4,073 uses the stable tier (60 / 15). An empty stable vector gives
    FeeTiersEmpty. A market cap below the first stable threshold picks the
    first stable tier (61 / 16).
  - A curve with `quote_mint = WSOL` takes the token path and the SOL tiers (95 / 30).
- **Token-2022 transfer fee.** At 100 bps the user pays 28,619,759. The curve
  nets 28,201,961, the same as at 0 bps (where the user pays 28,334,890), and
  buyback recipient 0 nets 131,599 (132,929 at 0 bps). With `maximum_fee` 1 the
  user pays 28,334,891. A newer fee epoch in the future leaves the older 100 bps
  in force. 10,000 bps gives Overflow (`util/transfer_fee.rs:66`). A Token-2022
  mint without extensions behaves like 0 bps. `buy_exact_quote_in_v3` with a
  budget of 100 units spends 100 and gets 3,433,599 tokens with fee 1 and
  creator fee 1; a budget of 1 gives BuyNotEnoughSolToCoverFees (`:891`).
- **Token crossing.** SPL `cross` buys 794,100,000,000,000 tokens and the user
  pays 86,485,934,431. A Global `pool_migration_fee` of 1,500,000,000 changes
  nothing on a token quote: the pool quote stays 85,005,359,057 in both cases.
- **Fee accrual on the curve.**
  - A curve `creator_fee` of u64::MAX − 83,955 plus this trade's creator fee of
    83,956 gives Overflow (`lib.rs:2554`). One unit lower ends exactly at u64::MAX.
  - `protocol_fees` at u64::MAX gives Overflow (`lib.rs:2550`).
  - On a mayhem curve the buyback fee is 0 and `protocol_fees` keeps all 265,859.
  - A whitelisted user buys and sells on a token quote with 0 / 0 bps and
    0 buyback; the curve's virtual quote reserves end at 30,027,985,075 (buy)
    and 29,969,199,179 (sell).
- **Buyback admission (token path).**
  - A wallet or a missing account gives AccountTypeNotSupported (`trade_v3.rs:172`).
  - A token account of another mint gives MintDoesNotMatchBondingCurve (`:180`).
  - An owner outside the list gives BuybackFeeRecipientNotAuthorized (`lib.rs:1884`).
  - A listed owner at a non-ATA address gives ConstraintSeeds (`:188`).
  - The ATA of the last list slot (index 7) is accepted.
- **Quote accounts.**
  - A missing curve quote ATA gives AccountNotInitialized (`buy_v2.rs:60`, no creation).
  - A user quote account with another authority gives AccountTypeNotSupported
    (`buy_v2.rs:121`). One of another mint gives MintDoesNotMatchBondingCurve
    (`:116`). A missing one gives AccountTypeNotSupported (`:109`).
  - **A user quote token account at a non-ATA address is accepted**, with the
    same trade as `spl/basic`. A curve quote account at a non-ATA address fails
    the Anchor seeds constraint.
  - Token-2022 as program for an SPL mint, and SPL Token for a Token-2022 mint,
    give AccountNotInitialized.
  - A quote mint, or WSOL, that differs from `curve.quote_mint` gives
    MintDoesNotMatchBondingCurve.

## Cases

The CU column is the original image's CU. The next column is the original minus
the rebuild. "Result" is decoded from the original's TradeEvent (`quote_amount`
for token quotes) and PostCompleteBuyEvent (the rebuild's are byte-identical).
"1" in the stop column is SPL Token error 1, insufficient funds, in the token
transfer.

| case | instruction | stop (both images) | CU original | CU orig - rebuild | result |
|---|---|---|---|---|---|
| `spl/basic` | buy_v3 | success | 85145 | +0 | tokens 1000000000000, quote 27985075, fee 90bp/251866, creator 20bp/55971 |
| `spl/len-4096-exotic` | buy_v3 | success | 85145 | +0 | tokens 1000000000000, quote 27985075, fee 90bp/251866, creator 20bp/55971 |
| `spl/len-4097-exotic` | buy_v3 | success | 85148 | +0 | tokens 1000000000000, quote 27985075, fee 70bp/195896, creator 10bp/27986 |
| `spl/len-4097-exotic-lp-only` | buy_v3 | success | 76477 | +0 | tokens 1000000000000, quote 27985075, fee 0bp/0, creator 0bp/0 |
| `spl/len-4097-exotic-zero` | buy_v3 | success | 85152 | +0 | tokens 1000000000000, quote 27985075, fee 90bp/251866, creator 20bp/55971 |
| `spl/tiers-empty` | buy_v3 | success | 85053 | +0 | tokens 1000000000000, quote 27985075, fee 90bp/251866, creator 20bp/55971 |
| `usdc/len-4072` | buy_v3 | FeeTiersEmpty (6096) | 46190 | +119 |  |
| `usdc/len-4073` | buy_v3 | success | 83783 | +0 | tokens 1000000000000, quote 27985075, fee 60bp/167911, creator 15bp/41978 |
| `usdc/len-4073-empty` | buy_v3 | FeeTiersEmpty (6096) | 46095 | +119 |  |
| `usdc/stable-threshold` | buy_v3 | success | 83809 | +0 | tokens 1000000000000, quote 27985075, fee 61bp/170709, creator 16bp/44777 |
| `wsol/curve-quote-wsol` | buy_v3 | success | 76139 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `wsol/sell` | sell_v3 | success | 75588 | +0 | tokens 1000000000000, quote 30800821, fee 95bp/292608, creator 30bp/92403 |
| `spl/sell` | sell_v3 | success | 84594 | +0 | tokens 1000000000000, quote 30800821, fee 95bp/292608, creator 30bp/92403 |
| `spl/sell-curve-ata-short` | sell_v3 | TransactionErrorInstructionError((1, Tagged(InstructionErrorCustom(1)))) (1) | 62322 | +0 |  |
| `spl/bxq` | buy_exact_quote_in_v3 | success | 86594 | +4 | tokens 34199203120618, quote 987654320, fee 95bp/9382717, creator 30bp/2962963 |
| `spl/user-quote-short` | buy_v3 | TransactionErrorInstructionError((1, Tagged(InstructionErrorCustom(1)))) (1) | 62977 | +0 |  |
| `spl/cross` | buy_v3 | success | 99849 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 1238544, buyback 1961027, pool before 206900000000000/85005359057 |
| `spl/cross-migration-fee` | buy_v3 | success | 99849 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 1238544, buyback 1961027, pool before 206900000000000/85005359057 |
| `spl/bxq-cross` | buy_exact_quote_in_v3 | success | 103900 | +7 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 28825461005666, quote_in 13760073039, fee 130720694, creator 41280220, buyback 65360347, pool before 206900000000000/85005359057 |
| `bb/wallet-not-ata` | buy_v3 | AccountTypeNotSupported (6010) | 44669 | +118 |  |
| `bb/wrong-mint` | buy_v3 | MintDoesNotMatchBondingCurve (6004) | 45051 | +14 |  |
| `bb/owner-not-listed` | buy_v3 | BuybackFeeRecipientNotAuthorized (6057) | 44822 | +14 |  |
| `bb/non-canonical` | buy_v3 | ConstraintSeeds (2006) | 48358 | +118 |  |
| `bb/listed-7` | buy_v3 | success | 85327 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `bb/missing` | buy_v3 | AccountTypeNotSupported (6010) | 44669 | +118 |  |
| `qa/curve-ata-missing` | buy_v3 | AccountNotInitialized (3012) | 43328 | +14 |  |
| `qa/user-wrong-owner` | buy_v3 | AccountTypeNotSupported (6010) | 44607 | +118 |  |
| `qa/user-wrong-mint` | buy_v3 | MintDoesNotMatchBondingCurve (6004) | 44592 | +14 |  |
| `qa/user-system-owned` | buy_v3 | AccountTypeNotSupported (6010) | 44211 | +118 |  |
| `qa/user-non-ata` | buy_v3 | success | 85145 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `qa/curve-non-ata` | buy_v3 | ConstraintSeeds (2006) | 31759 | +0 |  |
| `qa/quote-program-2022` | buy_v3 | AccountNotInitialized (3012) | 31519 | +14 |  |
| `qa/quote-mint-mismatch` | buy_v3 | MintDoesNotMatchBondingCurve (6004) | 22229 | +0 |  |
| `qa/wsol-for-spl-curve` | buy_v3 | MintDoesNotMatchBondingCurve (6004) | 21916 | +0 |  |
| `t22/buy-100bps` | buy_v3 | success | 70932 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `t22/buy-0bps` | buy_v3 | success | 69610 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `t22/buy-max-fee-1` | buy_v3 | success | 70944 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `t22/buy-10000bps` | buy_v3 | Overflow (6024) | 40624 | +14 |  |
| `t22/newer-epoch-future` | buy_v3 | success | 70925 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `t22/max-cost-low` | buy_v3 | TooMuchSolRequired (6002) | 42617 | +14 |  |
| `t22/bxq` | buy_exact_quote_in_v3 | success | 72674 | +4 | tokens 33868005679246, quote 977777777, fee 95bp/9288889, creator 30bp/2933334 |
| `t22/bxq-spend-100` | buy_exact_quote_in_v3 | success | 66971 | +4 | tokens 3433599, quote 97, fee 95bp/1, creator 30bp/1 |
| `t22/bxq-spend-1` | buy_exact_quote_in_v3 | BuyNotEnoughSolToCoverFees (6041) | 39957 | +13 |  |
| `t22/sell` | sell_v3 | success | 70331 | +0 | tokens 1000000000000, quote 30800821, fee 95bp/292608, creator 30bp/92403 |
| `t22/sell-min-exact-plus` | sell_v3 | TooLittleSolReceived (6003) | 42218 | +14 |  |
| `t22/cross` | buy_v3 | success | 85905 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 1238544, buyback 1941416, pool before 206900000000000/85005359057 |
| `t22/program-spl` | buy_v3 | AccountNotInitialized (3012) | 31450 | +14 |  |
| `t22/no-extension` | buy_v3 | success | 67884 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `acc/creator-fee-max` | buy_v3 | Overflow (6024) | 57703 | +14 |  |
| `acc/creator-fee-fit` | buy_v3 | success | 85145 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `acc/protocol-fees-max` | buy_v3 | Overflow (6024) | 57695 | +14 |  |
| `acc/mayhem-spl` | buy_v3 | success | 75949 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `acc/whitelist-spl` | buy_v3 | success | 75871 | +0 | tokens 1000000000000, quote 27985075, fee 0bp/0, creator 0bp/0 |
| `acc/whitelist-spl-sell` | sell_v3 | success | 75326 | +0 | tokens 1000000000000, quote 30800821, fee 0bp/0, creator 0bp/0 |

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

`producer.py` reads only `evidence/upstream/pump.json` from the repository, to
assert the discriminators. Two runs give byte-identical `runtime/` files.
`verify.py` uses only this folder and the two images:

1. it checks both image hashes and the receipt hash against the report;
2. it replays all 54 cases on both images and requires every receipt to equal
   the recorded one;
3. it recomputes the summary.

It exits 0 when everything matches and 1 otherwise. Expected output:
`{"ok": true, "cases": 54, "receipts_replayed": 108, "behavior_mismatches": {"upgradeable": []}, "compute_units_equal_cases": {"upgradeable": 31}}`.

## Files

- `producer.py`: case plan, synthetic state, execution, summary
- `verify.py`: independent replay (imports the execution code from `producer.py` in this folder)
- `runtime/plan.json.gz`: 54 cases with the full initial account set, instruction data and metas
- `runtime/receipts-upgradeable.jsonl.gz`: 108 receipts (tx, error, logs, CU, events, inner instructions, after-state)
- `runtime/report.json.gz`: image hashes, per-case comparison, aggregate counts

## Limits

- Token-2022 coverage is the TransferFeeConfig extension on the quote mint.
  Transfer hooks and other extensions are not exercised.
- SPL Token, Token-2022 and ATA are LiteSVM's built-in versions, not the
  mainnet captures in `evidence/dependencies/`.
- LiteSVM is not the validator. CU values are LiteSVM's, and the original and
  rebuild are compared under the same runtime.
