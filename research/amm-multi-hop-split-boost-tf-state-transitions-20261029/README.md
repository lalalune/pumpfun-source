# research: state transitions across legs on a split x boost x tf chain

## Problem

Earlier packets pinned what each leg does in isolation: a trade, a
sweep, a boost, a claim, a setter. They did not pin what a leg leaves
behind for the next leg. This packet runs legs back to back on one
split x boost x transfer-fee chain (true 3-hop, `three_amm` only,
final output U3) and records, step by step, how every account moves:
the main pool's virtual quote reserves, protocol fees, creator fees
and LP supply; the vaults; the user volume accumulator (UVA) and the
global volume accumulator (GVA); the GlobalConfig; the fee-table;
and the user's token accounts. The questions are: which transitions
change the next leg's price, which are pure bookkeeping, which
transitions are one-shot, and whether a failed leg leaves anything
behind.

## Cases

88 cases, 639 receipts (213 steps x 3 images: original, control,
candidate), 64 parts. All cases use the same split x boost x tf
chain unless noted. Anchors on the fixture chain: a 10**9-quote buy
yields tail 5,262,910,281,902 with buyback leg 4,515,471, withheld
vq1 10,000,000 and buyback withheld 45,611; a 10**9-base sell yields
net 178,541 quote with buyback 837. After a buy the main pool is
[vq -4,686,964, protocol 4,563,570, creator 123,394, supply
4,194,352,106,721]; after a sell it is [-126,729, 3,335, 123,394,
same supply]. The fixture window (vq + protocol + creator) is 0.

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
  buy-creator-sweep-collect-buy, sweep-first-buy, buy-sweep-sweep-
  buy, sell-sweep-sell, buy-collect-buy, buy-sweep-buy-sweep,
  sell-creator-sweep-collect-sell.
- `d-` boost transitions: standalone boost, boost x3, buy-then-
  boost, boost-then-buy, boost-buy-boost, sell-then-boost,
  sweep-then-boost, 1e6 boosts x3, buy-then-boost at a 10**9 vq
  patch, boost at a 10**9 vq patch, boost at a 1,000,125,882
  window, boost at window 0, boost after a 10**6-LP deposit, and
  a buy at a 10**9 vq patch.
- `e-` claim/lifecycle transitions: token claim x2, claim-buy-
  claim, sync-claim x2, cashback claim x2, init-claim,
  close-re-init-claim, extend-claim.
- `f-` setter-to-leg transitions: buyback-config 7500 then buy,
  buyback-config 7500 then buy x2, buyback-config 0 then buy,
  buyback-config 10000 then buy, buyback-config then protocol
  sweep, fee-config then buy, fee-config then protocol sweep,
  disable-buy-disable-off-buy, boost-toggle round trip,
  admin rotation then setter then buy, set-coin-creator then buy.
- `g-` failed-leg rollback: failed buy then buy, failed buy x2
  then buy, failed sell then buy, failed deposit then buy,
  failed withdraw then buy, failed boost then sweep, failed
  setter then buy, failed token claim then buy, failed
  withdraw-withheld then buy.
- `h-` order dependence pairs: buy-sweep vs sweep-buy,
  creator-sweep-collect vs collect-creator-sweep, sell-buy vs
  buy-sell, claim-buy vs buy-claim, disable-then-buy vs
  buy-then-disable, toggle-then-boost vs boost-then-toggle,
  deposit-withdraw vs withdraw-deposit, sell-sweep vs sweep-sell.
- `w-` withdraw-withheld recovery transitions: buy-harvest-
  withdraw-from-mint, creator-sweep-collect-withdraw-withheld-
  buy, buy-creator-sweep-collect-harvest-withdraw-from-mint.

## Result

All 88 cases agree on all three images (0 divergent cases).
Control == candidate everywhere.

### The window is invariant, and sweep only relocates

Window = vq + protocol_fees + creator_fees. On the fixture chain
it is exactly 0 after a buy, after a sell, after a sweep, after a
collect, and after a boost. Patching vq to 10**9 makes it
1,000,125,882 and it stays there through a buy, a sell, a sweep,
and a boost. A protocol sweep moves the accrued bucket into vq
(+4,563,570 vq, protocol 4,563,570 -> 0 after a buy; +2,488 vq,
protocol -> 0 for the seed bucket) and a creator sweep moves
+123,394 vq / creator -> 0. Neither sweep changes the next
trade's tail: buy-after-sweep is 5,072,980,706,277, exactly the
second buy of buy-x2, and sell-after-sweep is 178,540, exactly
the second sell of sell-x2. A second protocol sweep is a silent
no-op (0 events, 0 deltas), and a collect without a prior sweep
is a silent no-op too. Sweep is price-neutral and window-neutral:
it only relocates accrued fees from the pool's fee buckets into
its virtual quote reserves.

### Repeated burns shrink because vb1 drains, not because the window shrinks

