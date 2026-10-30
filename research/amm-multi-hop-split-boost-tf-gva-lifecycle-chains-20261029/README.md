# research: multi-hop split x boost GVA lifecycle chains under transfer fee

## Problem

The GlobalVolumeAccumulator (GVA) has no init and no close
instruction in the program: only `close_user_volume_accumulator`
exists, and it closes the UVA, not the GVA. The GVA is a PDA
account (`seeds = [b"global_volume_accumulator"]`) that must
pre-exist, and its lifecycle is driven by
`admin_update_token_incentives` plus the claim/sync reads. On the
same true-3-hop split x boost x tf chain as packets #64-#109
(`three_amm` only, final output U3), this packet measures what
chain legs do beside an absent / zeroed / truncated / wrong-owner
GVA, the full admin gate map, what a start change, a mid-range
admin call, a supply-slot edit, and a mint rotation each do to the
next claim, the sync reset gate, and the UVA close arc.

Fixture GVA: start 20, end 49, seconds_in_a_day 1, mint IMINT
(`e2` x 32), total_token_supply 1000 x 30, sol_volumes 100 x 30.
Fixture UVA seed (when seeded): needs 1, unclaimed 111, claimed
222, current_sol_volume 333444, last_update 20, has 1, earned 555,
cashback_claimed 666. Claim clock is 21, sync clock is 10, admin
clock is 10 unless a case says 25 or 60. The claim conversion is
reward = current_sol_volume x total_token_supply[prev_day] /
sol_volumes[prev_day]; the fixture conversion pays
333444 x 1000 / 100 = 3,334,440, plus the seeded unclaimed 111 =
3,334,551, for a claimed total of 222 + 3,334,551 = 3,334,773.

## Cases

60 cases, 294 receipts (steps x 3 images), 30 parts (29 x 10 + 4).
0 divergent cases across original / control / candidate.

- A (7): anchors. Multi-hop buy tail 5,262,910,281,902, multi-hop
  sell payout 178,541, boost burn 5,338,379,201,831, token claim
  3,334,551, sync no-op, sync reset, claim twice.
- B (14): GVA absent / zeroed / truncated (100 bytes) /
  wrong-owner, each beside chain legs, claim, sync, and admin.
- C (19): admin gates and admin effects: same-start, new-end,
  start-wipe, supply day-0, supply all-days, mid-range zeroing,
  the eight gate errors, outsider, unsigned, mint rotation,
  admin-then-boost, admin-then-buy.
- D (7): claim lifecycle: claim after buy / boost / sweeps,
  absent incentive vault, empty incentive vault, absent user ATA,
  seeded wrong-mint GVA.
- E (3): sync lifecycle: sync after claim + start change, sync
  with absent GVA, sync with zeroed GVA.
- F (8): UVA close lifecycle: close seeded, close then claim,
  close then buy, close then buy then claim, close then init
  then claim, close by another user, unsigned close, close then
  boost.
- G (3): GVA-blind chain legs: absent-GVA deposit/withdraw,
  admin then buy then boost, zeroed-GVA sell.

## Result

### There is no GVA init or close path; an absent GVA breaks only the incentive legs

- GVA absent: multi-hop buy tails the anchor 5,262,910,281,902,
  boost burns the anchor 5,338,379,201,831, protocol sweep pays
  2,488 -> net 2,463, creator sweep 123,394 -> net 122,160,
  collect 122,160 -> net 120,938, deposit/withdraw move the
  anchor amounts. Trades, boost, sweeps, collects, and liquidity
  never read the GVA.
- GVA absent: token claim, sync, and admin all fail 3012
  (AccountNotInitialized). Admin does NOT create the GVA: the
  account is `mut` without `init`, so there is no on-chain
  re-init path for a missing GVA at all.
- Truncated GVA (100 bytes): buy still tails the anchor, but
  claim and admin fail 3003 (deserialization). Wrong-owner GVA:
  buy still tails the anchor, claim fails 3007.
- Zeroed GVA (start 0, end 0, sec 0, supplies 0, vols 0): claim
  pays only the seeded unclaimed 111 (the conversion block is
  skipped when seconds_in_a_day is 0), volume stays 333444,
  needs_claim stays 1, claimed becomes 333. Sync is a no-op
  (now 10 is not < start 0). Admin from the zeroed GVA
  (start 20, end 49) does NOT restore conversion: the start
  change already reset supplies and vols to 0, and the next
  claim still pays only 111.

### The admin gate map, every code measured

- Start in the past -> 6030 StartTimeInThePast. End in the
  past -> 6031 EndTimeInThePast. End before start -> 6032
  EndTimeBeforeStartTime. Range over 30 x seconds_in_a_day - 1
  -> 6033 TimeRangeTooLarge (this is why an end of 60 with
  sec 1 fails: 60 - 20 = 40 > 29). Supply update for a finished
  range (start 0, end 0, supply > 0, clock 60 past end 49) ->
  6035 SupplyUpdateForFinishedRange. Day after the end day ->
  6036 DayIndexAfterEndIndex. Day inside the active range ->
  6037 DayInActiveRange. Outsider admin -> 6005 InvalidAdmin
  (has_one). Unsigned admin -> 3010. Every gate rolls back
  completely.
