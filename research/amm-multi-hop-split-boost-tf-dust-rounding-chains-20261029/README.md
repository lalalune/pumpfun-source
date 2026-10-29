# research: dust and rounding legs on the multi-hop split x boost x transfer-fee chain

## Problem

Earlier packets pinned amounts, gates, validation, and events on the split x
boost x transfer-fee chain (TRUE 3 hops, `three_amm` only, final output U3),
but never the extremes: what happens at 1 unit of input, at a full balance,
at a 100% fee, at 1 LP, at a negative boost window, at a 2**61 claim
volume. This packet pins the dust and rounding surface fresh on that chain:
tiny-input thresholds, huge-input and overflow boundaries, per-hop dust,
transfer-fee rounding direction, deposit/withdraw extremes, boost burn
rounding, claim conversion rounding, and sweep/collect dust. All numbers
below are measured on this chain (original / control / candidate images);
all three images agree on every case.

## Cases

114 cases, 411 receipts (137 steps x 3 images), 42 parts (41x10 + 1).

- Family A: tiny multi-hop buys, quote in 1, 2, 3, 4, 5, 10, 100, 1,000,
  10,000, 1,000,000, plus the 1,000,000,000 anchor, at 100 bps; min_out
  0 vs 1 at 1 and 1,000,000.
- Family B: tiny multi-hop sells, base in 1, 2, 10, 100, 1,000, 10,000,
  100,000, 500,000, 1,000,000, plus the 1,000,000,000 anchor, at 100 bps;
  min_out 0 vs 1 at 1.
- Family C: huge inputs: buys of 10**12, 10**14, 10**15, 2**63, 2**64-1;
  sells of 10**14, 10**15, 2**63, 2**64-1.
- Family D: transfer-fee rounding on the tail: buys and sells of
  1,000,000,000 at 0, 5,000, 10,000 bps; tiny buys (100 at 100 / 5,000 /
  10,000 bps, 10 at 5,000 bps, 7 at 100 bps, 3 at 10,000 bps) and tiny
  sells (100 at 100 / 5,000 bps).
- Family E: repeated trades and round-trips: 1,000,000-quote buys x3,
  1,000-quote buys x3, buy 10**9 then sell 10**12, and that round-trip x3.
- Family F: v2 single-leg attribution (buy2/sell2 at 1, 100, 10**9)
  and legacy single legs (legbuy/legsell at 1, 100, and 10**9 buy).
- Family G: deposit/withdraw extremes: LP-out deposits of 1, 2, 10, 100,
  1,000, 1,000,000; deposits capped at 1 base / 1 quote; deposit then
  withdraw 1 LP and deposit then withdraw exactly; withdrawals of 1, 2,
  100 LP, the full seeded LP, and slippage-capped withdrawals;
  deposits of 2**62 and 10**15 LP.
- Family H: boost dust and window rounding: quote in 1, 2, 3, 5, 7, 10,
  100, 1,000, 1,000,000, 10**9 at vq 10**9; two 10**9 boosts in a row;
  10**9 boosts at vq 0, vq 1, vq -126,882 (window -1,000); the tail-pool
  boost; a 10**9 boost with min_burned 2**64-1.
- Family I: claim conversion rounding: token claims at volumes 0, 1, 3,
  7, 99, 101, 333,444, 2**60, 2**61; cashback claims at earned 1, 3, 7;
  a token claim after a 1,000-quote dust buy.
- Family J: sweep/collect dust: protocol sweep after a 1,000-quote buy,
  creator sweep after a failed 1,000-base sell, buy 100 then sweep /
  sweep / collect, buy 1,000 then sweep twice, collect after a
  1,000,000-base sell.

## Result

### Tiny-input thresholds (exact)

- Multi-hop buy: 1-2 quote fail 6039 BuyNotEnoughQuoteTokensToCoverFees
  (the fee gross-up estimate is 0); 3 quote fails 6001 ZeroBaseAmount at
  the first hop (computed base out 0); 4 quote succeeds with tail 5,463.
  Buy ladder tails (100 bps): 4 -> 5,463; 5 -> 10,929; 10 -> 38,258;
  100 -> 530,188; 1,000 -> 5,351,132; 10,000 -> 53,604,285;
  1,000,000 -> 5,361,291,543; 1,000,000,000 -> 5,262,910,281,902.
