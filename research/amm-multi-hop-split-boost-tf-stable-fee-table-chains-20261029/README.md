# Multi-hop split x boost x tf chain with stable fee-table legs

## Problem

The split x boost x transfer-fee chain (true 3-hop, `three_amm`
only, final output U3) is now pinned across claim, lifecycle,
withdraw-withheld, coin-creator, admin setter, create-pool,
track-volume, reserved-fee, rotation, mode-toggle, disable,
buyback-config, fee-config and fee-table legs. The fee-table
packet (#80) left one observation unpinned: setting the stable
tier count to 0 moved the tail output, and the cause was not
established. This packet answers that question and pins the
stable table itself on the same chain: a real STABLE_QUOTE
(USDC) hop is routed into the chain, the stable tier table is
varied around it, the stable count is varied, the fee-table
account is truncated, and the downstream legs (sweep, collect,
boost, claim) are run after a stable buy. The question is
whether the stable hop prices from the stable tier table at
all, where a stable tier boundary moves the tail, what stable
count 0 actually deserializes into, and whether a stable change
is visible anywhere except the stable hop.

## Route

True 3-hop only. The stable route keeps the standard route's
main hop and swaps its middle and tail hop groups: buy =
fixed 16 accounts + main group + P2S group + P3S group, sell =
fixed 16 accounts + P3S group + P2S group + main group, final
output U3 in both directions, exactly three hop groups, no
g4/g5 group added. P2S is the pool with base mint USDC and
quote mint base (creator = the pool-authority PDA for USDC);
P3S is the pool with base mint BASE3 and quote mint USDC
(creator = C3, the tail pool's own creator). Both pools and
their vaults are funded with 10^15 each; the USDC mint account
is a plain SPL mint with supply 10^15. All cases use transfer
fee 100 bps on the quote mint unless the case name says
otherwise. All amounts below are measured on the original
image; control and candidate agree on every case (0 divergent
cases).

## How a hop prices (source-grounded)

`select_and_apply_v2` (`programs/pump-amm/src/curve/fees.rs`)
picks the table per hop: a non-canonical pool reads the flat
fees (25, 5, 0); a canonical pool with a native or
NORMAL_QUOTE quote reads the tier table; a canonical pool
with the STABLE_QUOTE (USDC) quote reads the stable tier
table when the fee-table account is at least 4073 bytes, else
an empty list that fails `tier()` with FeeTiersEmpty (6082);
any other canonical quote reads the exotic flat fees if at
least one of the three exotic values is nonzero, else the
flat fees. `tier()` returns the first tier when the market
cap is below every threshold, else the last tier whose
threshold the cap meets. The cap is `(mayhem ? 10^15 :
base_supply) * quote_reserve / base_reserve`
(`state/pool.rs`). The fee-table account is Borsh: flat fees
at 41..65, the tier count at 65, the tier vec at 69..1069,
the stable count at 1069, the stable vec at 1073..2073, the
exotic triple at 2073..2097. Because the two vecs are
variable-length, changing a count moves where every later
field deserializes from -- that is the whole mechanism behind
the count cases below.

## Cases

29 cases, 105 receipts, 11 parts (10x10 + 5).

Family A -- anchors on the standard route: `a-buy3` (buy
10^9 quote: tail U3 5,262,910,281,902, buyback 4,515,471,
hop-1 quote credit 985,438,918, vq1 withheld 10,000,000, bb22
withheld 45,611, fee-payer delta -1,849,400), `a-sell3` (sell
10^9 base: payout 178,541, buyback 837), `a-buy2`/`a-sell2`
(single-leg v2 anchors, same shape as #80).

Family S -- the stable tail hop: `s-buy3` and `s-sell3`
(the stable route at fixture tables), `s-t0-buy3` (stable
tiers 1..24 thresholds raised to 10^16, forcing tier[0]),
`s-t5-buy3` (tiers 6..24 raised, forcing tier[5]),
`s-t24c99-buy3`/`s-t24c99-sell3` (stable[24] creator bps
5 -> 99), `s-cross-buy` (two consecutive stable buys with
stable[24] threshold set to 1,007,000,000,000,000 and
creator 99, so the first buy prices from one tier and the
second from the next).

Family M -- stable-count misparses on the standard route:
`m-count0-buy3`/`m-count0-sell3` (stable count 0, the #80
observation reproduced), `m-misparse-a-buy3` (stable[0] =
(threshold 0, fees (7, 11, 13)) with count 0) against
`m-exo007-buy3` (direct exotic (0, 0, 7)),
`m-misparse-b-buy3` (stable[0] threshold 2^64+3, lp 40,
with count 0) against `m-exo3140-buy3` (direct exotic
(3, 1, 40)), `m-count1-buy3` (stable count 1) against
`m-exo59e-buy3` (direct exotic (59000000000, 0, 20)),
`m-count0-stbuy3`/`m-count0-stsell3` (stable route with
stable count 0).

Family T -- truncation: `t-trunc-buy3` (standard route,
fee-table account cut to 3000 bytes), `t-trunc-stbuy3`
(stable route, same cut).

Family E -- no stable hop: `e-stable-buy3`/`e-stable-sell3`
(standard route with stable[24] creator 99).

Family D -- downstream legs after a stable buy:
`d-st-swp-col` (stable buy, then P3S protocol sweep, P3S
creator sweep, main collect), `d-st-boost` (stable buy with
the main pool's virtual quote reserves patched to 10^9, then
a main-pool boost), `d-st-tclaim` (stable buy, then token
claim from a seeded accumulator), `d-st-cclaim`
(cashback claim in plain-quote mode with the #77 no_ww
guard, no trade step).

## Result

The stable hop prices from the stable tier table, and only
from it.

- `s-buy3` is identical to `a-buy3` to the unit (tail
  5,262,910,281,902, same hop-1/hop-2 deltas, same withheld),
  and `s-sell3` pays exactly 178,541 like `a-sell3`. This is
  not a coincidence to wave away: the P3S market cap is
  about 1.0045x10^15, which selects stable tier[24]
  (20, 5, 5), and the exotic triple is also (20, 5, 5), so
  the stable tail and the exotic tail agree numerically.
  The next cases prove the selection is really stable-side:
  stable-table edits move the stable buy, which they could
  not do if the hop priced from exotic.
- `s-t0-buy3` forces tier[0] (2, 93, 30): tail
  5,259,257,309,515, P3S creator bucket 15,861,313,401
  (creator 30). `s-t5-buy3` forces tier[5] (20, 5, 75):
  tail 5,226,607,338,054, creator bucket 39,405,635,564
  (creator 75). `s-t24c99-buy3` moves the tail to
  5,214,275,634,842 with the P3S creator bucket at
  51,892,030,882 (creator 99). The tail moves with the stable tier, and
  the creator bucket tracks the tier's creator bps.
- `s-cross-buy` crosses a tier boundary mid-case. Buy 1
  prices from tier[23] (20, 5, 8): tail 5,261,344,101,118,
  P3S creator bucket 4,231,461,199. Buy 2 prices from
  tier[24] (20, 5, 99): tail 5,026,109,389,340, creator
  bucket 54,773,601,616. The cap crosses the planted
  threshold between the two buys (about 1.0045x10^15 before
  buy 1, about 1.0098x10^15 before buy 2, threshold
  1.007x10^15), so the tier change is a cap crossing, not
  a table edit between steps.
- `s-t24c99-sell3` pays 176,858 (anchor 178,541): the
  stable tier moves the sell direction too, through the
  mirrored gate (lp+creator on the first hop for sells).

The #80 open question is answered: stable count 0 makes the
exotic triple deserialize from the first stable tier slot.

- `m-count0-buy3` reproduces #80's observation exactly
  (tail 5,274,948,716,226) and its hop-1/hop-2 deltas are
  byte-identical to the anchor -- only the tail hop moves,
  because only the tail hop prices from exotic.
  `m-count0-sell3` pays 178,953 (anchor 178,541).
- `m-misparse-a-buy3` (stable[0] = (0, (7, 11, 13)),
  count 0) gives tail 5,272,326,982,709, exactly equal to
  `m-exo007-buy3` (direct exotic (0, 0, 7)). The count-0
  exotic triple is (threshold low 8 bytes, threshold high
  8 bytes, stable tier-0 lp bps) = (0, 0, 7).
- `m-misparse-b-buy3` (stable[0] threshold 2^64+3, lp 40,
  count 0) gives tail 5,253,527,158,741, exactly equal to
  `m-exo3140-buy3` (direct exotic (3, 1, 40)). The
  threshold's low/high halves land in the exotic triple's
  first two slots, and the tier-0 lp bps lands in the third.
- `m-count1-buy3` (count 1) and `m-exo59e-buy3` (direct
  exotic (59000000000, 0, 20)) fail identically with custom
  6024 (Truncation), 1 ghost event, full rollback. With
  count 1 the exotic triple deserializes from the second
  stable tier slot -- (59,000,000,000, 0, 20) -- and that
  triple's lp value is far outside the valid bps range, so
  the misparse surfaces as a rejection rather than a moved
  tail. The equivalence is still exact (same code, same
  event count, same rolled-back state), just not a price.
- `m-count0-stbuy3` fails 6082 with 2 ghost events (the
  first two hops emit, the stable tail hop fails at fee
  selection); `m-count0-stsell3` fails 6082 with 0 events
  (the stable hop is first for sells and fails before any
  hop event). The gate position is visible in the event
  count: a failing hop emits nothing, earlier hops keep
  their events in the log even though the transaction
  rolls back.

Truncation splits by branch:

- `t-trunc-buy3` (3000-byte fee-table account, standard
  route) gives tail 5,262,910,281,903, anchor +1: the
  exotic branch requires account length >= 4097, so it
  falls back to the flat fees (25, 5, 0) instead of exotic
  (20, 5, 5).
- `t-trunc-stbuy3` (same cut, stable route) fails 6082
  with 2 ghost events: the stable branch requires length
  >= 4073, else the stable tier list is empty and `tier()`
  fails. The same cut is a fallback on one branch and a
  hard gate on the other.

Without a stable hop, the stable table is inert:
`e-stable-buy3` and `e-stable-sell3` are byte-identical to
the anchors, confirming #80's "stable fee changes inert"
for the standard route.

Downstream legs after a stable buy:

- `d-st-swp-col`: P3S protocol sweep moves 2,488 (bucket
  to 0), P3S creator sweep moves 2,645,500,920 (bucket to
  0, pool state [0, 0, 0]); the following main-pool
  collect moves 0 with 0 events, because the main pool's
  creator bucket was never swept in this case -- the
  stable tail's creator fees live in the stable creator
  ATA, not in the main collect path.
- `d-st-boost`: burn 5,255,205,915,165, identical to #80's
  anchor boost burn. Boost reads no fee table, so a
  stable tail leaves it untouched.
- `d-st-tclaim`: 3,334,551 (= 111 + 333,444x1000/100),
  identical to #73/#80. `d-st-cclaim`: 5,475, identical.
  Claims are independent of the stable table.

0 divergent cases: original, control and candidate agree
on every case, including the misparse and truncation
behaviours. The packet pins behaviours, not a divergence.

## Limits

- The stable route is synthetic: the USDC mint, P2S/P3S
  pools and their vaults are constructed in-fixture, and
  the P3S cap estimate (about 1.0045x10^15) uses fixture
  supply and vault values. The fee-selection logic is the
  program's; the route itself is not a mainnet route.
- The count-1 misparse is proven by identical rejection
  (6024, 1 event, full rollback), not by a moved tail,
  because the misparsed triple is itself invalid.
- Truncation is probed at 3000 bytes only; other lengths
  (in particular between 3000 and 4073, and between 4073
  and 4097) are not covered here.
- Only the tf100 quote-mint config is used; a tf0 stable
  route is not run.
- Error 6024 is reported as observed (custom 6024,
  Truncation per the program's error enum); no symbolic
  fee-validation name beyond that is claimed.

## Reproduction

`verify.py` re-checks, from the packet files alone plus the
three program images: MANIFEST hashes, report counts (29
cases, 105 receipts, 11 parts), part hashes/sizes, every
receipt transaction's signatures, per-step token/lamport/
withheld deltas, pool states (including the P2S/P3S pools),
fee-config fields, UVA fields, event decodings, error codes
and rollback, and control == candidate on every case.

Made via @slopdotcash
