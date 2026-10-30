# Completion checkpoint, sixteenth review pass — 2026-10-30

The fresh identity build preserves **1,034/1,035 Pump windows (99.90%)** and
**3,337/3,338 aggregate windows (99.97%)**, all raw-equal. Matched code covers
**5,185,728/5,213,128 bytes (99.47%)**. Both recovered reference models remain
outside the contract module graph: the full stripped and unstripped artifacts
match the [runtime-tested pass13 build](../completion-pass13-20261030/README.md).
Only `admin_cto::execute` remains unmatched: 48.742% instruction-token similarity,
27,400 bytes and 3,273 differing slots. Whole meaningful ELF equality remains 4/5.

## Evidence and limits

- [summary.json](summary.json) and [source-inputs.json](source-inputs.json) bind
  the current source tree, binary hashes and separate model verification.
- [score.json.gz](score.json.gz) retains the official inventory. The 771 paired
  synthetic runtime cases apply to the identical executable bytes.
- The separate exact-quote reference model passes **1,014 captured-original cases**.
- The separate multi-hop reference model passes **507 captured-original cases**:
  444 successes and 63 errors, including rollback checks. Its seven tests and two
  optimized-mode controls cover strict response counts, immutable images, all
  returned curves, and observable balances including shared destinations.
- The multi-hop fixture uses direct Pump calls with signature checks disabled for
  an AMM PDA slot; it is not a genuine outer AMM CPI. It uses SPL Token and does
  not compare events, compute units, Token-2022 or every account-admission/fee variant.
- These bounded results do not establish general runtime or whole-Pump identity.
  The [other four programs](../completion-20261030/other-programs.json) retain their
  prior exact-ELF checkpoints; none was newly rebuilt in this pass.
