# Remove stale crate-local lockfiles during Pump staging

Tested base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

`fastbuild.stage` moves the admitted root `Cargo.lock` to the generated workspace
root. Its original rsync exclude both hid the source lock and protected any old
lock already in `programs/pump/Cargo.lock`. Staged-input validation then masked
that path as generated even though no crate-local lock was generated. Restaging
could therefore succeed with an additional unbound file visible in the crate.

The probe uses the production snapshot and stage helpers with actual rsync 3.4.1.
It stages one admitted source into two workspaces, adds a stale crate-local lock
only to the reused workspace, and stages that workspace again. Before the fix,
staging succeeds with unequal staged receipts and the extra lock intact. After
the fix, the fresh and reused staged receipts are equal and the old lock is gone.
The original source receipt is unchanged in both runs. See `before.json` and
`after.json` for the observations.

The root lock now uses a sender-only hide filter so the existing rsync `--delete`
can remove the stale destination. Staged-file validation masks only the generated
crate manifest; an unexpected crate-local lock is rejected. The admitted lock
continues to be written at the workspace root, and nested path-crate locks are
copied and checked normally.

Repeat with rsync available on PATH and an unused work directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research/staged-crate-lock-20261031/probe.py \
  --harness reconstruction/harness --work /tmp/staged-crate-lock-probe
PYTHONDONTWRITEBYTECODE=1 python3 -B reconstruction/harness/test_source_input_directories.py
```

The two new regression tests fail on the unchanged base and pass with the fix.
They check fresh/reused staging equality, preservation of the source and workspace
root lock, preservation of nested path-crate locks, and rejection of a lock added
after the real copy. The affected five-module source/staging suite passes 28 tests
with six platform/tool-availability skips in the test environment.

This proof covers source staging with a regular stale lock. It runs no program
compiler, SDK, scorer, target metric, VM or program ELF. No program source, build
recipe, captured evidence, current match count or byte-equivalence claim changes.
The fresh staging receipt is identical before and after the fix.
