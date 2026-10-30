# pump_fees: update_fee_shares_v2 token-quote cost and instruction-trace ceiling vs shareholder counts, original vs rebuild

## Question

For `update_fee_shares_v2` on the token-quote route, does the rebuilt pump_fees image spend the **same compute units (CU)** and take the **same log path** as the deployed image? The sweep covers:

- the old shareholder count K, from 1 to 10;
- the new shareholder count L, from 1 to 10;
- an SPL Token quote mint and a Token-2022 quote mint (no extensions).

On this route pump_fees CPIs pump `distribute_creator_fees_v2(initialize_ata=true)`. That call pays the K old holders from the creator-vault quote ATA and creates each holder ATA that is missing. The existing update-shares packets checked payout semantics and rescaling. None of them measured cost or trace depth against K and L on this route.

## Method

- There are 230 points. Each point is one `update_fee_shares_v2` transaction on a fresh LiteSVM per image, preceded by `SetComputeUnitLimit(1400000)`.
- The SharingConfig (v2) holds K non-executable shareholders A..J with equal bps; the remainder goes to the first. The new list is L holders taken from J backwards.
- The curve's stored quote mint is the SPL or Token-2022 test mint, and the curve has non-zero reserves, so no AMM CPI runs. The creator-vault quote ATA holds 1,000,000,000 base units.
- Point groups:
  - `q-kKK-lLL` (100 points): SPL quote, no holder ATA exists beforehand.
  - `t-kKK-lLL` (100 points): Token-2022 quote, same grid.
  - `e-kKK-l01` (10 points): SPL quote, every old-holder ATA already exists.
  - `z-kKK-l01` (10 points): SPL quote, empty vault (amount 0).
  - `cq-/ct-k10-l01-preNN` (6 points): K = 10, with the first 1, 2 or 5 old-holder ATAs pre-created.
  - `a-kKK-l01-preNN` (4 points): SPL quote, zero curve reserves and a funded AMM coin-creator vault ATA (500,000,000), so pump_fees first CPIs pump_amm `transfer_creator_fees_to_pump_v2`. K = 1, 9, 10 and 10 with one ATA pre-created.
- pump and pump_amm are the deployed images from `evidence/original/` on both sides; only pump_fees is swapped.
- Per point, the packet compares:
  - transaction sha256 and error;
  - **all logs**, including the per-program `consumed` lines;
  - decoded events;
  - lamport and token deltas, and account state of the sharing config, vault ATAs, payer, authority and every holder ATA;
  - compute units.
- "Trace entries" counts the `Program … invoke [n]` log lines, top level included.
- The report also records each holder's ATA bump distance (255 − canonical bump) for both quote mints.
- The fixture follows the merged `pump-fees-update-shares-v2-native-quote-route` packet, with a token quote instead of WSOL: synthetic SharingConfig, 740-byte pump Global, pump curve, mint and ATA fixtures.

## Images

- **original:** `evidence/original/pump_fees/deployed.so`, sha256 `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`.
- **rebuild:** sha256 `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`.
  - recipe: `scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21
  - source tree `bd2409408730976e376f30580a2926f44e14f006`
- **CPI dependencies, both sides:**
  - pump `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
  - pump_amm `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`

## Result

**Original and rebuild match at all 230 points.**

- Behavior matches at every point, logs match byte for byte, and CU is identical (rebuild − original = 0).
- Trace-entry counts are identical too.
- No mismatch was found, so there is no divergence location to report.

The findings below hold for both images.

### 1. Ten old holders without ATAs fail with `MaxInstructionTraceLengthExceeded`

- All 21 points with K = 10 and no pre-existing holder ATA fail with `InstructionError(1, MaxInstructionTraceLengthExceeded)`: 10 per quote mint (L = 1..10), plus the AMM-route point.
- All 180 grid points with K ≤ 9 succeed.
- Trace entries are exactly:
  - 5 + 6K when the CPI creates every holder ATA. Each holder adds an ATA create (ATA program, GetAccountDataSize, system create, InitializeImmutableOwner, InitializeAccount3) plus TransferChecked.
  - 5 + K when every ATA exists (TransferChecked only).
  - 5 + 5K with an empty vault (creates, no transfer).
