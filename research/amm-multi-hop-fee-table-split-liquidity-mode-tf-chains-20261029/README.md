# amm-multi-hop-fee-table-split-liquidity-mode-tf-chains-20261029

## Problem

The split x liquidity x mode chains of 3rd #55 (main pool -> POOL2
-> P3; hop 1 selects a fee tier by the v2 cap rule, the tail hop
prices off exotic flat fees; a main-pool deposit/withdraw moves
the vault balances but leaves the proportional cap invariant; a
mode gate on one pool) meet a transfer fee on the quote mint
(tf100, plus one tf5000 anchor). Question: do the split legs, the
mode-gate divergence, and the liquidity limit gates all survive
tf, and do the tf pipes (gross reporting, isolated withheld)
compose with the mode gates? The route is the 3-hop route of
3rd #37/#49/#55 (1e9 quote in for buys, 1e9 BASE3 in for sells);
the main-pool sweep/collect steps run through the TOKEN22 pipes
(swc22/swp22/col22, BB22 buyback); the POOL2/P3 sweeps stay SPL
(their mints carry no transfer fee).

## Cases

31 cases, 70 steps, 210 receipts (3 images x 70 steps), 21 parts
(21 x 10). All cases run on the default fixture unless noted;
the fresh deposit leg is base -160,619,895,224, quote gross
-29,608,495 / net -29,312,410 (withheld 296,085), the fresh
withdraw leg is base +160,619,895,223, quote +29,312,409; the
post-buy deposit leg is base -159,335,860,239, quote
-29,548,629 no-fee (see tf basis below). Fee tiers A = (lp 10,
proto 111, creator 333), B = (lp 20, proto 222, creator 444);
cross threshold T_BUY = 182,350,153,971 + 1e9. Ghost events are
the hop events emitted before the gated hop fails.

Family A -- liquidity before a trade, mode on one pool:

- `a-cb-dep-buy`: cashback main. DIVERGENT. Original pays the
  tf dep-then-buy legs in full (tail out 5,262,920,106,229);
  rebuilt fails 6079 with 0 ghosts after the deposit.
- `a-cb-dep-buy-cross`: cashback main, tiers AB(T_BUY).
  DIVERGENT. Original pays both tier-crossed buys (buy 1 tier A
  buyback net 5,379,839 / withheld 54,342, buy 2 tier B buyback
  net 10,642,838 / withheld 107,504); rebuilt fails 6079 with
  0 ghosts on both buys.
- `a-cb-dep-sell`: cashback main, deposit then sell. DIVERGENT.
  Original pays the tf dep-then-sell legs (user quote net
  +178,541, buyback net 837 / withheld 9); rebuilt fails 6079
  with 2 ghosts after the deposit.
- `a-mayhem-dep-buy`: mayhem main. AGREEMENT. All images fail
  6080 with 0 ghosts after the deposit.
- `a-both-dep-buy`: both flags on main. DIVERGENT. Original
  fails 6080 with 0 ghosts (mayhem wins); rebuilt fails 6079
  with 0 ghosts (cashback wins).
- `a-cb-dep-exotic`: cashback main, exotic flat fees
  (25, 5, 333). DIVERGENT. Original pays the tf exotic legs
  (tail creator accrual 170,518,495,651, tail out
  5,094,584,146,611, then a full p3 sweep/collect drain);
  rebuilt fails 6079 with 0 ghosts, then sweeps/collects the
  untouched seed 123,394 from p3.
