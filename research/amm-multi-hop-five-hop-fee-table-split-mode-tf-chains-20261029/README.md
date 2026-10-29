# research: multi-hop fee-table split on mode pools under transfer fee at depth 5 — the split and the mode-gate divergence both survive tf, and the tf pipes compose with the gates

## Problem

3rd #37 pinned the multi-hop fee-table split with no mode flags
and no transfer fee: hop 1 follows the cap-based fee-tier
selection, the tail hop follows the exotic flat fees, and a
tiers-only feeconfig rebuild silently zeroes the tail fee.
3rd #40 moved the split under transfer fee (tf100/tf5000 on
the quote mint): the split survived, with the tf pipes
gross-reporting and each hop's withheld isolated. 3rd #43
moved the split onto mode pools: the original image gates
cashback only at the terminal hop, while the rebuilt images
gate it at every hop, so every non-terminal cashback pool
diverges. 3rd #46 closed the triple combination (split x
mode x tf) at depth 3. This packet is the 5-hop
generalization of #46: does the split survive when the
pools carry mode flags AND the quote mint carries a
transfer fee at depth 5, does the mode-gate divergence
survive tf at depth 5, and do the tf pipes compose with
the mode gates across five hops?

The route is main -> POOL2 -> P3 -> P4 -> P5. Cashback /
mayhem / both-flags are set on individual pools, tf100
(plus one tf5000 anchor) is set on the quote mint, and
the #38/#44 fee patches (tier crossing, exotic legs,
stable-count, tiers-only rebuild) are applied on top.
The fee-tier rule is the same as in 3rd #35/#36: the tier
is the last tier whose threshold is `<= cap`, where
`cap = base_mint_supply * effective_quote / vault_base`,
the main pool's starting cap is exactly 182,350,153,971,
and the two custom tiers are A = (lp 10, protocol 111,
creator 333) and B = (lp 20, protocol 222, creator 444).
Under tf100 the hop-1 legs shift exactly as in #40/#46
(buy1 A, buy2 B); the tf thresholds are the #46 ones:
cross at cap0 + 10^9, exact at the tf post-buy1 cap
185,266,148,570, mid-sell at 182,349,883,978.

## Cases

