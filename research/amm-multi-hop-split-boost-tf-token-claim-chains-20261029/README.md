# research: split x boost x tf chains meet token/cashback claims (TRUE 3-hop)

## Problem

3rd #64/#65/#66 pinned the split x boost x transfer-fee chain at TRUE
depths 3, 5, and 4. 3rd #20/#21 pinned `claim_token_incentives` (and
3rd #2/#13/#14 pinned `claim_cashback`) on single-pool trades. What
nobody had done is chain the two worlds in one VM: does a split
trade or a boost feed the token claim at all, does a seeded token
claim pay the same amount wherever it sits in a split x boost x tf
chain (including net payout under a transfer fee on the claim mint),
does the claim move the boost burn, the hop-1 tier-cap crossing, or
the tail output, do failed claims isolate with the chain still
draining in full afterwards, and do the cashback and token claims
stay field-disjoint on the split chain?

Route (read from the builder, not the packet name): `three_amm`
only, no g4/g5 hop group appended, so the route is
main -> POOL2 -> P3, final output U3: TRUE 3 hops. The quote mint
carries a per-case transfer-fee config (0/100 bps) with the split
legs routing the buyback through the TOKEN22 ATA; the claim mint
IMINT (bytes([226]) * 32, Token-2022) carries its own per-case
transfer-fee config (claim_bps 0/100/5000). The global volume
accumulator is seeded (20, 49, 1, then 30 x 1000 and 30 x 100);
the seeded user volume accumulator is (needs_claim 1, unclaimed
111, claimed 222, volume 333444, last 20, has_total_claimed_tokens
1, cashback_earned 555, total_cashback_claimed 666), unless a case
says otherwise. All figures below are measured on the original
image; control and candidate agree except where noted.

## Cases (21 cases, 261 receipts, 27 parts)

- `a-buy-tclaim-swc-col`, `a-buy-boost-tclaim-swc-col` (vq patched
  to 10^9 so the boost opens), `a-sell-tclaim-swc-col`: fresh split
  trade (and boost) -> token claim -> sweep -> collect.
- `b-tclaim-buy-swc-col`, `b-buy-tclaim-swc-col`,
  `b-buy-swc-col-tclaim`, `b-buy-tclaim-boost-swc-col`,
  `b-tclaim-buy-boost-swc-col`: seeded token claim in every chain
  position, including around a boost.
- `c0-buy-boost-tf100` (anchor), `c1-tclaim-buy-swc-col-tf100`,
  `c2-buy-tclaim-boost-tf100`, `c3-tclaim5000-buy-tf100`: the same
  chain under quote tf100 with claim-mint tf100 / tf5000.
- `d-tclaim-nogva-buy-swc-col`, `d-tclaim-shortvault-buy-swc-col`,
  `d-tclaim-missingata-buy-swc-col`: failure isolation (missing
  global accumulator, short vault, missing user ATA).
- `e0-buy-buy` (anchor), `e1-buy-tclaim-buy`,
  `e2-tclaim-buy-buy`: tier-cap crossing (tiers A = (10, 111, 333)
  at cap 100, B = (20, 222, 444) at cap 185,000,000,000, main vq
  patched to 10^9) with a claim interleaved.
- `f-cclaim-tclaim-buy-swc-col`, `f-tclaim-cclaim-buy-swc-col`,
  `f-cbflag-buy-cclaim-tclaim-swc-col`: cashback claim x token
  claim on the split chain, plus a split buy on a cashback-flagged
  main pool. The cashback family runs in plain-quote mode (no
  transfer-fee override, SPL buyback, SPL sweep/collect) for the
  reason in Limits.

## Result

- A fresh split trade feeds the token claim nothing, exactly as
  3rd #20 found for single-pool trades: the claim after a fresh
  buy, sell, or buy-then-boost is a zero claim (0 events, log
  "No tokens to claim", payer -5,000 fee only) that stamps
  `last_update_timestamp` 0 -> 21 and leaves the fee buckets
  untouched; the following sweep/collect drains the full creator
  bucket 123,394.
- A seeded token claim pays 3,334,551 = 111 + 333444 * 1000 / 100
  (event disc 4facf631cd5bcee8, len 104, total_claimed 3,334,773,
  current_sol_volume 0) wherever it sits in the chain: before the
  buy, between buy and sweep, after sweep/collect, before or after
  a boost. The token pipe and the fee pipes are fully
  independent.
