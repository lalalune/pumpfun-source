# Completion checkpoint, tenth review pass — 2026-10-30

A fresh identity build of #2749 preserves **1,033/1,035 windows (99.81%)**,
all raw-equal, with no normalized or raw losses against a fresh main
`4cc7946e7` build. The `admin_cto::execute` window remains 27,400 bytes;
its instruction-token similarity improves from **43.92% to 45.15%**, and
its positional differing slots decrease from **3,352 to 3,308**.
This partial improvement adds no fully matched window.

Two windows remain unmatched: `admin_cto::execute` (`0x22a10`, 27,400 bytes)
and `multi_hop_curve::swap_hop` (`0x5b3b0`, 18,584 bytes). The swap window is
unchanged, with 18 differing instruction slots. Independent measurement of
the accepted candidate finds 47 raw and normalized differing bytes in the
same cluster at window offsets `0x29f9..0x2a84`; see the
[residual packet and its limits](../../../../research/swap-hop-residual-20261030/README.md).

Across all five maintained checkpoints, **3,336/3,338 windows (99.94%)** match,
covering **5,167,144/5,213,128 code bytes (99.12%)**. Whole meaningful ELF
equality remains **4/5**. Other program counts retain their
[existing provenance](../completion-20261030/other-programs.json).

## Evidence

- [summary.json](summary.json) records source, binary and tool hashes,
  the no-loss comparison, partial metrics and runtime limits.
- [source-inputs.json](source-inputs.json) binds the source that was built.
- [baseline-score.json.gz](baseline-score.json.gz) and [score.json.gz](score.json.gz)
  retain the complete official window inventories.
- **363/363** signed synthetic admin-CTO cases match the captured original,
  including genuine dependency CPIs. They do not establish general runtime
  equivalence or whole-program identity.
- Build/scoring tool hashes refer to the fresh baseline revision above.
  Final merged-tree scoring is checked separately against that baseline.
- No new native Linux qualification or build of the other programs is claimed.
