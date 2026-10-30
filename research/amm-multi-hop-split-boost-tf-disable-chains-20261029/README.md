# research: split-chain admin disable — each bit gates only its own leg, boost takes the buy gate, sweep/collect/claim ignore disable, clearing restores the anchor

## Problem

The brief for this packet was to compose the 2nd-run #46 admin
disable setter bridge onto the split×boost×tf chain (true 3 hops,
`three_amm` only, final output U3): as the five disable bits
(create/deposit/withdraw/buy/sell) are set on the GlobalConfig,
which legs of the chain stop, what happens when two bits are set
at once, does disable state leak into boost, sweep, collect, or
claims, and does clearing the bits restore the chain exactly?
Measurement splits the answer five ways. Each bit gates only
its own leg: buy → buy legs 6020, sell → sell legs 6021,
deposit → deposit 6018, withdraw → withdraw 6019, and the
create bit gates nothing on pools that already exist. Bit
combinations gate per-leg with no cross-leg priority: every
set bit fires its own code on its own leg, and unset legs keep
working. Disable state does not leak into sweep, collect, or
either claim — all of those pay full amounts under all five
bits at once — and it reaches boost only through the buy gate:
boost under the buy bit fails 6020, under the sell or deposit
bit it burns the exact anchor amount. Clearing all bits
restores the chain: the disable byte returns to 0 in every
case, and every tail leg that runs on an untouched fixture
reproduces its anchor byte-for-byte.

Route confirmation (from the builder itself): the fixture route
calls `three_amm` only and appends no g4/g5 hop group — 3 hop
groups, final output U3. This packet does not repeat 3rd #61's
naming error (a "3-hop" packet whose builder actually appended a
P4 group).

One scope note, measured first: the fixture starts with
disable_flags 0 (GlobalConfig byte 56), and the setter writes
only that byte. The five gated bits are 1 (create), 2
(deposit), 4 (withdraw), 8 (buy), 16 (sell); bits 32/64/128
were not re-measured here. The cashback claim cases run in
plain-quote mode with the withdraw-withheld authority patch
skipped (`no_ww`): that patch writes the payer into the
quote-mint transfer-fee authority slot, which corrupts SPL
mint parsing in plain mode (measured in 3rd #76: claim fails
`InvalidAccountData` with the patch, pays 5475 without it).
The token claim case runs under tf100 with a separate
claim-bps override, as in 3rd #67.

## Cases

