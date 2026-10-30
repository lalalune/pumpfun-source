# Split x boost x tf event and log validation chains at TRUE 5 hops

3rd-run packet #144. This packet extends the #90 event/log validation
findings (event discriminators, field values, log ordering, event
counts per leg, ghost events on failures) from the TRUE 3-hop chain to
the TRUE 5-hop split x boost x tf chain: `three_amm + g4 + g5`, final
output U5. Route verified in the builder (`build_route` appends the g4
and g5 hop groups to `three_amm`); the name, README and title all say
5-hop because the route really is 5 hops (#61 was 4 hops despite its
3-hop name; that mistake is not repeated here).

## Problem

At depth 3, #90 pinned which legs emit events, what each event carries,
and which failures leave "ghost" events in the logs of a failed
transaction. At depth 5 the open questions were: does the hop-event
chain equality survive two more hops, does the ghost-event ladder
mirror between buy and sell directions, do transfer-fee effects show up
in hop event fields or only in single-leg event fields, and which legs
stay silent at depth 5? This packet measures all of that on the split
chain (quote mint carries a 100 bps transfer-fee config by default;
buyback routes through the TOKEN22 ATA).

## Cases

105 cases, 411 receipts (3 images x 137 steps), 42 parts of 10
receipts (41x10 + 1). Families:

- **A, 5-hop buy/sell anchors:** buy/sell at tf 0/100/5000, 1e6 and 1e9
  sizes, second buy, buy-then-sell, min-out failures.
- **B, single-leg events:** v2 buy/sell, legacy buy/sell (incl. slippage
  6004 and zero-quote 6002), deposit/withdraw.
- **C, sweep/collect events:** protocol/creator sweeps, second sweeps,
  empty collect, buy/sell-then-sweep/collect chains.
- **D, boost events:** tf 0/100/5000, no-window 6065, second boost.
- **E, claim events:** token claim, twice, after buy, bps 5000;
  cashback claim, twice, after sell.
- **F, lifecycle events:** init, close, extend 90 -> 137, sync
  fire/no-fire, sync-then-claim, close-then-extend, close-then-claim.
- **G, setter events:** silent buyback-config and mode toggles vs
  emitting fee-config/disable/admin-rotation, set on a normal and a
  zero-creator pool, migrate failure, failed-setter-then-trade.
- **H, ghost events:** pool discriminator faults at main/P2/P4/P5 in
  both directions, pool owner fault, fee-table/GlobalConfig/UVA/GVA
  discriminator faults, vault owner/mint faults per hop, fee-length
  gates 3001/3003/6083, disable bits.
- **I, mode/fee effects on events:** cashback/mayhem/both pools at
  main and terminal positions, buy2 on a cashback pool, boost-off
  then boost/buy.
- **J, leg-order chains:** buy/sell-then-sweep/collect, setter-then-trade,
  fail-then-trade.
- **T, tf variants:** buy/sell/buy2/boost and pool-disc fault at
  tf 5000.

## Result

All cases agree across the original, control and candidate images
except the two divergent cases below. `verify.py` re-checks every
receipt independently (signatures, deltas, withheld, event fields,
error codes, rollback, 3-image agreement).

### Hop events and chain equality

- 5-hop buy emits exactly 5 hop events, all discriminator
  `67f4521f2cf57777`, length 508 each, in execution order. The chain
  equality holds at depth 5: hop-N base == hop-(N+1) quote, for all
  four joins. First hop (tf 100): base 5,332,264,170,203, quote
  1,000,000,000; tail (hop 5 base) 5,207,955,235,891, matching the
  standing 5-hop anchor.
- 5-hop sell emits exactly 5 hop events, all discriminator
  `3e2f370aa503dc2a`, length 449 each, tail-first (the first emitted
  event is the terminal hop). First emitted: base 1,000,000,000,
  quote fields 997,999,001 / 997,499,001; last emitted: base
  997,496,013, quote fields 182,038 / 180,345.
- Buy hop event amounts move with tf: hop-1 base 5,385,694,844,757 at
  tf 0, 5,332,264,170,203 at tf 100, 2,703,654,255,828 at tf 5000;
  tails 5,259,040,470,738 / 5,207,955,235,891 / 2,668,075,748,732.
  The quote field shows the gross 1,000,000,000 at every tf.
- Sell hop event fields are tf-blind: byte-identical at tf 0, 100 and
  5000, at 1e6 and 1e9 sizes. The two quote fields (@104/@112) differ
  on the first-executed hop (500,000 at 1e9; 500 at 1e6) and on the
  last-executed hop (1,693 at 1e9; 2 at 1e6) and are equal on the three
  middle hops; the gap is not tf (it is present at tf 0).
