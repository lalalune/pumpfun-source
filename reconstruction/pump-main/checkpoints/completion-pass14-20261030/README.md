# Completion checkpoint, fourteenth review pass — 2026-10-30

The fresh identity build retains **1,034/1,035 Pump windows (99.90%)** and
**3,337/3,338 aggregate windows (99.97%)**, all raw-equal. Matched code covers
**5,185,728/5,213,128 bytes (99.47%)**. The added exact-quote reference model
is not linked into the contract: the entire stripped and unstripped artifacts
are byte-identical to the [pass13 runtime-tested build](../completion-pass13-20261030/README.md).
Only `admin_cto::execute` remains unmatched: 48.742% instruction-token similarity,
27,400 bytes and 3,273 differing slots. Whole meaningful ELF equality remains 4/5.

## Evidence and limits

- [summary.json](summary.json) and [source-inputs.json](source-inputs.json) bind
  the current source tree, binary hashes and separate model verification.
- [score.json.gz](score.json.gz) retains the official inventory. The 771 paired
  synthetic cases from pass13 apply to the identical executable bytes.
- The separate exact-quote/crossing reference model passes **1,014 captured-original
  cases** (774 fixed and 240 seeded random), including settlement and event bytes.
  All five tests pass, including response-count and immutable-image checks.
- Account admission is assumed in the model; whitelisted mayhem resynchronization
  and explicitly marked unconfirmed budget-shrink paths remain outside its proof.
- These bounded results do not establish general runtime or whole-Pump identity.
  The [other four programs](../completion-20261030/other-programs.json) retain their
  prior exact-ELF checkpoints; none was newly rebuilt in this pass.
