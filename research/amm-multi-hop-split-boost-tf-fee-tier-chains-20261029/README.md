# research: multi-hop split x boost x tf chains with fee-tier boost windows

## Problem

Packets #80/#81/#82/#83/#95 pinned the fee table on the split x
boost x tf chain: which table entry prices each hop, the tier
crossing, the exotic tail hop, truncation, validation, and dynamic
edits. What they left implicit is the boost window itself. The
boost gate reads a window built from the pool's virtual-quote
field plus the accrued protocol and creator buckets -- and this
packet shows that window sum is conserved by every leg on the
route, so no trade or fee-book leg ever opens the window on its
own, and a fee-tier edit moves the next burn only through the
accrual a trade leaves behind, never through the tier schedule
itself.

On the same true-3-hop split x boost x tf chain as packets
#64-#111 (`three_amm` only, final output U3, tf100 unless noted),
this packet measures the boost burn after tier-1, exotic-tail,
flat-edit, stable-fees-edit, stable-count-0 and 2-tier-rebuild
buys; after mid-walk tier edits and threshold crossings; after
sweeps, collects, deposits and withdrawals; on the P2/P3 hop
boosts under tier edits; under tf0/tf5000; and at the boost
`min_base` gate on a tier-1-accrual window. All amounts are for
this fixture (fee table: flat (25, 5, 0); tier 0 (threshold 0,
2/93/30), tier 1 (420,000,000,000, 20/5/95); stable count 25;
exotic (20, 5, 5); main-pool starting market cap
182,350,153,971). The first trade of a case costs the payer
1,849,400 lamports (fee 5,000 + UVA rent 1,844,400 for the
auto-created user volume accumulator).

## Cases

45 cases, 447 receipts (149 steps x 3 images), 45 parts
(44 x 10 + 7). 0 divergent cases across original / control /
candidate.

- A (5): anchors. Patched main boost 5,338,379,201,831; second
  boost without a re-patch 5,254,441,549,265; buy then patched
  boost 5,254,679,949,141; sell then patched boost
  5,338,394,848,092; buy then sell then patched boost
  5,254,695,806,281.
- B (8): window conservation. Buy, sell, tier-1 buy, exotic buy,
  buy+sell, buy+protocol sweep, buy+creator sweep, and
  buy+collect, each followed by an UNPATCHED boost: all fail
  6065.
- C (9): tier ladder, patched boost. Tier-1 buy, exotic buy,
  flat-edit buy, stable-fees-edit buy, stable-count-0 buy,
  2-tier-rebuild buy, empty-tier-rebuild buy (fails 6082),
  tier-1 sell, exotic sell.
- D (5): mid-walk tier edits. Buy then tier edit then boost;
  buy then tier edit then buy then boost; threshold-crossing
  buy then buy then boost; boost then tier edit then buy then
  boost; boost then buy then boost.
- E (8): sweep / collect / liquidity walks. Buy then protocol
  sweep, creator sweep, both sweeps, collect, exotic buy then
  P3 creator sweep, deposit, withdraw, and sell then protocol
  sweep, each then patched boost.
- F (4): hop boosts under tier edits. Tier-1 buy then P2 boost,
  exotic buy then P2 boost, flat-edit buy then P2 boost,
  tier-1 buy then P3 boost (all with the hop pool's vq field
  patched to 10^9).
- G (4): tf variants. Tier-1 buy at tf0 / tf5000, tier-0 buy at
  tf5000 / tf0, each then patched boost.
- H (2): min_base gate on a tier-1-accrual window: exact
  min_base succeeds, +1 fails 6004.

## Result

### The window sum is conserved: no leg opens the window on its own

The fixture pool starts at vq field -125,882, protocol bucket
2,488, creator bucket 123,394 -- sum exactly 0, so the fresh
boost fails 6065. A tier-0 buy leaves vq field -4,686,964 and
protocol bucket 4,563,570: the vq field moved down by exactly
4,561,082, the hop-1 protocol accrual (bucket 2,488 -> 4,563,570
is +4,561,082). A tier-1 buy leaves vq field -373,259 and
protocol bucket 249,865: down by exactly 247,377, again the
hop-1 accrual (2,488 -> 249,865 is +247,377). A sell leaves vq
field -126,729 and protocol bucket 3,335: down by exactly 847,
the sell's protocol accrual. A protocol sweep moves the vq
field UP by exactly the swept bucket (buy then sweep:
-4,686,964 -> -123,394, bucket 4,563,570 -> 0); a creator
sweep does the same for the creator bucket (buy then creator
sweep: -4,686,964 -> -4,563,570, bucket 123,394 -> 0). Every
B case therefore fails 6065: buy, sell, tier-1 buy, exotic buy,
buy+sell, buy+sweep, buy+creator sweep, buy+collect -- the
window sum stays 0 through all of them, and only the vq patch
opens it.

