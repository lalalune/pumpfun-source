# amm-multi-hop-split-boost-tf-user-wallet-chains-20261029

## Problem

3rd #93 pinned the chain as user-blind across users and #88 pinned
the vault/token-account validation slots, but neither pinned the
paying user's own wallet as a state machine: which wallet defects
fail a trade, which are ignored, what a trade costs the payer
beyond the quoted amounts, and what a failed or repeated trade
leaves behind in the wallet. The multi-hop route's wallet roles
are easy to misread -- the buy input is userquote, the sell input
is the tail output account U3, the sell output is userquote again,
and userbase is not an input at all -- so this packet patches the
wallet accounts themselves (amounts, lamports, frozen state,
owner, mint, absence) on the split x boost x tf chain at true 3
hops (three_amm only, final output U3) and pins what each patch
does to the next leg.

## Cases

85 cases, 321 receipts, 33 parts (32x10 + 1).

Family A -- buy-input amount (userquote, Token-2022 178 bytes,
tf100, buy 10^9 quote): `a-anchor` (tail U3 5,262,910,281,902),
`a-amt-exact-rent` (amount exactly 10^9 with lamports
amount + 2,039,280, then the same amount with lamports topped to
10^9 + 2,129,760), `a-amt-exact-floor` (amount 1,000,090,480 with
lamports amount + 2,039,280), `a-amt-minus1` (999,999,999),
`a-amt-half` (5 x 10^8), `a-amt-zero` (0), `a-amt-wh`
(pre-seeded withheld 12,345 on userquote).

Family B -- buy-input lamports, the native rent floor (post-trade
lamports X, amount 10^15): `b-floor-minus1` (X = 2,129,759),
`b-floor-exact` (X = 2,129,760), `b-floor-2129280`
(X = 2,129,280, the SPL 165-byte rent), `b-floor-2157600`
(X = 2,157,600), `b-rentonly-custom14` (lamports 2,039,280),
`b-rentonly-rentfail` (lamports 10^9 + 2,039,280).

Family C -- buy-input state / owner / mint / absence /
fail-then-recover: `c-frozen` (state 2), `c-uninit` (state 0),
`c-outsider` (owner outsider), `c-absent` (account removed),
`c-wrongmint` (mint base), `c-fail-sweep-buy` (buy with amount
5 x 10^8, TOKEN22 protocol sweep, restored buy).

Family D -- sell-input U3 and output-owner asymmetry (sell 10^9
base, anchor payout 178,541): `d-sell-anchor`, `d-amt-exact`
(U3 10^9), `d-amt-minus1` (999,999,999), `d-amt-half`,
`d-amt-zero`, `d-frozen` (U3 state 2), `d-lam0` (U3 lamports 0),
`d-lam1` (U3 lamports 1), `d-outsider` (U3 owner outsider),
`d-out-outsider-buy` (buy with U3 owner outsider),
`d-out-frozen-buy` (buy with U3 state 2),
`d-out-frozen-sell` (sell with userquote state 2),
`d-out-outsider-sell` (sell with userquote owner outsider).

Family E -- userbase is never touched by multi-hop: `e-absent-buy`,
`e-absent-sell`, `e-frozen-buy`, `e-outsider-sell`, `e-amt0-buy`.

Family F -- payer funds the UVA auto-init: `f-first-buy`,
`f-second-buy` (two buys), `f-first-sell`, `f-seeded-buy`
(seeded UVA), `f-payer-exact` (payer 1,849,400),
`f-payer-minus1` (payer 1,849,399), `f-payer-seeded-exact`
(seeded UVA, payer 5,000), `f-payer-seeded-minus1` (seeded UVA,
payer 4,999), `f-sweep-noinit` (TOKEN22 protocol sweep,
unseeded), `f-v2buy-init` (v2 buy 10^6, unseeded),
`f-boost-noinit` (boost with main vq patched to 10^9, unseeded),
`f-col-noinit` (TOKEN22 collect, unseeded),
`f-fail-noinit` (failed buy, restored buy),
`f-close-cycle` (buy, close, buy), `f-init-cost` (init, buy).

Family G -- cashback claim destination wallet (plain mode,
uvata funded with 5,475, seeded UVA earned 5,475): `g-anchor`,
`g-frozen` (userquote state 2), `g-outsider` (userquote owner
outsider), `g-absent` (userquote removed), `g-twice` (two
claims), `g-after-buy` (plain buy, then claim).

Family H -- deposit / withdraw wallet legs: `h-dep-anchor`
(deposit 10^6 base), `h-dep-ub-exact` (userbase exactly
160,619,896), `h-dep-ub-short` (160,619,895), `h-dep-uq-exact`
(userquote exactly 29,610), `h-dep-uq-short` (29,609),
`h-dep-uq-zero`, `h-dep-ulp-frozen`, `h-dep-ulp-absent`,
`h-dep-ub-frozen`, `h-wd-anchor` (withdraw 10^6 LP),
`h-wd-ulp-short` (userlp 10^5), `h-wd-ulp-frozen`,
`h-wd-ub-frozen`, `h-wd-uq-frozen`, `h-wd-toomuch` (withdraw
10^15 LP), `h-dep-wd-dust` (deposit then withdraw).

