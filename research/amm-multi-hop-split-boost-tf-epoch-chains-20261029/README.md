# research: multi-hop split x boost transfer-fee epoch chains under transfer fee

## Problem

The 1st-run epoch packet pinned Token-2022 transfer-fee schedule
selection on a standalone withdraw leg (`epoch >= newer.epoch ?
newer : older`, boundary inclusive, inverted pairs take the future
older schedule), but never measured it inside a chain: does the
same rule select per leg on a multi-hop route, does a schedule
change mid-walk reprice the next leg or only its withheld, and do
sweep, collect, boost, deposit, withdraw, harvest and
withdraw-from-mint each read the schedule live? This packet
answers that on the same true-3-hop split x boost x tf chain
(three_amm only, final output U3). The quote mint carries an
older schedule (epoch 0, 100bps) and a newer schedule (epoch 10,
5000bps) unless a case says otherwise; the clock epoch is a
harness setting per case, and mid-walk clock crossings and
schedule rewrites are harness field resets (cpatch steps, empty
transactions, never presented as instructions).

## Setup

- Route: three_amm (main -> pool2 -> pool3), split legs, tf
  override on the quote mint. All buys are 10^9 quote and all
  sells 10^9 base unless a case says otherwise; boosts are on the
  main pool with vq patched to 10^9 and request 10^9 unless noted.
- Fee arithmetic observed throughout: fee = ceil(amount * bps /
  10000), capped at the schedule's maximum_fee; the destination
  receives gross minus fee, and the fee lands in the destination
  account's withheld field (not the mint's -- the mint's own
  withheld stays 0 until a harvest moves ATA withheld into it).
- 51 cases, 321 receipts, 33 parts (32x10 + 1), 0 divergent
  cases across original / control / candidate. Every number
  below is measured on this chain.

## Cases

- `E-*` (11): buy-leg boundary ladder. Clock 0 / 9 / 10 / 11
  against older (0, 100) / newer (10, 5000); tied pair (10, 100) /
  (10, 5000) at clock 9 / 10; inverted pair (100, 100) /
  (50, 5000) at clock 0 / 49 / 50; future newer (10^9) at clock
  10^6; tie at epoch 0, newer (0, 5000) at clock 0.
- `S-*` (5): sell leg at clock 0 / 10, buy-sell at both
  schedules, sell-buy at the newer schedule.
- `W-*` (9): buy-sweep and buy-sweep-collect at both
  schedules; buy-sweep with a mid-walk clock crossing before
  the sweep; buy-sweep-collect with the crossing before the
  collect; buy-harvest-withdraw at both schedules; and a mixed
  harvest walk (buy at old, cross, harvest, withdraw, buy at
  new, harvest, withdraw).
- `B-*` (6): boost at both schedules, buy-boost at both,
  boost-buy at both.
- `M-*` (7): mid-walk changes. Clock-crossed buy-buy and
  sell-sell; schedule-rewritten buy-buy (newer epoch 10 -> 0)
  and boost (same rewrite); bps-rewritten buy-buy (older bps
  100 -> 200) and sweep (older bps 100 -> 5000); clock-crossed
  boost-boost.
- `F-*` (6): maximum_fee caps. Buy and sell with the older cap
  1000 at clock 0 and the newer cap 1000 at clock 10; a capped
  buy followed by a clock-crossed uncapped buy; a capped sweep
  (newer cap 1000) after an uncapped buy.
- `D-*` (4): deposit and deposit-withdraw at both schedules.
- `X-*` (3): plain-mint buy control (no tf override) and
  10^6-quote small buys at both schedules.

## Result

### 1. The rule selects per leg, boundary inclusive, in the chain

Buy tail and withheld, older (0, 100) / newer (10, 5000):

