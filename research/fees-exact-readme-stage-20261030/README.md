# Fees exact-source staging: stale research README pin

The public Fees builder rejected its own retained research README before it
could compile. At `d01d64aa7f6abfd864fdc157552cd36bf73728a5`, the real
`programs/pump-fees/build_exact.py::stage` raised:

```text
ValueError: canonical input changed: programs/pump-fees/README.md
```

The entire Fees subtree is unchanged at the publication base
`1cacecfbf9a58b698f99d5e11d6723a254588b81`. The builder maps that logical
README name to `programs/pump-fees/exact/research-README.md`. Its actual SHA-256
is `cce346bd98b407907bddb55fb14f2580464bcbf521c2f71d0ca0426b4304bc6e`;
the inventory still expected
`4bfba2b9f43bfa49440bcd31799b4cd212c08509b0a3b96ff84f1a9589101dc9`.
The correction changes exactly that one value in
`programs/pump-fees/exact/qualified-source-inputs.json`. The other 64 input
hashes and all input contents remain unchanged.

## Source and build boundary

The unchanged builder is SHA-256
`6fffc0c2d0eedf2e84541445c6a388092accb6bf3371e159acc851bc397a92b8`.
The README itself is unchanged, Git blob
`68aa1d57131f704bdd99d980946c30e1f83a11b2`.
Review of the 52 local Rust files found no README consumption and no
`include_str!` or `include_bytes!` use. There are no local `build.rs` files;
the vendored macro crate explicitly sets `build = false` and `readme = false`.
The other package manifests provide no custom build script or README-content
consumer. The recipe uses `cargo rustc --lib`, without packaging or documentation
generation. `FIXED-STAGE.json` records the reviewed manifests and source hashes.

This repairs the source-provenance gate, without changing Rust, Cargo manifests,
the linker script, toolchain, flags, dependency inputs, output processing or
historical expected ELF hashes. **Only source staging was executed.** No cold
build, new ELF equality, runtime equivalence, window gain or security conclusion
is claimed. Historical whole-ELF receipts are not retargeted to this correction.

## Replay from this public tree

Use Python 3.11 or newer. No SDK, Cargo, container, network or original executable
is needed. From the repository root, choose a **new** task-owned output path:

```bash
python3 -B research/fees-exact-readme-stage-20261030/replay.py \
  --repo . --output 'work/fees staging replay'
python3 -B research/fees-exact-readme-stage-20261030/test_stage.py
sha256sum -c research/fees-exact-readme-stage-20261030/SHA256SUMS
```

The producer resolves `--repo` and `--output` explicitly and works with paths
containing spaces. It rejects an existing output directory. It copies the current
program inputs into owned staging, restores the retained old inventory only in
that copy, and checks the original README failure. It then calls the same builder
with current inputs and checks all 65 staged files. The sole pre-existing staged
workspace macro-locator substitution is checked explicitly. Repository inputs
are hashed before and after. Partial baseline output, traceback, fixed source
and `RESULT.json` are retained below the chosen output path.

The four regression tests exercise the real staging function: current inputs
succeed; changed README bytes, changed Rust bytes and an unreviewed canonical
package-manifest change are rejected. They use temporary owned copies, including
paths with spaces, and leave repository inputs unchanged.

## Retained observations

- `ORIGINAL-PINS.json`, `ORIGINAL-STAGE.json` and `original-stage.log` preserve
  the original pin, all 65 authenticated public input mappings, 64 matching
  hashes and the actual pre-fix failure. Absolute paths in the historical raw
  traceback describe that run; the replay has no dependency on those paths.
- `FIXED-STAGE.json` preserves the first successful source-stage observation
  and non-consumption review on the d01 input cohort.
- `PORTABLE-REPLAY.json` and `portable-replay.log` record the explicit-root,
  spaces-in-output replay at the unchanged Fees inputs on the publication base.
- `focused-tests-original.log` preserves the initial four-test observation with
  the test temporarily placed under `scripts/`. The same-PR follow-up moves that
  tooling into this packet as required by `scripts/README.md`, adjusts only its
  repository-root locator and CI/docs references, and reruns the four tests;
  `focused-tests.log` records that run. No existing root script or script-set
  guard is changed. These observations concern staging only. Later gate results
  are reported with their exact PR head.

`CHECKS.json`, `REQUIRED-GATE-INPUTS.json` and the two official gate logs record
the publication-base checks with every read input authenticated to that Git tree.
Evidence verification passes all nine captures. The unchanged tooling gate runs
40 tests and reports three errors from its existing interface-inventory fixture:
it copies only Mayhem, then calls `analyze()` with a patched `ROOT`, but
`program_names(root=ROOT)` retains its earlier full-repository default. The
first Pump binary is absent from that temporary fixture. This failure is
preserved and is not a Fees staging failure or a passing required gate.

The new `fees-exact-source-staging` CI matrix entry runs these four focused tests
and the explicit-root replay. Unchanged historical Fees runtime/canonical suites
reference removed research/repro packages in this public tree; they were not
restored or represented as passing here. No program source changed.

The older README prose and historical research references are retained as-is;
this packet does not restore or qualify their removed support packages.
