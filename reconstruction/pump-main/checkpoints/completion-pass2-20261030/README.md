# Completion checkpoint, second pass — 2026-10-30

Pump Main now matches **1,033/1,035 windows (99.81%)**, all **1,033 raw-equal**.
The combined source from #2529 and #2524 was built with the maintained identity
recipe and compared to a fresh main `43daa2043` build. It adds the `create_v2`
window at `0x1e7c0` and **686 raw matches**, with **zero normalized or raw losses**.
The final merged source also includes #2558's swap-window refinement; it
preserves all memberships while improving the remaining window's local
comparison. The merged source snapshot equals the tested final candidate.

Two windows remain unmatched: `admin_cto::execute` (`0x22a10`, 27,400 bytes)
and `multi_hop_curve::swap_hop` (`0x5b3b0`, 18,584 bytes). Exact function size
alone does not establish a body match, and Pump Main still lacks whole
meaningful ELF identity.

Across the five maintained checkpoints, **3,336/3,338 windows (99.94%)** match,
covering **5,167,144/5,213,128 code bytes (99.12%)**. The other four program
counts and their distinct verification limits are retained from the
[earlier checkpoint](../completion-20261030/other-programs.json).

## Retained evidence

- [summary.json](summary.json): source/build/tool hashes, gains and counts.
  Actual build-harness hashes are separate from final verification-tool hashes.
- [baseline-score.json.gz](baseline-score.json.gz) and [score.json.gz](score.json.gz):
  complete official per-window censuses before and after the source changes.
- [source-inputs.json](source-inputs.json): complete built source inventory.
- [runtime-summary.json](runtime-summary.json): 110 creation, 303 extended
  create-v2 and 363 admin-CTO cases, plus 120 single-hop swap fixtures and
  288 reserve-boundary cases, all matching the captured original. Creation
  and admin cases use signed synthetic transactions; swap cases disable
  AMM PDA signature verification. These do not prove general runtime identity
  or full successful post-complete/multi-hop behavior.
- [tooling-validation.json](tooling-validation.json): 33 suites rerun on the
  merged tooling tree, including shared comparators, input preservation,
  roadmap source pins, relocation handling and binary tree diffs.

To reproduce, build `programs/pump` with `reconstruction/harness/fastbuild.py`
using `--recipe identity`, then invoke `reconstruction/harness/score.py` with
a freshly built main report as `--baseline`. The runtime comparisons use
`scripts/pump_create_v2_differential.py`,
`reconstruction/pump-main/lanes/create-native-quote-input/replay.py` and
`scripts/pump_admin_cto_differential.py`, each with `--candidate` pointing to
the built stripped ELF and `--output` pointing to a new report.
