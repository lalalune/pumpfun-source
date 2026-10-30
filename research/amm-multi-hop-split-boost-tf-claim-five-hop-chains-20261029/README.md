# research: split x boost x tf claim chains at TRUE 5 hops

## Problem

Packet #67 showed, at a TRUE 3-hop route, that a fresh split trade
feeds the token claim nothing, that a seeded token claim pays
3,334,551 wherever it sits in the chain, that the claim moves neither
the boost burn nor the tail, that claim-mint transfer fees pay
gross-reported / net-delivered, that failure isolation is complete,
and that cashback and token claims touch disjoint fields; #73 pinned
the sync reset gate (now < start AND last < start) and the claim
conversion by prev-day supply/volume. This packet extends every one
of those measurements to a TRUE 5-hop route (main -> POOL2 -> P3 ->
P4 -> P5, final output U5): does the seeded claim still pay the same
amount in every chain position at depth 5, does the 5-hop buy still
leave a seeded UVA untouched, does the cashback claim still pay the
ATA balance on a plain-quote 5-hop chain, does the transfer-fee
cashback gate still hold, does failure isolation still hold, and do
sync reset, close stranding and admin start-change still behave the
same way at depth 5?

Route verification: the builder's `build_route` calls `three_amm`
and then appends the g4 and g5 hop groups, so the buy runs
main -> P2 -> P3 -> P4 -> P5 and the sell runs the reverse;
successful swaps emit 5 hop events. The name, this README, and the
PR title all say 5 hops because the route really is 5 hops
(contrast the earlier 3-hop-named packet whose route was actually 4
hops). Each hop pool carries proper pool data (its own bump,
pool-authority creator, base mint, and vaults), not raw main-pool
bytes, and each hop boost uses an SPL-derived ATA for its hop quote
mint (BA4S for BASE3, BA5S for BASE4). The token-claim legs run at
harness timestamp 21 (GVA start 20, seconds_in_a_day 1, so the claim
converts prev-day 0: supply 1000 / volume 100); close/init/sync/admin
legs run at harness timestamp 10, which is what makes the sync-reset
and pre-start cases observable. The seeded user volume accumulator
is (needs_claim 1, unclaimed 111, claimed 222, volume 333444, last
20, has_total_claimed_tokens 1, cashback_earned 555,
total_cashback_claimed 666) unless a case says otherwise; the seeded
cashback variant carries earned 5475 with a 5475-balance cashback
ATA. The global volume accumulator is seeded (start 20, end 49,
seconds_in_a_day 1, then 30 x 1000 supply and 30 x 100 volume).

## Cases

59 cases, 438 receipts, 44 parts (43x10 + 8), across original,
control and candidate images. Quote transfer fee is 100 bps unless
stated; the claim mint IMINT (bytes([226]) * 32, Token-2022) carries
its own per-case transfer-fee config (claim_bps 0/100/5000).

- A (8 anchors): 5-hop buy, 5-hop sell, buy-then-boost,
  sell-then-boost, buy/sell against a seeded UVA, buy-then-claim and
  buy-boost-then-claim with no UVA seed.
- B (10): seeded token claim in every chain position at depth 5:
  buy-then-claim, claim-then-buy, buy-boost-then-claim,
  buy-claim-then-boost, claim-buy-then-boost, buy-sweep-collect-
  then-claim, buy-claim-then-sweep-collect, sell-then-claim,
  claim-then-sell, and buy-claim-claim.
- C (10): cashback claim on a plain-quote 5-hop chain (no
  transfer-fee override on the quote mint, `no_ww` guard, SPL
  sweep/collect): buy-then-claim, claim-then-buy, buy-claim-then-
  boost (boost probe), claim-then-boost (boost probe), claim with no
  UVA, zero-balance claim, buy-claim-then-sweep-collect,
  claim-then-token-claim, token-claim-then-claim, and
  buy-claim-claim.
- D (5): cashback claim gate under a transfer-fee quote mint:
  claim alone, buy-then-claim, buy-then-claim at tf5000, claim at
  tf0, and claim-then-sweep-collect.
