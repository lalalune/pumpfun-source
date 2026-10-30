# research: split x boost x transfer-fee chains meet the fee buckets

## Problem

The split multi-hop route (three hops, tail output U3) accrues fees into
two per-pool buckets, `protocol_fees` (pool bytes 271..279) and
`creator_fees` (279..287), and pays a buyback leg out of the first hop.
Earlier packets pinned each piece separately: sweep/ collect (#4, #5),
the boost window (#34), withdraw-withheld (#69), buyback-config (#78),
the window invariant (#92), and vault balances (#98). What was never
pinned on one chain is how the buckets themselves behave as state:
how much each leg accrues, whether a seeded bucket moves the price or
the boost burn, what a sweep does to the pool's virtual reserves,
what happens after a bucket is emptied, and what breaks when a bucket
is huge. This packet measures all of that on the same true-3-hop
split x boost x tf chain (three hop groups, final output U3).

## Cases

68 cases, 459 receipts, 46 parts (45x10 + 9), three images
(original / control / candidate) per step. Transfer fee is 100 bps
unless a case says otherwise. Fixture buckets: protocol 2,488,
creator 123,394 on every pool; virtual quote reserve -125,882.

### A. Accrual ladders (buy / sell / repeat)

- `a-anchor-buy`: a 1e9-quote buy accrues **4,561,082** to the hop-1
  protocol bucket (2,488 -> 4,563,570) and **2,645,377,526** to the
  tail creator bucket (123,394 -> 2,645,500,920). The middle pool is
  byte-identical afterwards and the hop-1 creator bucket never moves.
  The buyback leg pays **4,515,471 net** with **45,611 withheld** --
  gross 4,561,082, exactly the hop-1 protocol accrual. Tail output
  5,262,910,281,902.
- `a-anchor-sell`: a 1e9-base sell accrues only **847** to hop-1
  protocol (2,488 -> 3,335) and **500,000** to tail creator
  (123,394 -> 623,394). Sell accrual is two orders of magnitude
  smaller than buy accrual on the same chain.
- `a-buy-buy`, `a-buy-buy-buy`: the second buy re-accrues the same
  hop-1 amount (4,563,570 -> 9,124,652) and the third the same again
  (-> 13,685,734). Accrual is per-trade, not saturating.
- `a-sell-sell`, `a-buy-sell`: sells re-accrue 847 per sell; a sell
  after a buy still accrues 847 on top of the buy's bucket.

### B. v2 / legacy legs

- `i-v2-accrual`: a 1e6 v2 buy accrues 1 protocol + 1 creator per
  trade (2,488 -> 2,489, 123,394 -> 123,395); a second v2 buy adds
  1 + 1 again. The v2 event reports curve 183, lp fee 1,
  protocol fee 2 at 93 bps.
- `i-v2-sell-sweep`, `i-v2-sweep`: a v2 sell accrues the same 1 + 1;
  sweeping either bucket then pays it out gross-minus-withheld
  (2,489 -> 2,464 net, 25 withheld).
- `i-leg-accrual`, `i-leg-sweep`: legacy buys accrue **nothing** --
  both buckets stay at fixture values after two legacy buys, and a
  sweep after a legacy buy pays only the fixture 2,488
  (-> 2,463 net). Legacy trades are bucket-invisible.

### C. Seeded buckets (do they move price or burn?)

- `c-proto-zero-buy`, `c-creator-zero-buy`, `c-proto-big-buy`
  (1e9), `c-p2-seed-buy`, `c-p3-seed-buy`, `c-seed-sell`: seeding
  any bucket to 0 or 1e9 -- hop-1 protocol, hop-1 creator, middle
  protocol + creator, tail protocol + creator -- leaves the buy,
  the sell, and every delta byte-identical to the anchor. Buckets
  are accounting, not pricing inputs, at this scale.
- `c-seed-boost`, `c-seed-boost-zero`: with vq patched to 1e9, the
  boost burn is **5,338,379,201,831** whether the buckets are
  seeded to 1e9 each or zeroed. The burn does not read the buckets.
- `c-proto-huge-buy`, `c-proto-huge-sell`, `c-proto-huge-boost`,
  `c-creator-huge-buy`, `c-creator-huge-sweep`: a hop-1 bucket at
  **10^12 breaks everything** -- buy, sell, boost, and sweep all
  fail **6023 Overflow at pool.rs:417 with 0 events**, and the
  seeded bucket stays put. The boundary between 1e9 (harmless)
  and 10^12 (fatal) is unmeasured.
- `c-p3-creator-big-buy`: the same 10^12 on the *tail* creator
  bucket does **not** break the buy (anchor-identical). Only the
  hop-1 pool's buckets feed the overflowing computation.

### D. Sweep / collect / empty-bucket transitions

- `d-sweep-twice`: sweeping the post-buy protocol bucket pays
  **4,563,570 gross -> 4,517,934 net (45,636 withheld)** and the
  pool's virtual quote reserve rises by exactly the bucket
  (-4,686,964 -> -123,394: the sweep converts the bucket into
  virtual reserves). A second sweep is a silent no-op (0 events).
- `d-collect-twice`: creator sweep pays 123,394 -> 122,160 net
  (1,234 withheld) and converts the creator bucket into virtual
  reserves the same way; collect then pays 122,160 -> 120,938 net
  (1,222 withheld); a second collect is a silent no-op.
- `d-sweep-after-sell`: after a sell, protocol sweep pays 3,335
  -> 3,301 net and creator sweep pays the untouched 123,394
  -> 122,160 net; collect pays 120,938 net. Full drain leaves
  the main pool at [0, 0, 0].
- `d-sweep-seed`: sweeping a 1e9-seeded bucket pays the whole
  1,004,561,082 gross -> 994,515,471 net (10,045,611 withheld).
- `d-sweep-huge`: with the bucket at 10^12, the buy already fails
  6023, and the sweep fails 6023 too -- a huge bucket cannot be
  drained to escape the overflow.
- `d-sweep-vq1-zero`: with the quote vault emptied, the sweep
  fails **6023 at pool.rs:417** (0 events); restoring the vault
  to the post-setup snapshot and sweeping again pays the full
  4,563,570 -> 4,517,934 net. The bucket survives the failed sweep.
- `d-sweep-then-buy`, `d-sweep-then-sell`: after a full sweep +
  creator sweep + collect (main pool at [0, 0, 0]), the next buy
  accrues exactly the gross per-trade amount (0 -> 4,561,082, no
  fixture 2,488 base) and pays the same buyback leg 4,515,471 net
  at the second-buy tail 5,072,980,706,277 -- the buyback leg
  tracks per-trade accrual, not the bucket balance, and the price
  follows the vaults, not the books.

### E. Boost vs buckets

- `e-boost-after-buy`: after a buy (vq patch 1e9), the burn is
  **5,255,205,915,165**, lower than the fresh 5,338,379,201,831
  because the buy drained the base vault.
- `e-boost-after-sweep`, `e-boost-after-collect`: a full sweep,
  or sweep + collect, leaves that burn **byte-identical**
  (5,255,205,915,165). The sweep moves quote-vault funds and pool
  fields, but the burn follows the base vault balance, which the
  sweep never touches.
- `e-boost-twice`: the second boost burns 5,254,441,549,265 --
  less only because the first boost drained the base vault.
- `e-boost-after-sell`: after a sell the burn is
  5,338,394,947,565, essentially the fresh burn (the sell barely
  moves the base vault).
- `h-bucket-restore-boost`: restoring the protocol bucket to its
  post-setup value after a buy, then boosting, still burns
  5,255,205,915,165 -- bucket restoration does not restore burn.

### F. Transfer-fee interaction and the buyback leg

- `f-tf0-buy`, `f-tf0-buy-buy`: at tf0 the buy accrues more
  (4,607,154 vs 4,561,082) and the buyback leg pays the full
  4,607,153 (off by 1 from the accrual -- ceiling rounding);
  the second tf0 buy re-accrues the same amount (-> 9,216,796).
- `f-buyback-after-sweep`: sweeping the protocol bucket to zero
  does not change the next buy's buyback leg (still 4,515,471
  net) -- the leg is computed from the trade, not the bucket.
- `f-plain-buy`, `f-plain-buy-buy`, `f-plain-sweep`: with no
  transfer-fee override at all, the split multihop and the sweep
  fail **InvalidAccountData caused by account: quote_mint** in
  all three images. The fixture quote mint cannot be used without
  the transfer-fee extension present; this is a fixture-shape
  pin, not a plain-SPL-quote measurement.

### G. Failure rollback and leak checks

- `g-slip-after-accrual`, `g-sell-slip-after-buy`: a slippage
  breach (**6004**, 3 ghost hop events) leaves every bucket
  byte-identical, and the next buy lands on the second-buy tail
  5,072,980,706,277 exactly.
- `g-claim-after-fail`: a token claim after a failed buy still
  pays the full 3,334,551 -- the failed trade neither accrues
  nor blocks the claim.
- `g-sweep-fail-buy`: after a failed empty-vault sweep, restoring
  the vault to the post-setup snapshot and buying gives tail
  5,112,903,787,841, *not* the second-buy tail -- because the
  snapshot predates the first buy's 985,438,918 quote inflow
  into the vault. The bucket itself is untouched by the failure
  (4,563,570 preserved, then re-accrues to 9,124,652).

### H. Snapshot-restore transitions

- `h-bucket-restore-buy`: restoring the protocol bucket to its
  post-setup 2,488 after a buy, then buying again, re-accrues to
  4,563,570 (not to 9,124,652) but pays the *second*-buy tail
  5,072,980,706,277 -- the restore erases the first accrual from
  the books while the price still follows the vaults' movement.
- `h-bucket-restore-sweep`: sweeping, restoring, and sweeping
  again pays 4,563,570 -> 4,517,934 net a second time -- the
  restore resurrects a spendable bucket.
- `h-creator-restore-buy`: restoring the tail creator bucket to
  123,394 after a buy, then buying again, re-accrues with the
  second-buy amount (to 2,576,691,665) instead of stacking to
  ~5.29e12 or repeating the first-buy amount -- again the leg
  follows the vault walk, the books restart from the snapshot.
- `h-bucket-walk`: four buys with the bucket forced to 1e9
  mid-walk and restored to snapshot after give after-buy buckets
  4,563,570 -> 1,004,561,082 -> 4,563,570 -> 9,124,652, while the
  tails follow the plain vault walk (first/second/third/fourth
  buy tails) -- each leg's accrual is independent of the starting
  bucket value at scales below the 10^12 overflow.

## Result

0 divergent cases across all 68: original, control, and candidate
agree on every error, event, delta, withheld amount, and pool state.
The fee buckets are pure accounting below 10^12: they never move
the trade price or the boost burn, they convert into virtual quote
reserves when swept, they re-accrue per trade from whatever value
they hold, and they survive every failed step byte-identical. The
two sharp edges are the 10^12 overflow (hop-1 buckets only, 6023 at
pool.rs:417, undrainable) and the empty-vault sweep (same 6023),
plus the fixture-shape finding that the split route requires the
transfer-fee extension on the quote mint.

## Relation to earlier packets

- #4 / #5 (sweep -> collect, tf): the sweep/collect amounts and
  the 1% withheld split are re-measured here on the split chain
  and match (4,563,570 -> 4,517,934; 123,394 -> 122,160 ->
  120,938).
- #34 (boost chain): the burn's independence from the buckets is
  new -- #34 pinned the window as vq + buckets, but the burn
  itself follows the base vault balance; seeding buckets to 1e9
  leaves the burn at 5,338,379,201,831.
- #69 (withdraw-withheld): the withheld amounts on sweep/collect
  (45,636 / 1,234 / 1,222) are the same 1% mechanism; the bucket
  values swept here are what #69's harvest would later recover
  from the destination ATAs.
- #78 (buyback-config): the buyback leg equals the hop-1 protocol
  accrual gross (4,561,082 at tf100, 4,607,154 at tf0); changing
  the buyback bps would rescale the leg, not the accrual.
- #92 (window invariant): the sweep's conversion of bucket into
  virtual reserves is the mechanism behind #92's window
  conservation -- the window (vq + protocol + creator) is
  unchanged by a sweep, only its split moves.
- #98 (vault balances): the empty-vault sweep failure (6023 at
  pool.rs:417) and the vault-driven boost burn both extend #98's
  finding that hop prices and burns follow real vault balances,
  not pool fields.

## Limits

- The 1e9-to-10^12 bucket boundary is unmeasured; only the two
  endpoints are pinned.
- The 6023 site (pool.rs:417) is the same for buy, sell, boost,
  and sweep under a huge bucket, but the overflowing computation
  itself is not identified from these receipts alone.
- The plain-mode cases pin the fixture quote mint's extension
  requirement, not a genuine SPL-quote route (the fixture mint
  stays Token-2022 without the override).
- Bucket patches and snapshot restores are fixture-level
  mutations, not on-chain instructions; the restore cases
  describe harness state transitions, not program behaviour.

Made via @slopdotcash