### A tier edit alone moves nothing; a crossing is byte-identical to the edit

- Buy then tier edit (tier 0 fees -> tier-1 fees) then patched
  boost burns exactly the tier-0 post-buy value
  5,254,679,949,141: the edit touches the table, not the
  buckets or the vaults, so the burn cannot see it.
- Buy then tier edit then buy then patched boost burns
  5,172,400,764,059 with cumulative protocol accrual 4,810,947
  (= 4,563,570 tier-0 + 247,377 tier-1): only the second trade's
  accrual moves the burn.
- Threshold-crossing buy then buy then patched boost is
  byte-identical to the edit walk: second tail 5,116,788,773,158,
  protocol accrual 4,810,947, burn 5,172,400,764,059. Placing
  the tier-1 threshold 3,000,000 above the starting cap
  (182,353,153,971) reproduces #80's crossing, and the crossing
  is the edit -- no separate crossing mechanism exists.
- Boost then tier edit then buy then patched boost burns
  5,172,498,540,602; boost then buy then patched boost burns
  5,173,028,765,024 (the buy after the first boost drains a
  smaller vault, so the second burn sits above the
  buy-then-boost ladder).

### The burn reads vaults, not the tier schedule

Patched main boost after each C buy (vq field 10^9 in all):

| buy | tail | main protocol bucket | burn |
| --- | --- | --- | --- |
| tier-0 (anchor) | 5,262,910,281,902 | 4,563,570 | 5,254,679,949,141 |
| tier-1 fees | 5,308,343,025,925 | 249,865 | 5,254,134,170,969 |
| exotic (50, 10, 777) | 4,874,965,557,788 | 4,563,570 | 5,254,679,949,141 |
| flat edit (100, 50, 25) | 5,262,910,281,902 | 4,563,570 | 5,254,679,949,141 |
| stable tier-fee edit | 5,262,910,281,902 | 4,563,570 | 5,254,679,949,141 |
| stable count 0 | 5,274,948,716,226 | 4,563,570 | 5,254,679,949,141 |
| 2-tier rebuild | 5,262,910,281,903 | 4,563,570 | 5,254,679,949,141 |

