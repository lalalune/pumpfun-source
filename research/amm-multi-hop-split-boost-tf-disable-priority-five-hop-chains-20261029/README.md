# research: multi-hop split x boost x tf chains with disable-flag priority at TRUE 5 hops

Scope note: this packet is the 5-hop extension of #114
(`research/amm-multi-hop-split-boost-tf-disable-priority-chains-20261029`),
not a re-measure. #114 established, on the main pool at 3 hops, that
each GlobalConfig disable bit gates only its own leg, that disable
masks the #109 mode divergence (flagged + disabled legs fail with the
disable code on all three images), that the boost gate head is
6005 > 6066 > 6020, and that the create bit blocks new pools only
(6017). What #114 did not cover, and this packet measures, is whether
all of that scales to depth 5: (a) disable vs mode priority at every
hop position (main/P2/P3/P4/P5, both directions), (b) hop-pool (P4/P5)
boosts under each bit, (c) disable and boost_enabled toggles mid-walk
between a boost and a trade at depth 5, (d) the fee-book legs after a
disabled-leg failure at depth 5, (e) tf variants under disable at
depth 5, (f) exact legs under disable at depth 5, and (g) the create
bit against a NEW pool at depth 5 — plus the one case #114 could not
show: what happens when the disable bit is CLEARED mid-walk on a
mode-flagged pool.

## Problem

