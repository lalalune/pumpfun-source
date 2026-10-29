# GlobalVolumeAccumulator account validation on the split x boost x tf chain (true 3 hops)

## Problem

Packets 3rd #83, #84, #85, and #86 pinned the validation surface of
the fee-table account (disc wrong 3002, owner wrong 3007, zero
lamports 3012, check order 3012 > 3007 > 3002, key swaps all
3007), of the GlobalConfig account (disc wrong
InvalidAccountData, owner wrong 3007, zero lamports 3012, check
order 3012 > 3007 > InvalidAccountData, key swaps split by
owner/existence), of the route pools (disc wrong
InvalidAccountData, owner wrong 6027 on multi-hop but 3007
elsewhere, zero lamports 6027 on multi-hop but 3012 on v2, a
single 6027 gate collapsing the check order on multi-hop, key
swaps split into 6027 for non-pool keys and 6008 for other
pool keys), and of the UserVolumeAccumulator (disc wrong 3002,
owner wrong 3007, zero lamports 3012, check order
3012 > 3007 > 3002, key swaps split into 3002 for program-owned
keys, 3007 for the fee-table key, 3012 for a fresh key, 2006 for
another user's UVA, length gates 3001/3003 with a 90-byte floor,
extend alone on the 6027/2004/no-op path) on this chain. This
packet pins the same surface for the remaining account the
volume legs read -- the GlobalVolumeAccumulator (GVA), the
account the sync and token-claim legs read: does a wrong
discriminator, a wrong owner, zero lamports, a swapped
account key, a truncated/extended length, a rebound mint, or a
moved start/end gate the sync and token-claim legs the same
way -- and is the gate code the same? The close, extend, and
init legs take no GVA account, so they are out of scope here.

Route: the split x boost x tf chain at TRUE 3 hops (the
`three_amm`-only route 3rd #63/#64 pinned; no g4/g5 hop group is
appended, final output U3). The quote mint carries a 100 bps
transfer-fee config and the split legs route the buyback through
the Token-2022 ATA, as in #64.

Fixture: the GVA account is seeded as discriminator +
start_time 20 + end_time 49 + seconds_in_a_day 1 + mint IMINT +
total_token_supply[30] of 1000 + sol_volumes[30] of 100, padded
to 600 bytes, 10^9 lamports, pump-program owned, at the
`global_volume_accumulator` PDA. The UVA seeds are the #86
seeds: SEED (needs_claim 1, unclaimed 111, claimed 222,
current_sol_volume 333444, last_update 20, has 1, earned 555,
cashback_claimed 666), FSEED (earned 5475, cashback_claimed 0),
and SYNC_FIRE (last_update 10, otherwise SEED).

## Cases

