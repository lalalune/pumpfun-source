# research: state transitions across legs on a split x boost x tf chain at true 5 hops

## Problem

Earlier packets pinned what each leg does in isolation: a trade, a
sweep, a boost, a claim, a setter. The 3-hop packet (#92) pinned what
a leg leaves behind for the next leg on a `three_amm`-only chain.
This packet re-pins the same question at true 5 hops
(`three_amm + g4 + g5`, final output U5) on the same split x boost x
transfer-fee chain: after each leg, how does every account move —
the five pools' virtual quote reserves, protocol fees, creator fees
and LP supply; the vaults; the user volume accumulator (UVA) and the
global volume accumulator (GVA); the GlobalConfig; the fee-table;
and the user's token accounts. The questions are: which transitions
change the next leg's price, which are pure bookkeeping, which
transitions are one-shot, whether a failed leg leaves anything
behind, and — the one place depth changes the answer — what a
failing 5-hop buy does instead of returning a clean slippage error.

## Cases

88 cases, 639 receipts (213 steps x 3 images: original, control,
candidate), 64 parts. All cases use the same split x boost x tf
chain unless noted. Anchors on the fixture chain: a 10**9-quote buy
yields tail U5 5,207,955,235,891 with buyback leg 4,515,471,
withheld vq1 10,000,000 and buyback withheld 45,611; a 10**9-base
sell yields net 178,541 quote with buyback 837. After a buy the main
pool is [vq -4,686,964, protocol 4,563,570, creator 123,394, supply
4,194,352,106,721] and the terminal pool P5 is [vq -2,617,735,896,
protocol 2,488, creator 2,617,733,408, same supply]; after a sell the
main pool is [-126,729, 3,335, 123,394, same supply] and P5 is
[-625,882, 2,488, 623,394, same supply]. The fixture window (vq +
protocol + creator) is 0 on every pool. Every successful swap emits
exactly 5 hop events (buy disc 67f4521f2cf57777 len 508, sell disc
3e2f370aa503dc2a len 449).

Families (prefix = family):

- `a-` trade-to-trade transitions: buy x2, sell x2, buy-sell-buy,
  sell-buy-sell, 1e6 buys x5, 1e6 sells x3, tf0 buys x3, tf5000
  buys x2, plus the buy and sell anchors.
- `b-` liquidity-to-trade transitions: deposit then buy, withdraw
  then buy, deposit-withdraw-buy, 1e8 deposit then buy, full
  seeded-LP withdrawal then buy, buy then deposit, buy then
  deposit at a 10**9 vq patch, and deposit-only at vq patches
  5e8 and 2e9.
- `c-` sweep/collect-to-trade transitions: buy-sweep-buy,
  buy-sweep-creator-collect-buy, sweep-buy, buy-sweep-sweep-buy,
  sell-sweep-sell, buy-collect-buy, buy-sweep-buy-sweep,
  sell-sweep-creator-collect-sell.
- `d-` boost window transitions: boost anchor, boost x2, boost x3,
  boost with no window, buy-boost, boost-buy, boost-buy-boost,
  deposit-boost, sweep-boost, small boosts x3, sell-boost — all at
  a 1,000,000,000 vq patch unless noted.
- `e-` claim and lifecycle transitions: token claim x2, token
  claim-buy-token claim, sync-token claim x2, cashback claim x2,
  init-token claim, close-reinit-token claim, extend-token claim.
- `f-` setter-then-trade transitions: buyback-config (0, 5000,
  7500, 10000) then buy, buyback-config then sweep, fee-config
  then buy, fee-config then sweep, disable-buy-disable-off-buy,
  boost-toggle round trip with boosts, admin rotation chain,
  coin-creator set then buy.
- `g-` failure rollback, then the anchor leg: failing buy (twice),
  failing sell, failing deposit, failing withdraw, failing boost,
  failing setter, failing claim, failing withdraw-withheld — each
  followed by the anchor buy.
- `h-` order dependence: buy-sweep vs sweep-buy, sweep-creator-
  collect vs collect-sweep-creator, sell-buy vs buy-sell,
  claim-buy vs buy-claim, disable-then-buy vs buy-then-disable,
  toggle-then-boost vs boost-then-toggle, deposit-withdraw vs
  withdraw-deposit, sell-sweep vs sweep-sell.
- `w-` recovery transitions: buy-harvest-withdraw-from-mint,
  sweep-creator-collect-withdraw-withheld-buy,
  buy-sweep-creator-collect-harvest-withdraw-from-mint.

## Result

### The window is invariant, and sweep only relocates

Window = vq + protocol_fees + creator_fees is exactly 0 on the
fixture chain through every buy, sell, sweep, collect, and boost; a
1,000,000,000 vq patch makes it 1,000,125,882 and it stays there
through buy, sell, sweep, and boost. On a 5-hop buy only the first
hop pool (main) and the terminal hop pool (P5) move — the
intermediate pools P2, P3, P4 stay exactly at the fixture state
([-125,882, 2,488, 123,394]) after every buy and every sell. Sweep
only relocates accrued into vq (protocol sweep +4,563,570 vq /
-4,563,570 accrued, tf-netted to 4,517,934 tokens) and never
changes the next trade's tail: buy-sweep-buy and
buy-sweep-creator-collect-buy both land the second buy at exactly
the buy-x2 second tail, 4,918,089,082,874.

### A failing 5-hop buy panics where a failing 3-hop buy returns 6004

This is the one place depth changes the answer. At 3 hops, a buy
whose min_out exceeds the achievable tail returns clean
6004 ExceededSlippage at multi_hop_swap.rs:389. At 5 hops, the
same failing buy — for any unmet min_out, even tail+1
(5,207,955,235,892) — panics with ProgramFailedToComplete,
"memory allocation failed, out of memory", after all 5 hop events
have already been emitted, with no AnchorError line at all. The
panic is identical on all three images, the failed leg still rolls
back every watched account byte-identically, and the next leg pays
exactly the anchor. The mechanism behind the allocation failure was
not identified; what is pinned is the observable behavior: the
depth-5 buy slippage path never returns 6004. Sell slippage at
depth 5 stays clean (6002), as do deposit/withdraw (6004), setter
(6005), claim (3012), withdraw-withheld (token custom 4),
window-less boost (6065), toggle-gated boost (6066), disabled buy
(6020), and fee-config-gated sweep (6013).

### Repeated burns shrink because vb1 drains, not because the window shrinks

Three 10**9 boosts burn 5,338,379,201,831, 5,254,441,549,265, then
5,172,468,136,601 with pool state (vq, accrued, supply) unchanged
and only the remaining budget falling 999,000,000,000 ->
998,000,000,000 -> 997,000,000,000. A buy-first boost burns
5,255,205,915,165 (83B less than standalone), a sell-first boost
burns 5,338,394,947,565 (+15,745,734), and a sweep-first boost
equals the buy-first value (sweep is boost-neutral). A
deposit-first boost burns 5,338,379,211,910 (+10,079 vs
standalone). All of these burn values are identical to the 3-hop
packet: boost reads only the main pool, so depth does not move it.

### Trades are path-dependent in both directions, and depth amplifies it

Sell-then-buy yields tail 5,208,011,418,184 (+56,182,293 vs the buy
anchor, against +36,263,882 at 3 hops) and buy-then-sell pays
189,218 (+10,677 vs the sell anchor, against +6,747 at 3 hops);
each trade moves the curve in favor of the reverse trade.
Buy-sell-buy tails decay 5,207,955,235,891 -> 4,972,876,453,666
across the round trip; five 10**6 buys decay 5,361,233,911 ->
5,360,917,947 -> 5,360,602,013 -> 5,360,286,103 -> 5,359,970,223;
three 10**6 sells pay 178 each with pf creeping +1 per sell. tf0
and tf5000 repeats decay the same way with their own anchors
(tf0 first tail 5,259,040,470,738, tf5000 first tail
2,668,075,748,732).

### Deposit nudges vq linearly; withdraw does not move it

A 10**6-LP deposit moves vq by 0 at vq <= 0, +119 at 5e8, +476 at
2e9 (proportional to vq, truncating to 0 at small |vq|); a
withdraw never moves vq. Deposit-then-buy beats the anchor by
+9,597, withdraw-then-buy trails by -9,640, and a deposit/withdraw round trip
leaves the anchor -42 behind (the 1-base + 1-quote flooring dust
of the prior packet). Draining the seeded LP drops the next buy
by ~40.0B, to 5,167,905,288,822.

### Claims are one-shot, and sync strands volume

The token claim pays 3,334,551 (net 3,301,205 after 33,346
withheld) and the second claim is silent with 0 deltas; a buy
between claims does not re-arm it. Sync fires (claimed 222 -> 0,
has 1 -> 0) and the next claim pays only the 111 unclaimed while
volume 333,444 stays stranded through a second silent claim.
Cashback's second claim emits an amount-0 event (token's does
not). Close-then-re-init forfeits the whole claim (re-init claim
pays 0); a real 90 -> 137 resize emits the 96-byte ExtendEvent
(the prior packet's silent extend was a 137 -> 137 no-op).

### Setter transitions: one gross fee, split four ways

Buyback bps splits one gross fee 9,122,164 between buyback (bps
share, tf-netted: 5000 -> 4,515,471, 7500 -> 6,773,206, 10000 ->
9,030,942) and protocol bucket (0 -> 9,124,652, 5000 -> 4,563,570,
7500 -> 2,283,029, 10000 -> 2,488 unchanged) with the tail
identical in all four cases. A fee-config change leaves trades
identical but breaks the next protocol sweep (6013 recipient
gate). Disable and boost-toggle round trips restore the anchor
exactly; admin rotation hands every setter to the new admin (old
admin 6005, new admin succeeds) while sweeps and boosts ignore
admin identity.

### Failed legs roll back completely

6004 buy/deposit/withdraw failures (and the 5-hop buy panic
above), 6002 sell failure, 6005 setter failure, 3012 claim
failure, and token custom 4 withdraw-withheld failure all leave
every watched account byte-identical, and the next leg pays
exactly the anchor. Order decides execution for disable-then-buy
(6020) and toggle-then-boost (6066), but deposit-withdraw,
claim-buy, and sweep-creator-collect pairs are fully
order-independent in final state.

## Limits

- The 5-hop buy panic is pinned as observable behavior only; the
  allocation-failure mechanism inside the program was not traced
  to a source line, and no source change is proposed.
- Intermediate hop pools P2, P3, P4 are fixture-identical pools
  with the same reserves; the "only main + P5 move" observation is
  measured on that fixture, not on pools with distinct reserves.
- The route uses SPL token accounts throughout; hop-pool boost
  ATAs follow the hop quote mint's program (SPL-derived here).
- No claim is made about the whole program: only the measured
  transitions on this chain, on these three images, are pinned.
- All 88 cases agree on all three images (original, control,
  candidate): there is no rebuild divergence in this packet.

Made via @slopdotcash
