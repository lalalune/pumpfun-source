# Preserve parallel validator inputs

`pump_validate_parallel.py` previously checked bound inputs before publishing
the aggregate report, but did not check whether an output *was* one of those
inputs. A successful `--validate-existing` invocation could replace its candidate,
compiler receipt, compiled source, captured original, runner, saved report or
saved loader receipt with report JSON and still exit zero. Atomic publication
does not prevent this: it atomically replaces the wrong destination.

The runner now checks all active publications before creating the retained
directory or starting workers. Execution checks the aggregate, failure report,
suite logs, suite JSON and captured-loader receipts. Revalidation writes only
the aggregate, so inactive execution sidecars are not rejected. The protected
set includes the build-bound files, compiled sources, selected suite scripts,
saved report and saved loader receipts. Canonical paths, symlinks (including
parent-directory links) and existing hardlinks are compared. An unrelated
existing report can still be replaced.

The same change synchronizes the loader receipt input inventory with the
current wrapper from PR #2422: `deployed.so` is already protected by both tools
and is now also included in the expected receipt dictionary. An actual
`set_creator` receipt containing 1,018 real loads was rejected by the previous
inventory with `loader inputs differ` and accepted with the complete inventory.

## Real workflow evidence

The input build is the public successful [run 41013070961](https://github.com/miracle2044/pumpfun-source/actions/runs/41013070961),
artifact `proof-41013070961-1` (ID 12958493959). Its build/source revision is
`8d9c088750e6005304d919fe71192ccea74aa42c`, distinct from the workflow controller
revision `98e1cbde5b3477b4166cc7ade9970fba4d8b856e`.

- Candidate SHA-256: `f8e03b83699a723a85e1b1aa22eb857987a65a85c5e14958e7c00b1287d37f46`.
- Unmodified build-comparison SHA-256: `de526314d7d9492227964583bfbd72a674973e206c2b730b4fcc3b794f1a6241`.
- All 111 staged compiled-source hashes matched that actual compiler receipt.
- Before tooling revision: `34836eea96bf5d50064e3b46abed35f74f67274e`.
- Fix base: `5586068`; the parallel runner at this base is byte-identical to
  the before runner. The current wrapper includes the #2422 inventory change.
- Environment: Ubuntu 22.04, CPython 3.12.14, solders 0.27.1, pyelftools 0.32.

The candidate and captured original were executed locally through real
LiteSVM, with the captured upgradeable-loader accounts. The control used shard
4 of 4, two workers: 11 suites, 2,605 cases and 2,605 diagnostic-log cases, with
zero diagnostic mismatches. Then seven revalidation invocations used each bound
input as `--output`. Every before invocation exited zero and changed that input.
Only private disposable copies were used and each was restored in `finally`.
The fresh after execution and noncolliding revalidation controls each passed
all 2,605 cases and 11 suites with zero diagnostic mismatches. All seven after
aliases exited one before publication, with unchanged input hashes. The retained
JSON summary records these before/after hashes and results; full runtime
reports contain local absolute paths and are not republished here.

## Repeat

Download the public artifact with `gh run download 41013070961 --repo
miracle2044/pumpfun-source --name proof-41013070961-1 --dir <artifact-directory>`.
In a disposable projection, export the recorded tooling revision's `scripts`,
`evidence/original`, `evidence/dependencies` and `evidence/upstream`. Export
`research/imported-lab/analysis/pump_fun/config-snapshot.json` and
`curve-fresh-trades-v3-signed-surfpool.json` from that revision too. Export
`programs/pump` from the build/source revision. Reproduce the builder's staging:
put the crate under `work/captured-loader-build/source/programs/pump`, move its
Cargo.lock to `work/captured-loader-build/source`, and move the release profile
and workspace section to the workspace manifest, as `pump_build_verified.py --workspace-layout` does.
Require every `source_sha256` entry in the unmodified build-comparison receipt
to match before executing. Decompress the artifact's candidate.so.gz and copy
the unmodified build-comparison.json into `work/captured-loader-build`.

```sh
python -B scripts/pump_validate_parallel.py \
  --candidate work/captured-loader-build/candidate.so \
  --source-directory work/captured-loader-build/source/programs/pump \
  --build-comparison work/captured-loader-build/build-comparison.json \
  --captured-loader --shards 4 --shard 4 --workers 2 \
  --output work/alias-proof/control.json.gz
```

Repeat that command with `--validate-existing work/alias-proof/control.json.gz`
and each input as `--output`, restoring its bytes after each before run. For
the after run, copy the fixed runner and current wrapper into the projection,
generate a **fresh** control, and repeat. Expect all seven aliases to fail with
`validation output aliases a bound input`, with all input hashes unchanged.
Do not use repository originals for destructive before reproduction.

Fast filesystem regression tests (including all active sidecars) are in
`test_input_preservation.py` and run in the evidence CI job. Required checks are
`python scripts/verify_evidence.py`, `python scripts/test_tooling.py`,
`python scripts/test_pump_validate_parallel.py` and the new test file.

This is input preservation for a finite local verification workflow. It is not
a filesystem race defense, full program equivalence or security clearance.
Historical captures, checkpoint bindings and previous research packets are
unchanged; see `proposed-asset-transition.json` for the new runner binding.
