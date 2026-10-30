# Multi-hop split x boost x tf chain with fee-table legs

## Problem

The split x boost x transfer-fee chain (true 3-hop, `three_amm` only,
final output U3) is now pinned across claim, lifecycle,
withdraw-withheld, coin-creator, admin setter, create-pool,
track-volume, reserved-fee, rotation, mode-toggle, disable,
buyback-config and fee-config legs. The fee-config packet (#79)
showed the GlobalConfig values move no trade leg at all, because
all three trade paths price from the fee-table account. This
packet pins the table itself on the same chain: the tier table
and the exotic flat fees that actually set the price, the
validation the table account carries, and whether downstream
legs (sweep, collect, boost, claim, deposit/withdraw) notice a
table change. The question is not whether a fee table exists --
2nd-run #8 pinned the selection order on single-leg v2 and #29
pinned the tier boundary there, and 3rd #35/#36 pinned 2-tier and
3-tier crossings on single-leg v2 -- but whether every one of
those behaviours reproduces hop by hop on a split chain, where
each hop prices from a different table entry under different
gates, and where a table change can move one hop while leaving
the others byte-identical.

## Route

True 3-hop only. `build_route` calls `three_amm` and nothing else;
no g4/g5 group is added, so the final output is U3 and there are
exactly three hop groups. Hop 1 is the main pool (native quote),
hop 2 is the middle pool (a pass-through: it charges no fee, see
below), hop 3 is P3 (quote mint BASE2, i.e. exotic). All cases
use transfer fee 100 bps on the quote mint unless the case name
says tf0. All amounts below are measured on the original image;
control and candidate agree on every case (0 divergent cases).

## How a hop prices (source-grounded)

`select_and_apply_v2` (`programs/pump-amm/src/curve/fees.rs`)
picks the table per hop: a non-canonical pool (creator != the
pool-authority PDA for the base mint) reads the flat fees
(25, 5, 0); a canonical pool with a native or NORMAL_QUOTE
quote reads the tier table; a canonical pool with the
STABLE_QUOTE (USDC) quote reads the stable tier table; any
other canonical quote reads the exotic flat fees if at least
one of the three exotic values is nonzero, else the flat fees.
`tier()` returns the first tier when the market cap is below
every threshold, else the last tier whose threshold the cap
meets (an empty tier list fails FeeTiersEmpty, 6082). The cap
is `(mayhem ? 10^15 : base_supply) * quote_reserve /
base_reserve` (`state/pool.rs`). A buy hop's output depends on
the lp + protocol + creator bps sum after gates; the gates
(`multi_hop_swap.rs`, hop construction) are: buys charge
protocol on the FIRST hop and lp + creator on the LAST hop,
sells mirror that (lp + creator first, protocol last), and a
middle hop charges nothing. The protocol fee of a hop is split
by `accrue_fees` (`state/pool.rs`): with the fixture
buyback_basis_points of 5000, exactly half goes to the buyback
recipient (BB22) and half accrues to the pool protocol bucket,
so the buyback leg (gross) tracks the hop protocol accrual to
the unit (tier 0: 4,561,082 = 4,561,082; tier 1: 247,376 vs
247,377, one unit of ceiling rounding). The fixture table is:
flat (25, 5, 0); 25 tiers with tier 0 (threshold 0, 2/93/30),
tier 1 (420,000,000,000, 20/5/95), tier 2 (1,470,000,000,000,
20/5/90), tier 3 (2,460,000,000,000, 20/5/85), tier 4
(3,440,000,000,000, 20/5/80); stable count 25; exotic
(20, 5, 5). The main-pool starting market cap is
182,350,153,971.

## Cases

32 cases, 138 receipts (46 steps x 3 images), 14 parts.

Anchors (tf100): a-buy3 (split buy 1e9 quote: tail
5,262,910,281,902, buyback net 4,515,471, withheld vq1
10,000,000 / bb22 45,611), a-sell3 (split sell 1e9 base: payout
178,541, buyback 837, withheld userquote 1,804 / bb22 9),
a-buy2 (v2 buy 1e10 base: userquote -1,866,375, event lp_bps 2 /
lp_fee 365 / proto_bps 93 / proto_fee 16,973), a-sell2 (v2 sell
1e10 base: userquote +1,784,093).

Tier crossing (tf100): t-cross-up places the tier-1
threshold 3,000,000 above the starting cap (182,353,153,971):
the first buy pays tier 0 (tail 5,262,910,281,902, buyback
4,515,471) and the second buy pays tier 1 (tail
5,116,788,773,158, buyback 244,902) -- one buy moves the
main-pool cap past the threshold. t-cross-exact places the
threshold exactly at the starting cap (182,350,153,971): the
first buy already pays tier 1 (main protocol bucket 249,865,
buyback 244,902), proving the boundary is inclusive (>=).
t-cross-down (threshold 184,000,000,000) crosses back: buy
tier 0, buy tier 1, huge sell 1e13 (tier 1, payout
1,871,757,566), small sell tier 0 again (payout 179,068,
buyback 840, tier-0 scale). t-tier1-all forces tier 1
(threshold 0) across buy, sell, v2 buy (-1,895,679) and v2
sell (+1,813,892). t-shortcircuit raises the tier-0
threshold to 10^15: the buy is anchor-identical (first-tier
fallback). t-unsorted lists tiers [(100, (10, 111, 333)),
(50, (20, 222, 444))]: the last tier wins at cap 182e9 (main
protocol bucket 10,752,831, buyback 10,642,838, tail
5,197,698,194,693).

Exotic tail hop (tf100): x-lp100 (exotic (100, 0, 0)) and
x-creator100 (exotic (0, 0, 100)) move the tail to the same
5,224,033,425,497 -- the buy output depends on the lp+creator
sum, and only the creator case also accrues to the P3 creator
bucket (52,514,796,048). x-proto20 and x-proto100 move the
tail to the same 5,275,998,139,846: on the last buy hop the
protocol gate is off, so the protocol value only selects the
table (nonzero -> exotic path, zero -> flat path) and never
enters the price. x-zero (exotic (0, 0, 0)) falls back to the
flat fees, tail 5,262,910,281,903 -- exactly one unit above
the exotic anchor (5,262,910,281,902), because the flat sum
(25 + 0 = 25) equals the exotic sum (20 + 5 = 25) and only the
rounding differs. x-777 (exotic (50, 10, 777)) reproduces #79:
tail 4,874,965,557,788, P3 creator bucket 380,640,556,187,
hop-1 and hop-2 pools byte-identical. x-sell777 shows the
mirror: on a sell the P3 hop is first, so the exotic fee hits
the first hop (payout 164,186 vs anchor 178,541, buyback 770
vs 837, P3 creator bucket +77,823,317).

Table validation: g-count0-buy3 and g-count0-buy2 rebuild
the tier list empty and both fail 6082 FeeTiersEmpty
(fees.rs:160) with 0 events and full rollback -- the split
buy and the single-leg v2 buy share the gate.
g-count1-buy3 rebuilds a single tier (0, (2, 93, 30)):
hop-1/hop-2 price at tier 0, but the tail is
5,262,910,281,903, one unit above the anchor -- the rebuild
writes the stable count immediately after the tier list, so
it zeroes the exotic region and the tail hop falls back to
the flat fees (see Limits: this is a patch artifact of the
rebuild encoding, disclosed, not hidden). g-zero-buy2 zeroes
the main pool coin_creator (211..243, NOT the creator field
11..43): the v2 buy keeps its tier-0 event (lp_bps 2 /
proto_bps 93) but pays no creator fee (userquote -1,866,375
-> -1,860,845, exactly the 30 bps creator share), while
g-zero-buy3 is anchor-identical -- the first multi-hop hop
charges protocol only, so there is no creator leg to remove,
and the buyback leg is untouched. g-stable0-buy3 zeroes the
stable tier count (offset 1069): only the tail moves (tail
5,274,948,716,226, hop-1/hop-2 byte-identical, buyback
unchanged) although the stable table is otherwise inert on
this route; the path is not identified (see Limits).

Downstream under a tier-1 table (tf100):
d-tier1-swp22 buys under tier 1, then sweeps and collects:
the protocol sweep discharges only the tier-1 bucket
(249,865 vs the anchor 4,563,570), while the creator sweep
(123,394) and collect (120,938 net) are unchanged.
d-tier1-boost (main vq patched to 1e9, tier 1) burns
5,254,483,001,415 vs the tier-0 anchor 5,255,205,915,165:
the boost window is vq + accrued, and the tier-1 protocol
accrual (247,377) is smaller, so the window and the burn
shrink with it (event vq 999,752,623 = 1e9 - 247,377).
d-tier1-tclaim: token claim is tier-blind (gross 3,334,551 /
net 3,301,205, withheld 33,346, same as #73). d-tier1-cclaim
(plain quote, seeded earned 5,475): cashback claim pays
5,475, tier-blind. d-tier1-depwd: deposit quote -29,608,495
and withdraw quote +29,019,284, tier-blind, pool state
restored after withdrawal.

Transfer-fee interaction (tf0 baselines):
w-tier1-tf0 (tier 1, no tf): tail 5,360,959,279,511,
buyback 249,875 gross with zero withheld -- the tier-1
buyback gross is 249,875 without tf vs 247,376 gross under
tf100, and the tail is higher without the tf drag.
w-exo-tf0 (exotic (50, 10, 777), no tf): tail
4,923,313,100,054 vs 4,874,965,557,788 under tf100.
w-tier1-sell-tf0 (tier 1 sell, no tf): payout 181,946,
buyback 46, no withheld. w-cross-tf0 (threshold
cap0 + 3,000,000, no tf): buy tier 0 (buyback 4,607,153
gross), buy tier 1 (buyback 249,875) -- the crossing
reproduces with no withheld anywhere, so the tier
selection itself is tf-independent and only the amounts
carry the tf deduction.

## Result

Every tier, exotic and validation behaviour from the
single-leg packets reproduces hop by hop on the split chain,
with two split-specific pins: the middle hop is a pure
pass-through (no fee gate fires there, so no table change
touches it), and the buyback leg is exactly half the hop-1
protocol fee at buyback_basis_points 5000, so a tier change
moves the buyback leg, the protocol bucket and the
post-trade sweep by the same amount. The fee table, not
GlobalConfig, is the price: #79's setter moves nothing, and
this packet's table edits move exactly the hops whose gates
and quote mints select them. 0 divergent cases across
original, control and candidate.

## Limits

- The `tiers_rebuild` patch encoding writes the stable count
  immediately after the tier list, which zeroes the exotic
  region (2073..); g-count1-buy3's +1 tail difference is
  that artifact (flat fallback), not a program behaviour.
  `tiers_inplace` patches do not have this artifact.
- g-stable0-buy3's tail move has no identified mechanism in
  the checked-out source: stable fee changes and forcing
  stable tier 1 are both inert on this route, yet zeroing the
  stable count moves the tail hop. Recorded as an
  observation; the stable-count path is not claimed.
- A wrong fee-table account address was not delivered: the
  harness patches table data, it does not swap the account
  key in the instruction, so address validation is not
  covered here.
- The middle pool's pass-through is recorded as observed
  (pool-state bytes unchanged across every buy/sell/tier/
  exotic case); no claim is made about why its gates are off
  beyond the gate table in `multi_hop_swap.rs`.
- Single-leg v2 cases (buy2/sell2) use the main pool only;
  they are included as the table's control, not as a
  separate v2 packet.
- This packet does not change program source, does not
  build anything, and makes no claim about the full program
  beyond the measured cases.