- Same-start admin (20, 49, 1, day 0, supply 0) succeeds with
  the 88-byte admin event and leaves the GVA byte-identical.
  New-end admin (end 49 -> 40) succeeds and the next claim
  still converts normally (3,334,551).

### A start change wipes everything; a mid-range admin zeroes only the future

- Start 20 -> 30 (end 59): total_token_supply and sol_volumes
  both become all-zero. The next claim pays only the seeded
  unclaimed 111, volume stays 333444, needs_claim stays 1,
  claimed becomes 111. The following sync (clock 10 < start 30,
  last 21 < start 30) resets claimed 111 -> 0 with the 64-byte
  sync event (before 111, after 0).
- Mid-range admin at clock 25 (day 7, supply 777): supplies[7]
  becomes 777, sol_volumes[6..29] become 0, sol_volumes[0..5]
  stay 100, supplies elsewhere stay 1000. The day-0 claim is
  unaffected (3,334,551), because day 0 is already past.
- Supply-slot edits move the next claim reward exactly:
  day-0 supply 1000 -> 2000 doubles the conversion to
  333444 x 2000 / 100 = 6,668,880, amount 6,668,991, claimed
  6,669,213. All-days supply 500 (day_number 30) sets every
  slot to 500: conversion 333444 x 500 / 100 = 1,667,220,
  amount 1,667,331, claimed 1,667,553.

### Mint rotation breaks claims, restoration re-enables them

- Admin rotating the GVA mint to the quote mint costs fee 5,000
  + 2,157,600 rent for the newly created quote-mint incentive
  ATA (total payer delta -2,162,600) and stores the quote mint
  in the GVA. The next claim fails 6038 InvalidIncentiveMint
  (has_one). Admin rotating the mint back to IMINT costs only
  the 5,000 fee (the IMINT ATA already exists) and the next
  claim converts normally (3,334,551).
- Seeded wrong-mint GVA (mint = zero pubkey) also fails claims
  with 6038, without any admin call.

### Sync fires only when now < start and last < start

- Seeded UVA (last 20) with fixture start 20: sync is a no-op
  (0 events, "No changes in accumulator") because last is not
  < start. UVA with last 10: sync resets claimed 222 -> 0 and
  has_total_claimed_tokens 1 -> 0 with the 64-byte sync event.
- Claim then start-change (20 -> 30) then sync: sync resets
  claimed 3,334,773 -> 0 with the event, even though the claim
  just succeeded -- the reset gate only looks at the clocks,
  not at how the claimed total got there.
- Sync with absent GVA fails 3012; sync with zeroed GVA
  (start 0) is a no-op.

### Claim lifecycle: trades add no volume; the vault and the user ATA decide success

- Claim after a multi-hop buy, after a boost, and after sweeps
  all pay exactly the seeded conversion 3,334,551: chain trades
  do not write current_sol_volume (their events carry
  track_volume false), so the claim converts only fixture-seeded
  volume.
- Claim with the incentive vault account absent fails 3012.
  Claim with an empty vault (0 balance) fails with the token
  program's custom error 1 (insufficient funds).
- Claim with the user ATA absent succeeds and auto-creates it
  (init_if_needed): payer delta -2,162,600 (fee + 2,157,600
  ATA rent), then the full 3,334,551 lands in the new ATA.
- Claim twice: the second claim is a no-op (0 events, no
  deltas) -- after the first claim volume is 0 and unclaimed
  is 0, so there is nothing left to convert or pay.

### UVA close strands unclaimed tokens; the boost and the next buy do not care

- Close of the seeded UVA emits the 80-byte close event
  (unclaimed 111, claimed 222, volume 333444, last 20) and
  refunds the UVA lamports: payer delta +999,995,000 (fee
  -5,000 + 1,000,000,000 refund). The UVA account is gone.
- Claim after close fails 3012 (the claim's UVA account is
  `mut` without `init`). Close by another user fails 2006
  (seeds). Unsigned close fails 3010.
- Buy after close recreates a fresh UVA (rent 1,844,400 +
  fee 5,000) and tails the anchor 5,262,910,281,902. Claim
  after close + buy is a fresh no-op (claimed 0, last 21).
- Re-init after close creates a fresh zero UVA (rent
  1,844,400 + fee) and the next claim is still a no-op: the
  stranded unclaimed 111 never returns. Close then boost
  burns the anchor 5,338,379,201,831.
- Admin then buy then boost burns the post-buy value
  5,254,679,949,141 (the #105 post-buy burn, reproduced):
  admin supply edits do not move the burn either.

## Limits

- `cpatch` steps are harness field resets (GVA/pool fields,
  clock), never instructions; they carry empty transactions by
  design. The GVA seeds, the UVA seeds, and the incentive vault
  balances are fixture state set before the measured leg runs.
- The claim clock is fixed at 21 and the sync clock at 10 in
  this harness, so day conversions are measured for day 0 only;
  other days follow the same formula with their own supply and
  volume slots, which the admin cases pin slot by slot.
- No source change is proposed. No claim is made about the
  program beyond the measured legs above.

Made via @slopdotcash
