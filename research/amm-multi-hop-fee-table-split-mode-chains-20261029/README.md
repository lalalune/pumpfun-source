# research: multi-hop fee-table split on mode pools — the split survives wherever the mode gate does not fire, and the rebuilt cashback gate diverges at every non-terminal hop

## Problem

3rd #37 pinned the multi-hop fee-table split with no mode flags:
hop 1 follows the cap-based fee-tier selection, the tail hop
follows the exotic flat fees, and a tiers-only feeconfig rebuild
silently zeroes the tail fee. 3rd #25 pinned the multi-hop mode
gates on plain pools: the original image gates cashback only at
the terminal hop, while the rebuilt images gate it at every hop;
mayhem gates every hop on all three images. This packet closes
the combination: does the split survive when the pools carry
mode flags, and does the mode-gate divergence survive when the
route also crosses fee tiers and exotic legs?

The route is the 3-hop route of 3rd #37 (main -> POOL2 -> P3).
Cashback / mayhem / both-flags are set on individual pools, and
the #37 fee patches (tier crossing, exotic legs, stable-count,
tiers-only rebuild) are applied on top. The fee-tier rule is the
same as in 3rd #35/#36: the tier is the last tier whose threshold
is `<= cap`, where `cap = base_mint_supply * effective_quote /
vault_base`, the main pool's starting cap is exactly
182,350,153,971, and the two custom tiers are A = (lp 10,
protocol 111, creator 333) and B = (lp 20, protocol 222,
creator 444).

## Cases

