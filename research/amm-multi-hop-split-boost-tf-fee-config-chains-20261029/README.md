# Multi-hop split x boost x tf chain with update_fee_config legs

## Problem

The split x boost x transfer-fee chain (true 3-hop, `three_amm` only,
final output U3) is now pinned across claim, lifecycle,
withdraw-withheld, coin-creator, admin setter, create-pool,
track-volume, reserved-fee, rotation, mode-toggle, disable and
buyback-config legs. This packet pins the remaining fee-config
surface on the same chain: `update_fee_config` (2nd-run packet #43,
partially 3rd #71) -- the lp/protocol/creator fee bps and the
protocol fee recipient list -- and how each change binds to a live
split chain. The question is not whether the setter works in
isolation -- #43 already pinned the sorted-order gate, the check
order, the event and the legacy-sell binding -- but whether changing
the config moves any leg of a live split chain at all, and if not,
what the config actually controls. The answer splits three ways.
First, the config moves no trade leg amount: split buy, split sell,
v2 buy and v2 sell are all anchor-identical after the setter,
because all three trade paths price from the fee-table account, not
from GlobalConfig. Second, changing the fee table itself moves
everything the setter cannot: tier-0 fees move every leg, exotic
flat fees move only the tail hop. Third, the config list still gates
the protocol recipient: after the setter, legacy buy, legacy sell
and the protocol sweep all fail 6013, while the creator sweep and
collect still succeed.

## Route

True 3-hop only. `build_route` calls `three_amm` and nothing else; the
P4/P5 fixture pools exist for snapshots but are outside the route, and
the final output is U3. No g4/g5 hop group is appended (contrast 3rd #61,
whose name said 3-hop but whose route appended g4 and was really 4 hops).

All cases run under tf100 (quote mint transfer fee 100 bps) unless noted
(the cashback-claim case runs in plain-quote mode, see below).
Program images: original (`6a7ad345...`), control (`7a300434...`),
candidate (`d17a657b...`); every case is reproduced on all three.
The fixture fee-config is lp 20 / protocol 5 / creator 5 with 8 sorted
recipients starting with the fixture protocol recipient; the setter
under test writes lp 30 / protocol 40 / creator 100, 8 new sorted
recipients (0xd2..0xd9 keys), and a new fee authority (0x63 x 32).
The fixture fee table's tier 0 is threshold 0 with fees (2, 93, 30)
and its exotic flat fees are (20, 5, 5).

## Cases

34 cases, 189 receipts (63 steps x 3 images), 19 parts (18 x 10 + 9).

### Family A -- anchors

- `a-anchor-buy3`: mhbuy3 of 1e9 quote. Tail output U3
  5,262,910,281,902, buyback leg 4,515,471 to BB22 (withheld
  45,611), hop-1 quote credit 985,438,918.
- `a-anchor-sell3`: mhsell3 of 1e9 base. Tail quote payout
  178,541, buyback leg 837.
- `a-anchor-buy2`: v2 buy of 1e10 base. User quote -1,866,375,
  vq1 credit 1,839,310, buyback 8,401. The buy event carries
  lp_bps 2 / lp_fee 365 / proto_bps 93 / proto_fee 16,973 --
  the tier-0 values, not the config values (20 / 5).
- `a-anchor-sell2`: v2 sell of 1e9 base. User quote +178,409,
  buyback 840. The sell event carries lp_bps 2 / lp_fee 37 /
  proto_bps 93 / proto_fee 1,698 -- again tier-0, not config.

### Family C -- ufc contrast: split vs v2 single-leg

- `c-ufc-buy3`: setter, then mhbuy3. Every surface except the
  config fields themselves is anchor-identical: tail U3
  5,262,910,281,902, buyback 4,515,471, all five pool states,
  withheld, events.
- `c-ufc-sell3`: setter, then mhsell3. Tail payout 178,541,
  buyback 837, anchor-identical except config.
- `c-ufc-buy2`: setter, then v2 buy. Amounts AND the event are
  anchor-identical: lp_bps still 2, proto_bps still 93 -- the
  setter's 30 / 40 appear nowhere in the trade.
- `c-ufc-sell2`: setter, then v2 sell. Amounts and event
  anchor-identical (lp_bps 2, proto_bps 93).

Read together with Family A: the v2 event's bps fields are the
smoking gun. If v2 priced from GlobalConfig, the setter would
move lp_bps 2 -> 30 and proto_bps 93 -> 40. It moves neither.
The config bps fields are written (the setter's 360-byte event
echoes lp 30 / proto 40 / creator 100) but no trade path reads
them for pricing.

### Family T -- fee-table changes vs config changes

- `t-tier0-buy3`: tier-0 fees (2, 93, 30) -> (50, 50, 50),
  threshold kept at 0, then mhbuy3. The tail moves to
  5,285,012,799,839, buyback falls to 2,438,060 (withheld
  24,627), hop-1 quote credit rises to 987,537,313, main
  protocol fees fall to 2,465,175.
- `t-tier0-ufc-buy3`: same tier change PLUS the setter, then
  mhbuy3. Identical to `t-tier0-buy3` on every surface except
  the config fields: the setter adds nothing on top of a tier
  change.
- `t-tier0-buy2`: same tier change, then v2 buy. The event
  moves to lp_bps 50 / lp_fee 9,125 / proto_bps 50 /
  proto_fee 9,125; user quote -1,871,023, buyback 4,516.
- `t-tier0-ufc-buy2`: same tier change PLUS the setter, then
  v2 buy. Identical to `t-tier0-buy2` except config fields.
- `t-exo-buy3`: exotic flat fees (20, 5, 5) -> (50, 10, 777),
  then mhbuy3. ONLY the tail hop moves: U3 5,262,910,281,902
  -> 4,874,965,557,788, tail creator fees 2,645,500,920 ->
  380,640,556,187; hop-1 and hop-2 pools are byte-identical
  to the anchor, buyback stays 4,515,471.
- `t-exo-ufc-buy3`: same exotic change PLUS the setter, then
  mhbuy3. Identical to `t-exo-buy3` except config fields.

The 2x2 is complete: tiers move every leg, exotic moves only the
tail leg, config moves no leg. Pricing lives in the fee-table
account; GlobalConfig holds authorization metadata.

### Family G -- setter gates, then chain anchor

- `g-unsorted`: recipients in descending order -> 6012, then
  mhbuy3 anchor-identical (rollback holds across steps).
- `g-zero`: a zero recipient first -> 6011, then mhbuy3
  anchor-identical.
- `g-dup`: a duplicated recipient (first key twice) -> 6012,
  then mhbuy3 anchor-identical. Strictly ascending is required;
  non-decreasing is not enough.
- `g-lp1001-unsorted`: lp 1001 with an unsorted list -> 6000:
  the bps check beats the sorted check.
- `g-creator1001-unsorted`: creator 1001 with an unsorted list
  -> 6012: recipients are checked before creator.
- `g-creator1001-sorted`: creator 1001 with a sorted list ->
  6000, then mhbuy3 anchor-identical.
- `g-proto1001-sorted`: protocol 1001 with a sorted list ->
  6000, then mhbuy3 anchor-identical.
- `g-outsider`: setter signed by a non-admin -> 6005 (fee paid
  by the outsider, payer delta 0), then mhbuy3 anchor-identical.
- `g-unsigned`: setter with the admin account not signing ->
  3010 (fee paid by the outsider), then mhbuy3 anchor-identical.

Check order, confirmed on the split chain: lp, protocol,
recipients (nonzero, then sorted), creator -- every failure is
atomic and leaves the chain on its anchor.

### Family D -- downstream legs after the setter

- `d-ufc-swp-col`: setter, mhbuy3 (anchor-identical), then
  protocol sweep, creator sweep, collect. The protocol sweep
  FAILS 6013 with 0 events: the fixture protocol recipient is
  no longer in the config list, and the sweep gates on list
  membership exactly like a legacy trade. The creator sweep
  still discharges 123,394 (122,160 net) and collect still pays
  120,938 net -- the creator path does not consult the protocol
  list. (3rd #71 ran creator sweep/collect after the setter but
  never the protocol sweep; this is the new pin.)
- `d-ufc-boost`: vq patched to 1e9, setter, mhbuy3, boost of
  1e9. Burn stays 5,255,205,915,165 with quote_after
  124,922,129,638 and base_after 663,151,614,046,382 -- the
  setter does not move the boost.
- `d-ufc-tclaim`: setter, mhbuy3, token claim on the seeded
  volume. Claim pays gross 3,334,551, net 3,301,205 (withheld
  33,346), identical to 3rd #73's claim.
- `d-ufc-cclaim`: setter, cashback claim in plain-quote mode
  (the tf-override quote mint fails cashback claim with an
  Anchor token-program constraint, as in 3rd #67). Claim pays
  5,475 exactly, identical to 3rd #77's claim.
- `d-ufc-dep-wd`: setter, deposit then withdraw of 1e9 LP.
  Deposit: user LP +1,000,000,000, quote -29,608,495.
  Withdraw: user LP -1,000,000,000, quote +29,019,284 --
  both anchor-identical to 3rd #77's deposit/withdraw.

### Family N -- unchanged-values setter

- `n-same-buy3`: setter rewriting the fixture values (lp 20,
  protocol 5, creator 5, fixture recipients, fixture authority)
  succeeds and emits a 360-byte event echoing the fixture
  values; the following mhbuy3 is anchor-identical.
- `n-same-buy2`: same setter, then v2 buy -- anchor-identical
  (lp_bps 2, proto_bps 93).

### Family L -- legacy legs after the setter (recipient gate)

- `l-anchor-legsell`: legacy sell of 1e9 base, no setter.
  User quote +178,409, protocol leg 840, creator leg 542.
- `l-anchor-legbuy`: legacy buy of 1e10 base, no setter.
  User quote -1,866,234, protocol leg 8,402, creator leg
  5,420.
- `l-ufc-legsell`: setter, then legacy sell -> 6013, 0 events,
  full rollback. The fixture protocol recipient left the list,
  so the legacy sell is refused even though the pool, the
  amounts and the route are unchanged.
- `l-ufc-legbuy`: setter, then legacy buy -> 6013, 0 events,
  full rollback.

This is the same binding 2nd #43 pinned for a standalone legacy
sell, now reproduced on the split-chain fixture under tf100 and
extended to the legacy buy and the protocol sweep: the config
list is a membership gate for every leg that pays the protocol
recipient, and only for those legs.

## Result

0 divergent cases: all three images agree on every case surface.
The fee-config setter is fully characterized on the split chain:

1. The setter moves no trade leg amount. Split buy, split sell,
   v2 buy, v2 sell, deposit, withdraw, boost, token claim and
   cashback claim are all anchor-identical after it; the only
   surfaces that change are the config fields themselves and the
   setter's own 360-byte event.
2. Pricing lives in the fee-table account. Tier-0 fees move every
   leg (split tail and v2 event together); exotic flat fees move
   only the tail hop; the setter on top of either change adds
   nothing.
3. The recipient list gates the protocol recipient, not pricing.
   After the setter, legacy buy, legacy sell and protocol sweep
   all fail 6013, while creator sweep, collect, and every trade
   leg still succeed at anchor amounts.
4. The setter gates are lp/protocol/creator bps cap 1000 (6000),
   nonzero recipients (6011), strictly ascending recipients
   (6012), non-admin (6005), unsigned admin (3010), checked in
   write order with full atomicity: every failure leaves the
   chain on its anchor.
5. A setter rewriting the fixture values is a successful no-op
   for the chain.

## Limits

- The v2 buy/sell anchors use the fixture fee table's tier 0
  (threshold 0); tier-crossing behaviour at higher volumes is
  pinned by 3rd #35/#36, not re-measured here.
- The legacy buy/sell anchors run on the main pool with the
  fixture creator; zero-creator legacy legs (6053) are pinned by
  3rd #70, not re-measured here.
- The cashback-claim case runs in plain-quote mode because the
  tf-override quote mint cannot pass cashback claim's Anchor
  token-program constraint (3rd #67); the token-claim case runs
  under tf100.
- Error sites are recorded per image in `error_sites` and are never
  compared across images (the original and the rebuilds report
  different source lines for the same error code).
- No source changes are proposed; this packet pins observed
  behaviour only.

Made via @slopdotcash
