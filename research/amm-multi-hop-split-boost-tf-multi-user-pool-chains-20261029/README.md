# research: cross-user and cross-pool interactions on a split x boost x tf chain

## Problem

The split x boost x tf chain at TRUE 3 hops (three_amm only, final
output U3) is by now a pinned object: its prices, buckets, claims,
setters, and account checks are measured. What is not pinned is
whether the chain cares *who* trades it or *which* chain trades
next to it. The program's accounts suggest it should not: a
multi-hop's user slot is just a signer, the UVA slot is a PDA of
that signer, the fee buckets live on the pools, and the setters
live on the single GlobalConfig. But three bindings could break
that story: the trade's UVA deserialization (#86 found trades
read the UVA), the cashback claim's ATA derivation, and the
shared first hops of two chains that differ only in their tail
pool. This packet measures all three, plus the failure-isolation
question: when one user's leg fails, does the other user's next
leg pay the anchor or a moved price?

The second user is the harness outsider key, given the full
treatment: its own real UVA PDA (seeds `[b"user_volume_accumulator",
outsider]`), its own BASE3 tail ATA (OU3), its own quote ATA
(OQUOTE, tf-mode TOKEN22 copy of userquote with the owner
swapped, plain-mode SPL native account), its own UVA-owned
cashback ATA (the ATA of its UVA PDA), and its own IMINT ATA.
The second chain is the stable chain from #81: same main and
POOL2 hops, same GlobalConfig and fee-table, but a USDC tail
hop (P2S/P3S) instead of the standard tail. Every case runs on
the original, control, and candidate images; all 58 cases agree
on all three.

## Cases

58 cases, 396 receipts, 40 parts (39x10 + 6), all at transfer
fee 100 bps unless noted. Families:

- **A, two users alternating on one chain (15).** Payer and
  outsider buy/sell anchors; buy-buy, sell-sell, buy-sell, and
  sell-buy alternations in both orders; a four-trade alternation;
  and a failed buy (min-out 10**15, error 6004) by one user
  followed by the other user's buy.
- **B, claims across users (9).** Token claim then outsider
  token claim, and the reverse; both claims twice; cashback
  claim then outsider cashback claim, and the reverse
  (plain-quote, no withdraw-withheld authority patch); payer
  sync firing then outsider claim; outsider sync firing then
  payer claim; outsider sync firing then outsider claim;
  payer close then outsider claim.
- **C, pool-shared buckets (8).** Protocol sweep then outsider
  protocol sweep, and the reverse; creator sweep then outsider
  creator sweep; outsider creator sweep then payer collect;
  sweep then outsider buy; buy then outsider protocol sweep
  then buy; buy then outsider creator sweep then payer collect
  then buy; failed outsider buy then payer protocol sweep.
- **D, standalone legs on a chain pool (10).** v2 buy/sell and
  legacy buy/sell before and after a chain buy, in both orders,
  plus v2-buy/chain-buy/v2-buy and chain-buy/v2-buy/chain-buy
  sandwiches.
- **E, two chains sharing config (9).** Stable-chain buy and
  sell anchors; chain-then-stable, stable-then-chain, and
  chain-stable-chain buy sequences; stable buy then stable
  sell; buyback-bps 7500 then both chains' buys; buy disable
  then both chains' buys; fee-config replacement then both
  chains' buys and both chains' protocol sweeps.
- **F, one user's setter reaches the other user's legs (6).**
  Buyback-bps 7500 then outsider buy; buy disable, outsider
  buy, re-enable, outsider buy; admin rotation to the outsider,
  old-admin setter, new-admin setter, outsider buy; outsider
  buy (vq patched to 10**9) then payer boost; buyback-config
  change then outsider protocol sweep; boost toggle off,
  outsider buy, toggle on, payer boost.
- **G, cross-user sell failure (1).** Payer buy, outsider
  1-unit sell with min-out 1 (error 6023), payer buy.

## Result

No rebuild divergence anywhere: original, control, and
candidate agree on every transition. The findings:

### Trades are user-blind

