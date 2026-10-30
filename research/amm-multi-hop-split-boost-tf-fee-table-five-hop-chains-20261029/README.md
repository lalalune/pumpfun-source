# research: split x boost x tf fee-table chains at TRUE 5 hops — tier selection, crossing and the terminal exotic hop all hold at depth 5, stable count 0 moves the tail

## Problem

Packet #80 pinned, at a TRUE 3-hop split chain, that the trade
paths price from the fee-table account, not from GlobalConfig:
the tier table selects by market cap (first tier below every
threshold, else the last tier whose threshold the cap meets,
boundary inclusive; an empty tier list fails 6082), the middle
hop is a pure pass-through (no fee gate fires there), buys
charge protocol on the FIRST hop and lp + creator on the LAST
hop (sells mirror), a canonical pool with a non-native,
non-stable quote reads the exotic flat fees if any is nonzero
else the flat fees, the buyback leg is exactly half the hop-1
protocol fee at buyback_basis_points 5000, and downstream only
the protocol sweep moves with a tier change (the boost window
is vq + accrued, so a smaller tier-1 accrual shrinks the burn).
This packet asks whether every one of those holds on the TRUE
5-hop split x boost x tf chain, and adds the ordering question
#80 left open: does a tier edit before the buy vs after the buy
change the post-buy boost burn?

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
the TOKEN22 ATA. The fixture table is: flat (25, 5, 0); 25 tiers
with tier 0 (threshold 0, 2/93/30), tier 1 (420,000,000,000,
20/5/95), tier 2 (1,470,000,000,000, 20/5/90), tier 3
(2,460,000,000,000, 20/5/85), tier 4 (3,440,000,000,000,
20/5/80); stable count 25; exotic (20, 5, 5). The main-pool
starting market cap is 182,350,153,971.

## Cases

43 cases, 234 receipts, 24 parts (23x10 + 4), across original,
control and candidate images. The 5-hop buy tail anchor is
5,207,955,235,891 with buyback leg 4,515,471, the sell payout
anchor is 178,541 with leg 837, and the buy-then-patched-window
boost anchor burn is 5,254,679,949,141.

- A (5): anchors at depth 5: buy; sell; buy then patched-window
  boost; sell then patched-window boost (burn 5,338,394,848,076);
  buy then protocol sweep, creator sweep, collect.
- T (14): tier-table edits at depth 5: tier 1 then buy, sell,
  buy-then-boost, buy-then-sweep-collect, buy-then-buy;
  tier crossing up (threshold cap0 + 3,000,000) buy then buy;
  tier crossing exact (threshold exactly cap0) buy; tier
  crossing down (threshold 184,000,000,000) buy, buy, huge sell
  10^13, small sell; unsorted tiers buy; shortcircuit (tier-0
  threshold 10^15) buy; flat-fee edit buy; empty tier list buy
  and sell; single-tier rebuild buy.
- X (8): exotic flat fees on the terminal hop at depth 5:
  lp100 buy; creator100 buy; proto100 buy; zero buy; 777 buy,
  sell, buy-then-boost, buy-then-protocol-sweep.
- S (3): stable table at depth 5: stable count 0 buy and sell;
  stable tier-1 edit buy.
- O (4): tier-edit ordering at depth 5: buy then tier-1 edit
  then patched-window boost; tier-1 edit then buy then tier-0
  restore then patched-window boost; tier-1 edit then buy then
  buy; buy then tier-1 edit then buy.
- D (3): downstream legs under a tier-1 table at depth 5:
  buy then token claim; buy then cashback claim in plain-quote
  mode; buy then deposit then withdraw.
- F (6): tf variants: tf5000 tier-1 buy, tf0 tier-1 buy, tf5000
  tier-1 sell, tf0 tier-1 sell, tf5000 exotic-777 buy, tf0
  exotic-777 buy.

## Result

Control and candidate agree on every case. Original agrees on
every case too: there are no divergent cases in this packet.