- Single-leg v2 event fields are also tf-blind (identical at tf 0,
  100, 5000): v2 buy length 500, curve 1,824,983, lp_bps 2, lp_fee
  365, proto_bps 93, proto_fee 16,973, qwlp 1,825,348, uin 1,847,796;
  v2 sell length 449, curve 1,824,927, lp_fee 365, proto_fee 16,972,
  quote 1,824,562, uout 1,802,115. Legacy buy length 497, legacy sell
  length 449 (disc/len only). Legacy buy slippage fails 6004 with 0
  events; legacy buy with zero quote fails 6002 with 0 events.
- Deposit event length 264 (base 160,619,895,224, quote 29,312,410);
  withdraw event length 264 (base 160,619,895,223, quote 29,312,409):
  exactly 1 less on each leg than the deposit.

### Sweep, collect, boost, claim, lifecycle, setter events

- Sweep event discriminator `82a42461e48287a5`, length 185: protocol
  sweep 2,488 (bucket 0), creator sweep 123,394 (bucket 1), post-buy
  protocol sweep 4,563,570. A second sweep of an emptied bucket
  succeeds with 0 events; an empty collect succeeds with 0 events.
  Collect event discriminator `e8f5c2eeeada3a59`, length 120, fee
  122,160.
- Boost emits exactly 2 events: a leading 512-byte BuyEvent
  (`67f4521f2cf57777`) plus the boost event (`3f451c16305cc2b9`,
  length 208). Burn at vq 10^9: 5,391,870,655,895 at tf 0,
  5,338,379,201,831 at tf 100, 2,706,767,012,738 at tf 5000; second
  boost burn 5,254,441,549,265 with remaining 998,000,000,000. A
  no-window boost fails 6065 with 0 events; a boost-disabled boost
  fails 6066 with 0 events, while a boost-disabled buy still emits
  all 5 hop events.
- Token claim event length 104, amount 3,334,551, total_claimed
  3,334,773; a second token claim is silent (0 events). Cashback
  claim event length 72, amount 5,475; a second cashback claim still
  emits an event, with amount 0. Claim event amounts are identical
  at claim bps 100 and 5000.
- Init event length 80; close event length 80 (unc 111, claimed 222,
  vol 333,444, last 20); sync event length 64 (before 222, after 0)
  only when it fires; sync-no-fire emits 0 events; extend emits 0
  events. Close-then-extend fails 2004 with 0 events;
  close-then-claim fails 3012 with 0 events.
- Silent setters: buyback-config, mayhem toggle, cashback toggle,
  boost toggle, and set_coin_creator success all emit 0 events.
  Emitting setters: update_fee_config length 360 (lp 20, proto 5,
  creator 5); disable event discriminator `6bfdc14ce4ca1b68`, length
  53, bools [1, 0, 0, 0, 0]; update_admin length 80, and it fires even
  when old == new (rotation to self). Set on a zero-creator pool
  fails 6028 with 0 events; migrate fails 3012 with 0 events.

### Ghost events under faults

- Pool discriminator fault, buy direction: main 0, P2 1, P4 3, P5 4
  ghost hop events (error InvalidAccountData). Sell direction is
  the exact mirror: main 4, P2 3, P4 1, P5 0. Pool owner fault: buy
  main 0 events (6027), sell main 4 events (6027).
- Fee-table and GlobalConfig discriminator faults leave 0 events in
  both directions (3002 / InvalidAccountData): both are validated
  before any hop executes. Fee-length gates 3001/3003/6083 also
  leave 0 events. A UVA discriminator fault leaves all 5 buy events
  with success: trades are UVA-blind. A GVA discriminator fault on
  a token claim fails 3002 with 0 events.
- Vault faults: quote-vault owner fault at hop 3 leaves 2 buy events
  (3007); base-vault mint fault at hop 3 leaves 3 buy events
  (custom 3); quote-vault mint fault on the terminal hop leaves 1
  sell event (custom 3).
- Disable gates leave 0 events: buy bit fails 6020, sell bit fails
  6021; a buy-bit disable followed by a sell still emits all 5 sell
  events (the gate is direction-specific).
- Slippage failures still log the full chain: a buy min-out failure
  (ProgramFailedToComplete) and a sell min-out failure (6004) each
  log all 5 hop events in the failed transaction, and a failed buy
  followed by a good buy re-emits the full anchor chain.

### Divergent cases (2)

- `i-cb-main-buy` and `i-cb-main-sell`: the cashback-mode main-pool
  legs differ between the original image and the rebuilt images
  (mode-gate behaviour, same class as #109/#119). Every other case
  agrees on all three images, including all event fields above.

## Limits

- The pool-discriminator ghost ladder was measured at main, P2, P4
  and P5; the P3 position was not separately pinned (the ladder
  implies 2 buy / 2 sell events there, but that is interpolation,
  not measurement).
- The sell event's two quote fields (@104/@112) are positional
  decodes; the gap between them is reported as measured and is not
  attributed to a specific fee in this packet.
- Set_coin_creator success is silent in this harness (no metaplex
  event observed); the packet does not claim anything about
  metaplex-side emission.
- No source-change proposal is made and no full-program equivalence
  is claimed; the packet pins measured event/log behaviour only.

Made via @slopdotcash