21 cases, 48 steps, 144 receipts (each step run on the original,
control (#424), and candidate (#427) images). All amounts are
token amounts unless noted. Pool state is
(virtual_quote_reserves i128, protocol_fees, creator_fees,
lp_supply). The fixture pools are main, POOL2, P3, each
(-125,882, 2,488, 123,394, 4,194,352,106,721) at setup. The
report flags 13 cases divergent (original vs rebuilt) and 8
cases in agreement across all three images; control and
candidate agree in every case.

Family A -- hop-1 tier crossing under a non-terminal cashback
flag (divergent: the original crosses tiers, the rebuilt
images fail cashback 6079 at the flagged hop):

- `a-main-cb-cross`: main cashback, tiers [(100, A),
  (cap0 + 10^9, B)]. Original: buy1 pays A (out 5,305,797,837,698,
  buyback 5,489,071, main protocol 5,491,560), buy2 pays B (out
  5,058,267,896,137, buyback 10,858,932, main protocol
  16,350,492), tail sweep/collect drain 5,236,452,906. Rebuilt:
  6079 with 0 ghost events on both buys, then the seed
  sweep/collect drain 123,394 exactly.
- `a-p2-cb-cross`: POOL2 cashback, same tiers. Original:
  identical crossing legs. Rebuilt: 6079 with 1 ghost event on
  both buys (the hop completed before the flagged hop).
- `a-main-cb-exact`: main cashback, threshold set exactly to
  the post-buy1 cap (185,295,721,063). Original: buy2 still pays
  B -- the inclusive boundary holds under the mode flag too.
  Rebuilt: 6079 with 0 ghosts on both buys.
- `a-main-cb-loop`: main cashback, same tiers, three buys.
  Original: buy A, buy B, buy B (third out 4,879,443,310,227,
  buyback 10,858,932, main protocol 27,209,424), tail
  sweep/collect drain 7,739,937,932. Rebuilt: 6079 with 0
  ghosts on all three buys, then the seed drain.
- `a-p2-cb-sell`: POOL2 cashback, tiers set midway between cap0
  and the post-sell1 cap. Original: sell1 pays B (receipt
  177,996, buyback 2,021), sell2 pays A (receipt 180,016,
  buyback 1,010). Rebuilt: 6079 with 1 ghost event on both
  sells.
- `a-main-cb-sell-cross`: main cashback, same sell tiers.
  Original: sell B -> sell A, tail sweep/collect drain
  1,123,393. Rebuilt: 6079 with 2 ghost events on both sells
  (sells execute the tail hop first, so the main gate is last).

Family B -- the tail hop follows the exotic flat fees under a
non-terminal cashback flag (divergent: the original pays the
exotic tail legs, the rebuilt images fail at the head hop):

- `b-main-cb-exotic333`: main cashback, exotic (25, 5, 333).
  Original: tail creator 172,217,658,022, sweep/collect drain
  it exactly. Rebuilt: 6079 with 0 ghosts, then the seed drain.
- `b-main-cb-rebuild`: main cashback, feeconfig rebuilt with
  tiers only [(100, A)] (stable and exotic zeroed, as the 3rd
  #35/#36 builders did). Original: hop 1 pays A exactly
  (buyback 5,489,071, main protocol 5,491,560) but the tail
  creator bucket collapses to the seed 123,394 -- the rebuild
  trap survives the mode flag. Rebuilt: 6079 with 0 ghosts,
  then the seed drain.
- `b-main-cb-count0`: main cashback, stable count set to 0
  (stable entries left in place). Original: tail creator
  1,071,278,067, sweep/collect drain it exactly -- the
  count-field shift reproduces under the mode flag (mechanism
  not asserted). Rebuilt: 6079 with 0 ghosts, then the seed
  drain.
- `b-main-cb-exotic0`: main cashback, exotic (0, 0, 0).
  Original: tail creator stays at the seed 123,394, tail out
  5,315,084,721,959 (+1 vs default) -- the tail fee is exactly
  zero. Rebuilt: 6079 with 0 ghosts, then the seed drain.

Family C -- sweep pipes under a non-terminal cashback flag
(divergent):

- `c-main-cb-sweep`: main cashback, default config, one buy
  then protocol sweep, creator sweep, collect. Original:
  protocol sweep 4,609,642, creator sweep 123,394, collect
  123,394 (main pool ends at (0, 0, 0)). Rebuilt: the buy
  fails 6079 with 0 ghosts, then the seed protocol sweep
  2,488, creator sweep 123,394, collect 123,394 -- the pipes
  drain the seed exactly on both sides.

Family D -- mixed cashback/mayhem gates (divergent: different
error code AND different ghost count):

- `d-maincb-tailmayhem-buy`: main cashback + tail mayhem, one
  buy. Original: 6080 with 2 ghost events (the mayhem tail
  gate fires after two completed hops). Rebuilt: 6079 with 0
  ghosts (the cashback head gate fires first).
- `d-maincb-p2mayhem-buy`: main cashback + POOL2 mayhem, one
  buy. Original: 6080 with 1 ghost event. Rebuilt: 6079 with
  0 ghosts.

Family E -- agreement cases (all three images identical):

- `e-tail-cb`: tail cashback, one buy: 6079 with 2 ghosts on
  all images -- the terminal hop is cashback-gated everywhere.
- `e-main-mayhem`: main mayhem, one buy: 6080 with 0 ghosts on
  all images.
- `e-p2-mayhem`: POOL2 mayhem, one buy: 6080 with 1 ghost on
  all images.
- `e-tail-both`: tail both-flags, one buy: 6079 with 2 ghosts
  on all images -- at the terminal hop cashback wins
  everywhere.
- `e-tail-cb-exotic`: tail cashback + exotic (25, 5, 333),
  one buy: 6079 with 2 ghosts on all images -- exotic legs do
  not rescue a gated tail hop.
- `e-tail-mayhem-sweep`: tail mayhem, buy then protocol
  sweep, creator sweep, collect. The buy fails 6080 with 2
  ghosts, the protocol sweep fails 6013 with 0 events (the
  mayhem gate reaches the sweep handler), and the creator
  sweep/collect drain the seed 123,394 -- all on all images.
- `e-order-sell-tail-first`: main cashback + tail mayhem, one
  sell: 6080 with 0 ghosts on all images -- sells execute the
  tail hop first, so the tail mayhem gate fires before the
  main cashback gate on every image.
- `e-order-buy-head-first`: main mayhem + tail cashback, one
  buy: 6080 with 0 ghosts on all images -- buys execute the
  head hop first, so the head mayhem gate fires before the
  tail cashback gate on every image.

## Result

The fee-table split and the mode gates compose without
interference, on the original image and (by failing) on the
rebuilt images:

1. On the original image, a non-terminal cashback pool does
   not disturb the split: hop 1 still crosses tiers mid-chain
   in both directions with the inclusive boundary intact, the
   tail hop still follows the exotic flat fees only, the
   stable-count-0 shift reproduces, the tiers-only rebuild
   still zeroes the tail fee, and the sweep/collect pipes
   still drain exactly.
2. On the rebuilt images, every non-terminal cashback pool
   diverges: the trade fails 6079 at the flagged hop with
   ghost events equal to the hops completed before it (0 for
   main, 1 for POOL2 on buys, 2 for main on sells), and the
   seed buckets still sweep/collect exactly afterwards.
3. Mayhem gates every hop on all three images (6080), the
   terminal hop is cashback-gated on all three images (6079),
   and a mayhem tail pool's protocol sweep fails 6013 while
   its creator sweep/collect drain the seed -- all in
   agreement.
4. Mixed gates pin the hop order: buys execute head-first
   (head gate wins), sells execute tail-first (tail gate
   wins), and where the two orders disagree the original and
   rebuilt images report different errors at different hops
   (6080 with 2 ghosts vs 6079 with 0 ghosts on
   main-cashback + tail-mayhem buys).

## Verification

Run `python3 verify.py` from this directory. It checks, from the
packet files alone (plus the three program images):

- MANIFEST.json lists every packet file with a matching sha256.
- runtime/report.json.gz: 21 cases, 144 receipts, 15 parts
  (14x10 + 4), part sha256/byte counts match the part files.
- Every receipt transaction parses (solders) and all signatures
  verify.
- Every receipt's recorded before/after snapshots reproduce the
  report's per-image expected values: fee-payer lamport deltas,
  the token-leg deltas, pool states, volume accumulator state,
  and decoded event fields.
- Failure steps roll back every watched account except the fee
  payer (fee 5,000) and carry the expected error code plus the
  recorded per-image site line in their logs. Site lines are
  checked per image, never compared across images, because
  original and rebuilt sources differ in line numbers.
- Control and candidate observed surfaces are identical in
  every case; the original surface differs exactly in the 13
  cases the report flags divergent, and verify.py checks that
  the computed divergence matches the flag.
- The three program images hash to the values recorded in the
  report.

## Limits

- Mode flags and feeconfig patches are applied to the fixture
  account data in the harness, not through a mode setter or
  `update_fee_config`; the packet pins the gate and fee-table
  read paths, not the setters.
- The stable-count-0 mechanism is measured but not explained;
  no claim is made about which read path the count gates.
- The tail fee rate is reported as an observed accrual, not as
  a claimed formula: the exact rounding path through the curve
  feedback is not pinned here.
- Amounts are specific to the fixture reserves and the 10^9
  trade size; the split (hop 1 = tiers, tail = exotic), the
  gate positions, and the hop order are the general claims,
  the absolute numbers are not.
- No source change, no build, and no whole-binary identity
  claim is made. Control and candidate agree on every receipt
  surface in this packet; the original differs only in the 13
  flagged cases.