- E (8): token-claim failure isolation at depth 5: claim with no
  GVA (then buy, then buy-boost), claim with a 5-balance vault,
  claim with no user ATA, claim with no UVA, init-then-claim,
  init-clock-restored-then-claim, and buy-init-then-claim.
- F (11): sync / close / admin at depth 5: buy-then-sync (no
  reset), sync alone (reset fires), sync-then-claim, sync-clock-
  restored-then-claim, sync-claim-claim, buy-sync-then-claim,
  close-init-clock-restored-then-claim, close-then-buy,
  admin-start-change-then-claim-claim, outsider-admin-then-claim,
  and admin-then-claim with no GVA.
- G (7): tf variants at depth 5: buy-then-claim at claim-mint
  tf100 / tf5000, claim-then-buy at claim-mint tf100, buy-boost-
  then-claim at claim-mint tf5000, buy-then-claim at quote-mint
  tf5000, sell-then-claim at claim-mint tf100, and buy-claim-
  then-boost at claim-mint tf100.

## Result

0 divergent cases: original, control and candidate agree on every
case. All numbers below are measured on all three images.

- Anchors: 5-hop buy tail U5 5,207,955,235,891 with 5 hop events
  (508 bytes each); 5-hop sell payout 178,541 with 5 hop events
  (449 bytes each); buy-then-boost burn 5,254,679,949,141;
  sell-then-boost burn 5,338,394,848,076.
- The 5-hop buy leaves a seeded UVA byte-identical (volume 333444
  untouched: the multi-hop legs do not feed the volume accumulator
  at depth 5 either). But a 5-hop buy against an absent UVA
  initializes an empty one: the buy pays 1,849,400 (1,844,400 rent
  for the 137-byte account + 5,000 fee) where a seeded buy pays
  only the 5,000 fee, and the following token claim is a 0-event
  zero claim stamping last_update_timestamp 0 -> 21. The same
  rent-paid creation happens on a buy after a close. Conversely a
  claim with no prior buy fails 3012 AccountNotInitialized (site:
  user_volume_accumulator), which is what proves the buy itself --
  not the claim -- creates the account. An init after a buy costs
  fee only, since the account already exists.
- Seeded token claim at depth 5: pays 3,334,551 = 111 + 333444 *
  1000 / 100 (event disc 4facf631cd5bcee8, len 104,
  total_claimed 3,334,773, current_sol_volume 0, ts 21) in every
  chain position -- before the buy, between buy and sweep, after
  sweep/collect, before or after a boost, after a sell. The claim
  moves neither the boost burn (5,254,679,949,141 in all three
  boost positions) nor the tail (5,207,955,235,891 with the claim
  before or after the buy). A second token claim is a 0-event zero
  claim.
- Sweep/collect around the claim at depth 5: the protocol sweep
  after a 5-hop buy discharges 4,563,570 (net 4,517,934, withheld
  45,636); a creator collect with no prior creator sweep is a
  0-event no-op, not an error.
- Plain-quote cashback claim at depth 5: the plain 5-hop buy tail
  is 5,259,040,470,738 (no transfer fee) and the claim pays the ATA
  balance 5,475 (event disc e2d6f62107f293e5, len 72,
  total_claimed 5,475, total_earned 5,475) before and after the buy
  alike, while token fields (claimed 222, volume 333444) stay
  untouched. The zero-balance claim pays 0 despite earned 5,475 --
  the claim pays the ATA balance, not the earned field. The second
  cashback claim is a 1-event zero claim (amount 0), unlike the
  token claim's 0-event zero claim. A boost under a plain quote
  mint fails IncorrectProgramId with full rollback, in both
  positions -- the #103 2x2 rule (boost quote leg needs mint and
  vault both Token-2022) at depth 5. A cashback claim with no UVA
  fails 3012. The plain SPL protocol sweep discharges 4,609,642
  with no withholding, and the plain SPL creator collect without a
  prior creator sweep is again a 0-event no-op. Cashback and token
  claims stay field-disjoint in both orders.
