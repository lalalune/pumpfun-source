# research: UVA validation on the split x boost x tf chain at TRUE 5 hops

## Problem

Packet #86 pinned the UserVolumeAccumulator account's own
validation on the TRUE 3-hop split chain: a wrong discriminator
fails 3002, a wrong owner fails 3007, lamports 0 fails 3012
while lamports 1 and 1,000,000 succeed anchor-identically (no
rent-exempt check), check order is 3012 > 3007 > 3002, key swaps
split by the swapped account's owner/existence/seeds (another
user's valid UVA fails 2006 ConstraintSeeds), the length floor
is exactly 90 bytes with no upper bound, extend runs on its own
validation path (disc-zero 6027, wrong owner or 0 lamports
2004), and trade legs deserialize the UVA, so a broken UVA
blocks the trade outright. This packet asks whether every one
of those holds at depth 5, on the split x boost x tf chain
(three_amm + g4 + g5, final output U5 — a TRUE 5-hop route, not
the #61 shape that appended g4 only and was actually 4 hops),
and adds the ghost counts in both trade directions at depth 5
for each fault class, plus tf variants of the
discriminator/owner/swap faults.

## Route and anchors

The fixture route is main -> POOL2 -> P3 -> P4 -> P5, final output
U5. Successful 5-hop swaps carry exactly 5 hop events in both
directions. Anchors (bps 100 tf, UVA unmutated):

- Buy tail 5,207,955,235,891, buyback leg 4,515,471; the trade
  creates the UVA (1,844,400 lamports, 137 bytes, payer as user,
  all fields zero), so the payer delta is -1,849,400.
- Sell payout 178,541, buyback leg 837; same UVA creation.
- Token claim on the seeded UVA (claim bps 100): gross
  3,334,551, net 3,301,205, withheld 33,346, event disc
  4facf631cd5bcee8 len 104 (ts 21, total_claimed 3,334,773,
  current_sol_volume 0).
- Cashback claim in plain-quote mode (seeded earned 5,475,
  no-withheld-authority guard): the full 5,475, event disc
  e2d6f62107f293e5 len 72 (ts 1234567890, total_claimed 5,475,
  total_earned 5,475), token fields untouched.
- Sync with last_update 10 fires the pre-start reset: claimed
  222 -> 0, has 1 -> 0, event disc c57aa77c74515bff len 64
  (before 222, after 0, ts 10); sync with last_update 20 is a
  no-op (0 events, no change).
- Extend of a 90-byte UVA to 137 costs 327,120 rent (47 x 6960)
  plus the 5,000 fee (payer delta -332,120) with all fields
  preserved.
- Close pays 999,995,000 lamports (10^9 - 5,000 fee), removes
  the account, emits the 80-byte CloseEvent (disc
  929fbdac925838f4, unc 111, claimed 222, vol 333444, last 20),
  and pays no tokens.

## Cases (64 cases, 213 receipts, 22 parts of 10 + 3)

- **A (8 anchors):** buy, sell, token claim, cashback claim,
  sync firing, sync no-op, extend 90 -> 137, close — the values
  above.
- **D (11):** discriminator corruption — zeroed, flipped byte,
  pool discriminator, GlobalConfig discriminator, fee-table
  discriminator — on the token claim; disc-zeroed on sync,
  extend, close, cashback claim, 5-hop buy and 5-hop sell.
  All fail 3002 with 0 events, except extend, which fails
  6027 (its own account-type path).
- **T (4):** whole-data replacement at the kept length of 137
  bytes — pool data, GlobalConfig data, fee-table data,
  zeroed data — on the token claim. All fail 3002 with 0
  events.
- **O (7):** owner faults — SPL token, Token-2022, system,
  default, Fees program — on the token claim, all fail 3007
  with 0 events; SPL token owner on sync (3007) and on extend
  (2004 ConstraintOwner).
- **L (6):** lamports 0 fails 3012 with 0 events on token
  claim, sync and close, and 2004 on extend. Lamports 1 and
  1,000,000 (below the 1,844,400 rent-exempt minimum for a
  137-byte account) pay the anchor claim identically: no
  rent-exempt check fires.
- **X (4):** check order on the token claim is 3012 > 3007 >
  3002: disc+owner fails 3007, lamports+disc, lamports+owner
  and all three combined fail 3012.
- **K (7):** instruction account-key swaps. Token claim with
  the UVA slot pointed at the GlobalConfig key or the pool
  key fails 3002 (program-owned, wrong discriminator); at
  the fee-table key fails 3007 (Fees-owned, so the owner
  gate fires first); at a truly absent key (bytes [123]*32)
  fails 3012; at another user's valid UVA fails 2006
  ConstraintSeeds (the PDA seeds do not match the payer).
  Sync with the pool key fails 3002. Extend pointed at the
  GlobalConfig key succeeds as a no-op (fee 5,000 only, 0
  events — a 949-byte GlobalConfig is already at its type
  target).
- **G (9):** length gates. Token claim at 0 and 1 bytes fails
  3001 AccountDiscriminatorNotFound; at 89 bytes fails 3003
  AccountDidNotDeserialize; at 90, 100, 136 and 200 bytes
  succeeds with the anchor claim and no resize (a 90-byte
  claim leaves the account at 90 bytes, a 200-byte claim
  leaves it at 200 bytes). Extend of a 50-byte UVA to 137
  costs 605,520 rent plus the 5,000 fee and rewrites the
  account, preserving only the fields inside the first 50
  bytes (needs, unclaimed, claimed) and zeroing volume,
  last_update, has, earned and cashback_claimed; extend of
  an 89-byte UVA costs 334,080 rent plus the fee with all
  fields preserved.
- **W (4):** downstream legs after a UVA validation failure.
  A failed token claim then a 5-hop buy fails 3002 again:
  the trade does not heal or recreate a broken UVA, it
  fails outright — and with 0 events in both directions,
  unlike pool faults, which emit position ghosts: the UVA
  check fires before any hop executes. After a failed
  claim, the main-pool Token-2022 protocol sweep discharges
  2,488 (2,463 net, withheld 25), the creator sweep
  discharges 123,394 (122,160 net, withheld 1,234), collect
  pays 122,160 (120,938 net, withheld 1,222), and the
  patched-window boost burns 5,338,379,201,831, equal to
  the fresh-window value: a failed UVA validation leaks
  nothing downstream.
- **F (4):** tf variants — disc-zero 5-hop buy at tf5000 and
  tf0 fails 3002; owner-token token claim at tf5000 fails
  3007; fee-table-key swap token claim at tf0 fails 3007:
  validation is tf-neutral.

## Result

Every #86 finding reproduces exactly at depth 5, with one
depth-5 observation added: every UVA validation failure on a
trade leg carries 0 events in both directions. The UVA is
deserialized before any hop executes, so a broken UVA blocks
the whole 5-hop trade without emitting a single hop event —
in contrast to pool faults, where the ghost count pins the
failing hop's position (#139). The UVA keeps its three
Anchor codes distinguishable on every leg (unlike #85/#139's
pools, where multi-hop collapsed the order into a single
6027 gate), and extend keeps its own 6027/2004 path.

Across the original, control, and candidate images, all 64 cases
agree: 0 divergent cases.

## Limits

- UVA mutations (`uva_valid`, `uva_len`, `uva_swap`) and
  mid-case `cpatch` resets are harness fixture edits recorded
  with empty transactions, not on-chain instructions; they
  exist to place the account in the corrupted state the
  program then validates.
- The cashback-claim cases use plain-quote mode with the
  no-withheld-authority guard: as #67 found, a cashback
  claim on the transfer-fee-override quote mint fails with
  Anchor's ConstraintTokenTokenProgram, so the claim family
  is measured on the plain mint.
- Results are LiteSVM executions of the original, control, and
  candidate program images on this fixture; they pin the
  observed gate codes, ghost counts, tails, and rollback
  behaviour, and make no claim about any other account shape
  or program path.
- No source change is proposed.

## Files

- `README.md` — this file.
- `producer.py` — the packet builder (case list, harness edits,
  receipt writer).
- `verify.py` — independent re-verification: signatures, deltas,
  withheld, lamports, events, error codes, rollback, fixture
  pool/config/UVA/GVA/mint fields, account lengths, and the
  headline pins above. Run it from this directory.
- `MANIFEST.json` — sha256 and byte counts for every packet file.
- `runtime/report.json.gz` — per-case, per-image summaries.
- `runtime/raw-transactions-part01..22.jsonl.gz` — the 213
  receipts, 10 per part (last part 3).

Verify: `python3 verify.py` prints
`PASS: 64 cases, 213 receipts, 22 parts, ...` (full line in the
script).

Made via @slopdotcash
