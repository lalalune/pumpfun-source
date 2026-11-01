# Opt-in reconstruction disk budgets

Heavy reconstruction builds can share one APFS volume with several worktrees,
warm targets, compiler intermediates and retained receipts. The disk-budget
guard rejects or stops an owned operation when live filesystem-reported bytes
available to the current user fall below a configured floor.

The mode is opt-in. Existing unguarded command lines, recipes, target identities
and scorer behavior remain unchanged.

## Fastbuild

```bash
python3 reconstruction/harness/fastbuild.py \
  --src /path/to/programs/pump \
  --work /path/to/build-work \
  --out /path/to/output \
  --min-free-bytes 21474836480 \
  --disk-check-interval 1
```

Work and output filesystems are always selected when the option is enabled.
Use repeatable `--disk-path` arguments for another relevant volume, such as a
separate toolchain or cache volume. Paths may not exist yet; their existing
filesystem root is admitted without creating the requested target.

Admission occurs before rsync staging. Further checks occur after staging,
before target setup/compilation, during Cargo, and after compilation before
binary publication. A runtime crossing asks `build_process.py` to stop only
the compiler process group it created. Compiler output remains in `build.log`.
No cache or worktree is removed.

Every guarded attempt returns `resource_receipt`. Receipts live under the
workspace's `resource-receipts/attempt-*` directory, so a new failure cannot
overwrite an earlier receipt. Previous canonical binaries follow fastbuild's
existing preservation rule: attempts that reach compilation archive them under
`output/previous/build-*`; failures before publication install no candidate.

`build_score_pair.py` accepts the same three options and passes one immutable
configuration to its sequential base and candidate builds.

## Bounded experiments

```bash
python3 reconstruction/harness/experiment_runner.py matrix.json \
  --out /path/to/trials \
  --max-trials 20 \
  --min-free-bytes 21474836480 \
  --disk-check-interval 1
```

The matrix filesystem is admitted before the first trial. Each trial then
binds its destination filesystem and budget identity into the experiment cache
key. Admission is repeated before source staging, after staging, during the
owned process, and before result publication.

A crossed floor or unavailable measurement is `status: "error"`, never the
valid-negative `status: "fail"`. Its attempt remains immutable and is not
reused. Rerunning with unchanged inputs after storage recovers creates a new
attempt; completed pass/fail results are reused only when the resource receipt,
budget identity, experiment key and retained artifacts independently verify.
PR #4044's interrupted-attempt and parent-death recovery semantics remain in
effect.

## Receipt verification

```bash
python3 reconstruction/harness/resource_budget.py \
  /path/to/resource-receipt.json
```

The verifier recomputes observation order, filesystem membership, floor
classifications, minimum observed bytes, guard evidence, failure/outcome
consistency and implementation identity. Harness consumers additionally bind
the expected source/build or experiment identity. Producer summary booleans
are not trusted.

Receipts distinguish:

- measured available bytes at each phase;
- the configured floor and sampling interval;
- every selected filesystem device and path;
- minimum observed free bytes per filesystem;
- guard and measurement failures;
- build/tool or experiment identity;
- candidate publication state; and
- retained diagnostic log paths.

## Safety and limits

The measurement is `statvfs().f_bavail * f_frsize`, not a sum of logical file
sizes and not an estimate of recoverable APFS clone/cache storage. The guard
does not reserve bytes, remove caches, kill unrelated processes, protect
detached hostile processes, or guarantee survival of sudden external disk
consumption, filesystem failure or a whole-system crash. Choose a floor with
headroom for concurrent system activity.

Failure-path tests inject measurements and run tiny bounded child processes;
they never fill the host filesystem. See `DISK_BUDGET_GAP.md` for the audited
pre-change boundaries.
