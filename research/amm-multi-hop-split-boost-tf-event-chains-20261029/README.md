# research: event and log legs on the multi-hop split x boost x transfer-fee chain

## Problem

Earlier packets pinned amounts, gates, and validation on the split x boost x
transfer-fee chain (TRUE 3 hops, `three_amm` only, final output U3), but never
the events themselves: which legs emit what, in which order, with which
fields, and what survives in the logs when a leg fails. This packet pins the
event surface fresh on that chain: every leg's discriminator, length,
decoded fields, emission order, ghost events under faults, and the effect
of transfer fee and mode flags on event fields. All numbers below are
measured on this chain (original / control / candidate images); control and
candidate agree everywhere.

## Cases

85 cases, 345 receipts (115 steps x 3 images), 35 parts (34x10 + 5).

- A (11): multi-hop anchors and field chains — buy/sell at tf0 / tf100 /
  tf5000, 1e6 and 1e9 sizes, second buy, buy-then-sell, min-out failure.
- B (11): single-leg events — v2 buy/sell (tf0 / tf100 / tf5000), legacy
  buy (success, slippage, zero-quote), legacy sell, deposit, deposit-then-
  withdraw, deposit at tf0.
- C (8): sweep/collect events — protocol sweep, creator sweep, empty second
  sweep of each bucket, collect, empty collect, post-buy sweep,
  post-sell sweep-then-collect.
- D (5): boost events — tf0 / tf100 / tf5000 at vq 1e9, no-window failure,
  second boost.
- E (6): claim events — token claim, token claim twice, token claim after
  a buy, cashback claim, cashback claim twice, cashback claim after a sell.
- F (7): lifecycle events — init, close, extend, sync fire, sync no-fire,
  sync-then-claim, close-then-extend.
- G (11): setter events — silent buyback-config, silent mode toggles,
  fee-config event, disable event, admin-rotation event, silent
  already-set coin-creator, zero-pool coin-creator event, migrate
  failure, failed setter then trade, fee-config event then trade.
- H (13): ghost events under validation faults — pool-discriminator faults
  at each hop (buy and sell), fee-table / GlobalConfig / UVA
  discriminator faults, vault owner / owner-program / mint faults.
- I (9): mode and fee effects on events — cashback / mayhem / both first
  hop, cashback-first-mayhem-second, mayhem-first-cashback-second,
  cashback tail sell, v2 buy on a cashback pool, boost-off, global toggle
  then buy.
- J (4): leg order — full chain (buy, sweep, creator sweep, collect,
  boost, claim), sell chain, setter-then-trade, limit-fail-then-trade.

## Result

### Multi-hop hop events

- Buy hop event: disc `67f4521f2cf57777`, 508 bytes, ts 1234567890.
  At tf100, 1e9 quote in: hop 0 base 5,332,264,170,203 quote 1,000,000,000;
  hop 1 base 5,303,981,938,022 quote 5,332,264,170,203; hop 2 base
  5,262,910,281,902 quote 5,303,981,938,022. Chain equalities hold exactly:
  base of hop N equals quote of hop N+1, and hop-2 base equals the U3
  delta; hop base magnitudes equal the vault base deltas and hop quotes
  equal the vault quote deltas.
- Sell hop event: disc `3e2f370aa503dc2a`, 449 bytes, ts 1234567890.
  At tf100, 1e9 base in: hop 0 (tail pool first) base 1,000,000,000,
  quote_gross 997,999,001, quote 997,499,001; hop 1 base 997,499,001,
  quote_gross = quote = 997,498,005; hop 2 base 997,498,005, quote_gross
  182,038, quote 180,345. Chain equalities hold: base of hop N+1 equals
  quote of hop N; the tail quote equals the user quote delta at tf0.
- Emission order is route order: buy hops main, pool2, P3; sell hops P3,
  pool2, main. This order is what makes the ghost ladders below read the
  faulty hop.

### Transfer-fee asymmetry on events

- Buy hop events move with the fee (net basis). Hop base chains: tf0
  5,385,694,844,757 / 5,356,844,515,538 / 5,315,084,721,958; tf100 as above;
  tf5000 2,703,654,255,828 / 2,696,364,219,568 / 2,682,425,360,738.
- Sell hop events are fee-blind: identical at tf0, tf100, and tf5000.
  What moves is the user delta: tf0 net 180,345; tf100 net 178,541 with
  withheld 1,804; tf5000 net 90,172 with withheld 90,173. In both fee
  cases net + withheld equals the tf0 net exactly. The buyback leg is
  also net-basis: 846 (tf0) -> 837 (tf100) -> 423 (tf5000).
