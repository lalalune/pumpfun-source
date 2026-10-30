# Split x boost x tf dust and precision chains at TRUE 5 hops

## Problem

The 3-hop dust/precision packet (#91) pinned the tiny-amount,
rounding-boundary, and dust-threshold behaviour of the split x boost x
tf chain. This packet re-measures the same families on a TRUE 5-hop
route (three_amm + g4 + g5, final output U5): does the extra depth move
any threshold, change the per-hop dust attribution, or change the
accumulated precision loss? Every case runs on the original, control,
and candidate images; all three agree on every case in this packet
(0 divergent cases).

## Cases

117 cases, 140 steps, 420 receipts, 42 parts (42x10):

- **A — tiny multi-hop buys (13 cases):** quote inputs 1, 2, 3, 4, 5,
  10, 100, 1,000, 10,000, 1,000,000, 1,000,000,000, plus min_amount_out 0
  at 1 and at 1,000,000.
- **B — tiny multi-hop sells (11 cases):** base inputs 1, 2, 10, 100,
  1,000, 10,000, 100,000, 500,000, 1,000,000, 1,000,000,000, plus
  min_amount_out 0 at 1.
- **C — huge inputs (9 cases):** buys and sells of 10^12, 10^14, 10^15,
  2^63, 2^64-1.
- **D — transfer-fee variants (14 cases):** buy/sell at bps 0, 100,
  5000, 10000; tiny buys at 100/5000/10000 bps; tiny sells at 100/5000 bps.
- **E — repeated trades and round trips (4 cases):** 1,000,000-quote
  buy x3, 1,000-quote buy x3, buy 10^9 / sell 10^12 round trip, and the
  round trip repeated 3 times.
- **F — single-leg attribution (11 cases):** v2 buy/sell and legacy
  buy/sell legs at 1, 100, and 10^9.
- **G — deposit/withdraw extremes (18 cases):** 1-LP to 10^6-LP
  deposits, capped deposits, exact and full-LP withdrawals, slippage
  caps, 2^62-LP and 10^15-LP deposits.
- **H — boost dust and window (19 cases):** main-pool boosts of 1 to
  10^9 quote, second 10^9 boost, window patches, min-fail, and the
  terminal-hop (P5) boost at a fresh window, a patched 10^9 window,
  and 1/100-quote inputs.
- **I — claim rounding (13 cases):** token-incentive claims at volumes
  0, 1, 3, 7, 99, 101, 333,444, 2^60, 2^61; cashback claims of 1, 3, 7;
  a claim after a dust split buy.
- **J — sweep/collect dust (5 cases):** sweep/collect after tiny buys
  and a tiny sell, a second sweep after a drain, and the full
  buy-sweep-collect chain after a 100-quote buy.

## Result

**Route confirmation.** Successful 5-hop swaps emit exactly 5 hop
events: buys disc 67f4521f2cf57777 (len 508), sells disc
3e2f370aa503dc2a (len 449). Failed tiny sells emit 4 ghost events
before the final-hop failure (the 3-hop packet saw 2 ghosts).

**Buy thresholds do not move with depth.** Buys of 1-2 quote fail
6039, a buy of 3 fails 6001 at the first hop, and a buy of 4 succeeds.
Buy tails at depth 5 (3-hop values in parentheses): 4 -> 5,461
(5,463), 5 -> 10,927 (10,929), 10 -> 38,256 (38,258), 100 -> 530,184
(530,188), 1,000 -> 5,351,128 (5,351,132), 10,000 -> 53,604,277
(53,604,285), 1,000,000 -> 5,361,233,911 (5,361,291,543), 1,000,000,000
-> 5,207,955,235,891 (5,262,910,281,902). Every tail is 2-55M lower
than at depth 3: the two extra hops each cost a small rounding dust.

**Per-hop dust attribution.** At a 5-quote input the hop outputs are
10,959 -> 10,958 -> 10,957 -> 10,956 -> tail 10,927: middle hops lose
exactly 1 each, and the terminal hop loses 29 (the ~0.25% fee lands at
the terminal hop, as at depth 3). At a 1,000,000-quote input the hop
outputs are 5,374,752,478 -> 5,374,723,589 -> 5,374,694,701 ->
5,374,665,813 -> tail 5,361,233,911: middle hops lose ~28,888 each,
the terminal hop loses 13,431,902 (~0.25%). At 10^9 the chain is
5,332,264,170,203 -> 5,303,981,938,022 -> 5,275,998,139,846 ->
5,248,308,076,854 -> 5,207,955,235,891.

**Sell thresholds do not move with depth.** Sells of 1 fail 6002, of
2 fail 6023, of 10-10,000 fail 6002 at the final hop after 4 ghost
events, and of 100,000 succeed with net 16 quote; 500,000 -> 89,
1,000,000 -> 178, 1,000,000,000 -> 178,541 (all identical to depth 3).

**Huge inputs.** Buy 10^12 succeeds with tail 175,991,970,811,038
(depth 3: 271,955,112,938,539); buy 10^14 succeeds with tail
181,903,371,987,611 (depth 3: 286,334,059,446,171) — the depth-5 tail
saturates far lower. Buy 10^15 fails at runtime with
InsufficientFundsForRent (account_index 9, vs 5 at depth 3) after all
5 hop events are logged, not a program error. 2^63 and 2^64-1 fail
token custom 1 on both buy and sell. Sell 10^14 succeeds with net
11,538,890,655 (depth 3: 13,246,848,248); sell 10^15 succeeds with net
27,582,118,449 (depth 3: 39,869,889,652).

**Transfer-fee rounding is ceiling, not floor, at depth 5.** A 7-quote
buy at 100 bps withholds 1 (0.07 -> 1); a 3,334,551-token claim at 100
bps withholds 33,346 (33,345.51 -> 33,346), net 3,301,205. A 100%-fee
buy fails 6039 with 0 events; a 100%-fee sell emits all 5 hop events
then fails 6004. tf0 buy tail 5,259,040,470,738; tf5000 buy tail
2,668,075,748,732. Tiny tf buys: 100 at 5000 bps -> 262,355, 10 at
5000 bps -> 16,392, 7 at 100 bps -> 21,859; 3 at 10000 bps fails 6039.

**Repeated trades.** Three 1,000,000-quote buys give tails
5,361,233,911 -> 5,360,917,947 -> 5,360,602,013 (decay ~315,964 per
repeat, vs ~200,000 at depth 3); three 1,000-quote buys give the
identical tail 5,351,128 each time. A buy-10^9 / sell-10^12 round trip
leaves 4,207,955,235,891 base dust; repeating the round trip, sell
proceeds grow 188,160,784 -> 196,899,508 -> 205,733,334 per cycle
(depth-3 first-cycle proceeds were 184,635,724).

**Single legs are depth-independent.** A v2 buy of 1 or 100 base costs
exactly 5 quote; a v2 sell of 1 or 100 base succeeds with 0 quote out;
a legacy sell of 1 or 100 base fails 6004. All identical to depth 3.

**Deposit/withdraw extremes are depth-independent.** A 1-LP deposit
costs 161 base + 2 quote gross; withdrawing exactly the deposited
1,000,000 LP returns 1 base and 1 quote gross less than deposited;
withdrawing the full seeded 2,097,176,053,360 LP returns
336,848,197,956,292 base and 60,858,549,593 quote net (61,473,282,418
gross, 614,732,825 withheld at 100 bps). Deposit caps of 1 base or 1
quote fail 6004; a 2^62-LP deposit fails 6024; a 10^15-LP deposit
fails token custom 1.

**Boost dust.** Main-pool boost ladder is identical to depth 3:
1 -> 6002, 2 -> 6001 (burned 0), 3 -> 5,435, 10 -> 43,482, 100 ->
532,666, 1,000,000 -> 5,380,970,054, 10^9 -> 5,338,379,201,831, and
the second 10^9 boost burns 5,254,441,549,265. The terminal-hop (P5)
boost pins the same dust scale at depth 5: a fresh window fails 6065,
a vq5 patch of 10^9 burns 999,997,999 for a 10^9 quote, a 1-quote boost
with the window open fails 6001, and a 100-quote boost burns 98.

**Claim rounding is depth-independent.** Token claims: volume 0 ->
111, 1 -> 121, 3 -> 141, 7 -> 181, 99 -> 1,101, 101 -> 1,121,
333,444 -> 3,334,551; 2^60 fails token custom 1, 2^61 fails 6024.
Cashback claims of 1, 3, 7 pay exactly 1, 3, 7. A claim after a dust
split buy still pays exactly 3,334,551.

**Sweep/collect dust is conserved.** After a 100-quote buy the
protocol bucket sweeps 2,489, the creator bucket sweeps 123,394, and
collect delivers 120,938 (123,394 - 1,234 - 1,222 withheld). A second
protocol sweep after a drain is a silent no-op (0 events), and a
failed tiny sell does not poison the following creator sweep.

## Limits

- All amounts are measured on this fixture (seeded pools, 10^12/10^12
  vaults, tf100 default where noted); other pool states will give
  different absolute tails, but the thresholds (6039/6001/6002/6023
  boundaries, ceiling withholding, terminal-hop fee attribution) are
  structural.
- No divergence between original, control, and candidate was found in
  this packet; the depth-5 deltas above are measured differences from
  the 3-hop packet's values, not image divergences.

Made via @slopdotcash
