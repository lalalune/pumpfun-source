# research: split x boost x tf buyback-config chains at TRUE 5 hops

## Problem

Packet #78 pinned, at a TRUE 3-hop split chain, the
`update_buyback_config` surface: the buyback leg scales linearly
with bps on both trade sides while the tail never moves, the
recipient list is a membership gate only (the destination is the
route's buyback ATA; position and order inside the list are
irrelevant), the setter takes exactly 8 recipients (1 or 9 fail
6057), bps above 10000 fails 6056, non-admin 6005, unsigned admin
3010, every failure rolls back, and downstream only the protocol
sweep moves with bps. This packet asks whether every one of those
holds on the TRUE 5-hop split x boost x tf chain, and adds the
ordering question #78 left open: does a buyback setter before the
buy vs after the buy change the post-buy boost burn?

Route verification: the builder's `build_route` calls `three_amm`
and then appends the g4 and g5 hop groups, so the buy runs
main -> P2 -> P3 -> P4 -> P5 and the sell runs the reverse;
successful swaps emit 5 hop events. The name, this README, and
the PR title all say 5 hops because the route really is 5 hops
(contrast the earlier 3-hop-named packet whose route was actually
4 hops). Each hop pool carries proper pool data (its own bump,
pool-authority creator, base mint, and vaults), not raw main-pool
bytes, and each hop boost uses an SPL-derived ATA for its hop quote
mint. The quote mint carries a per-case transfer-fee config (100
bps unless stated) and the split legs route the buyback through
the TOKEN22 ATA (BB22). The GlobalConfig buyback baseline is 5000
bps in every case unless a setter changes it.

## Cases

42 cases, 327 receipts, 33 parts (32x10 + 7), across original,
control and candidate images. The 5-hop buy tail anchor is
5,207,955,235,891 with buyback leg 4,515,471, the sell payout
anchor is 178,541 with leg 837, and the buy-then-patched-window
boost anchor burn is 5,254,679,949,141.

- A (5): anchors at depth 5: buy; sell; buy then patched-window
  boost; sell then patched-window boost (burn 5,338,394,848,076);
  buy then protocol sweep, creator sweep, collect.
- L (9): bps ladder at depth 5: buy at 2500/7500/10000/0 and a
  second 2500 buy; sell at 2500/7500/10000/0.
- R (8): recipient replacement at depth 5: owner first, owner
  last, reversed list, owner alone (1 key), 9 keys,
  owner-excluding list then buy, owner-excluding list then sell,
  bps 7500 plus owner-first list in one setter.
- G (4): setter gates at depth 5: bps 10001 then buy, outsider
  setter then buy, unsigned setter then buy, None setter (bps
  None + no recipients) then buy, sell, sweep, collect.
- D (6): downstream legs after a bps change at depth 5: 7500
  buy then protocol sweep, creator sweep, collect; 7500 buy then
  patched-window boost; 2500 buy then patched-window boost;
  7500 buy then token claim; 7500 then cashback claim in
  plain-quote mode; 7500 sell then protocol sweep.
- O (5): setter ordering at depth 5: buy then 7500 setter then
  patched-window boost; 7500 setter then buy then 2500 setter
  then patched-window boost; 7500 setter then 2500 setter then
  buy; 7500 setter then buy then 2500 setter then buy; sell
  then 7500 setter then buy.
- F (5): tf variants after a setter at depth 5: tf5000 buy at
  7500/2500, tf5000 sell at 7500, tf0 buy at 7500/10000.

## Result

Control and candidate agree on every case. Original agrees on
every case too: there are no divergent cases in this packet.

- The buyback bps ladder is linear on both sides at depth 5
  while the tail never moves. Buy side (10^9 quote in, tail U5
  5,207,955,235,891 in every row):

  | bps | buyback leg (BB22) | withheld | hop-1 quote credit |
  |----:|-------------------:|---------:|-------------------:|
  | 2500 | 2,257,735 | 22,806 | 987,719,459 |
  | 5000 | 4,515,471 | 45,611 | 985,438,918 |
  | 7500 | 6,773,206 | 68,417 | 983,158,377 |
  | 10000 | 9,030,942 | 91,222 | 980,877,836 |
  | 0 | (no leg) | -- | 990,000,000 |

  The leg comes out of the hop-1 quote credit, not out of the
  tail. A second 2500 buy takes the same 2,257,735 leg
  (second tail 4,918,089,082,874, pools moved): the leg is
  per-trade, with no state carried from the first buy beyond
  the moved pools. Sell side (10^9 base in, payout 178,541 in
  every row): legs 418/837/1,256/1,676 at 2500/5000/7500/10000
  (withheld 5/9/13/17), no leg at 0.

