# Pump Main trades after the fee quote: slippage, rounding, fee split and curve completion (original vs rebuild)

## Problem

Every Pump Main trade handler (`buy`, `buy_exact_sol_in`, `sell`, `buy_v2`,
`buy_exact_quote_in_v2`, `sell_v2`) CPIs pump_fees `get_fees_with_quote_mint`
and only then does the curve math, the slippage checks, fee rounding, the
lamport/token transfers, curve completion and the `TradeEvent`. pump_fees is
not one of the two images, so earlier offline runs stopped at that CPI. This
packet runs the trade handlers to the end and compares the original
`evidence/original/pump/deployed.so` with the rebuild `candidate.so`.

## Method

- The pump_fees slot (`pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`) holds a
  9-instruction SBPFv0 test double that `producer.py` generates (`fee_stub`,
  an 896-byte ELF built in memory and never written as a file). It ignores its input and returns
  the 24-byte `Fees {lp_fee_bps, protocol_fee_bps, creator_fee_bps}` value set for
  the case through `sol_set_return_data`. Both images get the identical stub
  (default stub sha256 `b2b7a41f…6c93`, in `report.json.gz`). The stub does not
  model pump_fees' fee tiers. The fee values are inputs chosen to hit rounding and
  overflow boundaries, so a difference can only come from Pump Main.
- Pump runs under the upgradeable loader (program account plus programdata, the
  mainnet layout). One fresh LiteSVM per case, fixed clock, fixed-seed keys,
  synthetic accounts from the IDL layouts (Global 1,088 B, BondingCurve 166 B),
  native-SOL curve with virtual reserves 1,073,000,000,000,000 tokens and
  30,000,000,000 lamports, and real token reserves 793,100,000,000,000.
- Boundary values (`max_sol_cost`, `min_sol_output`) come from the closed-form
  quote in `producer.py` (`buy_cost`, `sell_output`). The receipts show whether each
  boundary passes or fails.
- 81 cases: 71 single-instruction trades (6 of them on cashback curves,
  BondingCurve byte 82 = 1) and 10 multi-instruction sequences in one
  transaction (with a 600,000 CU ComputeBudget limit; they cover curve-state
  transitions). Each receipt has the transaction, error, full logs, compute units,
  inner instructions, return data, events and the after-state (lamports, owner,
  data) of every non-executable account the transaction touches.

## Results (81 cases, `runtime/report.json.gz`)

**Behavior: original and rebuild match in all 81 cases.** The transaction, error,
events, inner instructions, return data and every account after-state are
byte-identical. 54 cases succeed and 27 fail with the same error on both images.

Compute units are equal in 48 cases. The other 33 differ (original minus rebuild):

| delta | cases | where |
|---|---|---|
| +14 | 27 | every AnchorError except the two `NotEnoughTokensTo*` errors: the error-site string is `programs/pump/src/…` in the original and `src/…` in the rebuild (BuyZeroAmount 6, TooMuchSolRequired 4, Overflow 4, BondingCurveComplete 4, TooLittleSolReceived 2, InvalidCashbackAccumulator 2, BuySlippageBelowMinTokensOut 1) |
| +118 | 4 | `NotEnoughTokensToBuy` 6021 (3 cases: buy.rs:151, buy_v2.rs:997, lib.rs:619) and `NotEnoughTokensToSell` 6023 (1 case, lib.rs:972): the same 14-CU site difference plus 104 CU the logs don't explain |
| +1 | 6 | successful non-completing `buy_v2` / `buy_exact_quote_in_v2` (base, max-cost-exact, protocol-bps-10000, exact-quote base, `cashback/buy_v2`) and `seq/buy_v2-then-sell_v2`. Only the outer `consumed` line differs. The v2 completion buy (`buy_v2/amount-eq-real-reserves`) and all single `sell_v2` successes have delta 0 |

Only the outer `consumed` line and the AnchorError site line differ. All other
log lines are the same.

### Measured behavior (identical on both images)

