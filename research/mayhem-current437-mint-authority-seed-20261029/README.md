# Count Mayhem `mint-authority` seed string and descriptor (30 bytes)

## Problem

The merged qualified437 data ledger stops at **23,834 / 26,180 payload bytes**.
The `mint-authority` seed literal and its `.data.rel.ro` descriptor are still
uncredited. The seed sits in the original image directly after the
`mint_authority` literal at `[712401, 712415)`, which has no descriptor, and
immediately before binary bytes.

## Requirement

Attribute exactly that one observed seed literal and its descriptor under the
project's data-attribution scope, without counting adjacent bytes or
re-crediting any prior packet.

## Cause / Why

The original image has `b"mint-authority"` at `[712415, 712429)`. A 16-byte
`.data.rel.ro` record at `[727632, 727648)` contains `u32 low = 0`,
`u32 high = 712415`, `u64 length = 14`, with exactly one type-8,
symbol-index-zero relocation at the record start. The candidate image carries
the same bytes and layout at `[690969, 690983)` and `[707920, 707936)`. The
descriptor therefore gives the exact length bound; no NUL or adjacent string is
used.

The archived source at `src/state.rs:607` declares the same seed, in the same
`InitializeMayhemState` accounts struct that declares the `global-params` seed:

```rust
#[account(signer, seeds = [b"mint-authority"], bump, seeds::program = PUMP_ID)]
pub mint_authority: UncheckedAccount<'info>,
```

## Result

- Baseline, recomputed as the sealed union of the 24 merged qualified437
  deltas at current `upstream/main` (`907d3980`): **23,834 / 26,180 payload
  bytes** (`.rodata` 16,722 / 18,396; `.data.rel.ro` 7,112 / 7,784).
- New payload: **30 bytes** (14 `.rodata` + 16 `.data.rel.ro`; descriptor split
  into 8 raw length bytes and 8 mapped pointer bytes).
- After: **23,864 / 26,180 bytes (91.15%)**, `.rodata` **16,736 / 18,396**,
  `.data.rel.ro` **7,128 / 7,784**.
- New intervals: `[712415, 712429)` and `[727632, 727648)`; disjoint from the
  merged qualified437 union and from open #1000 `[711426, 711439)` /
  `[727376, 727392)`, #1003 `[710472, 710488)` / `[732888, 732904)` and #1005
  `[708936, 708968)` / `[732696, 732712)`.

The descriptor interval fills a 16-byte hole exactly: the preceding
`.data.rel.ro` bytes are covered up to `727632` and the following descriptor
record starts at `727648`.

## Evidence

`observations.json.gz` records the original/candidate string bytes, descriptor
words, pointer targets, and the type-8/symbol-zero relocations.
`baseline/sources.json` records all 24 source delta paths and SHA-256 values;
the verifier recomputes the union and asserts 23,834 rather than summing
packets. `source-context/provenance.json` pins the archived tarball, member,
line, excerpt hash and seed.

## Implementation choices

- Count only the selected 14-byte literal and 16-byte descriptor.
- Do not claim a code site, a descriptor-table allocation, or any adjacent
  byte; the preceding `mint_authority` literal and following binary bytes are
  not absorbed.
- Treat the pointer field as 8 mapped bytes and the length field as 8 raw
  bytes, matching the existing descriptor grammar.
- This is static data attribution only. The `InitializeMayhemState` handler
  body remains a stopped lane and is not reopened, extended or claimed here.

## Tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research/mayhem-current437-mint-authority-seed-20261029/verify.py --repo .
PYTHONDONTWRITEBYTECODE=1 python3 -B research/mayhem-current437-mint-authority-seed-20261029/test_verify.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/verify_evidence.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/test_tooling.py
```

Results: package verifier OK; **16/16** package tests OK;
`verify_evidence.py` reports 9 captures verified; `test_tooling.py` 6/6 OK.

## Still open

Nearby uncredited static items remain for separate packets, each with its own
bound and no overlap with this one:

- `Unexpected variant tag: ` at `[712372, 712396)` with descriptor
  `[727592, 727608)`.
- `mint_authority` at `[712401, 712415)` and `payer` at `[712396, 712401)`;
  neither has a located descriptor, so neither has an exact length bound.
- The Rust core range/slice panic literals at `[725204, 725291)` and
  `[710520, 710536)` with their descriptors at `[733120, 733216)`; one
  34-byte literal has two descriptors and needs one careful packet.