Family I -- wallet exhaustion chains: `i-buy-chain` (three buys),
`i-buy-amt-chain` (userquote 2 x 10^9, three buys),
`i-buy-rent-chain` (userquote 2 x 10^9 with lamports
2 x 10^9 + 2,039,280, buy, buy, lamports topped to 3 x 10^9,
buy, buy), `i-sell-chain` (U3 2 x 10^9, three sells),
`i-sell-topup` (U3 10^9, sell, sell, U3 topped to 10^9, sell).

Family J -- v2 wallet legs: `j-v2-anchor` (v2 buy 10^6 base),
`j-v2-outsider`, `j-v2-frozen`, `j-v2-short` (userquote 100),
`j-v2-sell-anchor` (v2 sell 10^6 base), `j-v2-sell-frozen`.

## Result

All 85 cases agree on all three images: **0 divergences**.

- The buy input is strict. Amount below the 10^9 gross fails
  Token custom 1 with 0 events (999,999,999, 5 x 10^8, and 0 all
  fail alike -- there is no partial fill). A frozen input fails
  Token custom 17 with 0 events; an uninitialized input fails
  UninitializedAccount (caused by account:
  user_in_token_account); an absent input fails 3012 (caused by
  account: user_in_token_account); a wrong-mint input fails 6084
  MultiHopDiscontinuousPath (multi_hop_swap.rs:251); an input
  owned by someone other than the payer fails Token custom 4.
  The input leg's authority is the payer, full stop.
- The output leg is lax. An outsider-owned U3 still receives
  the full buy tail (5,262,910,281,902) and an outsider-owned
  userquote still receives the full sell payout (178,541) -- the
  output account's owner is never checked. Only a frozen output
  fails, with Token custom 17 and 2 ghost events on multi-hop
  (the first two hops emit, the tail hop fails), versus 0 events
  on a v2 leg.
- The native rent floor is exact. A buy whose post-trade
  userquote lamports fall below 2,129,760 -- the rent-exempt
  minimum for a 178-byte Token-2022 account, (128 + 178) x 6960
  -- fails with TransactionErrorInsufficientFundsForRent
  (account_index 5) with all 3 hop events in the logs but zero
  state change except the 5,000 fee: 2,129,759 fails, 2,129,760
  succeeds. The SPL 165-byte rent 2,129,280 is not enough for
  the 178-byte account. Amount exactly 10^9 with lamports
  amount + 2,039,280 fails the same way (post-trade 2,039,280),
  but topping lamports to 10^9 + 2,129,760 makes the identical
  amount succeed -- the binding constraint is lamports, not
  tokens. Amount 1,000,090,480 with lamports amount + 2,039,280
  succeeds exactly at the floor (post-trade 2,129,760). The two
  failure regimes are distinct: lamports that would go negative
  fail at the program level with Token custom 14 and 0 events
  (lamports 2,039,280 against amount 10^15), while positive but
  below-floor lamports fail at the runtime rent check with 3
  logged events and full rollback.
- A pre-seeded withheld balance on the input is untouched: buy
  with userquote withheld 12,345 succeeds at the anchor tail
  with withheld still 12,345 after (the buy's own withheld
  accrues at the vault and buyback legs, 10,000,000 and 45,611).
- The sell output's lamports exceed its token delta by exactly
  the withheld amount: payout 178,541 tokens, withheld +1,804,
  lamports +180,345 (gross). The buy input shows no such split
  (tokens -10^9, lamports -10^9, withheld 0) -- the fee is
  withheld at the destination, never at the source.
- userbase is dead weight on multi-hop. Absent, frozen,
  outsider-owned, or zero-balance userbase leaves buys and
  sells byte-identical to the anchor (buy tail
  5,262,910,281,902, sell payout 178,541). The route's real
  wallets are userquote (buy in, sell out) and U3 (buy out,
  sell in); userbase only matters to deposit/withdraw/v2 legs.
- The first trade auto-creates the user's volume accumulator,
  and the payer pays for it. An unseeded buy or sell costs the
  payer 1,849,400 (fee 5,000 + UVA rent 1,844,400 for 137 bytes)
  and leaves a zero-field UVA with 1,844,400 lamports; the second
  trade costs only the 5,000 fee. A seeded UVA drops the first
  trade to 5,000 as well. The payer threshold is exact: 1,849,400
  succeeds unseeded, 1,849,399 fails Token custom 1; seeded,
  5,000 succeeds and 4,999 fails InsufficientFundsForFee with 0
  events and no fee charged. v2 buys auto-create the UVA too
  (1,849,400 on a 10^6-base buy that spends only 189 quote),
  while sweep, collect, and boost never create it (5,000 fee,
  volume stays absent). An explicit init costs the same 1,849,400
  and the following buy costs 5,000. A failed trade never
  creates it: a custom-1 failed buy leaves the volume absent,
  and the restored buy pays the full 1,849,400 at the anchor
  tail. Close refunds the auto-created UVA (+1,839,400 =
  1,844,400 - 5,000 fee) and the next buy pays the rent again,
  landing on the second-buy tail (5,072,980,706,277) -- close
  refunds rent but does not rewind the curve.
