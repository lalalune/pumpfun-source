# Split x boost x tf coin-creator reassignment boost chains at TRUE 5 hops

## Problem

The 3-hop packet showed that boost is coin-creator-blind, that a rerouted
creator sweep moves the main-pool boost burn by exactly +5,272,467 while
leaving hop-pool boost burns byte-identical, and that set/migrate gates
reproduce on hop pools. This packet extends those findings to a TRUE
5-hop split x boost x tf chain (three_amm + g4 + g5, final output U5),
and asks whether each result survives at depth 5: set no-op
boost-blindness, zero-to-set firing on the main pool and on P4/P5, the
rerouted sweep/collect then main boost, the migrate gates (6081
pre-sweep, 6048 post-migrate collect) on main/P4/P5, hop-pool
reassignment sweep sensitivity at depth 5, tf variants, and the
cashback claim gate after set.

Route verification: the builder's `build_route` calls `three_amm` and
then appends the g4 and g5 hop groups, so the buy runs
main -> P2 -> P3 -> P4 -> P5 and the sell runs the reverse; successful
swaps emit 5 hop events (the `events` count on every mhbuy5/mhsell5
step is 5). The name, this README, and the PR title all say 5 hops
because the route really is 5 hops (contrast the earlier 3-hop-named
packet whose route was actually 4 hops). Each hop pool carries proper
pool data (its own bump, pool-authority creator, base mint, and vaults),
not raw main-pool bytes, and each hop boost uses an SPL-derived ATA for
its hop quote mint (BA4S for BASE3, BA5S for BASE4).

## Cases

41 cases, 657 receipts (3 images each), 66 parts of 10 receipts
(65x10 + 7). Common parameters: tf100 unless stated, multi-hop
(10^9, 1), boost (10^9, 0), patched virtual_quote_reserves 10^9 on the
boosted pool, zero coin_creator patches where marked.

- A (5): main-pool set no-op against the patched-window boost:
  boost-set-boost, set-boost, buy-set-sweep-boost,
  buy-set-sweep-collect-boost, buy-boost-set-boost.
- B (5): zero main pool: boost, set-boost, buy-set-boost,
  set-sweep-collect-boost (rerouted to the NEW vault/destination),
  buy-set-sweep-collect-boost.
- C (5): main-pool migrate with sharing=CREATOR: buy-migrate-fail-boost,
  buy-sweep-collect-migrate-boost, migrate-boost-sharing-sweep-blocked-
  collect-boost, migrate-buy-boost, migrate-buy-sharing-sweep-boost.
- D (8): P4 reassignment: zero-P4 set4-boost, zero-P4 buy-set4-P4boost,
  zero-P4 set4-sweep-collect-P4boost, zero-P4 set4-buy-P4boost,
  P4 migrate-fail-boost, P4 sweep-collect-migrate-boost,
  P4 migrate-boost-sharing-sweep-blocked-collect-boost,
  P4 migrate-buy-P4boost (sharing4=CREATOR on the migrate cases).
- E (8): P5 reassignment, same shape as D with set5/migrate5 and
  sharing5=CREATOR.
- E2 (3): zero terminal creator: zero-P5 sell, zero-P5 buy-mainboost,
  zero-P4 sell (control).
- F (3): tf variants: zero-set-sweep-collect-boost at tf5000,
  migrate-boost at tf0, zero-P4 set4-boost at tf5000.
- G (4): cashback claim after set (tf0) on a set pool and on a zero
  pool, and set inside longer walks: buy-set-sell-boost,
  boost-set-sell-boost.

## Result

All 41 cases agree across original, control, and candidate: 0 divergent
cases. The 5-hop anchors match the earlier 5-hop packets: the mhbuy5
tail is 5,207,955,235,891 and the fresh 5-hop sell payout is 178,541
(buyback leg 837).

- Set no-op boost-blindness holds at depth 5. The patched-window main
  boost is 5,338,379,201,831; set on the already-set pool is a 0-event
  no-op with coin_creator unchanged, and the second boost is
  5,254,441,549,265. Set first then boost is still the anchor burn.
