# pump_fees: update_fee_shares compute-unit cost vs shareholder counts, original vs rebuild

## Question

Does the rebuilt pump_fees image spend the **same compute units (CU)** and take the **same log path** as the deployed image for `update_fee_shares`? The check covers the full range of:

- the old shareholder count K, from 1 to 10;
- the new shareholder count L, from 1 to 10.

Earlier update-shares packets checked the payout and rescale semantics. None of them measured how the cost scales with these counts.

## Method

- There are 100 points (K × L). Each point is one `update_fee_shares` transaction on a fresh LiteSVM per image. A `SetComputeUnitLimit(1400000)` instruction precedes it.
- The SharingConfig (v2) holds K non-executable shareholders. They have equal bps, and the remainder goes to the first.
- The new list has L shareholders, built the same way.
- The pump creator vault holds 1 SOL above rent, so the pump `distribute_creator_fees` CPI pays all K old holders.
- The curve has non-zero reserves, so no AMM CPI runs.
- The pump and pump_amm programs are the deployed images from `evidence/original/` on both sides; only pump_fees is swapped.
- Per point, the packet compares:
  - transaction sha256 and error;
  - **all logs**, including the per-program `consumed` lines;
  - decoded events;
  - lamport deltas and account state of the sharing config, the creator vault, the payer and every holder;
  - compute units.
- The fixture is the one from the merged update-shares packets: synthetic SharingConfig, 740-byte pump Global and pump curve.

## Images

- **original:** `evidence/original/pump_fees/deployed.so`, sha256 `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`.
- **rebuild:** sha256 `7a14f41440c60ac6e95053e9fdc712376a1eac3447ec2de6fa29b1b6ec654900`.
  - recipe: `scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21
  - source tree `bd2409408730976e376f30580a2926f44e14f006`
- **CPI dependencies, both sides:**
  - pump `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
  - pump_amm `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`

## Result

**100 of 100 points succeed on both images.**

- Behavior (error, logs, events, lamports, state) matches at every point.
- Compute units are identical at every point (rebuild − original = 0).
- Logs match byte for byte.
- No mismatch was found, so there is no divergence location to report.

Transaction CU, original image (equal to the rebuild):

- 122438 at K = 1, L = 1.
- 171114 at K = 10, L = 10.

**The cost is exactly separable.** CU(K, L) = CU(1,1) + f(K) + g(L), with zero residual at all 100 points. Every row has the same L-differences, and every column has the same K-differences.

| step | CU added by each +1 (K = 2..10 or L = 2..10) |
|---|---|
| old holder K (paid by the pump distribute CPI, then dropped) | 4445, 4680, 4400, 4424, 4452, 4480, 4508, 4651, 4874 |
| new holder L | 689, 707, 751, 1005, 836, 879, 922, 965, 1008 |

**New holders (L).** The per-holder step rises by 43 CU per holder from L = 6 on (836 → 1008). The L = 5 step is about 210 CU above that trend. Measured from the `Program data:` logs, the `UpdateFeeSharesEvent` is 151 B at L = 1 and grows by 34 B per holder. It is 253 B at L = 4 and 287 B at L = 5, so the extra step happens where the event first goes over 256 bytes. The FeeConfig setter cost packet sees the same correlation at 256 / 512 / 1024 / 2048 bytes. The packet does not instrument which buffer grows.

**Old holders (K).** Each K step includes the pump `distribute_creator_fees` CPI paying one more holder. pump is the same deployed image on both sides, so it adds no difference.

At K = 1, L = 1 the logs show these per-program CU lines:

| program | CU | what it is |
|---|---|---|
| pump (first CPI, in log order) | 2170 | |
| pump (second CPI, in log order) | 24157 | |
| pump_fees | 122288 | includes both CPIs |
| — | 150 | the rest of the transaction total |

## Reproduce

From this folder:

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_fees/deployed.so", "candidate": "<candidate.so>"}'
```

- `verify.py` reads pump and pump_amm from `<repo>/evidence/original/{pump,pump_amm}/deployed.so`, next to the original image.
- It checks all four image sha256 values against the report.
- It replays the 100 points on both images, compares every receipt, and requires both runtime files to match byte for byte.
- Exit code 0 means everything matched; 1 means something differed.

Determinism: two producer runs gave byte-identical runtime files:

- `receipts.jsonl.gz` `2114eb51ef63b38d…`
- `report.json.gz` `53be075f455aac6d…`

## Files

- `producer.py`: fixture, cases and runner, writes `runtime/`.
- `verify.py`: independent replay.
- `runtime/receipts.jsonl.gz`: per point, the case and the full per-image results.
- `runtime/report.json.gz`: the CU grid (original, rebuild) for every point, the mismatch lists and the image sha256 values.
- `MANIFEST.json`: sha256 and size of every other file.