Fee stub `(lp, protocol, creator) = (0, 95, 30)` unless noted. Lamport deltas
are from the after-state. The `user` delta includes the 5,000-lamport
transaction fee and, for buys, 1,844,400 lamports of rent for the new
user-volume accumulator.

- **Buy slippage boundary.** For `buy` of 10^9 tokens, sol cost = 27,960,
  protocol fee 266 and creator fee 84. `max_sol_cost` = 28,310 passes and
  28,309 fails with `TooMuchSolRequired` (6002). The same boundary holds for
  amount 1 (cost 1 + 1 + 1 = 3; 3 passes, 2 fails), for the completing buy and
  for `buy_v2`.
- **Fee rounding is ceiling.** `buy` of 1 token: sol 1, protocol fee 1, creator fee 1.
  `sell` of 35,767 tokens (gross quote 1 lamport by the closed-form quote, so
  ceiling fees are 1 + 1) fails with `Overflow` (6024, lib.rs:1009). Sell fee bps (9970, 30) and (9971, 30) both fail with
  `Overflow`. (0, 10000, 0) succeeds with the whole quote (27,958) going to
  fees, so the seller gets 0.
- **`sell` of 1 token** succeeds: quote 0, fees 0, curve real token reserves +1,
  no lamports to the seller.
- **Protocol fee split (Global `buyback_basis_points`, 5000 in the fixture).**
  The buyback recipient (remaining account) gets floor(fee × bps / 10000) and
  the fee recipient gets the rest. Measured on a 266-lamport fee, as
  (buyback, fee recipient):
  - bps 0 → (0, 266); bps 1 → (0, 266); bps 3333 → (88, 178);
    bps 5000 → (133, 133); bps 9999 → (265, 1); bps 10000 → (266, 0).
  - bps 10001 → (266, 0). The total stays the fee, so nothing beyond 266 is
    paid out.
  - `buy_exact_sol_in` of 10^9 lamports at 5000: 9,382,717 → 4,691,358 +
    4,691,359.
  - `sell` with bps 0 sends all 266 to the fee recipient.
  - On a mayhem curve with the reserved fee recipient, the full 266 goes to the
    reserved recipient and nothing goes to the buyback recipient.
- **Creator fee override (Global `creator_fee_configurable`, BondingCurve
  `creator_fee_bps`).** With the flag on and curve bps 200, the creator fee is
  560 (200 bps) instead of 84. Curve bps 0 falls back to the pump_fees value
  (30 → 84). With the flag off, curve bps 200 is ignored (84). With the flag on,
  curve bps 5000 is above Global `max_configurable_creator_fee_bps` (500) and is
  still applied at trade time: creator fee 13,980. The maximum is not checked
  in the trade path.
- **The fee bps returned by pump_fees are not bounded by Pump Main.** With
  protocol bps 2^31-1, `buy` of 10^9 tokens charges a protocol fee of
  6,004,364,278 lamports and succeeds, because `max_sol_cost` was 10^15.
  `lp_fee_bps` = 25 changes nothing.
- **No creator fee without a creator.** When the curve creator is the default
  key, the event has `creator_fee_basis_points` 30 and `creator_fee` 0 (buy and
  sell).
- **Curve completion.** Buying exactly the 793,100,000,000,000 real tokens costs
  85,005,359,057 + 807,550,912 + 255,016,078 lamports and sets
  `complete` = 1 (virtual token reserves 279,900,000,000,000). Buying 1 fewer
  token costs the same lamports and leaves 1 token and `complete` = 0. A
  partial-fill buy of reserves + 1 is clamped to the reserves and completes.
  `buy_v2` behaves the same way.
