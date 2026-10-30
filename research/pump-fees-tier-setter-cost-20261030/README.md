# pump_fees: FeeConfig tier-setter compute-unit cost, original vs rebuild

## Question

The five FeeConfig writers are:

- `update_fee_config`
- `update_stable_fee_config`
- `upsert_fee_tiers`
- `upsert_stable_fee_tiers`
- `set_exotic_flat_fees`

This packet asks two things about them:

1. Does the rebuilt pump_fees image spend the **same compute units (CU)** as the deployed image?
2. Does it take the **same log/error path** across the whole range of these inputs?
   - incoming tier count N
   - stored tier counts M (normal and stable)
   - upsert offset
   - position of the first failing tier
   - account length (2512 / 4073 / 4097 B)

Earlier pump_fees packets checked the return values and state of these setters, and the read-side lookup cost (`get_fees*`). None of them measured how the write-side cost scales with these inputs.

## Method

- Each sweep is one case. Each point in a sweep is one transaction.
- Before every point, the FeeConfig, the FeeProgramGlobal and the signers are reset, so all points start from the same state.
- Each image runs in its own LiteSVM. The clock is fixed and the keys come from fixed seeds.
- Per point, the packet compares:
  - transaction error and Anchor error code;
  - **all logs**, including the `consumed N of M compute units` lines;
  - FeeConfig lamports, length and sha256 after the transaction;
  - compute units.
- The stored tier lists are built as thresholds `0, 10, 20, …`, with fees `(1,1,1)` unless stated otherwise.
- The producer checks every discriminator against `evidence/upstream/pump_fees.json`.

## Images

