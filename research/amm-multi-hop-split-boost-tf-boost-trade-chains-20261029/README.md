# research: multi-hop split x boost trade-interaction chains under transfer fee

## Problem

#100 pinned the boost burn as a function of the pool state (window,
vq field, vaults, tf, request size) and #101 pinned the boost
gates, but neither measured the two-way coupling: does a boost
move the next trade's price, and does a trade move the next
boost's burn, in the same walk? This packet closes that loop on
the same true-3-hop split x boost x tf chain (three_amm only,
final output U3): boost-then-trade, trade-then-boost, alternating
legs, failed legs, and the boost's effect on the fee-bucket,
buyback, sweep, collect, and claim legs.

## Setup

- Route: three_amm (main -> pool2 -> pool3), split legs, tf
  override bps 100 unless a case says otherwise (tf0 / tf5000
  cases use bps 0 / 5000). All boosts are on the main pool
  except the `boost3` tail-pool cases.
- Boost anchor (vq patched to 10^9, tf100, request 10^9): used
  10^9, burned 5,338,379,201,831, quote_after 123,936,690,720,
  base_after 668,358,016,710,914, remaining 999,000,000,000.
- Fresh baselines on the same chain: buy (10^9 quote) tails
  5,262,910,281,902 with no vq patch and 5,221,217,806,636 with
  vq patched to 10^9; sell (10^9 base) pays 178,541 with no
  patch and 179,993 with the patch; first-trade payer cost
  -1,849,400 (fee 5,000 + UVA rent 1,844,400), later trades
  -5,000.