- Tier selection holds at depth 5. Replacing tier 0 with
  (20, 5, 95) moves the buy tail to 5,252,440,110,816 with
  buyback leg 244,902 (protocol bucket 249,865 = fixture 2,488
  + accrual 247,377; buyback gross 247,376 = net 244,902 +
  withheld 2,474, one unit of ceiling rounding below the
  accrual, as in #80) and the sell payout to 180,126 with leg
  45. The tier-1 buy-then-patched-window burn is
  5,254,134,170,969, below the tier-0 anchor 5,254,679,949,141:
  the window is vq + accrued, and the smaller tier-1 accrual
  shrinks the burn. A second tier-1 buy pays the same leg
  244,902 (second tail 4,957,670,972,204, pools moved).
  The tier-1 protocol sweep discharges only 249,865 (net
  247,366) against the anchor 4,563,570, while creator sweep
  (123,394, net 122,160) and collect (net 120,938) are
  byte-identical.
- Tier crossing reproduces at depth 5. With the tier-1
  threshold 3,000,000 above the starting cap, the first buy
  pays tier 0 (anchor tail, leg 4,515,471) and the second buy
  pays tier 1 (tail 4,960,132,739,427, leg 244,902): one buy
  moves the main-pool cap past the threshold. With the
  threshold exactly at the starting cap, the first buy already
  pays tier 1 (tail 5,252,440,110,816, leg 244,902): the
  boundary is inclusive (>=). Crossing down (threshold
  184,000,000,000): buy tier 0, buy tier 1, huge sell 10^13
  (tier 1, payout 1,910,135,019, leg 477,773), small sell tier
  0 again (payout 178,959, leg 839, pools moved).
- Unsorted tiers pay the last tier at depth 5: tiers [(100,
  (10, 111, 333)), (50, (20, 222, 444))] give tail
  5,144,089,657,804 with leg 10,642,838 (protocol bucket
  10,752,831). Raising the tier-0 threshold to 10^15 leaves
  the buy anchor-identical (first-tier fallback).
- The flat-fee edit is inert on the canonical route: flat
  (100, 50, 25) then buy is anchor-identical in tail, leg and
  pools. All five fixture pools are canonical (creator ==
  pool-authority PDA), so no hop reads the flat fees.
- Tier-list validation holds at depth 5. An empty tier list
  fails 6082 FeeTiersEmpty with full rollback on both sides:
  buy with 0 events, sell with 4 ghost events (the sell
  executes P5 -> P4 -> P3 -> P2 and fails at the main hop).
  A single-tier rebuild [(0, (2, 93, 30))] pays anchor + 1
  (tail 5,207,955,235,892): the rebuild encoding zeroes the
  exotic region, so the terminal hop falls back to the flat
  fees (flat sum 25 + 0 = 25 equals exotic sum 20 + 5 = 25,
  only the rounding differs) — the same patch artifact #80
  disclosed, not a program behaviour.
- Exotic edits move only the terminal hop at depth 5, and the
  terminal hop's pool fields move exactly by the creator
  accrual. Exotic (100, 0, 0) and (0, 0, 100) both give tail
  5,169,482,220,021: the buy output depends on the lp +
  creator sum, and only the creator case accrues to the P5
  creator bucket (51,963,569,700). The lp100 case leaves the
  P5 pool fields at fixture ([-125,882, 2,488, 123,394]):
  the lp fee leaves no pool-field trace, while the P5 vq
  field moves by exactly minus the creator accrual (anchor:
  -2,617,610,014 against creator accrual 2,617,610,014;
  creator100: -51,963,446,306 against 51,963,446,306). Exotic
  (0, 100, 0) gives tail 5,220,907,148,355: on the last buy hop
  the protocol gate is off, so the protocol value only
  selects the table (nonzero -> exotic path) and never enters
  the price. Exotic (0, 0, 0) falls back to flat, tail anchor
  + 1 (5,207,955,235,892). Exotic (50, 10, 777) gives tail
  4,824,041,766,089 with P5 creator bucket 376,645,119,766;
  the 777 sell pays 164,186 with leg 770 (P5 is the first hop
  on a sell, so the exotic fee hits first); the 777 post-buy
  burn is the anchor 5,254,679,949,141 and the 777 protocol
  sweep is the anchor 4,563,570 — the exotic hop touches
  neither the main-pool window nor the main-pool bucket.
- Stable count 0 moves the tail at depth 5, as in #80, and the
  mechanism is still unidentified: buy tail 5,219,868,625,118
  (P5 creator bucket 1,049,575,120, hop-1 pools
  byte-identical, buyback leg unchanged) and sell payout
  178,953 (leg 839). A stable tier-1 edit, by contrast, is
  anchor-identical. Recorded as an observation; the
  stable-count path is not claimed.
- The post-buy burn is set by the buy-time table, not by the
  table in force at boost time — the packet's sharpest new
  pin, matching #132's buy-time-bps pin. Buy then tier-1 edit
  then patched-window boost burns the anchor
  5,254,679,949,141; tier-1 edit then buy then tier-0 restore
  then patched-window boost burns the tier-1 value
  5,254,134,170,969. The burn reads the hop-1 credit the buy
  actually accrued, not the current table. Second buys agree
  across edit positions (tier-1 second buy tail
  4,957,670,972,204; buy-then-edit-then-buy second tail
  4,960,132,739,427, pools moved in both).
- Downstream legs under a tier-1 table are tier-blind except
  the protocol sweep: token claim pays 3,334,551 gross,
  cashback claim pays 5,475 in plain-quote mode, deposit quote
  -29,848 and withdraw +29,252 (pool state restored after
  withdrawal).
- Tf variants: tf5000 tier-1 buy tail 2,691,196,006,460 with
  buyback leg net 62,469 (withheld 62,469, gross 124,938);
  tf0 tier-1 buy tail 5,303,948,604,604 with leg 249,875
  (gross, no withheld); tf5000 tier-1 sell payout 90,973
  with leg 23; tf0 tier-1 sell payout 181,946 with leg 46;
  tf5000 exotic-777 buy tail 2,470,928,850,703 with leg
  1,151,788; tf0 exotic-777 buy tail 4,871,379,604,942 with
  leg 4,607,153. Tier selection itself is tf-independent;
  only the amounts carry the tf deduction.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- Fee-table edits are harness patches to the fee-table account
  (case-level `feepatch` and mid-case `cpatch` "feetier"
  steps), not on-chain table-writing instructions; the
  `tiers_rebuild` encoding writes the stable count immediately
  after the tier list, which zeroes the exotic region
  (2073..) — the +1 tail in the single-tier rebuild case is
  that artifact, disclosed as in #80.
- The stable-count-0 tail move has no identified mechanism in
  the checked-out source: stable fee changes and forcing
  stable tier 1 are both inert on this route, yet zeroing the
  stable count moves the tail hop. Recorded as an observation;
  the stable-count path is not claimed.
- A wrong fee-table account address was not delivered: the
  harness patches table data, it does not swap the account key
  in the instruction, so address validation is not covered.
- The middle hops' pass-through is recorded as observed
  (pool-state bytes unchanged across every buy/sell/tier/
  exotic case); no claim is made about why their gates are off
  beyond the gate table in `multi_hop_swap.rs`.
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