- **original:** `evidence/original/pump_fees/deployed.so`, sha256 `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`.
- **rebuild:** sha256 `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`.
  - recipe: `scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21
  - source tree `bd2409408730976e376f30580a2926f44e14f006`, repo commit `e2f999e1fd9150c48b4dc8c6c1838f980da8c6b1`

## Result

**26 sweeps, 873 points:**

- Original and rebuild match at every point on behavior: error, error code, logs and account bytes.
- Compute units are identical at every point (rebuild − original = 0 everywhere).
- Logs match byte for byte.
- No mismatch was found, so there is no divergence location to report for these handlers.

Per sweep (CU from the original image; "CU rebuild − orig" lists every distinct difference in the sweep):

| sweep | handler | x | points | outcome | CU orig (first x -> last x) | CU rebuild - orig | behavior | dominant step (CU per +1 x) | steps that differ from it (x: extra CU) |
|---|---|---|---|---|---|---|---|---|---|
| `ok-update-n` | update_fee_config | N incoming | 50 | ok | 21929 (1) -> 61693 (50) | 0 | same | 794 | 4: +219, 5: -10, 10: +1, 11: +218, 16: +1, 23: +213, 24: +4, 29: +1, 35: +1, 41: +1, 48: +1, 49: +216, 50: -8 |
| `ok-update-stored-normal` | update_fee_config | M stored normal | 10 | ok | 21787 (0) -> 24329 (50) | 0 | same | 50 | 1: +42 |
| `ok-update-stored-stable` | update_fee_config | M stored stable | 10 | ok | 21631 (0) -> 34473 (50) | 0 | same | 256 | 1: +42 |
| `ok-stable-n` | update_stable_fee_config | N incoming | 50 | ok | 22083 (1) -> 61847 (50) | 0 | same | 794 | 4: +219, 5: -10, 10: +1, 11: +218, 16: +1, 23: +213, 24: +4, 29: +1, 35: +1, 41: +1, 48: +1, 49: +216, 50: -8 |
| `ok-stable-stored-stable` | update_stable_fee_config | M stored stable | 10 | ok | 21991 (0) -> 24533 (50) | 0 | same | 50 | 1: +42 |
| `ok-stable-stored-normal` | update_stable_fee_config | M stored normal | 10 | ok | 21529 (0) -> 34371 (50) | 0 | same | 256 | 1: +42 |
| `ok-upsert-n-at-0-empty` | upsert_fee_tiers | N incoming (stored 0, offset 0) | 50 | ok | 21575 (1) -> 61386 (50) | 0 | same | 794 | 2: +48, 4: +1, 5: +207, 11: +219, 17: +1, 23: +1, 24: +216, 29: +1, 36: +1, 42: +1, 48: +1, 50: +208 |
| `ok-upsert-n-at-0-over-50` | upsert_fee_tiers | N incoming (stored 50, offset 0) | 50 | ok | 36197 (1) -> 63809 (50) | 0 | same | 546 | 4: +1, 5: +208, 11: +219, 17: +1, 23: +1, 24: +216, 29: +1, 36: +1, 42: +1, 48: +1, 50: +208 |
| `ok-upsert-offset-k-of-50` | upsert_fee_tiers | offset k (stored 50, N 1) | 50 | ok | 36197 (0) -> 36197 (49) | 0 | same | 0 | - |
| `ok-upsert-append-at-m` | upsert_fee_tiers | M stored = offset (N 1) | 50 | ok | 21575 (0) -> 36273 (49) | 0 | same | 298 | 1: +98, 2: -1, 3: -1 |
| `ok-upsert-stable-n-at-0-empty` | upsert_stable_fee_tiers | N incoming (stored 0, offset 0) | 50 | ok | 21837 (1) -> 61648 (50) | 0 | same | 794 | 2: +48, 4: +1, 5: +207, 11: +219, 17: +1, 23: +1, 24: +216, 29: +1, 36: +1, 42: +1, 48: +1, 50: +208 |
| `ok-upsert-stable-append-at-m` | upsert_stable_fee_tiers | M stored = offset (N 1) | 50 | ok | 21837 (0) -> 36535 (49) | 0 | same | 298 | 1: +98, 2: -1, 3: -1 |
| `err-update-invalid-fee-at-i` | update_fee_config | index i of the 10001-bps tier (N 50) | 50 | InvalidFeeTotal | 14404 (0) -> 15727 (49) | 0 | same | 27 | - |
| `err-update-unsorted-at-i` | update_fee_config | index i of the first non-increasing pair (N 50) | 49 | FeeTiersNotSorted | 15774 (0) -> 16494 (48) | 0 | same | 15 | - |
| `err-stable-invalid-fee-at-i` | update_stable_fee_config | index i of the 10001-bps tier (N 50) | 50 | InvalidFeeTotal | 14349 (0) -> 15672 (49) | 0 | same | 27 | - |
| `err-upsert-invalid-fee-in-kept-prefix` | upsert_fee_tiers | stored M with a 10001-bps stored tier 0, N 1 appended at M | 49 | InvalidFeeTotal | 12031 (1) -> 14429 (49) | 0 | same | 50 | 2: -1, 3: -1 |
| `err-update-flat-invalid-n` | update_fee_config | N incoming, flat (10001,0,0) | 50 | InvalidFeeTotal | 11840 (1) -> 14290 (50) | 0 | same | 50 | - |
| `err-update-wrong-admin-n` | update_fee_config | N incoming, non-admin signer | 50 | InvalidAdmin | 5944 (1) -> 8394 (50) | 0 | same | 50 | - |
| `err-update-too-many-n` | update_fee_config | N incoming > 50 | 10 | TooManyFeeTiers | 15459 (51) -> 15909 (60) | 0 | same | 50 | - |
| `err-upsert-offset-gap` | upsert_fee_tiers | N incoming at offset 3 over 2 stored | 8 | OffsetNotContinuous | 13006 (1) -> 15456 (50) | 0 | same | 50 | - |
| `err-upsert-merged-over-50` | upsert_fee_tiers | offset k with N 2 over 50 stored (end = k + 2) | 2 | TooManyFeeTiers | 15535 (49) -> 15583 (50) | 0 | same | 48 | - |
| `ok-update-n-alloc-2512` | update_fee_config | N incoming (account 2512 B) | 50 | ok | 21569 (1) -> 61333 (50) | 0 | same | 794 | 4: +219, 5: -10, 10: +1, 11: +218, 16: +1, 23: +213, 24: +4, 29: +1, 35: +1, 41: +1, 48: +1, 49: +216, 50: -8 |
| `ok-update-n-alloc-4073` | update_fee_config | N incoming (account 4073 B) | 50 | ok | 21601 (1) -> 61365 (50) | 0 | same | 794 | 4: +219, 5: -10, 10: +1, 11: +218, 16: +1, 23: +213, 24: +4, 29: +1, 35: +1, 41: +1, 48: +1, 49: +216, 50: -8 |
| `ok-exotic-alloc-2512` | set_exotic_flat_fees | M stored normal (account 2512 B) | 5 | ok | 23298 (0) -> 36140 (50) | 0 | same | 256 | 1: +42 |
| `ok-exotic-alloc-4073` | set_exotic_flat_fees | M stored normal (account 4073 B) | 5 | ok | 23336 (0) -> 36178 (50) | 0 | same | 256 | 1: +42 |
| `ok-exotic-alloc-4097` | set_exotic_flat_fees | M stored normal (account 4097 B) | 5 | ok | 20822 (0) -> 33664 (50) | 0 | same | 256 | 1: +42 |

## How the CU scales

Both images show the same values. All numbers below come from the table above.

**Decoding the instruction argument costs 50 CU per tier.** These failing sweeps grow by exactly 50 CU per incoming tier:

- `err-update-wrong-admin-n` (`InvalidAdmin`, 5944 → 8394)
- `err-update-flat-invalid-n` (`InvalidFeeTotal` on the flat fees, 11840 → 14290)
- `err-update-too-many-n` (`TooManyFeeTiers`)
- `err-upsert-offset-gap` (`OffsetNotContinuous`)

They fail before or without touching the tier list, so the only N-dependent work is decoding. The admin check fails after the argument is decoded: 50 CU per tier is already spent at `InvalidAdmin`.

**Validation stops at the first failing tier.**

- `InvalidFeeTotal` at index i costs `14404 + 27·i` for `update_fee_config` and `14349 + 27·i` for `update_stable_fee_config`. Zero residual over i = 0..49.
- `FeeTiersNotSorted` at pair i costs `15774 + 15·i`. Zero residual over i = 0..48.
- The fee-total pass runs over all 50 tiers before the sort pass starts. This matches the two `all(...)` passes in `replace_*_tiers` (`programs/pump-fees/src/state.rs`).

**Stored tiers cost differently depending on what happens to them:**

- A stored list that the writer **replaces** costs 50 CU per stored tier:
  - stored normal tiers under `update_fee_config`;
  - stored stable tiers under `update_stable_fee_config`.
- A stored list that is **kept and written back** costs 256 CU per tier:
  - stored stable tiers under `update_fee_config`;
  - stored normal tiers under `update_stable_fee_config` and under `set_exotic_flat_fees`.
- The first stored tier costs a further +42 in all of these sweeps.

**Upsert:**

- Appending at offset M to M stored tiers costs 298 CU per stored tier.
- Writing one tier at offset k into 50 stored tiers costs a flat 36197 CU for every k = 0..49.
- N tiers written at offset 0 cost:
  - 546 CU per tier when they overwrite inside 50 stored tiers;
  - 794 CU per tier when they grow an empty list. This equals the per-tier step of `update_fee_config` and `update_stable_fee_config`.

**Account length:**

- The `update_fee_config` N sweep has the same per-tier step (794) on 2512, 4073 and 4097-byte accounts.
- The intercepts differ: 21569, 21601 and 21929 CU at N = 1. The 4097-byte sweep also stores one stable tier.
- `set_exotic_flat_fees` on a 2512 or 4073-byte account resizes the account to 4097. The program tops the lamports up to 29406000 (the 4097-byte rent minimum; the fixture starts it at 29405000). This costs 23298 / 23336 CU at M = 0, against 20822 on an account that is already 4097 bytes.
- On an account already at 4097 bytes, the lamports are left at 29405000 and no top-up happens. Both images behave this way.

**Step jumps follow the event size.** Every success sweep that varies N has four steps that are about +207 to +219 CU above its dominant step. The length of the `Program data:` event log (read from the receipts) grows by 40 bytes per tier:

- `update_fee_config` / `update_stable_fee_config` events are 148 B at N = 1.
- `upsert_*` events are 125 B at N = 1.

The jumps happen at exactly the points where that event length first goes over 256, 512, 1024 or 2048 bytes:

| sweep | jumps at N | event bytes (N−1 → N) at each jump |
|---|---|---|
| `ok-update-n`, `ok-stable-n` | 4, 11, 23, 49 | 228→268, 508→548, 988→1028, 2028→2068 |
| `ok-upsert-n-at-0-empty`, `ok-upsert-n-at-0-over-50` | 5, 11, 24, 50 | 245→285, 485→525, 1005→1045, 2045→2085 |

This is a correlation measured on both images. The packet does not instrument which buffer grows. The ±1 to ±10 CU wobbles next to the jumps are listed in the table as measured.

## Transaction size

These measurements run in LiteSVM, which does not enforce the 1232-byte packet limit. The serialized transaction size is recorded per point (2 signers, no lookup tables):

| sweep | largest N with tx ≤ 1232 B | tx bytes at that N | tx bytes at N = 50 |
|---|---|---|---|
| `ok-update-n` | 20 | 1203 | 2403 |
| `ok-stable-n` | 21 | 1219 | 2379 |
| `ok-upsert-n-at-0-empty` | 21 | 1220 | 2380 |
| `ok-upsert-stable-n-at-0-empty` | 21 | 1220 | 2380 |

So a full 50-tier list cannot be sent by one legacy transaction of this shape. With these accounts it takes one `update_*` call of at most 20 or 21 tiers followed by `upsert_*` calls. The points above N = 21 measure program behavior only.

## Reproduce

From this folder:

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

- `--images` also accepts a path to a JSON file.
- `verify.py` needs only this folder and the two images:
  1. It checks both image sha256 values against the report.
  2. It replays all 873 points on both images.
  3. It compares each point with the stored receipt.
  4. It rebuilds both runtime files and requires them to match byte for byte.
- Exit code 0 means everything matched; 1 means something differed.

Determinism:

- The producer was run three times: one-VM-per-point, then one-VM-per-sweep twice.
- The runtime files were byte-identical each time:
  - `receipts.jsonl.gz` sha256 `b2ff9e5fcb760579…`
  - `report.json.gz` sha256 `a9a7e31a386bb342…`

Negative checks, both of which make `verify.py` exit 1:

- swapping the two images;
- changing one stored CU value by 1.

## Files

- `producer.py`: builds the cases, runs both images, writes `runtime/`.
- `verify.py`: independent replay and byte comparison.
- `runtime/receipts.jsonl.gz`: per sweep, the case definition and, per point and per image, the error, error code, full logs, FeeConfig lamports/length/sha256, CU and transaction bytes.
- `runtime/report.json.gz`: per sweep, the outcomes, CU arrays for both images, CU differences, transaction sizes and a two-point linear fit with residuals; plus the mismatch lists and image sha256 values.
- `MANIFEST.json`: sha256 and size of every other file.
