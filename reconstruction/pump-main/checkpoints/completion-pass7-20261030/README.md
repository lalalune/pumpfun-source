# Completion checkpoint, seventh pass — 2026-10-30

A fresh identity-recipe build of main `20a1ae9c0` preserves **1,033/1,035
windows (99.81%)**, all raw-equal, with zero normalized or raw losses against
the retained [sixth-pass score](../completion-pass6-20261030/README.md).
Source PR #2686 was already merged when this review began.

The `multi_hop_curve::swap_hop` window remains 18,584 bytes. Its instruction-token
similarity rises from **98.91% to 99.91%**, with **18 differing instruction
slots** remaining. This partial improvement adds no fully matched window.
`admin_cto::execute` (27,400 bytes) also remains unmatched.

Across all five maintained checkpoints, **3,336/3,338 windows (99.94%)** match,
covering **5,167,144/5,213,128 code bytes (99.12%)**. Whole meaningful ELF
equality remains **4/5**; Pump Main is not yet equal. Other program counts retain
their [existing provenance](../completion-20261030/other-programs.json).

## Retained evidence

- [summary.json](summary.json) records the source, binary and build-tool hashes,
  complete score comparison, partial window metric and runtime limits.
- [baseline-score.json.gz](baseline-score.json.gz) and [score.json.gz](score.json.gz)
  retain the complete official window inventories.
- [source-inputs.json](source-inputs.json) binds the freshly built source.
- **408/408** synthetic one-hop and reserve-boundary differential cases passed.
  The harness disables AMM PDA signature verification. These cases do not prove
  general successful post-complete, multi-hop or Token-2022 equivalence.
- No native Fees or Mayhem compiler was rerun in this pass. Their existing
  checkpoint claims are not expanded by these Pump or tooling checks.

Build and scoring tool hashes refer to the source revision above. The later
scorer admission fix rejects symbol-free candidates; the final merged-tree
check scores this same unstripped candidate again.
