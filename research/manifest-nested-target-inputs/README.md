# Bind nested source and asset directories named target

`build_source_manifest.source_manifest` removed every candidate with a path
component named `target`, including `src/target/checkpoint.rs`. The production
`strict_manifest` also lost these inputs because its admission callback only sees
files selected by that inventory. Changing such a source left the manifest
unchanged. An explicitly supplied asset directory had the same omission for
`layout/target/mayhem-header.bin`.

The source walker now excludes the walked root's `target/` build directory,
while preserving nested `target/` source and assets. `.git` remains excluded at
every depth. This matches the current `fastbuild.stage` rule, whose comment and
`rsync --exclude /target/` explicitly preserve nested target source directories.
The staging correction was merged as `b4c720264` (PR #1531); this transition fixes
the independent manifest omission, without editing staging or receipt code.

This is a proposed one-script asset transition, bound by `transition.json`.
Historical capture data, packages, manifests and their source hashes are not
rewritten. A historical package pinning the previous script must be replayed at
its own recorded revision; it is not re-certified for this source revision.
The root Python script set is unchanged; the new regression lives in `tests/`.

## Real filesystem workflow

```
python -I -B -X utf8 tests/test_manifest_nested_target.py
python -I -O -B -X utf8 tests/test_manifest_nested_target.py
python -E -B -X utf8 scripts/test_build_source_manifest.py
python -E -B -X utf8 scripts/test_source_manifest_guard.py
python -E -B -X utf8 scripts/verify_evidence.py
python -E -B -X utf8 scripts/test_tooling.py
```

The regression copies the actual `crates/native-transfer-fee` reconstruction
crate into an owned temporary repository. Its existing library explicitly
selects a copied source through Rust's `#[path = "target/checkpoint.rs"]` module
attribute. The selected module is the retained fee implementation (only the
crate-level `no_std` attribute is omitted for the module copy). The test changes
its basis-point constant from 10,000 to 10,001 and checks its independently
computed source digest changes in both ordinary and guarded manifests.

The asset control uses two consecutive 64-byte blocks from the real retained
Mayhem ELF under an explicit asset directory. Both binary changes must affect
the manifest. Root build output and nested Git metadata remain excluded.
On the base, two tests fail because these source/asset keys are absent. After
the transition, all three methods pass normally and under `-O`. The existing
two source-manifest regressions and all nine saved captures also pass.

The existing symlink guard test cannot create its fixture on this Windows host
(`WinError 1314`, symlink privilege unavailable), before exercising the guard.
The full tooling suite was attempted with the exact pinned requirements but
fails at import: official Windows solders 0.27.1 lacks native `FeatureSet` needed
by `solders.litesvm`. No fake runtime or symlink implementation was substituted.

## Limits

The current tracked native-transfer-fee crate has no nested `target/` module;
the demonstrated omission uses its real source in an explicit local module
layout. No compiler, Cargo, SBF SDK, VM or deployed program is executed, and no
fresh source equivalence or match-count improvement is claimed. A source
manifest still inventories known inputs rather than proving hermetic Cargo
resolution. Independently generated nested `target/` directories are now
inventoried if included in the selected source or explicit asset tree.
