# research: multi-hop split x boost exact-out chains under transfer fee

## Problem

The brief for this packet called `buy_exact` the "exact base-out" leg.
That is wrong, and the packet exists in part to pin the correction
from the program itself (`programs/pump-amm/src/lib.rs:191-200`):

- `buy` / `buy_v2` take `(base_amount_out, max_quote_amount_in)`:
  these ARE the exact-out legs.
- `buy_exact_quote_in` / `buy_exact_quote_in_v2` take
  `(spendable_quote_in, min_base_amount_out)`: these are exact-IN
  legs, not exact-out.
- `sell` / `sell_v2` take `(base_amount_in, min_quote_amount_out)`:
  exact base-in with a minimum-quote gate. There is NO exact-quote-out
  sell instruction, so the sell-side analogue measured here is a
  tight `min_quote_amount_out` gate.
- `multi_hop_swap` takes `(amount_in, min_amount_out)`: exact-in
  with a slippage gate, so the chain analogue is a tight `min_out`
  gate.

On the same true-3-hop split x boost x tf chain as packets
#64-#107 (`three_amm` only, final output U3), this packet measures
both exact families, their gates, their round trip, and their
placement before / after / between chain legs (multi-hop buy/sell,
boost, sweep, collect, deposit). All amounts are for this fixture
(fee table, pool reserves, tf100 unless noted); the first trade of
a case costs the payer 1,849,400 lamports (fee 5,000 + UVA rent
1,844,400 for the auto-created user volume accumulator).

## Cases

59 cases, 270 receipts (59 cases x steps x 3 images), 27 parts
of 10 receipts. 0 divergent cases across original / control /
candidate.

- A (9): exact-out anchors, single hop on the main pool.
  `legbuy` / `buy2m` (buy_v2 with a custom max) at base_out
  10^6 / 10^8 / 10^9, repeated, tf0 / tf100 / tf5000.
- B (8): exact-in anchors. `lexact` / `bexact2` at spendable
  10^6 / 10^8 / 10^9, repeated, tf5000.
- C (4): exact-out `max_quote` gates, one below / exactly at the
  required input.
- D (4): exact-in `min_base` gates, exactly at / one above the
  attainable output.
- E (4): round trip: the exact-out cost spent as exact-in,
  tf100 and tf0.
- F (6): sell-side tight `min_quote` gates, tf100 / tf5000.
- G (6): multi-hop tight `min_amount_out` gates (buy, sell,
  plain), exact / +1.
- H (6): exact legs between chain legs (mh -> exact -> mh,
  mhsell -> exact sell).
- I (5): exact legs around a boost (exact -> boost, boost ->
  exact, mh -> boost reference).
- J (5): sweep / collect / deposit after exact legs (legacy vs
  v2 bucket behaviour).
- K (2): failed exact legs followed by a chain buy (rollback
  isolation).

## Result

### Exact-out vs exact-in anchors (tf100, base_out 10^9 / spend 10^9)

- Legacy exact-out costs 186,623 quote (curve quote 182,533;
  withheld vq1 1,844, bb22/proto22/creat22 fees 840/840/542,
  withheld 9/9/6). V2 exact-out costs 186,637 (+14 vs legacy;
  vq1 +183,930, withheld vq1 1,858): same base out, different
  quote-side routing.
- Legacy exact-in spends 999,878,519 quote for base
  5,315,544,542,190. V2 exact-in yields the identical base but
  spends 999,954,075 (+75,556 vs legacy): the base curve is
  shared, the quote routing is not.
