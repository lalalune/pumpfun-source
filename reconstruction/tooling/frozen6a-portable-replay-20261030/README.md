# Frozen6a replay without symbolic-link privileges

The documented default offline replay of the newly published frozen6a checkpoint
failed on native Windows Python 3.12 with `WinError 1314`: its temporary input
projection required symbolic-link privileges. The original capture, frozen TSV
and optional toolchain inputs are now copied as regular files into the owned
temporary projection. All existing content authentication and scoring checks
remain in place.

| Actual CLI | Before | After |
| --- | --- | --- |
| Native Windows Python 3.12.13 | Exit 1, WinError 1314 | Exit 0, all 1,035 memberships verified |
| WSL Ubuntu Python 3.12.3 | Exit 0 | Exit 0, identical complete report |

`before-windows.stderr.txt` retains the original failure. `replay.json.gz` is the
canonical complete JSON report shared by the three successful runs (Linux before,
Windows after, Linux after). `measurement.json` binds its SHA-256, the source
transition and unchanged evidence hashes. Reports were parsed and compared in
full, including every membership, rather than only comparing their counts.

The replay remains the historical **6a1d23a** build: **1,027 normalized / 276 raw**.
This work performs no compilation, VM execution, current-main scoring or new
bytecode recovery. Optional physical SDK, registry and toolchain-input
qualification was not run. In particular, this does not qualify an authentic
macOS SDK's physical symlink layout on Windows.

## Reproduce

Use Python 3.12 from the repository root, or absolute paths for a standalone
copy of the checkpoint packet:

```sh
python -I -B reconstruction/pump-main/checkpoints/native-6a1d23a-20261030/verify.py \
  --original evidence/original/pump/deployed.so --report <new-report.json>
python -I -B reconstruction/pump-main/checkpoints/native-6a1d23a-20261030/test_verify.py
```

The new full-artifact regression disables symlink creation and still requires the
exact retained summary and all 1,035 memberships. The real captured original is
required: set `PUMP_CHECKPOINT_ORIGINAL` to its absolute path when outside the
repository. If no capture is available, that regression explicitly skips and the
eight rejection controls still run. Both native Windows and Linux runs here
passed all nine tests without skips.

Only the checkpoint's `verify.py`, `qualification.py`, `test_verify.py` and README
entries change in its source manifest. The other twelve entries, including the
ZIP, frozen inputs, Git proof, checkpoint metadata and historical receipts/logs,
retain their exact SHA-256 and byte counts. Historical replay records remain
records of their original tool version. The source changes and these new
measurements are separate from those prior records.

## Repository gates

`scripts/verify_evidence.py` passed all nine captures. The full
`scripts/test_tooling.py` run on base `7ca3235d` ran 178 tests and reported 24
failing subtests in the single existing method
`MayhemReceiptAdmissionTests.test_optimized_modes_refuse_before_checks_can_be_stripped`.
Its expected diagnostic is `requires unoptimized Python`, while the merged
verifiers exit with `Normal Python is required; do not use -O.`. These are
unchanged files outside this patch. An isolated projection of their exact base
Git bytes and the real Mayhem capture reproduces the same 24 failures; its
complete output is retained in `base-optimization.log.gz`. The full tooling
gate therefore remains failing on this unrelated base diagnostic mismatch.
No test or optimization guard was weakened to accommodate it.
