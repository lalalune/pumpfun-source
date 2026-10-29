# amm-multi-hop-split-boost-tf-dynamic-fee-table-chains-20261029

## Problem

3rd #80 pinned the fee table statically: each hop prices from its
own fee-table entry (tier table for native-quote hops, stable tier
table for STABLE_QUOTE hops, exotic flat fees for the tail hop).
3rd #81 pinned the stable table, #82 truncation, #83 account
validation, #92 state transitions. What none of them pinned is
the table in motion: the fee-table account is just an account,
and its fields can change between two trades. Does the next
trade reprice immediately? Does the change carry into
sweep/collect/boost/claim? Does a failed trade, or a restore
patch, bring the price back? This packet patches the fee-table
account mid-case -- between real trades, with no transaction of
its own, so it leaves no receipt -- and pins what each patch
does to the next trade and to every downstream leg, on the
split x boost x tf chain at true 3 hops (three_amm only, final
output U3).

## Cases

32 cases, 276 receipts, 28 parts (27x10 + 6).

Family A -- tier transitions on the standard route: `a-anchor-buy`
(buy 10^9 quote: tail U3 5,262,910,281,902, buyback 4,515,471),
`a-anchor-sell` (sell 10^9 base: payout 178,541, buyback 837),
`a-t1-live` (buy, tier-1 threshold patched to 0, buy, threshold
restored, buy), `a-t0lp-walk` (buy, tier-0 lp 2 -> 20, buy, lp
restored, buy), `a-t1-all` (tier 1 from setup, buy, buy,
threshold restored, buy), `a-cross-live` (tier-1 threshold
planted at cap+3,000,000, buy, buy, buy), `a-count1` (tier count
25 -> 1, buy, count restored, buy), `a-count0-fail` (tier count
25 -> 0, buy, buy again, count restored, buy).

Family B -- flat fees: `b-flat-inert` (buy with flat patched to
(100,5,0), buy with flat restored), `b-flat-live` (exotic zeroed
from setup, buy, flat lp 25 -> 100, buy, flat restored, buy,
exotic restored, buy), `b-flat-live-sell` (same walk in the sell
direction).

Family C -- exotic transitions: `c-exotic-walk` (buy, exotic
(100,0,0), buy, exotic (0,0,100), buy, exotic restored, buy),
`c-exotic-sell` (sell, exotic (50,10,777), sell, exotic restored,
sell), `c-exotic-zero-sell` (exotic zeroed from setup, sell,
exotic restored, sell).

Family D -- stable transitions on the stable route (real
STABLE_QUOTE tail hop): `d-stable-tier-walk` (stable buy, stable
tier-24 creator 5 -> 99, buy, creator restored, buy),
`d-stable-t0-inert` (stable buy with stable tier 0 patched to
(50,50,50), buy with tier 0 restored), `d-stable-count0`
(stable buy with stable count 0, buy with count restored),
`d-stable-count1` (stable buy with stable count 1, buy with
count restored), `d-stable-sell-walk` (stable sell, stable
tier-24 creator 99, sell, creator restored, sell).

