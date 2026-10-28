# WIP snapshot (2026-10-28): main Pump Round37 composites 11

Pushed in a hurry, before a usage limit hit. **This is not a verified package.**
- **Not run:** the 44-suite regression, and the repository-builder control.
- **Measured:** everything here comes from the fastbuild identity recipe (Linux v1.44 sbpf target libraries, hybrid sysroot) and harness/score.py, scored against the Round37 identity build (749).

| directory | normalized / raw | notes |
|---|---|---|
| `integ-layout-r37-11/` | **905 / 165** | Synthetic layout (labelled `// layout-pad` positioning). +117 vs base r37g5, no losses, runtime_valid (no stack warnings). |
| `integ-genuine-r37-11/` | **813 / 165** | No padding. +25 vs r37g5, no losses, runtime_valid. |

Each composite contains:
- `src/`, the crate;
- `tools/`, the pipeline (`tools/pipeline_r37.sh`);
- `patch.diff`, against r37g5;
- `README.md`, with per-window attribution;
- the ELFs, as evidence.

Other directories:
- `lane-deliveries/`: round-4 lane deliveries on base L06 (integ-layout-r37-06). Each has its README, delivery.json and patch.diff; these are what composite 11 merged.
- `lanes/`: in-progress lane diffs against L06, plus PROGRESS.md logs. Nothing in them is delivered yet.
- `harness/`: build/score/package tools. They expect the work root at `~/Documents/Codex/2026-10-24/claude-pump-work`; `LANE-RULES.md` describes the lane protocol.

To promote:
1. Run `harness/mkpkg.py --name r37-layout-11 --src integ-layout-r37-11/src --base round37 --control …`, using the builder args recorded in the `pkgmeta/` and r37-layout-06 packages.
2. Run `harness/regress.sh r37-layout-11 4`.
3. Run `harness/add_regression.py r37-layout-11`.
4. Repeat steps 1-3 for genuine.
