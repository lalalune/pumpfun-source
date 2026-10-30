# Reconstruction toolchain

Everything needed to rebuild the main Pump program from `programs/pump` and compare
it, function by function, with the deployed original in
`evidence/original/pump/deployed.so`.

## Layout

| Path | Contents |
| --- | --- |
| `harness/fastbuild.py` | Builds a pump crate exactly like the verified builder (one-member workspace, `--locked --offline`, identity recipe). |
| `harness/score.py` | Official window scorer: an original window matches when a candidate function has the same size and the same bytes after masking only internal call immediates and section-pointer `lddw` values. `raw` means exact bytes. |
| `harness/win.py` | Window inspection: unmatched list, original/candidate disassembly and normalized diffs. |
| `harness/target_metric.py` | Per-window closeness: differing normalized slots, instruction ratio and call counts for a candidate build. |
| `harness/coords.py`, `triage.py`, `treediff.py`, `integrate.py` | Source-coordinate extraction, residual triage, tree diffs and multi-lane composition. |
| `harness/link_order.py`, `pump_link_rustc.py`, `pump_link_lld.py`, `sbf_default.ld` | Pinned link order: when the crate carries `link/ordered.ld`, fastbuild links the root cdylib with it instead of the SBF default script (input-section reordering only; see `pump-main/lanes/w8-sibling-recipes/NOTES.md`). |
| `harness/make_hybrid144.sh`, `harness/linux144-sbpf-target-libs.sha256` | Recipe and pins for the identity toolchain. |
| `toolchain/linux-v1.44-x86_64/` | The 25 `sbpf-solana-solana` target libraries from the official Linux x86_64 platform-tools v1.44 archive. |
| `toolchain/v1.44-macos-inventory.json` | SHA-256 of every file in the macOS arm64 platform-tools v1.44 SDK. |
| `toolchain/bootstrap.py` | Verifies the SDK, assembles the identity toolchain and prepares shared caches. |
| `base/functions.tsv` | The 1,035-window function inventory of the original; `base/original.so` links to the captured original. |
| `pump-main/` | Attempt ledger and protocol for matching the remaining main-Pump functions. |

## Setup

The tree-diff helper uses portable `/` paths in generated source patches. Its
Git patch round-trip tests run on Windows and POSIX with only Python and Git:

```bash
python reconstruction/harness/test_treediff.py
```

The macOS v1.44 SDK is not stored in git (its `librustc_driver` is 134 MB, over
GitHub's per-file limit). Install it once with `cargo-build-sbf --tools-version v1.44`
so it lives at `~/.cache/solana/v1.44/platform-tools`, then run:

```bash
python3 reconstruction/toolchain/bootstrap.py --warm
```

The bootstrap checks every SDK file against the inventory, assembles the "hybrid144"
identity toolchain (macOS v1.44 `rustc` with the Linux v1.44 `sbpf-solana-solana`
target libraries) and seeds a dependency cache. Generated files go to
`$PUMP_RECON_HOME` (default `~/.cache/pumpfun-reconstruction`), which every
worktree shares. The crates come from `~/.cargo/registry` (builds run offline).

## Build and score

The scorer reads candidate function symbols directly from the ELF without an SDK.
Disassembly tools select `llvm-objdump` from the installed v1.52 SDK first, then
the documented v1.44 SDK, then `PATH`. Set `PUMP_OBJDUMP` to an executable path
or command name to override disassembly tool selection.
An invalid explicit override fails rather than silently selecting another tool.
This selection does not change the compiler or the identity build recipe.

```bash
python3 reconstruction/harness/fastbuild.py --src programs/pump --work ~/.cache/pumpfun-reconstruction/work/me --out /tmp/pump-out
python3 reconstruction/harness/score.py /tmp/pump-out/unstripped.so --baseline reconstruction/pump-main/baseline/score.json
python3 reconstruction/harness/win.py show 0x14f4e0 --cand /tmp/pump-out/unstripped.so
```

The scorer reads `base/original.so` and `base/functions.tsv` on each call.
It ignores old `base/original-windows.pkl` files so an earlier read cannot
hide a changed window inventory or original image. Run the offline input-change
regressions with `python3 -B reconstruction/harness/test_score_inputs.py`.
The tests use temporary copies of the captured ELF and inventory; they do not
execute a program or establish a new reconstruction match count.

The pinned canonical source (`git archive e38a8b97a programs/pump`) reproduces
unstripped `0f50faa8c325104dc77898ed84866dec2ad1eec475b6abba72c475cf7bf9bab6` and
stripped `d0377d7cef5b7378063f8bfabac5dc9c08d29eeaaaaa14022d36909688ff5e1b`, scoring
1,019/1,035 normalized and 188 raw windows.

## Check source patch contents

Source patches must preserve the intended UTF-8 file bytes, including embedded
Unicode separators, CRLF endings and a missing final LF. Run the real patch-application
regressions without a compiler or Solana SDK:

```bash
python3 -B reconstruction/harness/test_treediff_line_boundaries.py
```
The composition helper `harness/integrate.py` also passes
`pump-main/baseline/score.json` explicitly when it invokes the scorer. Its gains
and losses therefore refer to this checked-in historical baseline, not an absent
`base/current/inventory.json` or a newly measured current-main build. Normalized
and raw scoring definitions are unchanged; the report is not an automatic
acceptance or runtime-validity gate.
If the required baseline file is missing, composition stops with an explicit
error before changing the output directory or invoking the builder or scorer. `--no-build` remains available
without a baseline file.

The baseline-argument regression can be checked without a compiler or scorer:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 reconstruction/harness/test_integrate.py
```

This test substitutes the builder and subprocess boundary with synthetic
in-memory results. It does not compile source, read ELF/cache/pickle data, run a
target program, or establish a new matched-window count.

## Gate saved score reports

After scoring a trial, compare its per-window memberships with the pinned baseline:

```bash
python3 reconstruction/harness/compare_scores.py reconstruction/pump-main/baseline/score.json /tmp/pump-out/score.json --json /tmp/pump-out/regressions.json
```

Exit status is 0 only when every normalized and raw membership is preserved and
both inventories have identical addresses and lengths; 1 means a regression or
inventory change, and 2 means malformed input. Gains cannot offset losses in other
windows. Both harness score reports and inventory-format window lists are accepted.
This gate checks saved results, not their provenance or the candidate binary itself.
