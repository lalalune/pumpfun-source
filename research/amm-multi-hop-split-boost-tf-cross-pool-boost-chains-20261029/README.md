# Multi-hop split x boost x tf: cross-pool boost authority chains

## Problem

On the true-3-hop split x boost x transfer-fee chain (three pools, final
output U3), this packet measures boost on the hop pools P2 and P3 against
the main pool: each hop pool has its own boost vault, its own window and
its own burn, but the boost authority is a single GlobalConfig field.
The questions are whether a hop-pool boost is window-open at all, what it
burns, what closes or fails when its vault drains, whether authority
rotates per pool or globally, which Anchor gates fire on a wrong boost
ATA or wrong token program, and how a hop-pool boost moves the chain
buy/sell legs and the sweep/collect legs that follow it.

## Cases

50 cases, 369 receipts, 37 parts, bps 100 unless noted. Every case runs
on original, control and candidate images; all three agree everywhere
(0 divergent cases). Spends are 10^9 quote unless noted; `vq` patches
set a pool's virtual_quote_reserves i128 field to 10^9 to open its
boost window (the fixture window sum is 0).

- **A anchors (5).** Multi-hop buy tail 5,262,910,281,902; multi-hop sell
  payout 178,541; main boost burn 5,338,379,201,831 (vq patch + request
  10^9, vault 10^12); unpatched P2 boost 6065; unpatched P3 boost 6065.
- **B P2 boost core (10).** Fresh P2 boost burns 999,997,999 (used
  10^9, remaining 999,000,000,000, quote_after 1,000,001,000,000,000,
  base_after 999,999,000,002,001); second boost burns 999,995,999;
  min_base exactly 999,997,999 succeeds, +1 fails 6004; request 0 fails
  6002; empty vault fails 6002; vault equal to the request drains and
  **closes the boost ATA** (remaining 0, account gone); vault 10^6
  against a 10^9 request succeeds, burns 999,997 and closes the ATA;
  a re-boost after the close fails 3012; a P2 vq patch alone moves
  the buy tail to 5,262,905,073,807 (-5,208,095).
- **C P3 boost core (6).** Fresh P3 boost burns 999,997,999; draining
  its vault exactly closes its ATA (remaining 0); min+1 fails 6004; a
  closed boost followed by a vq patch burns the anchor; a P3 vq patch
  alone moves the buy tail to 5,262,905,046,036 (-5,235,866); a
  P2-then-P3 sequence burns 999,997,999 on both pools.
- **D authority x pool (8).** Outsider-signed P2 and P3 boosts fail
  6005. `set_boost_authority` by the payer rotates the authority to
  the outsider (1 event, disc 5980f08d5bca4769, 112 bytes); then the
  outsider P2 boost burns the anchor while the payer P2 boost fails
  6005, and rotating back restores the payer P2 boost at the second
  burn 999,995,999. The P3 rotation walk mirrors P2 exactly. An
  outsider-signed rotation attempt fails 6005. The same rotation
  moves the main boost too (outsider main boost burns the anchor
  5,338,379,201,831), so the authority is global, not per pool.
  With `boost_enabled = 0` a P2 boost fails 6066; with the buy
  disable flag (8) it fails 6020.
- **E ATA / program gates (8).** P2 boost with another pool's vault ATA
  fails 2015 ConstraintTokenOwner; a P2 vault ATA owned by the payer
  fails 2015; a P2 boost passing the TOKEN22 program for an SPL ATA
  fails 2023 ConstraintAssociatedTokenTokenProgram; a Token-2022 ATA
  on an SPL mint passes the Anchor checks and fails in the Token-2022
  TransferChecked CPI with fieldless IncorrectProgramId; a P3 boost
  with a TOKEN22-owned ATA and the TOKEN program fails 2023; a P3
  boost with a TOKEN-owned, BP3-owned, BASE2-mint account at a
  non-derived address fails 2009 ConstraintAssociated; a P3 boost
  with the TOKEN22 program for an SPL ATA fails 2023; a main boost
  with a foreign ATA and the TOKEN22 program fails 2023.
- **F chain interactions (8).** P2 boost then buy: tail
  5,262,894,631,186. Buy then P2 boost: burn 989,418,204 (fresh
  999,997,999 minus 10,579,795). P2 boost then sell: payout 178,542,
  exactly +1 over the anchor; a P2 vq patch alone leaves the sell
  payout at 178541, so the +1 comes from the boost, not the patch
  (the patch does move the internal hop splits). P2 boost then
  sweep/collect: protocol sweep 2,488 in full, creator sweep 123,394
  in full, collect 123,394 in full - no Token-2022 withholding split,
  unlike the main pool's net 2,463 / 122,160. P2 boost then main
  boost burns the main anchor; main boost then P2 boost burns the
  P2 anchor. A failed (6065) P2 boost leaves the buy tail at the
  anchor, so the failure rolls back cleanly.
- **G init_boost (3).** init_boost on P2 with no boost ATA succeeds
  with 0 events and creates the empty ATA (rent 2,039,280, balance 0)
  but leaves the vq field at -125,882; a patched boost on that empty
  vault then fails 6002. init_boost on P2 followed by an unpatched
  boost fails 6065. init_boost on the main pool (ATA already present)
  succeeds with 0 events and leaves the vq field unchanged, and the
  following unpatched boost fails 6065.
- **H transfer-fee independence (2).** A P2 boost at bps 5000 and at
  bps 0 both burn 999,997,999 with no withheld amounts: the main
  pool's transfer-fee rate does not touch hop-pool boosts, whose
  quote mints are plain SPL.

## Result

Hop-pool boosts are real, not window-closed: once a hop pool's vq
field is patched to 10^9, P2 and P3 boost exactly like the main pool
at the same vault scale (fresh burn 999,997,999, second 999,995,999),
with the same min_base boundary (exact succeeds, +1 fails 6004) and
the same request-0 / empty-vault 6002. Two asymmetries pin the
cross-pool story. First, draining a hop-pool boost vault **closes the
ATA** and the next boost fails 3012, while the main pool's
Token-2022 quote mint blocks the same close with 6088
QuoteMintNotWritable: hop-pool quote mints are plain SPL, so the
close path skips the harvest step and closes directly. Second, the
boost authority is a single global field: rotating it moves main, P2
and P3 boosts together, and an outsider can only boost after a
payer-signed rotation, never by signing alone. The Anchor gate map
on hop pools is 2015 (wrong owner), 2009 (wrong address), 2023
(wrong token program), with a Token-2022 CPI IncorrectProgramId
behind the Anchor checks for a Token-2022 ATA on an SPL mint. Chain
legs: a P2 vq patch moves the buy tail (-5,208,095) and the internal
sell splits but not the sell payout; a P2 boost moves the buy tail
further and the sell payout by exactly +1; hop-pool sweeps and
collects pay the full accrued amounts with no withholding split.
init_boost creates a missing hop-pool boost ATA but does not open
the window. All 50 cases agree across original, control and
candidate images (0 divergent cases).

## Limits

- All measurements are synthetic harness states (patched vq fields,
  seeded vaults); no on-chain pool was boosted.
- The vq patch is a harness field reset, not an on-chain state
  transition: it models a pool whose window sum is already nonzero.
- The 2009 case uses a hand-seeded account at a non-derived address;
  it pins the Anchor address check, not a reachable user flow.
- Boost burns are measured at vault scale 10^12 with request 10^9;
  other scales were not swept.

Made via @slopdotcash