- `a-cb-dep-rebuild`: cashback main, tiers-only rebuild
  (100, A). DIVERGENT. Original pays the tf rebuild legs
  (tail out 5,253,722,645,179 -- exactly +1 over the tier-A
  dep cross buy1's 5,253,722,645,178, the tf+dep rebuild
  rounding of 3rd #52, reproduced under a mode flag);
  rebuilt fails 6079 with 0 ghosts, then sweeps/collects the
  seed 123,394 from p3.
- `a-p2-cb-dep-buy`: cashback on POOL2. DIVERGENT. Original
  pays the tf legs in full; rebuilt fails 6079 with 1 ghost
  (the main hop completes first).
- `a-p3-cb-dep-buy`: cashback on P3 (terminal). AGREEMENT.
  All images fail 6079 with 2 ghosts after the deposit.
- `a-mayhem-dep-sell`: mayhem main, deposit then sell.
  AGREEMENT. All images fail 6080 with 2 ghosts (sells
  execute tail-first, so the main hop is last).
- `a-cb-wd-buy`: cashback main, withdraw then buy. DIVERGENT.
  Original pays the tf wd-then-buy legs; rebuilt fails
  6079 with 0 ghosts after the withdraw.

Family B -- liquidity between trades, mode on main:

- `b-cb-buy-dep-buy`: cashback main. DIVERGENT. Original pays
  the tf buy -> post-trade deposit -> second buy chain
  (second tail out 5,072,990,104,313); rebuilt fails the
  first buy 6079 with 0 ghosts, then the deposit succeeds on
  the fresh pool (the fresh tf legs), then the second buy
  fails 6079 with 0 ghosts.
- `b-cb-buy-dep-sell`: cashback main. DIVERGENT. Original pays
  the tf buy -> deposit -> sell chain (sell out net +185,288,
  withheld 1,872, buyback net 869 / withheld 9); rebuilt fails
  the buy 6079 with 0 ghosts,
  deposits fresh, then fails the sell 6079 with 2 ghosts.
- `b-mayhem-buy-dep-buy`: mayhem main. AGREEMENT. All images
  fail the buys 6080 with 0 ghosts and deposit fresh between
  them.
- `b-cb-buy-dep-swc-col`: cashback main, buy -> deposit ->
  creator sweep -> collect -> protocol sweep. DIVERGENT.
  Original pays the tf chain (creator sweep gross 123,394
  -> net 122,160, withheld 1,234; collect dest net 120,938,
  withheld 1,222; protocol sweep gross 4,563,570 -> net
  4,517,934, withheld 45,636; main pool drained to
  [0, 0, 0]); rebuilt fails the buy, deposits fresh, then
  sweeps/collects the seed creator 123,394 and protocol
  2,488 through the tf pipes.
- `b-cb-sell-dep-sell`: cashback main. DIVERGENT. Original pays
  the tf sell -> post-sell deposit -> second sell chain
  (second sell net +178,540); rebuilt fails each sell 6079
  with 2 ghosts and deposits fresh between them.

Family C -- sweep before a trade, mode on main:

- `c-cb-swc-buy`: cashback main, creator sweep then buy.
  DIVERGENT. Original sweeps the seed through the tf pipe
  (gross 123,394 -> net 122,160, withheld 1,234) and pays
  the tf buy legs; rebuilt sweeps the seed, then fails the
  buy 6079 with 0 ghosts.
- `c-mayhem-swp-buy`: mayhem main, protocol sweep then buy.
  AGREEMENT. All images fail the protocol sweep 6013 with
  0 events (mayhem pools cannot sweep protocol fees, tf or
  not), then fail the buy 6080 with 0 ghosts.
- `c-cb-swc-sell`: cashback main, creator sweep then sell.
  DIVERGENT. Original sweeps the seed and pays the tf sell
  legs (user quote net +178,541); rebuilt sweeps the seed,
  then fails the sell 6079 with 2 ghosts.

Family D -- limit gates after a trade, mode on main (tf basis):

- `d-cb-buy-dep-limit-low`: cashback main, buy then deposit
  with maxquote 29,844,713 (one below the tf post-trade
  deposit gross). DIVERGENT. Original pays the buy, then
  the deposit fails 6004 (limit rollback, volume stays
  initialized); rebuilt fails the buy 6079, then the same
  maxquote deposits fresh successfully -- the same limit
  value gives opposite outcomes because the trade in front
  of it failed, exactly as in 3rd #55 but on the tf basis.
- `d-cb-buy-dep-limit-exact`: cashback main, buy then deposit
  with maxquote 29,844,714 (exactly the tf post-trade
  deposit gross). DIVERGENT. Original pays buy + deposit;
  rebuilt fails the buy, then deposits fresh successfully.
- `d-cb-buy-wd-limit-high`: cashback main, buy then withdraw
  with minquote 29,250,803 (one above the tf post-trade
  withdraw net). DIVERGENT. Original pays the buy, then
  the withdraw fails 6004; rebuilt fails the buy, then
  the withdraw also fails 6004 -- but on the fresh pool,
  not the post-trade pool, so the surfaces still differ.
  (A probe with minquote exactly 29,250,802 passes on the
  post-trade pool, confirming the floor.)
- `d-mayhem-buy-dep-limit`: mayhem main, buy then deposit
  with maxquote 29,844,713. AGREEMENT. All images fail the
  buy 6080 with 0 ghosts, then deposit fresh successfully.

Family E -- 1-hop terminal gate (single hop = terminal hop):

- `e-cb-dep-buy1`: cashback main, deposit then 1-hop buy.
  AGREEMENT. All images fail 6079 with 0 ghosts after the
  deposit.
- `e-cb-dep-sell1`: cashback main, deposit then 1-hop sell.
  AGREEMENT. All images fail 6079 with 0 ghosts after the
  deposit.

Family Z -- anchors:

- `z-cb-buy`: cashback main, plain buy. DIVERGENT. Original
  pays the tf buy legs (tail out 5,262,910,281,902, buyback
  net 4,515,471 / withheld 45,611, vault quote withheld
  10,000,000); rebuilt fails 6079 with 0 ghosts.
- `z-cb-sell`: cashback main, plain sell. DIVERGENT. Original
  pays the tf sell legs (user quote net +178,541, withheld
  1,804, buyback net 837 / withheld 9); rebuilt fails 6079
  with 2 ghosts.
- `z-mayhem-buy`: mayhem main, plain buy. AGREEMENT. All
  images fail 6080 with 0 ghosts.
- `z-both-buy`: both flags on main, plain buy. DIVERGENT.
  Original fails 6080 with 0 ghosts; rebuilt fails 6079 with
  0 ghosts.
- `z-dep-buy`: no flags, deposit then buy. AGREEMENT. The tf
  legs reproduce exactly on all images (sanity anchor):
  deposit gross 29,608,495 / net 29,312,410 / withheld
  296,085, then buy tail out 5,262,920,106,229.

Family F -- transfer-fee 5000 anchor:

- `f-tf5000-dep-buy`: cashback main, tf5000, deposit then buy.
  DIVERGENT. Original pays the tf5000 legs (deposit gross
  58,624,820 / net 29,312,410 / withheld 29,312,410; buy
  tail out 2,682,427,912,876, buyback net 1,151,788 /
  withheld 1,151,789, vault quote withheld 500,000,000);
  rebuilt fails the buy 6079 with 0 ghosts after the
  deposit.

## Result

31 cases, 210 receipts, 21 parts. 21 cases diverge between the
original image and the rebuilt images; 10 agree on all three.
Control and candidate agree everywhere. The pinned behaviors:

- Original cashback gate: fires only at the last-listed pool
  (P3), tf or not. Non-terminal cashback pools never gate on
  the original, in either direction: main/POOL2 buys pay in
  full and main sells pay in full.
- Rebuilt cashback gate: fires at every hop in execution
  order -- buys head-first (main 0, POOL2 1, P3 2 ghosts),
  sells tail-first (P3 0, POOL2 1, main 2 ghosts) -- tf or
  not.
- Both-flag winner: original mayhem (6080), rebuilt cashback
  (6079), at every position tested (main buys, main
  deposit-then-buys), tf or not.
- Mayhem gate: every hop, all images, both directions
  (6080); a mayhem pool's protocol sweep fails 6013 with
  0 events on all images while its creator sweep/collect
  still drain the seed, tf or not.
- Liquidity is mode-blind under tf: fresh deposits/withdraws
  on flagged pools, and deposits between failed trades, carry
  exactly the tf legs on all images (fresh deposit gross
  29,608,495 / net 29,312,410; post-trade deposit base
  -159,348,598,959 / gross 29,844,714 / net 29,546,266 /
  withheld 298,448; post-sell deposit base -160,620,133,044 /
  gross 29,608,451 / net 29,312,366 / withheld 296,085).
- The tf post-trade basis differs from the no-fee basis
  (3rd #55: post-trade deposit base -159,335,860,239 / quote
  -29,548,629), because the tf buy leaves different vault
  state -- but the basis itself is identical to 3rd #52's
  tf post-trade basis, mode flags or not.
- Liquidity limits are judged on the pool state at the time
  of the call, not the intended chain, and sit on the tf
  basis: the deposit cap is gross-side (29,844,714 passes,
  29,844,713 fails 6004) and the withdraw floor is net-side
  (29,250,802 passes, 29,250,803 fails 6004); the deposit
  event reports NET and the withdraw event reports GROSS.
  The same maxquote 29,844,713 that rolls back a post-trade
  deposit (6004) passes a fresh deposit after a failed
  trade.
- The tf pipes compose with the gates: wherever the mode
  gate does not fire, sweep/collect report gross per hop
  and isolate withheld per account (creator sweep 123,394
  -> net 122,160, withheld 1,234; collect dest net 120,938,
  withheld 1,222, vault ATA withheld 1,234 stranded;
  protocol sweep 4,563,570 -> net 4,517,934, withheld
  45,636); wherever the gate fires, the seed buckets still
  sweep/collect exactly through the tf pipes.
- The tf+dep rebuild rounding of 3rd #52 survives the mode
  flag: the tiers-only rebuild buy under a deposit comes
  out exactly +1 over the tier-A cross buy1 under the same
  deposit (5,253,722,645,179 vs 5,253,722,645,178).
- 1-hop trades gate on all images: a single hop is the
  terminal hop, so a cashback main fails 6079 with 0 ghosts
  in both directions on every image, tf or not.
- After any rebuilt failure the seed buckets still
  sweep/collect exactly (creator 123,394, protocol 2,488),
  and the sweep/collect pipes never move a trade leg.

## Limits

- 3 hops only, split route only. The 5-hop and 4-hop
  versions of this combination are not pinned here (the
  split x liquidity x mode 5-hop/4-hop chains are 3rd
  #56/#57, the split x liquidity x tf 5-hop/4-hop chains
  are 3rd #53/#54).
- The transfer fee is 100 bps (5000 bps only for the tf5000
  anchor); no other rate was measured.
- The deposit and withdraw amounts are fixed at 1e9 LP; no
  other deposit size was measured.
- No source-level mechanism is claimed for why the original
  gates cashback only at the last-listed pool: the mayhem
  program source is not in this sparse checkout, and the
  packet pins observed behavior (error codes, ghost counts,
  legs, pool states, withheld amounts) only.
- No source change, no build, and no whole-program
  equivalence is claimed. The images compared are the
  deployed original, control (#424 rebuild), and candidate
  (#427 rebuild) pump-amm binaries.