- Transfer-fee cashback gate at depth 5: the cashback claim fails
  2021 under a transfer-fee quote mint at tf100, at tf5000, and
  even at tf0 -- the gate is the mint program (Token-2022), not the
  bps. The failed claim rolls back and the following fixture
  protocol sweep still drains 2,488 (net 2,463, withheld 25).
- Token-claim failure isolation at depth 5: missing GVA fails 3012
  (site: global_volume_accumulator) and the following buy
  (anchor tail) and buy-boost (anchor burn) are unaffected. A
  5-balance vault against a 3,334,551 claim fails Token custom 1
  with rollback and the following buy is the anchor tail. A
  missing user ATA is created by init_if_needed (payer -2,162,600
  = 2,157,600 rent for the 182-byte Token-2022 ATA + 5,000 fee)
  and the full claim lands. A claim with no UVA fails 3012, but
  the following buy creates the empty UVA at rent cost and keeps
  the anchor tail.
- Sync reset at depth 5: sync after a buy with last == start (20)
  is a 0-event no-op -- the gate needs last < start. With last 10
  the reset fires (64-byte event disc c57aa77c74515bff, before
  222, after 0, ts 10): claimed 222 -> 0, has 1 -> 0, while
  unclaimed 111 and volume 333444 are untouched. The claim after
  a reset pays only the pre-existing unclaimed 111
  (total_claimed 111, current_sol_volume still 333444): the volume
  is NOT converted on the same day, because last < start blocks
  the conversion branch. A second same-day claim is a 0-event zero
  claim with the volume still stranded. The buy-sync-claim walk
  gives the same 111 payout.
- Close stranding at depth 5: close refunds the payer 999,995,000
  (close event: unclaimed 111, claimed 222, volume 333444, last
  20) and re-init builds an all-zero UVA; the following claim is a
  0-event zero claim -- the 111 unclaimed never comes back.
- Admin start-change at depth 5: admin (start 30, end 49, day 0,
  supply 2000) succeeds with an 88-byte event (disc
  93fa6c78f71d43de) and rewrites the GVA to start 30, end 49,
  supply [2000, 0, ...], volumes all 0 -- the start change wipes
  supply/volume, then sets supply[day 0] to 2000. The following
  pre-start claim pays only the unclaimed 111, and the next
  pre-start claim re-resets total_claimed_tokens to 0 (has back
  to 0), erasing the just-claimed 111 from the books -- the tokens
  stay paid out, but the counter reads 0 again. (The first admin
  attempt in this packet used end 79 and failed 6033
  TimeRangeTooLarge, since the range 49 exceeds seconds_in_a_day
  x 30 - 1 = 29; the passing range is 19.) Outsider admin fails
  6005 InvalidAdmin and the following claim is the unaffected
  full 3,334,551. Admin and claim both fail 3012 without a GVA.
- Claim-mint tf at depth 5: tf100 pays net 3,301,205 / withheld
  33,346 and tf5000 pays net 1,667,275 / withheld 1,667,276 on the
  gross 3,334,551 event, before the buy, after the buy, and after
  a boost alike; a tf-withheld claim does not move the following
  boost burn (5,254,679,949,141). Quote-mint tf5000 leaves the
  token claim whole (gross 3,334,551, no withholding): the two
  transfer-fee domains are independent.

## Limits

- All results are measured on the three program images (original,
  control, candidate) in the litesvm harness with the fixture pools
  and fee table; they are not a claim about any other program
  version or live state.
- The token-claim legs run at harness timestamp 21 and the
  close/init/sync/admin legs at timestamp 10 by harness design;
  the sync-reset, pre-start-claim and admin-start-change numbers
  are stated against those timestamps and the seeded GVA
  (start 20, end 49, seconds_in_a_day 1).
- The pre-start claimed-erasure (second pre-start claim resetting
  total_claimed_tokens to 0) is observed as a state transition
  only; this packet does not propose a source change for it.
- Error-site lines live in each receipt row's `error_sites` field,
  never in `observed`, because original/rebuild line numbers differ.
- No source change is proposed.

Made via @slopdotcash