The exotic tail fee, the flat edit, the stable tier-fee edit,
the stable-count-0 misparse and the 2-tier rebuild all leave
the main hop-1 accrual at 4,563,570, so the main boost is
byte-identical to the tier-0 burn even though the tails differ
by up to 387,944,724,114 (exotic) -- the tail hop's fee
selection never reaches the main pool's burn. The stable-count-0
tail (5,274,948,716,226, #80's unexplained move) is confirmed
to move only the tail: main accrual and main burn are
anchor-identical, narrowing the mechanism to tail-hop fee
selection alone. The 2-tier rebuild tail (5,262,910,281,903,
exactly +1 over anchor) reproduces #80's rebuild artifact --
the rebuild encoding zeroes the exotic region, so the tail hop
falls back to the flat fees (creator 0, hence no P3 creator
accrual) -- while the main boost stays tier-0. The empty tier
list fails the buy with 6082 FeeTiersEmpty and leaves the
anchor boost (5,338,379,201,831) untouched.

Sell side, patched boost: tier-1 sell pays 180,126 (vs tier-0
178,541) and burns 5,338,394,882,318; exotic sell pays 164,186
(#80's x-sell777 payout) and burns 5,338,393,590,113 -- below
the tier-0 sell boost 5,338,394,848,092, because the exotic
sell's vault deltas differ from the tier-0 sell's.

### Sweeps move the next burn along the secant; collect does not

- Buy then protocol sweep (4,563,570) then patched boost:
  5,254,870,391,988 -- up 190,442,847 over the post-buy burn,
  41.73 per unit swept at the post-buy evaluation point (the
  #102 trade secant -41.69, #109's 41.73).
- Buy then creator sweep (123,394) then patched boost:
  5,254,685,098,328 -- up 5,149,187, again 41.73 per unit.
- Buy then both sweeps then patched boost: 5,254,875,541,549
  -- exactly #109's post-buy sweep boost, reproduced.
- Buy then collect (main pool) then patched boost:
  5,254,679,949,141 -- byte-identical to the post-buy burn.
  The collect is a 0-event no-op here: without a prior creator
  sweep the creator ATA holds nothing to collect, so the bucket
  stays 123,394 and the vaults never move. The contrast is the
  pin: a creator SWEEP pays from the real quote vault (vq1
  -123,394) and moves the burn, while a collect pays from the
  creator ATA and does not touch the burn at all.
- Exotic buy then P3 creator sweep pays 380,640,556,187
  (#80's x-777 P3 creator bucket) and leaves the main boost
  byte-identical to the tier-0 burn: hop-pool fee-book legs
  never reach the main boost.
- Buy then deposit then patched boost: 5,254,679,968,956
  (+19,815 over post-buy); buy then withdraw then patched
  boost: 5,254,679,929,285 (-19,856) -- near-mirror vault
  effects, two orders of magnitude below the sweep secant.
- Sell then protocol sweep (3,335) then patched boost:
  5,338,394,990,593 -- up 142,501 over the post-sell boost,
  42.73 per unit at the fresh-pool slope (#100's slope).

### Hop boosts see the tier only through vault drainage

With the hop pool's vq field patched to 10^9, after a chain buy:

- Tier-1 buy then P2 boost: 989,326,626 (P2 anchor 999,997,999
  in #111; the buy drained VB2, so the hop burn drops).
- Exotic buy then P2 boost: 989,418,199; flat-edit buy then
  P2 boost: 989,418,199 -- identical, because the flat edit
  leaves the buy's vault deltas anchor-identical.
- Tier-1 buy then P3 boost: 989,396,393 (VB3 drainage differs
  from VB2's, so the P3 burn sits between the two P2 values).
No tier schedule is read by a hop boost: the burn differences
are exactly the vault-drainage differences of the preceding
buy.

### tf variants and the min_base gate

- Tier-1 buy at tf0 then patched boost: 5,305,935,661,947
  (tail 5,360,959,279,511, #80's w-tier1-tf0 tail).
- Tier-1 buy at tf5000 then patched boost: 2,685,024,002,564
  (tail 2,705,796,070,079).
- Tier-0 buy at tf5000 then patched boost: 2,685,165,599,125
  (#109's tf5000 anchor boost, reproduced).
- Tier-0 buy at tf0 then patched boost: 5,306,492,329,463
  (tail 5,315,084,721,958, the plain tail; #109's tf0 boost,
  reproduced).
- On a tier-1-accrual window, min_base exactly
  5,254,134,170,969 succeeds and +1 fails 6004 with 0 events:
  the boost slippage gate is tier-blind, it only sees the burn.

### The boost itself is vault-neutral

After every successful boost in this packet, the pool's vq
field and both buckets are byte-identical to before the boost
(anchor: vq 10^9, protocol 2,488, creator 123,394): the boost
burns base and moves quote through the vaults, but it never
writes the vq field or either fee bucket. A second boost
without a re-patch therefore burns the #100 decay-ladder
second value 5,254,441,549,265 -- the window stays open because
the boost never closes it.

## Limits

- `cpatch` steps are harness field resets (fee table, pool vq
  field), never instructions; they carry empty transactions by
  design. The `tiers_rebuild` patch encoding writes the stable
  count immediately after the tier list, which zeroes the
  exotic region (2073..); the 2-tier rebuild's +1 tail
  difference is that artifact (flat fallback), not a program
  behaviour, as disclosed in #80.
- The window-sum conservation is measured on the fixture pools
  (hop 1 canonical native, hop 2 pass-through, hop 3 exotic);
  the gate input itself (vq + protocol + creator) is the
  #100 window definition, and this packet pins its
  conservation, not the gate's internal arithmetic.
- The stable-count-0 tail move is narrowed to tail-hop fee
  selection (main accrual and main burn anchor-identical) but
  the exact selection path is still not identified, as in #80.
- No source change is proposed. No claim is made about the
  program beyond the measured legs above.

Made via @slopdotcash
