# Fee-table account validation on the split x boost x tf chain

## Problem

The previous packet (#82) pinned the fee-table account's *length* gates
(3001/3003/6083/6082). This packet pins the account *itself*: what happens
on the split x boost x tf chain at TRUE 3 hops (three_amm only, final
output U3) when the fee-table account has a wrong discriminator, a wrong
owner, zero lamports, foreign data under its key, or when a different
account key is passed in its place. The question is which check fires,
in what order, and whether a validation failure leaks into the
sweep/collect/boost/claim legs that follow it.

## Fixture

The fee-table account in the harness is
`5PHirr8joyTMp9JMm6nW7hNDVyEYdkzDqazxPD7RaTjx`, owned by the Fees program
`pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ` (not the pump program
`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`), lamports 33,103,977,
length 4,097 bytes, discriminator `8f3492bbdb7b4c9b`.

Anchor (unmutated fee-table account, tf100 multi-hop buy of 10^9):
final output U3 = 5,262,910,281,902, buyback leg 4,515,471, withheld
10,000,000 on the first hop's quote vault and 45,611 on the buyback ATA,
3 hop events.

## Cases

40 cases, 138 receipts (46 steps x 3 images), 14 parts (13x10 + 8).
Every case runs on the original, control, and candidate images.

- `v-anchor`: unmutated buy, the anchor above.
- Discriminator (`v-disc-*`): first 8 bytes zeroed, replaced with the
  pool discriminator, replaced with the GlobalConfig discriminator,
  first byte flipped — all on a multi-hop buy.
- Whole data (`v-data-*`): the fee-table account's 4,097 bytes replaced
  with GlobalConfig data, pool data, or all zeros.
- Owner (`v-owner-*`): owner set to the pump program, SPL Token,
  Token-2022, the System Program, or the default pubkey.
- Lamports (`v-lam*`): 0, 1, and 2,000,000 (below rent-exempt for a
  4,097-byte account).
- Check order (`v-order-*`): discriminator + owner both bad,
  lamports 0 + discriminator bad, lamports 0 + owner bad.
- Key swaps (`v-swap-*`): the fee-table key replaced in the instruction
  with the GlobalConfig key, the pool key, a token account (DEST),
  a fresh nonexistent key, or the user quote account.
- Leg parity: the same discriminator / owner / swap faults on a
  multi-hop sell, a v2 buy, a v2 sell, a legacy buy, a legacy sell,
  and a stable-route buy.
- Downstream after failure (`v-fail-*`): a buy that fails with 3002,
  followed by TOKEN22 protocol sweep, creator sweep, collect; by a
  boost (virtual quote patched to 10^9); by a token claim (seeded
  accumulator); and, in plain-quote mode, by a cashback claim
  (seeded earned 5,475).

## Result

- Wrong discriminator — zeroed, pool, GlobalConfig, single flipped byte,
  or a whole foreign data blob (GlobalConfig / pool / zeros) — fails
  with **3002 AccountDiscriminatorMismatch**, 0 events, full rollback.
  Error site in every case: `caused by account: fee_config`.
- Wrong owner — including the pump program itself — fails with
  **3007 AccountOwnedByWrongProgram**, 0 events, full rollback. The
  expected owner is the Fees program; no other owner passes.
- Lamports 0 fails with **3012 AccountNotInitialized**, 0 events.
  Lamports 1 succeeds with byte-identical results to the anchor, and
  lamports 2,000,000 (below rent-exempt for 4,097 bytes) also succeeds
  anchor-identically: **no rent-exempt check is applied** to this
  account, only the zero-lamports initialized check.
- Check order is **3012 > 3007 > 3002**: lamports 0 + bad discriminator
  reports 3012, lamports 0 + bad owner reports 3012, and bad
  discriminator + bad owner reports 3007.
- Every key swap fails with **3007**: the owner check fires before any
  discriminator read, so a swapped key never reaches the data checks —
  including the fresh nonexistent key, whose owner is the default
  pubkey rather than a "missing account" error.
- Leg parity is exact: buy, sell, v2 buy, v2 sell, legacy buy,
  legacy sell, and stable-route buy all report the same code for the
  same fault (3002 for discriminator, 3007 for owner/swap).
- A validation failure leaks nothing downstream. After a 3002 buy
  failure, all of these succeed at their fixture values: TOKEN22
  protocol sweep discharges 2,488 (2,463 net, withheld 25), creator
  sweep discharges 123,394 (122,160 net, withheld 1,234), collect pays
  122,160 (120,938 net, withheld 1,222); boost burns 5,338,379,201,831,
  equal to the #64 tf100 anchor because the failed trade left the
  boost window (vq 10^9 + accrued buckets) untouched; token claim
  pays 3,334,551 (3,301,205 net, withheld 33,346); cashback claim pays
  the full seeded 5,475.
- Divergence: **0**. Original, control, and candidate agree on all
  40 cases.

## Limits

- Only the fee-table account's own validation is pinned here;
  tier-content behaviour is #80 (fee-table), #81 (stable fee-table),
  and #82 (length gates).
- No key swap reaches the discriminator check, so a "right owner,
  wrong key" case cannot be constructed from fixture accounts: no
  second Fees-owned fee-table account exists in the harness. The
  discriminator check itself is pinned by data/disc mutations on the
  real key.
- The rent-exempt finding rests on two probed points (1 and 2,000,000
  lamports); both pass anchor-identically.
- The cashback-claim downstream case uses plain-quote + no_ww mode:
  as in #67/#77, a cashback claim on the tf-override quote mint fails
  with the Anchor 2021 ConstraintTokenTokenProgram check, which is
  unrelated to fee-table validation.
- Downstream sweep/collect legs use the TOKEN22 path; the SPL-Token
  sweep of the main pool fails InvalidAccountData for a fixture
  reason (the main quote vault is Token-2022 owned), as noted in #82,
  not because of fee-table validation.

Made via @slopdotcash
