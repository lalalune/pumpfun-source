# research: multi-hop split x boost x tf chains with disable-flag priority

Scope note: this packet is deliberately NOT a re-measure of #77
(`research/amm-multi-hop-split-boost-tf-disable-chains-20261029`).
#77 established, on the main pool, that each GlobalConfig disable bit
gates only its own leg (buy bit -> 6020 on buys, sell bit -> 6021 on
sells, deposit bit -> 6018, withdraw bit -> 6019), that sweep /
collect / claim ignore disable, and that clearing a bit restores the
anchor. What #77 did not cover, and this packet measures, is: (a) the
priority of a disable bit against the #109 mode flags (cashback /
mayhem) on the same leg, (b) hop-pool (P2/P3) boosts under each bit --
#77 measured only the main-pool boost under the buy bit, #111 only the
P2 boost under the buy bit, (c) disable and boost_enabled toggles
mid-walk between a boost and a trade, (d) the fee-book legs after a
disabled-leg failure, (e) tf variants under disable, (f) exact legs
under disable, and (g) the create bit against a NEW pool (#77 tested
only existing pools, where the create bit gates nothing).

## Problem

On a true 3-hop split x boost x tf chain (three_amm only, final output
U3, 10^9 quote input, transfer fee 100 bps), what does a disable flag
do to a boost, and what does it do to a leg that is ALSO mode-flagged?
Two orderings are at stake: the disable check against the mode gates
(#109: original cashback gate is terminal-hop-only, rebuild cashback
gate is every hop), and the boost gate chain (#101: 6005 > 6066 >
6020 > 6065 > 6002 > 6023 > 6001). If disable is checked before the
mode gates, a flagged + disabled leg fails identically on original,
control and candidate -- the #109 divergence is masked, not resolved.
If it is checked after, the divergence survives under disable.

## Cases

52 cases, 456 receipts, 46 parts (45x10 + 6), 3 images
(original / control / candidate). All receipts carry before/after
snapshots of every watched account; verify.py re-derives every
expected value from the receipts alone.

- A (5 anchors): fresh buy, fresh sell, fresh boost, boost-then-buy,
  buy-then-boost.
- B (12, disable vs mode priority): main/p2/p3 cashback and main
  mayhem flags combined with the buy or sell bit, on buys, sells and
  boosts; boost_enabled=0 under the buy bit; rotated boost authority
  under the buy bit.
- C (9, hop-pool boosts by bit): P2 and P3 boosts under the buy, sell,
  deposit, withdraw and all-bits flags; cleared-bit P2 boost then buy;
  sell-bit P2 boost then sell.
- D (9, mid-walk toggles): boost -> set buy bit -> failed buy ->
  clear -> buy -> boost; buy -> set buy bit -> failed boost -> clear
  -> boost; set buy bit -> failed boost -> clear -> boost; the same
  walk driven by the real set_disable_flags instruction; outsider
  disable setter; boost -> boost_enabled=0 -> failed boost ->
  re-enable -> boost; deposit-bit and sell-bit and withdraw-bit
  toggle walks ending in a boost.
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
  boost and P2 boost under the create bit.

Route note: the multi-hop route is three_amm only (main -> P2 -> P3,
final output U3) in every case. This is a true 3-hop packet; the #61
miscount (a "3-hop" name on a 4-hop route) does not apply here.

## Result

