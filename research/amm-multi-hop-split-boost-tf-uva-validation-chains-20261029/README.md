# UserVolumeAccumulator account validation on the split x boost x tf chain (true 3 hops)

## Problem

Packets 3rd #83, #84, and #85 pinned the validation surface of
the fee-table account (disc wrong 3002, owner wrong 3007, zero
lamports 3012, check order 3012 > 3007 > 3002, key swaps all
3007), of the GlobalConfig account (disc wrong
InvalidAccountData, owner wrong 3007, zero lamports 3012, check
order 3012 > 3007 > InvalidAccountData, key swaps split by
owner/existence), and of the route pools (disc wrong
InvalidAccountData, owner wrong 6027 on multi-hop but 3007
elsewhere, zero lamports 6027 on multi-hop but 3012 on v2, a
single 6027 gate collapsing the check order on multi-hop, key
swaps split into 6027 for non-pool keys and 6008 for other
pool keys) on this chain. This packet pins the same surface
for the account the claim, sync, extend, and close legs read
themselves -- the UserVolumeAccumulator (UVA): does a wrong
discriminator, a wrong owner, zero lamports, a swapped
account key, or a truncated/extended length gate the
token-claim, cashback-claim, sync, extend, close, and trade
legs the same way -- and is the gate code the same?

Route: the split x boost x tf chain at TRUE 3 hops (the
`three_amm`-only route 3rd #63/#64 pinned; no g4/g5 hop group is
appended, final output U3). The quote mint carries a 100 bps
transfer-fee config and the split legs route the buyback through
the Token-2022 ATA, as in #64.

## Cases

60 cases, 198 receipts (66 steps x 3 images: original, control
#424, candidate #427), 20 parts of 10 receipts (19x10 + 8).

- Family A, anchors (8): mhbuy3 / mhsell3 in 10^9 at bps 100;
  token claim on the seeded UVA (claim bps 100); cashback
  claim in plain-quote mode (seeded earned 5,475, no
  withheld-authority guard); sync with a firing reset
  (seed last_update 10, before the GlobalVolumeAccumulator
  start 20) and a no-op sync (seed last_update 20);
  extend of a 90-byte UVA to 137; close of the seeded UVA.
- Family D, discriminator (11): token-claim disc zeroed,
  flipped, replaced with the pool discriminator, replaced
  with the GlobalConfig discriminator, replaced with the
  fee-table discriminator; sync / extend / close / cashback
  claim with disc zeroed; multi-hop buy and multi-hop sell
  with disc zeroed.
- Family T, whole-data swaps (4): token-claim UVA data
  replaced with pool data, GlobalConfig data, fee-table
  data, or zeros (length kept at 137).
- Family O, owner (7): token-claim owner changed to SPL
  Token, Token-2022, System Program, the default pubkey, or
  the Fees program; sync and extend with the SPL Token
  owner.
- Family L, lamports (6): token claim at 0, 1, and
  1,000,000 lamports (below the 1,844,400 rent-exempt
  minimum for a 137-byte account); sync, extend, and close
  at 0 lamports.
- Family X, combined faults / check order (4):
  disc+owner, lamports+disc, lamports+owner, and all three
  combined on a token claim.
- Family K, instruction account-key swaps (7): the
  token-claim UVA slot pointed at the GlobalConfig key, the
  pool key, the fee-table key, a fresh key with no account,
  or another user's valid UVA; the sync UVA slot pointed at
  the pool key; the extend slot pointed at the GlobalConfig
  key.
- Family G, length (9): token claim at 0, 1, 89, 90, 100,
  136, and 200 bytes; extend of a 50-byte and an 89-byte
  UVA to 137.
- Family W, downstream after a validation failure (4):
  failed token claim then multi-hop buy; failed token claim
  then main-pool Token-2022 protocol sweep + creator sweep
  + collect; failed token claim then boost (vq patched to
  10^9); multi-hop buy then token claim, both against a
  discriminator-zeroed UVA.

## Result

All 60 cases agree on all three images (0 divergent cases).
Every failure step rolls back every watched account except the
fee payer (fee 5,000).

Anchors (bps 100). mhbuy3 in 10^9: user quote -10^9, tail
output U3 5,262,910,281,902, Token-2022 buyback 4,515,471,
withheld vq1 10,000,000 and buyback 45,611, 3 hop events
(disc 67f4521f2cf57777, len 508 each); the trade creates the
UVA (1,844,400 lamports, 137 bytes, payer as user, all fields
zero), so the payer delta is -1,849,400. mhsell3 in 10^9:
user quote +178,541, withheld user quote 1,804 and buyback
9, 3 hop events (disc 3e2f370aa503dc2a, len 449 each), and
the same UVA creation (-1,849,400). Token claim on the
seeded UVA (claim bps 100): gross 3,334,551, net 3,301,205,
withheld 33,346, event disc 4facf631cd5bcee8 len 104
(ts 21, total_claimed 3,334,773, current_sol_volume 0).
Cashback claim in plain-quote mode: the full seeded 5,475,
event disc e2d6f62107f293e5 len 72 (ts 1234567890,
total_claimed 5,475, total_earned 5,475), token fields
untouched. Sync with last_update 10 fires the pre-start
reset: claimed 222 -> 0, has 1 -> 0, event disc
c57aa77c74515bff len 64 (before 222, after 0, ts 10); sync
with last_update 20 is a no-op (0 events, no change).
Extend 90 -> 137 costs 327,120 rent (47 x 6960) plus the
5,000 fee with all fields preserved. Close pays 999,995,000
lamports (10^9 - 5,000 fee), removes the account, emits the
80-byte CloseEvent (disc 929fbdac925838f4, unc 111,
claimed 222, vol 333444, last 20), and pays no tokens.

Discriminator: every disc fault on the Anchor legs fails
**3002 AccountDiscriminatorMismatch** -- zeroed, flipped,
pool disc, GlobalConfig disc, fee-table disc, and the
whole-data pool / GlobalConfig / fee-table / zero swaps
alike -- on token claim, cashback claim, sync, close,
multi-hop buy, and multi-hop sell. The UVA discriminator
gate is the fee-table account's custom 3002, not the
GlobalConfig/pool InvalidAccountData: the UVA is read
through the same Anchor account struct on all these legs.

Owner: the Anchor legs fail **3007
AccountOwnedByWrongProgram** for every non-program owner
tried (SPL Token, Token-2022, System Program, default
pubkey, Fees program), on token claim and on sync alike.

Lamports: 0 fails **3012 AccountNotInitialized** on token
claim, sync, and close (the 0-lamport account vanishes
from the VM). 1 lamport and 1,000,000 lamports both
succeed with anchor-identical payouts (gross 3,334,551,
net 3,301,205, withheld 33,346), so no rent-exempt minimum
is checked -- existence only, exactly as #83/#84/#85 found
for the fee-table, GlobalConfig, and pool accounts.

Check order: on the Anchor legs the order is **lamports >
owner > disc**, identical to #83 and #84. Disc+owner fails
3007 (owner beats disc); lamports+disc, lamports+owner,
and all three combined fail 3012 (lamports beats both).
Unlike #85's pools, where multi-hop collapsed the order
into a single 6027 gate, the UVA keeps the three codes
distinguishable.

Key swaps: the code splits by what the swapped key points
at. The pool key and the GlobalConfig key fail **3002**
(program-owned, wrong discriminator); the fee-table key
fails **3007** (Fees-owned, so the owner gate fires first);
a fresh key with no account fails **3012**; another
user's valid UVA fails **2006 ConstraintSeeds** (the PDA
seeds do not match the payer). Sync with the pool key in
the UVA slot fails 3002, the same as the claim legs.

