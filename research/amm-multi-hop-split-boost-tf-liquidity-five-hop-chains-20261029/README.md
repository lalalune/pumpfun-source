# research: split x boost x tf chains meet liquidity legs at the boost, at TRUE 5 hops

3rd-run packet #124: the split x boost x tf chain at TRUE 5 hops
(`three_amm` + g4 + g5, final output U5) meets deposit and withdraw.
This is the 5-hop extension of #118, not a re-measure: every #118
result is re-checked at depth 5, and the new depth-5-only behaviour
is the 5-hop buy/sell tails before and after liquidity legs and the
P4/P5 hop-pool legs.

## Problem

Deposit and withdraw are not boost-neutral legs. When a pool can
boost, deposit adds to `virtual_quote_reserves` proportionally
(`deposit.rs`: vq += total_virtual x amount / old_supply, floor)
and withdraw subtracts it with a ceiling (`withdraw.rs`: vq -=
ceil(total_virtual x amount / old_supply)), and the boost burn
reads the vq field plus the real vaults (#100: burn slope about
-42.73 per vq unit; #102: the vq field also enters hop-1 pricing).
#118 pinned all of this at 3 hops. This packet measures, on the
real 5-hop route main -> POOL2 -> P3 -> P4 -> P5, whether the
ladder, the round-trip residue, the gates, the hop-deposit
failure and the tf legs hold at depth 5, and how far a liquidity
leg moves the 5-hop tail in each direction.

The route is a TRUE 5-hop route: `three_amm` plus the g4 and g5
hop groups, five hop groups, final output token U5. (The #61
miscount does not apply here: the builder appends g4 AND g5, and
successful 5-hop swaps emit exactly 5 hop events.)

## Setup

Three images are compared on every case: the original program, the
control rebuild (#424) and the candidate rebuild (#427). The chain is
the #64/#115 chain: a split fee-table route with a boost leg and a
transfer-fee quote mint (tf100 unless noted). Deposit args are
(lp_out, max_base_in, max_quote_in); withdraw args are (lp_in,
min_base_out, min_quote_out). The main pool's seeded creator bucket
is 123,394 and its protocol bucket 2,488 in every case, and so is
each hop pool's. The patched-window boost uses a vq field patch to
10^9 (a harness field reset, recorded with an empty transaction and
never presented as an on-chain instruction); the fresh pool's total
virtual is exactly 0 (-125,882 + 2,488 + 123,394), so an unpatched
pool cannot boost and a deposit on it leaves the vq field untouched.
Hop pools are seeded with proper pool data (bump, pool-authority
creator, their own base mints and vaults), per the #119 build
lesson, and hop boosts use SPL-derived ATAs for the hop quote
mints, per the #120 lesson.

## Cases (71 cases, 228 steps, 684 receipts)

Family A — anchors and bare legs (bps 100): patched-window boost,
buy-then-boost, sell-then-boost, 5-hop buy alone (tail anchor),
5-hop sell alone (payout anchor), deposit 10^6 alone, withdraw
10^6 alone, deposit-then-withdraw alone.

Family B — main-pool deposit -> boost at depth 5: deposit 10^6 /
10^9 / 10^12 then boost; deposit-boost-boost; boost-deposit-boost;
buy-deposit-boost; deposit-buy (5-hop tail); deposit-buy-boost;
deposit-sell (5-hop payout); sell-deposit-boost; deposit-protocol-
sweep-boost.

Family C — main-pool withdraw -> boost at depth 5: withdraw 10^6 /
10^9 then boost; buy-withdraw-boost; sell-withdraw-boost;
deposit-withdraw-boost and withdraw-deposit-boost round trips;
deposit-withdraw-deposit-boost; withdraw-protocol-sweep-boost.

Family D — liquidity gates, then boost at depth 5: deposit
base-limit -1, deposit quote-limit -1, withdraw min-base +2,
withdraw min-quote above the payout, zero deposit, zero withdraw,
deposit under the deposit disable bit, withdraw under the withdraw
bit, and deposit under the bit then cleared by the real
`set_disable_flags` instruction then deposit then boost.

Family E — hop-pool liquidity at depth 5: P2/P3 carryover legs (P2
deposit then P2 boost, P2 deposit 10^9 then P2 boost, P2 withdraw
then P2 boost, P3 deposit then P3 boost, P2 deposit then 5-hop
buy, buy then P2 deposit then P2 boost, P2 deposit then P2
withdraw then P2 boost, and the authority-patched P2/P3 legs)
plus the new P4/P5 legs (P4 deposit then P4 boost, P4 deposit
10^9 then P4 boost, P4 withdraw then P4 boost, P5 deposit then P5
boost, P5 withdraw then P5 boost, P4/P5 deposit then 5-hop buy,
buy then P4/P5 deposit then P4/P5 boost, P4/P5 deposit-withdraw
then P4/P5 boost, and the authority-patched P4/P5 legs including
patched deposit then 5-hop buy).

Family F — tf variants at depth 5: deposit-boost and
withdraw-boost at tf5000, deposit-boost at tf0, deposit then
5-hop buy at tf5000, and the P2/P4/P5 deposit failures at tf5000
(showing the failure is tf-independent).

## Result (0 divergent cases; control == candidate everywhere)

### Anchors and bare legs at depth 5

- Fresh patched-window main boost burn 5,338,379,201,831;
  buy-then-boost burn 5,254,679,949,141; sell-then-boost burn
  5,338,394,848,076.
- 5-hop buy tail anchor 5,207,955,235,891, emitted as exactly 5
  hop events of 508 bytes each; 5-hop sell payout anchor
  178,541, emitted as exactly 5 hop events of 449 bytes each.
  The 5-hop buy tail matches the #119/#121 anchor; the hop-event
  counts confirm the route is truly 5 hops.
- Deposit 10^6 alone: user pays base 160,619,896 and quote
  29,610 (quote amount 29,313 + 297 withheld in the vault),
  receives 1,000,000 LP; the vq field stays -125,882 (can_boost
  is false on the unpatched pool, so the proportional vq update
  does not run).
- Withdraw 10^6 alone: user receives base 160,619,895 and quote
  29,018 (29,312 out of the vault, 294 withheld in the user
  account), burns 1,000,000 LP; the vq field stays -125,882.
- Deposit-then-withdraw alone restores the pool exactly
  (vq -125,882, lp_supply 4,194,352,106,721).

### The deposit ladder moves the burn at depth 5 exactly as at 3 hops

With the vq patch (10^9) first, total virtual is 1,000,125,882
and the vq update is floor/ceil(total x amount / old_supply):

- Deposit 10^6: vq +238 (floor of 238.41), burn
  5,338,379,211,910 = anchor +10,079.
- Deposit 10^9: vq +238,445, burn 5,338,389,284,765 =
  anchor +10,082,934.
- Deposit 10^12: vq +238,445,856, burn 5,346,535,371,563 =
  anchor +8,156,169,732.
- Withdraw 10^6: vq -239 (ceil of 238.41), burn
  5,338,379,191,752 = anchor -10,079.
- Withdraw 10^9: vq -238,446, burn 5,338,369,114,126 =
  anchor -10,087,705.
- Deposit after a buy lifts the post-buy burn by 9,841
  (5,254,679,958,982); withdraw after a buy cuts it by exactly
  9,841 (5,254,679,939,300). The ladder is symmetric to the unit
  at 10^6 scale, as at 3 hops.
- Deposit before a 5-hop buy lifts the tail by 9,597
  (5,207,955,245,488) -- slightly less than the 3-hop lift of
  9,801, a genuine depth effect; deposit-buy-boost is the
  post-buy burn +39,495 (5,254,679,988,636), identical to 3 hops.
- Deposit before a 5-hop sell leaves the payout byte-identical
  at 178,541 (all leg deltas identical to the anchor sell):
  the sell direction is insensitive to a main-pool deposit,
  while the buy direction is not.
- Deposit after a sell lifts the post-sell burn by 10,078
  (5,338,394,858,154); withdraw after a sell cuts it by 10,077
  (5,338,394,837,999).
- Deposit-boost-boost: the second burn is 5,254,441,578,883
  (the plain second burn 5,254,441,549,265 + 29,618). A deposit
  after the first boost costs less base (159,347,142, because
  the boost shrank the base vault) and its second burn is
  5,254,441,559,109.
- Deposit then protocol sweep then boost is anchor +126,557
  (5,338,379,328,388): the deposit effect (+10,079) plus the
  sweep effect (+116,478) compose. Withdraw then sweep then
  boost is anchor +86,017 (5,338,379,287,848).

### The round trip leaves vq off by one but the burn byte-identical

- Deposit-withdraw and withdraw-deposit both end at vq
  999,999,999 (one below the 10^9 patch: floor up, ceil down)
  and both burn exactly the anchor 5,338,379,201,831.
- Deposit-withdraw-deposit lands at vq 1,000,000,237 (one below
  the single-deposit 1,000,000,238) and burns exactly the
  single-deposit burn 5,338,379,211,910. The burn is insensitive
  to a 1-unit vq difference at this scale: the vq rounding
  residue does not survive into the burn.
- One depth-5 asymmetry in the walk order: a deposit after a
  buy moves vq by +239 rather than the fresh +238 (the buy
  accrued fee buckets into total_virtual, so the floor rounds
  one higher), and a withdraw after a buy moves vq by -240
  rather than the fresh -239 (ceil on the same inflated total).
  A deposit/withdraw after a sell moves vq by the fresh
  +238/-239. The burn ladder itself is unaffected by the
  1-unit difference.

### Gates: slippage 6004, zero legs are no-ops, disable bits 6018/6019

- Deposit with base limit 160,619,895 (amount - 1) fails
  6004; deposit with quote limit 29,609 (transfer - 1) fails
  6004; withdraw with min base 160,619,897 (amount + 2) fails
  6004; withdraw with min quote 29,611 (above the 29,018
  payout) fails 6004. Every failed leg rolls back fully and
  the following boost is the anchor burn.
- Zero deposit and zero withdraw both succeed as 1-event
  no-ops (0 deltas) and the following boost is the anchor burn.
- Deposit under the deposit disable bit fails 6018; withdraw
  under the withdraw bit fails 6019; the following boosts are
  the anchor burn.
- Deposit under the bit, then the real `set_disable_flags`
  instruction clearing all bits, then deposit, then boost:
  the deposit succeeds (no vq patch before it, so the vq
  field is untouched by the deposit itself) and the boost is
  5,338,379,222,079 = anchor +20,248 -- the vault-only deposit
  effect, matching #114 and #118.

### Hop pools at depth 5: deposits fail on the shared LP mint; withdraws work; the hop burn is insensitive

- Hop-pool deposits fail on every hop leg and at every size:
  P2 deposit, P2 deposit 10^9, P3 deposit, P4 deposit, P4
  deposit 10^9, P5 deposit, P2/P4/P5 deposit after a buy, and
  P2/P4/P5 deposit at tf5000 all fail with Token-2022
  MintTo "owner does not match", custom 0x4, full rollback.
  Cause, measured from the fixture: all five pools share one
  LP mint whose mint authority is the MAIN pool PDA, while
  `mint_to_pool` signs with the depositing pool's own PDA
  seeds -- so a hop-pool deposit can never satisfy the mint
  authority on this fixture. The following hop boosts are
  unaffected (anchor hop burn 999,997,999 on every hop pool;
  post-buy hop burns P2 989,418,199, P4 989,528,958, P5
  989,596,358) and a failed hop deposit leaves the 5-hop tail
  at the anchor 5,207,955,235,891.
- Hop-pool withdraws work on every hop pool: P2, P4 and P5
  withdraw 10^6 each pay 238,415,844 of base and quote (both
  hop vaults hold 10^15), move the hop vq field by -239
  (ceil, same as the main pool), and the hop boost stays
  byte-identical at 999,997,999 -- the hop burn is insensitive
  to sweep-scale vq moves, as in #116 and #118.
- Patching the LP mint authority to the hop pool (a harness
  field reset, disclosed here) makes the deposit succeed and
  proves the failure is purely the authority mismatch: P4
  deposit pays BASE3 238,415,845 and BASE4 238,415,845 (ceil,
  both vaults 10^15), moves the P4 vq field by +238, and the P4
  boost is still exactly 999,997,999. P5 deposit behaves
  identically (vq +238, P5 boost 999,997,999). The patched
  P4/P5 deposit-withdraw round trips end at hop vq
  999,999,999 with the anchor hop burn. The patched P4
  deposit lifts the 5-hop tail by 6,482 (5,207,955,242,373)
  and the patched P5 deposit by 6,466 (5,207,955,242,357);
  the patched P2 deposit at depth 5 also lifts by 6,482,
  versus 6,620 at 3 hops -- again a genuine depth effect.

### Tf variants at depth 5

- tf5000 deposit: the user pays quote 58,626 (quote amount
  29,313 grossed up, 29,313 withheld in the vault -- the 50%
  fee doubles the quote leg), and the boost is
  2,706,767,015,328. tf5000 withdraw pays 14,656 net with the
  boost at 2,706,767,010,148.
- tf0 deposit: the user pays quote 29,313 flat (no
  withholding) and the boost is 5,391,870,666,177 = the tf0
  anchor burn 5,391,870,655,895 + 10,282.
- tf5000 deposit then 5-hop buy: tail 2,668,075,751,246.

## Limits

- The hop-deposit failure is a fixture property (one shared LP
  mint, authority = main-pool PDA), not a program gate: on a
  chain where each pool owns its LP mint, hop deposits would
  clear the mint authority. The packet pins the measured
  failure mode and the authority-patch recovery, not a general
  claim that hop deposits are impossible.
- The mint-authority patch cases use a harness field reset on
  the LP mint account, exactly as the vq patches reset pool
  fields; the deposit/withdraw/boost steps themselves are real
  instructions.
- The 1-unit vq round-trip residue not moving the burn is
  reported as measured; the packet does not prove the rounding
  mechanism behind hop-burn insensitivity.
- Error sites are recorded per image in the report's
  `error_sites` (Token-2022 failures carry no "thrown in" /
  "caused by account" site line, so none is asserted for them).

## Files

- `README.md` — this file.
- `producer.py` — the packet builder.
- `verify.py` — independent re-verification.
- `MANIFEST.json` — sha256 of every packet file except itself.
- `runtime/report.json.gz` — 71 cases, 684 receipts, 69 parts
  (68x10 + 4), per-image expected values, error sites, image hashes.
- `runtime/raw-transactions-part01..69.jsonl.gz` — the receipts,
  10 per part except part 69 (4).

## Verification

```
$ python3 verify.py
PASS: 71 cases, 684 receipts, 69 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchor with 5 hop events, deposit/withdraw vq ladder and burn ladder at depth 5, round-trip -1 vq with anchor burn, deposit-before-buy tail lift +9597 and deposit-before-sell payout unchanged, slippage 6004, zero-amount no-ops, disable 6018/6019, hop deposit Token-2022 OwnerMismatch (4) on P2/P3/P4/P5 and authority-patch recovery with byte-identical hop burns, patched hop deposit tail lifts +6482/+6466, tf5000 gross-up and tf0 flat legs); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []
```

Made via @slopdotcash