Three 10**9 boosts burn 5,338,379,201,831, then
5,254,441,549,265, then 5,172,468,136,601. After each boost the
pool state (vq, accrued, supply) is unchanged; only the
remaining budget falls 999,000,000,000 -> 998,000,000,000 ->
997,000,000,000. The shrink is the base vault draining: each
boost's buy leg consumes ~5.3e12 base from vb1, so the next
boost's buy leg starts from a thinner vault. This corrects the
prior packet's suggestion that the second boost fell because
the window shrank: the window does not move at all. Small
boosts shrink the same way: three 10**6 boosts burn
5,380,970,054, 5,380,884,096, 5,380,798,141 (~86k per repeat).
A buy-first boost burns 5,255,205,915,165, 83B below the
standalone burn, because the buy already drained vb1; a
sell-first boost burns 5,338,394,947,565, 15,745,734 above
standalone, because the sell refilled vb1; a sweep-first boost
burns exactly the buy-first value, because sweep does not
touch vb1. A boost at window 0 fails 6065 PoolCannotBoost
with 0 events; a boost at a 10**9 vq patch burns the standalone
value.

### Trades are path-dependent in both directions

Sell-then-buy yields tail 5,262,946,545,784, which is
36,263,882 above the buy anchor: a sell adds base to the
vaults, making base cheaper for the next buy. Buy-then-sell
yields net 185,288, which is 6,747 above the sell anchor: a
buy removes base, making base scarcer for the next sell. Each
trade moves the curve in favor of the reverse trade. Repeated
same-direction trades decay: buy-sell-buy tails fall
5,262,910,281,902 -> 5,108,657,030,385; five 10**6 buys decay
5,361,291,543 -> 5,360,488,750 (about 200k per repeat, with
protocol accrual creeping +4,562 per repeat); three 10**6
sells pay 178 each with protocol accrual creeping +1 per
sell. tf0 buys decay 5,315,084,721,958 -> 5,121,405,353,567 ->
4,938,123,213,306 and tf5000 buys decay 2,682,425,360,738 ->
2,632,645,264,199, each with its own anchor but the same
decay shape. This is the repeated-trade decay of the prior
residue packet, now shown to hold across fee regimes and to
reverse sign for the opposite direction.

### Deposit nudges vq linearly; withdraw does not move it

A 10**6-LP deposit moves vq by 0 at vq <= 0, +119 at vq
5e8, +238 at vq 10**9, +476 at vq 2e9: the nudge is
proportional to vq and truncates to 0 at small |vq|. A
withdraw never moves vq at any patch. The mechanism is
consistent with a proportional update of the form quote_in x
vq / vault quote balance, truncated toward zero (29,313 x
(-125,882) / ~1.23e14 is about -0.03, hence 0 on the fixture;
29,313 x 10**9 / ~1.23e14 is 238), but the vault balance is
not pinned by this packet, so the formula is stated as a
fit, not a finding. Deposit-then-buy beats the anchor by
+9,801 and withdraw-then-buy trails it by -9,844, so a
deposit improves the next buy and a withdrawal worsens it.
A deposit/withdraw round trip leaves the next buy 42 below
the anchor: the 1-base + 1-quote flooring dust of the prior
residue packet survives in the price. A 10**8-LP deposit
improves the next buy by +982,642, and draining the full
seeded LP (2,097,176,053,360) drops the next buy by about
40.9B to 5,222,013,969,107. At a 10**9 vq patch, a buy makes the next deposit
236 quote dearer (29,846 vs 29,610). Deposit and withdraw
themselves move only lp_supply on the fixture; the pool's
vq and accrued buckets are untouched except for the deposit
nudge above.

### Claims are one-shot, and sync strands volume

The token claim pays 3,334,551 (user receives 3,301,205 net
after 33,346 withheld) and sets UVA claimed 222 -> 3,334,773,
volume -> 0, last -> 21. The second claim is silent: 0
events, 0 deltas, UVA unchanged. A buy between claims does
not re-arm it (the second claim is still silent), confirming
the prior packet's finding that trades do not touch the UVA.
Sync fires (claimed 222 -> 0, has 1 -> 0, 64-byte event) and
the next claim pays only the 111 unclaimed (net 109, withheld
2) while volume 333,444 stays stranded: the claim after that
is silent too, so the stranded volume is not payable by
another claim at the same clock. The cashback claim differs:
its second claim emits an amount-0 event (token's second
claim emits none), both pay the full 5,475 the first time.
Init-then-claim pays 0 silently on a fresh zero UVA (last
still advances to 21). Close-then-re-init-then-claim also
pays 0: re-initialization does not restore the claimable
3,334,551 or even the 111 unclaimed. A real 90 -> 137 resize
emits the 96-byte ExtendEvent (disc 6161d7905d92167c, old 90,
new 137) and the claim after it pays the full 3,334,551;
this qualifies the prior event packet's "extend is silent"
note, whose extend was a 137 -> 137 no-op.