25 cases, 113 steps, 339 receipts (113 steps × 3 images), 34
parts (33×10 + 9). All cases run the same steps on the
original, control (#424) and candidate (#427) images. All
cases run under tf100 on the quote mint unless noted (family
C's cashback cases run in plain-quote mode, see above). The
bools order for the setter is [create, deposit, withdraw,
buy, sell].

Family A — chain anchors (3 cases):

- `a-anchor-buy`: mhbuy3 of 10^9, no disable. Tail output U3
  +5,262,910,281,902, buyback +4,515,471, withheld vq1
  10,000,000 / buyback 45,611, fee-payer delta −1,849,400.
- `a-anchor-sell`: mhsell3 of 10^9, no disable. Receipt
  178,541 (gross 180,345, withheld userquote 1,804 / buyback
  9), buyback +837.
- `a-anchor-dep-wd`: deposit then withdraw of 10^9 LP, no
  disable. Deposit: user LP +1,000,000,000, quote
  −29,608,495. Withdraw: user LP −1,000,000,000, quote
  +29,019,284.

Family D — one disable bit at a time (5 cases):

- `d-buy`: buy bit on → mhbuy3 fails 6020, mhsell3
  succeeds; bits cleared → mhbuy3 succeeds again.
- `d-sell`: sell bit on → mhsell3 fails 6021, mhbuy3
  succeeds; bits cleared → mhsell3 succeeds again.
- `d-dep`: deposit bit on → deposit fails 6018, mhbuy3
  succeeds; bits cleared → deposit succeeds again.
- `d-wd`: withdraw bit on → withdraw fails 6019, mhbuy3
  succeeds; bits cleared → deposit then withdraw succeed.
- `d-create`: create bit on → mhbuy3, mhsell3, deposit,
  and withdraw all succeed (the create bit gates no
  existing-pool leg); bits cleared → mhbuy3 succeeds.

Family X — bit combinations (5 cases):

- `x-buy-sell`: buy+sell bits → mhbuy3 fails 6020,
  mhsell3 fails 6021; cleared → mhbuy3 reproduces the
  anchor byte-for-byte.
- `x-buy-dep`: buy+deposit bits → mhbuy3 fails 6020,
  deposit fails 6018, mhsell3 succeeds; cleared → mhbuy3
  succeeds.
- `x-sell-wd`: sell+withdraw bits → deposit succeeds,
  withdraw fails 6019, mhsell3 fails 6021, mhbuy3 succeeds;
  cleared → withdraw succeeds.
- `x-create-dep`: create+deposit bits → deposit fails
  6018 only, both trades succeed; cleared → deposit
  succeeds.
- `x-all`: all five bits → mhbuy3 fails 6020, mhsell3
  fails 6021, deposit fails 6018, withdraw fails 6019
  (the gate fires even with no deposit first in the case);
  cleared → mhbuy3 reproduces the anchor byte-for-byte.

Family B — disable state vs boost / sweep / collect
(5 cases, boost cases patch main pool
virtual_quote_reserves to 10^9):

- `b-buy-boost`: buy bit on → boost fails 6020 (the buy
  gate inside boost: original `boost.rs:240`, rebuilds
  `boost_burn.rs:34`); cleared → boost burns exactly
  5,338,379,201,831, the anchor amount.
- `b-sell-boost`: sell bit on → boost burns exactly
  5,338,379,201,831; cleared → mhbuy3 succeeds.
- `b-dep-boost`: deposit bit on → boost burns exactly
  5,338,379,201,831; cleared → deposit succeeds.
- `b-sweep`: mhbuy3 seeds fees, then buy+sell bits on →
  protocol sweep 4,563,570 (net 4,517,934, withheld
  45,636), creator sweep 123,394 (net 122,160, withheld
  1,234), collect 122,160 (dest net 120,938, withheld
  1,222); cleared → mhbuy3 succeeds.
- `b-all-sweep`: same sweep/collect sequence under all
  five bits, same amounts; cleared → mhbuy3 succeeds.

Family C — disable state vs claims (3 cases):

- `c-tclaim-dis`: all five bits on → token claim pays
  gross 3,334,551, net 3,301,205 (withheld 33,346) at
  tf100, exactly the 3rd #67 tf100 claim; cleared.
- `c-cclaim-dis`: all five bits on → cashback claim pays
  5,475 in full (plain mode); cleared.
- `c-cclaim-buy`: buy bit on → cashback claim pays 5,475
  in full; cleared.

Family G — setter gates and the DisableEvent pin
(3 cases):

- `g-outsider`: buy bit set by a non-admin → 6005,
  mhbuy3 then succeeds (no disable was set).
- `g-unsigned`: buy bit set with the admin account not
  signing → 3010, mhbuy3 then succeeds.
- `g-event`: buy bit set then cleared by the admin →
  DisableEvent pinned both times: disc
  `6bfdc14ce4ca1b68`, 53 bytes, ts 1234567890, bools
  [0, 0, 0, 1, 0] then [0, 0, 0, 0, 0]; tail mhbuy3
  reproduces the anchor byte-for-byte.

Family R — full roundtrip (1 case):

- `r-full`: all five bits on → mhbuy3 fails 6020,
  mhsell3 fails 6021, deposit fails 6018; cleared →
  mhbuy3 reproduces the anchor byte-for-byte, then deposit
  and withdraw succeed.

## Result

- Every disable bit gates only its own leg, and bit
  combinations gate per-leg: no combination produced a
  failure on an unset leg, and no combination changed
  which code a set leg fails with. The create bit is the
  exception that proves the rule — it gates nothing on
  pools that already exist.
- Boost is the one non-trade leg that disable reaches,
  and only through the buy bit (6020); the sell and
  deposit bits leave the anchor burn untouched.
- Sweep, collect, token claim, and cashback claim are
  fully disable-blind: under all five bits they pay
  exactly their anchor amounts.
- Clearing the bits restores disable byte 0 everywhere,
  and every tail leg on an untouched fixture (the
  `x-buy-sell`, `x-all`, `r-full`, and `g-event` buy
  legs, and all three boost burns) reproduces its anchor
  byte-for-byte — deltas, lamport deltas, withheld,
  pool states, and events. Tail legs that follow a
  successful leg in the same case succeed with numbers
  shifted only by that leg's state movement.
- Failure steps roll back every watched account except
  the fee payer (fee 5,000 each), and every error site is
  recorded per image: the buy gate sits at
  `multi_hop_swap.rs:469` on the original and `:489` on
  the rebuilds; the boost buy gate sits at `boost.rs:240`
  on the original and `boost_burn.rs:34` on the
  rebuilds. Sites are recorded per image and are not
  compared across images.
- 0 divergent cases: control == candidate in every case,
  and the original agrees with both in every case.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #64/#71 fixture (true 3
  hops, tf100 in families A/D/X/B/R); the cashback claim
  cases are plain-quote mode (see the scope note above).
- Only the true 3-hop split route is covered; 4- and 5-hop
  routes were not re-measured here, and mayhem-mode split-chain
  behaviour is not covered (mayhem source is absent from the
  sparse checkout).
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
