# research: multi-hop fee-table split x boost chains under transfer fee (TRUE 4-hop, 41 cases)

## Problem

3rd #64 pinned split x boost under transfer fee at TRUE depth 3
and #65 at TRUE depth 5. This packet is the same combination at
TRUE depth 4 (main -> POOL2 -> P3 -> P4, `three_amm` + g4, final
output U4; hop 1 selects its fee tier by the cap, the tail hop
charges exotic flat fees and ignores the tier table entirely).
The question is whether every tf-boost effect measured at depths
3 and 5 survives at the even hop count: the net-based burn, the
fee-shifted dust ladder, the net min gate, window neutrality of
trades/sweeps, proportional liquidity drift, the tf pipes composing
with the boost, and the hop-1 tier-cap shift. Depth must not be
assumed to be free: the tail output, the tail creator accrual,
and the post-boost repricing all depend on hop count, so each
number below was measured fresh on the 4-hop route, not copied
from #64 or #65.

## Cases

41 cases, 276 receipts (92 steps x 3 images), 28 parts (27 x 10 + 6).
Every case runs on all three images (original, control #424,
candidate #427) and every expected value below is asserted per image
before writing; the report flags 0 divergent cases.

Route convention: `mhbuy4`/`mhsell4` are 4-hop split trades with
10^9 quote/base in, limit 1 (sells limit 1); `boost` is
boost_buy_and_burn on the main pool, `boost3` on the middle pool
P3, `boost4` on the true tail pool P4; `swc22`/`col22` are the
creator sweep/collect pair; `dep`/`wd` are 10^9 LP deposit/withdraw.
Unless noted, the quote mint carries a 100-bps transfer fee and the
main pool is patched to virtual_quote_reserves = 10^9 for boostable
cases.

### A. Window neutrality under tf100 (fresh pool, vq + accrued = 0)

- `t-fresh-boost`: fresh boost -> 6065 PoolCannotBoost.
- `t-buy-boost`, `t-sell-boost`, `t-buy-buy-boost`,
  `t-buy-sell-boost`, `t-sell-buy-boost`: trade then boost -> 6065.
- `t-buy-swc22-boost`, `t-buy-swc22-col22-boost`: trade, sweep,
  (collect), then boost -> 6065.
- `t-boost4`: bare true tail pool P4 boost -> 6065.
- `t-buy-boost4`: trade then true tail pool P4 boost -> 6065.
- `t-buy-boost3`: trade then middle pool P3 boost -> 6065.
- `t-buy-boost4-buy`: trade, failed tail boost, second trade:
  the second trade (tail 4,994,603,067,981) exactly equals the
  uninterrupted second trade in `t-buy-buy-boost`, so the failed
  boost leaves no residue.
- `t-buy-boost3-buy`: trade, failed middle boost, second trade:
  the second trade (tail 4,994,603,067,981) again exactly equals
  the uninterrupted second trade, so the failed middle boost
  leaves no residue either.

All fail at boost.rs:245 with full rollback: only the 5,000
fee-payer lamports move. Neither the true tail pool P4 nor the
middle pool P3 opens a window on a fresh 4-hop route.

### B. Boostable pool under tf100 (vq = 10^9)

- `t-vq-boost`: 10^9 quote gross in burns 5,338,379,201,831 base
  -- exactly the depth-3 and depth-5 tf100 burns. Vault quote
  net +990,000,000, withheld 10,000,000. The event reports
  requested = used = 10^9 gross and the net-derived burn;
  quote_after 123,936,690,720, base_after 668,358,016,710,914,
  remaining 999,000,000,000.
- `t-vq-boost-min-exact` / `t-vq-boost-min-plus1`: min ==
  5,338,379,201,831 succeeds; min + 1 fails 6004 ExceededSlippage
  at boost.rs:274. The min gate sits on the NET burn, as at
  depths 3 and 5.
- `t-vq-boost-amt1` / `t-vq-boost-amt2` / `t-vq-boost-amt3`: the
  dust ladder is unchanged by depth. Amount 1 fails 6002
  ZeroQuoteAmount at boost.rs:255 (the net quote is 0 after the
  fee); amount 2 fails 6001 ZeroBaseAmount at boost.rs:273 (net
  1 quote burns 0 base); amount 3 succeeds, burning 5,435.
- `t-vq-boost-buy`: boost then buy, tail 5,113,614,896,866 (vs
  5,194,030,843,046 for the same patched-pool buy without a prior
  boost, 5,235,288,546,505 for the fresh unpatched anchor, and the
  depth-3 boosted tail 5,139,964,404,268), buyback net 4,515,471 /
  withheld 45,611, vault quote withheld 10,000,000.
- `t-vq-boost-sell`: boost then sell, user net +182,879 /
  withheld 1,848 (vs the unboosted anchor +178,541 / 1,804),
  buyback net 858 / withheld 9 -- the sell leg is depth-blind,
  matching depths 3 and 5 exactly.
- `t-vq-boost-buy-buy`: boost, buy, second buy tail
  4,883,270,291,053.
- `t-vq-buy-boost-buy`: buy (tail 5,194,030,843,046), boost (burn
  5,255,205,915,165, vq 995,562,312), second buy tail
  4,880,890,740,588.
- `t-vq-boost-swc22-col22`: boost, sweep, collect: sweep net
  122,160 / withheld 1,234, collect dest net 120,938 / withheld
  1,222 -- exactly the no-boost tf pipe, so the fee pipes compose
  with the boost unchanged at depth 4 too.
- `t-vq-boost-boost`: second burn 5,254,441,549,265; the window
  survives the first boost.
- `t-vq-buy-swc22-col22-boost-buy`: buy, sweep, collect, boost
  (burn 5,255,205,915,165 on the post-trade window), buy (tail
  4,880,890,740,588).
- `t-vq-dep-boost` / `t-vq-wd-boost` / `t-vq-depwd-boost`:
  liquidity drifts the window proportionally under tf too.
  dep-1e9 moves vq 10^9 -> 1,000,238,445 and the next burn is
  5,338,389,284,765 (+10,082,934 over baseline); wd-1e9 moves vq
  to 999,761,554 and the next burn is 5,338,369,114,126
  (-10,087,705); dep -> wd leaves vq at 999,999,999 and the next
  burn is back to the tf baseline 5,338,379,201,831 exactly.
  All three drift numbers match depths 3 and 5 to the unit.
- `t-vq-dep-boost-buy`: dep, boost (burn 5,338,389,284,765),
  buy (tail 5,113,643,191,808).
- `t-vq-wd-boost-sell`: wd, boost (burn 5,338,369,114,126),
  sell (user net +182,880 / withheld 1,848).
- `t-vq-boost-dep`: boost then dep on the boosted vaults: base
  -159,347,141,038, user quote -29,846,911 gross, vault quote
  +29,548,441 net / withheld 298,470 -- the same dep drift as
  the no-fee boosted pool.

### C. Hop-1 tier-cap shift under tf100 (vq = 10^9)

Two tiers, A = (10, 111, 333), B = (20, 222, 444), read by the
buyback net (A: 5,379,839; B: 10,642,838).

- `t-vq-cross-185`: buys cross A -> B (5,379,839 -> 10,642,838;
  tails 5,184,999,635,360 -> 4,896,334,816,905).
- `t-vq-cross-boost-shift-185`: the boosted first buy already
  selects B (10,642,838, tail 5,050,550,180,582), second buy stays
  B (tail 4,825,789,651,392).
- `t-vq-boost-cross-188`: the boosted buys cross A -> B
  (5,379,839 -> 10,642,838; tails 5,104,720,782,479 ->
  4,823,406,061,831).

The cap shift from #61/#62/#63/#64/#65 survives the fee unchanged
at depth 4.

### D. tf5000 / exotic / tf10000 anchors

- `t5-vq-boost`: tf5000 boost burns 2,706,767,012,738 -- exactly
  the depth-3 and depth-5 burns -- net 500,000,000 / withheld
  500,000,000, quote_after 123,446,690,720, base_after
  670,989,628,900,007.
- `t5-boost-buy`: boost then buy, tail 2,632,829,652,205,
  buyback net 1,151,788 / withheld 1,151,789, vault quote net
  +497,696,423.
- `t5-dust-ladder`: amount 1 -> 6002, amount 2 -> 6001, amount 3
  -> 6001 (net 1 at 50%), amount 4 -> success, burn 5,435
  (net 2). The smallest successful gross at tf5000 is 4, as at
  depths 3 and 5.
- `t-exotic-buy`: exotic (25, 5, 333) buy, tail
  5,067,831,887,327 (vs the depth-3 exotic tail
  5,094,574,634,908), tail creator accrual 169,618,399,360.
- `t-boost-exotic-buy`: boost then exotic buy, tail
  4,950,030,741,509 (vs the depth-3 boosted exotic tail
  4,975,541,545,687), tail creator accrual 165,656,026,094.
- `t10000-vq-boost`: tf10000 boost fails 6002 ZeroQuoteAmount
  at boost.rs:255 (the whole quote is withheld).

## Result

No divergence across the three images in any of the 41 cases.
Depth 4 changes exactly the depth-dependent numbers and nothing
else:

1. The burn, the dust ladder, the min gate, the liquidity drift,
   and the tier-cap shift are all depth-blind: tf100 burn
   5,338,379,201,831, tf5000 burn 2,706,767,012,738, dust ladders
   1 -> 6002 / 2 -> 6001 / 3 -> success (tf100) and 1 -> 6002 /
   2 -> 6001 / 3 -> 6001 / 4 -> success (tf5000), dep/wd drift
   +10,082,934 / -10,087,705, and the A -> B cap crossing all
   match depths 3 and 5 to the unit.
2. The depth-dependent numbers move as expected with one more
   hop over depth 3: the patched-pool 4-hop buy tail is
   5,194,030,843,046 (vs 5,207,955,235,891 at depth 5 and
   5,262,910,281,902 at depth 3; the fresh unpatched 4-hop buy
   tail is 5,235,288,546,505), the boosted buy tail is
   5,113,614,896,866 (vs 5,087,534,167,771 and 5,139,964,404,268),
   the exotic tail is 5,067,831,887,327 (vs 5,041,368,432,945
   and 5,094,574,634,908), and the boosted exotic tail is
   4,950,030,741,509 (vs 4,924,780,203,008 and 4,975,541,545,687).
   The sell leg is depth-blind (net +178,541 fresh, +182,879
   boosted, both matching depths 3 and 5).
3. The window stays the vq + accrued sum at depth 4: trades,
   sweeps, and collects never open it, on the main pool, the
   middle pool P3, or the true tail pool P4, and a failed boost
   leaves no residue on the next trade.

## Limits

- True 4-hop route only (main -> POOL2 -> P3 -> P4). Depths 3
  (#64) and 5 (#65) bracket it at the same tf combination; the
  split x boost x tf combination is now pinned at all three
  depths, so a further packet on this axis needs a new
  dimension (e.g. a claim or lifecycle leg composed with the
  split x boost x tf chain).
- Only the quote mint carries a transfer fee; the base mints
  and the boost ATA's own fee state are the fixture's.
- The fresh-pool window cases use the fixture's exact zero sum
  (vq -125,882, protocol_fees 2,488, creator_fees 123,394);
  a nonzero accrued sum was not re-probed under tf here (the
  0-bps packets cover the window arithmetic).
- All amounts are LiteSVM replays of signed receipts, not
  mainnet transactions; error sites are per-image (original and
  rebuilt sources differ in line numbers) and are recorded per
  image, never compared across images.

## Reproduce

```
python3 verify.py
```

Expected output:

```
PASS: 41 cases, 276 receipts, 28 parts, per-image expectations hold (signatures, deltas, withheld, events, error codes/sites, rollback); control == candidate everywhere; original agrees everywhere (0 divergent cases)
```

Made via @slopdotcash
