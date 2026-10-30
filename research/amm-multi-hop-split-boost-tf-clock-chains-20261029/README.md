# amm-multi-hop-split-boost-tf-clock-chains-20261029

## Problem

The split x boost x transfer-fee multi-hop chain (TRUE 3 hops: three
pools only, final output U3) was pinned in packets #63-#66 and then
combined with claims (#67), lifecycle (#68), recovery (#69),
reassignment (#70), setters (#71), create (#72), track-volume/sync/
claim (#73), reserved fees (#74), rotation (#75), toggles (#76),
disable (#77), buyback-config (#78), fee-config (#79), fee-tables
(#80-#82), account validation (#83-#88), signer validation (#89),
events (#90), dust/rounding (#91), state transitions (#92), and
multi-user/multi-pool legs (#93). None of those packets moved the
clock: every leg ran at a fixed timestamp, so it was unproven
whether prices, claim conversion, sync, boost, sweeps, or setters
read the clock at all, and whether the day-boundary arithmetic in
`claim_token_incentives` and the pre-start reset gate in `sync`
behave at the boundaries rather than only at the fixture point.

This packet runs the same TRUE 3-hop chain with an explicit unix
timestamp on every leg (per-step clock control in the producer) and
with GlobalVolumeAccumulator start/end/seconds patches, and pins
what the clock does and does not move.

## Cases

66 cases, 237 signed receipts, 24 parts (23 x 10 + 7), three program
images (original, control, candidate) per step. Fixture UVA seed
(needs_claim 1, unclaimed 111, claimed 222, volume 333444, last 20,
has 1, earned 555, claimed-cashback 666); GVA fixture start 20,
end 49, seconds_in_a_day 1, supply 30 x 1000, sol 30 x 100; chain
buy anchor in 10**9 pays tail U3 5,262,910,281,902; sell anchor of
10**9 pays 178,541.

- Family A (14): trade/event clock-independence. Multi-hop buy at
  ts 0, 10, 21, 777, -1, 2**62; sell at 0, 777, -1; v2 buy,
  deposit, protocol sweep, sweep+collect, and boost (vq patch
  10**9) at ts 777; boost at ts -1.
- Family B (18): token-claim clock sweep. Single claims at ts 0,
  10, 19, 20, 21, 22, 49, 50, 100, 1000, 2**62, -1; last 49 at
  ts 50, last 50 at ts 60, last 100 at ts 200, last 0 at ts 21;
  sequences [claim@0, claim@21, claim@22] and [claim@21,
  claim@22].
- Family C (12): sync clock sweep. Single syncs at ts 0, 10, 19,
  20, 21, 50, -1 (last 10); last 20 at ts 10, last 19 at ts 19,
  last 21 at ts 10; sequences [sync@10, claim@21, claim@22] and
  [sync@10, claim@10, claim@21, claim@22].
- Family D (12): GVA start/end/seconds patches. start 100 / end
  1000: claim at 99, 100, 101; sync at 99, 101 (last 50). end 30:
  claim at 31, and claim at 40 from last 31. seconds 0: claim at
  21, sync at 10. seconds 86400: claim at 86420, claim at 90000
  from last 86420, sync at 10.
- Family E (5): lifecycle/cashback event clock. Cashback claim
  (plain mint, no withdraw-withheld authority patch) at ts 777
  and ts 0; init, close, and real 90 -> 137 extend at ts 777.
- Family F (4): setter/sweep clock. Buyback-config 7500 then buy,
  buy-disable then buy, admin rotation, and
  sweep+creator-sweep+collect, all at ts 777.
- Family G (1): sell at ts -1 (negative-clock leg outside the
  claim path).

## Result

All 66 cases agree on all three images: **0 divergences**. Amounts
and error codes are identical across original, control, and
candidate everywhere; only event timestamps move with the clock.

- Trade prices are clock-blind. The multi-hop buy tail is
  5,262,910,281,902 at ts 0, 10, 21, 777, -1, and 2**62 alike, and
  the sell pays 178,541 at ts 0, 777, and -1. Every hop event
  timestamp equals the leg clock exactly, including -1 and
  2**62 (4,611,686,018,427,387,904). The v2 buy (cost 186,637),
  deposit (base 160,619,896 / quote 29,313 / LP 1,000,000),
  protocol sweep (2,488 -> net 2,463), creator sweep (123,394 ->
  net 122,160), and collect (122,160 -> net 120,938) amounts are
  the #93 anchors; their event timestamps are 777.
- Token-claim conversion is a day-boundary gate, not a smooth
  function of time. At ts <= 20 only the 111 unclaimed pays
  (net 109, volume stays 333444, last moves to the claim ts).
  At ts >= 21 the full 3,334,551 pays (net 3,301,205: 111 +
  333444 x 1000/100, withheld ceil 1% = 33,346) and volume goes
  to 0. The last_update gate is independent of the clock: last
  49 at ts 50 converts (previous_day 29 <= end_day 29), last 50
  at ts 60 does not (previous_day 30 > 29), last 100 at ts 200
  does not, and last 0 at ts 21 does not (last < start skips
  the reward branch). A claim at ts 0 then 21 pays 111 then
  nothing (volume stranded at last 21, silent second claim);
  only the ts 22 claim converts, paying 3,334,440 (net
  3,301,095) because the 111 was already paid. A negative
  clock claim fails with ProgramFailedToComplete (the
  timestamp-to-usize conversion panics) and rolls back fully:
  0 events, UVA unchanged.
- Sync fires only when now < start AND last < start. Sync at
  ts 0, 10, 19, and -1 fires (claimed 222 -> 0, has flag
  cleared, 64-byte SyncUserVolumeAccumulatorEvent with the
  clock ts); sync at ts 20, 21, and 50 does not. The
  last_update side is independent: last 20 at ts 10 does not
  fire, last 19 at ts 19 fires, last 21 at ts 10 does not.
  After a firing sync, claim at 21 pays only the 111
  unclaimed and claim at 22 converts the full volume
  (claimed 111 -> 3,334,551); inserting a claim at 10 between
  sync and claim 21 changes nothing (the ts 10 claim pays
  111, the ts 21 claim is silent, the ts 22 claim converts).
  This confirms #92's "sync strands volume" for the
  cross-clock case: the stranded volume is payable the next
  day, not lost.
- GVA patches move the gates with the fields, not the clock.
  With start 100 / end 1000, claim at 99 pays 111 (pre-start),
  claim at 100 pays 111 (today 0, reward branch skipped
  because last 20 < start), and claim at 101 converts
  (3,334,551); sync at 99 fires (last 50 < 100) and sync at
  101 does not. With end 30, claim at 31 converts
  (previous_day 0 <= end_day 10) but claim at 40 from last 31
  pays only 111 (previous_day 11 > 10). With seconds 0, claim
  at 21 pays only 111 (the reward branch is skipped when
  seconds_in_a_day is 0) while sync at 10 still fires. With
  seconds 86400, claim at 86420 converts (today 1,
  previous_day 0 <= end_day 0) but claim at 90000 from last
  86420 pays only 111 (previous_day 1 > 0), and sync at 10
  still fires (sync never reads seconds_in_a_day).
- Lifecycle and cashback events follow the clock. Cashback
  claims pay 5,475 at ts 777 and ts 0 with the event ts
  equal to the leg clock. Init (80 bytes), close (80 bytes,
  carrying unc 111 / claimed 222 / vol 333444 / last 20), and
  real 90 -> 137 extend (96 bytes) events all carry ts 777.
- Setters and boost are clock-blind in amounts. Buyback bps
  7500 scales the buyback leg to 6,773,206 at ts 777 with the
  tail unchanged; buy disable fails the buy with 6020 at
  ts 777 (0 events); admin rotation emits its 80-byte event
  at ts 777; sweep/collect amounts and timestamps are the
  #93 anchors at timestamp 777. Boost burn is 5,338,379,201,831
  at ts 777 and ts -1 alike, while the 208-byte boost event
  ts follows the clock (777 / -1).

## Relation to earlier packets

- #73 established the claim conversion (3,334,551) and the
  pre-start reset gate at the fixture clock; this packet
  extends both along the clock axis and confirms the gate
  conditions are `now < start AND last < start` for sync
  and the previous_day / end_day comparison for claim.
- #68 established the UVA lifecycle events at the fixture
  clock; this packet shows init/close/extend event
  timestamps track the leg clock while amounts do not move.
- #87 established the GVA start-field reset gate via account
  validation; this packet shows the same gate driven by
  start/end/seconds patches on valid accounts.
- #92's "sync strands volume" and "claim is one-shot"
  observations hold across clocks: stranded volume converts
  the next day, and a second claim in the same day is silent.
- #90 recorded event timestamps at the fixture clock; this
  packet proves the timestamp field of every event family
  (trade, sweep, collect, boost, claim, sync, init, close,
  extend, setter) equals the leg clock.

## Limits

- The clock is set per leg through LiteSVM's clock override;
  this packet does not test slot/epoch progression or
  on-chain clock sysvar staleness across transactions.
- The negative-clock claim panic is observed as
  ProgramFailedToComplete with full rollback; the exact
  panic site inside the claim path is not pinned to a
  source line by this packet.
- The boost-internal 512-byte buy event is recorded by
  disc/len only; its timestamp field is not decoded in
  this packet (the boost event's own ts is decoded).
- Only the TRUE 3-hop route (three_amm, final output U3)
  is used; 4-hop and 5-hop routes are covered by #61/#62
  and #65/#66 and are not re-run here.

## Reproduce

`python3 producer.py` rebuilds the receipts under
`runtime/` (10 per part, 24 parts); `python3 verify.py`
re-checks signatures, deltas, withheld, pool/UVA/GVA/
GlobalConfig states, decoded events, error codes, rollback,
and three-image agreement from the packet files alone.

Made via @slopdotcash
