# research: multi-hop split x boost buyback legs and route accounts under transfer fee

## Problem

3rd #78 pinned the `update_buyback_config` setter on the same
true-3-hop split x boost x tf chain (`three_amm` only, final output
U3): the bps ladder, the recipient membership gate, the setter
gates, and the bps-blind boost burn at 5000 vs 7500 after a buy.
This packet does not re-measure the setter ladder. It measures the
two buyback angles #78 left open: (a) buyback legs on trades that
follow a boost -- a main boost, hop boosts, and second buys -- and
(b) the buyback account passed in the route itself, which #78
explicitly did not test. On top of that it measures buyback legs at
huge/small sizes, the out-of-range config itself (bps 10001 patched
past the setter, so the trade rather than the setter is what fails),
and harvest/sweep of buyback accrual after a boost.

Fixture: buyback bps 5000, recipient list of 8 keys starting with
the fixture buyback owner, buyback destination BB22 (the owner's
Token-2022 ATA). tf100 unless noted. All amounts are for this
fixture; every case runs on original / control / candidate, 0
divergent cases.

## Cases

42 cases, 375 receipts (125 steps x 3 images), 38 parts
(37 x 10 + 5).

- A (4): anchors. Fresh buy leg 4,515,471 (withheld 45,611), tail
  5,262,910,281,902; fresh sell leg 837 (withheld 9), payout
  178,541; main boost burn 5,338,379,201,831; boost then buy.
- B (6): buyback ladder after a boost, bps set by the real setter:
  0 / 2500 / 7500 / 10000 then buy, boost then sell, boost then
  buy then buy.
- C (7): route buyback-account variants: non-owner Token-2022 ATA,
  payer's ATA, SPL ATA of the fixture owner, wrong-mint (base)
  Token-2022 ATA of the fixture owner, absent account; non-owner
  sell; failed buy then boost.
- D (4): hop boosts then trades: P2 boost then buy, P3 boost then
  buy, P2 boost then sell, main boost then P2 boost then buy.
- E (4): sizes: buy 10^12 quote, buy 10^6 quote, sell 10^12 base,
  sell 10^6 base.
- F (4): bps 10001 patched into GlobalConfig past the setter:
  buy, sell, boost, and a protocol sweep after the failed buy.
- G (5): setter mid-walk after a boost: 7500 then buy; buy, boost,
  7500, second buy; outsider setter then buy; excluded-owner
  setter then buy; None setter then boost then buy.
- H (5): harvest / sweep after a boost: boost, buy, protocol
  sweep; boost, buy, harvest, boost; buy, harvest, boost; boost,
  buy, creator sweep, collect; boost, buy, buy, protocol sweep.
- I (3): tf variants, boost first: tf0 buy, tf5000 buy, tf5000
  sell.

## Result

### The hop-1 quote credit is fixed; bps only moves the split

At 10^9 quote in, the hop-1 quote credit is exactly 9,122,164,
and the buyback leg (gross, net + withheld) and the protocol
accrual split it by bps:

| bps | buyback leg (net + withheld) | protocol accrual |
|----:|-----------------------------:|-----------------:|
| 0 | 0 | 9,122,164 |
| 2500 | 2,257,735 + 22,806 = 2,280,541 | 6,841,623 |
| 5000 | 4,515,471 + 45,611 = 4,561,082 | 4,561,082 |
| 7500 | 6,773,206 + 68,417 = 6,841,623 | 2,280,541 |
| 10000 | 9,030,942 + 91,222 = 9,122,164 | 0 |

At 10000 the buyback leg eats the entire credit and the protocol
bucket does not grow at all (pool fields after the buy: vq field
still the patched 10^9, protocol 2,488). The tail never moves with
bps: 5,139,964,404,268 after a boost at every bps, exactly as the
fresh-buy tail 5,262,910,281,902 never moves in #78.

### A prior boost leaves the buy leg identical but moves the sell leg

- Boost then buy: leg 4,515,471, withheld 45,611 -- byte-identical
  to the fresh buy. Boost then buy then buy: the second leg is
  again 4,515,471. The buy leg is per-trade and boost-invariant.
- Boost then sell: leg 858 (withheld 9), payout 182,879 -- the
  fresh sell leg is 837, payout 178,541. The sell leg is
  boost-sensitive (+21) because the sell's hop-1 credit moves with
  the vaults (fresh credit 1,693, post-boost credit 1,735), while
  the buy's hop-1 credit does not.
- Setter walks after a boost agree: boost, setter 7500, buy pays
  6,773,206; buy, boost, setter 7500, second buy pays 6,773,206.
  Outsider setter fails 6005 and the following buy is anchor.
  Excluded-owner setter succeeds and the following buy fails
  6053. A None setter is a silent no-op and the boost-then-buy
  leg is anchor.