61 cases, 204 receipts (68 steps x 3 images: original, control
#424, candidate #427), 21 parts of 10 receipts (20x10 + 4).

- Family A, anchors (6): mhbuy3 / mhsell3 in 10^9 at bps 100;
  token claim on the seeded UVA (claim bps 100, gross
  3,334,551); cashback claim in plain-quote mode (seeded earned
  5,475, no withheld-authority guard); sync with a firing reset
  (seed last_update 10, before the GVA start 20) and a no-op
  sync (seed last_update 20).
- Family D, discriminator (8): sync disc zeroed, flipped,
  replaced with the pool discriminator, replaced with the
  GlobalConfig discriminator, replaced with the fee-table
  discriminator; token-claim disc zeroed, flipped, replaced
  with the pool discriminator.
- Family T, whole-data swaps (4): token-claim GVA data
  replaced with pool data, GlobalConfig data, fee-table data,
  or zeros (length kept at 600).
- Family O, owner (6): token-claim owner SPL Token,
  Token-2022, System Program, default pubkey, Fees program;
  sync owner SPL Token.
- Family L, lamports (4): token-claim lamports 0, 1, and
  2,000,000 (below the 5,066,880 rent-exempt minimum for a
  600-byte account); sync lamports 0.
- Family X, combined faults (4): token-claim disc+owner,
  lamports+disc, lamports+owner, all three combined.
- Family Z, missing account (2): token-claim and sync with
  the GVA account absent (0 lamports, empty, default owner).
- Family K, key swaps (9): sync GVA slot pointed at the
  GlobalConfig key, the pool key, the fee-table key, a fresh
  key, a second key holding valid GVA bytes (but not the PDA),
  and another user's UVA; token-claim GVA slot pointed at the
  pool key, a fresh key, and another user's UVA.
- Family G, length (6): sync GVA lengths 0, 543, 544, 1000;
  token-claim GVA lengths 543, 544.
- Family M, mint binding (3): token-claim GVA mint replaced
  with the quote mint, the base mint, or zero.
- Family S, start/end contents (4): sync with SYNC_FIRE and
  GVA start moved to 100 (fires) and to 5 (no-op); token
  claim with GVA start moved to 100 (reward branch skipped);
  token claim with GVA start 100 and end 49 (end before
  start -- panic probe).
- Family W, downstream legs after a GVA failure (5): a
  disc-zeroed GVA fails the token claim, then multi-hop buy,
  multi-hop sell, protocol sweep + creator sweep + collect,
  boost, and cashback claim each run as the next step.

## Result

All 61 cases agree on all three images (original, control #424,
candidate #427). No divergence. Error sites are pinned per
image in the report and are never compared across images.

- Discriminator wrong: 3002 AccountDiscriminatorMismatch on
  both legs (sync disc zero/flip/pool/config/fee, token-claim
  disc zero/flip/pool, whole-data swaps pool/config/fee/zero).
  This matches the #83 fee-table and #86 UVA pattern, and
  differs from #84 GlobalConfig and #85 Pool, which fail
  InvalidAccountData on a wrong discriminator (Anchor
  deserialization vs custom parsing).
- Owner wrong: 3007 AccountOwnedByWrongProgram on both legs
  (SPL Token, Token-2022, System Program, default pubkey,
  Fees program). The fee-table key swap also lands on 3007,
  because the fee-table account is Fees-owned.
- Lamports: 0 fails 3012 AccountNotInitialized on both legs
  (the account vanishes from the VM); 1 lamport and 2,000,000
  lamports both succeed with the anchor-identical token-claim
  payout of 3,334,551 gross (net 3,301,205, withheld 33,346),
  so no rent-exempt minimum is checked -- same as #86.
- Check order: lamports > owner > disc > seeds.
  Disc+owner fails 3007, lamports+disc and lamports+owner and
  all three combined fail 3012 -- exactly the #83/#86 order.
  The seeds constraint (2006 ConstraintSeeds) sits below the
  discriminator check: it is only reachable when the
  discriminator matches, as the second key holding valid GVA
  bytes proves (valid bytes, wrong key -> 2006, while the
  pool, GlobalConfig, and other-user-UVA keys all fail 3002
  first and the fee-table key fails 3007 first).
- Key swaps: sync -- GlobalConfig key 3002, pool key 3002,
  fee-table key 3007, fresh key 3012, valid-GVA-bytes key
  2006, another user's UVA 3002. Token-claim -- pool key 3002,
  fresh key 3012, another user's UVA 3002. The split differs
  from #86's UVA swaps (where another user's UVA failed 2006
  on the PDA-seeds check): on the GVA slot the discriminator
  check fires before seeds, so a UVA account fails 3002, and
  only a discriminator-matching key reaches the seeds gate.
- Missing account: 3012 on both legs (sync and token-claim),
  matching #73's sync observation and extending it to claim.
- Length gates: 0 bytes fails 3001
  AccountDiscriminatorNotFound, 543 bytes fails 3003
  AccountDidNotDeserialize, and 544, 600, and 1000 bytes all
  succeed -- the 544-byte struct floor with no upper bound
  check (trailing bytes ignored). The 544-byte token-claim
  pays the full 3,334,551; the 544/1000-byte syncs are no-ops
  on the SEED UVA (last_update 20, not before start 20).
- Mint binding: a GVA mint of quote, base, or zero all fail
  6038 InvalidIncentiveMint (PumpAmmError 38, incentives.rs
  `has_one=mint` on the claim leg). The binding is exact: only
  the incentive mint itself passes.
- Start/end contents vs the #73 reset gate: the gate is
  driven by the GVA start field itself. Sync with last_update
  10 fires when GVA start is 20 or 100 (claimed 222 -> 0,
  has 1 -> 0, 64-byte event disc c57aa77c74515bff) and is a
  no-op when GVA start is 5 (0 events, claimed stays 222).
  Claim with GVA start 100 pays only the 111 unclaimed
  (reward branch skipped, volume 333444 preserved, needs_claim
  stays 1, claimed 111, event amount 111 with
  current_sol_volume 333444). An end-before-start GVA (end 49,
  start 100) does NOT panic: it pays the same 111-only amount
  with the same event, because the reward branch is skipped
  before any end/start arithmetic.
- Downstream legs after a GVA failure: all still work.
  Multi-hop buy tail U3 5,262,910,281,902 and multi-hop sell
  match the #64 anchors; protocol sweep 2,488 -> net 2,463
  (withheld 25), creator sweep 123,394 -> net 122,160
  (withheld 1,234), collect 122,160 -> net 120,938 (withheld
  1,222); boost burn 5,338,379,201,831 (the #64 tf100 anchor);
  cashback claim 5,475 in full. A failed GVA validation leaks
  nothing into the next step: every failure step rolls back
  all watched accounts except the 5,000 fee, and the GVA
  account itself is byte-identical before and after every
  step (sync and claim never write it).

Comparison with the earlier validation packets on this chain:

| account | disc | owner | lamports 0 | order | key swaps |
|---|---|---|---|---|---|
| fee-table (#83) | 3002 | 3007 | 3012 | 3012>3007>3002 | all 3007 |
| GlobalConfig (#84) | InvalidAccountData | 3007 | 3012 | 3012>3007>InvalidAccountData | fee 3007 / pool InvalidAccountData / fresh 3012 |
| Pool (#85) | InvalidAccountData | 6027 mh / 3007 | 6027 mh / 3012 | single 6027 on mh | non-pool 6027 / other pool 6008 |
| UVA (#86) | 3002 | 3007 | 3012 | 3012>3007>3002 | pool/cfg 3002 / fee 3007 / fresh 3012 / other UVA 2006 |
| GVA (#87) | 3002 | 3007 | 3012 | 3012>3007>3002>seeds 2006 | pool/cfg/other-UVA 3002 / fee 3007 / fresh 3012 / valid-bytes key 2006 |

The GVA pattern is the #83/#86 pattern plus one rung: the
seeds gate at the bottom, reachable only with a matching
discriminator.

## Limits

- Only the sync and token-claim legs read the GVA account;
  close, extend, and init take no GVA account and are not
  covered here. The multi-hop, sweep, collect, boost, and
  cashback-claim legs do not read GVA either; they appear
  only as downstream legs after a GVA failure.
- The GVA fixture uses one mint (IMINT), one start/end/
  seconds triple (20/49/1), and uniform supply/sol arrays
  (1000/100); field interactions beyond start/end/mint (for
  example seconds_in_a_day, or per-day supply/sol values)
  are not varied.
- The end-before-start probe covers end 49 with start 100
  at claim time 21 only; other orderings of now/start/end
  were not probed.
- Receipts are LiteSVM executions against three program
  images (original, control #424, candidate #427) on the
  sparse fixture harness, not mainnet transactions. No
  program source was modified; no claim is made about
  programs other than pump-amm.

## Reproduce

`producer.py` is the exact builder that produced the
receipts in `runtime/`; `verify.py` independently re-checks
every receipt (signatures, deltas, withheld, pool/UVA/GVA/
GlobalConfig states, events, error codes, rollback, GVOL
invariance, control == candidate) from the packet files
alone plus the three program images.

Made via @slopdotcash
