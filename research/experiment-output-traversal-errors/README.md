# Refuse incomplete retained-output enumeration

Baseline: `13fe4536be64d8c5c10f8905e9d2236f423ac4f4`.

The experiment runner's retained-artifact collector used `Path.rglob`, which
suppresses a directory `PermissionError`. An actual unprivileged child can
write `output/closed/result`, remove directory read access and exit normally.
The baseline reports a reusable pass without hashing the unreadable result.
Likewise, making a previously empty retained output directory unreadable is
silently skipped and the old pass is reused. Both are demonstrated by real
POSIX permissions and child processes in `before.log`; no launch or traversal
functions are mocked.

The fix enumerates outputs with `os.walk(onerror=raise)`. A post-run read error
uses the existing error-receipt/log-retention path; a retained-tree read error
invalidates reuse and runs a new isolated attempt. Readable outputs still pass
and reuse. Existing link/special-file checks remain unchanged.

Run from the repository root with Python 3.12.3 as an unprivileged POSIX user:

```sh
python3 -B reconstruction/harness/test_experiment_output_walk_errors.py
python3 -m unittest discover -s reconstruction/harness -p 'test_experiment*.py'
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

Applying only the new test to the baseline produces two failures. The fixed
experiment suite runs 55 tests: 53 pass and two existing environment-dependent
controls skip. Required checks authenticate nine captures and pass all 228
tooling tests on native Linux. The tooling suite includes synthetic/offline
runtime controls; this is not a static-only test claim. A sparse-validation
attempt initially lacked a tracked imported configuration fixture; materializing
its exact HEAD bytes resolved four unrelated setup failures before the final
clean run. No dependency installation or capture download was required.

Open PR #3487 records ordinary output directory membership; it does not expose
failed subtree enumeration. Its code patch applies cleanly to this fix, and
both sets of regression tests pass together (three methods). Open #3441 deals
with directory junctions. Existing source-walk tests exercise a different
collector, which already uses an error callback. No matching output traversal
fix appeared in live GitHub searches.

This is reconstruction experiment-harness tooling, permitted by CONTRIBUTING.md.
It changes no program source, build inputs, captures, pins or scores and makes
no bytecode reconstruction claim. Native Windows permission behavior is not
claimed; the new permission controls skip there. Public logs redact the local
checkout prefix and omit verbose passing-test detail; result metadata and file
hashes accompany the packet.
