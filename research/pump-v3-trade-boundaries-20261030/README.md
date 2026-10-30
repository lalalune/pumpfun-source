# Pump Main v3 trades (buy_v3, buy_exact_quote_in_v3, sell_v3): original vs rebuild

## Question

Do the deployed Pump Main program and the source rebuild behave the same in the
v3 trade handlers, `buy_v3`, `buy_exact_quote_in_v3` and `sell_v3`? This
includes their argument and slippage boundaries, the curve-completion and
post-complete branches, FeeConfig tier selection and the error paths.

The v3 handlers differ from the legacy and v2 trades in one way that matters
for measuring them: they **do not CPI pump_fees**. `v3_trade_fees` deserializes
the pump_fees `FeeConfig` account itself (`programs/pump/src/util/fee.rs:182`).
It requires `data_len >= 2512`, picks the fee tier by market cap, and applies
`creator_fee_configurable` and the default-creator rule. A case therefore needs
only the pump image plus account state, and no pump_fees binary or stub is
involved.

None of the `research/` packets in the tree or in open pull requests measures
`*_v3` trades; `pump-instruction-decode-boundaries-20261030` covers only their
instruction decoding. The repository has `scripts/pump_v3_configured_fee_differential.py`
and `scripts/pump_v3_token_extensions_differential.py`. They cover v3 creator-fee
overrides, token-quote mints and near-completion `real_base` values. Both read
the captured fixture `research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json`
through `scripts/pump_trade_fixture.py`, and that file is not tracked at
origin/main, so they cannot run from a checkout. This packet is self-contained:
synthetic state built from the IDL layouts, on a native-SOL curve.

## Setup

