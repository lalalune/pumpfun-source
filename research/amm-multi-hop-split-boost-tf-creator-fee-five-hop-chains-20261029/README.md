# research: multi-hop creator fee is terminal-hop only at true 5 hops — P5 is the lever both directions, main/P2/P3/P4 inert, P5 10000 sell overflows

3rd-run packet #120: the split x boost x tf chain at TRUE 5 hops
(`three_amm` + g4 + g5, final output U5) meets creator fees. This is
the 5-hop extension of #115, not a re-measure: #115 pinned the rule
on 3 hops (buys charge creator on the LAST hop, sells on the FIRST
hop, the main pool's `creator_fee_bps` is inert on the route). The
question here is whether the rule scales when the terminal hop moves
from P3 to P5: does the lever move with it in both directions, does
a P5 10000 sell overflow the way the P3 10000 sell did, and does the
boost burn still read buckets rather than the rate at depth 5?

Route confirmation (from the builder itself): the fixture route
calls `three_amm` and appends g4 and g5 hop groups — 5 hop groups,
final output U5, and 5 hop events on every successful swap. This
packet does not repeat 3rd #61's naming error (a "3-hop" packet
whose builder actually appended a P4 group). Routed hop pools carry
proper pool data (bump, pool-authority creator, their base mints,
their vaults), as #119 established: raw main-pool bytes on a routed
hop fail 6008.

## Problem

On a multi-hop route, which pool's `creator_fee_bps` actually charges
the creator fee? The pool field (pool bytes 261..269) overrides the
fee-table creator bps whenever `GlobalConfig.creator_fee_configurable`
is set and the pool value is nonzero (`curve/fees.rs`,
`select_and_apply_v2`). But the multi-hop fee gates charge the
creator fee only at one hop per direction
(`instructions/swap/multi_hop_swap.rs`: buys charge creator on the
LAST hop, sells on the FIRST hop). On the 3-hop route #115 found the
lever is P3 in both directions (buys: last hop P3; sells: first
executed hop P3). At 5 hops the buy terminal hop is P5 and the sell
first-executed hop is also P5 — so the prediction is that P5 alone
is the lever in both directions, and main/P2/P3/P4 are inert. This
packet tests that prediction, plus the P5 10000 sell, the boost burn
after a P5-fee buy, P5 sweep/collect walks, the configurable gate
and the real `update_creator_fee_config` setter, and tf variants.

The real `admin_cto_pool` setter is NOT used here: it requires the
pool-authority PDA as a transaction signer, which no harness
transaction can supply, and it additionally requires
`pool.creator_fees == 0` first. Creator-fee values in this packet
are set with harness field resets (`cpatch` steps, recorded with an
empty transaction and never presented as on-chain instructions),
except for the `update_creator_fee_config` cases, which are real
instructions. The fixture pools have `creator_fee_bps` 0, so the
fee-table creator bps (5 bps on this tier) applies until patched.

## Cases

48 cases, 375 receipts (125 steps x 3 images), 38 parts of 10
receipts (37x10 + 5). All amounts are for a 10^9 quote buy / 10^9
base sell unless noted; `tf100` unless noted.

- A anchors (5): buy, sell, boost, buy-then-boost, boost-then-buy.
- B hop-pool creator-fee ladder, buys (6): main / P2 / P3 / P4 300
  buys, P5 300 buy, P5 10000 buy.
- C buys at a creator fee, then a main boost (3): main 300, P5 300,
  P5 10000.
- D sells at a creator fee (4): main 300, P4 300, P5 300, P5 10000.
- E mid-walk P5 creator-fee edits (4): buy, patch P5 to 300, buy,
  boost; boost, patch P5 to 300, buy, boost; P5 300 buy, patch P5
  to 0 / 10000, buy, boost.
- F configurable gate and the real setter (6): P5 300 with
  configurable off / on; `update_creator_fee_config` off (0, 300)
  and on (1, 10000) then a P5 300 buy; outsider and unsigned setter
  then a buy.
- G GlobalConfig `creator_fee` field alone (2): patched to 0 and
  to 10000, then buy-then-boost.
- H P5 creator sweep/collect after a buy (3): P5 300 buy, P5
  creator sweep, collect, main boost; P5 300 buy, P5 protocol
  sweep, main boost; 0 buy, P5 creator sweep, collect, main boost.
- I P5 boosts after a creator-fee buy (4): P5 300 buy then P5
  boost; P5 10000 buy then P5 boost; main 300 buy then P5 boost;
  P5 boost anchor (P5 window patched open, no buy).
- J tf variants under a P5 creator fee (2): P5 300 buy at tf0 and
  at tf5000, then a main boost.
- K single-pool legs under a creator fee (2): legacy buy and v2
  buy on the main pool at 300.
- L walks under a P5 creator fee (4): buy-sell-boost, sell-boost,
  buy-buy-boost, boost-boost.
- M terminal-hop sells, then boosts (3): P5 300 sell then boost;
  P5 10000 sell then boost; P5 300 buy, P5 boost, main boost.

## Result

All 48 cases agree on original, control and candidate (0 divergent
cases). The creator fee on this route is a terminal-hop fee only,
and the terminal hop moved from P3 to P5 exactly as predicted:

