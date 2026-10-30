# Completion checkpoint, twelfth review pass — 2026-10-30

The fresh #2808 identity build preserves **1,034/1,035 Pump windows (99.90%)**,
all raw-equal, with no missing, added, resized or lost windows. Nested signer-seed
arrays preserve the same seeds while improving `admin_cto::execute` instruction-token
similarity from **45.177% to 45.267%** at 27,400 bytes. Its 3,308 differing slots
remain; this partial improvement adds no fully matched window.

Across all five maintained checkpoints, **3,337/3,338 windows (99.97%)** match,
covering **5,185,728/5,213,128 code bytes (99.47%)**. Only `admin_cto::execute`
(`0x22a10`) remains unmatched. Whole meaningful ELF equality remains **4/5**.

## Evidence and limits

- [summary.json](summary.json) records source, binary and runtime report hashes.
- [source-inputs.json](source-inputs.json) matches the merged program source tree.
- [baseline-score.json.gz](baseline-score.json.gz) is the fresh prior checkpoint;
  [score.json.gz](score.json.gz) records the fresh candidate and no-loss comparison.
- **771/771** paired synthetic runtime cases match: 363 signed admin-CTO cases,
  120 swap cases and 288 additional swap boundary cases, all on this candidate.
- Swap fixtures disable AMM PDA signature verification. These cases do not prove
  all successful post-complete, multihop or Token-2022 behavior or general runtime equivalence.
- The other four programs retain their [existing checkpoints](../completion-20261030/other-programs.json).
  No new build or native Linux qualification of them is claimed.
