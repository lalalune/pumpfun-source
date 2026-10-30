# Isolated fastbuild staging test loader

Current base `6a1d23a306ce0b2213aac937d7a81472efe5986b` runs this exact
workflow command in the `fastbuild-staging` job:

```sh
python3 -I -B tests/test_fastbuild_stage.py
```

The test's explicit fastbuild file loader cannot resolve the builder's newly
required sibling `build_process` and `source_inputs` modules. It exits with
`ModuleNotFoundError: build_process` before running any staging assertions.

Temporarily add the repository's exact harness directory while loading the
builder, then restore `sys.path`. Keep isolated Python mode and every existing
real-stage assertion. No production builder, source-receipt policy, compiler
flag, workflow or program input changes.

The same command passes all three existing cases at source commit
`f233246b3757d16c1a913427058e744b1adef99f`: nested source paths survive, root target
output is excluded, unchanged mtimes do not hide changed/deleted inputs, and a
regular file named target remains a source asset. These use the real rsync
process without a compiler or SDK. Before/after logs and source hashes are
retained here; a later packet-only commit preserves the exact tested leaf.

The host initially lacked rsync. Official Debian snapshot packages rsync and
libpopt0 were downloaded with APT into a task-owned directory, compared with
the package index SHA-256 values, and extracted without changing system or
SBPF toolchain files. `before.json` records exact package/binary identities.
The executed host uses rsync 3.4.1. Ordinary replay requires rsync on PATH;
other rsync versions or operating systems were not measured here.

Required saved-capture/tooling gate results are reported separately in the PR.
The known analyzer-root fixture failure is owned by PR #2103; this patch does
not copy that fix. No byte-match improvement, build result or runtime
equivalence is claimed.