- At K = 10 the creating route needs 65 entries:
  - The failing receipt reaches 64 `invoke` lines. The last is pump's event self-invoke.
  - The rejected 65th is pump_fees' own self-invoke after its `UpdateFeeSharesEvent` log line; at K = 9 the same invoke is entry 59.
  - The whole transaction reverts, so every token delta is 0.
- The controls show that pre-creating **one** of the ten ATAs (60 entries) is enough for success, on both quote mints.
  - The 5 + 5K and 5 + K routes stay at 55 and 15 entries at K = 10 and succeed.
- The AMM route adds exactly 2 entries (7 + 6K: 13 at K = 1, 61 at K = 9). It does not move the ceiling: K = 9 succeeds, K = 10 fails at 64 entries, and K = 10 with one ATA pre-created succeeds at 62.
- The count of 5 fixed entries includes the `SetComputeUnitLimit` top-level instruction. Every `q-`/`t-` point with K ≥ 2 uses more than 200,000 CU, the default limit for a single instruction. So on this route, dropping that instruction to save a trace entry is not an option.

### 2. Cost model

- **CU is exactly separable** for K ≤ 9: CU(K, L) = CU(K, 1) + CU(1, L) − CU(1, 1). The residual is 0 at all 90 successful (K, L) points per quote mint.
- Corners on the original image (equal to the rebuild):
  - SPL: 175657 at (1, 1) and 533285 at (9, 10).
  - Token-2022: 176526 at (1, 1) and 491338 at (9, 10).
- **New holders (L):** the per-holder step is identical for SPL and Token-2022: 689 … 1008.
  - It rises steadily except at L = 5 (+1005).
  - The `UpdateFeeSharesEvent` data is 151 B at L = 1 and grows 34 B per holder. It is 253 B at L = 4 and 287 B at L = 5, so the extra step is where the event first goes over 256 B.
- **Old holders (K):** the per-holder step depends on the holder's ATA bump distance (table below).
  - With ATA creation, SPL steps are 39450–40122 CU at bump distance 0, 44065–44397 at 1 and 48785–49009 at 2.
  - Token-2022 steps are 35338–35782 at 0, 39723–40170 at 1 and 44895 at 2.
  - With pre-created ATAs the steps are 13865–14537 at 0, 15480–15812 at 1 and 17200–17424 at 2.
  - The K = 10 step of the failing rows is only up to the abort point and is not comparable.
  - The bump-dependent part is spent in callees that are the same images on both sides. At (1, 1) on the SPL quote, the logs show:
    - pump `distribute_creator_fees_v2` CPI: 62959 CU, including ATA create 20490 and TransferChecked 6173;
    - pump_fees event self-invoke: 6595 CU;
    - pump_fees total: 175507 CU;
    - transaction total: 175657 CU.

### Tables

#### K sweep at L = 1

| K | added holder | ATA bump distance (SPL / T22) | SPL quote CU | +step | T22 quote CU | +step | empty vault (SPL) CU | +step | ATAs pre-created (SPL) CU | +step | trace entries (create / pre-created / empty vault) | outcome (create) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | A | 0 / 0 | 175657 | — | 176526 | — | 166971 | — | 150072 | — | 11 / 6 / 10 | ok |
| 2 | B | 0 / 1 | 215107 | 39450 | 216249 | 39723 | 197735 | 30764 | 163937 | 13865 | 17 / 7 / 15 | ok |
| 3 | C | 0 / 0 | 254972 | 39865 | 251887 | 35638 | 228914 | 31179 | 178217 | 14280 | 23 / 8 / 20 | ok |
| 4 | D | 1 / 0 | 299037 | 44065 | 287225 | 35338 | 264293 | 35379 | 193697 | 15480 | 29 / 9 / 25 | ok |
| 5 | E | 1 / 1 | 343210 | 44173 | 327171 | 39946 | 299780 | 35487 | 209285 | 15588 | 35 / 10 / 30 | ok |
| 6 | F | 2 / 0 | 391995 | 48785 | 362729 | 35558 | 339879 | 40099 | 226485 | 17200 | 41 / 11 / 35 | ok |
| 7 | G | 1 / 1 | 436392 | 44397 | 402899 | 40170 | 375590 | 35711 | 242297 | 15812 | 47 / 12 / 40 | ok |
| 8 | H | 2 / 0 | 485401 | 49009 | 438681 | 35782 | 415913 | 40323 | 259721 | 17424 | 53 / 13 / 45 | ok |
| 9 | I | 0 / 2 | 525523 | 40122 | 483576 | 44895 | 447349 | 31436 | 274258 | 14537 | 59 / 14 / 50 | ok |
| 10 | J | 6 / 0 | 585056 | 59533 | 511882 | 28306 | 506320 | 58971 | 298330 | 24072 | 64 / 15 / 55 | MaxInstructionTraceLengthExceeded |

