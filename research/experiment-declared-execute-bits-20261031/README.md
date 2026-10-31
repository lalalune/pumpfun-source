# Declared experiment input execute permissions

On base `ebe5387e12e948c2534618adf7a3cf0f27d9de51`, a real experiment matrix
reuses a pass after its declared shell helper changes from mode `0755` to
`0644`, even though the same command at a fresh destination returns an
infrastructure error. The helper bytes, command and environment are unchanged.
The same mismatch affects cached failing predicates and removing only the
owner execute bit (`0755` to `0655`, for a non-root owner).

The runner hashes declared input contents but does not bind their execute
permission bits. Its existing source and retained-output checks already track
executable metadata. This change adds a separate `input_execute_bits` map of
`st_mode & 0o111` for the command executable and declared inputs. It is included
in admission identity, non-command input refresh after the destination lock,
and reuse, pre-launch and post-run checks. The existing input hash strings stay
unchanged. The runner fingerprint makes earlier cache keys ineligible for reuse;
previous attempt directories remain unchanged. A write-bit-only change still
reuses a valid attempt.

Run the regression from the repository root:

```sh
python3 -B tests/test_experiment_input_modes.py -v
```

The matrix cases invoke the CLI and execute a real shell helper using Python's
subprocess API. They compare resumed and fresh runs and verify that prior
attempt files remain unchanged. A real helper also removes its own execute
permissions before returning zero; the runner must retain an error result.
Supplemental pre-launch and lock-wait cases use deterministic synchronization
around real filesystem copying/admission; child execution and receipts are not
mocked.

On macOS 27.0.1 arm64 with CPython 3.12.13, the new suite reports seven failing
subcases across four methods on the unchanged base, then all five methods pass
with this change. Existing experiment tests run 53 tests (52 pass, one explicit
SBF-SDK-dependent skip); bisection tests pass 5 and minimizer tests pass 8.
Required `scripts/test_tooling.py` passes 228 tests and
`scripts/verify_evidence.py` verifies all 9 captures. Compact raw CLI results,
commands, source hashes and test summaries are in [results.json](results.json).
The existing `tests/` discovery job runs the new regression.

This is a POSIX execute-bit cache correction, measured on macOS. It does not
bind ownership, ACLs or read/write bits, and is not a hermetic execution or
concurrent-mutation guarantee. No SBF compiler, program build, score change,
Linux/Windows test result or hosted CI result is claimed. Program source,
original captures and historical receipts are unchanged.

Source and ownership checks, accessed 2026-10-31:

- Repository contributors, [base experiment runner](https://github.com/lalalune/pumpfun-source/blob/ebe5387e12e948c2534618adf7a3cf0f27d9de51/reconstruction/harness/experiment_runner.py) and [experiment contract](https://github.com/lalalune/pumpfun-source/blob/ebe5387e12e948c2534618adf7a3cf0f27d9de51/reconstruction/harness/EXPERIMENTS.md).
- Python Software Foundation, [chmod documentation](https://docs.python.org/3.12/library/os.html#os.chmod) and [subprocess exceptions](https://docs.python.org/3.12/library/subprocess.html#exceptions).
- [Open PR #3487](https://github.com/lalalune/pumpfun-source/pull/3487) concerns retained output directory membership; [#3505](https://github.com/lalalune/pumpfun-source/pull/3505) concerns unreadable retained output traversal. Their output-artifact changes are separate from this declared-input metadata fix.
- [Merged PR #2730](https://github.com/lalalune/pumpfun-source/pull/2730) retains post-run validation exceptions. It does not add missing execute-bit comparisons.
