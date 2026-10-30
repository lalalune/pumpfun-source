# Pump Main admin_update_token_incentives: schedule boundaries (original vs rebuild)

## Question

Do the original Pump Main image and the rebuild behave the same on `admin_update_token_incentives`, the admin setter for the PUMP-token incentive schedule? The cases cover:

- the time-range checks: errors 6031–6035 and the `secs * 30` overflow;
- the daily-supply update before and after start: errors 6036–6038 and the `day_number >= 30` fill;
- the account constraints;
- the setter chained with `claim_token_incentives` in one transaction.

## Why this is not covered yet

These repository harnesses exercise the setter:

- `scripts/pump_admin_token_incentives_differential.py` (and `pump_admin_token_incentives_verify.py`, which imports it)
- `pump_incentives_admin_differential.py` (and `pump_incentive_schedule_differential.py`, which imports it)

Both base harnesses load `research/imported-lab/...`, which is not in the git tree, so none of them can be rerun from a checkout.

No repository test (`tests/test_*_captured.py`) models this instruction, and no existing `research/` folder or open PR covers it. The companion packet `pump-claim-incentives-cashback-boundaries-20261030` covers the claim side.

## Setup

- **Images.** Original: `evidence/original/pump/deployed.so`, sha256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`, 10,485,715 bytes. Rebuild: sha256 `e04e3e5652e0cfbf55c6ef30533aea6084ea60432aac8a468056b0a6f19dd633`, 1,934,648 bytes. It was built by `scripts/build_partial_candidate.py` with platform-tools v1.44 / cargo-build-sbf 2.1.21, from source tree `97a2a2a383ba1bc5c5af08429de150e6124f0fc1`, repo commit `aba9e07e8872a53ebfdeffc7cc5bfa20714fc053`.
- **Loader and simulator.** Each image is loaded with the upgradeable-loader layout in an in-process LiteSVM (solders 0.27.1). System, SPL Token, Token-2022 and ATA are LiteSVM built-ins. There is no network.
- **State.** Global is synthetic: 1,088 bytes, with `authority` at offset 9 set to the fee payer. The `GlobalVolumeAccumulator` is synthetic too (600 bytes), built from the upstream IDL layout; discriminators and account counts are asserted. Keys come from fixed seeds. The clock is fixed at unix 1,800,000,000 (except two cases that move it). Each case is one signed transaction.
- **Accumulator states.**
  - FRESH: all zero.
  - FUTURE: start = now + 1 day, 10-day range, 86,400 s days.
  - RUNNING: now is on day 3 of 0..=10; supply 7 and volume 5 in every slot.
  - FINISHED: ended 10 days ago.
- **Recording and comparison.** The same as the companion packet:
  - The receipts hold the transaction bytes, the error, all logs, events and the Pump `msg!` lines. Those lines include the setter's `GlobalVolumeAccumulator={:?}` dump.
  - They also hold the panic text without location, the inner instructions, the full after-state and the compute units.
  - Behavior equality means equal tx, error, events, Pump messages, panic text, inner instructions and after-state.

## Result

**All 55 cases behave identically on the original and the rebuild:** 0 behavior mismatches and 0 outcome mismatches. 27 cases succeed and 28 fail, with the same error or panic on both images. That includes the full `{:?}` dump line.

Compute units are equal in 36 cases; 35 have byte-identical logs. The other 19 differ only in compute units and in the printed source path (`programs/pump/src/...` in the original, `src/...` in the rebuild; line:column identical):

| orig - rebuild CU | cases | where |
|---|---|---|
| +14 | 17 | the AnchorError exits of the time-range and supply checks (6031–6038), plus the `end_day` divisor panic (case 31) |
| +11 | 1 | "SVM is 64-bit" panic at volume_accumulator.rs:436 (negative start_time, case 40) |
| 0 | 1 | "Unexpected overflow" panic at volume_accumulator.rs:376 (secs * 30): path differs, CU equal |
| −90 | 1 | `index out of bounds` panic at volume_accumulator.rs:317: **the rebuild costs 90 CU more** |

The companion claim packet shows the same −90 on its two `index out of bounds` panics, at lines 429 and 78. So all three bounds-check panics measured across the two packets cost the rebuild exactly 90 CU more. The other panic kinds cost it 0–14 CU less. The cause was not determined.

Measured behavior worth noting. Each item holds on both images, and none of it is a divergence.

- **The accepted range is exactly `secs * 30 - 1`** (cases 6–7).
  - `seconds_in_a_day` 0 or −1 is rejected with `TimeRangeTooLarge`.
  - `i64::MAX / 30 + 1` panics with "Unexpected overflow".
  - `i64::MAX / 30` with `end = i64::MAX` is accepted (case 12).
- **Writes outside the range update.**
  - `seconds_in_a_day` and `mint` are written even when the range update is skipped, i.e. when start or end is 0 (cases 13–14).
  - A different mint replaces the stored mint without a check, and the new mint's incentive ATA is created (case 43).
- **Shrinking a running range (cases 17 and 19).**
  - Only `sol_volumes[current+1..=new end_day]` is zeroed. Slots after the new end keep their old volume, and `total_token_supply` is never cleared.
  - `end_day == current` is rejected with 6035 (case 18).
- **Changing `seconds_in_a_day` while running (case 24).**
  - The new day length takes effect immediately. The current day becomes 6, and only slots 7..=29 are zeroed.
  - Days 0..=6 keep the volumes recorded under the old 86,400 s day.
- **Supply before start.**
  - `day_number <= end_day` sets one slot (cases 25–26).
  - `day_number` 11..29 is rejected with 6037 (cases 27–28).
  - `day_number >= 30`, including u64::MAX, fills 0..=end_day (case 29).
- **Supply after start.**
  - It is accepted while `now <= end_time`, including now == end_time (case 38); a finished range gives 6036 (case 37).
  - `day_number < current` gives 6038 (case 34).
  - A fill writes current..=end_day (case 36).
- **Panics and in-transaction claims.**
  - With `seconds_in_a_day = 0` and a supply update, `end_day` panics with "end_time should be bigger than start_time" (case 31).
  - A synthetic 40-day range panics at the fill loop's index 30 (case 32).
  - A new future start zeroes both arrays. A claim in the same transaction then pays 0 (case 55), while a claim after a fill is paid from the untouched day-2 supply: 7 units (case 54).

The columns below show the decoded accumulator after the transaction. Times are offsets from the clock (1,800,000,000), and the arrays are run-length encoded (`7x3 1000x8` = three 7s, then eight 1000s). "(unchanged)" means the transaction was rolled back or changed nothing.

## Per-case results

| # | case | outcome (both images) | accumulator after: start / end / secs (offsets from clock) | total_token_supply | sol_volumes | CU original | CU rebuild | orig - rebuild |
|---|---|---|---|---|---|---|---|---|
| 1 | `fresh-set-range` | ok:updated | +100 / +864100 / 86400 | 0x30 | 0x30 | 118880 | 118880 | 0 |
| 2 | `start-equals-now` | error:StartTimeInThePast | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 48342 | 48328 | 14 |
| 3 | `start-now-plus-1` | ok:updated | +1 / +86400 / 86400 | 0x30 | 0x30 | 118880 | 118880 | 0 |
| 4 | `end-equals-now` | error:EndTimeInThePast | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 48364 | 48350 | 14 |
| 5 | `end-equals-start` | error:EndTimeBeforeStartTime | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 48379 | 48365 | 14 |
| 6 | `range-30-days-minus-1` | ok:updated | +100 / +2592099 / 86400 | 0x30 | 0x30 | 118880 | 118880 | 0 |
| 7 | `range-30-days` | error:TimeRangeTooLarge | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 48305 | 48291 | 14 |
| 8 | `secs-zero` | error:TimeRangeTooLarge | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 48130 | 48116 | 14 |
| 9 | `secs-one-range-29` | ok:updated | +100 / +129 / 1 | 0x30 | 0x30 | 118846 | 118846 | 0 |
| 10 | `secs-negative` | error:TimeRangeTooLarge | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 48134 | 48120 | 14 |
| 11 | `secs-mul-overflow` | panic:Unexpected overflow | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 46368 | 46368 | 0 |
| 12 | `secs-max-end-max` | ok:updated | +100 / i64::MAX / 307445734561825860 | 0x30 | 0x30 | 119058 | 119058 | 0 |
| 13 | `start-zero-skips-range` | ok:updated | 0 / 0 / 86400 | 0x30 | 0x30 | 118631 | 118631 | 0 |
| 14 | `end-zero-skips-range` | ok:updated | 0 / 0 / 123 | 0x30 | 0x30 | 118616 | 118616 | 0 |
| 15 | `fresh-supply-only` | error:SupplyUpdateForFinishedRange | 0 / 0 / 0 (unchanged) | 0x30 | 0x30 | 46863 | 46849 | 14 |
| 16 | `fresh-range-and-fill` | ok:updated | +100 / +864100 / 86400 | 1000x11 0x19 | 0x30 | 119291 | 119291 | 0 |
| 17 | `running-same-start-shorter-end` | ok:updated | -259300 / +172700 / 86400 | 7x30 | 5x4 0x2 5x24 | 117712 | 117712 | 0 |
| 18 | `running-end-on-current-day` | error:EndTimeBeforeCurrentDay | -259300 / +604700 / 86400 (unchanged) | 7x30 | 5x30 | 48113 | 48099 | 14 |
| 19 | `running-end-current-plus-1` | ok:updated | -259300 / +86300 / 86400 | 7x30 | 5x4 0x1 5x25 | 117701 | 117701 | 0 |
| 20 | `running-end-in-past` | error:EndTimeInThePast | -259300 / +604700 / 86400 (unchanged) | 7x30 | 5x30 | 48340 | 48326 | 14 |
| 21 | `running-new-future-start` | ok:updated | +100 / +864100 / 86400 | 0x30 | 0x30 | 117688 | 117688 | 0 |
| 22 | `running-new-past-start` | error:StartTimeInThePast | -259300 / +604700 / 86400 (unchanged) | 7x30 | 5x30 | 48342 | 48328 | 14 |
| 23 | `running-halve-day-length` | error:TimeRangeTooLarge | -259300 / +604700 / 86400 (unchanged) | 7x30 | 5x30 | 48281 | 48267 | 14 |
| 24 | `running-halve-day-length-ok` | ok:updated | -259300 / +1036699 / 43200 | 7x30 | 5x7 0x23 | 117943 | 117943 | 0 |
| 25 | `future-supply-day-0` | ok:updated | +86400 / +950400 / 86400 | 1000x1 0x29 | 0x30 | 117586 | 117586 | 0 |
| 26 | `future-supply-end-day` | ok:updated | +86400 / +950400 / 86400 | 0x10 1000x1 0x19 | 0x30 | 117586 | 117586 | 0 |
| 27 | `future-supply-after-end-day` | error:DayIndexAfterEndIndex | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 48037 | 48023 | 14 |
| 28 | `future-supply-day-29` | error:DayIndexAfterEndIndex | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 48037 | 48023 | 14 |
| 29 | `future-supply-fill-u64max-day` | ok:updated | +86400 / +950400 / 86400 | 1000x11 0x19 | 0x30 | 117944 | 117944 | 0 |
| 30 | `future-supply-zero` | ok:updated | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 117537 | 117537 | 0 |
| 31 | `future-secs-zero-supply` | panic:end_time should be bigger than start_time | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 46310 | 46296 | 14 |
| 32 | `future-40-day-fill` | panic:index out of bounds: the len is 30 but the index is 30 | +86400 / +3542400 / 86400 (unchanged) | 0x30 | 0x30 | 46946 | 47036 | -90 |
| 33 | `running-supply-current-day` | ok:updated | -259300 / +604700 / 86400 | 7x3 1000x1 7x26 | 5x30 | 117643 | 117643 | 0 |
| 34 | `running-supply-past-day` | error:DayInActiveRange | -259300 / +604700 / 86400 (unchanged) | 7x30 | 5x30 | 48028 | 48014 | 14 |
| 35 | `running-supply-after-end-day` | error:DayIndexAfterEndIndex | -259300 / +604700 / 86400 (unchanged) | 7x30 | 5x30 | 48048 | 48034 | 14 |
| 36 | `running-supply-fill` | ok:updated | -259300 / +604700 / 86400 | 7x3 1000x8 7x19 | 5x30 | 117887 | 117887 | 0 |
| 37 | `finished-supply` | error:SupplyUpdateForFinishedRange | -1728000 / -864000 / 86400 (unchanged) | 7x30 | 5x30 | 46863 | 46849 | 14 |
| 38 | `supply-at-exact-end` | ok:updated | -259300 / +604700 / 86400 | 7x10 1000x1 7x19 | 5x30 | 117643 | 117643 | 0 |
| 39 | `supply-at-exact-start` | ok:updated | -259300 / +604700 / 86400 | 1000x1 7x29 | 5x30 | 117643 | 117643 | 0 |
| 40 | `running-negative-clock-start` | panic:SVM is 64-bit: TryFromIntError(()) | -1800000100 / -1799568000 / 86400 (unchanged) | 0x30 | 0x30 | 46575 | 46564 | 11 |
| 41 | `not-authority` | error:NotAuthorized | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 43757 | 43757 | 0 |
| 42 | `authority-unsigned` | error:AccountNotSigner | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 4425 | 4425 | 0 |
| 43 | `mint-replaced` | ok:updated | +86400 / +950400 / 86400 | 1000x1 0x29 | 0x30 | 126807 | 126807 | 0 |
| 44 | `incentive-ata-exists` | ok:updated | +86400 / +950400 / 86400 | 1000x1 0x29 | 0x30 | 89056 | 89056 | 0 |
| 45 | `token-2022-mint` | ok:updated | +86400 / +950400 / 86400 | 1000x1 0x29 | 0x30 | 122497 | 122497 | 0 |
| 46 | `incentive-not-ata` | error:AccountNotAssociatedTokenAccount | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 12646 | 12646 | 0 |
| 47 | `accumulator-absent` | error:AccountNotInitialized | absent |  |  | 6547 | 6547 | 0 |
| 48 | `accumulator-wrong-owner` | error:AccountOwnedByWrongProgram | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 7072 | 7072 | 0 |
| 49 | `accumulator-543-bytes` | error:AccountDidNotDeserialize | 543-byte data, not decoded |  |  | 8063 | 8063 | 0 |
| 50 | `global-wrong-address` | error:ConstraintSeeds | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 43595 | 43595 | 0 |
| 51 | `token-program-mismatch` | runtime MissingAccount | +86400 / +950400 / 86400 (unchanged) | 0x30 | 0x30 | 14630 | 14630 | 0 |
| 52 | `seq-update-twice-same-start` | ok:updated | +100 / +777700 / 86400 | 1000x1 0x29 | 0x30 | 208049 | 208049 | 0 |
| 53 | `seq-update-twice-new-start` | ok:updated | +101 / +432100 / 86400 | 0x30 | 0x30 | 208050 | 208050 | 0 |
| 54 | `seq-fill-then-claim` | ok:updated (claim paid 7) | -259300 / +604700 / 86400 | 7x3 9x8 7x19 | 5x30 | 152180 | 152180 | 0 |
| 55 | `seq-new-start-then-claim` | ok:No tokens to claim (claim paid 0) | +100 / +864100 / 86400 | 0x30 | 0x30 | 138167 | 138167 | 0 |

The per-case notes, the outcome strings and the log-line classification are in `runtime/report.json.gz`, under `loaders.upgradeable.cases`.

## Reproduce

```
python3 producer.py --root <repo checkout> \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' \
  --out <this folder>
python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
```

`producer.py` is deterministic. Two runs into different folders produced byte-identical `plan.json.gz`, `receipts-upgradeable.jsonl.gz` and `report.json.gz`.

`verify.py` reads only this folder and the two images, and exits 0 or 1:

1. checks both image sha256 values against the report;
2. checks the receipt file's sha256;
3. replays all 55 cases on both images and requires every receipt to be identical;
4. recomputes the summary.

Passing the rebuild in the `original` slot exits 1 with an image sha256 mismatch.

## Files

- `producer.py`: the case plan, execution and summary. `verify.py` imports its execution code.
- `verify.py`: the independent re-check.
- `runtime/plan.json.gz`: the initial accounts and instructions of every case.
- `runtime/receipts-upgradeable.jsonl.gz`: 110 receipts (55 cases × 2 images).
- `runtime/report.json.gz`: image hashes, the summary and per-case rows.
- `MANIFEST.json`: sha256 and size of every file except itself.