- Zero-to-set fires on main, P4, and P5 alike: the 144-byte metaplex
  event sets coin_creator to the zero address, and the next boost is
  the anchor burn (main 5,338,379,201,831; P4/P5 999,997,999). Post-buy
  hop burns with a normal creator are P4 989,528,958 and P5
  989,596,358; a buy made while P5 is still zero (fee waived, see
  below) boosts P5 at 989,593,786 instead, 2,572 less, while a buy made
  after set5 (creator already nonzero) boosts at the normal
  989,596,358.
- The rerouted main-pool sweep moves the next boost by exactly
  +5,272,467 at depth 5 as at 3 hops: sweep 122,160 (123,394 less
  withheld 1,234) and collect 120,938 to the NEW vault/destination,
  then the burn is 5,338,384,474,298; buy-set-sweep-collect-boost is
  5,254,685,098,328.
- Migrate gates reproduce on all three pools: migrate before sweeping
  fails 6081 (main, P4, P5); migrate after sweep+collect moves
  coin_creator to the pool's sharing-config PDA (main
  00227b4418b2609389185b46abad39b4e37f35940229a719bab852a8c0705960,
  P4 35d69ff080684f6356bd600e93bb9aeae2c57a75a69f000ff0e2a8a366cd2394,
  P5 8ac3f4689e86c8356eea3126cb79d8669261bbc832f1510e81f0634540b98682);
  collect after migrate fails 6048 on all three pools; the sharing
  sweep with a zero bucket is a 0-event no-op on all three.
- Hop-burn sweep sensitivity is NOT byte-identical at depth 5: it
  scales with sweep size. The P4 sweep of the fixture 123,394 moves
  the post-buy P4 boost by +1 (989,528,958 -> 989,528,959), and the
  P5 sweep of the terminal-hop accrual 2,617,733,408 (fixture 123,394
  plus the mhbuy5 terminal fee) moves the post-buy P5 boost by +2,576
  (989,596,358 -> 989,598,934). At 3 hops the same 123,394 sweep left
  the hop burn unchanged; at depth 5 it moves by one unit. The fresh
  P4/P5 boost after a rerouted sweep+collect is still the anchor
  999,997,999, and second-buy hop burns are P4 979,592,717 and P5
  979,826,191.
- NEW: a zero coin_creator on the terminal hop P5 silently waives the
  terminal-hop creator fee, in both directions. Buy with a zero P5:
  tail 5,210,540,474,900 (+2,585,239,009 vs the anchor tail) and the
  P5 bucket stays at the fixture 123,394 instead of accruing to
  2,617,733,408. Sell with a zero P5: payout 178,630 (+89 vs the
  anchor 178,541, buyback leg 838 vs 837) and the P5 bucket stays at
  123,394 instead of accruing to 623,394. The control sells with a
  zero P4: payout 178,541 and P5 accrual 623,394, both exactly the
  anchor values, so the waiver is terminal-hop-specific, not a
  general zero-creator effect. The waived fee does not move the main
  post-buy boost (5,254,679,949,141, the anchor post-buy burn),
  because the main vaults are unchanged.
- tf variants: tf5000 rerouted sweep nets 61,697 (half of 123,394
  withheld) and collect nets 30,848 (half of 61,697 withheld, 1-unit
  rounding), boost 2,706,769,696,611; tf0 boost after migrate is
  5,306,497,528,599; P4 boost after zero-to-set4 at tf5000 is the
  anchor hop burn 999,997,999 (tf-blind).
- Cashback claim after set still fails 2021 under the tf quote mint,
  on both the set pool and the zero pool: reassignment does not
  rescue it. Buy-set-sell-boost pays 189,218 and boosts at
  5,254,696,142,668; boost-set-sell-boost ends at 5,254,457,135,451.

## Limits

- All results are measured on the three program images (original,
  control, candidate) in the litesvm harness with the fixture pools
  and fee table; they are not a claim about any other program version
  or live state.
- The hop-burn sensitivity numbers (+1 for the 123,394 P4 sweep,
  +2,576 for the 2,617,733,408 P5 sweep) are measured at the fixture
  fee table and patched vq 10^9; the slope between sweep size and
  burn movement is not fitted here.
- The terminal-fee waiver is observed as a silent skip (the buy/sell
  succeeds with 5 hop events and the terminal bucket simply does not
  accrue); this packet does not identify the internal branch that
  skips it.
- Error-site lines live in each receipt row's `error_sites` field,
  never in `observed`, because original/rebuild line numbers differ.
- No source change is proposed.

Made via @slopdotcash
