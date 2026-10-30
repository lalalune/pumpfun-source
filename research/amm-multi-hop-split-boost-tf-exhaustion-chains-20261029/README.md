# research: multi-hop split x boost exhaustion chains under transfer fee

## Problem

On the true-3-hop split x boost x tf chain, what happens when the
boost repeatedly drains the main pool's base vault (vb1) toward
zero? This packet measures the burn as a function of the vault
balance, the hard boundary where the next boost fails, which gate
fires when the boost ATA and the vault are both short, whether a
deposit can replenish a drained vault, and what trade, sweep,
collect and claim legs do after exhaustion.

## Setup

- Route: `three_amm` only (no g4/g5), final output U3 — a true
  3-hop split x boost x tf chain. tf override is 100 bps unless a
  case says otherwise; the boost window is opened by patching the
  main pool's virtual-quote field to 10^9 (cpatch "pool").
- Fixture main pool: base vault vb1 = 673,696,395,912,745,
  quote vault vq1 = 122,946,690,720, pool fields
  [vq = -125,882, protocol_fees = 2,488, creator_fees = 123,394].
  Boost ATA starts at 10^12. Boost request is 10^9 unless a case
  says otherwise.
- 71 cases, 576 receipts, 58 parts (57 x 10 + 6). Every case runs
  on three images (original / control / candidate); control and
  candidate agree everywhere and original agrees everywhere:
  0 divergent cases.

## Cases

- Z anchors: fresh boost, fresh multi-hop buy, fresh multi-hop
  sell.
- L: base-vault ladder for the boost burn, vb1 =
  10^15 / 10^14 / 10^13 / 10^12 / 10^11 / 10^10 / 10^9 / 10^6,
  plus vb1 = 0 and vb1 = 0 then restored to 10^15.
- R: repeated boosts — 5 rounds at the fixture vault, 3 rounds
  at vb1 = 10^12.
- Q: request-size ladder 0 / 1 / 10 / 10^3 / 10^5 / 10^6 /
  10^8 / 10^10 / 10^12 at the fixture vault.
- A: boost-ATA exhaustion — ATA 10^6 (short), ATA 0, ATA exactly
  the request, ATA request + 1, ATA 2 x request over two boosts,
  ATA 2 x request + 1 over two boosts, short ATA at small vb1,
  ATA 0 with vb1 0.
- T: trade legs on a drained vault — multi-hop buy and sell at
  vb1 = 10^12 / 10^11 / 10^10 / 10^9 / 10^6 and at vb1 = 0,
  single-hop buy2 / legacy buy / sell2 / legacy sell at vb1 = 0
  and at vb1 = 10^12, plain-quote buy at vb1 = 10^12 and buy/sell
  at vb1 = 0.
- D: deposit and withdraw on a drained vault — vb1 = 0 deposit,
  vb1 = 0 deposit then boost, vb1 = 0 deposit then buy,
  vb1 = 0 withdraw, vb1 = 10^9 withdraw, vb1 = 10^9 deposit then
  boost.
- F: fee-book legs after the drain — vb1 = 0 sweep + creator
  sweep + collect, vb1 = 0 token claim, buy then vb1 = 0 then
  sweeps, failed-6088 boost then multi-hop buy.
- V: real quote-vault ladder for the boost burn — vq1 = 0 /
  10^9 / 10^12 boosts, vq1 = 0 multi-hop buy.
- X: tf variants and walk combinations — vb1 = 10^12 at tf0 /
  tf5000, vb1 = 10^12 with request 10^10, vb1 = 10^12 buy then
  boost, boost then vb1 = 0 then boost, vb1 = 10^12 with the
  window unpatched.

## Result

### The burn is linear in the base vault

At fixed vq field 10^9, tf100, request 10^9, the burn is
0.79240133% of vb1 across the whole ladder, from 10^6 to 10^15:

| vb1 | burn |
| --- | --- |
| 10^15 | 7,924,013,300,677 |
| 10^14 | 792,401,330,067 |
| 10^13 | 79,240,133,006 |
| 10^12 | 7,924,013,300 |
| 10^11 | 792,401,330 |
| 10^10 | 79,240,133 |
| 10^9 | 7,924,013 |
| 10^6 | 7,924 |