- 121 cases, 1005 receipts, 101 parts (100x10 + 5), 0
  divergent cases across original / control / candidate.
  Every number below is measured on this chain, not copied
  from earlier packets (where a value repeats an earlier
  packet's anchor, it is called out as a reproduction).

## Cases

- `z-*` (5): baselines. Anchor boost, fresh buy/sell with and
  without the vq patch.
- `a-*` (15): boost -> trade. Buy, sell, buy-buy, sell-sell,
  buy-sell, sell-buy, double boost then buy, v2 buy/sell,
  legacy buy/sell, deposit, withdraw, small buy (10^6 quote),
  small sell (10^6 base).
- `b-*` (16): trade -> boost. Buy, sell, buy-buy, sell-sell,
  buy-sell, sell-buy, v2 buy/sell, legacy buy/sell, deposit,
  withdraw, deposit-withdraw, buy-sweep, buy-sweep-collect,
  sell-sweep.
- `c-*` (25): alternating and failed legs. buy-boost-buy-boost
  (and the 5-step extension), boost-sell-boost,
  boost-buy-boost-buy, buy-boost-sell-boost,
  boost-boost-buy-boost, sell-boost-buy, failed boost (6005)
  then sell, failed buy (6004) then boost, failed boost then
  boost, window-zero boost-buy-boost, failed buy/sell (6004)
  after a boost then boost, boost-buy-boost-boost,
  boost-sell-boost-buy, buy-sell-boost-sell,
  sell-buy-boost-buy, boost-deposit-boost,
  deposit-boost-buy, withdraw-boost-sell,
  buy-boost-deposit-boost, sell-boost-sweep-boost,
  boost-sweep-boost-buy, boost-off toggle then restore then
  boost then buy, buy-disable then release then boost then
  buy.
- `d-*` (10): boost x buckets/buyback/sweep. Buy buckets with
  and without a preceding boost, sweep after boost, sweep
  after buy-boost, sweep-collect after buy-boost, sweep after
  boost-buy, buyback-bps 7500 then boost-buy and buy-boost,
  sweep after boost-buy-buy, sweep after sell-boost.
- `e-*` (11): boost x claims. Token claim and cashback claim
  before/after a boost, buy-boost then token claim,
  boost-buy then token/cashback claim, sell-boost then token
  claim, boost-claim-boost for both claim kinds,
  boost-buy-boost then token claim.
- `f-*` (15): tf variants. tf0/tf5000 boost then buy/sell,
  buy/sell then tf5000 boost, tf0 boost-boost, tf0 buy then
  boost, tf5000 boost-buy-boost, tf5000 sell-boost-sell,
  tf5000 v2 buy both directions, tf0 boost-buy-boost,
  tf5000 boost-sell-boost, tf5000 boost then sweep.
- `g-*` (10): boost size x trade. 10^6 and 10^10 boosts then
  buy/sell, buy/sell after an anchor boost at 10^6 size,
  10^8 boost then buy, buy/sell then small/big boost,
  boost-buy then a 10^6 boost.
- `h-*` (10): boost x deposit/withdraw and tail boosts.
  Boost-deposit-withdraw-boost, deposit-boost-withdraw-boost,
  boost-withdraw-boost-buy, boost-buy-withdraw-boost,
  boost-buy-deposit-boost, buy-boost-withdraw-buy,
  boost-boost-deposit-boost, and tail-pool boost (boost3)
  after a boost, after a buy, and after boost-buy.
- `i-*` (4): outsider-signed boost in the walk.
  Outsider boost then buy, buy then outsider boost,
  outsider boost then buy then payer boost, buy then
  outsider boost then buy.

## Result

### 1. A boost moves the next trade through the vaults

The boost burns base out of vault vb1, so the next trade
walks a smaller vault:

- Buy (10^9 quote) after the anchor boost tails
  5,139,964,404,268, vs 5,221,217,806,636 with no boost
  (-81,253,402,368, -1.56%). After two boosts it tails
  5,060,586,700,476.
- Sell (10^9 base) after the anchor boost pays 182,879, vs
  179,993 with no boost (+2,886).
- The second buy in a boost-buy-buy walk tails
  4,958,122,565,416, vs 5,034,258,806,956 for a buy-buy walk
  with no boost (-76,136,241,540). The second sell in a
  boost-sell-sell walk pays 182,878, vs 179,992 for
  sell-sell (+2,886 -- the same edge as the first sell:
  each sell refills the vault by the same base, so the
  boost's edge persists unchanged into the second sell).
- Cross-direction: buy after boost-sell tails
  5,139,999,948,043; sell after boost-buy pays 189,649
  (vs 186,740 for buy-sell with no boost).
- Small legs move too: a 10^6-quote buy after the boost
  tails 5,234,086,896; a 10^6-base sell after the boost pays
  182. v2 buy after the boost pays -193 quote (vs -190
  with no boost); v2 sell after the boost pays 180 (vs
  177); legacy buy/sell after the boost match v2 exactly
  (-193 / 180).
- Deposit after the boost costs -29,848 quote (vs -29,610
  with no boost); withdraw after the boost pays 29,252
  (vs 29,018). Deposit after buy-boost costs -30,084;
  withdraw after buy-boost pays 29,484; deposit after two
  boosts costs -30,086.

The buy-tail shift is near-proportional to the burn at
small and anchor sizes and saturates slightly at 10^10:

- 10^6 boost (burn 5,380,970,054) -> buy tails
  5,221,135,596,803, a shift of -82,209,833 (1.53% of the
  burn).
- 10^8 boost (burn 537,672,386,159) -> buy tails
  5,213,006,386,660, a shift of -8,211,419,976 (1.53%).
- 10^9 anchor boost (burn 5,338,379,201,831) -> shift
  -81,253,402,368 (1.52%).
- 10^10 boost (burn 49,830,102,507,836) -> buy tails
  4,486,666,452,043, a shift of -734,551,354,593 (1.47%).

The sell side is strongly nonlinear in boost size: a 10^6
boost moves the sell by only +3 (179,996), while a 10^10
boost moves it by +29,901 (209,894, +16.6%).

### 2. A trade moves the next burn the same way

- Buy then boost burns 5,255,205,915,165 (reproduces #100 /
  #99 exactly). Sell then boost burns 5,338,394,947,565
  (reproduces #100 exactly).
- Buy-buy then boost burns 5,173,961,394,349 (second buy
  tails 5,034,258,806,956). Sell-sell then boost burns
  5,338,410,693,271 (second sell pays 179,992).
- Buy-sell then boost burns 5,255,221,870,808 (the sell
  after a buy pays 186,740); sell-buy then boost burns
  5,255,221,294,351 (the buy after a sell tails
  5,221,253,785,885). The two round trips land within
  576,457 of each other but not on each other: the walk
  is path-dependent at the 10^5 scale.
- v2 buy then boost burns 5,338,379,186,002 (anchor
  -15,829, reproduces #100); legacy buy then boost is
  identical. v2 sell then boost burns 5,338,379,217,531
  (anchor +15,700); legacy sell then boost is identical.
- Deposit then boost burns 5,338,379,211,910 (anchor
  +10,079, reproduces #100); withdraw then boost burns
  5,338,379,191,752 (anchor -10,079); deposit-withdraw
  then boost burns the anchor exactly.
- Buy then a 10^6 boost burns 5,296,803,957 (vs a 10^6
  boost alone at 5,380,970,054, -1.56% -- the same decay
  rate as the anchor ladder). Sell then a 10^10 boost
  burns 49,830,244,610,915 (vs 49,830,102,507,836 alone,
  +142,103,079). Boost-buy then a 10^6 boost burns
  5,213,841,726.

### 3. Alternating legs decay together, and failed legs leave nothing

- buy-boost-buy-boost: tails 5,221,217,806,636 then
  4,956,499,821,134; burns 5,255,205,915,165 then
  5,093,856,866,968. The 5-step extension adds a third
  buy at 4,711,416,228,510.
- boost-buy-boost-buy: burns 5,338,379,201,831 then
  5,173,214,684,656; final buy tails 4,882,120,715,494.
  boost-boost-buy-boost: burns 5,338,379,201,831 then
  5,254,441,549,265, buy tails 5,060,586,700,476, final
  boost burns 5,093,127,430,565.
- boost-sell-boost: sell pays 182,879, next boost burns
  5,254,457,171,685. buy-boost-sell-boost: sell pays
  189,711, next boost burns 5,173,230,516,292.
  sell-boost-buy: buy tails 5,139,999,709,298.
- Failed boost (6005) then sell pays the fresh 179,993.
  Failed buy (6004, min-out 10^15) then boost burns the
  anchor. Failed boost then boost burns the anchor.
  Failed buy or sell (6004) after a boost, then a boost,
  burns the second-boost value 5,254,441,549,265 -- exactly
  as if the failed trade never happened.
- Window-zero chain: boost fails 6065, buy tails the
  fresh 5,262,910,281,902, next boost still fails 6065
  (#92's window invariant, in interaction form).
- Boost-off toggle (6066) then restore, then boost, burns
  the second-boost value; buy-disable (6020) then release,
  then boost, burns the second-boost value; the following
  buys tail 5,060,586,700,476 in both cases.
- Sweep between two boosts changes nothing: boost-sweep-
  boost burns 5,254,441,549,265, the plain second-boost
  value.

### 4. The boost moves no fee book: accrual, buyback, sweep, collect are boost-blind

- The buy's hop-1 protocol accrual is 4,561,082 and its
  buyback leg is gross 4,561,082 / net 4,515,471 whether
  or not a boost ran first: the accrual is charged on the
  quote input, which the boost does not touch, while the
  output tail moves by -81,253,402,368. The buyback-bps
  setter (7500) likewise moves neither the boost nor the
  buy that follows it.
- Sweep after a boost pays the fixture protocol bucket
  2,488 (net 2,463 at tf100, net 1,244 at tf5000); sweep
  after buy-boost pays the buy's bucket; creator sweep
  after buy-boost pays 123,394 (net 122,160) and collect
  pays 120,938 -- all identical to the no-boost values
  from #99.
- Sweep/collect/claim move no later burn: buy-sweep-boost
  and buy-sweep-sweep-collect-boost both burn
  5,255,205,915,165, the plain buy-then-boost value
  (#100's sweep-neutrality, extended to the full
  sweep-collect chain).

### 5. Claims: token claims are boost-blind, cashback claims fail 2021 everywhere

- Token claim pays 3,334,551 before a boost, after a
  boost, after buy-boost, after sell-boost, and after
  boost-buy-boost. A boost after a token claim burns the
  second-boost value 5,254,441,549,265.
- Cashback claim under the transfer-fee override fails
  2021 in every position: after a boost, before a boost,
  and after boost-buy. The failed claim moves no later
  burn (boost after a failed cashback claim burns the
  second-boost value). This reproduces #67's constraint
  (the tf-override quote mint is not a plain token
  account for the cashback claim) inside the walk; it is
  not a new claim failure, it is the interaction pin that
  a boost neither rescues nor changes it.

### 6. Transfer fee scales both legs, and the tail pool stays shut

- tf0: boost 5,391,870,655,895, buy after it tails
  5,190,120,300,217 (vs tf0 buy alone 5,272,986,673,608);
  second tf0 boost 5,306,249,181,882; tf0 boost-buy-boost
  burns 5,223,412,367,287; tf0 sell after boost pays
  184,757.
- tf5000: boost 2,706,767,012,738, buy after it tails
  2,639,797,163,464 (vs tf5000 buy alone
  2,660,981,910,591); buy then tf5000 boost burns
  2,685,302,061,999; sell after tf5000 boost pays 91,641
  (vs 90,906 alone); sell then tf5000 boost burns
  2,706,775,012,096; tf5000 boost-buy-boost burns
  2,663,895,353,955; tf5000 boost-sell-boost burns
  2,685,111,605,206.
- tf5000 v2 buy after a boost pays -379 quote (vs -190
  at tf100); v2 buy then tf5000 boost burns
  2,706,767,004,697 (anchor -8,041, vs -15,829 at tf100:
  the small-trade burn shift is itself tf-dependent).
- Tail-pool boost (boost3) fails 6065 after a boost,
  after a buy, and after boost-buy: the tail window stays
  0 through the whole walk (#100 reproduced in three
  positions).

### 7. The vq field is a trade input, not just a burn input

Patching vq to 10^9 with no boost at all moves the buy
tail from 5,262,910,281,902 to 5,221,217,806,636
(-41,692,475,266) and the sell payout from 178,541 to
179,993 (+1,452). #98's "hop prices follow the real vault
balances" is therefore incomplete as stated: the vq field
enters hop-1 pricing too, at a two-point secant of about
-41.69 per unit on the buy tail at fixture vaults (vs
-42.73 per unit on the burn from #100 -- same curve
family, different evaluation point).

### 8. Withdraw is state-dependent: a deposit-withdraw pair straddling a boost leaves residue

- Withdraw alone removes 160,619,895 base; withdraw after
  a boost removes 159,347,141 base -- 1,272,754 less,
  because the withdraw takes an LP fraction of the vault
  the boost just shrank.
- Deposit-withdraw before a boost burns the anchor
  exactly; deposit-boost-withdraw-boost burns
  5,254,441,569,039, which is +19,774 above the plain
  second-boost value -- the residue of the straddled pair.
- Withdraw between two boosts lowers the second boost by
  9,844 (5,254,441,539,421) and the buy after it by
  27,932 (5,060,586,672,544 vs 5,060,586,700,476).
- Deposit/withdraw after buy-boost move the next boost by
  +9,611 / -9,611 (5,173,214,694,267 /
  5,173,214,675,045 vs 5,173,214,684,656); deposit after
  two boosts moves the third boost by +9,616
  (5,172,468,146,217 vs 5,172,468,136,601). The #100
  deposit +10,079 pattern holds to within ~500 after a
  trade has moved the vaults.

### 9. Outsider-signed boosts are walk-identical

Outsider boost then buy tails 5,139,964,404,268; buy
then outsider boost burns 5,255,205,915,165; outsider
boost then buy then payer boost burns 5,173,214,684,656;
buy then outsider boost then buy tails 4,956,499,821,134
-- all exactly the payer-signed values (#101's
signer-blindness, extended to the whole walk).

## Limits

- All boosts run under the transfer-fee override; no
  plain-mint boost case exists here (same limit as #100).
  Plain-quote cashback claims are not measured in this
  packet: the claim side is pinned for token claims and
  for the tf-override cashback 2021 failure only.
- The vq-field trade slope is a two-point secant (fresh
  vs 10^9), not a ladder; the buy-tail slope at other
  vq values is not measured here.
- The buyback leg is measured at hop-1 / the main pool;
  tail-pool creator accrual is not isolated here.
- The 10^9--10^12 bucket boundary is inherited from #99
  and not re-measured here.
- The walk is measured on the fixture vaults (vb1
  4,194,352,106,721 base, vq1 vault at the fixture
  level); the 1.52% buy-shift ratio is a fixture-vault
  number, and the 10^10 saturation point (1.47%) shows it
  is not a constant.
- No source change is proposed and no full-program
  equivalence is claimed. All amounts are receipt-level
  measurements on the original, control, and candidate
  images; the three images agree on every surface in
  every case (0 divergent).

Made via @slopdotcash
