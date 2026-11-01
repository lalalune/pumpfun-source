# Reconstruction disk-budget gap

Audited against upstream `e89d79aa8d0ad61cefa99b614390eca13500a743`.

## Existing boundaries

`fastbuild.py` authenticates source inputs, serializes work and output paths,
archives prior outputs, owns compiler process groups through `build_process.py`,
and publishes binaries only after a successful compiler and strip step. It does
not measure available storage before rsync staging, warm-target cloning, Cargo,
strip, or publication. A filesystem-full failure is therefore reported as a
generic staging/compiler/publication failure.

`experiment_runner.py` durably records staging, running, interrupted, completed,
and published attempts. PR #4044 added parent-death cleanup and crash recovery.
It has no storage admission or runtime sampling. Exit 1 is a valid negative
experiment, while other exits and timeouts are infrastructure errors; a storage
guard must preserve that distinction and PR #4044's attempt states.

`build_score_pair.py` delegates its two cold builds to `fastbuild.py`; it has no
independent storage protection. A shared fastbuild option can protect both
workspaces without changing scoring.

The Donation Relay native replay packet contains a local `os.statvfs` guard.
It proves that `f_bavail * f_frsize` and owned-process-group termination are
practical, but its fixed receipt fields, fixed floor label, and package-local
launcher are not reusable by the reconstruction harness.

## Expensive filesystem operations

| Operation | Maintained protection before this change |
| --- | --- |
| Source snapshot | Input integrity only |
| rsync workspace staging | Workspace lock and source comparison |
| Warm target clone | Workspace lock; APFS clone where available |
| Cargo target generation and compilation | Build slot and owned compiler group |
| Link maps and intermediate files | Workspace/output locks |
| Previous-output archive | Output lock; no deletion |
| Strip and pending binary creation | Temporary publication directory |
| Final binary publication | No-replace hard links and hash verification |
| Experiment source copy and trial output | Attempt lock and durable state receipts |

None of these paths had an available-byte floor. APFS logical sizes are not a
safe estimate of recoverable physical storage, so the new guard must use live
filesystem measurements rather than summing file sizes or clone extents.

## Bounded reproduction

Tests reproduce the gap with injected filesystem measurements. An impossible
floor admits the old code to staging or process launch; a sequence of mocked
available-byte values lets a tiny sleeping process cross the floor. The tests
never allocate filler data and never reduce real host free space.

The qualified behavior is opt-in. Default command lines and build identities
remain compatible, no cache is removed, and no unrelated process is signaled.
