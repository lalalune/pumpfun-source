# research: split x boost x tf boost and trade interaction chains at TRUE 5 hops

## Problem

Packet #102 pinned how boosts and trades interact on a 3-hop split chain:
a boost before a trade lowers the buy tail, a trade before a boost changes
the burn, and the order of the two operations matters. This packet re-measures
every one of those interaction families on a TRUE 5-hop split x boost x tf
chain (three_amm + g4 + g5, final output U5, five hop events on every
successful swap), so the depth-5 interaction numbers stand on their own
receipts instead of being extrapolated from depth 3.

## Cases

119 cases, 963 receipts, 97 parts (96 x 10 + 3). All amounts are measured
on the original, control, and candidate program images; the three images
agree on every step (0 divergent cases). Boosts request 10^9 quote unless
a family says otherwise; the main pool virtual_quote_reserves field is
patched to 10^9 wherever a boost must succeed; transfer fee is 100 bps
unless a family says otherwise. First-trade payer cost is -1,849,400
(fee 5,000 + UVA rent 1,844,400); later steps cost -5,000 each.

- z baselines: anchor boost, fresh and patched buys and sells, buy-buy,
  sell-sell, buy-sell, sell-buy.
- a boost-then-trade: boost before buy, sell, buy-buy, sell-sell,
  buy-sell, sell-buy, double boost then buy, v2 buy/sell, legacy
  buy/sell, deposit, withdraw, small buy (10^6 quote), small sell
  (10^6 base).
- b trade-then-boost: buy, sell, buy-buy, sell-sell, buy-sell,
  sell-buy, v2 buy/sell, legacy buy/sell, deposit, withdraw,
  deposit-withdraw, buy-sweep, buy-sweep-collect, sell-sweep, each
  followed by a boost.
- c alternating and failed legs: buy-boost-buy-boost(-buy),
  boost-sell-boost, boost-buy-boost-buy, buy-boost-sell-boost,
  double-boost-buy-boost, sell-boost-buy, outsider-signed boost
  then sell, failing buy then boost, failed boost then boost,
  window-0 boost then buy then patched boost, failing sell then
  boost, boost-failing-sell-boost, boost-failing-buy-boost,
  boost-deposit-boost, deposit-boost-buy, withdraw-boost-sell,
  buy-boost-deposit-boost, sell-boost-sweep-boost,
  boost-sweep-boost-buy, boost-off-boost-buy, buy-disabled
  boost-buy.
- d boost x buckets and sweeps: sweep/collect after buy, after
  boost-then-buy, after buy-then-boost, after a boost alone, after
  buy-boost, after boost-buy, after sell-boost, after boost-sell,
  after buy-boost-buy.
- e boost x claims: seeded token claim before a boost, after a
  boost, after buy-boost, after boost-buy, after sell-boost, and
  between two boosts; plain-mode cashback claim (5,475 funded)
  before a boost, after a boost, after boost-buy, and between two
  boosts (plain cases use the no_ww guard).
- f transfer-fee variants: boost-then-trade and trade-then-boost
  at tf0 and tf5000, double boosts at tf0, boost-buy-boost and
  sell-boost-sell at tf5000, v2-buy-boost at tf5000, boost-sweep
  at tf5000.
- g boost size x trade: 10^6, 10^8, and 10^10 boosts before buys
  and sells, and 10^6 / 10^10 boosts after buys.
- h boost x deposit/withdraw and terminal-hop boosts: boost-dep-wd
  -boost, dep-boost-wd-boost, boost-wd-boost-buy, boost-buy-wd
  -boost, boost-buy-dep-boost, buy-boost-wd-buy,
  boost-boost-dep-boost, P5 boost then buy, buy then P5 boost,
  main boost then P5 boost, P5 boost then main boost, P5
  boost-buy-P5 boost (P5 window patched to 10^9, SPL-derived BA5S).
- i outsider-signed boost in the walk: outsider boost then buy,
  buy then outsider boost, outsider boost then buy then payer
  boost, buy then outsider boost then buy.

## Result

