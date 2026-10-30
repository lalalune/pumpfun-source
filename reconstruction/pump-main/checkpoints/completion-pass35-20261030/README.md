# Completion checkpoint, thirty-fifth review pass — 2026-10-30

The fresh reopened #2906 source proposal preserves **1,034/1,035 Pump windows
(99.90%)**, all raw-equal, with zero missing, added, resized or lost windows.
Its reordered independent curve-field reads and stores preserve the reviewed
behavior. `admin_cto::execute` instruction-token similarity improves from
**49.101% to 49.131%** at 27,400 bytes; **3,280** positional differences remain.
This partial gain adds no fully matched window.

Across all five maintained checkpoints, **3,337/3,338 windows (99.97%)** match,
covering **5,185,728/5,213,128 code bytes (99.47%)**. Only `admin_cto::execute`
(`0x22a10`) remains unmatched. Whole meaningful ELF equality remains **4/5**.

## Evidence and limits

- [summary.json](summary.json) records source, binary and runtime report hashes,
  the no-loss comparison and the semantic review.
- [source-inputs.json](source-inputs.json) matches all 137 merged program inputs.
- [baseline-score.json.gz](baseline-score.json.gz) retains the previous checkpoint;
  [score.json.gz](score.json.gz) records the freshly built candidate inventory.
- **771/771** paired synthetic cases pass on this candidate: 363 signed admin-CTO
  cases, 120 swap cases and 288 additional swap boundary cases.
- The retained exact-quote and multi-hop reference models keep their separate
  [1,014-case and 507-case evidence](../completion-pass16-20261030/README.md).
- Swap fixtures disable AMM PDA signature verification. These cases do not prove
  all successful post-complete, multihop or Token-2022 behavior or general runtime equivalence.
- The other four programs retain their [existing checkpoints](../completion-20261030/other-programs.json).
  No new build or native Linux qualification of them is claimed.