- **buy_exact_sol_in.** 10^9 lamports spendable with (95, 30) bps → sol 987,654,320
  and 34,199,203,120,618 tokens. Spendable 1, 2, 3 and 1,000, and protocol bps
  10000, all fail with `BuyZeroAmount` (6020, buy.rs:57). Spendable 10^12
  (more than the curve) fails with `NotEnoughTokensToBuy` (6021, buy.rs:151).
  `buy_exact_quote_in_v2` matches (BuyZeroAmount at buy_v2.rs:769,
  NotEnoughTokensToBuy at buy_v2.rs:997). A `min_tokens_out` of u64::MAX fails
  with `BuySlippageBelowMinTokensOut` (6042, buy.rs:143).
- **Sell boundaries.** For `sell` of 10^9 tokens, `min_sol_output` = gross − fees
  passes and +1 fails with `TooLittleSolReceived` (6003, lib.rs:1012 /
  sell_v2.rs:379).
  With real quote reserves equal to the gross quote (27,932,960) the sell
  succeeds and leaves 0 real quote reserves. One lamport less fails with
  `Overflow` (6024, lib.rs:1037).
- **Curve-state transitions in one transaction.**
  - After a buy that completes the curve, a following `buy` (lib.rs:608), `sell`
    (lib.rs:968), `buy_exact_sol_in` (buy.rs:53) or `buy_v2` (buy_v2.rs:345)
    fails with `BondingCurveComplete` (6005). The whole transaction rolls back
    (user delta −5,000, the transaction fee only).
  - With 1 real token left, `buy` of 2 fails with `NotEnoughTokensToBuy`
    (lib.rs:619). A partial-fill `buy` of 2 is clamped to 1 token (sol 1,
    fee 1, creator fee 1) and completes the curve.
  - After a sell that leaves 0 real quote reserves, the next `sell` fails with
    `NotEnoughTokensToSell` (6023, lib.rs:972).
  - Buy 10^9 then sell 10^9 in one transaction: the buy pays 27,960 + 266 + 84
    and the sell returns 27,959 − 266 − 84. The curve keeps +1 lamport and each
    fee recipient keeps 266 in total. Two consecutive buys of 10^9 cost 27,960
    each.
- **Cashback curves.** With byte 82 = 1, the creator fee (84 on a 10^9 buy) goes
  to the user-volume accumulator instead of the creator vault. The event
  `creator_fee` is 0. Protocol fees are unchanged. Legacy `sell` on a cashback
  curve needs the user-volume accumulator as the **first** remaining account.
  With the default remaining accounts (curve-v2, buyback) or with it last, sell
  fails with `InvalidCashbackAccumulator` (6073, sell.rs:33). With it first,
  sell succeeds, creates the accumulator and credits it 84 lamports above its
  1,844,400 rent. `sell_v2` takes it as a named
  account and succeeds.

## Files

- `producer.py`: case plan, fee stub generator, LiteSVM runner, report.
- `verify.py`: replays `runtime/plan.json.gz` on both images using only this
  folder and compares every receipt and the summary byte for byte.
- `runtime/plan.json.gz`: all 81 cases with their full initial account set.
- `runtime/receipts-upgradeable.jsonl.gz`: 162 receipts (81 cases × 2 images).
- `runtime/report.json.gz`: image sha256s, the per-case summary (decoded
  TradeEvent, curve after-state, lamport deltas, CU) and the aggregates above.

Images: original sha256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
(10,485,715 B), candidate sha256
`1cbf63aed735e3859e6019f297b946596ed54c9cb86cc32fedf7360d39ab81c6` (1,934,176 B).

## Reproduce

```
python3 producer.py --root <repo> --out . \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
python3 verify.py \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}'
```

Requires python3 and solders 0.27.1 (LiteSVM). No network. Two producer runs
give byte-identical `runtime/` files.

## Limits

- pump_fees is replaced by a fixed-answer stub, so pump_fees' own tier
  selection and its account checks are not exercised here.
- Only native-SOL curves. The token-quote v2 path, holder rewards and the
  cashback claim instructions are not covered.
- The cause of the extra 104 CU on `NotEnoughTokensToBuy` / `NotEnoughTokensToSell`
  and of the +1 CU on non-completing v2 buys was not located.
