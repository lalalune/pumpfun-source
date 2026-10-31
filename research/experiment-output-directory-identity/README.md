# Retained experiment output directory identity

Source baseline: `963d1eefbed3a81a51d2d52f80026c5434a7a423`.

## Observed defect

`reconstruction/harness/EXPERIMENTS.md` says a pass/fail result is reused only
when retained artifacts still match. The runner hashes files but omitted
directory entries. A real child command creates `output/cache/empty/` and an
unchanged result file, then exits 0 or 1. Removing, renaming or adding an empty
directory in that retained output tree left its artifact map unchanged. The
next `run_trial` returned `reused=true` instead of producing a new attempt.
Thus a reusable result could refer to an output layout no longer retained.

The focused regression uses actual child processes, not mocked launch or
artifact functions. Its six subcases (three mutations for each reusable exit
status) fail on the baseline (`before.log`). The fix records directory
membership with trailing-slash keys and `{"directory": true}` entries; file
hashes/executable bits and link/special-file rejection stay intact. Unchanged
trees reuse successfully before and after mutation recovery. Previous attempts
are preserved.

## Reproduction and checks

From the repository root on Ubuntu/WSL2 with Python 3.12:

```sh
python3 -m unittest discover -s reconstruction/harness -p test_experiment_output_directories.py -v
python3 -m unittest discover -s reconstruction/harness -p 'test_experiment*.py' -v
python3 -m unittest discover -s reconstruction/harness -p 'test_bisect*.py' -v
python3 -m unittest discover -s reconstruction/harness -p 'test_minimize*.py' -v
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

To reproduce the failure, apply just the new test to the baseline and run the
same focused command. `after.log` records 54 experiment tests: 52 pass and two
environment-dependent skips (an explicit SBF SDK/host rustc probe and an ASCII
text locale with UTF-8 filesystem control). Related bisect tests pass 5/5 and
minimizer tests pass 8/8. Captured evidence authentication passes all nine
captures (`verify-evidence.log`). Required tooling-suite outcome is recorded
in `results.json`; it must not be inferred from the focused tests.

Initial validation on the Windows-mounted filesystem hit seven unchanged
analysis-publication failures because Linux `renameat2(RENAME_NOREPLACE)`
returned `EINVAL`. Native Linux scripts/tests fixed that filesystem issue.
A subsequent setup attempt linked captures from outside the native root and
hit an existing fixture-path assumption. Local pinned evidence and program
files were then copied into the native root before the final required run.
These setup failures do not alter the captured bytes or production code.

## Scope and limits

This is reconstruction experiment-cache tooling, allowed by CONTRIBUTING.md.
It changes no program source, build inputs, score, original binary, capture,
acceptance threshold or reconstruction claim. No program score gain is claimed
and no new program build is required for this tooling-only change. Focused
tests execute only synthetic Python commands. The repository-wide tooling
suite also includes offline runtime controls and is reported separately.

Related PR #2399 admits the output root and rechecks retained files, #2922
tracks empty source directories, and open #3441 rejects output junctions.
Those address different omissions; this change records ordinary output
directory membership. Live searches for experiment/output-directory work found
no matching fix. The runner's existing source fingerprint changes naturally,
so old results are not silently reused under the new artifact representation.
These hashes are integrity checks, not signed or tamper-proof provenance.
