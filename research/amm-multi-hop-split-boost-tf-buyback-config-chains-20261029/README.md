# Multi-hop split x boost x tf chain with update_buyback_config legs

## Problem

The split x boost x transfer-fee chain (true 3-hop, `three_amm` only,
final output U3) is now pinned across claim, lifecycle,
withdraw-withheld, coin-creator, admin setter, create-pool,
track-volume, reserved-fee, rotation, mode-toggle and disable legs.
This packet pins the remaining buyback-config surface on the same
chain: `update_buyback_config` -- the buyback bps ladder and the
buyback recipient list -- and how each change binds to a live split
chain. The question is not whether the setter works in isolation --
2nd-run packet #42 already pinned that -- but whether changing bps
or recipients moves the chain's buyback leg, its tail output, its
sweep/collect/boost/claim downstream legs, or only the
authorization gate, and whether a failed setter leaves the chain on
its anchor.

## Route

True 3-hop only. `build_route` calls `three_amm` and nothing else; the
P4/P5 fixture pools exist for snapshots but are outside the route, and
the final output is U3. No g4/g5 hop group is appended (contrast 3rd #61,
whose name said 3-hop but whose route appended g4 and was really 4 hops).

All cases run under tf100 (quote mint transfer fee 100 bps) unless noted
(the cashback-claim case runs in plain-quote mode, see below).
Program images: original (`6a7ad345...`), control (`7a300434...`),
candidate (`d17a657b...`); every case is reproduced on all three.
The buyback destination is the buyback owner's Token-2022 ATA (BB22)
passed in the route; the fixture buyback bps is 5000 and the fixture
recipient list holds 8 keys starting with the buyback owner.

## Cases

28 cases, 231 receipts (77 steps x 3 images), 24 parts (23 x 10 + 1).

### Family A -- anchors

- `a-anchor-buy`: mhbuy3 of 1e9 quote. Buyback leg 4,515,471 to BB22
  (withheld 45,611 at tf100), hop-1 quote credit 985,438,918, tail
  output U3 5,262,910,281,902.
- `a-anchor-sell`: mhsell3 of 1e9 base. Buyback leg 837 to BB22
  (withheld 9), tail quote payout 178,541.
- `a-anchor-buy-swc-col`: buy, then protocol sweep (4,563,570
  discharged, 4,517,934 net to the protocol ATA, withheld 45,636),
  creator sweep (123,394 discharged, 122,160 net, withheld 1,234),
  collect (120,938 net to the creator destination, withheld 1,222).

### Family L -- buyback bps ladder, buy and sell sides

Buy side (1e9 quote in, tail U3 in every row):

| bps | buyback leg (BB22) | withheld | hop-1 quote credit | tail U3 |
|----:|-------------------:|---------:|-------------------:|--------:|
| 2500 | 2,257,735 | 22,806 | 987,719,459 | 5,262,910,281,902 |
| 5000 | 4,515,471 | 45,611 | 985,438,918 | 5,262,910,281,902 |
| 10000 | 9,030,942 | 91,222 | 980,877,836 | 5,262,910,281,902 |
| 0 | (no leg) | -- | 990,000,000 | 5,262,910,281,902 |

The leg scales linearly with bps (2500 is half of 5000, 10000 is
twice) while the tail output is exactly unchanged: the buyback leg
comes out of the hop-1 quote credit, not out of the tail. The
7500 point (6,773,206, exactly 1.5x the 5000 leg) was already pinned
by 3rd #71 and is re-confirmed by the 7500 cases below.

Sell side (1e9 base in, tail quote payout in every row):

| bps | buyback leg (BB22) | withheld | tail quote payout |
|----:|-------------------:|---------:|------------------:|
| 2500 | 418 | 5 | 178,541 |
| 5000 | 837 | 9 | 178,541 |
| 7500 | 1,256 | 13 | 178,541 |
| 10000 | 1,676 | 17 | 178,541 |
| 0 | (no leg) | -- | 178,541 |

Same shape at small scale: the leg scales linearly, the tail payout
is fixed. (The 5000 sell row is the anchor; the ladder rows are
2500/7500/10000/0.)

- `l-bb2500-buy2`: two consecutive 2500 buys. Each buy takes the same
  2,257,735 leg (second buy tail 5,072,980,706,277, pools moved): the
  leg is per-trade, with no state carried from the first buy to the
  second beyond the moved pools.

### Family R -- recipient replacement

- `r-owner-in-buy`: recipients replaced with the owner plus 7 new keys
  (owner still first). Setter succeeds; the buy still pays BB22
  exactly 4,515,471, tail unchanged.
- `r-owner-last-buy`: recipients replaced with 7 new keys plus the
  owner last. Setter succeeds; the buy still pays BB22 exactly
  4,515,471, tail unchanged.
- `r-unsorted-owner-buy`: recipients replaced with the reversed list
  (owner last, descending). Setter succeeds; the buy still pays BB22
  exactly 4,515,471. There is no ordering check on buyback recipients
  (contrast `update_fee_config`, which rejects unsorted recipients).