- Images: the original is `evidence/original/pump/deployed.so` (sha256
  `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, 10,485,715 bytes).
  The rebuild is the partial candidate built by `scripts/build_partial_candidate.py`
  (platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree
  `97a2a2a383ba1bc5c5af08429de150e6124f0fc1`, sha256
  `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633`, 1,934,648 bytes).
  Both hashes are recorded in `runtime/report.json.gz` and checked by `verify.py`.
- Pump runs under the upgradeable loader (program account plus programdata, the
  mainnet layout). The VM is LiteSVM (solders 0.27.1), with a fresh VM per case,
  a fixed clock, fixed-seed keys and no network.
- State: a 1,088-byte Global and a 166-byte BondingCurve with virtual reserves
  1,073,000,000,000,000 / 30,000,000,000 and real token reserves 793,100,000,000,000.
  The FeeConfig is 2,512 bytes, owned by pump_fees, with one tier of 95 / 30 bps
  unless the case changes it. Global buyback bps are 5,000 and buyback recipient
  0 is passed. The `cross/*` cases put the whole supply (1,000,000,000,000,000)
  in the curve's base ATA, as on a launched curve, so the post-complete pool has
  206,900,000,000,000 base tokens. The other cases hold only the real reserves.
- Instruction data uses the upstream IDL discriminators (`evidence/upstream/pump.json`, asserted
  by `producer.py`). `partial_fill` is the 1-byte `OptionBool` and is `0`
  unless the case says otherwise.
- Each case's initial accounts, instruction bytes and metas are in `runtime/plan.json.gz`.

## Result

**60 cases and 120 receipts. Behavior is identical in all 60 cases.** The
transaction bytes, error, return data, emitted events (TradeEvent and
PostCompleteBuyEvent), inner instructions and the after-state of every
non-executable account match byte for byte between the two images.

- Stops: 27 successes. The 33 failures cover 20 error names: NotEnoughTokensToBuy 5;
  BondingCurveComplete, BuyNotEnoughSolToCoverFees, BuyZeroAmount,
  BuybackFeeRecipientNotAuthorized, CashbackCoinNotSupported, FeeTiersEmpty,
  Overflow, TooMuchSolRequired and Truncation 2 each; and 1 each of the rest.
- Compute units are equal and logs are identical in 26 cases: 22 successes and
  the 4 Anchor-framework rejections that happen before the handler
  (AccountDiscriminatorMismatch, AccountOwnedByWrongProgram,
  InstructionDidNotDeserialize, MintDoesNotMatchBondingCurve).
- **All 5 successful `buy_exact_quote_in_v3` cases cost the original more**:
  `bxq/basic` +4, `bxq/whitelist-basic` +6, `bxq/mayhem-cross-partial` +7, `cross/bxq` +7
  and `bxq/whitelist-cross-partial` +12. Only the `consumed` lines differ. Every
  successful `buy_v3` and `sell_v3` case has equal CU.
- In the 29 handler-raised errors, the AnchorError source site is
  `programs/pump/src/...` in the original and `src/...` in the rebuild, with the
  same line numbers (23 distinct sites, all listed in the report). The original
  costs more:
  - +14 CU for most `require!` sites;
  - +15 for `util/fee.rs:183` (FeeConfigTooShort) and `util/fee.rs:34` (Truncation);
  - +10 for `trade_v3.rs:317` (BuyNotEnoughSolToCoverFees);
  - +18 for `trade_v3.rs:1001` (BuySlippageBelowMinTokensOut);
  - +118 at 6 sites: `trade_v3.rs:506`, `:518`, `:802`, `:1127`,
    `lib.rs:1879` and `fee.rs:162` (`fee.rs:162` is +119 on buy and +118 on sell);
  - +126 for `trade_v3.rs:926`.

  This packet does not determine the cause of the 118–126 CU gaps.

Measured behavior on both images (same values in each):

- `buy_v3` running past `real_token_reserves` crosses into the post-complete
  branch for an ordinary user, whether `partial_fill` is 0 or 1. The curve is
  bought out (793,100,000,000,000 tokens for 85,005,359,057 lamports, then
  `complete=1`), and the excess is priced against a virtual pool of
  206,900,000,000,000 / 85,005,359,057:
  - `cross/excess-T`: a 1,000,000,000,000-token excess costs `quote_in` 412,847,786,
    with fee 3,922,054, creator fee 1,238,544 and buyback 1,961,027.
  - The curve records the excess in `post_complete_base_out` and
    `post_complete_quote_in`, and `real_quote_reserves` stays 85,005,359,057.
  - Global buyback bps 0 / 5,000 / 10,000 send 0 / 1,961,027 / 3,922,054 of the
    post-complete protocol fee to the buyback recipient. The curve's
    `protocol_fees` grows by the remainder: 811,472,966 / 405,736,483 / 0 in total.
  - A Global `pool_migration_fee` of 1,500,000,000 lowers the pool quote to
    83,505,359,057 and `quote_in` to 405,562,696. A fee above real quote plus
    curve quote stops with Overflow at `trade_v3.rs:502`.
  - An excess of 1 costs `quote_in` 1, fee 1 and creator fee 1, because both
    fees round up. An excess equal to the pool base stops with
    NotEnoughTokensToBuy (`:518`). An excess of pool base − 1 stops with
    Truncation (`:526`, because `quote_in` does not fit in u64). With only the
    real reserves in the ATA, pool base is 0 and a 1-token excess stops at `:506`.
- Users who may not cross: a whitelisted user (`Global.whitelist_pda`) or a
  mayhem curve.
  - With `partial_fill=0` they stop with NotEnoughTokensToBuy (`:802`; `:926`
    for exact-quote).
  - With `partial_fill=1` the buy is clamped to the real reserves and completes the curve.
  - The whitelisted user pays 0 bps protocol and creator fees.
- `OptionBool`: when the byte is omitted, the buy succeeds with the same
  amounts as `partial_fill=0` (54,485 CU vs 54,487 CU). A byte value of 2 gives
  InstructionDidNotDeserialize.
- FeeConfig:
  - A length of 2,511 gives FeeConfigTooShort; 2,512 works.
  - An empty tier vector gives FeeTiersEmpty.
  - A market cap one below the first threshold picks the first tier (77 / 11 bps).
  - A market cap equal to a threshold picks that tier (50 / 10 for the first,
    120 / 20 for the last).
  - Protocol bps 10,000 charge a fee equal to the quote. Protocol bps u64::MAX
    give Truncation (`fee.rs:34`).
  - A FeeConfig owned by the System program gives AccountOwnedByWrongProgram;
    a zeroed discriminator gives AccountDiscriminatorMismatch.

## Cases

The CU column is the original image's CU. The next column is the original minus
the rebuild. "Result" is decoded from the original's TradeEvent and
PostCompleteBuyEvent (the rebuild's are byte-identical).

| case | instruction | stop (both images) | CU original | CU orig - rebuild | result |
|---|---|---|---|---|---|
| `buy/basic` | buy_v3 | success | 54487 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `buy/max-equals-cost` | buy_v3 | success | 54487 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `buy/max-cost-minus-1` | buy_v3 | TooMuchSolRequired (6002) | 34761 | +14 |  |
| `buy/amount-zero` | buy_v3 | BuyZeroAmount (6020) | 31820 | +14 |  |
| `buy/amount-1` | buy_v3 | success | 54247 | +0 | tokens 1, quote 1, fee 95bp/1, creator 30bp/1 |
| `buy/partial-byte-absent` | buy_v3 | success | 54485 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 30bp/83956 |
| `buy/partial-byte-2` | buy_v3 | InstructionDidNotDeserialize (102) | 6112 | +0 |  |
| `buy/exact-real` | buy_v3 | success | 60098 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1 |
| `buy/real-plus-1-pool-base-0` | buy_v3 | NotEnoughTokensToBuy (6021) | 34167 | +118 |  |
| `cross/excess-1` | buy_v3 | success | 69025 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1, quote_in 1, fee 1, creator 1, buyback 0, pool before 206900000000000/85005359057 |
| `cross/excess-T` | buy_v3 | success | 69162 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 1238544, buyback 1961027, pool before 206900000000000/85005359057 |
| `cross/excess-pool-minus-1` | buy_v3 | Truncation (6025) | 33169 | +14 |  |
| `cross/excess-pool` | buy_v3 | NotEnoughTokensToBuy (6021) | 34596 | +118 |  |
| `cross/max-curve-only` | buy_v3 | TooMuchSolRequired (6002) | 37184 | +14 |  |
| `cross/buyback-bps-0` | buy_v3 | success | 69060 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 1238544, buyback 0, pool before 206900000000000/85005359057 |
| `cross/buyback-bps-10000` | buy_v3 | success | 69162 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 1238544, buyback 3922054, pool before 206900000000000/85005359057 |
| `cross/creator-default` | buy_v3 | success | 68554 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/0, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 0, buyback 1961027, pool before 206900000000000/85005359057 |
| `cross/migration-fee` | buy_v3 | success | 69163 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 405562696, fee 3852846, creator 1216689, buyback 1926423, pool before 206900000000000/83505359057 |
| `cross/migration-fee-over` | buy_v3 | Overflow (6024) | 32861 | +14 |  |
| `cross/partial-flag` | buy_v3 | success | 69164 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 1000000000000, quote_in 412847786, fee 3922054, creator 1238544, buyback 1961027, pool before 206900000000000/85005359057 |
| `cross/bxq` | buy_exact_quote_in_v3 | success | 73213 | +7 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1; post-complete base_out 28825461005666, quote_in 13760073039, fee 130720694, creator 41280220, buyback 65360347, pool before 206900000000000/85005359057 |
| `buy/whitelist-over-real` | buy_v3 | NotEnoughTokensToBuy (6021) | 32354 | +118 |  |
| `buy/whitelist-over-real-partial` | buy_v3 | success | 59430 | +0 | tokens 793100000000000, quote 85005359057, fee 0bp/0, creator 0bp/0, complete=1 |
| `buy/whitelist-small` | buy_v3 | success | 53811 | +0 | tokens 1000000000000, quote 27985075, fee 0bp/0, creator 0bp/0 |
| `buy/mayhem-over-real` | buy_v3 | NotEnoughTokensToBuy (6021) | 32327 | +118 |  |
| `buy/mayhem-over-real-partial` | buy_v3 | success | 59473 | +0 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1 |
| `buy/complete-curve` | buy_v3 | BondingCurveComplete (6005) | 30772 | +14 |  |
| `buy/cashback-coin` | buy_v3 | CashbackCoinNotSupported (6094) | 30779 | +14 |  |
| `buy/buyback-stranger` | buy_v3 | BuybackFeeRecipientNotAuthorized (6057) | 31164 | +14 |  |
| `buy/buyback-default` | buy_v3 | BuybackFeeRecipientMissing (6062) | 31238 | +118 |  |
| `buy/quote-mint-other` | buy_v3 | MintDoesNotMatchBondingCurve (6004) | 21800 | +0 |  |
| `buy/creator-fee-configurable` | buy_v3 | success | 54492 | +0 | tokens 1000000000000, quote 27985075, fee 95bp/265859, creator 250bp/699627 |
| `fee/len-2511` | buy_v3 | FeeConfigTooShort (6097) | 32113 | +15 |  |
| `fee/tiers-empty` | buy_v3 | FeeTiersEmpty (6096) | 32051 | +119 |  |
| `fee/owner-system` | buy_v3 | AccountOwnedByWrongProgram (3007) | 11013 | +0 |  |
| `fee/bad-disc` | buy_v3 | AccountDiscriminatorMismatch (3002) | 10733 | +0 |  |
| `fee/mcap-below-first` | buy_v3 | success | 54513 | +0 | tokens 1000000000000, quote 27985075, fee 77bp/215486, creator 11bp/30784 |
| `fee/mcap-at-first` | buy_v3 | success | 54552 | +0 | tokens 1000000000000, quote 27985075, fee 50bp/139926, creator 10bp/27986 |
| `fee/mcap-at-second` | buy_v3 | success | 54537 | +0 | tokens 1000000000000, quote 27985075, fee 120bp/335821, creator 20bp/55971 |
| `fee/protocol-10000` | buy_v3 | success | 54485 | +0 | tokens 1000000000000, quote 27985075, fee 10000bp/27985075, creator 0bp/0 |
| `fee/bps-u64-max` | buy_v3 | Truncation (6025) | 32325 | +15 |  |
| `bxq/basic` | buy_exact_quote_in_v3 | success | 55936 | +4 | tokens 34199203120618, quote 987654320, fee 95bp/9382717, creator 30bp/2962963 |
| `bxq/min-zero` | buy_exact_quote_in_v3 | BuyZeroAmount (6020) | 31783 | +14 |  |
| `bxq/spend-zero` | buy_exact_quote_in_v3 | BuyNotEnoughSolToCoverFees (6041) | 31927 | +14 |  |
| `bxq/spend-1` | buy_exact_quote_in_v3 | BuyNotEnoughSolToCoverFees (6041) | 33944 | +10 |  |
| `bxq/min-huge` | buy_exact_quote_in_v3 | BuySlippageBelowMinTokensOut (6042) | 36118 | +18 |  |
| `bxq/whitelist-cross` | buy_exact_quote_in_v3 | NotEnoughTokensToBuy (6021) | 31843 | +126 |  |
| `bxq/whitelist-cross-partial` | buy_exact_quote_in_v3 | success | 60524 | +12 | tokens 793100000000000, quote 85005359057, fee 0bp/0, creator 0bp/0, complete=1 |
| `bxq/mayhem-cross-partial` | buy_exact_quote_in_v3 | success | 62881 | +7 | tokens 793100000000000, quote 85005359057, fee 95bp/807550912, creator 30bp/255016078, complete=1 |
| `bxq/whitelist-basic` | buy_exact_quote_in_v3 | success | 54303 | +6 | tokens 34612903192310, quote 1000000000, fee 0bp/0, creator 0bp/0 |
| `sell/basic` | sell_v3 | success | 51875 | +0 | tokens 1000000000000, quote 30800821, fee 95bp/292608, creator 30bp/92403 |
| `sell/amount-zero` | sell_v3 | SellZeroAmount (6022) | 31788 | +14 |  |
| `sell/min-huge` | sell_v3 | TooLittleSolReceived (6003) | 34389 | +14 |  |
| `sell/more-than-balance` | sell_v3 | NotEnoughTokensToSell (6023) | 32319 | +118 |  |
| `sell/all-balance` | sell_v3 | success | 51973 | +0 | tokens 100000000000000, quote 2795899347, fee 95bp/26561044, creator 30bp/8387699 |
| `sell/complete` | sell_v3 | BondingCurveComplete (6005) | 30771 | +14 |  |
| `sell/cashback` | sell_v3 | CashbackCoinNotSupported (6094) | 30778 | +14 |  |
| `sell/buyback-stranger` | sell_v3 | BuybackFeeRecipientNotAuthorized (6057) | 31123 | +14 |  |
| `sell/rqr-short` | sell_v3 | Overflow (6024) | 32842 | +14 |  |
| `sell/fee-tiers-empty` | sell_v3 | FeeTiersEmpty (6096) | 32007 | +118 |  |

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

`producer.py` reads only `evidence/upstream/pump.json` from the repository, to
assert the discriminators. Two runs give byte-identical `runtime/` files.
`verify.py` uses only this folder and the two images:

1. it checks both image hashes and the receipt hash against the report;
2. it replays all 60 cases on both images and requires every receipt to equal
   the recorded one;
3. it recomputes the summary.

It exits 0 when everything matches and 1 otherwise. Expected output:
`{"ok": true, "cases": 60, "receipts_replayed": 120, "behavior_mismatches": {"upgradeable": []}, "compute_units_equal_cases": {"upgradeable": 26}}`.

## Files

- `producer.py`: case plan, synthetic state, execution, summary
- `verify.py`: independent replay (imports the execution code from `producer.py` in this folder)
- `runtime/plan.json.gz`: 60 cases with the full initial account set, instruction data and metas
- `runtime/receipts-upgradeable.jsonl.gz`: 120 receipts (tx, error, logs, CU, events, inner instructions, after-state)
- `runtime/report.json.gz`: image hashes, per-case comparison, aggregate counts

## Limits

- Only native-SOL curves (quote mint default, WSOL passed). The token-quote and
  Token-2022 transfer-fee branches of `check_quote` are not exercised here.
- `pool_migration_fee` and the post-complete branch are measured on the
  synthetic Global above, not on a captured mainnet state.
- LiteSVM is not the validator. CU values are LiteSVM's, and the original and
  rebuild are compared under the same runtime.