Anchors (tf100, 10^9 quote in): fresh buy tail U3 5,262,910,281,902
(hop-1 buyback leg 4,515,471 + withheld 45,611); fresh sell payout
178,541 (leg 837 + withheld 9); fresh main boost burn 5,338,379,201,831;
boost-then-buy tail 5,139,964,404,268 (#102 value); buy-then-boost
burn 5,254,679,949,141. First trade payer cost 1,849,400 (fee 5,000 +
UVA rent 1,844,400).

Disable masks the mode divergence (headline). Every flagged +
disabled leg fails with the disable code on ALL THREE images, 0
events, full rollback: main-cashback + buy bit buy -> 6020, p3-cashback
+ buy bit buy -> 6020 (the rebuild's 6079 never fires), main-mayhem +
buy bit buy -> 6020, main-cashback + sell bit sell -> 6021,
p3-both + sell bit sell -> 6021. The whole packet has 0 divergent
cases: disable is checked before the mode gates, so the #109
original-vs-rebuild split is invisible while any disable bit is set.

Boost gate order extends to 6005 > 6066 > 6020. Main-cashback + buy
bit boost -> 6020 (a boost is NOT mode-blind to disable: the buy bit
gates it, the sell bit does not -- main-cashback + sell bit boost
burns the anchor 5,338,379,201,831). Boost_enabled=0 + buy bit boost
-> 6066, so 6066 beats 6020. Rotated authority + buy bit boost ->
6005, so 6005 beats 6020. This matches #101's chain
(6005 > 6066 > 6020 > 6065) at the head; the tail of the chain was not
re-measured here.

Hop-pool boosts, bit by bit: P2 and P3 boosts fail 6020 under the buy
bit (#111's P2 result, now with P3 added), and burn the anchor hop
value 999,997,999 under the sell bit, the deposit bit and the withdraw
bit alike. Under all-bits (31) they fail 6020 -- the buy bit
dominates. After clearing the buy bit, a P2 boost succeeds and the
following buy tail is 5,262,894,631,186 (#111 tail). A sell-bit P2
boost succeeds and the following sell still fails 6021.

Mid-walk toggles restore exactly. Boost -> set buy bit -> failed buy
(6020) -> clear -> buy -> boost = 5,173,028,765,024 (#112
boost-buy-boost value). Buy -> set buy bit -> failed boost (6020) ->
clear -> boost = the post-buy burn 5,254,679,949,141. Set buy bit ->
failed boost -> clear -> boost = the anchor 5,338,379,201,831. The
same walk driven by the real set_disable_flags instruction (1 event)
behaves identically, and its final boost is also 5,173,028,765,024.
An outsider disable setter fails 6005 and changes nothing: the
following buy is the anchor tail. Boost -> boost_enabled=0 -> failed
boost (6066) -> re-enable -> boost = 5,254,441,549,265 (the #100
second-burn decay value). Deposit-bit toggle walk: deposit fails
6018, clears, deposit succeeds (userbase -160,619,896, userquote
-29,610, +1,000,000 LP), boost = 5,338,379,222,079 (anchor +20,248,
#109 value). Sell-bit toggle walk: sell fails 6021, clears, sell is
the anchor payout, boost = 5,338,394,848,092 (post-sell anchor).
Withdraw-bit toggle walk: withdraw fails 6019, clears, withdraw
succeeds (userbase +160,619,895, userquote +29,018), boost =
5,338,379,181,539 (anchor -20,292, the deposit mirror).

Fee-book legs ignore disable; the later boost does not. After a
failed buy under the buy bit, the protocol sweep (fixture 2,488 only),
the creator sweep (123,394 -> net 122,160, withheld 1,234) and the
collect (122,160 -> dest 120,938, withheld 1,222) all succeed, the
token claim pays the seeded 3,334,551, and the deposit succeeds --
but the boost at the end of each walk still fails 6020 while the bit
stays set. The cashback claim under tf still fails 2021 (#102 value).
After a failed sell under the sell bit, the protocol sweep succeeds
and the following boost burns 5,338,379,308,140 (anchor +106,309:
2,488 swept at the #100 slope of ~42.73 per unit).

Tf variants: disable beats tf. tf5000 buy-bit buy fails 6020 and its
boost fails 6020. Boost_enabled=0 under tf5000 still fails 6066, so
the enabled gate is tf-independent. tf0 sell-bit failed sell, boost = 5,391,870,655,895
(the tf0 anchor burn, vq1 +1,000,000,000, no withholding). Caution on
one value: the tf5000 cleared-buy walk (failed boost attempt, then
clear, then tf5000 buy, then boost) tails 2,660,981,910,591 and burns
2,685,252,553,572 -- NOT #109's unpatched tf5000 values
(2,682,425,360,738 / 2,685,165,599,125). The difference is the VQ
patch (vq field = 10^9) that the failed boost attempt left active
during the buy; the vq field enters hop-1 pricing (#102), so the two
walks are not the same walk and the values are reported as measured,
not as a #109 reproduction. The mechanism of the +86,954,447 boost
gap is not determined from these receipts.

Exact legs take the same disable gates: legacy exact-out buy
(10^9 base_out), legacy exact-in buy (10^9 spend) and v2 exact-out buy
(10^9 base_out) all fail 6020 under the buy bit, 0 events; legacy
sell fails 6021 under the sell bit.

Create bit blocks new pools only (headline). A new-pool create_pool
under the create bit fails 6017 DisabledCreatePool
(create_pool.rs:193), 0 events, full rollback -- a dedicated code, not
a generic disable code, and a sharp contrast with #77's "the create
bit gates nothing on existing pools". The same bit leaves boosts on
existing pools untouched: main boost = anchor 5,338,379,201,831, P2
boost = 999,997,999.

## Limits

- The create-bit 6017 is measured on one create_pool shape (standard
  pool, 10^12/10^12 initial liquidity, plain quote mint, no transfer
  fee); other create shapes were not tested.
- The boost gate tail (6065 > 6002 > 6023 > 6001) was not re-measured
  under disable; only the head (6005 > 6066 > 6020) is pinned here.
- The tf5000 cleared-buy boost gap (+86,954,447 vs #109) is reported
  as a measured difference between two different walks, not as a
  mechanism claim.
- No source change is proposed. The packet records measured
  behaviour only; the original/rebuild divergence count is 0, and
  that itself is the finding for the disable-vs-mode question.

Made via @slopdotcash