On a true 5-hop split x boost x tf chain (three_amm + g4 + g5, final
output U5, 10^9 quote input, transfer fee 100 bps), what does a disable
flag do to a boost, and what does it do to a leg that is ALSO
mode-flagged? Two orderings are at stake: the disable check against
the mode gates (#109/#119: original cashback gate is terminal-hop-only
— now P5 — rebuild cashback gate is every hop), and the boost gate
chain (#101: 6005 > 6066 > 6020 > 6065 > 6002 > 6023 > 6001). If disable
is checked before the mode gates, a flagged + disabled leg fails
identically on original, control and candidate at every hop position
— the #119 divergence is masked, not resolved. If it is checked after,
the divergence survives under disable at some hop. A third question is
whether masking is permanent: clearing the bit mid-walk should unmask
whatever the mode gates would have done on their own.

## Cases

65 cases, 525 receipts, 53 parts (52x10 + 5), 3 images
(original / control / candidate). All receipts carry before/after
snapshots of every watched account; verify.py re-derives every
expected value from the receipts alone.

- A (5 anchors): 5-hop buy, 5-hop sell, fresh boost, buy-then-boost,
  boost-then-buy.
- B (11, disable vs mode priority, buys): main/p2/p3/p4/p5 cashback,
  main/p2/p4/p5 both, main/p5 mayhem, each combined with the buy bit.
- B2 (6, disable vs mode priority, sells): main cashback, p2/p4/p5
  both, p5 cashback, main mayhem, each combined with the sell bit.
- B3 (5, boosts under disable + mode flags, gate head): main-cashback
  + buy bit boost, main-cashback + sell bit boost, p5-both + buy bit
  boost, boost_enabled=0 + buy bit boost, rotated authority + buy bit
  boost.
- C (10, hop-pool boosts by bit): P2/P4/P5 boosts under the buy bit,
  P4/P5 under the sell bit, P4 under the deposit bit, P5 under the
  withdraw bit, P4 under all-bits (31); cleared-bit P4 boost then buy;
  sell-bit P5 boost then sell.
- D (9, mid-walk toggles): boost -> set buy bit -> failed buy ->
  clear -> buy -> boost; buy -> set buy bit -> failed boost -> clear
  -> boost; set buy bit -> failed boost -> clear -> boost; the same
  walk driven by the real set_disable_flags instruction; outsider
  disable setter; boost -> boost_enabled=0 -> failed boost ->
  re-enable -> boost; deposit-bit and sell-bit and withdraw-bit
  toggle walks ending in a boost.
- D2 (2, clearing disable unmasks the mode divergence): main-cashback
  buy under the buy bit, clear, buy, boost; p5-both buy under the buy
  bit, clear, buy, boost.
- E (6, fee-book legs after a disabled-leg failure): failed buy ->
  protocol sweep, creator sweep, collect, token claim, cashback claim,
  deposit, each followed by a boost; failed sell -> protocol sweep ->
  boost.
- F (4, tf variants): tf5000 buy-bit buy + boost; tf0 sell-bit sell
  + boost; buy-bit failed boost -> clear -> tf5000 buy -> boost;
  boost_enabled=0 + tf5000 boost.
- G (4, exact legs under disable): legacy exact-out buy, legacy
  exact-in buy, v2 exact-out buy under the buy bit; legacy sell under
  the sell bit.
- H (3, create bit): new-pool create_pool under the create bit; main
  boost and P5 boost under the create bit.

Route note: the multi-hop route is three_amm + g4 + g5 (main -> P2 ->
P3 -> P4 -> P5, final output U5) in every case, confirmed by 5 hop
events on every successful swap. This is a true 5-hop packet; the #61
miscount (a "3-hop" name on a 4-hop route) does not apply here. A
routed hop pool needs proper pool data (bump, pool-authority creator,
its base mints, its vaults), not raw main-pool bytes, or legs fail
6008 (#119 build lesson, applied here for P5).

## Result

64 of 65 cases agree on original, control and candidate; exactly 1
case diverges, and it is the unmasking case (see below). Control ==
candidate everywhere.

Anchors (tf100, 10^9 quote in): 5-hop buy tail U5 5,207,955,235,891
(hop-1 buyback leg 4,515,471 + withheld 45,611); 5-hop sell payout
178,541 (leg 837 + withheld 9); fresh main boost burn
5,338,379,201,831; buy-then-boost burn 5,254,679,949,141;
boost-then-buy tail 5,087,534,167,771. First trade payer cost
1,849,400 (fee 5,000 + UVA rent 1,844,400).

Disable masks the mode divergence at depth 5 (headline). Every
flagged + disabled leg fails with the disable code on ALL THREE
images, 0 events, full rollback, at every hop position and in both
directions: main/p2/p3/p4/p5 cashback + buy bit buy -> 6020,
main/p2/p4/p5 both + buy bit buy -> 6020 (the rebuild's 6079 never
fires), main/p5 mayhem + buy bit buy -> 6020 (the 6080 never fires),
main cashback + sell bit sell -> 6021, p2/p4/p5 both + sell bit sell
-> 6021, p5 cashback + sell bit sell -> 6021, main mayhem + sell bit
sell -> 6021. Disable is checked before the mode gates at depth 5
exactly as at depth 3; the #119 original-vs-rebuild split is invisible
while any disable bit is set.

Boost gate order holds at depth 5: 6005 > 6066 > 6020. Main-cashback
+ buy bit boost -> 6020 (a boost is NOT mode-blind to disable: the
buy bit gates it, the sell bit does not -- main-cashback + sell bit
boost burns the anchor 5,338,379,201,831; p5-both + buy bit boost ->
6020). Boost_enabled=0 + buy bit boost -> 6066, so 6066 beats 6020.
Rotated authority + buy bit boost -> 6005, so 6005 beats 6020. This
matches #101's chain (6005 > 6066 > 6020 > 6065) at the head; the tail
of the chain was not re-measured here.

Hop-pool boosts, bit by bit: P4 and P5 boosts fail 6020 under the buy
bit (P2 included, as in #114), and burn the anchor hop value
999,997,999 under the sell bit, the deposit bit and the withdraw bit
alike. Under all-bits (31) they fail 6020 -- the buy bit dominates.
After clearing the buy bit, a P4 boost succeeds and the following
buy tail is 5,207,939,747,168 (anchor - 15,488,723: the P4 boost moved
the following tail, reported as measured). A sell-bit P5 boost
succeeds and the following sell still fails 6021.

Mid-walk toggles restore exactly. Boost -> set buy bit -> failed buy
(6020) -> clear -> buy -> boost = 5,173,028,765,024 (#112
boost-buy-boost value). Buy -> set buy bit -> failed boost (6020) ->
clear -> boost = the post-buy burn 5,254,679,949,141. Set buy bit ->
failed boost -> clear -> boost = the anchor 5,338,379,201,831. The
same walk driven by the real set_disable_flags instruction (1 event
per setter call) behaves identically, and its final boost is also
5,173,028,765,024. An outsider disable setter fails 6005 and changes
nothing: the following buy is the anchor tail. Boost ->
boost_enabled=0 -> failed boost (6066) -> re-enable -> boost =
5,254,441,549,265 (the #100 second-burn decay value). Deposit-bit
toggle walk: deposit fails 6018, clears, deposit succeeds (userquote
-29,610), boost = 5,338,379,222,079 (anchor +20,248, #114 value).
Sell-bit toggle walk: sell fails 6021, clears, sell is the anchor
payout, boost = 5,338,394,848,076 (post-sell anchor; 16 below #114's
3-hop post-sell value, a depth effect reported as measured).
Withdraw-bit toggle walk: withdraw fails 6019, clears, withdraw
succeeds (userquote +29,018), boost = 5,338,379,181,539 (anchor
-20,292, the deposit mirror).

Clearing disable UNMASKS the divergence (headline, the packet's 1
divergent case). Main-cashback buy under the buy bit fails 6020 on
all images; clearing the bit and buying again passes on the original
at the full tail 5,207,955,235,891 (main is non-terminal at depth 5,
so the original's terminal-only cashback gate does not fire) and
fails 6079 on the rebuild, with the following boost at the post-buy
burn 5,254,679,949,141 on the original and the anchor
5,338,379,201,831 on the rebuild. Contrast: p5-both buy under the buy
bit fails 6020, and after clearing, the buy fails 6079 with 4 ghosts
on BOTH images -- at the terminal hop the original and the rebuild
agree, so no divergence. Masking is a property of the disable check
running first, not of the mode gates being resolved: remove the mask
and the #119 split returns exactly where #119 put it.

Fee-book legs ignore disable; the later boost does not. After a
failed buy under the buy bit, the protocol sweep (fixture 2,488 ->
net 2,463, withheld 25), the creator sweep (123,394 -> net 122,160,
withheld 1,234) and the collect (122,160 -> dest 120,938, withheld
1,222) all succeed, the token claim pays the seeded 3,334,551, and
the deposit succeeds -- but the boost at the end of each walk still
fails 6020 while the bit stays set. The cashback claim under tf still
fails 2021 (#102 value). After a failed sell under the sell bit, the
protocol sweep succeeds and the following boost burns
5,338,379,308,140 (anchor +106,309, the #114 value).

Tf variants: disable beats tf. tf5000 buy-bit buy fails 6020 and its
boost fails 6020. Boost_enabled=0 under tf5000 still fails 6066, so
the enabled gate is tf-independent. tf0 sell-bit failed sell, boost =
5,391,870,655,895 (the tf0 anchor burn). The tf5000 cleared-buy walk
(failed boost attempt, then clear, then tf5000 buy, then boost) tails
2,646,860,200,791 and burns 2,685,252,553,572 -- the burn is byte-
identical to #114's 3-hop tf5000 cleared-buy burn, while the tail
differs by depth (3-hop tail 2,660,981,910,591); the VQ patch (vq
field = 10^9) left active by the failed boost attempt is the same
mechanism #114 reported, and the values are reported as measured,
not as a #109 reproduction.

Exact legs take the same disable gates: legacy exact-out buy
(10^9 base_out), legacy exact-in buy (10^9 spend) and v2 exact-out buy
(10^9 base_out) all fail 6020 under the buy bit, 0 events; legacy
sell fails 6021 under the sell bit.

Create bit blocks new pools only (headline). A new-pool create_pool
under the create bit fails 6017 DisabledCreatePool
(create_pool.rs:193), 0 events, full rollback -- a dedicated code, not
a generic disable code, and a sharp contrast with #77's "the create
bit gates nothing on existing pools". The same bit leaves boosts on
existing pools untouched: main boost = anchor 5,338,379,201,831, P5
boost = 999,997,999.

## Limits

- The create-bit 6017 is measured on one create_pool shape (standard
  pool, 10^12/10^12 initial liquidity, plain quote mint, no transfer
  fee); other create shapes were not tested.
- The boost gate tail (6065 > 6002 > 6023 > 6001) was not re-measured
  under disable; only the head (6005 > 6066 > 6020) is pinned here.
- The tf5000 cleared-buy burn equalling #114's 3-hop value is
  reported as a measured equality, not as a mechanism claim.
- The cleared-P4-boost buy tail (anchor - 15,488,723) and the 16-unit
  post-sell boost gap vs #114 are reported as measured depth
  effects; their mechanisms are not narrowed by these receipts.
- No source change is proposed. The packet records measured
  behaviour only; the original/rebuild divergence count is 1, and
  that single case is the finding for the disable-vs-mode question
  at depth 5.

Made via @slopdotcash
