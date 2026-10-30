# amm-multi-hop-five-hop-fee-table-split-liquidity-mode-chains-20261029

## Problem

The split x liquidity chains of 3rd #50 (main pool -> POOL2 -> P3
-> P4 -> P5; hop 1 selects a fee tier by the v2 cap rule, the
tail hop prices off exotic flat fees; a main-pool
deposit/withdraw moves the vault balances but leaves the
proportional cap invariant) meet a mode gate: one pool carries
is_cashback (byte 244), is_mayhem (byte 243), or both. This is
the 5-hop generalisation of 3rd #55. On the original image the
cashback gate fires only at the last-listed pool of the route
(P5): a cashback main, POOL2, P3, or P4 pool still pays the
full #50 legs, and a cashback main sell succeeds outright,
because sells execute tail-first (P5 -> P4 -> P3 -> POOL2 ->
main) and the gate never fires at a non-terminal hop. The
rebuilt images gate cashback at every hop in execution order,
so every chain touching a non-terminal cashback pool diverges;
on both-flag pools the original reports mayhem (6080) where
the rebuilt images report cashback (6079). Mayhem gates every
hop on all three images. Liquidity itself is mode-blind: a
deposit/withdraw on a flagged pool succeeds with exactly the
#50 legs on every image. This packet pins the 5-hop split x
liquidity x mode interaction: which legs move, which gates
fire where, and where the liquidity limit gates sit when the
trade in front of them fails.

## Cases

31 cases, 68 steps, 204 receipts (3 images x 68 steps), 21 parts
(20 x 10 + 4). All cases run on the default fixture unless
noted; the split route is the 5-hop route of 3rd #50
(1e9 quote in for buys, 1e9 BASE5 in for sells); the fresh
deposit leg is base -160,619,895,224, quote -29,312,410 for
1e9 LP, the fresh withdraw leg is base +160,619,895,223, quote
+29,312,409; the post-buy deposit leg is base -159,335,860,239,
quote -29,548,629 and the post-buy withdraw leg is base
+159,335,860,238, quote +29,548,628. Fee tiers A = (lp 10,
proto 111, creator 333), B = (lp 20, proto 222, creator 444);
cross threshold T_BUY = 182,350,153,971 + 1e9. Ghost events are
the hop events emitted before the gated hop fails.

Family A -- liquidity before a trade, mode on one pool:

- `a-cb-dep-buy5`: cashback main. DIVERGENT. Original pays the
  #50 dep-then-buy legs in full (tail out 5,259,050,280,623);
  rebuilt fails 6079 with 0 ghosts after the deposit.
- `a-cb-dep-sell5`: cashback main, deposit then sell. DIVERGENT.
  Original pays the #50 dep-then-sell legs (user quote
  +180,345, buyback 846); rebuilt fails 6079 with 4 ghosts
  after the deposit.
- `a-cb-dep-buy-cross5`: cashback main, tiers AB(T_BUY).
  DIVERGENT. Original pays both tier-crossed buys (buy 1 tier A
  buyback 5,489,071, buy 2 tier B 10,858,932); rebuilt fails
  6079 with 0 ghosts on both buys.
- `a-cb-dep1e12-buy5`: cashback main, 1e12 deposit then buy.
  DIVERGENT. Original pays the 1e12-dep legs (base
  -160,619,895,223,680, quote -29,312,409,095 for 1e12 LP)
  and a tier-A buy (buyback 4,607,153, tail out
  5,266,975,647,284): even a 1e12 proportional deposit does
  not flip the hop-1 tier. Rebuilt fails 6079 with 0 ghosts.
- `a-mayhem-dep-buy5`: mayhem main. AGREEMENT. All images fail
  6080 with 0 ghosts after the deposit.
- `a-both-dep-buy5`: both flags on main. DIVERGENT. Original
  fails 6080 with 0 ghosts (mayhem wins); rebuilt fails 6079
  with 0 ghosts (cashback wins).
- `a-p2-cb-dep-buy5`: cashback on POOL2. DIVERGENT. Original
  pays the #50 legs in full; rebuilt fails 6079 with 1 ghost
  (the main hop completes first).
- `a-p4-cb-dep-buy5`: cashback on P4. DIVERGENT. Original
  pays the #50 legs in full; rebuilt fails 6079 with 3 ghosts
  (main, POOL2, P3 complete first).
- `a-p5-cb-dep-buy5`: cashback on P5 (terminal). AGREEMENT.
  All images fail 6079 with 4 ghosts after the deposit.
