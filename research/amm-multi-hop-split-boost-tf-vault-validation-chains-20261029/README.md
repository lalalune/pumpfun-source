# research: vault and token-account validation on the split x boost x tf chain (TRUE 3-hop)

## Problem

Packets #83-#87 pinned the same account-validation surface for the
fee-table account, the GlobalConfig, the pool, the
UserVolumeAccumulator, and the GlobalVolumeAccumulator on the
split x boost x tf chain. This packet pins it for the accounts the
trade legs actually move value through: the per-hop base/quote
vault ATAs, the user base/quote/LP token accounts, the tail output
account U3, and the Token-2022 buyback/sweep/collect ATAs.

Token accounts carry no discriminator (mint at bytes 0:32, ATA
owner at 32:64, amount as u64 at 64, state at byte 108: 0
uninitialized, 1 initialized, 2 frozen), so the surface is wrong
mint, wrong ATA owner, wrong owning program, zero or below-rent
lamports, zero amount, uninitialized or frozen state, and
instruction account-key swaps -- measured on multi-hop buy/sell,
v2 buy/sell, legacy buy/sell, deposit/withdraw, sweep/collect, and
boost legs, plus whether a tail-vault failure leaks into the
main-pool downstream legs.

## Route

`build_route` calls `three_amm` only and appends no g4/g5 hop
group, so the route is main -> POOL2 -> P3 with final output U3:
TRUE 3 hops. The quote mint carries a 100 bps transfer-fee config
and the split legs route the buyback through the Token-2022 ATA,
as in #64. Anchors (all three images agree):

- multi-hop buy 1e9: tail U3 5,262,910,281,902, buyback
  4,515,471, withheld vq1 10,000,000 / buyback 45,611, 3 BuyEvents
  (disc 67f4521f2cf57777, len 508 each).
- multi-hop sell 1e9: userquote +178,541, 3 SellEvents
  (disc 3e2f370aa503dc2a, len 449 each).
