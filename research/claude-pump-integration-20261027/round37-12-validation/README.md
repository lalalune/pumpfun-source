# Round37 composite 12: completed validation

The two snapshot binaries were rebuilt with the archived `fastbuild.py`
identity recipe (`sbpf-solana-solana`, native macOS v1.44 compiler with Linux
v1.44 target libraries). Both stripped and unstripped outputs repeat exactly.
The builds reuse external dependencies and force recompilation of the Pump
crate; they are not fresh dependency builds. Neither reports an oversized
stack frame. The bounded 44-suite captured-loader corpus passes separately
for each exact binary: 10,468 cases, 10,464 paired diagnostic logs, no mismatches.

`identity-genuine/` and `identity-layout/` retain the build result, build log,
source-bound corpus input record, full regression output and manifest. The
staged-source hashes can be reconstructed from the archived input crates:
`fastbuild.py` moves the release profile to the workspace manifest without
changing Rust, IDL or lockfile bytes. The corpus input record is explicitly a
record of this fastbuild invocation, not a repository-builder receipt.

The separate `r37-genuine-12/` and `r37-layout-12/` packages use the repository
builder's `linux-v1.44-sbf` profile and preserve their own unchanged-source
controls. Their counts are 808/147 and 902/147; the snapshot recipe's counts
are 813/165 and 907/165. The layout variants contain synthetic source-line
positioning. These are research packages, not maintained-source promotion,
historical-source proof, complete runtime coverage or whole-ELF equality.

From the repository root:

```sh
python3 -I -B research/claude-pump-integration-20261027/verify_round37_12.py
python3 -I -B research/claude-pump-integration-20261027/test_round37_12.py
```

The first command checks package manifests, sources, build bindings, independent
window inventories and all four full regression reports. The second exercises
rejection of missing suites, altered counts, rebound candidates and mismatches.
Both run offline without compiling or executing a target program.