- The recipient list is a membership gate only, at depth 5.
  Owner first, owner last, and the reversed list all pay BB22
  exactly 4,515,471 with the tail unchanged: there is no
  ordering or position check on buyback recipients (contrast
  `update_fee_config`, which rejects unsorted recipients).
  One recipient alone fails 6057 and 9 recipients fail 6057,
  each rolling back so the following buy pays 4,515,471 on the
  original list. An owner-excluding list of 8 new keys succeeds
  as a setter, but then the buy fails 6053 with 0 events and
  the sell fails 6053 with 4 ghost events: the buyback gate is
  main-pool-legged in both directions (the buy fails at once
  at the main hop; the sell executes P5 -> P4 -> P3 -> P2 and
  fails at the main hop). Bps 7500 plus the owner-first list
  in one setter pays 6,773,206 with the tail unchanged: bps
  and recipients combine without interaction.

- Setter gates are unchanged at depth 5: bps 10001 fails 6056,
  outsider-signed fails 6005, unsigned fails 3010, and every
  failure rolls back so the following buy pays the anchor leg
  and tail. A None setter (bps None + no recipients) is a
  silent no-op (fee 5,000, 0 events) followed by an
  anchor-identical buy, a moved-pools sell (payout 189,218,
  leg 888), protocol sweep net 4,518,823, creator sweep net
  122,160 and collect net 120,938.

- Downstream, only the protocol sweep moves with bps, at depth
  5. After a 5000 buy the protocol sweep discharges 4,563,570
  (4,517,934 net, withheld 45,636); after a 7500 buy it
  discharges 2,283,029 (2,260,198 net, withheld 22,831) — the
  shrinkage is exactly the buyback-gross delta 2,280,541.
  Creator sweep (123,394 discharged, 122,160 net, withheld
  1,234) and collect (120,938 net, withheld 1,222) are
  byte-identical at both bps. After a 7500 sell the protocol
  sweep discharges only 2,912 (2,882 net, withheld 30): the
  sell leaves a tiny protocol bucket. Token claim after a 7500
  buy pays the full 3,334,551 (the incentive mint carries no
  transfer fee in this setup), identical to #125's base claim;
  cashback claim after a 7500 setter pays exactly 5,475 in
  plain-quote mode. Both claims are setter-blind.

- The post-buy boost burn is set by buy-time bps, not by the
  bps in force at boost time — the packet's sharpest new pin.
  With the window patched after the buy, the anchor
  (5000-at-buy) burn is 5,254,679,949,141; a 7500-before-buy
  burn is 5,254,775,116,926 (+95,167,785, the #128
  setter-before-buy value, reproduced here through the
  dedicated buyback setter); a 2500-before-buy burn is
  5,254,584,784,804 (-95,164,337). But a setter after the buy
  never moves the burn: buy at 5000 then set 7500 then boost
  burns exactly the anchor 5,254,679,949,141, and buy at 7500
  then set 2500 then boost still burns the buy-time value
  5,254,775,116,926. The burn reads the hop-1 credit the buy
  actually accrued, not the current bps — the #128 conclusion,
  now shown through the buyback setter alone. (Contrast #78,
  whose pre-buy-patched-window boost burned identically at
  5000/7500: the window-patch timing differs — patched before
  the buy there, after the buy here — so the two results are
  not in conflict; the patch-timing dependence itself is not
  separately isolated in this packet.) Last setter wins for
  the leg: 7500 then 2500 then buy pays the 2500 leg
  2,257,735, and a 7500 buy followed by a 2500 setter and a
  second buy pays 2,257,735 on moved pools (tail
  4,918,089,082,874). A sell then a 7500 setter then a buy
  pays 6,773,206 on moved pools (tail 5,208,011,418,184).

- Tf variants after a setter at depth 5: tf5000 buy tail
  2,668,075,748,732 with legs 575,894 at 2500 and 1,727,682 at
  7500; tf5000 sell payout 90,172 with leg 634 at 7500 (gross
  payout 180,345, split 90,172 + 90,173 withheld); tf0 buy tail
  5,259,040,470,738 with legs 6,910,730 at 7500 and 9,214,307
  at 10000 and no withheld anywhere. The ladder shape is
  tf-independent; only the scale moves.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The buyback destination account (BB22) is the fixture owner's
  Token-2022 ATA passed in the route; this packet does not test
  passing a non-owner ATA as the buyback account.
- The sell-side ladder is measured on the standalone sell
  (10^9 base in, 178,541 quote out at tf100); the sell leg at
  larger sizes is not separately measured.
- The cashback-claim case runs in plain-quote mode because the
  tf-override quote mint cannot pass cashback claim's Anchor
  token-program constraint (3rd #67); the token-claim case runs
  under tf100 with an incentive mint that carries no transfer
  fee, so it pays the full gross 3,334,551.
- The sweep cases use the Token-2022 sweep variants (swp22 /
  swc22 / col22): the SPL sweep variants fail InvalidAccountData
  on this fixture because the quote vault is Token-2022 form
  after the transfer-fee override. That failure is a fixture
  account-form property, recorded here so the variant choice is
  reproducible, not a program behaviour claim.
- Error sites are recorded per image in `error_sites` and are
  never compared across images (the original and the rebuilds
  report different source lines for the same error code).
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity.

Made via @slopdotcash