Baselines (tf100): fresh 5-hop buy tail 5,207,955,235,891; vq-patched
buy tail 5,167,125,538,753; sell payout 178,541 unpatched and 179,993
patched; anchor boost burn 5,338,379,201,831 (identical to the
#100/#154/#155 anchor). Every successful multi-hop swap emits exactly
5 hop events.

Boost-then-trade: boost then buy pays 5,087,534,167,771, which is
79,591,370,982 (-1.54%) below the patched buy tail -- the same
direction and nearly the same size as the -1.56% measured at depth 3
in #102. A second boost then buy pays 5,009,755,337,763. Boost then
sell pays 182,879, ABOVE the patched 179,993: the sell leg is
boost-sensitive in the opposite direction from the buy leg. A small
buy (10^6 quote) after a boost pays 5,234,031,967; a small sell
(10^6 base) after a boost pays 182.

Trade-then-boost: buy then boost burns 5,255,205,915,165; sell then
boost burns 5,338,394,947,549; two buys then boost burns
5,173,961,394,349; two sells then boost burns 5,338,410,693,165.
A v2 buy then boost burns 5,338,379,186,002 and a v2 sell then boost
burns 5,338,379,217,531 -- v2 legs leave the anchor burn essentially
unchanged, while multi-hop legs move it.

Ordering matters, not just the multiset of legs. Buy-boost-buy-boost
-buy ends at tail 4,483,355,941,890 (legs: buy 5,167,125,538,753,
boost 5,255,205,915,165, buy 4,807,055,742,256, boost
5,093,856,866,968, buy 4,483,355,941,890), while
boost-buy-boost-buy ends at 4,737,131,390,020 (boost
5,338,379,201,831, buy 5,087,534,167,771, boost 5,173,214,684,656,
buy 4,737,131,390,020). A buy-boost-sell leg pays 193,704, versus
179,993 for a plain patched sell and 182,879 for boost-then-sell.
A sell-boost-buy leg pays 5,087,588,952,459, which is 54,784,688
above the boost-then-buy tail -- the sell leg leaves a residue
the next buy still feels.

Failed legs roll back cleanly and never poison the next leg. A
failing 5-hop buy panics (ProgramFailedToComplete, 5 ghost events)
and the next boost still burns the anchor 5,338,379,201,831. A
failing sell is clean 6004 and the next boost still burns the
anchor. A window-0 boost fails 6065, then a fresh buy pays
5,207,955,235,891, then a patched boost burns 5,254,679,949,141
(525,966,024 below the patched-buy-then-boost value -- the burn
depends on which buy path opened the window). A buy-disabled boost
fails 6020, a toggled-off boost fails 6066, and an outsider-signed
boost fails 6005; after re-enabling, the boost and the following
buy pay exactly the anchor and boost-then-buy values. An
outsider-signed boost leaves the next buy tail at exactly the
patched 5,167,125,538,753.

Boosts are fee-book neutral. Sweep after buy, after boost-then-buy,
and after buy-then-boost all sweep exactly 4,517,934 protocol and
122,160 creator, and collect pays the same 122,160. Sweep after a
boost alone is 2,463 (fixture buckets only). Sweep after sell+boost
is 3,308 versus 3,322 after boost+sell -- a 14-unit residue that
records which leg ran first. Sweep or collect before a boost never
changes the boost: buy-sweep-boost and buy-sweep-collect-boost
both burn the post-buy 5,255,205,915,165.

Boosts are token-claim neutral. A seeded token claim pays
3,334,551 before a boost, after a boost, after buy-boost, after
boost-buy, after sell-boost, and between two boosts alike.

Cashback claims do not mix with boosts at all. In plain mode the
claim pays 5,475, but every boost in the same plain walk panics
(ProgramFailedToComplete, 0 events) -- a standalone probe
attributes the panic to plain mode alone (tf + no_ww succeeds,
plain + ww also panics), consistent with the #103 rule that the
boost quote leg must be Token-2022. Under transfer fee the claim
itself fails 2021 (measured in #102, cited here, not re-measured).
So there is no walk in which a cashback claim and a boost both
succeed: tf mode kills the claim, plain mode kills the boost.

Transfer-fee variants: at tf0 the boost burns 5,391,870,655,895
and boost-then-buy pays 5,136,667,160,892; at tf5000 the boost
burns 2,706,767,012,738 and boost-then-buy pays 2,625,898,824,386,
while buy-then-boost at tf5000 burns 2,685,302,061,999. The boost
burn scales with the fee rate, but the ordering gap
(boost-then-trade below trade-then-boost) holds at every rate.
At tf5000 a sell-then-boost-then-sell walk pays 90,906 then
91,639, and a v2 buy at tf5000 then boost burns 2,706,767,004,697.

Boost size scales the trade. A 10^6 boost then buy pays
5,167,045,023,486 (only 80,515,267 below the patched tail); a 10^8
boost then buy pays 5,159,083,248,442; a 10^10 boost then buy pays
4,446,665,291,666 (-14% versus the patched tail). Post-buy burns
are 5,296,803,957 for a 10^6 boost and 49,079,187,497,559 for a
10^10 boost. A boost-then-buy-then-10^6-boost walk burns
5,213,841,726 on the small second boost.

Terminal-hop boosts barely move the walk. A P5 boost (999,997,999)
then buy pays 5,207,939,665,660, only 15,570,231 below the fresh
buy tail -- against 79,591,370,982 for a main-pool boost. Buy then
P5 boost burns 989,598,940, and a second P5 boost after a buy burns
989,596,971. Main and P5 boosts commute: main-then-P5 and
P5-then-main burn the anchor and 999,997,999 in either order.

Deposit/withdraw legs are boost-neutral in size. Deposit after a
boost moves vb1 by 159,347,142 versus 160,619,896 without a boost,
and withdraw after a boost returns 29,252 versus 29,018 without
one. In boost-dep-wd-boost the second boost burns exactly the
decay value 5,254,441,549,265; in dep-boost-wd-boost it burns
5,254,441,569,039 (decay + 19,774, the withdraw residue already
pinned in #102). A buy-boost-wd-buy walk ends at tail
4,807,055,733,582, within 8,674 of the no-withdraw
buy-boost-buy tail 4,807,055,742,256.

## Limits

- All numbers are harness measurements on the three program images
  (original, control, candidate); they pin the rebuilt program's
  behavior against the original on these fixtures, not mainnet
  state.
- The plain-mode boost panic is a harness-fixture observation: the
  plain quote mint carries no transfer-fee extension. It is
  consistent with the #103 Token-2022 boost-leg rule, but the
  packet does not claim a mainnet pool with an SPL quote mint
  would panic the same way.
- The tf-mode cashback-claim 2021 failure is cited from #102, not
  re-measured in this packet (this packet's cashback cases are
  plain-mode only).
- No source change is proposed. No claim is made about the full
  program beyond the measured walks.

Made via @slopdotcash
