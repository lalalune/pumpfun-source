# research: multi-hop fee-table split on mode pools at depth 4 — the split survives wherever the mode gate does not fire, and the rebuilt cashback gate diverges at every non-terminal hop

## Problem

3rd #37 pinned the multi-hop fee-table split with no mode flags:
hop 1 follows the cap-based fee-tier selection, the tail hop
follows the exotic flat fees, and a tiers-only feeconfig rebuild
silently zeroes the tail fee. 3rd #25/#26 pinned the multi-hop
mode gates on plain pools: the original image gates cashback
only at the terminal hop, while the rebuilt images gate it at
every hop; mayhem gates every hop on all three images. 3rd #43
closed the split x mode combination at depth 3, and 3rd #44
generalized it to depth 5. This packet is the even-hop check
of that combination at depth 4: does the split survive when
the pools carry mode flags at depth 4, and does the mode-gate
divergence hold at the even depth, including the depth-4
rounding observations already seen in 3rd #39/#42?

The route is main -> POOL2 -> P3 -> P4. P5 stays at fixture
state and is NOT part of the 4-hop route. Cashback / mayhem /
both-flags are set on individual pools, and the #39 fee
patches (tier crossing, exotic legs, stable-count,
tiers-only rebuild) are applied on top. The fee-tier rule is
the same as in 3rd #35/#36: the tier is the last tier whose
threshold is `<= cap`, where `cap = base_mint_supply *
effective_quote / vault_base`, the main pool's starting cap
is exactly 182,350,153,971, and the two custom tiers are
A = (lp 10, protocol 111, creator 333) and B = (lp 20,
protocol 222, creator 444).

## Cases

