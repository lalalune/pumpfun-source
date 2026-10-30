# Lane w6r1-layout-rodata (wave 6, round 1): rodata / data layout for raw

Base: origin/main c2f6d6509, rebased onto 8289b1712 (both 1027/1035 normalized, 276 raw; the rebased branch was re-scored against a fresh 8289b17 build: zero losses, unstripped 94a9b81f).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w6r1-layout-rodata/` (`scripts/trial.sh`
wraps fastbuild + score + the w3-raw-layout data metrics; `scripts/capture.py` captures
`-C no-prepopulate-passes` IR, experiment only).

## Data layout on base (w3-raw-layout metrics)

- 1021 matched windows had every data lddw at the original's in-section offset; 2 did not
  (`0x10c20` TryFromIntError Debug, `0x101448` GlobalVolumeAccumulator deserialize).
- `.data.rel.ro`: 6 non-`.text` slot diffs, all from one swapped pair at 0x220: the original has the
  borsh `src/de/mod.rs:637:21` Location (`ArrayDropGuard::fill_buffer`, `init_count += 1`) before the
  `&()` Debug vtable; ours had the vtable first. w3 attributed it to U-block hash order.
- `.rodata`: 31993/32031 aligned; the only difference is the `creator/admin_cto.rs` path string after
  the `No canonical pump pool for this mint; curve only` msg! literal (both first created inside the
  unmatched `admin_cto::execute`, so it belongs to that window's reconstruction).

## Finding: the swapped pair is a TryFromSliceError Debug artefact, not hash order (`afe4e465`)

Pre-opt IR (`capture.py ... -C no-prepopulate-passes`) shows the `&()` Debug vtable (`vtable.9`) is first
referenced by the cross-crate-inlinable local copy of `<core::array::TryFromSliceError as Debug>::fmt`
(`_ZN67_...`, which sorts before `fill_buffer`'s `_ZN70_$LT$$u5b...`); the next user is
TryFromIntError Debug (`_ZN70_$LT$core..num...`), which sorts after `fill_buffer`. The TFSE fmt mono item
exists only because seven `slice.try_into().unwrap()` sites need `TryFromSliceError: Debug`
(`Result::unwrap` is MIR-inlined, its `E` Debug vtable references the fmt). The fmt itself is dead after
LLVM (all conversions have fixed length), so it never appears in either binary, but the vtable it
created first survives for TryFromIntError. The original therefore has no TFSE Debug mono item.

Change: those seven sites use `.try_into().unwrap_or_default()` (quote_control::state x2,
pump_quote::vault_amount x2, set_reserved_fee_recipients, DistributionCurve::try_deserialize_unchecked x2).
Every one converts a fixed-length range of the right length, so the `Err` arm is unreachable and no
runtime path changes. `.text` differs from base only in the two lddw operands; `.rodata` is unchanged.

| metric | base | this lane |
| --- | ---: | ---: |
| official normalized / raw | 1027 / 276 | 1027 / 276 (0 losses) |
| windows with every data lddw at the original offset | 1021 | **1023** (all checked) |
| `.data.rel.ro` non-`.text` slot diffs (of 1294) | 6 | **0** |
| `.rodata` aligned bytes (of 32031) | 31993 | 31993 |
| model raw, unmatched fixed, full original order, data as built | 1017 | **1019** |

Rule for every lane: do not write `slice.try_into().unwrap()`/`.expect()` (any `Result<_, TryFromSliceError>`
that needs `Debug`). It brings the TFSE Debug mono item back and swaps the pair again.

## Remaining data differences (all inside the unmatched admin_cto::execute)

`scripts/unmdata.py` compares, for each unmatched window, the multiset of data lddw targets (section, offset)
against the original. All of them already reference exactly the original's constants, except
`0x22a10 admin_cto::execute`:
- `.rodata`: the `creator/admin_cto.rs` path is created after the `No canonical pump pool for this mint; curve only`
  msg! literal (line 766). Both are first referenced in `admin_cto::execute`. In the pre-opt IR the path is
  referenced earlier in the text (IR line 593 vs 1186), yet the msg global is created first, because rustc creates
  constants in RPO codegen order. So in the original's MIR, an `admin_cto.rs` error block comes before the msg block
  in RPO. `#[inline]` on the nested `validate` (`17497f92`) gives byte-identical output.
- path Source references: 16 in ours vs 15 in the original. The `.data.rel.ro:0x128` (24-B vtable) has 12 references vs 10.

These are code-structure facts for the admin_cto lanes. They will change when that window matches.

## Attempts

| id | trial | result |
| --- | --- | --- |
| `afe4e465` | t01: 7 TFSE unwrap sites -> `unwrap_or_default` | kept: data windows 1021 -> 1023, .data.rel.ro diffs 6 -> 0, 0 losses |
| `17497f92` | t02: `#[inline]` nested admin_cto `validate` (path vs msg order) | byte-identical, rejected |
| - | t03: t01 rebased on 8289b17 | 1027/276, 0 losses vs fresh main build |

## Why official raw cannot move from data layout

Every data offset in matched windows now equals the original's. The 601 data-lddw windows that are still not raw
fail only because the section bases sit 0x140 higher: `.text` is 0x1b5a10 vs 0x1b58d0. That comes from the
unmatched windows' size deltas plus the extra 512-B `v2_native_payments::ensure_rent_exempt` unit (see
w6r1-layout-order), and `.rel.dyn` has two more entries (0x18050 vs 0x18030), which matches admin_cto's two extra vtable lddw (86 vs 84 data lddw). Once `.text` reaches the original size, the model gives
1019 raw (full original order) with the data as built here.