- v2 buy 1e10 / sell 1e10, deposit 1e9, withdraw 1e9, legacy buy
  1e10 (limit 1e12) / legacy sell 1e9, boost 1e9 on a 1e9 virtual
  quote patch (burn 5,338,379,201,831, the #64 tf100 anchor), and
  protocol sweep 2,488 -> net 2,463 (withheld 25) all succeed.
- Legacy buy/sell events share the multi-hop discriminators
  (BuyEvent len 497, SellEvent len 449).

## Cases (80 cases, 261 receipts, 27 parts)

- A (10 anchors): mhbuy3, mhsell3, buy2, sell2, dep, wd, legbuy,
  legsell, boost, swp22.
- V (13, owning program): vq1 -> SPL Token / System / default
  pubkey; vb1 -> Token-2022 / System; vq2 -> Token-2022 / System;
  vq3 -> Token-2022 / default; plus vq1 -> SPL Token on sell, v2
  buy, deposit, and sweep.
- M (11, mint): vq1 -> base / BASE2 / zero; vb1 -> quote / BASE2;
  vq2 -> BASE3; vb3 -> BASE2; userquote -> base; U3 -> BASE2;
  plus vq1 -> base on sell and on v2 buy.
- O (7, ATA owner): vq1 -> outsider / zero; vb1 -> outsider;
  userquote -> outsider; U3 -> outsider; buyback ATA -> outsider;
  user LP -> outsider on deposit.
- L (9, lamports): vq1 / vb1 / vq3 at 0, 1, 1,000,000;
  userquote at 0 and at exactly the rent-exempt minimum
  (2,039,280, zero spendable balance).
- S (6, amount/state): vq1 amount 0; vb1 amount 0; vq1 state 0 / 2;
  vb1 state 0; userquote amount 0.
- K (10, key swaps on the multi-hop route): vq1 slot -> vb1 /
  VQ2 / fresh / userquote; vb1 slot -> vq1; vq3 slot -> vq1;
  userquote slot -> userbase / fresh; U3 slot -> userquote;
  vq1 slot -> vb1 on sell.
- X (3, combined): vq1 mint + owning program; vq1 lamports 0 +
  mint; vq1 owning program + ATA owner.
- W (5, downstream after a tail-vault failure): tail mint fault,
  then protocol sweep + creator sweep + collect; tail mint
  fault, then boost; tail mint fault, then token claim; tail
  base-vault owning-program fault on sell, then cashback claim;
  tail mint fault on sell, then protocol sweep.
- P (6, leg parity): vq1 -> SPL Token on sell2, legbuy, boost,
  withdraw; vb1 -> System on buy2; vq1 -> base on legsell.

## Result

All 80 cases agree on all three images (original, control #424,
candidate #427); 0 divergent. Every failure rolls back every
watched account except the fee payer (fee 5,000).

### Owning program: the Anchor gate accepts either token program

- A vault owned by the System Program or by the default pubkey
  fails 3007 AccountOwnedByWrongProgram at the hop's validation
  (site: `pool_quote_token_account` / `pool_base_token_account`).
- A vault owned by the *other* token program passes that gate
  and fails inside the token CPI instead: a Token-2022 vault
  owned by SPL Token fails IncorrectProgramId on mhbuy3, mhsell3,
  buy2, dep, swp22, boost, wd, and legbuy alike, while an SPL
  vault owned by Token-2022 fails ExternalAccountDataModified.
  The owner gate is program-set membership (SPL or Token-2022);
  the layout/program match is enforced inside the CPI.
- The same split appears on single legs: vb1 -> System fails
  3007 on buy2 as on mhbuy3; vq1 -> SPL Token fails
  IncorrectProgramId on every leg tested.

### Mint and ATA owner: token program vs route check

- A vault with the wrong mint fails token-program custom 3 and
  a vault with the wrong ATA owner fails custom 4, on every hop
  and every leg (including deposit's quote vault and the sweep's
  quote vault). #85's pool-mint binding error 6008 does NOT
  appear here: vault mint binding is a token-program check,
  not a pool check.
- The user accounts are different: a wrong userquote mint fails
  6084 MultiHopDiscontinuousPath at multi_hop_swap.rs:251 and a
  wrong U3 mint fails 6084 at multi_hop_swap.rs:300 -- the route
  continuity check, not the token program. And the output
  account's ATA owner is not checked at all: an outsider-owned
  U3 succeeds with an anchor-identical payout (contrast: an
  outsider-owned userquote input fails custom 4).
- The buyback ATA's owner is checked against the authorized
  recipient list: an outsider-owned buyback ATA fails 6053
  BuybackFeeRecipientNotAuthorized at global_config.rs:326.
  A deposit into an outsider-owned LP account fails Anchor
  2015 ConstraintTokenOwner.

### Lamports, amount, state

- A 0-lamport vault or user account vanishes from the VM and
  fails 3012 AccountNotInitialized at the hop's validation
  (site: the vault or `user_in_token_account`). 1 lamport and
  1,000,000 lamports (below rent-exempt) both succeed
  anchor-identically: no rent-exempt minimum is checked. This
  is exactly the #83-#87 pattern.
- A rent-only native user account (lamports equal to the
  rent-exempt minimum, zero spendable balance) fails
  Token-2022 custom 14 on the buy input transfer. A native user
  account whose data amount field is zeroed (lamports
  untouched) fails token custom 1: the transfer reads the data
  amount field, not the lamports-derived balance.
- A zero-amount quote vault fails 6023 Overflow at pool.rs:417;
  a zero-amount base vault fails 6025 DivisionByZero at
  pool.rs:386. State byte 0 fails UninitializedAccount (site:
  the vault account); state byte 2 (frozen) fails token custom
  17.

### Key swaps: pool binding, with the init check first

- A base-vault slot holding another account fails 6014
  InvalidPoolBaseTokenAccount and a quote-vault slot holding
  another account fails 6015 InvalidPoolQuoteTokenAccount,
  both reported against the pool account (the pool's stored
  vault keys must match the passed accounts). A userquote slot
  holding the userbase key fails 6084 at multi_hop_swap.rs:251
  and a U3 slot holding the userquote key fails 6084 at
  multi_hop_swap.rs:300.
- A fresh (nonexistent) key fails 3012 first, on the vault slot
  and on the userquote slot alike: the initialization check
  precedes the pool-binding check.

### Check order

On a vault: existence > owning program > content. Lamports 0 +
wrong mint fails 3012; wrong mint + wrong owning program fails
IncorrectProgramId; wrong owning program + wrong ATA owner
fails IncorrectProgramId.

### Per-hop lazy validation and ghost events

Each hop's vault checks run when that hop is processed, so
ghost events pin the failing transfer, not just the hop:

- Buy direction (main -> POOL2 -> P3): a main-hop in-side
  fault (vq1) leaves 0 ghost events, a main-hop out-side fault
  (vb1) leaves 1, a middle-hop in-side fault (vq2) leaves 1, a
  tail-hop in-side fault (vq3) leaves 2, and a tail-hop
  out-side fault (vb3) leaves 2.
- Sell direction reverses (tail hop first, main hop last): a
  tail-hop out-side fault (vq3) leaves 1 ghost event, a
  main-hop in-side fault (vq1) leaves 2.
- The rule: non-terminal hop events sit between the hop's
  in-transfer and out-transfer, and the terminal hop's event
  sits after its out-transfer. Anchor-gate failures (3007 /
  3012 / 6014 / 6015) leave only the completed hops' events,
  because validation for a hop runs before that hop's
  transfers.

### Leg parity and downstream

- The same fault fails identically on multi-hop buy/sell, v2
  buy/sell, legacy buy/sell, deposit/withdraw, sweep, and
  boost legs. Method note: an early legbuy probe failed 6004
  ExceededSlippage at buy.rs:405 with a limit argument of 1
  even with no fault; with a sufficient limit (1e12) the
  legbuy fault fails IncorrectProgramId like every other leg.
- After a tail-vault failure the downstream legs all still
  work with no leak: protocol sweep 2,488 -> net 2,463,
  creator sweep 123,394 -> net 122,160, collect 122,160 ->
  net 120,938, boost burn 5,338,379,201,831, token claim
  3,334,551, and cashback claim 5,475 -- all anchor-identical.

### Comparison with #83-#87

| account | disc wrong | owner wrong | lamports 0 | check order |
| --- | --- | --- | --- | --- |
| fee-table (#83) | 3002 | 3007 | 3012 | 3012 > 3007 > 3002 |
| GlobalConfig (#84) | InvalidAccountData | 3007 | 3012 | 3012 > 3007 > InvalidAccountData |
| Pool (#85) | InvalidAccountData | 6027 (multi-hop) / 3007 | 6027 (multi-hop) / 3012 | single 6027 gate (multi-hop) |
| UVA (#86) | 3002 | 3007 | 3012 | 3012 > 3007 > 3002 |
| GVA (#87) | 3002 | 3007 | 3012 | 3012 > 3007 > 3002 > seeds 2006 |
| vault / token account (#88) | n/a (no discriminator) | 3007 (non-token owner) / CPI error (other token program) | 3012 | 3012 > owner gate > content |

Vaults are the only surface where the owner check splits into
two layers (Anchor gate vs token CPI) and where a wrong mint is
a token-program error (custom 3) rather than a program error
(6008 / 3002 / InvalidAccountData).

## Limits

- LiteSVM harness measurements on the original, control (#424),
  and candidate (#427) images only; no on-chain execution.
- Error sites are recorded per image from the receipt logs and
  are never compared across images (line numbers differ between
  the original and the rebuilds).
- Token-program custom codes 1, 14, and 17 are reported as
  observed codes with their triggering conditions; only 3
  (mint) and 4 (owner) are named, from the consistent
  mint-fault -> 3 / owner-fault -> 4 pattern across all cases.
- The legbuy limit argument must be sufficient (1e12 used
  here); a limit of 1 fails 6004 ExceededSlippage even with no
  vault fault, which is a property of the leg's arguments, not
  of vault validation.
- No source change, no build, and no whole-program equivalence
  claim: only the measured legs above.

## Reproduce

```
python3 verify.py
```

`verify.py` re-checks, from the packet files alone (plus the
three program images): MANIFEST sha256 values, report counts
(80 cases, 261 receipts, 27 parts) and part hashes, receipt
signature verification, per-image expected deltas / withheld /
lamports / pool states / UVA / GVA / GlobalConfig fields, event
disc/len and decoded fields, error codes, rollback, 3-image
agreement, and per-image error-site lines.

Made via @slopdotcash
