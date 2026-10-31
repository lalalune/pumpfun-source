# Completion checkpoint — 2026-10-31

Source #3666 improves `admin_cto::execute` token similarity from **67.346% to 67.376%**, at the same 27,400 bytes and 3,124 positional differences. The fresh identity build retains **1,034/1,035 raw and normalized Pump matches (99.90%)**, with zero losses and no new exact window.

Across all five maintained checkpoints, **3,337/3,338 windows (99.97%)** and **5,185,728/5,213,128 code bytes (99.47%)** match. Whole meaningful ELF equality remains **4/5**. Pump's remaining window is `admin_cto::execute` at `0x22a10`.

All **388 signed synthetic admin CTO cases** were rerun against this freshly built candidate and match the captured original, with genuine dependency CPIs. This remains bounded runtime evidence, not whole-program equivalence.

- [summary.json](summary.json) records actual build/validated revisions, binary hashes, no-loss scoring and limits.
- [source-inputs.json](source-inputs.json) seals all 263 Pump inputs.
- [semantic-review.json](semantic-review.json) independently checks field-copy semantics, macro coordinates and call ordering.
- [score.json.gz](score.json.gz), [baseline-score.json.gz](baseline-score.json.gz) and [admin-runtime.json.gz](admin-runtime.json.gz) retain complete evidence.
- Unlinked reference models do not add compiled completion. The other four programs retain their [existing checkpoints](../completion-20261030/other-programs.json); no fresh build of them is claimed here.
