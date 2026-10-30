# research: split x boost x tf admin setter chains at TRUE 5 hops

## Problem

Packet #71 showed, at a TRUE 3-hop route, that the four admin
setters (`update_buyback_config`, `update_fee_config`, the mode
toggles, and `disable`) bind to a live split chain in specific
ways: the buyback bps ladder scales the buyback leg linearly while
the tail never moves, the fee-config rewrite leaves the split chain
byte-identical, the global mode flags are separate from the pool
flags, and all four disable bits bind with exact recovery. This
packet extends every one of those measurements to a TRUE 5-hop
route (main -> POOL2 -> P3 -> P4 -> P5, final output U5): does the
buyback ladder still scale the leg while the 5-hop tail stays put,
does the fee-config rewrite still leave the 5-hop buy, sell, sweep,
collect and boost byte-identical, do the toggles and the
global-vs-pool flag separation still hold at depth 5, do the
disable bits still bind the 5-hop legs and the boost, and does
setter ordering against buy/boost matter at depth 5?

Route verification: the builder's `build_route` calls `three_amm`
and then appends the g4 and g5 hop groups, so the buy runs
main -> P2 -> P3 -> P4 -> P5 and the sell runs the reverse;
successful swaps emit 5 hop events. The name, this README, and the
PR title all say 5 hops because the route really is 5 hops
(contrast the earlier 3-hop-named packet whose route was actually
4 hops). Each hop pool carries proper pool data (its own bump,
pool-authority creator, base mint, and vaults), not raw main-pool
bytes, and each hop boost uses an SPL-derived ATA for its hop quote
mint (BA4S for BASE3, BA5S for BASE4). The quote mint carries a
per-case transfer-fee config (100 bps unless stated) and the split
legs route the buyback through the TOKEN22 ATA. The GlobalConfig
buyback baseline is 5000 bps in every case unless a setter changes
it.

## Cases

42 cases, 330 receipts, 33 parts (33x10), across original, control
and candidate images. The 5-hop buy tail anchor is 5,207,955,235,891
and the buy-then-boost anchor burn is 5,254,679,949,141.

- A (11): buyback config at depth 5: anchor buy-sweep-collect;
  bps 7500 then buy-sweep-collect; bps 10000 then buy; bps 0 then
  buy; bps 10001 (rejected) then buy; recipients excluding the
  fixture buyback owner then buy; outsider setter; unsigned
  setter; bps None + no recipients (silent no-op) then buy;
  bps 7500 then buy then boost; bps 7500 then sell.
- B (6): fee config at depth 5: lp 30 / proto 40 / creator 100 /
  sorted recipients / new authority then buy-sweep-collect;
  unsorted recipients (rejected) then buy; lp 1001 with unsorted
  recipients (rejected); outsider setter; the rewrite then buy
  then boost; the rewrite then sell.
- C (8): toggles at depth 5: mayhem off twice; cashback off
  twice; boost same-state True; outsider mayhem toggle; boost
  toggle off then boost then toggle on then boost; buy on a
  cb-flagged P4 (anchor); global cashback off then buy on a
  cb-flagged P4; global mayhem off then buy on a mayhem-flagged
  P4.
- D (7): disable at depth 5: buy bit then buy then clear then
  buy; sell bit then sell then clear then sell; deposit bit then
  deposit then clear then deposit; withdraw bit then withdraw
  then clear then withdraw; buy bit then patched-window boost
  then clear then buy; all-bits then buy then clear then buy;
  patched-window buy control (no disable bit).
- E (6): neutrality, creator-fee config, ordering at depth 5:
  no-op setter trio then buy then boost; creator-fee-config off
  then buy; creator-fee-config outsider; creator-fee-config
  unsigned; buy then bps 7500 then boost; buy then fee-config
  rewrite then boost.
- F (4): tf variants at depth 5: bps 7500 then buy at tf5000;
  bps 7500 then buy at tf0; fee-config rewrite then buy at
  tf5000; buy bit then buy then clear then buy at tf5000.

## Result

Control and candidate agree on every case. Original agrees on
every case except the two marked divergent cases below (the
rebuild cashback divergence, not a setter difference).

- Buyback bps ladder at depth 5: the leg scales exactly with bps
  and the tail never moves. Baseline (5000): leg 4,515,471, hop-1
  credit 985,438,918, tail 5,207,955,235,891. 7500: leg 6,773,206,
  credit 983,158,377, tail unchanged. 10000: leg 9,030,942,
  credit 980,877,836, tail unchanged. 0: no leg, credit
  990,000,000, tail unchanged. The leg values are identical to
  the 3-hop ladder in #71 -- the hop-1 credit split does not
  depend on route depth. The setter itself emits no event and
  only rewrites GlobalConfig bytes 899..907 (bps) or 643..899
  (recipients).
- Buyback setter gates at depth 5: bps 10001 fails 6056 with full
  rollback and the following buy is the anchor. Recipients
  excluding the fixture buyback owner fail the following buy
  6053 with 0 events. Outsider fails 6005, unsigned fails 3010,
  both with no config change. bps None + no recipients succeeds
  silently with no config change and the following buy is the
  anchor.
- NEW -- setter-before-buy moves the post-buy burn, tail or no
  tail: bps 7500 then buy then boost burns 5,254,775,116,926,
  which is the anchor burn 5,254,679,949,141 + 95,167,785. The
  burn reads the hop-1 credit the buy actually accrued, so a
  setter that changes the buy's credit changes the following
  burn even though the tail is untouched. The sell side scales
  too: bps 7500 sell leg is 1,256 (anchor sell leg 837 x 1.5,
  ceil).
