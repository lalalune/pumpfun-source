# GlobalConfig account validation on the split x boost x tf chain (true 3 hops)

## Problem

Packet 3rd #83 pinned the validation surface of the fee-table
account on this chain: wrong discriminator 3002, wrong owner
3007, zero lamports 3012, check order 3012 > 3007 > 3002, key
swaps all 3007, full leg parity, no downstream leak. This packet
pins the same surface for the GlobalConfig account itself (the
949-byte account at `ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw`):
does a wrong discriminator, a wrong owner, zero lamports, or a
swapped account key gate the trade, setter, sweep, boost, and
claim legs the same way -- and is the gate code the same?

Route: the split x boost x tf chain at TRUE 3 hops (the
`three_amm`-only route 3rd #63/#64 pinned; no g4/g5 hop group is
appended, final output U3). The quote mint carries a 100 bps
transfer-fee config and the split legs route the buyback through
the Token-2022 ATA, as in #64.

## Cases

48 cases, 162 receipts (54 steps x 3 images: original, control
#424, candidate #427), 17 parts of 10 receipts (16x10 + 2).

- Family A, anchors (4): mhbuy3 / mhsell3 in 10^9, single-leg
  v2 buy2 / sell2 in 10^10, all at bps 100.
- Family D, discriminator (6): disc zeroed, disc first byte
  flipped, disc replaced with the pool discriminator, disc
  replaced with the fee-table discriminator; buy3, sell3, buy2.
- Family T, whole-data swaps (3): GlobalConfig data replaced
  with fee-table data, pool data, or zeros (length kept at 949).
- Family O, owner (7): owner left at the pump program
  (control), or changed to SPL Token, Token-2022, System
  Program, the default pubkey, or the Fees program; buy3 and
  sell3.
- Family L, lamports (5): 0, 1, and 2,000,000 (below
  rent-exempt for a 949-byte account); buy3, sell3, buy2.
- Family X, combined faults / check order (5): disc+owner,
  lamports+disc, lamports+owner, all three, disc-flip+owner
  (System) on a sell.
- Family K, instruction account-key swaps (6): GlobalConfig
  key replaced with the fee-table key, the pool key, a fresh
  key with no account, or the user quote account; buy3, sell3,
  buy2.
- Family P, leg parity (5): disc-zero legacy buy / legacy
  sell, owner-Token legacy buy, disc-zero boost (vq patched to
  10^9), disc-zero Token-2022 sweep (single leg).
- Family W, downstream after a validation failure (4):
  failed buy then sweep + creator sweep + collect; failed buy
  then boost (vq 10^9); failed buy then token claim (seeded
  UVA, claim bps 100); failed buy then cashback claim
  (plain-quote mode, seeded earned 5,475).
- Family S, setters (3): buyback-config setter with a valid
  config (control), the same setter with disc zeroed, and the
  disable setter with disc zeroed.

## Result

All 48 cases agree on all three images (0 divergent cases).
Every failure step has 0 events (no ghost events -- validation
fails before any hop event is emitted) and rolls back every
watched account except the fee payer (fee 5,000).

Anchors (bps 100). mhbuy3 in 10^9: user quote -10^9, tail
output U3 5,262,910,281,902, Token-2022 buyback 4,515,471,
withheld vq1 10,000,000 and buyback 45,611, 3 hop events
(disc 67f4521f2cf57777, len 508 each). mhsell3 in 10^9: user
quote +178,541, withheld user quote 1,804 and buyback 9, 3 hop
events (disc 3e2f370aa503dc2a, len 449 each). buy2 in 10^10:
user base +10^10, user quote -1,866,375, buyback 8,401.
sell2 in 10^10: user quote +1,784,093, buyback 8,401.

Discriminator: every disc fault fails **InvalidAccountData**
(zeroed, flipped, pool disc, fee disc, whole-data fee/pool/
zero swaps alike), on every leg tried (multi-hop buy/sell,
single-leg v2 buy, legacy buy/sell, boost, Token-2022 sweep,
both setters). This is NOT the fee-table account's 3002: the
two accounts are validated by different code paths --
GlobalConfig is read through Anchor account deserialization,
which raises InvalidAccountData on a discriminator mismatch,
while the fee-table account is read through a custom parser
that raises 3002.

Owner: any owner other than the pump program fails **3007**
(SPL Token, Token-2022, System Program, default pubkey, Fees
program all alike), on buy, sell, and legacy buy. The control
case (owner left at the pump program) reproduces the anchor
outputs exactly.

Lamports: 0 fails **3012** (buy, sell, single-leg v2 buy
alike). 1 lamport and 2,000,000 lamports both succeed with
anchor-identical outputs, so no rent-exempt minimum is
checked -- existence only, exactly as #83 found for the
fee-table account.

Check order: **3012 > 3007 > InvalidAccountData** -- lamports
beats owner beats discriminator. disc+owner fails 3007,
lamports+disc fails 3012, lamports+owner fails 3012, all three
fail 3012, disc-flip+owner-System on a sell fails 3007. This
is the same order shape as #83's 3012 > 3007 > 3002, with
InvalidAccountData in place of 3002.

Key swaps: the fee-table key fails 3007 (its owner is the
Fees program, so the owner gate fires first), the user quote
account fails 3007 (its owner is SPL Token), the pool key
fails InvalidAccountData (its owner IS the pump program, so
the owner gate passes and deserialization fails), and a fresh
key with no account fails 3012. The sell and single-leg v2
buy with the fee-table key also fail 3007. Note the one
difference from #83, where every key swap failed 3007: here
the pool and fresh swaps expose the deeper gates because
their owners / existence differ.

Downstream after a validation failure: legs that read
GlobalConfig fail alike (both Token-2022 sweeps fail
InvalidAccountData, boost fails InvalidAccountData), while
legs that never read it keep working -- collect still
succeeds, but as a silent 0-payout no-op since the failed
trade and failed sweeps never filled any bucket; the token
claim pays the full seeded amount (gross 3,334,551, net
3,301,205, withheld 33,346, event disc 4facf631cd5bcee8 len
104); the cashback claim pays the full seeded 5,475 (event
disc e2d6f62107f293e5 len 72). A failed trade therefore
leaves no downstream leak and no partial payout.

Setters: the buyback-config control setter succeeds silently
(0 events; bps 5000 and the empty recipient list rewrite the
fixture values). With disc zeroed, the buyback-config setter
and the disable setter both fail InvalidAccountData.

## Limits

- The cashback-claim downstream case uses plain-quote mode:
  as #67 found, a cashback claim on the transfer-fee-override
  quote mint fails with Anchor's ConstraintTokenTokenProgram,
  so the claim family is measured on the plain mint with the
  no-withheld-authority guard.
- Boost is measured here only as a failure leg (disc zeroed);
  boost success under a valid config is pinned in #34/#64
  (burn 5,255,205,915,165 at vq 10^9 on this chain).
- No success case for the disable setter is included; the
  setter control is the buyback-config setter only.
- Error sites (source lines) are pinned per image in
  report.json.gz and are never compared across images, since
  the original and rebuilt sources differ in line numbers.
- Fixture values are the #64 chain fixture: GlobalConfig
  949 bytes, pool virtual_quote_reserves -125,882,
  protocol_fees 2,488, creator_fees 123,394, lp_supply
  4,194,352,106,721.

Reproduce: `python3 verify.py` from this directory. The
verifier re-checks every receipt signature, every per-image
expected delta / withheld / pool / UVA / GlobalConfig state,
every event, every error code and rollback, GVOL invariance,
and control == candidate on every case.

Made via @slopdotcash