- Sell quote_gross vs quote gaps (observed, not decomposed): first-hop
  gap 500,000, exactly 5 bps of the 1e9 base input; tail-hop gap 1,693
  (182,038 gross vs 180,345 quote at tf0). Intermediate hops report
  gross = quote (no split on the intermediate quote leg).

### Single-leg events

- v2 buy event (1e10 quote, tf100): disc `67f4521f2cf57777`, 500 bytes —
  curve 1,824,983, lp_bps 2, lp_fee 365, proto_bps 93, proto_fee 16,973,
  qwlp 1,825,348, uin 1,847,796. v2 sell event (1e10 base, tf100): disc
  `3e2f370aa503dc2a`, 449 bytes — curve 1,824,927, lp_bps 2, lp_fee 365,
  proto_bps 93, proto_fee 16,972, quote 1,824,562, uout 1,802,115.
- Legacy buy takes (base_out, max_quote_in), not (quote_in, min_out):
  (1e9 base out, 1e10 max quote) succeeds with 1 event, disc
  `67f4521f2cf57777`, 497 bytes (11 bytes shorter than the multi-hop buy
  event), user quote -186,623, vault base -1e9. (1e9, 1) fails 6004
  ExceededSlippage with 0 events; (1e9, 0) fails 6002 ZeroQuoteAmount
  with 0 events. Legacy sell (1e10 base, min 1) succeeds with 1 event,
  disc `3e2f370aa503dc2a`, 449 bytes (disc/len only decoded).
- Deposit event: disc `78f83d531f8e6b90`, 264 bytes, base 160,619,895,224,
  quote 29,312,410 (deposit 1e9, tf100). Withdraw event: disc
  `1609851aa02c47c0`, 264 bytes, base 160,619,895,223, quote 29,312,409 —
  exactly 1 less on each leg than the deposit event, pinned as observed.

### Sweep / collect / boost events

- Sweep event: disc `82a42461e48287a5`, 185 bytes. Protocol sweep: bucket
  0, recipient = protocol, amount 2,488. Creator sweep: bucket 1, amount
  123,394. A second sweep of an emptied bucket succeeds silently with 0
  events (both buckets). An empty collect also succeeds silently with 0
  events. Collect event: disc `e8f5c2eeeada3a59`, 120 bytes, fee 122,160
  (= 123,394 - 1,234 tf100 withheld).
- Post-trade sweeps: after a buy, protocol sweep is 4,563,570; after a
  sell, protocol sweep is 3,335 and the creator sweep is still 123,394
  (sells do not move the creator bucket).
- Boost leg emits 2 events: a 512-byte BuyEvent (disc
  `67f4521f2cf57777`, 4 bytes longer than the multi-hop buy event) plus
  the 208-byte boost event (disc `3f451c16305cc2b9`). At vq 1e9,
  requested = used = 1e9, remaining 999,000,000,000; burned 5,391,870,655,895
  (tf0), 5,338,379,201,831 (tf100), 2,706,767,012,738 (tf5000). A second
  boost burns 5,255,205,915,165 at tf100 with remaining 998,000,000,000.
  With a zero window the boost fails 6065 with 0 events.

### Claim and lifecycle events

- Token claim event: disc `4facf631cd5bcee8`, 104 bytes, amount
  3,334,551, total_claimed 3,334,773, volume 0, ts 21. A second token
  claim succeeds silently with 0 events. Token claim after a buy is
  identical (split trades do not move the UVA).
- Cashback claim event: disc `e2d6f62107f293e5`, 72 bytes, amount 5,475,
  total_claimed 5,475, total_earned 5,475. A second cashback claim DOES
  emit an event with amount 0 (total_claimed stays 5,475) — the opposite
  of the token claim's silent second claim. Cashback claim after a sell
  is identical at 5,475.
- Init event: disc `86240d48e86582d8`, 80 bytes, payer = user, ts 10.
  Close event: disc `929fbdac925838f4`, 80 bytes, unclaimed 111, claimed
  222, volume 333,444, last 20, ts 10. Extend succeeds (90 -> 137 bytes)
  but emits 0 events — extend is a silent leg. Sync-fire event: disc
  `c57aa77c74515bff`, 64 bytes, claimed 222 -> 0, ts 10; sync no-fire
  (last 21) succeeds silently with 0 events. Sync-then-claim pays only
  111 with volume staying 333,444 (the pre-start reward branch is
  skipped). Close-then-extend fails 2004 with 0 events.

### Setter events: silent vs eventful

- Silent (0 events on success): update_buyback_config, mode toggles
  (mayhem and boost), already-set set_coin_creator.