27 cases, 59 steps, 177 receipts (each step run on the
original, control (#424), and candidate (#427) images). All
amounts are token amounts unless noted. Pool state is
(virtual_quote_reserves i128, protocol_fees, creator_fees,
lp_supply). The fixture pools are main, POOL2, P3, P4, P5,
each (-125,882, 2,488, 123,394, 4,194,352,106,721) at
setup. The report flags 18 cases divergent (original vs
rebuilt) and 9 cases in agreement across all three
images; control and candidate agree in every case. The
first successful multi-hop step pays 1,849,400 lamports
(1,844,400 rent for the 137-byte volume accumulator plus
the 5,000 fee); later steps pay 5,000. Intermediate pools
accrue nothing on any image. Under tf the hop-1 buyback
leg lands in a TOKEN22 buyback ATA (bb22) and the
main-pool sweep/collect pipes use TOKEN22 vault/dest
ATAs; the intermediate and tail pools (SPL mints) keep
SPL sweep/collect pipes.

Family A -- hop-1 tier crossing under a non-terminal
cashback flag, under tf100 (divergent: the original
crosses tiers, the rebuilt images fail cashback 6079 at
the flagged hop):

- `a-main-cb-cross`: main cashback, tiers [(100, A),
  (cap0 + 10^9, B)]. Original: buy1 pays A (tail out
  5,198,948,720,102, buyback gross 5,434,181 = net
  5,379,839 + withheld 54,342, main protocol 5,436,669,
  vault quote withheld 10,000,000), buy2 pays B (tail
  out 4,858,217,656,788, buyback gross 10,750,342, main
  protocol 16,187,012), tail sweep/collect drain
  5,079,819,320. The hop-1 legs are byte-identical to
  the no-mode 5-hop tf100 cross legs of #41 and the
  3-hop mode tf100 cross legs of #46: neither the mode
  flag nor the route depth moves a single hop-1 tf leg.
  Rebuilt: 6079 with 0 ghost events on both buys, then
  the seed sweep/collect drain 123,394 exactly.
- `a-p2-cb-cross`: POOL2 cashback, same tiers.
  Original: identical crossing legs. Rebuilt: 6079
  with 1 ghost event on both buys.
- `a-p3-cb-cross`: P3 cashback, same tiers. Rebuilt:
  6079 with 2 ghost events on both buys.
- `a-p4-cb-cross`: P4 cashback, same tiers. Rebuilt:
  6079 with 3 ghost events on both buys.
- `a-main-cb-exact`: main cashback, threshold set
  exactly to the tf post-buy1 cap (185,266,148,570).
  Original: buy2 still pays B -- the inclusive
  boundary holds under mode AND tf at depth 5 too.
  Rebuilt: 6079 with 0 ghosts on both buys.
- `a-main-cb-loop`: main cashback, same tiers, three
  buys. Original: buy A, buy B, buy B (third tail out
  4,598,268,689,287, buyback gross 10,750,342, main
  protocol 26,937,355), tail sweep/collect drain
  7,436,902,263. Rebuilt: 6079 with 0 ghosts on all
  three buys, then the seed drain.
- `a-p2-cb-sell`: POOL2 cashback, mid-sell tiers.
  Original: sell1 pays B (user net 176,216, withheld
  1,780, buyback gross 2,021, withheld 21), sell2 pays
  A (user net 178,214, withheld 1,801, buyback gross
  1,010, withheld 11) -- the 5-hop sell2 net is 1
  below the 3-hop value (178,215), the depth-5
  rounding shift seen in #41/#42. Rebuilt: 6079 with
  3 ghost events on both sells (sells execute
  tail-first, so POOL2 is the fourth hop on sells).
- `a-main-cb-sell-cross`: main cashback, same sell
  tiers. Original: sell B -> sell A, tail sweep/collect
  drain 1,123,393. Rebuilt: 6079 with 4 ghost events on
  both sells (main is the last hop on sells).

Family B -- the tail hop follows the exotic flat fees
under a non-terminal cashback flag, under tf100
(divergent: the original pays the exotic tail legs, the
rebuilt images fail at the head hop):

- `b-main-cb-exotic333`: main cashback, exotic (25, 5,
  333). Original: tail creator 168,728,313,160,
  sweep/collect drain it exactly -- byte-identical to
  the no-mode 5-hop tf100 exotic333 tail of #41.
  Rebuilt: 6079 with 0 ghosts, then the seed drain.
- `b-main-cb-rebuild`: main cashback, feeconfig rebuilt
  with tiers only [(100, A)]. Original: hop 1 pays A
  exactly (buyback gross 5,434,181, main protocol
  5,436,669) but the tail creator bucket collapses to
  the seed 123,394, and the tail out is one token
  higher than the plain tier-A out (5,198,948,720,103
  vs 5,198,948,720,102) -- the rebuild trap survives
  mode AND tf, and the 5-hop tf rebuild out is +1 (not
  exactly equal as at depth 3/4). Rebuilt: 6079 with 0
  ghosts, then the seed drain.
- `b-main-cb-count0`: main cashback, stable count set
  to 0 (stable entries left in place). Original: tail
  creator 1,049,575,120, sweep/collect drain it exactly
  -- the count-field shift reproduces under mode AND
  tf at depth 5 (mechanism not asserted). Rebuilt:
  6079 with 0 ghosts, then the seed drain.
- `b-main-cb-exotic0`: main cashback, exotic (0, 0, 0).
  Original: tail creator stays at the seed 123,394,
  tail out 5,207,955,235,892 (+1 vs the tf default
  5,207,955,235,891) -- the tail fee is exactly zero
  under mode AND tf. Rebuilt: 6079 with 0 ghosts, then
  the seed drain.

Family C -- sweep pipes under a non-terminal cashback
flag, under tf100 (divergent):

- `c-main-cb-sweep`: main cashback, default config,
  one buy then protocol sweep, creator sweep, collect
  on main, all through the TOKEN22 pipes. Original:
  buy leaves main protocol 4,563,570 (buyback gross
  4,561,082 = net 4,515,471 + withheld 45,611);
  protocol sweep gross 4,563,570 -> net 4,517,934
  (withheld 45,636), creator sweep gross 123,394 ->
  net 122,160 (withheld 1,234), collect gross 122,160
  -> dest net 120,938 (withheld 1,222), main pool ends
  at (0, 0, 0). The vault ATA keeps its 1,234 withheld
  isolated, exactly as in #40/#46. Rebuilt: the buy
  fails 6079 with 0 ghosts, then the seed pipes drain
  (protocol gross 2,488 -> net 2,463, withheld 25;
  creator 123,394 -> 122,160; collect 120,938).
- `c-p4-cb-sweep`: P4 cashback, one buy plus creator
  sweep and collect on P4 (SPL pipes: the
  intermediate mint is not tf'd). Original: P4
  accrues nothing (it is an intermediate pool), so its
  creator sweep/collect drain the 123,394 seed.
  Rebuilt: 6079 with 3 ghosts on the buy, then the same
  seed drains.

Family D -- mixed cashback/mayhem gates, under tf100
(divergent: different error code AND different ghost
count):

- `d-maincb-tailmayhem-buy`: main cashback + tail
  mayhem, one buy. Original: 6080 with 4 ghost events
  (the mayhem tail gate fires after four completed
  hops). Rebuilt: 6079 with 0 ghosts (the cashback
  head gate fires first).
- `d-maincb-p4mayhem-buy`: main cashback + P4 mayhem,
  one buy. Original: 6080 with 3 ghosts. Rebuilt:
  6079 with 0 ghosts.
- `d-p2cb-tailmayhem-buy`: POOL2 cashback + tail
  mayhem, one buy. Original: 6080 with 4 ghosts.
  Rebuilt: 6079 with 1 ghost.

Family E -- agreement cases, under tf100 (all three
images identical):

- `e-tail-cb`: tail cashback, one buy: 6079 with 4
  ghosts on all images -- the terminal hop is
  cashback-gated everywhere, tf included.
- `e-main-mayhem`: main mayhem, one buy: 6080 with 0
  ghosts on all images.
- `e-p2-mayhem`: POOL2 mayhem, one buy: 6080 with 1
  ghost on all images.
- `e-p4-mayhem`: P4 mayhem, one buy: 6080 with 3
  ghosts on all images.
- `e-tail-both`: tail both-flags, one buy: 6079 with 4
  ghosts on all images -- at the terminal hop
  cashback wins everywhere, tf included.
- `e-tail-cb-exotic`: tail cashback + exotic (25, 5,
  333), one buy: 6079 with 4 ghosts on all images --
  exotic legs do not rescue a gated tail hop, even
  under tf.
- `e-tail-mayhem-sweep`: tail mayhem, buy then
  protocol sweep, creator sweep, collect. The buy
  fails 6080 with 4 ghosts, the protocol sweep fails
  6013 with 0 events (the mayhem gate reaches the
  sweep handler), and the creator sweep/collect drain
  the seed 123,394 -- all on all images.
- `e-order-sell-tail-first`: main cashback + tail
  mayhem, one sell: 6080 with 0 ghosts on all images
  -- sells execute the tail hop first, so the tail
  mayhem gate fires before the main cashback gate on
  every image, tf included.
- `e-order-buy-head-first`: main mayhem + tail
  cashback, one buy: 6080 with 0 ghosts on all images
  -- buys execute the head hop first, so the head
  mayhem gate fires before the tail cashback gate on
  every image, tf included.

Family F -- tf5000 anchor (divergent):

- `f-tf5000-main-cb-cross`: main cashback, tf5000,
  same cross tiers. Original: buy1 pays A (tail out
  2,663,395,456,718, buyback gross 2,744,536 = net
  1,372,268 + withheld 1,372,268, vault quote withheld
  500,000,000), buy2 pays B (tail out 2,558,852,815,290,
  buyback gross 5,429,466 = net 2,714,733 + withheld
  2,714,733) -- the buyback grosses match the 3-hop
  tf5000 cross legs of #46 exactly. Rebuilt: 6079 with
  0 ghosts on both buys.

## Result

The triple combination composes without interference at
depth 5:

1. On the original image, a non-terminal cashback pool
   does not disturb the tf split: hop 1 still crosses
   tiers mid-chain in both directions with the
   inclusive boundary intact (including the tf exact
   cap), the tail hop still follows the exotic flat
   fees only, the stable-count-0 shift reproduces, the
   tiers-only rebuild still zeroes the tail fee, and
   the sweep/collect pipes still drain exactly -- and
   the tf100 cross, exotic333, count0, exotic0, and
   tf5000 cross legs match the corresponding no-mode
   5-hop tf legs of #41 and the 3-hop mode tf legs of
   #46 wherever the two overlap.
2. On the rebuilt images, every non-terminal cashback
   pool diverges under tf exactly as without it: the
   trade fails 6079 at the flagged hop with ghost
   events equal to the hops completed before it (0
   for main, 1 for POOL2, 2 for P3, 3 for P4 on buys, 4
   for main, 3 for POOL2 on sells), and the seed
   buckets still sweep/collect exactly afterwards,
   through the TOKEN22 pipes (protocol 2,488 -> 2,463,
   creator 123,394 -> 122,160, collect 120,938) as well
   as the SPL ones.
3. Mayhem gates every hop on all three images (6080),
   the terminal hop is cashback-gated on all three
   images (6079), and a mayhem tail pool's protocol
   sweep fails 6013 while its creator sweep/collect
   drain the seed -- all in agreement, tf included.
4. Mixed gates pin the hop order under tf at depth 5:
   buys execute head-first (head gate wins), sells
   execute tail-first (tail gate wins), and where the
   two orders disagree the original and rebuilt images
   report different errors at different hops (6080
   with 4 ghosts vs 6079 with 0 ghosts on
   main-cashback + tail-mayhem buys).

## Verification

Run `python3 verify.py` from this directory. It checks, from the
packet files alone (plus the three program images):

- MANIFEST.json lists every packet file with a matching sha256.
- runtime/report.json.gz: 27 cases, 177 receipts, 18 parts
  (17x10 + 7), part sha256/byte counts match the part files.
- Every receipt transaction parses (solders) and all signatures
  verify.
- Every receipt's recorded before/after snapshots reproduce the
  report's per-image expected values: fee-payer lamport deltas,
  the token-leg deltas, the Token-2022 withheld deltas,
  pool states, volume accumulator state, and decoded event
  fields.
- Failure steps roll back every watched account except the fee
  payer (fee 5,000) and carry the expected error code plus the
  recorded per-image site line in their logs. Site lines are
  checked per image, never compared across images, because
  original and rebuilt sources differ in line numbers.
- Control and candidate observed surfaces are identical in
  every case; the original surface differs exactly in the 18
  cases the report flags divergent, and verify.py checks that
  the computed divergence matches the flag.
- The three program images hash to the values recorded in the
  report.

## Limits

- Mode flags, feeconfig patches, and the transfer-fee schedule
  are applied to the fixture account data in the harness, not
  through a mode setter, `update_fee_config`, or a transfer-fee
  setter; the packet pins the gate, fee-table, and tf read
  paths, not the setters.
- The stable-count-0 mechanism is measured but not explained;
  no claim is made about which read path the count gates.
- The tail fee rate is reported as an observed accrual, not as
  a claimed formula: the exact rounding path through the curve
  feedback is not pinned here.
- Amounts are specific to the fixture reserves and the 10^9
  trade size; the split (hop 1 = tiers, tail = exotic), the
  gate positions, the hop order, and the tf pipe behavior are
  the general claims, the absolute numbers are not.
- No source change, no build, and no whole-binary identity
  claim is made. Control and candidate agree on every receipt
  surface in this packet; the original differs only in the 18
  flagged cases.
