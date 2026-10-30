# Completion checkpoint, eleventh review pass — 2026-10-30

A fresh identity build of #2766 plus #2792 matches **1,034/1,035 Pump windows
(99.90%)**, all raw-equal. The swap-hop window at `0x5b3b0` adds **18,584
matched bytes**, with zero normalized or raw losses against a fresh baseline.
The only unmatched window is `admin_cto::execute` at `0x22a10` (27,400 bytes).
Its instruction-token similarity is **45.177%**, with 3,308 differing slots.

Across all five maintained checkpoints, **3,337/3,338 windows (99.97%)** match,
covering **5,185,728/5,213,128 code bytes (99.47%)**. Whole meaningful ELF
equality remains **4/5**. Other programs retain their
[existing provenance](../completion-20261030/other-programs.json).

## Evidence and limits

- [summary.json](summary.json) binds source, binary and tool hashes and the no-loss comparison.
- [source-inputs.json](source-inputs.json) records exactly what was built.
- [baseline-score.json.gz](baseline-score.json.gz) and [score.json.gz](score.json.gz)
  retain the complete official window inventories.
- **771/771** paired synthetic runtime cases match: 363 signed admin-CTO cases,
  120 swap cases and 288 additional swap boundary cases. The selected tuple
  spelling produces the same complete ELF bytes as the runtime-tested helper spelling.
- Swap fixtures disable AMM PDA signature verification; they do not establish
  all successful post-complete, multihop or Token-2022 behavior.
- These checks do not establish general runtime equivalence or Pump whole-ELF identity.
  No new build or native Linux qualification of the other programs is claimed.
