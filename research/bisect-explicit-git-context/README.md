# Bind bisection reads to the explicitly selected Git repository

Baseline: `13fe4536be64d8c5c10f8905e9d2236f423ac4f4`.

`bisect_membership.py --repo PATH` passed `git -C PATH` but inherited the
enclosing process's repository-local Git environment. `GIT_DIR` and
`GIT_WORK_TREE` could therefore select another repository. A real CLI run over
two temporary repositories with identical `good`/`bad` tag names returned a
successful boundary belonging to the other repository. `GIT_COMMON_DIR` and
`GIT_OBJECT_DIRECTORY` contexts also prevented reading the available explicit
repository. The baseline has three failing cases and an unchanged normal
control (`before.log`). No launch, Git command or archive is mocked.

The Git wrapper now asks Git for `rev-parse --local-env-vars`, removes those
names from an environment copy, and uses that copy only for the repository
reads. Revision resolution, first-parent enumeration and archive extraction
therefore use the same explicit repository. Non-local settings are preserved;
the experiment oracle still receives its existing admitted environment.
The process environment and either repository are not modified by this fix.

Run from the repository root with Python 3.12.3 and Git:

```sh
python3 -B reconstruction/harness/test_bisect_git_context.py
python3 -m unittest discover -s reconstruction/harness -p 'test_bisect*.py' -v
python3 -m unittest discover -s reconstruction/harness -p 'test_experiment*.py'
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

Apply only the new test on the baseline for the same before-fix reproduction.
After the fix all six bisection tests pass, including the normal and three
ambient-context CLI cases. The existing experiment suite runs 53 tests: 51
pass and two environment-dependent controls skip. Required results and raw
log hashes are recorded in `results.json`; they are distinct from the focused
CLI controls. Public logs redact the checkout prefix and omit verbose passing
details.

This is permitted offline reconstruction-harness tooling. It changes no
program source, build inputs, captured data, scoring thresholds or bytecode.
The focused test creates only synthetic Git histories and Python predicates.
The required tooling suite includes existing offline runtime controls; no
live network or chain operation is used. No program build, window gain,
hosted CI or platform-wide isolation claim is made. Git's own installed local
environment-name list is used rather than guessing a subset of routing keys.
Live GitHub searches for GIT_DIR/Git environment/bisection routing found no
matching open contribution; open #3443 optimizes midpoint selection instead.