### The route buyback account gates by program, mint, then owner

- Non-owner Token-2022 ATA: buy fails 6053, 0 events. Payer's own
  Token-2022 ATA: buy fails 6053. The gate is owner membership in
  the recipient list, not the account address: any owner's ATA
  outside the list fails the same way #78's excluded-list buy did.
- SPL ATA of the fixture owner: buy fails 6027. Absent account:
  buy fails 6027, not 3012 -- the program/token-program check fires
  before existence is ever consulted.
- Wrong-mint Token-2022 ATA (base mint, fixture owner): buy fails
  6009.
- Non-owner sell fails 6053 with 2 ghost hop events (sell runs
  p3 -> p2 -> main, so two hops execute before the failing hop).
- A failed route-account buy leaves no residue: the following
  patched boost burns the anchor 5,338,379,201,831.

### Hop boosts do not move the buyback leg on either side

- P2 boost then buy: leg 4,515,471, tail 5,262,894,631,186 (the
  #111 P2-boost-then-buy tail). P3 boost then buy: leg 4,515,471,
  tail 5,262,894,547,951 (a different tail move than P2's, same
  leg). Main boost then P2 boost then buy: leg 4,515,471.
- P2 boost then sell: leg 837, payout 178,542 (the #111 +1, from
  the boost, not the leg).

### Size ladder: the leg scales, the small sell rounds to zero

- Buy 10^12 quote: leg 4,515,471,118, withheld 45,610,820, tail
  271,955,112,938,539. Buy 10^6 quote: leg 4,515, withheld 46,
  tail 5,361,291,543.
- Sell 10^12 base: leg 835,113, withheld 8,436, payout
  177,923,993. Sell 10^6 base: leg net 0 with 1 withheld, payout
  178 -- the 1-unit hop-1 credit goes entirely to withholding.

### Bps 10001 past the setter: the buy panics, the sell caps, the boost does not care

- Buy at patched bps 10001: `ProgramFailedToComplete` (a panic,
  0 events), full rollback; restoring bps to 5000 returns the
  anchor leg 4,515,471.
- Sell at patched bps 10001: succeeds with leg 1,676 (withheld
  17), payout 178,541 -- exactly the 10000-bps sell leg from #78,
  as if the sell path capped bps at 10000 while the buy path
  panicked on it. This buy/sell asymmetry is measured, not
  explained: the receipts pin the two behaviours, not the reason.
- Boost at patched bps 10001: burns the anchor 5,338,379,201,831.
  The boost never reads buyback bps.
- Protocol sweep after the panicked buy discharges only the
  fixture 2,488 (vq field -125,882 -> -123,394, bucket -> 0):
  the failed buy left nothing behind.

### Harvest and sweep after a boost

- Boost, buy, protocol sweep discharges the full 4,563,570
  (bucket -> 0, vq field up by exactly the swept bucket, the #112
  window conservation). Boost, buy, buy, sweep discharges the
  cumulative 9,124,652.
- Harvest after a buy clears BB22 withheld (-45,611) and leaves
  the BB22 balance unchanged; the next patched boost burns
  5,173,028,765,024 (the #112 boost-buy-boost value) with harvest,
  and 5,254,679,949,141 without it -- harvest moves nothing the
  burn reads.
- Boost, buy, creator sweep, collect: the creator sweep drains
  the 123,394 bucket and the following collect is a 0-event
  no-op (nothing left to collect).

### tf variants, boost first

- tf0 boost then buy: leg 4,607,153, no withholding, tail
  5,190,120,300,217; tf0 boost burn 5,391,870,655,895 (the #109
  tf0 anchor).
- tf5000 boost then buy: leg 1,151,788 + withheld 1,151,789 (a
  50/50 split), tail 2,639,797,163,464; tf5000 boost burn
  2,706,767,012,738.
- tf5000 boost then sell: leg 430 + withheld 430, payout 91,641.

## Limits

- `cpatch` steps are harness field resets (pool vq patched to
  10^9 so a boost window exists; GlobalConfig bps patched to
  10001 past the setter's cap), never instructions; they carry
  empty transactions by design.
- The sell-at-10001 behaviour is reported as measured (leg
  identical to the 10000 leg); whether the sell path clamps, the
  buyback fee formula saturates, or another mechanism applies is
  not pinned by these receipts.
- The route-account cases pass the variant account as the
  multi-hop instruction's buyback account only; other
  instructions' buyback-account handling is not measured here.
- No source change is proposed. No claim is made about the
  program beyond the measured legs above.

Made via @slopdotcash