Length: 0 and 1 bytes fail **3001
AccountDiscriminatorNotFound**; 89 bytes fails **3003
AccountDidNotDeserialize**; 90, 100, 136, and 200 bytes
all succeed. The UVA deserialization floor is exactly 90
bytes with no upper bound check -- trailing bytes are
ignored, and a 90-byte claim leaves the account at 90
bytes (claim does not resize).

The trade legs read the UVA account. A multi-hop buy and
a multi-hop sell both fail **3002** on a
discriminator-zeroed UVA, and a buy followed by a token
claim against the same broken UVA fails twice: the trade
does not heal or recreate a broken UVA, it fails outright.
This sharpens #73's finding that split trades never move
UVA fields -- they do not move them, but they do
deserialize them, so a broken UVA blocks the trade.

Extend is a different validation path. It does not use the
Anchor account deserialization: a discriminator-zeroed
UVA fails **6027 AccountTypeNotSupported** (thrown in
extend_account.rs:114 -- the discriminator selects the
account type and a zeroed disc matches none); a
Token-owned UVA and a 0-lamport UVA both fail **2004
ConstraintOwner** (a vanished account fails the owner
constraint, not the 3012 initialized check); and pointing
the extend slot at the GlobalConfig key succeeds as a
no-op (a 949-byte GlobalConfig is already at its type
target: fee 5,000 only, 0 events). Extend sizes are exact:
90 -> 137 costs 327,120 rent, 89 -> 137 costs 334,080
rent, both with all fields preserved; 50 -> 137 costs
605,520 rent and rewrites the account, preserving only
the fields inside the first 50 bytes (needs, unclaimed,
claimed) and zeroing volume, last_update, has, earned,
and cashback_claimed. All three sizes add the 5,000 fee.

Downstream after a validation failure: legs that read
other accounts keep working at fixture values. After a
failed token claim, the main-pool Token-2022 protocol
sweep discharges 2,488 (2,463 net, withheld 25), the
creator sweep discharges 123,394 (122,160 net, withheld
1,234), collect pays 122,160 (120,938 net, withheld
1,222), and boost burns 5,338,379,201,831, equal to the
#64 tf100 anchor because the failed claim left the boost
window (vq 10^9 + accrued buckets) untouched. A failed
UVA validation therefore leaks nothing downstream.

## Limits

- The cashback-claim cases use plain-quote mode with the
  no-withheld-authority guard: as #67 found, a cashback
  claim on the transfer-fee-override quote mint fails with
  Anchor's ConstraintTokenTokenProgram, so the claim
  family is measured on the plain mint.
- The sell direction is probed for the discriminator fault
  only; the remaining UVA faults are measured on the buy
  leg and on the claim / sync / close / extend legs, which
  share the same Anchor account struct as the sell leg.
- Error sites (source lines) are pinned per image in
  report.json.gz and are never compared across images, since
  the original and rebuilt sources differ in line numbers.
- Fixture values are the #64 chain fixture: pool
  virtual_quote_reserves -125,882, protocol_fees 2,488,
  creator_fees 123,394, lp_supply 4,194,352,106,721; UVA
  seed (needs 1, unclaimed 111, claimed 222, volume
  333444, last_update 20, has 1, earned 555, cashback
  claimed 666); cashback seed earned 5,475; the other
  user's UVA is seeded with the outsider key as user.
- No success case for set_coin_creator or for a UVA-keyed
  deposit/withdraw is included here; the set control is
  pinned in #70 and the UVA lifecycle (init/close/extend)
  in #68.

Reproduce: `python3 verify.py` from this directory. The
verifier re-checks every receipt signature, every per-image
expected delta / withheld / pool / UVA / GlobalConfig state,
every event, every error code and rollback, GVOL invariance,
and control == candidate on every case.

Made via @slopdotcash
