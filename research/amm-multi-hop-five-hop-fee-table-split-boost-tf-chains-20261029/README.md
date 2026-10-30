# research: multi-hop fee-table split x boost chains under transfer fee (TRUE 5-hop, 41 cases)

## Problem

3rd #64 pinned split x boost under transfer fee at TRUE depth 3.
This packet is the same combination at TRUE depth 5 (main -> POOL2
-> P3 -> P4 -> P5, `three_amm` + g4 + g5, final output U5; hop 1
selects its fee tier by the cap, the tail hop charges exotic flat
fees and ignores the tier table entirely). The question is whether
every tf-boost effect measured at depth 3 survives two more hops:
the net-based burn, the fee-shifted dust ladder, the net min gate,
window neutrality of trades/sweeps, proportional liquidity drift,
the tf pipes composing with the boost, and the hop-1 tier-cap
shift. Depth must not be assumed to be free: the tail output, the
tail creator accrual, and the post-boost repricing all depend on
hop count, so each number below was measured fresh on the 5-hop
route, not copied from #64.

## Cases

41 cases, 276 receipts (92 steps x 3 images), 28 parts (27 x 10 + 6).
Every case runs on all three images (original, control #424,
candidate #427) and every expected value below is asserted per image
before writing; the report flags 0 divergent cases.

Route convention: `mhbuy5`/`mhsell5` are 5-hop split trades with
10^9 quote/base in, limit 1 (sells limit 1); `boost` is
boost_buy_and_burn on the main pool, `boost3` on the middle pool
P3, `boost5` on the true tail pool P5; `swc22`/`col22` are the
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
- `t-boost5`: bare true tail pool P5 boost -> 6065.
- `t-buy-boost5`: trade then true tail pool P5 boost -> 6065.
- `t-buy-boost3`: trade then middle pool P3 boost -> 6065.
- `t-buy-boost3-buy`: trade, failed middle boost, second trade:
  the second trade (tail 4,918,089,082,874) exactly equals the
  uninterrupted second trade in `t-buy-buy-boost`, so the failed
  boost leaves no residue.

All fail at boost.rs:245 with full rollback: only the 5,000
fee-payer lamports move. Neither the true tail pool nor the middle
pool opens a window on a fresh 5-hop route.

### B. Boostable pool under tf100 (vq = 10^9)

- `t-vq-boost`: 10^9 quote gross in burns 5,338,379,201,831 base
  -- exactly the depth-3 burn (vs 5,391,870,655,895 at 0 bps).
  Vault quote net +990,000,000, withheld 10,000,000. The event
  reports requested = used = 10^9 gross and the net-derived burn;
  quote_after 123,936,690,720, base_after 668,358,016,710,914,
  remaining 999,000,000,000.
- `t-vq-boost-min-exact` / `t-vq-boost-min-plus1`: min ==
  5,338,379,201,831 succeeds; min + 1 fails 6004 ExceededSlippage
  at boost.rs:274. The min gate sits on the NET burn, as at depth 3.
- `t-vq-boost-amt1` / `t-vq-boost-amt2` / `t-vq-boost-amt3`: the
  dust ladder is unchanged by depth. Amount 1 fails 6002
  ZeroQuoteAmount at boost.rs:255 (the net quote is 0 after the
  fee); amount 2 fails 6001 ZeroBaseAmount at boost.rs:273 (net
  1 quote burns 0 base); amount 3 succeeds, burning 5,435.
- `t-vq-boost-buy`: boost then buy, tail 5,087,534,167,771 (vs
  the unboosted 5-hop tf anchor 5,207,955,235,891 and the depth-3
  boosted tail 5,139,964,404,268), buyback net 4,515,471 /
  withheld 45,611, vault quote withheld 10,000,000.
- `t-vq-boost-sell`: boost then sell, user net +182,879 /
  withheld 1,848 (vs the unboosted anchor +178,541 / 1,804),
  buyback net 858 / withheld 9 -- the sell leg is depth-blind,
  matching depth 3 exactly.
- `t-vq-boost-buy-buy`: boost, buy, second buy tail
  4,810,157,577,058.
- `t-vq-buy-boost-buy`: buy (tail 5,207,955,235,891), boost (burn
  5,255,205,915,165, vq 995,438,918), second buy tail
  4,807,055,742,256.
- `t-vq-boost-swc22-col22`: boost, sweep, collect: sweep net
  122,160 / withheld 1,234, collect dest net 120,938 / withheld
  1,222 -- exactly the no-boost tf pipe, so the fee pipes compose
  with the boost unchanged at depth 5 too.
- `t-vq-boost-boost`: second burn 5,254,441,549,265 (vs
  5,306,249,181,882 at 0 bps); the window survives the first boost.
- `t-vq-buy-swc22-col22-boost-buy`: buy, sweep, collect, boost
  (burn 5,255,205,915,165 on the post-trade window), buy (tail
  4,807,055,742,256).
- `t-vq-dep-boost` / `t-vq-wd-boost` / `t-vq-depwd-boost`:
  liquidity drifts the window proportionally under tf too.
  dep-1e9 moves vq 10^9 -> 1,000,238,445 and the next burn is
  5,338,389,284,765 (+10,082,934 over baseline); wd-1e9 moves vq
  to 999,761,554 and the next burn is 5,338,369,114,126
  (-10,087,705); dep -> wd leaves vq at 999,999,999 and the next
  burn is back to the tf baseline 5,338,379,201,831 exactly.
  All three drift numbers match depth 3 to the unit.
- `t-vq-dep-boost-buy`: dep, boost (burn 5,338,389,284,765),
  buy (tail 5,087,562,174,825).
- `t-vq-wd-boost-sell`: wd, boost (burn 5,338,369,114,126),
  sell (user net +182,880 / withheld 1,848).
- `t-vq-boost-dep`: boost then dep on the boosted vaults: base
  -159,347,141,038, user quote gross -29,846,911 / net
  +29,548,441 / withheld 298,470 -- the same dep drift as the
  no-fee boosted pool.

### C. Hop-1 tier-cap shift under tf100 (vq = 10^9)

Two tiers, A = (10, 111, 333), B = (20, 222, 444), read by the
buyback net (A: 5,379,839; B: 10,642,838).

- `t-vq-cross-185`: buys cross A -> B (5,379,839 -> 10,642,838).
- `t-vq-cross-boost-shift-185`: the boosted first buy already
  selects B (10,642,838), second buy stays B (tail
  4,754,405,411,120).
- `t-vq-boost-cross-188`: the boosted buys cross A -> B
  (5,379,839 -> 10,642,838).

The cap shift from #61/#62/#63/#64 survives the fee unchanged at
depth 5.

### D. tf5000 / exotic / tf10000 anchors

- `t5-vq-boost`: tf5000 boost burns 2,706,767,012,738 -- exactly
  the depth-3 burn -- net 500,000,000 / withheld 500,000,000,
  quote_after 123,446,690,720, base_after 670,989,628,900,007.
- `t5-boost-buy`: boost then buy, tail 2,625,898,824,386,
  buyback net 1,151,788 / withheld 1,151,789, vault quote net
  +497,696,423.
- `t5-dust-ladder`: amount 1 -> 6002, amount 2 -> 6001, amount 3
  -> 6001 (net 1 at 50%), amount 4 -> success, burn 5,435
  (net 2). The smallest successful gross at tf5000 is 4, as at
  depth 3.
- `t-exotic-buy`: exotic (25, 5, 333) buy, tail
  5,041,368,432,945 (vs the depth-3 exotic tail
  5,094,574,634,908), tail creator accrual 168,728,189,766.
- `t-boost-exotic-buy`: boost then exotic buy, tail
  4,924,780,203,008 (vs the depth-3 boosted exotic tail
  4,975,541,545,687), tail creator accrual 164,806,818,095.
- `t10000-vq-boost`: tf10000 boost fails 6002 ZeroQuoteAmount
  at boost.rs:255 (the whole quote is withheld).

## Result

No divergence across the three images in any of the 41 cases.
Depth 5 changes exactly the depth-dependent numbers and nothing
else:

1. The burn, the dust ladder, the min gate, the liquidity drift,
   and the tier-cap shift are all depth-blind: tf100 burn
   5,338,379,201,831, tf5000 burn 2,706,767,012,738, dust ladders
   1 -> 6002 / 2 -> 6001 / 3 -> success (tf100) and 1 -> 6002 /
   2 -> 6001 / 3 -> 6001 / 4 -> success (tf5000), dep/wd drift
   +10,082,934 / -10,087,705, and the A -> B cap crossing all
   match depth 3 to the unit.
2. The depth-dependent numbers move as expected with two more
   hops: the fresh 5-hop buy tail is 5,207,955,235,891 (vs
   5,262,910,281,902 at depth 3), the boosted buy tail is
   5,087,534,167,771 (vs 5,139,964,404,268), the exotic tail is
   5,041,368,432,945 (vs 5,094,574,634,908), and the boosted
   exotic tail is 4,924,780,203,008 (vs 4,975,541,545,687).
   The sell leg is depth-blind (net +178,541 fresh, +182,879
   boosted, both matching depth 3).
3. The window stays the vq + accrued sum at depth 5: trades,
   sweeps, and collects never open it, on the main pool, the
   middle pool P3, or the true tail pool P5, and a failed boost
   leaves no residue on the next trade.

## Limits

- True 5-hop route only (main -> POOL2 -> P3 -> P4 -> P5). The
  split x boost x tf combination at depth 4 is not covered here
  (but #61's actual 4-hop route at 0 bps and #64's depth-3 tf
  packet bracket it); it is the natural next packet.
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
PASS: 41 cases, 276 receipts, 28 parts, per-image expectations hold (0 divergent cases)
```

Made via @slopdotcash
