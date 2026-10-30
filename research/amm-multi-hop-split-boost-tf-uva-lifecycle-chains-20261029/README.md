# research: split x boost x tf chains meet the UVA lifecycle (TRUE 3-hop)

## Problem

3rd #64/#65/#66 pinned the split x boost x transfer-fee chain at TRUE
depths 3, 5, and 4, and 3rd #67 chained token/cashback claims onto
it. 3rd #1 pinned the user volume accumulator close lifecycle and
3rd #27 pinned extend_account, but both did so on single-pool
setups. What nobody had done is chain the lifecycle onto the split
chain in one VM: does a claim-then-close on the split chain refund
the full balance while leaving the 500 unclaimed tokens unpaid, do
claim/sync/a second close/cashback-claim all fail 3012 on the
closed account, does re-init restore a fully fresh 137-byte
account that the chain then uses normally, does extend 90 -> 137
preserve every field and extend 50 -> 137 rewrite the truncated
layout the same way on the split chain, do the close authorization
gates (other signer 2006, unsigned user 3010, close-then-extend
2004, read-only extend target 2000) hold, and do close/extend
move the boost burn, the tail output, or the hop-1 tier-cap
crossing at all?

Route (read from the builder, not the packet name): `three_amm`
only, no g4/g5 hop group appended, so the route is
main -> POOL2 -> P3, final output U3: TRUE 3 hops. The quote mint
carries a per-case transfer-fee config (0/100 bps) with the split
legs routing the buyback through the TOKEN22 ATA; the claim mint
IMINT (bytes([226]) * 32, Token-2022) carries its own transfer-fee
config (0 bps here unless a case says otherwise). The global
volume accumulator is seeded (20, 49, 1, then 30 x 1000 and
30 x 100). Seeded user volume accumulators are either
(needs_claim 1, unclaimed 111, claimed 222, volume 333444,
last 20, has_total_claimed_tokens 1, cashback_earned 555,
total_cashback_claimed 666) at 10^9 lamports, or
(needs_claim 1, unclaimed 500, claimed 700, volume 20, last 10,
has 1, cashback_earned 55, total_cashback_claimed 13) at the
lamports a case states. All figures below are measured on the
original image; control and candidate agree on every case
(0 divergent cases).

## Cases (20 cases, 204 receipts, 21 parts)

- `a-tclaim-close-reinit-tclaim-swc-col`: seeded claim, close,
  re-init, claim, sweep, collect.
- `a-close-unclaimed500`: close of the 500-unclaimed seed, alone.
- `a-tclaim-close-tclaim`, `a-tclaim-close-sync`,
  `a-tclaim-close-close`, `a-tclaim-close-cclaim` (plain-quote
  mode): each post-close step after claim-then-close.
- `a-close-by-other`, `a-close-unsigned`: close authorization
  gates.
- `b-extend90-tclaim-close`: 90-byte seed (1,517,280 lamports)
  extended, claimed, closed.
- `b-extend137-noop-tclaim-close`, `b-extend138-noop-close`:
  at-target and above-target extends.
- `b-extend50-tclaim-close`: 50-byte seed (10^9 lamports)
  extended, claimed, closed.
- `b-close-extend-init-extend`: close, extend, re-init, extend.
- `b-extend-unsigned-signed-close`,
  `b-extend-readonly-signed-tclaim`, `b-extend-twice-tclaim-close`:
  extend authorization gates and the double extend.
- `c-buy-close-reinit-buy-swc-col`: buy, close, re-init, buy,
  sweep, collect.
- `c-buy-boost-close-reinit-buy-boost` (main vq patched to 10^9):
  buy, boost, close, re-init, buy, boost.
- `c-tiercap-close-reinit-buy` (main vq patched to 10^9, tiers
  A = (10, 111, 333) at cap 100, B = (20, 222, 444) at cap
  185,000,000,000): buy, close, re-init, buy.
- `c-buy-tf100-close-reinit-buy-swc-col`: the same lifecycle
  under quote tf100.

## Result

- Claim-then-close refunds the full balance and pays nothing
  else. After a seeded token claim (3,334,551 = 111 +
  333444 * 1000 / 100, total_claimed 3,334,773), close returns
  +999,995,000 (10^9 balance minus the 5,000 fee) and its
  CloseEvent (disc 929fbdac925838f4, len 80) reports the
  post-claim fields (unclaimed 0, claimed 3,334,773, volume 0,
  last 21, ts 10). The account is gone afterwards.
- The 500 unclaimed tokens are NOT paid out by the close. A
  close of the 500-unclaimed seed returns exactly +999,995,000
  with zero token deltas, and its CloseEvent reports
  unclaimed 500, claimed 700, volume 20, last 10 -- the 500
  exist only in the event.