- `r-owner-only-buy`: recipients replaced with 1 key (the owner
  alone). Setter fails 6057 and rolls back; the following buy pays
  BB22 4,515,471 on the original list.
- `r-nine-buy`: recipients replaced with 9 keys. Setter fails 6057
  and rolls back; the following buy pays BB22 4,515,471 on the
  original list.
- `r-excl-fullchain`: recipients replaced with 8 new keys that exclude
  the fixture buyback owner. Setter succeeds, then the buy fails
  6053 (0 events) and the sell fails 6053 (2 ghost sell events,
  disc `3e2f370aa503dc2a`, len 449). Both failures roll back, so the
  seeded buckets survive untouched: protocol sweep discharges 2,488
  (2,463 net, withheld 25), creator sweep discharges 123,394
  (122,160 net, withheld 1,234), collect pays 120,938 net.
- `r-bps7500-owner-in-buy`: bps 7500 plus the owner-in list in one
  setter. Buy leg 6,773,206 (exactly 1.5x), tail unchanged: bps and
  recipients combine without interaction.

Read together: the recipient list is a membership gate, not a
destination selector. The destination is the buyback ATA passed in
the route; the list only decides whether that owner is authorized.
As long as the owner stays in the list -- first, last, or unsorted --
the destination and the amount do not move.

### Family G -- setter gates, full chain after a failed setter

- `g-bb10001-fullchain`: bps 10001 fails 6056 and rolls back; the
  following buy, sell, sweep and collect are anchor-identical
  (buy leg 4,515,471, tail 5,262,910,281,902).
- `g-bb-outsider-fullchain`: setter signed by a non-admin fails 6005
  (fee paid by the outsider, payer delta 0); the following buy and
  sell are anchor-identical.
- `g-bb-unsigned-fullchain`: setter with the admin account not signing
  fails 3010 (fee paid by the outsider, payer delta 0); the following
  buy and sell are anchor-identical.

### Family D -- downstream legs after a bps change

- `d-bb7500-swp-col`: bps 7500, then buy, protocol sweep, creator
  sweep, collect. The protocol sweep shrinks to 2,283,029 discharged
  (2,260,198 net, withheld 22,831) from the 5000-anchor 4,563,570:
  the buyback leg grows out of the protocol bucket. The creator
  sweep (123,394 discharged, 122,160 net) and collect (120,938 net)
  are byte-identical to the anchor.
- `d-bb5000-boost` / `d-bb7500-boost`: vq patched to 1e9, setter, buy,
  then boost of 1e9. The burn is bps-blind: burned
  5,255,205,915,165, base_after 663,151,614,046,382 and remaining
  999,000,000,000 at both bps. The burn event's vq field
  (995,438,918 at 5000 vs 997,719,459 at 7500) and quote_after field
  (124,922,129,638 vs 124,919,849,097) both shift by exactly the
  buyback-gross delta 2,280,541 -- the burn itself does not move,
  only the bookkeeping around it does.
- `d-bb7500-tclaim`: bps 7500, buy, then token claim on the seeded
  volume. Claim pays gross 3,334,551, net 3,301,205 (withheld
  33,346), identical to 3rd #73's claim: the buyback setter does not
  move the token claim.
- `d-bb7500-cclaim`: bps 7500, then cashback claim in plain-quote
  mode (the tf-override quote mint fails cashback claim with an
  Anchor token-program constraint, as in 3rd #67). Claim pays 5,475
  exactly, identical to 3rd #77's claim: the buyback setter does not
  move the cashback claim either.

### Family E -- no-op setter, full chain

- `e-none-fullchain`: bps None + no recipients (silent no-op, fee
  5,000), then buy, sell, protocol sweep, creator sweep, collect --
  every leg anchor-identical (buy leg 4,515,471, tail
  5,262,910,281,902, sweeps 4,564,449 protocol / 123,394 creator,
  collect 120,938 net; the protocol sweep figure differs from Family
  A only because the intervening sell moved the bucket).

## Result

0 divergent cases: all three images agree on every case surface.
The buyback setter is fully characterized on the split chain:

1. The buyback leg scales linearly with bps on both trade sides
   while the tail output never moves.
2. The recipient list gates authorization only; the destination is
   the route's buyback ATA, and position/order inside the list are
   irrelevant.
3. The setter takes exactly 8 recipients (1 or 9 fail 6057); bps
   above 10000 fails 6056; non-admin 6005; unsigned admin 3010 --
   and every failure rolls back, leaving the chain on its anchor.
4. Downstream, only the protocol sweep moves with bps (it shrinks by
   the buyback increase); creator sweep, collect, boost burn, token
   claim and cashback claim are all setter-blind.
5. A None bps + no-recipients setter is a silent no-op.

## Limits

- The buyback destination account (BB22) is the fixture owner's ATA
  passed in the route; this packet does not test passing a
  non-owner ATA as the buyback account.
- The sell-side ladder is measured on the small standalone sell
  (1e9 base in, 178,541 quote out); the sell leg at larger sizes is
  not separately measured.
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