- Multi-hop sell: 1 base fails 6002 ZeroQuoteAmount; 2 base fails 6023
  Overflow; 10-10,000 base fail 6002 at the final hop after two ghost
  events (e.g. sell 10,000: hops emit 10,000 -> 9,974 -> 9,973, then the
  final hop's quote total is 0); 100,000 base succeeds with net 16
  quote; 500,000 -> net 89; 1,000,000 -> net 178; 1,000,000,000 ->
  net 178,541.
- Buy or sell with min_amount_out 0 fails 6001 ZeroBaseAmount at entry
  (multi_hop_swap.rs:266-267 requires amount > 0 and minimum > 0),
  on both sides and at every input size.
- Per-hop dust on the buy ladder (input 5): hop outs 10,959 -> 10,958
  (-1) -> 10,929 (tail -29, about 0.26%). At input 1,000,000: hop outs
  5,374,752,478 -> 5,374,723,589 (-28,889) -> 5,361,291,543 (tail
  -13,432,046, about 0.25%). The tail hop takes the ~0.25% fee; the
  middle hop loses only rounding dust.

### Transfer-fee rounding is ceiling, never floor

- Withheld fee = ceil(amount x bps / 10000), with a minimum of 1 on any
  nonzero amount: a 7-quote buy at 100 bps withholds 1 (0.07 -> 1); a
  5-quote buy withholds 1 (0.05 -> 1); a 180,345-quote sell at 5,000
  bps withholds 90,173 (90,172.5 -> 90,173); a 3,334,551-token claim at
  100 bps withholds 33,346 (33,345.51 -> 33,346); a 61,473,282,418-quote
  withdrawal at 100 bps withholds 614,732,825 (614,732,824.18 -> 614,732,825).
- Tail effect at 1,000,000,000 quote buy: 0 bps -> 5,315,084,721,958;
  100 bps -> 5,262,910,281,902; 5,000 bps -> 2,682,425,360,738 (about
  half, as the 50% fee halves the net quote in). At 100 bps on a
  100-quote buy the tail is 530,188; at 5,000 bps it is 262,359.
- A 100%-fee buy fails 6039 with 0 events (net quote 0 at the first
  hop); a 100%-fee sell emits all three hop events then fails 6004
  ExceededSlippage (net 0 < min 1 at the final check).
- Sell-side fee is taken on the final quote out (userquote withheld),
  buy-side fee on the first hop's vault in (vq1 withheld) plus the
  buyback account; the sell event stream is otherwise tf-blind.

### Repeated trades and round-trip dust

- Three 1,000-quote buys return the identical tail 5,351,132 every
  time: dust-scale trades do not move the curve measurably.
- Three 1,000,000-quote buys decay: tails 5,361,291,543 ->
  5,361,090,828 -> 5,360,890,125 (about -200,000 per repeat) as the
  vaults drain.
- Round-trip buy 10**9 / sell 10**12 leaves 4,262,910,281,902 base dust
  in U3. Three round-trips: buy tails decay 5,262,910,281,902 ->
  5,108,657,030,385 -> 4,962,112,707,627, while sell quote returns rise
  184,635,724 -> 190,148,635 -> 195,702,345.

### Huge inputs and overflow

- Buy 10**12 succeeds (tail 271,955,112,938,539); buy 10**14 succeeds
  (tail 286,334,059,446,171, only ~5% above the 10**12 tail: the tail
  pool's base vault saturates). Buy 10**15 fails at runtime with
  InsufficientFundsForRent (account_index 5), not a program error.
- Sell 10**14 succeeds (net 13,246,848,248 quote); sell 10**15 succeeds
  (net 39,869,889,652 quote).
- Buy or sell of 2**63 or 2**64-1 fails token custom 1: the token
  program log line is "insufficient funds" (the amount exceeds the
  user's balance), bubbled up as custom 0x1.
- Deposit of 2**62 LP fails 6024 Truncation; deposit of 10**15 LP fails
  token custom 1 (insufficient funds).

### Deposit / withdraw extremes

- 1 LP costs 161 base + 2 quote gross (vault net 1 + 1 withheld).
  Per-LP cost at 1,000,000 LP: 160.62 base, 0.0296 quote gross.
- Withdraw 1 LP returns 160 base, 0 quote (quote rounds to zero);
  withdraw 2 LP returns 321 base; withdraw 100 LP returns 16,061 base
  + 1 quote net (gross 2, withheld 1).
- Deposit 1,000,000 LP then withdraw exactly 1,000,000 LP returns 1
  base and 1 quote less than deposited on the vault side (base
  160,619,895 out vs 160,619,896 in; quote 29,312 out vs 29,313 net
  in): the deposit/withdraw round-trip loses 1 unit on each side
  to flooring.
- Withdrawing the full seeded 2,097,176,053,360 LP returns
  336,848,197,956,292 base and 60,858,549,593 quote net
  (61,473,282,418 gross, 614,732,825 withheld).
- Deposit capped at 1 base or 1 quote fails 6004 ExceededSlippage;
  withdrawals capped at 2**64-1 base or quote fail 6004.

### Boost dust and window rounding

- Burn ladder at vq 10**9 (window 1,000,125,882): 1 quote fails 6002
  ZeroQuoteAmount (net 0 after fee); 2 quote fails 6001 ZeroBaseAmount
  (burned 0); 3 -> 5,435; 5 -> 16,306; 7 -> 27,176; 10 -> 43,482;
  100 -> 532,666; 1,000 -> 5,375,583; 1,000,000 -> 5,380,970,054;
  10**9 -> 5,338,379,201,831. Burn per quote climbs from 1,811 (3
  quote) toward ~5,381 through 10**6, then eases to 5,338 at 10**9
  as the window binds.
- The 10**9 burn 5,338,379,201,831 is identical to the prior split x
  boost x tf packet's 10**9 burn at the same window.
- Burns fall as the window grows: window -1,000 (vq -126,882) ->
  5,381,458,147,872; window 125,882 (vq 0) -> 5,381,452,638,525;
  window 125,883 (vq 1) -> 5,381,452,638,482; window 1,000,125,882
  (vq 10**9) -> 5,338,379,201,831. A negative window still burns:
  the window sum is not clamped at zero.
- The second 10**9 boost burns 5,254,441,549,265, less than the first,
  as the window shrinks after the first burn.
- The tail-pool boost fails 6065 PoolCannotBoost (window 0), and a
  10**9 boost with min_burned 2**64-1 fails 6004 ExceededSlippage.

### Claim conversion rounding

- Conversion is exactly volume x 10 on this fixture (GVA supply 1,000 /
  sol 100 per day) at every volume, plus the 111 unclaimed: volume 1
  -> total 121; 3 -> 141; 7 -> 181; 99 -> 1,101; 101 -> 1,121; 0 -> 111;
  333,444 -> 3,334,551. The 3,334,551 total reproduces the prior
  claim packet's conversion exactly; the payout net of the 100 bps
  claim fee is 3,301,205 (33,346 withheld).
- Volume 2**60 fails token custom 1: the GVA ATA holds only 10**9, so
  the payout transfer is short. Volume 2**61 fails 6024 Truncation in
  the conversion math (2**61 x 10 overflows u64).
- Cashback claims of earned 1, 3, 7 pay exactly 1, 3, 7.
- A dust split buy leaves the UVA untouched: the token claim after a
  1,000-quote buy still pays exactly 3,334,551.

### Sweep / collect dust

- After a 100-quote buy, the protocol bucket sweeps 2,489 (2,488 seed
  + 1 accrual); after a 1,000-quote buy it sweeps 2,493 (2,488 + 5).
  The creator bucket sweeps the full 123,394; collect delivers
  120,938 (123,394 - 1,234 withheld - 1,222 withheld), with ceiling
  fees at each step (123,394 x 1% = 1,233.94 -> 1,234;
  122,160 x 1% = 1,221.6 -> 1,222).
- A second protocol sweep is a silent no-op: 0 events, no deltas.
- A failed tiny sell does not poison the following sweep: sell 1,000
  base fails 6002 with 2 ghost events, then the creator sweep still
  drains the full 123,394.

### v2 and legacy legs differ at dust scale

- A v2 buy of 1 or 100 base costs exactly 5 quote (event: curve 1,
  lp fee 1, proto fee 1, uin 4, plus 1 withheld): the v2 curve quote
  floors at 1 and the fees floor at 1 each. A v2 buy of 10**9 base
  costs 186,637 quote.
- A v2 sell of 1 or 100 base SUCCEEDS with 0 quote out (event quote 0,
  uout 0): the v2 sell path has no zero-out gate at min_out 0, where
  the multi-hop sell fails 6002 and the legacy sell fails 6004
  ExceededSlippage (min 1 > computed 0). A v2 sell of 10**9 base
  returns 178,409 quote net.
- A legacy buy of 1 or 100 base costs exactly 5 quote as well
  (vault net 2 + 3 withheld across vault/protocol/creator accounts);
  a legacy buy of 10**9 base costs 186,623 quote.

### Relation to prior packets

- Rebuild rounding: the +1 rebuild rounding seen at 5-hop split scale
  does NOT reappear here. Original, control, and candidate agree on
  all 114 cases, including every dust, rounding, and overflow case:
  0 divergent cases.
- Boost dust ladder: the prior split x boost x tf dust ladder is
  extended down to 1-quote inputs (1 -> 6002, 2 -> 6001, 3 -> 5,435)
  and across windows (negative, 0, 1, 10**9); the 10**9 burn matches
  exactly.
- Claim conversion: the prior claim packet's 3,334,551 conversion is
  reproduced exactly and extended to volumes 0 through 2**61, with
  the ceiling-fee overlay (33,346 withheld) now pinned.

## Limits

- Only the TRUE 3-hop split x boost x tf chain was measured (three_amm
  only, final output U3). Raw multi-hop metas with no hop groups fail
  6027 AccountTypeNotSupported at route validation; that is a route
  shape rejection, not a program property, so no 1-hop multi-hop cases
  are pinned here (the valid single-leg shapes are v2 and legacy).
- Thresholds are fixture-specific: pool reserves, the fee-table tier,
  the 100 bps transfer fee, and the 1,000/100 GVA day ratio all come
  from the seeded fixture. The error-code transitions and the
  ceiling-fee direction are program properties; the exact threshold
  numbers are not.
- The 6001 vs 6039 split at buy inputs 2 vs 3 is measured, not
  hand-derived: both gates exist in the buy hop (estimate > 0 ->
  6039, computed out > 0 -> 6001), and the measured transition is
  1-2 -> 6039, 3 -> 6001, >= 4 -> success.
- The final-hop zero at sell inputs <= 10,000 is measured (two ghost
  events, then 6002); the exact intermediate arithmetic that zeroes
  the final hop's total at 9,973 in but not at 99,748 in is not
  separately derived.
- No source changes, no builds, no whole-program equivalence claims.
  Only the legs and images listed above were measured.

Made via @slopdotcash
