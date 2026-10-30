# research: split x boost x tf UVA lifecycle chains at TRUE 5 hops

## Problem

Packet #68 pinned the user volume accumulator (UVA) lifecycle on a
TRUE 3-hop split chain, and #125 pinned close stranding and
buy-created UVA at depth 5. This packet extends every #68
measurement to a TRUE 5-hop route (main -> POOL2 -> P3 -> P4 ->
P5, final output U5): does claim-then-close still refund the full
balance while the unclaimed tokens exist only in the CloseEvent,
do post-close claim/sync/close/cashback all still fail 3012, does
re-init still build a fresh 137-byte zero account the chain then
uses normally, do the extend chains (90 -> 137 field-preserving,
137/138 no-ops, 50 -> 137 truncated-layout rewrite,
close-then-extend 2004, unsigned 3010, read-only 2000, second
extend no-op) still hold, do the close authorization gates (other
signer 2006, unsigned user 3010) still hold, and does the
lifecycle still move nothing on the chain -- now checked against
uninterrupted control walks for the plain buy, the buy-boost
walk, a fee-table walk, and tf5000 / tf0 / plain-quote walks?

Route verification: the builder's `build_route` calls `three_amm`
and then appends the g4 and g5 hop groups, so the buy runs
main -> P2 -> P3 -> P4 -> P5 and the sell runs the reverse;
successful swaps emit 5 hop events. The name, this README, and the
PR title all say 5 hops because the route really is 5 hops
(contrast the earlier 3-hop-named packet whose route was actually 4
hops). Each hop pool carries proper pool data (its own bump,
pool-authority creator, base mint, and vaults), not raw main-pool
bytes, and each hop boost uses an SPL-derived ATA for its hop quote
mint (BA4S for BASE3, BA5S for BASE4). The seeded UVA is
(needs_claim 1, unclaimed 111, claimed 222, volume 333444, last 20,
has_total_claimed_tokens 1, cashback_earned 555,
total_cashback_claimed 666) at 10^9 lamports unless a case says
otherwise; the 500-seed variant is (1, 500, 700, 20, 10, 1, 55, 13).
The global volume accumulator is seeded (start 20, end 49,
seconds_in_a_day 1, then 30 x 1000 supply and 30 x 100 volume).
Quote transfer fee is 100 bps unless stated; the claim mint IMINT
(bytes([226]) * 32, Token-2022) carries its own per-case
transfer-fee config.

## Cases

37 cases, 318 receipts, 32 parts (31x10 + 8), across original,
control and candidate images.

- A (12): claim-close-reinit chains and gates: seeded
  tclaim-close-reinit-tclaim-sweep-collect; close of the
  500-unclaimed seed alone; tclaim-close then tclaim / sync /
  second close / cashback-claim (plain-quote mode); close by
  another signer; close with an unsigned user; init on a seeded
  account; init on an absent account; init-then-claim on an
  absent account; init-close-init.
- B (8): extend chains: 90-byte seed extend-then-claim-then-close
  (1,517,280 lamports); extend at target 137 then claim then
  close; extend above target 138 then close; 50-byte seed
  extend-then-claim-then-close; close-extend-init-extend;
  extend-unsigned then signed extend; extend-read-only then
  signed extend; extend twice.
- C (10): lifecycle inside 5-hop walks, each against an
  uninterrupted control walk where one exists: buy-close-reinit-
  buy-sweep-collect; buy-buy control; buy-boost-close-reinit-
  buy-boost (main vq patched to 10^9); buy-boost-buy-boost
  control; buy-close-buy; buy against a seeded UVA (invariance);
  buy-then-claim against a seeded UVA; close-buy-claim;
  fee-table buy-close-reinit-buy; fee-table buy-buy control.
- D (7): tf / plain variants: tf5000 buy-close-reinit-buy;
  tf5000 buy-buy control; tf0 buy-close-reinit-buy; tf0 buy-buy
  control; close then cashback-claim in plain-quote mode;
  plain-quote buy-close-reinit-buy; plain-quote buy-buy control.

## Result

0 divergent cases: original, control and candidate agree on every
case. All numbers below are measured on all three images.

- Anchors at depth 5: 5-hop buy tail U5 5,207,955,235,891 with 5
  hop events (508 bytes each); buy-then-boost burn
  5,254,679,949,141. The fee-table first buy tail is
  5,252,440,110,816; tf5000 first buy tail 2,668,075,748,732;
  tf0 and plain first buy tails 5,259,040,470,738.