### Setter transitions: one gross fee, split four ways

Buyback bps splits a single gross fee of 9,122,164 between
the buyback leg (bps share, tf-netted) and protocol accrual
(the remainder), with the tail identical in all four cases:
bps 0 -> buyback leg gone, vq1 keeps the full 990,000,000,
protocol bucket 9,124,652; bps 5000 -> buyback 4,515,471,
protocol bucket 4,563,570; bps 7500 -> buyback 6,773,206
(exactly 1.5x), protocol bucket 2,283,029; bps 10000 ->
buyback 9,030,942 (exactly 2x), protocol bucket 2,488
unchanged (accrual 0).
Two 7500 buys end at exactly the one-5000-buy pool state
([-4,686,964, 4,563,570, 123,394]), because 7500 accrues at
half the 5000 rate. A fee-config change (lp 20 -> 30, proto
5 -> 40, recipients replaced, creator 100) leaves the next
buy byte-identical to the anchor, but breaks the next
protocol sweep: it fails 6013 on the recipient gate, because
the sweep's protocol recipient is no longer in the config
list. This is the prior fee-config packet's gate, now shown
as a transition break: a config edit can silently disable
fee recovery. Disable and boost-toggle round trips restore
the anchor exactly (disable buy -> buy 6020, re-enable ->
anchor buy; boost-off -> boost 6066, boost-on -> anchor
burn 5,338,379,201,831). Admin rotation hands every setter
to the new admin (old admin's buyback-config fails 6005
with no residue, new admin's succeeds) and the next buy is
anchor-identical; sweeps and boosts ignore admin identity
entirely. An already-set coin-creator set is a silent no-op
and the next buy is anchor-identical.

### Failed legs roll back completely

A 6004 buy (slippage), a second 6004 buy, a 6002 sell, a
6004 deposit, a 6004 withdraw, a 6005 setter, a 3012 claim,
and a token custom 4 withdraw-withheld failure all leave
every watched account byte-identical, and the next leg pays
exactly the anchor (buy 5,262,910,281,902; protocol sweep
2,488 -> net 2,463). The failed buy leaves 3 ghost hop
events in the logs but no state change: logs are not state.
A failed boost (6004 minimum) likewise leaves the seed
sweep paying the anchor. The failed withdraw-withheld case
also confirms the recovery path still works after a failure:
sweep and collect before the failure are unaffected, and
the buy after it is anchor-identical.

### Order dependence: execution vs bookkeeping

Order decides execution for disable and toggle pairs:
disable-then-buy fails 6020 while buy-then-disable succeeds
with the anchor tail; toggle-then-boost fails 6066 while
boost-then-toggle burns the anchor value. Order does not
decide anything for claim-buy vs buy-claim (claim pays
3,334,551 and buy pays the 1000-quote tail 5,351,132 in
both orders) or for deposit-withdraw vs withdraw-deposit
(both end at the same pool state and the same net user
deltas: -1 base, -592 quote for the round trip). For
buy-sweep vs sweep-buy and sell-sweep vs sweep-sell the
tails are identical but the final pool split differs by
exactly the seed bucket (2,488): sweeping first moves the
seed into vq before the trade accrues, sweeping after
moves the trade's accrual instead. Creator-sweep-collect
vs collect-creator-sweep ends with identical pool fields,
but the 122,160 sits in the creator vault account in one
order and in the destination account (120,938 after fees)
in the other: pool state is order-independent, token
distribution is not. Recovery transitions are clean: a
buy-harvest-withdraw-from-mint recovers the isolated
withheld 2,456 and the next buy is anchor-identical, and
the creator-sweep-collect-withdraw-withheld-buy path
recovers the same 2,456 before an anchor buy.

## Limits

- All numbers are measured on the fixture chain (split x
  boost x tf, true 3-hop, tf 100 bps unless noted) with the
  seeded pool, UVA, and GVA states described above; other
  chains, fee tables, and pool states will differ in
  magnitude, though the transition shapes (window
  invariance, sweep relocation, one-shot claims, rollback
  completeness) are structural.
- The deposit vq-nudge formula (quote_in x vq / vault
  quote balance) is a fit to five measured points, not a
  pinned mechanism: the vault quote balance is not read
  directly in this packet.
- The sync-stranded volume is observed at a fixed clock
  (ts 21 after a ts-10 sync); whether it becomes payable
  after the day boundary rolls is not measured here.
- The prior packet's "second boost falls because the
  window shrinks" suggestion is corrected here: the window
  does not move; vb1 drains.
- The prior packet's "extend is silent" note is qualified
  here: a same-size extend is silent, a real resize emits
  the ExtendEvent.
- No source change is claimed; this packet is a
  measurement of the three program images, which agree on
  every case.

Made via @slopdotcash
