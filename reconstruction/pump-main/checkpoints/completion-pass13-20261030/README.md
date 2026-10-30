# Completion checkpoint, thirteenth review pass — 2026-10-30

The fresh #2831 identity build preserves **1,034/1,035 Pump windows (99.90%)**,
all raw-equal, with no missing, added, resized or lost windows. The admin-CTO
refinement retains #2808's nested signer seeds and improves instruction-token
similarity from **45.267% to 48.742%** at the original 27,400-byte size.
Differing instruction slots fall from **3,308 to 3,273**. This partial improvement
adds no fully matched window.

Across all five maintained checkpoints, **3,337/3,338 windows (99.97%)** match,
covering **5,185,728/5,213,128 code bytes (99.47%)**. Only `admin_cto::execute`
(`0x22a10`) remains unmatched. Whole meaningful ELF equality remains **4/5**.

## Evidence and limits

- [summary.json](summary.json) records source, binary and runtime report hashes,
  the no-loss comparison and semantic review. All 20 error/message macro sites
  retain their original source line numbers.
- [source-inputs.json](source-inputs.json) matches the merged program source tree.
- [baseline-score.json.gz](baseline-score.json.gz) retains the prior fresh checkpoint;
  [score.json.gz](score.json.gz) contains the fresh candidate inventory.
- **771/771** paired synthetic runtime cases match on this candidate: 363 signed
  admin-CTO cases, 120 swap cases and 288 additional swap boundary cases.
- Swap fixtures disable AMM PDA signature verification. These cases do not prove
  all successful post-complete, multihop or Token-2022 behavior or general runtime equivalence.
- The other four programs retain their [existing checkpoints](../completion-20261030/other-programs.json).
  No new build or native Linux qualification of them is claimed.