- Small sizes agree on base too: 10^6 spend -> base
  5,357,760,549 for both legacy and v2; 10^8 spend (v2) ->
  535,356,061,229. Second v2 exact-in decays to
  5,232,312,441,616 (-1.56%, same decay family as #91/#100).
- tf0: both exact-out legs cost 184,779. tf5000: legacy
  367,312 (withheld vq1 = the full curve quote 182,533),
  v2 368,709; exact-in base at tf5000 is 2,695,143,552,032 for
  both, but legacy spends 993,925,925 vs v2 997,703,704
  (legacy cheaper by 3,777,779).
- Repeated exact-out dust: the second legbuy costs 186,624,
  exactly +1 over the first.

### The gates split by leg family, and every boundary is sharp at +-1

- Exact-out `max_quote` breached by 1 -> 6004 ExceededSlippage,
  0 events (legacy buy.rs:405, v2 trade_v2.rs:706). Exactly at
  the required input -> success (186,623 legacy, 186,637 v2).
- Exact-in `min_base` exceeded by 1 -> 6040
  BuySlippageBelowMinBaseAmountOut, 0 events (legacy buy.rs:776,
  v2 trade_v2.rs:816). Exactly at the attainable base ->
  success (5,315,544,542,190).
- Sell `min_quote` exceeded by 1 -> 6004, 0 events (legacy
  sell.rs:189, v2 trade_v2.rs:906). Payouts are identical
  legacy/v2: 178,409 at tf100 (gross 180,212 = net 178,409 +
  withheld 1,803); at tf5000 net 90,106 with withheld 90,106
  (same gross 180,212, only the split moves).
- Multi-hop `min_out` exceeded by 1 -> 6004 at
  multi_hop_swap.rs:389 with all 3 hop events left as ghosts:
  buy tail 5,262,910,281,902, sell payout 178,541, plain buy
  tail 5,315,084,721,958, each exact at the boundary.

### The round trip is not a round trip, even at tf0

- Legacy exact-out cost 186,623 spent as exact-in yields only
  999,869,711 base: shortfall 130,289 against the 10^9 target.
- V2 exact-out cost 186,637 spent as exact-in yields
  999,946,425: shortfall 53,575.
- At tf0 the same quote (184,779) spent as exact-in yields
  999,995,741 for both legacy and v2: shortfall 4,259 with
  zero transfer fee. The exact-out leg prices the target and
  charges fees on top; the exact-in leg re-fees the input
  before the curve sees it, so the same quote always buys
  slightly less base, and the tf withheld on the input side
  widens the gap at tf100.

### Chain interaction: exact legs move the next tail and the next burn

- Plain second chain buy tails 5,072,980,706,277. With a
  legbuy in between (cost 189,614, +2,991 vs fresh, because
  the chain already drained vb1), the second tail is
  5,072,965,739,290 (-14,966,987).
- With an exact-in leg in between, the second tail is
  4,994,963,371,566 for BOTH legacy and v2 exact-in: the
  quote-side routing difference does not reach chain price,
  because both drain the same base from vb1.
- After a chain sell, an exact sell pays 178,408 (1 less than
  the fresh 178,409), legacy and v2 alike.
- Exact leg then boost (vq patched to 10^9): legbuy -> burn
  5,338,363,478,447 (anchor 5,338,379,201,831, -15,723,384);
  bexact2 -> burn 5,254,810,797,338; chain buy -> burn
  5,254,679,949,141 (the #105 post-buy burn, reproduced).
- Boost then exact leg: legbuy costs 191,159 (+4,536 vs
  fresh); bexact2 yields 5,190,075,630,656 (vs fresh
  5,315,544,542,190). The burn moves the trade through the
  vaults, exactly as in #102.

### Legacy pays fees out; v2 accrues them into the pool buckets

- After a legacy exact-out buy, protocol sweep pays only the
  fixture 2,488 (-> net 2,463) and creator sweep only the
  fixture 123,394 (-> net 122,160): the legbuy fees
  (840/840/542) went straight to recipient ATAs, never into
  the pool buckets.
- After a v2 exact-in buy, protocol sweep pays 4,549,155
  (= fixture 2,488 + accrual 4,546,667) -> net 4,503,663,
  and creator sweep pays 3,056,728 (= 123,394 + 2,933,334)
  -> net 3,026,160.
- Collect after legbuy + creator sweep drains 122,702
  (= 542 direct creator fee + 122,160 swept) -> dest net
  121,474 + withheld 1,228.
- Deposit after exact legs moves with the drained vaults:
  after bexact2, base -159,352,586 / quote -29,845; after
  legbuy, base -160,619,657 / quote -29,610 (vs the plain
  deposit anchor base 160,619,895 / quote 29,610).

### Failed exact legs leave no residue

- Failed legbuy (6004, max 186,622) followed by a chain buy
  tails exactly 5,262,910,281,902. Failed bexact2 (6040,
  min base +1) followed by a chain buy tails exactly the
  same. Both failure modes roll back completely.

## Limits

- `cpatch` steps are harness field resets (pool vq patched to
  10^9 so a boost window exists), never instructions; they
  carry empty transactions by design.
- In this harness, single-hop legacy/v2 legs force the
  Token-2022 quote path, so plain single-hop exact legs fail
  with IncorrectProgramId (0 events); plain cases here use
  multi-hop legs only, which succeed on plain mints.
- There is no exact-quote-out sell instruction in the program;
  the sell side is measured through tight min_quote gates.
- Error-site lines are image-specific (original vs rebuild
  line numbers differ), so verify.py asserts error codes,
  event counts, deltas and rollback, not site lines.
- 6088 (boost ATA shortfall) is not retriggered here; its pin
  stays with #100. The tf epoch schedule is not re-measured
  here; #106 covers it on the same chain.
- No source change is proposed. No claim is made about the
  program beyond the measured legs above.

Made via @slopdotcash