- `a-cb-dep-exotic5`: cashback main, exotic flat fees
  (25, 5, 333). DIVERGENT. Original pays the #50 exotic legs
  (tail out 5,090,837,464,986, then a full p5 sweep/collect
  drain of 170,392,450,600); rebuilt fails 6079 with 0 ghosts,
  then sweeps/collects the untouched seed 123,394 from p5.
- `a-cb-wd-buy5`: cashback main, withdraw then buy. DIVERGENT.
  Original pays the #50 wd-then-buy legs (tail out
  5,259,030,656,171); rebuilt fails 6079 with 0 ghosts after
  the withdraw.
- `a-cb-vq0-dep-buy5`: cashback main, main vq patched to 0,
  then deposit then buy. DIVERGENT. The deposit drifts main
  vq to +30 (the #49 drift, mode-blind) and the original pays
  the buy legs off the drifted pool (hop-1 base leg
  -5,385,699,636,968); rebuilt fails 6079 with 0 ghosts.

Family B -- liquidity between trades, mode on main:

- `b-cb-buy-dep-buy5`: cashback main. DIVERGENT. Original pays
  the #50 buy -> post-trade deposit -> second buy chain
  (second tail out 4,963,549,649,179); rebuilt fails the first
  buy 6079 with 0 ghosts, then the deposit succeeds on the
  fresh pool (the #50 fresh legs), then the second buy fails
  6079 with 0 ghosts.
- `b-cb-buy-dep-sell5`: cashback main. DIVERGENT. Original pays
  the #50 buy -> deposit -> sell chain (sell out +191,240,
  buyback 898); rebuilt fails the buy 6079 with 0 ghosts,
  deposits fresh, then fails the sell 6079 with 4 ghosts.
- `b-mayhem-buy-dep-buy5`: mayhem main. AGREEMENT. All images
  fail the buys 6080 with 0 ghosts and deposit fresh between
  them.
- `b-cb-buy-dep-swc-col5`: cashback main, buy -> deposit ->
  creator sweep -> collect -> protocol sweep. DIVERGENT.
  Original pays the #50 chain (creator 123,394 out, then
  protocol 4,609,642 out, pool drained to [0, 0, 0]); rebuilt
  fails the buy, deposits fresh, then sweeps/collects the
  seed creator 123,394 and protocol 2,488.
- `b-cb-sell-dep-sell5`: cashback main. DIVERGENT. Original pays
  the #50 sell -> post-sell deposit (base -160,620,133,043,
  quote -29,312,366) -> second sell chain (sell out +180,343);
  rebuilt fails each sell 6079 with 4 ghosts and deposits
  fresh between them.

Family C -- sweep before a trade, mode on main:

- `c-cb-swc-buy5`: cashback main, creator sweep then buy.
  DIVERGENT. Original sweeps the seed 123,394 and pays the
  #50 buy legs; rebuilt sweeps the seed, then fails the buy
  6079 with 0 ghosts.
- `c-mayhem-swp-buy5`: mayhem main, protocol sweep then buy.
  AGREEMENT. All images fail the protocol sweep 6013 with
  0 events (mayhem pools cannot sweep protocol fees), then
  fail the buy 6080 with 0 ghosts.
- `c-cb-swc-sell5`: cashback main, creator sweep then sell.
  DIVERGENT. Original sweeps the seed and pays the #50 sell
  legs (user quote +180,345); rebuilt sweeps the seed, then
  fails the sell 6079 with 4 ghosts.

Family D -- limit gates after a trade, mode on main:

- `d-cb-buy-dep-limit-low5`: cashback main, buy then deposit
  with maxquote 29,548,628 (one below the post-trade leg).
  DIVERGENT. Original pays the buy, then the deposit fails
  6004 (limit rollback, volume stays initialized); rebuilt
  fails the buy 6079, then the same maxquote deposits fresh
  successfully -- the same limit value gives opposite
  outcomes because the trade in front of it failed.
- `d-cb-buy-dep-limit-exact5`: cashback main, buy then deposit
  with maxquote 29,548,629 (exactly the post-trade leg).
  DIVERGENT. Original pays buy + deposit; rebuilt fails the
  buy, then deposits fresh successfully.
- `d-cb-buy-wd-limit-high5`: cashback main, buy then withdraw
  with minquote 29,548,629 (one above the post-trade leg).
  DIVERGENT. Original pays the buy, then the withdraw fails
  6004; rebuilt fails the buy, then the withdraw also fails
  6004 -- but on the fresh pool, not the post-trade pool, so
  the surfaces still differ.