- Anchors: buy tail 5,207,955,235,891 (buyback leg 4,515,471 +
  withheld 45,611, the #119/#62 5-hop anchor); sell payout 178,541
  (leg 837); main boost burn 5,338,379,201,831; buy-then-boost burn
  5,254,679,949,141; boost-then-buy tail 5,087,534,167,771.
- Main, P2, P3 and P4 creator fees are inert on buys: at 300 each,
  the buy tail stays 5,207,955,235,891. Only P5 moves it: P5 300
  cuts the tail to 5,059,837,684,614 (down 148,117,551,277) and
  fills the P5 creator bucket to 152,567,218,652 (from the anchor
  2,617,733,408 at the fee-table 5 bps). P5 10000 roughly halves
  the tail to 2,614,678,042,767 with a P5 creator bucket of
  2,621,532,629,315.
- Sells charge creator at the first-executed hop, which at depth 5
  is also P5: main 300 sell pays the anchor 178,541, P4 300 sell
  pays the anchor 178,541, P5 300 sell pays 173,260 (P5 creator
  bucket 30,123,364 — the same bucket #115 measured for the P3
  300 sell, while the payout differs by 1 from #115's 173,261,
  a depth effect reported as measured). P5 10000 sell fails the
  whole sell with Overflow 6023 and full rollback (0 events):
  a 100% first-hop creator fee overflows the sell computation
  instead of paying zero, exactly as the P3 10000 sell did.
- The main boost burn does NOT read the creator fee rate: it reads
  the buckets. A P5 300 buy followed by a MAIN boost burns the
  anchor post-buy 5,254,679,949,141, and so does a P5 10000 buy
  followed by a main boost, because P5 fees never touch main
  buckets. The second-buy burn is identical (5,172,933,848,347)
  whether the second buy ran under P5 300, P5 0, or P5 10000.
  Boost, patch P5 to 300, buy, boost burns 5,173,028,765,024 (the
  #112 boost-buy-boost value).
- Configurable gate: P5 300 with `creator_fee_configurable` off
  falls back to the fee-table creator bps exactly (buy tail
  5,207,955,235,891, P5 creator bucket 2,617,733,408). The real
  `update_creator_fee_config` writes configurable/max (off:
  0/300, on: 1/10000); an outsider setter fails 6005 and an
  unsigned setter fails 3010, both with full rollback, and the
  following buy is the P5 300 tail in both cases (the fixture
  config stays configurable=1, max=300).
- The GlobalConfig `creator_fee` field (313..321) alone moves
  nothing: patched to 0 or 10000, the buy tail and the
  buy-then-boost burn are anchor-identical.
- P5 sweeps discharge in full but never move the MAIN boost: a P5
  300 buy's creator sweep pays the full 152,567,218,652 to the
  P5 creator ATA and the collect pays it in full to the
  destination, yet the following main boost is still the anchor
  post-buy burn; the P5 protocol sweep discharges the fixture
  2,488 with the same result. The cf0 buy's P5 creator sweep
  discharges 2,617,733,408, again with the anchor post-buy burn
  after it.
- P5 boosts need the SPL-derived ATA, not the Token-2022 one.
  The first build used the Token-2022-derived boost ATA (BA5)
  and every P5 boost failed IncorrectProgramId, including the
  anchor — the same 2x2 shape #103 pinned for the main pool,
  here with the hop pool's SPL quote mint: the boost quote leg
  must match the mint's program, so the SPL-derived ATA (BA5S)
  is the one that burns. P5 boost anchor 999,997,999 (the #111
  hop anchor); main 300 buy then P5 boost 989,596,358; P5 300
  buy then P5 boost 989,743,701 (the main-buy P5 boost +
  147,343: the enlarged P5 creator bucket nudges the P5 burn,
  as #115's +148,882 nudged the P3 burn); P5 10000 buy then P5
  boost 992,176,090. A P5 boost does not move the following main
  boost (still 5,254,679,949,141).
- tf variants under a P5 300 fee: tf0 buy tail 5,109,477,485,375
  then boost 5,306,492,329,463; tf5000 buy tail 2,592,005,765,796
  then boost 2,685,165,599,125. The tf ordering from #106/#112
  holds; the creator fee does not change it.
- Single-pool legs DO charge the main pool creator fee, unlike
  the multi-hop route: a legacy buy at 300 pays the same as in
  #115 (quote 191,550 for 10^9 base), while a v2 buy at 300
  accrues 5,475 to the pool creator bucket (128,869 from
  123,394; quote paid 191,614). Same rate, different destination.
- Walks: P5 300 buy-sell-boost ends at 5,254,695,659,101 (sell
  payout 183,568); P5 300 sell-boost ends at 5,338,394,385,335;
  P5 300 buy-buy-boost ends at 5,172,933,848,347 (second tail
  4,779,600,400,262); P5 300 boost-boost second burn is
  5,254,441,549,265. A failed P5 10000 sell leaves no residue:
  the following main boost is the anchor 5,338,379,201,831.

## Limits

- Creator-fee values on multi-hop pools are harness field resets,
  not the `admin_cto_pool` setter (PDA-signer-gated, see Problem).
  The setter's own gates are therefore not measured here; only
  `update_creator_fee_config` is exercised as a real instruction.
- The "terminal hop" rule is measured on this exact route
  (main -> POOL2 -> P3 -> P4 -> P5, buys and sells). Other routes
  charge the creator fee at their own terminal hop by the same
  gate code.
- The P5 10000 sell Overflow (6023) is measured at a 10^9 base
  sell with the fixture reserves; the overflowing computation is
  not narrowed to a single arithmetic site by these receipts.
- The P5 boost SPL-ATA requirement is a fixture property (the hop
  quote mint BASE4 is an SPL mint); on a chain where the hop quote
  mint is Token-2022, the Token-2022-derived ATA would be the one
  that burns, by the same #103 matrix.
- No source change is proposed by this packet.

Made via @slopdotcash