Family E -- downstream legs after a tier-1 buy:
`e-t1-sweep-collect` (tier-1 buy, TOKEN22 protocol sweep,
creator sweep, collect, buy), `e-t1-boost` (tier-1 buy with main
vq patched to 10^9, boost, buy), `e-t1-tclaim` (tier-1 buy, token
claim from a seeded accumulator), `e-t1-cclaim` (tier-1 buy in
plain-quote mode with the #77 no_ww guard, cashback claim),
`e-t1-depwd` (tier-1 deposit, withdraw, buy).

Family F -- rollback: `f-t1-slip` (tier-1 slippage failure
min-out 10^15, then a successful tier-1 buy), `f-flat-slip`
(flat-fallback slippage failure, then a successful flat buy),
`f-slip-then-patch` (slippage failure, then a tier-1 buy after
patching the threshold to 0).

Family G -- table walks: `g-walk-buy` (buy, tier 1, exotic
(100,0,0), exotic-zero + flat 100, full restore, buy),
`g-walk-sell` (sell, tier 1, exotic (50,10,777), full restore,
sell).

Family H -- mixed routes (standard + stable in one case):
`h-mixed-walk` (standard buy, stable buy, stable buy with
stable-24 creator 99, standard buy, stable buy with creator
restored), `h-mixed-count` (stable buy with stable count 0,
standard buy, stable buy with count restored),
`h-mixed-flat` (standard buy, standard buy with exotic zeroed,
stable buy, stable buy with exotic restored).

## Result

The fee table is read live on every trade. A patch between two
trades reprices the next trade immediately, and a restore patch
brings the bps back -- on the moved curve, not at the original
price.

- `a-t1-live`: buy 1 pays tier 0 (tail 5,262,910,281,902,
  buyback 4,515,471); after the tier-1 threshold drops to 0,
  buy 2 pays tier 1 (tail 5,116,788,773,158, buyback 244,902);
  after the threshold is restored, buy 3 pays tier-0 bps again
  (buyback 4,515,471) on the moved curve (tail
  4,891,611,475,391). `a-t1-all` (tier 1 from setup) buys
  5,308,343,025,925 then 5,115,150,209,754, then 4,890,073,154,943
  after restore. `a-cross-live` plants the tier-1 threshold at
  cap+3,000,000 (182,353,153,971): buy 1 pays tier 0, the first
  buy moves the cap past the threshold, so buy 2 pays tier 1
  and buy 3 stays tier 1 (4,933,867,307,098).
- Tier-0 lp is inert on buys: patching tier-0 lp 2 -> 20 leaves
  the second buy byte-identical to the unpatched second buy
  (5,072,980,706,277, the #93 chain-chain second-buy value) --
  the buy's first hop charges protocol only, so the lp leg never
  lands on this path.
- Tier count: 25 -> 1 fails 3003 (Borsh) with 0 events -- the
  shortened tier vec corrupts the parse -- and 25 -> 0 fails
  6082 FeeTiersEmpty with 0 events, twice in a row (the table
  stays broken until restored). Restoring the count restores
  the anchor buy exactly (5,262,910,281,902).
- Flat fees: with exotic nonzero, flat (25,5,0) -> (100,5,0) is
  inert (buy anchor-identical). With exotic zeroed, the tail
  falls back to flat fees: the fresh-curve buy is anchor+1
  (5,262,910,281,903), while a later flat-fallback buy equals
  the exotic buy to the unit (5,072,980,706,277) -- the +1 is a
  fresh-curve rounding artifact, not a rate change. Under the
  fallback, flat lp 25 -> 100 moves the buy to 5,035,487,568,211
  and restoring flat moves it back. On sells, the exotic-zero
  first sell pays anchor-identical 178,541 because both
  schedules total 30 bps -- the split shows only in buckets
  (tail creator bucket static under flat, +500,000 under
  exotic); flat lp 100 drops the sell to 177,197.
- Exotic: (100,0,0) moves the buy to 5,035,500,751,655 with the
  tail creator bucket static (creator 0); (0,0,100) moves it to
  4,857,165,185,656 with the creator bucket at 52,480,853,017;
  restoring exotic gives 4,723,275,601,852. On sells, exotic
  (50,10,777) drops the payout to 164,185 with the creator
  bucket at 78,823,159.
- Stable: stable tier-24 creator 5 -> 99 moves the stable buy
  to 5,026,093,586,810 (P3S creator bucket 53,187,641,337) and
  the stable sell to 176,857 (anchor 178,541); restoring gives
  the anchor bps back (buyback 837 on sells). Patching stable
  tier 0 moves nothing (selection is last-met-tier). Stable
  count 0 fails 6082 with 2 ghost events on the stable route
  (the first two hops emit, the tail hop fails on the empty
  stable table); stable count 1 fails 6024 with 1 ghost event
  -- the same misparse rejection #81 pinned on the standard
  route.
- Downstream: a tier-1 buy shrinks the protocol sweep to
  249,865 (anchor 4,563,570) while the creator sweep (123,394)
  and collect (122,160 gross, 120,938 net) are unchanged, and
  the next buy (5,115,150,209,754) equals the no-sweep tier-1
  second buy -- sweep/collect are price-neutral. A tier-1 buy
  followed by a boost burns 5,254,483,001,415, exactly #80's
  tier-1 burn. Token claim after a tier-1 buy pays the full
  3,334,551 (net 3,301,205) and cashback claim pays 5,475 --
  claims are table-blind. Deposit/withdraw under tier 1 leaves
  the next buy 42 below the tier-1 first-buy tail
  (5,308,343,025,883 vs 5,308,343,025,925), the #91
  deposit/withdraw flooring dust.
- Rollback: a slippage failure (6004) leaves all 3 hop events
  as ghosts and rolls back fully under both the tier-1 and the
  flat-fallback tables; the next buy succeeds at the table
  price. A failure, then a patch, then a success works
  (tier-1 buy 5,308,343,025,925 after a failed anchor-table buy).
- Walks: the 5-step buy walk runs anchor -> tier 1 -> exotic
  (100,0,0) -> exotic-zero + flat 100 -> restore (tails
  5,262,910,281,902 -> 5,116,788,773,158 -> 4,897,410,990,063
  -> 4,725,564,805,810 -> 4,557,191,115,624, buyback back to
  4,515,471 on restore). The sell walk runs 178,541 -> 180,125
  under tier 1 (buyback collapses 837 -> 45) -> 165,642 under
  exotic (50,10,777) (buyback 41) -> 178,537 restored (buyback
  837). Note the sell direction moves opposite to buys under
  tier 1: the payout rises while the buyback leg collapses.
- Mixed routes: a stable-table patch does not move the
  standard route's fee selection (buyback stays 4,515,471),
  and an exotic-zero patch does not move the stable route's
  table (the P3S creator bucket still accrues at the
  stable-tier rate). One asymmetry is pinned: under stable
  count 0 the stable route fails 6082 while the standard route
  succeeds at the misparsed-exotic price (tail
  5,274,948,716,226, exactly #81's count-0 tail, hop-1/hop-2
  byte-identical to the anchor) -- the misparse is global to
  the fee-table account, but only the route that reads the
  broken branch fails.

All 32 cases agree on all three images (original, control,
candidate): 0 divergent cases. Error sites are pinned per
image, never compared across images.

## Limits

- Patches are applied directly to the fee-table account between
  steps; they are not transactions and leave no receipt. The
  receipt stream pins the before/after state of every real step,
  and producer.py records every patch in the case definitions,
  so the sequence is reproducible from the packet files -- but
  a patch itself has no signature to verify.
- No source change is proposed and no program is rebuilt: the
  packet pins observed behaviour of the three images only.
- The tier-1 sell mechanism (payout up, buyback collapsed) is
  recorded as measured values, not explained: the checked-out
  source does not identify which leg of the mirrored sell fee
  assignment moves.
- The flat-fallback +1 is a fresh-curve observation only; on
  later curve states the flat buy equals the exotic buy
  exactly, so the +1 must not be quoted as a flat-vs-exotic
  rate difference.

Made via @slopdotcash