The outsider's buy anchor is exactly the payer's: tail
5,262,910,281,902, buyback leg 4,515,471, quote in
1,000,000,000. The outsider's sell anchor pays exactly
178,541, same as the payer's. Alternating buys decay
identically no matter who trades: 5,262,910,281,902 ->
5,072,980,706,277 -> 4,893,150,521,808 -> 4,722,716,145,040.
Alternating sells pay 178,541 then 178,540 (the +1 protocol
creep of #91, user-independent). Cross-direction legs match
the single-user values exactly: buy-then-sell (either user
second) nets 185,288, and sell-then-buy (either user second)
tails 5,262,946,545,784. The chain's price depends on pool
state only; the signer's identity never enters it.

### Claims are per-user and order-independent

The payer token claim pays 3,334,551 (net 3,301,205 after
33,346 withheld) and the outsider token claim pays 1,050
(net 1,039 after 11 withheld) from its own UVA
(100 x 1000/100 + 50), in either order, and second claims by
either user are silent with 0 deltas and 0 events. Cashback
claims pay 5,475 to the payer and 777 to the outsider from
their own UVA ATAs, in either order. One user's sync firing
leaves the other user's claim untouched: payer sync firing
(claimed 222 -> 0) still leaves the outsider claim at 1,050,
and outsider sync firing (claimed 100 -> 0, has 1 -> 0)
still leaves the payer claim at 3,334,551. After its own
sync fires, the outsider's next claim pays only the 50
unclaimed (net 49) with volume 100 stranded -- last_update
10 < GVA start 20 skips the reward branch, the #73
mechanism on the second user's accumulator. One user's
close leaves the other user's claim untouched (outsider
claim still 1,050 after the payer's UVA is closed).

The outsider's cashback ATA must be the ATA of its UVA PDA:
an arbitrary key for that account fails with Anchor 2009
(measured during construction, fixed by deriving the ATA
the same way the payer's uvata is derived). The token
claim's destination ATA is the ATA of the user key, and the
trade's UVA slot must be the PDA of the trading user
(#86's 2006 seeds gate); with those three bindings
satisfied, the second user's legs succeed exactly like the
first user's.

### Fee buckets are pool-shared, not per-user

A protocol sweep by either user drains the seed 2,488
(net 2,463) and the other user's sweep is a silent no-op
(0 events), in either order. The same holds for the creator
sweep (123,394 -> net 122,160), and the payer collect after
an outsider creator sweep pays 122,160 -> net 120,938:
collect is user-blind. A sweep by either user is
price-neutral for the other user's next buy (the anchor
5,262,910,281,902), and a buy's accrual swept by the other
user leaves the next buy at the second-buy tail
5,072,980,706,277 -- the same as if the buyer had swept
it themselves. Buckets belong to pools; users only drain
them.

### Standalone legs move the next chain trade exactly like chain legs

A v2 buy (cost 186,637 for 10**9 base out) and a legacy buy
(cost 186,623) both move the next chain buy to tail
5,262,894,882,207 (anchor -539,695), and a v2 sell and a
legacy sell (both pay 178,409) both move the next chain
buy to 5,262,925,678,490 (anchor +15,396,588). The
mechanism is visible in the vault deltas: legacy legs move
real vault balances (vb1 +/-10**9, vq1 -/+~182k) but leave
virtual reserves and accrued fields untouched, while v2
legs also move virtual vq and accrued fields -- yet the
next chain tail is identical, because chain pricing keys
off the real base vault and the virtual quote reserves,
not the real quote vault (legacy vs v2 real-quote moves
differ by 1,397 with zero tail effect). Chain-then-v2
costs 189,628 (buy) / pays 181,267 (sell) versus 186,637 /
178,409 standalone: the chain trade moves the curve
against the next buy and in favor of the next sell, the
#92 path-dependence on a shared pool. A v2 leg sandwiched
between chain buys leaves the second chain tail at
5,072,965,739,290, below the chain-chain second tail
5,072,980,706,277, because the v2 leg's full-size vb1 move
stacks on the chain's intermediate move.

### Two chains interfere only through their shared hops

The stable chain's buy and sell anchors equal the standard
chain's (5,262,910,281,902 / 178,541). The second trade
through either chain is 5,181,110,886,130: the shared
main/POOL2 hops decay, but the untouched tail hop prices
fresh, so it sits above the chain-chain second tail
5,072,980,706,277. The third trade (chain, stable, chain)
is 4,994,726,580,728. A stable buy then stable sell nets
185,288, same as the standard chain. A buyback-bps change
to 7500 scales both chains' buyback legs to 6,773,206
with tails unchanged; a buy disable fails both chains
with 6020; a fee-config change leaves both buys at their
anchors but breaks both protocol sweeps (main and
stable-tail) with 6013. Shared config and shared hops are
the whole interference surface; the tail pools are
independent.

### Setters reach the other user; boosts do not care who bought

A buyback-bps change to 7500 scales the outsider's
buyback leg to 6,773,206. A buy disable fails the
outsider's buy with 6020, and re-enabling restores the
anchor. An admin rotation to the outsider makes the old
admin's setter fail 6005 and the new admin's succeed
while the outsider's buy stays at the anchor. A
buyback-config change leaves the outsider's protocol
sweep untouched (setter-independent, admin-independent,
as in #75). An outsider buy leaves the payer's boost at
the buy-first value 5,255,205,915,165 -- exactly the #92
buy-first burn: boost burn depends on pool state only,
not on who bought. A boost toggle off does not gate the
outsider's buy, and the boost after re-enabling burns
the same 5,255,205,915,165.

### Failures are isolated across users, with distinct ghost shapes

A failed buy (6004 slippage) by one user rolls back fully
and the other user's next buy is the anchor, in either
order; a failed outsider buy leaves the payer's protocol
sweep at the seed 2,488. A failed 1-unit outsider sell
(6023) leaves the payer's next buy at the second-buy
tail 5,072,980,706,277. The failure shapes differ:
disable-gate failures (6020) and the 6023 sell failure
emit 0 events, while the 6004 buy slippage failure emits
all 3 hop events with zero deltas -- the #90 ghost
ladder, with gate failures silent and limit failures
fully ghosted, now confirmed across users.

## Limits

- The second user is one fixed outsider key with the
  fixture balances (10**12 lamports, 10**15 quote, 10**15
  BASE3); no second-user case is measured at dust or
  whale sizes, and no third user is introduced.
- The second chain differs from the first only in its
  tail hop (USDC stable tail vs standard tail); two
  chains sharing no hop, and two chains with different
  fee-tables, are not measured here.
- The outsider's standalone legs (v2, legacy, deposit)
  are not measured: the outsider trades only through the
  multi-hop route, sweeps, and claims.
- The 6023 sell failure is a single measured point (1
  base unit, min-out 1 after a buy); its exact raising
  site is not pinned beyond the error code and the
  0-event shape.
- The chain-pricing claim (real base vault + virtual
  quote reserves, real quote vault irrelevant) is
  inferred from the legacy-vs-v2 tail identity plus the
  vault deltas, not from a pricing-formula derivation.

Made via @slopdotcash