- Cashback claims check the destination wallet, not just the
  accumulator. The funded claim pays 5,475 (uvata -5,475,
  cb_claimed 0 -> 5,475); a frozen destination fails Token
  custom 17, an outsider-owned destination fails 2015, an absent
  destination fails 3012 (caused by account:
  user_wsol_token_account); a second claim emits its event but
  pays 0. A plain buy before the claim leaves the claim at the
  full 5,475 (plain buy tail 5,315,084,721,958, SPL buyback) --
  trades do not touch cashback earnings.
- Deposit and withdraw are exact-amount legs. Deposit spends
  exactly 160,619,896 base + 29,610 quote for 1,000,000 LP; one
  unit short on either side fails Token custom 1, zero quote
  fails the same way, a frozen LP / base / quote account fails
  Token custom 17, and an absent LP account fails 3012. Withdraw
  of 10^6 LP returns 160,619,895 base (one less than deposit
  spent, the #91 flooring dust) plus 29,018 quote; withdrawing
  more LP than held fails Token custom 1 (10^5 held vs 10^6
  asked, and 10^15 asked vs the fixture balance alike), and a
  frozen leg fails Token custom 17.
- Wallet exhaustion is curve-neutral. Three chained buys decay
  5,262,910,281,902 -> 5,072,980,706,277 -> 4,893,150,521,808.
  With userquote 2 x 10^9, the third buy fails custom 1 (amount
  exhausted). With lamports 2 x 10^9 + 2,039,280, the second buy
  fails the rent check (post-trade 2,039,280), topping lamports
  to 3 x 10^9 makes the next buy succeed at the second-buy tail
  (5,072,980,706,277), and the buy after that fails custom 1
  (amount exhausted). With U3 2 x 10^9, sells pay 178,541 then
  178,540, then fail custom 1; topping U3 back to 10^9 after a
  failed sell pays 178,540 -- the second-sell value, not the
  anchor -- proving the failed sell moved nothing.
- v2 mirrors multi-hop's input rules: outsider-owned input
  fails custom 4, frozen input fails custom 17, short input
  fails custom 1, and a frozen sell output fails custom 17 with
  0 events (no ghost ladder on the single-hop leg). The v2 buy
  of 10^6 base spends 189 quote (vault quote +186, withheld 2
  at the vault and 1 at the buyback).

## Relation to earlier packets

- #93 established that trades are user-blind across users; this
  packet shows the boundary of that blindness -- the payer must
  own the input leg, while the output leg accepts any owner.
- #88 established vault/token-account validation slots; this
  packet extends the same codes to the user's own wallets on the
  chain (custom 1/4/17, 3012, 6084) and adds the rent floor and
  the withheld-vs-lamports split, which #88 did not measure.
- #91 established amount thresholds and ceiling rounding; this
  packet shows the wallet-side thresholds are exact on both
  sides (amount -1 fails, lamports -1 below the floor fails)
  and that deposit/withdraw dust (1 base) is wallet-visible.
- #92 established state transitions and the window invariant;
  this packet shows the wallet state transitions that gate those
  transitions (auto-init cost, close refund, exhaustion chains).
- #68 established the UVA lifecycle at the fixture clock; this
  packet pins who pays for each lifecycle step (init and first
  trade 1,849,400, close +1,839,400, later trades 5,000).
- #96 established account-length gates; this packet shows the
  wallet-side length consequence -- a 178-byte Token-2022 native
  account rents at 2,129,760, not at the SPL 165-byte 2,039,280.

## Limits

- Wallet patches are applied directly to the account between
  steps; they are not transactions and leave no receipt. The
  receipt stream pins the before/after state of every real step,
  and producer.py records every patch in the case definitions,
  so the sequence is reproducible from the packet files -- but
  a patch itself has no signature to verify.
- The rent-floor account index (account_index 5) is recorded as
  reported by the runtime; the failing account is identified as
  userquote by the lamport bisection (only userquote lamports
  were varied, and the floor equals the 178-byte rent formula),
  not by decoding the runtime's account ordering.
- No source change is proposed and no program is rebuilt: the
  packet pins observed behaviour of the three images only.
- Only the TRUE 3-hop route (three_amm, final output U3)
  is used; 4-hop and 5-hop routes are covered by #61/#62
  and #65/#66 and are not re-run here.

## Reproduce

`python3 producer.py` rebuilds the receipts under
`runtime/` (10 per part, 33 parts); `python3 verify.py`
re-checks signatures, deltas, withheld, pool/UVA/GVA/
GlobalConfig states, decoded events, error codes, rollback,
and three-image agreement from the packet files alone.

Made via @slopdotcash
