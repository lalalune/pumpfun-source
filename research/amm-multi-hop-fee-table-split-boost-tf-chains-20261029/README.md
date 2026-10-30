# research: multi-hop fee-table split x boost chains under transfer fee (TRUE 3-hop, 38 cases)

## Problem

The 3rd run's split x boost packets (#61, #62, #63) pinned the boost
window and its repricing effect at 0 bps only, and the 3rd run's boost
packet (#34) pinned the transfer-fee burn only for a single isolated
boost. What changes when the split route itself runs under a transfer
fee? The question matters because the fee is taken twice over in this
setup: once on the boost's own quote leg, and once on every hop of the
split route. If the boost burn were computed on the gross quote, the
fee would be invisible to the curve; if the window were computed on
gross virtual reserves, trades and sweeps would open it. This packet
pins which side of each boundary the fee lands on, on a TRUE 3-hop
split route (main -> POOL2 -> P3 only, `three_amm` alone, final output
U3; hop 1 selects its fee tier by the cap, the tail hop charges
exotic flat fees and ignores the tier table entirely).

## Cases

38 cases, 258 receipts (86 steps x 3 images), 26 parts (25 x 10 + 8).
Every case runs on all three images (original, control #424,
candidate #427) and every expected value below is asserted per image
before writing; the report flags 0 divergent cases.

Route convention: `mhbuy3`/`mhsell3` are 3-hop split trades with
10^9 quote/base in, limit 1 (sells limit 1); `boost` is
boost_buy_and_burn on the main pool, `boost3` on the true tail pool
P3; `swc22`/`col22` are the creator sweep/collect pair; `dep`/`wd`
are 10^9 LP deposit/withdraw. Unless noted, the quote mint carries
a 100-bps transfer fee and the main pool is patched to
virtual_quote_reserves = 10^9 for boostable cases.

### A. Window neutrality under tf100 (fresh pool, vq + accrued = 0)

- `t-fresh-boost`: fresh boost -> 6065 PoolCannotBoost.
- `t-buy-boost`, `t-sell-boost`, `t-buy-buy-boost`,
  `t-buy-sell-boost`, `t-sell-buy-boost`: trade then boost -> 6065.
- `t-buy-swc22-boost`, `t-buy-swc22-col22-boost`: trade, sweep,
  (collect), then boost -> 6065.
- `t-buy-boost3`: trade then true tail pool P3 boost -> 6065.
- `t-buy-boost3-buy`: trade, failed tail boost, second trade: the
  second trade (tail 5,072,980,706,277) exactly equals the
  uninterrupted second trade in `t-buy-buy-boost`, so the failed
  boost leaves no residue.

All ten fail at boost.rs:245 with full rollback: only the 5,000
fee-payer lamports move.

### B. Boostable pool under tf100 (vq = 10^9)

- `t-vq-boost`: 10^9 quote gross in burns 5,338,379,201,831 base
  (vs 5,391,870,655,895 at 0 bps). Vault quote net +990,000,000,
  withheld 10,000,000. The event reports requested = used = 10^9
  gross and the net-derived burn; quote_after 123,936,690,720,
  base_after 668,358,016,710,914, remaining 999,000,000,000.
- `t-vq-boost-min-exact` / `t-vq-boost-min-plus1`: min ==
  5,338,379,201,831 succeeds; min + 1 fails 6004 ExceededSlippage
  at boost.rs:274. The min gate sits on the NET burn.
- `t-vq-boost-amt1` / `t-vq-boost-amt2` / `t-vq-boost-amt3`: the
  dust ladder shifts by the fee. Amount 1 fails 6002
  ZeroQuoteAmount at boost.rs:255 (the net quote is 0 after the
  fee); amount 2 fails 6001 ZeroBaseAmount at boost.rs:273 (net
  1 quote burns 0 base); amount 3 succeeds, burning 5,435 -- the
  same burn as no-fee amount 2. At 0 bps the ladder was 1 -> 6001,
  2 -> 5,435; under tf100 the smallest successful gross is 3.
- `t-vq-boost-buy`: boost then buy, tail 5,139,964,404,268 (vs the
  unboosted tf anchor 5,262,910,281,902), buyback net 4,515,471 /
  withheld 45,611, vault quote withheld 10,000,000.
- `t-vq-boost-sell`: boost then sell, user net +182,879 /
  withheld 1,848 (vs the unboosted anchor +178,541 / 1,804),
  buyback net 858 / withheld 9.
- `t-vq-boost-buy-buy`: boost, buy, second buy tail
  4,958,122,565,416.
- `t-vq-buy-boost-buy`: buy (tail 5,221,217,806,636), boost (burn
  5,255,205,915,165, vq 995,438,918), second buy tail
  4,956,499,821,134.
- `t-vq-boost-swc22-col22`: boost, sweep, collect: sweep net
  122,160 / withheld 1,234, collect dest net 120,938 / withheld
  1,222 -- exactly the no-boost tf pipe, so the fee pipes compose
  with the boost unchanged.
- `t-vq-boost-boost`: second burn 5,254,441,549,265 (vs
  5,306,249,181,882 at 0 bps); the window survives the first boost.
- `t-vq-buy-swc22-col22-boost-buy`: buy, sweep, collect, boost
  (burn 5,255,205,915,165 on the post-trade window), buy (tail
  4,956,499,821,134).
- `t-vq-dep-boost` / `t-vq-wd-boost` / `t-vq-depwd-boost`:
  liquidity drifts the window proportionally under tf too.
  dep-1e9 moves vq 10^9 -> 1,000,238,445 and the next burn is
  5,338,389,284,765 (+10,082,934 over baseline); wd-1e9 moves vq
  to 999,761,554 and the next burn is 5,338,369,114,126
  (-10,087,705); dep -> wd leaves vq at 999,999,999 and the next
  burn is back to the tf baseline 5,338,379,201,831 exactly.
- `t-vq-dep-boost-buy`: dep, boost (burn 5,338,389,284,765),
  buy (tail 5,139,992,991,557).
- `t-vq-wd-boost-sell`: wd, boost (burn 5,338,369,114,126),
  sell (user net +182,880 / withheld 1,848).
- `t-vq-boost-dep`: boost then dep on the boosted vaults: base
  -159,347,141,038, user quote gross -29,846,911 / net
  +29,548,441 / withheld 298,470, dep vq 1,000,238,445 -- the
  same dep drift as the no-fee boosted pool.

### C. Hop-1 tier-cap shift under tf100 (vq = 10^9)

Two tiers, A = (10, 111, 333), B = (20, 222, 444), read by the
buyback net (A: 5,379,839; B: 10,642,838).

- `t-vq-cross-185`: buys cross A -> B (5,379,839 -> 10,642,838).
- `t-vq-cross-boost-shift-185`: the boosted first buy already
  selects B (10,642,838), second buy stays B.
- `t-vq-boost-cross-188`: the boosted buys cross A -> B
  (5,379,839 -> 10,642,838).

The cap shift from #61/#62/#63 survives the fee unchanged.

### D. tf5000 / exotic / tf10000 anchors

- `t5-vq-boost`: tf5000 boost burns 2,706,767,012,738, net
  500,000,000 / withheld 500,000,000, quote_after
  123,446,690,720, base_after 670,989,628,900,007.
- `t5-boost-buy`: boost then buy, tail 2,639,797,163,464,
  buyback net 1,151,788 / withheld 1,151,789, vault quote net
  +497,696,423.
- `t5-dust-ladder`: amount 1 -> 6002, amount 2 -> 6001, amount 3
  -> 6001 (net 1 at 50%), amount 4 -> success, burn 5,435
  (net 2). The smallest successful gross at tf5000 is 4.
- `t-exotic-buy`: exotic (25, 5, 333) buy, tail
  5,094,574,634,908, tail creator accrual 170,518,175,660.
- `t-boost-exotic-buy`: boost then exotic buy, tail
  4,975,541,545,687, tail creator accrual 166,514,154,324.
- `t10000-vq-boost`: tf10000 boost fails 6002 ZeroQuoteAmount
  at boost.rs:255 (the whole quote is withheld).

## Result

No divergence across the three images in any of the 38 cases.
The fee changes the boost in exactly three pinned ways, and
nothing else:

1. The burn is net-based: 10^9 gross in burns 5,338,379,201,831
   at tf100 and 2,706,767,012,738 at tf5000, vs 5,391,870,655,895
   at 0 bps. The event still reports the gross requested/used.
2. The dust and min gates sit on the net side: min gates on the
   net burn, amount 1 fails 6002 (net quote zero) instead of the
   no-fee 6001, and the smallest successful gross is 3 at tf100
   and 4 at tf5000 (net 2 quote always burns 5,435).
3. Everything structural is fee-blind: the window stays the
   vq + accrued sum (trades and sweeps never open it), the
   liquidity drift is proportional, the sweep/collect pipes are
   byte-identical with or without a boost, and the hop-1
   tier-cap shift is unchanged.

## Limits

- True 3-hop route only (main -> POOL2 -> P3). The 4-hop and
  5-hop split x boost x tf combinations are not covered here;
  they are the natural next packets.
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
PASS: 38 cases, 258 receipts, 26 parts, per-image expectations hold (0 divergent cases)
```

Made via @slopdotcash