25 cases, 55 steps, 165 receipts (each step run on the
original, control (#424), and candidate (#427) images). All
amounts are token amounts unless noted. Pool state is
(virtual_quote_reserves i128, protocol_fees, creator_fees,
lp_supply). The fixture pools are main, POOL2, P3, P4, P5,
each (-125,882, 2,488, 123,394, 4,194,352,106,721) at setup.
The report flags 16 cases divergent (original vs rebuilt)
and 9 cases in agreement across all three images; control
and candidate agree in every case. The first successful
multi-hop step pays 1,849,400 lamports (1,844,400 rent for
the 137-byte volume accumulator plus the 5,000 fee); later
steps pay 5,000. Intermediate pools accrue nothing on any
image.

Family A -- hop-1 tier crossing under a non-terminal
cashback flag (divergent: the original crosses tiers, the
rebuilt images fail cashback 6079 at the flagged hop):

- `a-main-cb-cross`: main cashback, tiers [(100, A),
  (cap0 + 10^9, B)]. Original: buy1 pays A (tail out
  5,277,725,288,579, buyback 5,489,071, main protocol
  5,491,560), buy2 pays B (tail out 4,979,765,376,019,
  buyback 10,858,932, main protocol 16,350,492), tail
  sweep/collect drain 5,182,048,698. Rebuilt: 6079 with 0
  ghost events on both buys, then the seed sweep/collect
  drain 123,394 exactly.
- `a-p2-cb-cross`: POOL2 cashback, same tiers. Original:
  identical crossing legs. Rebuilt: 6079 with 1 ghost
  event on both buys (the hop completed before the flagged
  hop).
- `a-p3-cb-cross`: P3 cashback, same tiers. Rebuilt:
  6079 with 2 ghost events on both buys.
- `a-main-cb-exact`: main cashback, threshold set exactly
  to the post-buy1 cap (185,295,721,063). Original: buy2
  still pays B -- the inclusive boundary holds under the
  mode flag too. Rebuilt: 6079 with 0 ghosts on both buys.
- `a-main-cb-loop`: main cashback, same tiers, three buys.
  Original: buy A, buy B, buy B (third tail out
  4,756,579,132,460, buyback 10,858,932, main protocol
  27,209,424), tail sweep/collect drain 7,621,664,358.
  Rebuilt: 6079 with 0 ghosts on all three buys, then the
  seed sweep/collect drain 123,394 exactly.
- `a-p2-cb-sell`: POOL2 cashback, tiers at the mid-sell
  cap ((cap0 + post-sell1 cap) // 2 = 182,349,883,978),
  two sells. Original: sell1 pays B (user quote +177,996,
  buyback 2,021, tail creator 623,394), sell2 pays A (user
  quote +180,015, buyback 1,010). Rebuilt: 6079 with 2
  ghost events on both sells -- sells execute
  tail-first, so POOL2 is the third hop on sells.
- `a-main-cb-sell-cross`: main cashback, same mid-sell
  tiers, two sells plus tail sweep/collect. Original:
  identical sell legs, tail sweep/collect drain
  1,123,393. Rebuilt: 6079 with 3 ghost events on both
  sells (main is the last hop on sells), then the seed
  sweep/collect drain 123,394 exactly.

Family B -- tail exotic legs under a non-terminal cashback
flag (divergent: the original pays the exotic tail legs,
the rebuilt images fail cashback 6079 with 0 ghosts, then
the seed sweep/collect drain 123,394 exactly):

- `b-main-cb-exotic333`: main cashback, exotic flat fees
  (25, 5, 333). Original: tail creator bucket
  171,300,031,073 (about 64x the plain tail bucket),
  buyback 4,607,153.
- `b-main-cb-rebuild`: main cashback, tiers-only rebuild
  [(100, A)]. Original: the tail fee is zeroed (tail pool
  stays at its seed state), and the tail out equals the
  plain tier-A out exactly (5,277,725,288,579) -- unlike
  the 5-hop case, where the rebuild out was one token
  higher; the depth-4 rounding observation from 3rd #39
  holds under the mode flag too.
- `b-main-cb-count0`: main cashback, stable count 0.
  Original: tail creator bucket 1,065,570,632.
- `b-main-cb-exotic0`: main cashback, exotic flat fees
  (0, 0, 0). Original: the tail fee is zeroed (tail pool
  stays at its seed state), and the tail out is one token
  higher than the plain default out (5,286,914,075,405 vs
  5,286,914,075,404).

Family C -- sweep pipes under a non-terminal cashback flag
(divergent: the original buys and drains, the rebuilt
images fail cashback 6079, then the seed pipes drain
exactly):

- `c-main-cb-sweep`: main cashback, buy plus protocol
  sweep, creator sweep, collect on main. Original: buy
  leaves main protocol 4,609,642, protocol sweep drains
  it, creator sweep/collect drain the 123,394 seed.
  Rebuilt: 6079 with 0 ghosts on the buy, then the same
  three seed drains (protocol sweep 2,488, creator sweep
  123,394, collect 123,394).
- `c-p3-cb-sweep`: P3 cashback, buy plus creator sweep
  and collect on P3. Original: P3 accrues nothing (it is
  an intermediate pool), so its creator sweep/collect
  drain the 123,394 seed. Rebuilt: 6079 with 2 ghosts on
  the buy, then the same seed drains.

Family D -- mixed cashback/mayhem gates (divergent: the
original reports mayhem 6080 at the flagged hop, the
rebuilt images fail cashback 6079 at the head hop):

- `d-maincb-tailmayhem-buy`: main cashback, P4 mayhem.
  Original: 6080 with 3 ghost events (the three hops
  completed before the tail hop). Rebuilt: 6079 with 0
  ghosts.
- `d-maincb-p3mayhem-buy`: main cashback, P3 mayhem.
  Original: 6080 with 2 ghosts. Rebuilt: 6079 with 0
  ghosts.
- `d-p2cb-tailmayhem-buy`: POOL2 cashback, P4 mayhem.
  Original: 6080 with 3 ghosts. Rebuilt: 6079 with 1
  ghost.

Family E -- agreement cases (identical on all three
images):

- `e-tail-cb`: P4 cashback. 6079 with 3 ghosts -- the
  terminal hop is cashback-gated on all three images.
- `e-main-mayhem`: main mayhem. 6080 with 0 ghosts.
- `e-p2-mayhem`: POOL2 mayhem. 6080 with 1 ghost.
- `e-p3-mayhem`: P3 mayhem. 6080 with 2 ghosts.
- `e-tail-both`: P4 cashback and mayhem. 6079 with 3
  ghosts -- cashback wins at the terminal hop, as in
  3rd #32.
- `e-tail-cb-exotic`: P4 cashback with exotic flat fees
  (25, 5, 333). 6079 with 3 ghosts -- exotic legs do not
  rescue a gated tail hop.
- `e-tail-mayhem-sweep`: P4 mayhem, buy plus protocol
  sweep, creator sweep, collect on P4. Buy fails 6080
  with 3 ghosts, protocol sweep fails 6013 (a mayhem
  pool has no protocol bucket to sweep), creator
  sweep/collect drain the 123,394 seed.
- `e-order-sell-tail-first`: main cashback, P4 mayhem,
  one sell. 6080 with 0 ghosts on all images -- sells
  execute the tail hop first.
- `e-order-buy-head-first`: main mayhem, P4 cashback,
  one buy. 6080 with 0 ghosts on all images -- buys
  execute the head hop first.

## Result

At depth 4 the split survives wherever the mode gate does
not fire: a non-terminal cashback pool still pays the
tier-crossed hop-1 legs (including the inclusive exact
boundary), the exotic tail legs, the tiers-only rebuild
zeroing, and the stable-count shift, and the sweep/collect
pipes still drain exactly. The rebuilt cashback gate
diverges at every non-terminal hop, with ghost-event
counts that pin the hop order: buys run head-first
(main 0, POOL2 1, P3 2, P4 3), sells run tail-first
(P4 0, P3 1, POOL2 2, main 3). Mixed gates show the
same order from the other side: the original reports
mayhem at the flagged hop while the rebuilt images fail
cashback at the head hop, and the two order-pinning cases
show sells failing at the tail hop and buys failing at
the head hop on all three images. After a rebuilt
failure, the seed buckets still sweep/collect exactly
(2,488 protocol, 123,394 creator). The depth-4 rounding
observations reproduce under the mode flag: the
tiers-only rebuild tail out equals the plain tier-A out
exactly, while the exotic-zero tail out is one token
higher than the plain default out. Control (#424) and
candidate (#427) agree in every case.

## Verification

`verify.py` re-checks, from the packet files alone plus
the three program images: MANIFEST sha256 for every file,
report counts (25 cases, 165 receipts, 17 parts) and part
hashes/sizes, signature verification of every receipt
transaction, per-image expected values (fee-payer lamport
deltas, token-leg deltas, five pool states, volume
accumulator state, decoded event fields), failure
rollback (every watched account unchanged except the fee
payer), error codes plus the recorded per-image site line
in the logs, control == candidate everywhere, and the
report's divergent flag matching the computed comparison
(16 divergent, 9 in agreement). Site lines are checked
per image, never compared across images, because original
and rebuilt sources differ in line numbers.

## Limits

- The packet pins behavior, not intent: it does not claim
  the original's terminal-only cashback gate is a bug, nor
  that the rebuilt every-hop gate is one. It records the
  observable difference and the exact hop at which each
  image fails.
- All legs use the synthetic fixture pools and the
  1,000,000,000-unit input; real pools with different
  reserves, tiers, or flags may behave differently.
- No source change, no build, and no claim of whole-program
  equivalence is made. The three images are the deployed
  original, control (#424), and candidate (#427) binaries
  only.
- The mayhem gate map itself is not re-derived here: the
  mayhem cases pin the observable gate positions (6080
  with the ghost counts above) on the three images.