- Claim-then-close refunds the full balance and pays nothing
  else. After a seeded token claim (3,334,551 = 111 + 333444 *
  1000 / 100, total_claimed 3,334,773), close returns
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
  cashback claim ALL fail 3012 AccountNotInitialized, each
  costing only the 5,000 fee with full rollback of everything
  else. The cashback case runs in plain-quote mode (no
  transfer-fee override, `no_ww` guard), because
  claim_cashback cannot run on the transfer-fee-overridden
  quote mint at all (Anchor 2021, pinned in #67/#125).
- Re-init after a close creates a FRESH 137-byte account
  (1,844,400 lamports rent + 5,000 fee = payer -1,849,400,
  InitEvent disc 86240d48e86582d8, len 80) with all 9 fields
  zero. The following token claim is a zero claim (0 events,
  last 0 -> 21), and the following sweep/collect drain the
  full creator bucket 123,394 (sweep net 122,160, collect dest
  net 120,938).
- NEW: init on an already-seeded account succeeds as a 1-event
  fee-only step (payer -5,000, all 9 fields byte-identical) --
  init is not an error on an existing account, and it charges
  no rent. Init on an absent account builds the fresh
  137-byte zero account at -1,849,400, and init-close-init
  runs close (+1,839,400) then a second fresh init
  (-1,849,400).
- Extend 90 -> 137 preserves every field byte-for-byte and
  tops the rent up exactly: payer -332,120 (47 * 6,960 top-up
  + 5,000 fee), fields (needs 1, unclaimed 500, claimed 700,
  volume 20, last 10, has 1, cashback_earned 55,
  total_cashback_claimed 13) untouched. The following claim
  pays only the 500 unclaimed (claimed 700 -> 1200, volume 20
  untouched, last 21): the seed's last 10 is before the GVA
  start 20, so the volume conversion branch stays blocked --
  the same pre-start gate pinned in #125. The close after it
  refunds 1,839,400.
- Extend at target (137) and above target (138) are silent
  no-ops: 0 events, payer -5,000 only, fields untouched; the
  following claim and close run identically (claim 3,334,551,
  close +999,995,000).
- Extend 50 -> 137 rewrites the truncated field layout:
  payer -610,520 (87 * 6,960 + 5,000 fee), balance
  10^9 -> 1,000,605,520, fields become (needs 1, unclaimed
  500, claimed 188 -- the low byte of 700 -- volume 0,
  last 0, has 0, cashback_earned 0, total_cashback_claimed 0).
  The following claim pays 500 (claimed 188 -> 688), and the
  close after it refunds 1,000,600,520.
- Close after close-then-extend fails 2004 ConstraintOwner;
  re-init after it succeeds, and a further extend on the
  fresh account is a silent no-op.
- Close authorization binds to the PDA seeds, not the stored
  user field: close by another signer fails 2006
  ConstraintSeeds, and close with an unsigned user fails 3010
  AccountNotSigner. Both cost only the 5,000 fee (paid by the
  outsider fee payer) with full rollback.
- Extend authorization mirrors it: extend with an unsigned
  user fails 3010 AccountNotSigner, extend with a read-only
  target fails 2000 ConstraintMut; the signed extend right
  after each failure succeeds (-332,120), and extend twice
  makes the second extend a silent no-op (0 events, -5,000).
- The lifecycle moves nothing on the chain at depth 5.
  Buy-close-reinit-buy reproduces the uninterrupted second
  buy exactly (tail 4,918,089,082,874, identical token deltas),
  and sweep/collect after it drain the full 123,394.
  Buy-boost-close-reinit-buy-boost reproduces the
  uninterrupted buy-boost-buy-boost chain exactly: first burn
  5,254,679,949,141, second buy tail 4,804,996,083,991,
  second burn 5,093,171,141,582. The fee-table second buy is
  4,957,670,972,204 with close + re-init between the buys,
  exactly as in the uninterrupted fee-table control.
- A buy after a close re-creates the empty UVA at rent cost
  (buy step payer -1,849,400 instead of -5,000) with the
  uninterrupted tail: second-buy tail 4,918,089,082,874 in
  the buy-close-buy walk, anchor tail 5,207,955,235,891 in
  the close-buy walk, and the following claim is a 0-event
  zero claim (last 0 -> 21).
- A 5-hop buy leaves a seeded UVA byte-identical (volume
  333444 untouched: the multi-hop legs do not feed the volume
  accumulator at depth 5 either), and a buy-then-claim against
  a seeded UVA still pays the full 3,334,551.
- tf / plain lifecycle neutrality holds the same way:
  tf5000 lifecycle second buy 2,590,950,921,881, tf0
  lifecycle second buy 4,963,540,456,839, plain-quote
  lifecycle second buy 4,963,540,456,839 -- each exactly the
  uninterrupted control second buy at that fee setting.

## Limits

- All results are measured on the three program images (original,
  control, candidate) in the litesvm harness with the fixture pools
  and fee table; they are not a claim about any other program
  version or live state.
- The unsigned-user cases use a fee payer different from the
  user account: when fee payer and user are the same key,
  LiteSVM merges the fee-payer signature onto the user meta
  and the unsigned close/extend succeed instead of failing
  3010 (measured during construction in #68; the packet pins
  the separated-payer form, matching #68).
- The plain-quote cases use the `no_ww` guard (no
  withdraw-withheld authority patch on the quote mint): the
  patch assumes the transfer-fee-overridden mint layout, and
  applying it to the un-overridden mint broke the plain buy
  leg with InvalidAccountData during construction -- a harness
  artifact, not program behaviour, so the plain cases run
  without the patch.
- The cashback-claim-after-close case runs in plain-quote
  mode (no transfer-fee override, SPL buyback) because
  claim_cashback cannot run on the transfer-fee-overridden
  quote mint at all (Anchor 2021 ConstraintTokenTokenProgram,
  pinned in #67/#125).
- Only the quote mint carries a transfer fee in the tf cases;
  the claim mint runs at 0 bps here (claim-mint tf was pinned
  in #21/#67/#125).
- Error-site lines live in each receipt row's `error_sites` field,
  never in `observed`, because original/rebuild line numbers differ.
- No source change is proposed.

Made via @slopdotcash