- Fee-config rewrite at depth 5: the setter (lp 30, proto 40,
  creator 100, sorted recipients, authority `6363...63`) succeeds
  with a 1-event step and rewrites GlobalConfig, yet the
  following 5-hop buy (tail 5,207,955,235,891, leg 4,515,471),
  sweep (discharge 123,394, net 122,160, withheld 1,234),
  collect (net 120,938, withheld 1,222), sell (leg 837) and
  post-buy boost (5,254,679,949,141) are all byte-identical to
  the anchor: the split chain prices off feeconfig tiers, not
  the global lp/proto/creator bps, at depth 5 as at 3 hops.
- Fee-config gates at depth 5: unsorted recipients fail 6012 with
  no config change and the following buy is the anchor. lp 1001
  with unsorted recipients fails 6000, not 6012: the bps bound
  is checked before recipient ordering. Outsider fails 6005
  with no config change.
- Toggles at depth 5: mayhem True -> False rewrites GlobalConfig
  byte 417 (1 -> 0); a second False fails 6043. Cashback True ->
  False rewrites byte 642 (1 -> 0); a second False fails 6051.
  Boost True -> True succeeds silently with no config change:
  unlike mayhem/cashback, `toggle_boost` has no same-state
  check. Outsider toggle fails 6005. Toggles emit no event.
  Boost toggle off fails the patched-window boost 6066, and
  toggling back on restores the anchor burn 5,338,379,201,831.
- Global flags are separate from pool flags at depth 5: a buy on
  a mayhem-flagged P4 fails 6080 with 3 ghosts on all three
  images even with the global mayhem flag off -- the mayhem gate
  is per-hop on every image and does not consult the global flag.
- DIVERGENT (2 cases, rebuild difference, not a setter
  difference): a buy on a cb-flagged P4 succeeds on the original
  (5 hop events, anchor tail) and fails 6079 with 3 ghosts on
  control and candidate, whether the global cashback flag is on
  or off. The rebuild's per-hop cashback gate does not consult
  the global flag either. This is the same divergence seen in
  #71/#109/#119.
- Disable bits at depth 5: buy bit (disable byte 0 -> 8) fails
  the 5-hop buy 6020; sell bit (0 -> 16) fails the 5-hop sell
  6021; deposit bit (0 -> 2) fails deposit 6018; withdraw bit
  (0 -> 4) fails withdraw 6019; all-bits (31) fails the buy 6020
  (the buy bit dominates). Clearing the bits restores the anchor
  chain byte-identically in every case: recovery buy tail
  5,207,955,235,891, recovery sell leg 837, recovery deposit
  (user base -160,619,896, quote -29,610, LP +1,000,000),
  recovery withdraw (user base +160,619,895, quote +29,018,
  LP -1,000,000). Disable emits a 1-event step. Boost under the
  buy bit fails 6020: boost routes through an internal buy, so
  the buy gate applies to it too.
- The D-dis-buy-boost recovery buy tail is 5,167,125,538,753,
  not the fresh anchor -- and that is the VQ patch, not the
  disable bit: the case patches vq to 10^9 before the failed
  boost, so the recovery buy runs against the patched window.
  The standalone VQ-patch control buy gives exactly
  5,167,125,538,753, pinning the difference to the patch.
- Setter neutrality at depth 5: the no-op setter trio (buyback
  None, boost same-state True, disable all false) leaves the
  5-hop buy (tail 5,207,955,235,891) and boost
  (5,254,679,949,141) byte-identical to the anchor. Setters
  themselves do not move prices; only a setter that changes
  what a later buy accrues moves the following burn.
- Creator-fee config at depth 5: setting configurable off
  (byte 940: 1 -> 0, max 300 unchanged) leaves the 5-hop buy
  byte-identical (anchor tail, anchor leg). Outsider fails
  6005, unsigned fails 3010, both with configurable still 1.
- Setter ordering at depth 5: buy then bps 7500 then boost burns
  the anchor 5,254,679,949,141 -- the setter after the buy does
  not move the burn, because the buy already accrued its leg
  under bps 5000. Buy then fee-config rewrite then boost is
  likewise the anchor burn. Only a setter before the buy moves
  the following burn, via the buy's accrued credit.
- Tf variants at depth 5: bps 7500 at tf5000 gives tail
  2,668,075,748,732 (the tf5000 anchor tail) with leg 1,727,682;
  at tf0 the tail is 5,259,040,470,738 with leg 6,910,730.
  Fee-config rewrite at tf5000 leaves the tf5000 buy
  byte-identical (tail 2,668,075,748,732, leg 1,151,788). Buy
  bit at tf5000 fails the buy 6020 and clearing restores the
  tf5000 anchor.

## Limits

- All results are measured on the three program images (original,
  control, candidate) in the litesvm harness with the fixture pools
  and fee table; they are not a claim about any other program
  version or live state.
- The buyback bps ladder is measured at 0 / 5000 / 7500 / 10000
  only; intermediate bps values were not swept.
- The fee-config update uses one recipient set and one authority;
  the "chain unmoved" result is for the split chain's tier pricing,
  not a claim that global bps never affect any path (single-pool
  v2 trades price off them).
- The burn movement from setter-before-buy (+95,167,785 at
  bb7500) is reported as measured; the packet does not fit the
  burn slope behind it.
- Error-site lines live in each receipt row's `error_sites` field,
  never in `observed`, because original/rebuild line numbers differ.
- No source change is proposed.

Made via @slopdotcash