- After a close, token claim, sync, a second close, and
  cashback claim ALL fail 3012 AccountNotInitialized (site:
  user_volume_accumulator), each costing only the 5,000 fee
  with full rollback of everything else.
- Re-init after a close creates a FRESH 137-byte account
  (1,844,400 lamports rent + 5,000 fee = payer -1,849,400,
  InitEvent disc 86240d48e86582d8, len 80, payer = user,
  ts 10) with all 9 fields zero. The following token claim
  is a zero claim (0 events, log "No tokens to claim",
  last 0 -> 21), and the following sweep/collect drain the
  full creator bucket 123,394.
- Extend 90 -> 137 preserves every field byte-for-byte and
  tops the rent up exactly: payer -332,120 (47 * 6,960 top-up
  + 5,000 fee), ExtendEvent (disc 6161d7905d92167c, len 96)
  old 90 new 137, fields (needs 1, unclaimed 500, claimed 700,
  volume 20, last 10, has 1, cashback_earned 55,
  total_cashback_claimed 13) untouched. The following claim
  pays the 500 unclaimed (claimed 700 -> 1200, volume 20,
  last 21), and the close after it refunds 1,839,400 with a
  close event reporting claimed 1200.
- Extend at target (137) and above target (138) are silent
  no-ops: 0 events, payer -5,000 only, fields untouched; the
  following claim and close run identically.
- Extend 50 -> 137 rewrites the truncated field layout:
  payer -610,520 (87 * 6,960 + 5,000 fee), balance
  10^9 -> 1,000,605,520, fields become (needs 1, unclaimed
  500, claimed 188 -- the low byte of 700 -- volume 0,
  last 0, has 0, cashback_earned 0, total_cashback_claimed 0).
  The following claim pays 500 (claimed 188 -> 688), and the
  close after it refunds 1,000,600,520.
- Close after close-then-extend fails 2004 ConstraintOwner
  (site: account); re-init after it succeeds, and a further
  extend on the fresh account is a silent no-op.
- Close authorization binds to the PDA seeds, not the stored
  user field: close by another signer fails 2006
  ConstraintSeeds (site: user_volume_accumulator), and close
  with an unsigned user fails 3010 AccountNotSigner (site:
  user). Both cost only the 5,000 fee with full rollback.
- Extend authorization mirrors it: extend with an unsigned
  user fails 3010 AccountNotSigner, extend with a read-only
  target fails 2000 ConstraintMut (site: account); the signed
  extend right after each failure succeeds, and extend twice
  makes the second extend a silent no-op (0 events, -5,000).
- The lifecycle moves nothing on the chain. Buy, close,
  re-init, buy reproduces the uninterrupted second buy
  exactly (tail 5,121,405,353,567, buyback 4,607,153), and
  sweep/collect after it drain the full 123,394. Buy, boost,
  close, re-init, buy, boost reproduces the uninterrupted
  buy-boost-buy-boost chain exactly: first burn
  5,307,028,789,111, second buy tail 5,003,067,470,011,
  second burn 5,142,500,299,802 (measured on the uninterrupted
  chain as a control probe). The tier-cap second buy is
  5,019,668,351,471 with close + re-init between the buys,
  exactly as in 3rd #67's uninterrupted tier-cap chain.
  Under tf100 the lifecycle is likewise neutral: buy tails
  5,262,910,281,902 then 5,072,980,706,277, sweep net
  122,160 / withheld 1,234, collect dest net 120,938 /
  withheld 1,222 -- the tf pipes survive close and re-init
  unchanged.

## Limits

- The unsigned-user cases use a fee payer different from the
  user account: when fee payer and user are the same key,
  LiteSVM merges the fee-payer signature onto the user meta
  and the unsigned close/extend succeed instead of failing
  3010 (measured during construction; the packet pins the
  separated-payer form, matching 3rd #1/#27).
- The cashback-claim-after-close case runs in plain-quote
  mode (no transfer-fee override, SPL buyback) because
  claim_cashback cannot run on the transfer-fee-overridden
  quote mint at all (Anchor 2021 ConstraintTokenTokenProgram,
  pinned in 3rd #67).
- Only the quote mint carries a transfer fee in the tf100
  case; the claim mint runs at 0 bps here (claim-mint tf
  was pinned in 3rd #21/#67).
- All amounts are LiteSVM replays of signed receipts, not
  mainnet transactions; error sites are per-image (original
  and rebuilt sources differ in line numbers) and are
  recorded per image, never compared across images.

## Reproduce

```
python3 verify.py
```

Expected output:

```
PASS: 20 cases, 204 receipts, 21 parts, per-image expectations hold (0 divergent cases)
```

Made via @slopdotcash