#### L sweep at K = 1 (both quotes)

| L | SPL CU | +step | T22 CU | +step |
|---|---|---|---|---|
| 1 | 175657 | — | 176526 | — |
| 2 | 176346 | 689 | 177215 | 689 |
| 3 | 177053 | 707 | 177922 | 707 |
| 4 | 177804 | 751 | 178673 | 751 |
| 5 | 178809 | 1005 | 179678 | 1005 |
| 6 | 179645 | 836 | 180514 | 836 |
| 7 | 180524 | 879 | 181393 | 879 |
| 8 | 181446 | 922 | 182315 | 922 |
| 9 | 182411 | 965 | 183280 | 965 |
| 10 | 183419 | 1008 | 184288 | 1008 |

#### K = 10 controls (L = 1)

| point | quote | old-holder ATAs pre-created | trace entries | CU | outcome |
|---|---|---|---|---|---|
| q-k10-l01 | SPL | 0 | 64 | 585056 | MaxInstructionTraceLengthExceeded |
| cq-k10-l01-pre01 | SPL | 1 | 60 | 567595 | ok |
| cq-k10-l01-pre02 | SPL | 2 | 55 | 542010 | ok |
| cq-k10-l01-pre05 | SPL | 5 | 40 | 459255 | ok |
| t-k10-l01 | T22 | 0 | 64 | 511882 | MaxInstructionTraceLengthExceeded |
| ct-k10-l01-pre01 | T22 | 1 | 60 | 494032 | ok |
| ct-k10-l01-pre02 | T22 | 2 | 55 | 465058 | ok |
| ct-k10-l01-pre05 | T22 | 5 | 40 | 384136 | ok |

#### AMM route controls (SPL, zero curve reserves, AMM coin-creator vault ATA holds 500000000)

| point | K | old-holder ATAs pre-created | trace entries | CU | outcome |
|---|---|---|---|---|---|
| a-k01-l01-pre00 | 1 | 0 | 13 | 265619 | ok |
| a-k09-l01-pre00 | 9 | 0 | 61 | 615485 | ok |
| a-k10-l01-pre00 | 10 | 0 | 64 | 652089 | MaxInstructionTraceLengthExceeded |
| a-k10-l01-pre01 | 10 | 1 | 62 | 657557 | ok |

## Reproduce

From this folder:

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

- `verify.py` reads pump and pump_amm from `<repo>/evidence/original/{pump,pump_amm}/deployed.so`, next to the original image.
- It checks all four image sha256 values against the report.
- It replays the 230 points on both images, compares every receipt, and requires both runtime files to match byte for byte.
- Exit code 0 means everything matched; 1 means something differed.

Determinism: two producer runs gave byte-identical runtime files:

- `receipts.jsonl.gz` `44aacf81aaf4612d…`
- `report.json.gz` `e3bef46b143d484b…`

## Files

- `producer.py`: fixture, cases and runner, writes `runtime/`.
- `verify.py`: independent replay.
- `runtime/receipts.jsonl.gz`: per point, the case and the full per-image results.
- `runtime/report.json.gz`: per point, the CU grid (original, rebuild), the trace-entry counts and the error. It also holds the holder ATA bump distances, the mismatch lists and the image sha256 values.
- `MANIFEST.json`: sha256 and size of every other file.