- Clock 0 and 9: tail 5,262,910,281,902 (#102's no-patch anchor),
  buyback net 4,515,471 + withheld 45,611 (gross 4,561,082),
  vault-quote withheld 10,000,000 (1% of the 10^9 input).
- Clock 10 and 11: tail 2,682,425,360,738 (#105's tf5000 tail),
  buyback net 1,151,788 + withheld 1,151,789 (gross 2,303,577),
  vault-quote withheld 500,000,000 (50% of the input).
- Tied pair (10, 100) / (10, 5000): clock 9 takes older, clock 10
  takes newer -- the boundary is inclusive at exactly
  newer.epoch.
- Inverted pair (100, 100) / (50, 5000): clock 0 and 49 take the
  older (epoch-100) schedule, clock 50 takes newer. Nothing
  validates the epoch ordering.
- Future newer (epoch 10^9) at clock 10^6: older numbers exactly
  -- a newer schedule that never activates never applies.
- Tie at epoch 0, newer (0, 5000) at clock 0: newer numbers --
  0 >= 0 already selects newer.

### 2. A buy's net input reprices the curve; a sell's gross does not move

The buy's quote input is fee'd before it reaches the curve, so
the schedule changes the price itself: old tail
5,262,910,281,902 vs new tail 2,682,425,360,738. The sell's base
input is not fee'd (the base mint carries no transfer fee), so
only the quote payout splits: gross 180,345 in both schedules,
net 178,541 + withheld 1,804 at 100bps, net 90,172 + withheld
90,173 at 5000bps (the 0.5 rounds up). The sell's buyback leg
splits the same way: gross 846 -> net 837 + 9 at 100bps, net
423 + 423 at 5000bps. Buy-sell walks: old sell pays 185,288
(net, withheld 1,872); new sell pays 91,885 (withheld 91,886).
Sell-buy at new: the second buy tails 2,682,443,927,826,
slightly above the fresh new tail -- the sell refilled the
vaults a little.

### 3. Sweep, collect, boost, deposit and withdraw each read the schedule live

- Sweep after a buy: old bucket 4,563,570 -> protocol net
  4,517,934 + withheld 45,636; new bucket 2,306,065 -> net
  1,153,032 + withheld 1,153,033. The sweep amount is the
  bucket (schedule-independent); only the fee split follows the
  schedule at sweep time.
- Collect after a creator sweep: old creator 123,394 -> collect
  net 120,938 + withheld 1,222; new -> net 30,848 + withheld
  30,849 (gross 61,697, the 0.5 rounds up).
- Mixed walks prove the read is per leg, not per case: buy at
  old, cross to epoch 10, sweep the old bucket -> protocol net
  2,281,785 + withheld 2,281,785 (50% of 4,563,570); buy at old,
  creator-sweep at old, cross, collect -> dest net 61,080 +
  withheld 61,080 (50% of 122,160).
- Boost: old burn 5,338,379,201,831 (#100 anchor, vault-quote
  net 990,000,000 + withheld 10,000,000); new burn
  2,706,767,012,738 (#100 tf5000 anchor, net 500,000,000 +
  withheld 500,000,000). Buy then vq-reset then boost: old
  5,254,679,949,141 (#105's post-buy boost, not #102's
  5,255,205,915,165 -- the vq reset changes the field the burn
  reads); new 2,685,165,599,125. Boost then buy: old tail
  5,139,964,404,268 (#102 anchor), new tail 2,639,797,163,464
  (#102 tf5000 anchor).
- Deposit: old user cost 29,610 (vault net 29,313 + withheld
  297); new user cost 58,626 (net 29,313 + withheld 29,313) --
  the deposit quote leg is fee'd on the gross the user pays.
  Withdraw: old user net 29,018 + withheld 294 (gross 29,312);
  new net 14,656 + withheld 14,656. Base legs are unchanged
  (deposit base 160,619,896, withdraw base 160,619,895 -- the
  usual 1 dust).

### 4. Harvest and withdraw-from-mint move whatever was withheld, schedule-agnostic

Buy at old, harvest the buyback and vault-quote withheld, then
withdraw-from-mint: mint pool 10,045,611 -> destination in
full, no fee on the withdrawal. Buy at new: pool 501,151,789 ->
destination in full. Mixed walk: buy at old, cross, harvest,
withdraw (10,045,611), buy at new, harvest, withdraw
(501,151,789) -- each harvest moves exactly what its preceding
legs withheld, and the second buy tails 2,585,193,161,051
(the clock-crossed second-buy value, see section 5).

### 5. A mid-walk clock crossing and a mid-walk schedule rewrite are identical

- Buy at old, cross to epoch 10, buy again: second tail
  2,585,193,161,051, buyback net 1,151,788 + withheld
  1,151,789, vault-quote withheld 500,000,000. Buy at old,
  rewrite newer epoch 10 -> 0 (clock still 0), buy again: the
  same tail, the same withheld, byte for byte. The schedule is
  read fresh at every leg; there is no per-case or per-walk
  caching.
- Sell-sell crossed: second sell pays 90,172 + withheld
  90,172 (the second sell's gross is 180,344, one less than
  the first sell's 180,345 -- the first sell moved the curve).
- Boost-boost crossed: first burn 5,338,379,201,831 (old),
  second burn 2,664,124,872,647 (new schedule on the
  post-first-burn vaults). The epoch-rewritten boost-boost
  lands on the identical second burn.
- Bps rewrite: buy at old, rewrite older bps 100 -> 200, buy
  again: second tail 5,022,653,667,871, vault-quote withheld
  20,000,000, buyback net 4,424,709 + withheld 90,301. Buy at
  old, rewrite older bps 100 -> 5000, sweep: protocol net
  2,281,785 + withheld 2,281,785 -- identical to the
  clock-crossed sweep, so a bps rewrite and a clock crossing
  are interchangeable for the fee leg.

### 6. Maximum_fee caps the fee per leg and makes bps irrelevant while it binds

- Buy with the older cap 1000 at clock 0: vault-quote withheld
  1000, buyback withheld 1000, tail 5,315,079,504,355. Buy with
  the newer cap 1000 at clock 10: the identical tail and the
  identical 1000/1000 withheld -- the cap, not the bps,
  decides the fee (compare the uncapped tails
  5,262,910,281,902 at 100bps and 2,682,425,360,738 at
  5000bps). The capped tail sits near the plain tail
  5,315,084,721,958 because the net input is 999,999,000.
- Sell with either cap 1000: user net 179,345 + withheld 1000
  (gross 180,345); the buyback leg's small fee (9 at 100bps,
  423 at 5000bps) stays under the cap and is uncapped.
- Capped buy then clock-crossed uncapped buy: second tail
  2,584,238,241,974 -- slightly below the clock-crossed
  second-buy tail 2,585,193,161,051, because the capped first
  buy left the curve in a different state. Path dependence
  survives the cap.
- Capped sweep: buy uncapped at old, cross, sweep with newer
  cap 1000 -> protocol net 4,562,570 + withheld 1000 on the
  4,563,570 bucket.

### 7. Small amounts show the ceiling rounding

10^6-quote buys: old tail 5,361,291,543, buyback net 4,515 +
withheld 46 (gross 4,561, 1% = 45.61 -> 46), vault-quote
withheld 10,000; new tail 2,707,743,055, buyback net 1,152 +
withheld 1,152 (gross 2,304, 50% = 1,152 exactly), vault-quote
withheld 500,000. The plain-mint control buy tails
5,315,084,721,958 with no withheld anywhere.

## Limits

- Clock epochs and schedule rewrites are harness settings, not
  on-chain clock or mint instructions: the packet pins how the
  program reads the schedule at each leg, not how a schedule
  reaches the mint on-chain (a real schedule change goes
  through the transfer-fee-config authority, which is not
  exercised here).
- The quote mint is the native wSOL mint in this harness; the
  epoch rule is measured on the legs that transfer_checked
  through it (buy input, buyback, sweep, collect, boost quote
  leg, deposit, withdraw). Non-quote mints' schedules are not
  measured here.
- The mint's own withheld field is 0 after every trade and only
  becomes nonzero after a harvest; all per-leg withheld figures
  above are destination-ATA withheld fields.
- No source change is proposed and no full-program
  equivalence is claimed. All amounts are receipt-level
  measurements on the original, control, and candidate
  images; the three images agree on every surface in
  every case (0 divergent).

Made via @slopdotcash