quote_after is identical across the ladder (123,936,690,720 =
vq field + real vq1 + net): the burn moves base only. Repeated
boosts decay about 1.56% per round at the fixture vault
(5,338,379,201,831 -> 5,254,441,549,265 -> 5,172,468,136,601 ->
5,092,398,150,835 -> 5,014,173,114,355) and at vb1 = 10^12
(7,924,013,300 -> 7,799,420,601 -> 7,677,743,517). A buy before
the boost lowers the next burn only through the vault it
consumed (vb1 = 10^12 buy then boost: 7,798,964,344, vs the
second-round ladder value 7,799,420,601 — a -456,257 difference
from the buy's vault movement).

### vb1 = 0 is a hard boundary, and the code depends on the leg

- Boost: 6001, 0 events.
- Multi-hop buy: 6025, 0 events. Multi-hop sell: 6025,
  2 ghost hop events.
- Single-hop buy2 and legacy buy: 6016, 0 events.
  Single-hop sell2 and legacy sell: 6025, 0 events.
- Plain-quote buy and sell at vb1 = 0: 6025 (sell: 2 ghosts).
- Restoring vb1 to 10^15 after a failed boost returns the burn
  exactly to the 10^15 ladder value (7,924,013,300,677): no
  residue from the failed boost.

### The boost ATA must end strictly positive — 6088 is a remainder rule

- ATA 10^6 with request 10^9: used 10^6 only, burn
  5,380,970,054 computed, then 6088, 2 events left, state rolled
  back.
- ATA exactly the request (10^9): 6088. ATA request + 1:
  success, remaining exactly 1.
- ATA 2 x request over two boosts: first succeeds, second
  6088 (burn 5,254,441,549,265 computed, remaining 0, rolled
  back). ATA 2 x request + 1: both succeed, final remaining 1.
- Short ATA at small vb1 (ATA 10^6, vb1 10^9): used 10^6, burn
  7,987, 6088.
- ATA 0 with vb1 0: 6002 — the ATA gate fires before the vault
  gate, matching the #101 gate order (6002 > 6001).
- A failed 6088 boost leaves no residue: the next multi-hop
  buy is the vq-patched fresh tail 5,221,217,806,636.

### Request size: 0 and 1 fail, 10 succeeds

Request 0 and request 1 both fail 6002 with 0 events even though
the ATA holds 10^12. Request 10 succeeds (used 10, net 9,
withheld 1, burn 43,482). The request ladder at the fixture
vault: 10^3 -> 5,375,583; 10^5 -> 538,095,981;
10^6 -> 5,380,970,054; 10^8 -> 537,672,386,159;
10^10 -> 49,830,102,507,836; 10^12 -> 6088 with ghost burn
598,735,502,793,632 (ATA exhausted exactly, rolled back).

### Deposit cannot rescue a zero base vault

- vb1 = 0 deposit (10^6 LP): base leg 0, quote leg net 29,313
  only (user quote -29,610, withheld 297, user LP +1,000,000).
  vb1 = 0 deposit then boost: still 6001. vb1 = 0 deposit then
  buy: still 6025. Deposit adds quote-side liquidity, never
  base, when the base vault is empty.
- vb1 = 0 withdraw (10^6 LP): base 0, quote 29,312 (user net
  +29,018, withheld 294). vb1 = 10^9 withdraw: base 238 only
  (LP-proportional), quote 29,312. vb1 = 10^9 deposit then
  boost: burn 7,924,013, exactly the 10^9 ladder value (the
  deposit's +239 base is offset by its quote leg in the burn).

### Trade legs on a drained vault: buys shrink linearly, sells explode

Multi-hop buy tails at vb1 = 10^12 / 10^11 / 10^10 / 10^9 /
10^6: 7,963,960,047 / 796,407,430 / 79,640,853 / 7,964,081 /
7,961 — linear in vb1, and the buy consumes about 0.798% of
vb1. Multi-hop sell nets at the same vb1 levels: 121,230,928 /
60,751,929,177 / 121,534,401,396 at 10^12 / 10^9 / 10^6 — the
sell price explodes as the base vault shrinks (a 10^9-base sell
against a 10^6 vault pays 121,534,401,396 quote). The sell
always adds exactly 997,498,005 to vb1 regardless of vb1 level.
Single-hop at vb1 = 10^12: buy2 costs 124,685,392 quote for
10^9 base (vq1 +123,408,078, withheld vq1 1,246,547, buyback
308); sell2 nets 121,230,716 (withheld 1,224,553). Plain-quote
buy tail at vb1 = 10^12 is 8,043,754,098 (above the tf100 tail).

### The real quote vault steers the burn

- vq1 = 0: boost 6023, 0 events; multi-hop buy 6023, 0 events.
- vq1 = 10^9 (shallow real quote pool): burn
  223,063,355,017,720, base_after 450,633,040,895,025,
  quote_after 1,990,000,000.
- vq1 = 10^12 (deep real quote pool): burn 665,634,817,992,
  quote_after 1,000,990,000,000 — below the fixture anchor
  5,338,379,201,831. The shallower the real quote pool, the
  larger the burn.

### Fee-book legs survive the drain untouched

At vb1 = 0: protocol sweep 2,488 -> net 2,463 (withheld 25),
creator sweep 123,394 -> net 122,160 (withheld 1,234), collect
122,160 -> net 120,938 (withheld 1,222), seeded token claim
3,334,551 in full. After a buy, draining vb1 to 0, then
sweeping: protocol sweep 4,563,570 -> net 4,517,934, creator
sweep in full. The fee book and the claim are independent of
the base vault.

### tf variants

At vb1 = 10^12: tf0 burn 8,003,413,241 (above tf100's
7,924,013,300), tf5000 burn 4,017,784,612 (vq1 +500,000,000,
withheld 500,000,000). Request 10^10 at vb1 = 10^12: burn
73,965,220,550, base_after 926,034,779,450, quote_after
132,846,690,720. Unpatched window at vb1 = 10^12: 6065 (the
window sum is exactly 0 without the vq patch, same as #100).

## Limits

- cpatch / seedata / bata steps are harness field resets, not
  instructions: the vb1, vq1 and ATA values are set directly in
  the fixture accounts before the measured leg runs.
- The vb1 = 0 boundary is measured on the fixture pool; a pool
  whose base vault reaches exactly 0 through real trades (rather
  than a reset) is not covered here.
- The request 0/1 -> 6002 observation is reported as measured:
  the failure code is 6002 with 0 events, but the internal
  reason (a minimum-request check vs an ATA-balance check) is
  not pinned by these receipts.
- 6088 is pinned here as a remainder rule (the ATA must end
  strictly positive), which refines #100's "request > ATA
  balance" wording: request == balance also fails.
- No source change is proposed. No claim is made about the
  whole program; only the measured legs above are asserted.

Made via @slopdotcash