- The claim moves nothing on the chain. Boost burn after a
  vq-patched buy is 5,307,028,789,111 at 0 bps with the claim
  before the buy, between buy and boost, or after the boost --
  byte-identical. Under tf100 the burn is 5,255,205,915,165 with
  or without an interleaved claim (vaultquote net +990,000,000,
  withheld 10,000,000). The tier-cap second buy is
  5,019,668,351,471 with the claim before both buys, between the
  buys, or absent. The tail output is unchanged in every case.
- Under transfer fee the claim still pays gross-reported, net-
  delivered: claim-mint tf100 gives user +3,301,205 / withheld
  33,346 on a gross 3,334,551 event; claim-mint tf5000 gives
  +1,667,275 / withheld 1,667,276. The tf sweep/collect pipes are
  claim-independent: sweep net 122,160 / withheld 1,234, collect
  dest net 120,938 / withheld 1,222, with or without a claim.
- Failure isolation is complete. Missing global accumulator ->
  3012 AccountNotInitialized (site: global_volume_accumulator).
  Vault holding 5 against a 111 claim -> Token custom 1.
  Missing user ATA -> created by init_if_needed (payer
  -2,162,600 = 2,157,600 rent for the 182-byte Token-2022 ATA +
  5,000 fee; the 111 claim lands, total_claimed 333). In all
  three cases the following split buy, sweep, and collect drain
  the full bucket, and the failed step rolls back everything
  except the fee payer.
- Cashback and token claims touch disjoint fields in both orders
  on the split chain: cashback claim pays 5,475 (event disc
  e2d6f62107f293e5, len 72, total_claimed 5,475, total_earned
  5,475; UVA cashback_earned stays 5,475, total_cashback_claimed
  becomes 5,475) while token fields are untouched, and the token
  claim pays 3,334,551 while cashback fields are untouched. The
  split buy tail is identical in both orders.
- A split buy on a cashback-flagged main pool earns no cashback
  at all: on the original image the buy succeeds with the usual
  tail (5,315,084,721,958) and UVA cashback_earned stays 0, and
  the following cashback claim is a zero claim (1 event, amount
  0, total_claimed 0, total_earned 0). The same case diverges on
  the rebuilds (see below).

## Divergence (1 case, pinned, not a defect claim)

`f-cbflag-buy-cclaim-tclaim-swc-col`: the original gates cashback
only at the terminal hop, so the buy on the cashback-flagged main
pool (a non-terminal hop) succeeds. Control and candidate gate at
every hop, so the buy fails 6079 CashbackCoinNotSupported at
multi_hop_swap.rs:500, and the following cashback and token claims
fail 3012 on the still-absent volume accumulator. The seed creator
bucket still drains in full via sweep/collect (123,394) on all
images. This is the 3rd #25 mode-gate divergence, reproduced on
the split chain; the packet records per-image expectations for
this case and asserts control == candidate.

## Limits

- `claim_cashback` cannot run on the transfer-fee-overridden quote
  mint at all: it fails Anchor 2021 ConstraintTokenTokenProgram
  ("A token account token program constraint was violated")
  because the mint's program is Token-2022 while the claim's token
  accounts are SPL. That is why the cashback family runs in
  plain-quote mode. In plain mode the split buy tail
  (5,315,084,721,958) equals the 0-bps transfer-fee-mode tail
  exactly (buyback leg 4,607,153 either way; only the account role
  differs, SPL buyback vs TOKEN22 buyback).
- Harness fixture note, not a program defect: quote is the native
  mint in this harness, so a native token account's lamports must
  equal rent + amount. Seeding the cashback UVA token account with
  amount 5,475 but rent-only lamports (2,039,280) makes the
  cashback claim fail the runtime rent check
  (InsufficientFundsForRent) after emitting its event; seeding
  rent + amount (2,044,755) makes it succeed cleanly.
- The token-claim event discriminator measured here is
  4facf631cd5bcee8 (len 104). No source changes, no builds, and
  no whole-program equivalence are claimed; this packet pins the
  measured chain behaviour above, plus the one divergence.
