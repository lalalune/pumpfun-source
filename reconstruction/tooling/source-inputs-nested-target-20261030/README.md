# Align source receipts with real staging

At base `6a1d23a306ce0b2213aac937d7a81472efe5986b`, the builder deliberately
stages nested directories named target. Its rsync exclusion is `/target/`,
not every directory with that name. However, `source_inputs.snapshot` prunes
all target directories before hashing or checking symlinks.

A real `src/lib.rs` module at `src/target/mod.rs` and an `include_bytes!` asset
at `assets/target/data.bin` are copied by the actual stager, but both can change
without changing its source receipt. A nested target directory symlink also
escapes the advertised symlink rejection.

Prune target only at the crate root, matching the existing stager. Keep Git
metadata exclusion, file checks, symlink rejection and the compiler recipe
unchanged. The new tests use actual rsync and filesystem links; no replacement
stager, mock filesystem or compiler is involved.

```sh
python3 -B reconstruction/harness/test_source_inputs.py
```

With the same nine tests, test-method commit
`083f1bd2e70fcc73be67111b9b96f6eb3f3a8393` (unmodified production code) gives
two failures. Source commit `a300c6857fdc9358475f56c28427e403dfba2ead` gives nine
passes. The two failures are the unchanged receipt despite real staged input
changes and the accepted nested symlink. The other seven controls continue
to pass. Before/after raw logs and exact source/test hashes are retained here.
A later packet-only commit preserves those tested leaves.

The actual current Pump tree contains 99 inputs and no target-named source
directory. Its complete old/new receipts are equal, digest
`889f4c6595381c3cb5de70398d09d073cf4365359f212f5c4ac05e0e6b107a43`. This fix
does not claim a changed current Pump input vector or bytecode gain.

`host-tools.json` identifies the real task-owned Debian rsync 3.4.1 and
APT-index-verified package archives used by both this proof and PR #2156.
Normal replay needs rsync on PATH. No system install or SDK/compiler change
was made. Current required capture/tooling gate results are reported in the
PR; the known analyzer-root test failure remains separately owned by #2103.

These are crate-tree receipts, not a complete Cargo/environment read-set or
a proof against every concurrent writer. No compiler, VM, new ELF or full
reproducibility/equivalence claim is made.
