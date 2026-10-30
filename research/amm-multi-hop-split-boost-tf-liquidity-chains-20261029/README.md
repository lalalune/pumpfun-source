# research: split x boost x tf chains meet liquidity legs at the boost, at TRUE 3-hop

3rd-run packet #118: the split x boost x tf chain at TRUE 3 hops
(`three_amm` only, final output U3) meets deposit and withdraw.

## Problem

Deposit and withdraw are not boost-neutral legs. When a pool can
boost, deposit adds to `virtual_quote_reserves` proportionally
(`deposit.rs`: vq += total_virtual x amount / old_supply, floor)
and withdraw subtracts it with a ceiling (`withdraw.rs`: vq -=
ceil(total_virtual x amount / old_supply)), and the boost burn
reads the vq field plus the real vaults (#100: burn slope about
-42.73 per vq unit; #102: the vq field also enters hop-1 pricing).
This packet measures, on the real 3-hop route main -> POOL2 -> P3,
exactly how much each liquidity leg moves the next boost burn, how
the deposit-then-withdraw round trip behaves (floor vs ceil), how
the liquidity gates (slippage, zero amounts, disable bits) interact
with a following boost, whether hop-pool liquidity legs reproduce
the main-pool behaviour, and how transfer fee reshapes deposit and
withdraw.

The route is a TRUE 3-hop route: `three_amm` only, three hop groups,
final output token U3. No g4/g5 hop group is added (the #61 miscount
does not apply here).

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

## Cases (45 cases, 146 steps, 438 receipts)

Family A — anchors and bare legs (bps 100): patched-window boost,
buy-then-boost, deposit 10^6 alone, withdraw 10^6 alone,
deposit-then-withdraw alone.

Family B — main-pool deposit -> boost: deposit 10^6 / 10^9 / 10^12
then boost; deposit-boost-boost; boost-deposit-boost; buy-deposit-
boost; deposit-buy (tail); deposit-buy-boost; deposit-protocol-
sweep-boost.

Family C — main-pool withdraw -> boost: withdraw 10^6 / 10^9 then
boost; buy-withdraw-boost; deposit-withdraw-boost and withdraw-
deposit-boost round trips; deposit-withdraw-deposit-boost;
withdraw-protocol-sweep-boost.

Family D — liquidity gates, then boost: deposit base-limit -1,
deposit quote-limit -1, withdraw min-base +2, withdraw min-quote
above the payout, zero deposit, zero withdraw, deposit under the
deposit disable bit, withdraw under the withdraw bit, and deposit
under the bit then cleared by the real `set_disable_flags`
instruction then deposit then boost.

Family E — hop-pool liquidity: P2 deposit then P2 boost, P2 deposit
10^9 then P2 boost, P2 withdraw then P2 boost, P3 deposit then P3
boost, P2 deposit then multi-hop buy, buy then P2 deposit then P2
boost, P2 deposit then P2 withdraw then P2 boost, and the same
deposit legs with the LP mint authority patched to the hop pool
(P2 deposit, P3 deposit, P2 deposit-withdraw, P2 deposit then
multi-hop buy).

Family F — tf variants: deposit-boost and withdraw-boost at
tf5000, deposit-boost at tf0, and the P2 deposit failure at
tf5000 (showing the failure is tf-independent).

## Result (0 divergent cases; control == candidate everywhere)

### Anchors and bare legs

- Fresh patched-window main boost burn 5,338,379,201,831;
  buy-then-boost burn 5,254,679,949,141; anchor buy tail
  5,262,910,281,902.
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

### The deposit ladder moves the burn, and the withdraw ladder mirrors it

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
  at 10^6 scale.
- Deposit before a buy lifts the multi-hop tail by 9,801
  (5,262,910,291,703); deposit-buy-boost is the post-buy burn
  +39,495 (5,254,679,988,636).
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
  effect, matching #114. Cross-check: +20,248 (vaults) minus
  238 x ~42.73 (the vq effect) equals the +10,079 patched
  deposit-boost burn above, consistent with #100's slope.

### Hop pools: deposits fail on the shared LP mint; withdraws work; the hop burn is insensitive

- Hop-pool deposits fail on every hop leg and at every size:
  P2 deposit, P2 deposit 10^9, P3 deposit, P2 deposit after a
  buy, and P2 deposit at tf5000 all fail with Token-2022
  MintTo "owner does not match", custom 0x4, full rollback.
  The two SPL transfers (base and quote) succeed first and
  then the mint_to CPI fails. Cause, measured from the fixture:
  all three pools share one LP mint whose mint authority is
  the MAIN pool PDA, while `mint_to_pool` signs with the
  depositing pool's own PDA seeds -- so a hop-pool deposit can
  never satisfy the mint authority on this fixture. The
  following hop boosts are unaffected (anchor hop burn
  999,997,999; post-buy hop burn 989,418,199) and a failed hop
  deposit leaves the multi-hop tail at the anchor.
- Hop-pool withdraws work: P2 withdraw 10^6 pays base and
  quote 238,415,844 each (both P2 vaults hold 10^15), moves the
  P2 vq field by -239 (ceil, same as the main pool), and the
  P2 boost stays byte-identical at 999,997,999 -- the hop burn
  is insensitive to sweep-scale vq moves, as in #116.
- Patching the LP mint authority to the hop pool (a harness
  field reset, disclosed here) makes the deposit succeed and
  proves the failure is purely the authority mismatch: P2
  deposit pays base 238,415,845 and BASE2 238,415,845 (ceil,
  both vaults 10^15), moves the P2 vq field by +238, and the P2
  boost is still exactly 999,997,999. P3 deposit behaves
  identically (vq +238, P3 boost 999,997,999). The patched
  P2 deposit-withdraw round trip ends at hop vq 999,999,999
  with the anchor hop burn. The patched P2 deposit lifts the
  multi-hop tail by 6,620 (5,262,910,288,522).

### Tf variants

- tf5000 deposit: the user pays quote 58,626 (quote amount
  29,313 grossed up, 29,313 withheld in the vault -- the 50%
  fee doubles the quote leg), and the boost is
  2,706,767,015,328. tf5000 withdraw pays 14,656 net with the
  boost at 2,706,767,010,148.
- tf0 deposit: the user pays quote 29,313 flat (no
  withholding) and the boost is 5,391,870,666,177 = the tf0
  anchor burn 5,391,870,655,895 + 10,282.

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
- `runtime/report.json.gz` — 45 cases, 438 receipts, 44 parts
  (43x10 + 8), per-image expected values, error sites, image hashes.
- `runtime/raw-transactions-part01..44.jsonl.gz` — the receipts,
  10 per part except part 44 (8).

## Verification

```
$ python3 verify.py
PASS: 45 cases, 438 receipts, 44 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, deposit/withdraw vq ladder and burn ladder, round-trip -1 vq with anchor burn, slippage 6004, zero-amount no-ops, disable 6018/6019, hop deposit Token-2022 OwnerMismatch (4) and authority-patch recovery with byte-identical hop burns, tf5000 gross-up and tf0 flat legs); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []
```

Made via @slopdotcash