- Eventful: update_fee_config, disc `5a1741233ef4bcd0`, 360 bytes (lp
  20, proto 5, creator 5, 8 recipients, authority); disable, disc
  `6bfdc14ce4ca1b68`, 53 bytes (bools all 0); update_admin, disc
  `e198ab57f63f42ea`, 80 bytes (ts, old admin, new admin); zero-pool
  set_coin_creator, disc `966bc77b7ccf66e4`, 144 bytes (creator slot
  reads the system program id — layout note, see Limits).
- Migrate on the fixture pool (no sharing-config PDA seeded) fails 3012
  with 0 events. A failed setter emits nothing and the next trade is
  anchor-identical (buyback-config outsider 6005, then a 3-event buy);
  a fee-config event followed by a buy leaves the buy events
  anchor-identical.

### Ghost events under faults (event view of #85/#88)

- Pool-discriminator ladder, buy: main fault -> 0 ghosts, pool2 -> 1,
  P3 -> 2 (all InvalidAccountData). Sell ladder: P3 -> 0, pool2 -> 1,
  main -> 2. The ghost count reads the faulty hop exactly.
- Fee-table discriminator fault -> 3002, 0 events. GlobalConfig
  discriminator fault -> InvalidAccountData, 0 events. UVA discriminator
  fault -> 3002, 0 events.
- Vault quote owner program swapped to SPL -> IncorrectProgramId, 0
  events. Vault quote mint swapped to base -> token custom 3, 0 events.
- Tail-output program owner swapped to Token-2022 ->
  ExternalAccountDataModified with 2 ghost buy events: the fault
  surfaces only at the tail hop, as a runtime error, not an Anchor gate.
- Tail-output ATA owner swapped to outsider -> full success,
  anchor-identical 3 events: the U3 ATA owner is unchecked (#88
  reproduced in event terms).
- Limit failure is different from gate failure: min-out 1e15 fails 6004
  ExceededSlippage but ALL 3 hop events remain in the failed
  transaction's logs as ghosts, while state rolls back; the next trade
  succeeds anchor-identically. Gates stop before/at the hop; the limit
  check runs after all hops.

### Mode gates in event terms (3 divergent cases)

- Cashback-flagged first hop, buy: original succeeds (3 events),
  rebuilds fail 6079 with 0 events.
- Both-flagged first hop, buy: original fails 6080 with 0 events,
  rebuilds fail 6079 with 0 events (gate order divergence, no ghosts
  either way).
- Cashback-first / mayhem-second buy: original fails 6080 with 1 ghost
  event (hop 1 succeeded, hop 2 hit the mayhem gate); rebuilds fail 6079
  with 0 events.
- Agreeing cases: mayhem-first-hop buy (all 6080, 0 events),
  mayhem-first / cashback-second buy (all 6080, 0 events), cashback tail
  sell (all 6079, 0 events — the sell's first hop is P3, so both images
  gate immediately), v2 buy on a cashback pool (all 6079, 0 events).
- Boost-off: the toggle itself is silent, then boost fails 6066 with 0
  events. A global mayhem toggle off followed by a buy leaves the buy
  events anchor-identical (global toggles do not touch pool-flagged
  events).

### Leg order

- Full chain (vq_patch 1e9): buy (3 events, window-shifted amounts) ->
  protocol sweep 4,563,570 -> creator sweep 123,394 -> collect 122,160 ->
  boost (burned 5,255,205,915,165, vq 1,000,125,882) -> token claim
  3,334,551. Sell chain: sell (3 events) -> protocol sweep 3,335 ->
  creator sweep 123,394 -> collect 122,160. Leg order is step order;
  hop order is route order.

## Limits

- Hop-event decoding covers ts / base / quote (/ quote_gross for sells).
  The remaining 508/449-byte slots (fee splits, reserve snapshots) are
  present in the receipt logs but not decoded here; the sell gross/quote
  gaps are pinned as observed values, not mechanistically decomposed.
- The zero-pool set event's creator slot (system program id) is reported
  as decoded by the shared decoder; its field layout is not separately
  resolved here.
- Legacy buy/sell events are pinned by disc/len only; their field
  layout is shared with the multi-hop events but not separately decoded.
- The reserved-fee setter event (272 bytes, #74) and create_pool event
  (344 bytes, #72) were pinned on this same chain in earlier packets and
  are not re-measured here: this builder has no reserved-setter or
  create instruction kind (set/mig are covered).
- No source changes, no builds, no whole-program equivalence claims.
  Only the legs and images listed above were measured.

Made via @slopdotcash