- `d-mayhem-buy-dep-limit5`: mayhem main, buy then deposit
  with maxquote 29,548,628. AGREEMENT. All images fail the
  buy 6080 with 0 ghosts, then deposit fresh successfully.

Family E -- 1-hop terminal gate (single hop = terminal hop):

- `e-cb-dep-buy1`: cashback main, deposit then 1-hop buy.
  AGREEMENT. All images fail 6079 with 0 ghosts after the
  deposit.
- `e-cb-dep-sell1`: cashback main, deposit then 1-hop sell.
  AGREEMENT. All images fail 6079 with 0 ghosts after the
  deposit.

Family Z -- anchors:

- `z-cb-buy5`: cashback main, plain buy. DIVERGENT. Original
  pays the #50 buy legs (tail out 5,259,040,470,738);
  rebuilt fails 6079 with 0 ghosts.
- `z-cb-sell5`: cashback main, plain sell. DIVERGENT. Original
  pays the #50 sell legs; rebuilt fails 6079 with 4 ghosts.
- `z-mayhem-buy5`: mayhem main, plain buy. AGREEMENT. All
  images fail 6080 with 0 ghosts.
- `z-both-buy5`: both flags on main, plain buy. DIVERGENT.
  Original fails 6080 with 0 ghosts; rebuilt fails 6079 with
  0 ghosts.
- `z-dep-buy5`: no flags, deposit then buy. AGREEMENT. The #50
  legs reproduce exactly on all images (sanity anchor).

## Result

31 cases, 204 receipts, 21 parts. 22 cases diverge between the
original image and the rebuilt images; 9 agree on all three.
Control and candidate agree everywhere. The pinned behaviors:

- Original cashback gate: fires only at the last-listed pool
  (P5). Non-terminal cashback pools never gate on the
  original, in either direction: main/POOL2/P3/P4 buys pay in
  full and main sells pay in full.
- Rebuilt cashback gate: fires at every hop in execution
  order -- buys head-first (main 0, POOL2 1, P3 2, P4 3, P5 4
  ghosts), sells tail-first (P5 0, P4 1, P3 2, POOL2 3,
  main 4 ghosts).
- Both-flag winner: original mayhem (6080), rebuilt cashback
  (6079), at every position tested (main buys, main
  deposit-then-buys).
- Mayhem gate: every hop, all images, both directions
  (6080); a mayhem pool's protocol sweep fails 6013 with
  0 events on all images while its creator sweep/collect
  still drain the seed.
- Liquidity is mode-blind: fresh deposits/withdraws on
  flagged pools, and deposits between failed trades, carry
  exactly the #50 legs on all images (fresh deposit base
  -160,619,895,224 / quote -29,312,410; post-trade deposit
  base -159,335,860,239 / quote -29,548,629; post-sell
  deposit base -160,620,133,043 / quote -29,312,366).
  The hop-1 leg is depth-invariant: the post-trade deposit
  and withdraw legs, and the limit gates built on them
  (29,548,629 / 29,548,628), are identical to the 3-hop
  packet #55.
- The 1e12 proportional deposit does not flip the hop-1 tier
  (buyback stays 4,607,153); the vq 0 patch still drifts main
  vq to +30 under a deposit, mode-blind.
- Liquidity limits are judged on the pool state at the time
  of the call, not the intended chain: the same maxquote
  29,548,628 that rolls back a post-trade deposit (6004)
  passes a fresh deposit after a failed trade, and a
  post-trade withdraw floor of 29,548,629 fails on both the
  post-trade pool (original) and the fresh pool (rebuilt)
  for the same limit reason.
- 1-hop trades gate on all images: a single hop is the
  terminal hop, so a cashback main fails 6079 with 0 ghosts
  in both directions on every image.
- After any rebuilt failure the seed buckets still
  sweep/collect exactly (creator 123,394, protocol 2,488),
  and the sweep/collect pipes never move a trade leg.

## Limits

- 5 hops only, split route only. The 3-hop version of this
  combination is 3rd #55; the 4-hop version is not pinned
  here (the split x liquidity 4-hop chains are 3rd #51, the
  split x mode 4-hop chains are 3rd #45).
- No transfer-fee (Token-2022) combination: the split x
  liquidity x mode chains under tf are a separate packet,
  not claimed here.
- No source-level mechanism is claimed for why the original
  gates cashback only at the last-listed pool: the mayhem
  program source is not in this sparse checkout, and the
  packet pins observed behavior (error codes, ghost counts,
  legs, pool states) only.
- No source change, no build, and no whole-program
  equivalence is claimed. The images compared are the
  deployed original, control (#424 rebuild), and candidate
  (#427 rebuild) pump-amm binaries.
