# Native host output isolation

The Global admin and lifecycle captured-program fixtures used shared executable
paths under `/tmp`. Rust also places codegen objects beside the selected output.
Parallel worktrees can therefore share both the executable and intermediate
objects; the fixed fixtures use a separate `TemporaryDirectory` for each setup.
That also makes the fixtures honor the configured temporary directory.

`evidence.json` records a bounded native-compiler experiment: unchanged admin host
and module source in two real worktrees, `rustc --edition=2021 -O`, and a barrier
that starts the two actual compiler processes together. All six shared-output
compilations failed with mixed-object linker errors; all six private-output
compilations and empty-input native executions passed. Compiler results and source
bytes were not mocked or edited. The running-executable overwrite control did
not fail on macOS; no `ETXTBSY` result is claimed.

Reproduce with two checkouts containing the same recorded host and module bytes:

```sh
python3 reconstruction/verification/native_host_isolation/repro.py \
  /path/to/checkout-a /path/to/checkout-b \
  --rustc rustc --output-dir /path/to/new-results --trials 3
```

Use a fresh output directory whose parent exists. The script checks source-byte
identity, invokes real compilers, records normalized diagnostics, requires the
private controls to pass, and removes its build directories. Only `results.json`
is retained. The packaged reproducer repeated the experiment with four shared
compile failures out of six and six successful private controls, reinforcing the
timing limit. The recorded source hashes are required before any compiler runs;
use two distinct resolved roots. Compiler and native executions have timeouts.
Shared-build failures are timing dependent and are recorded rather
than required, so this experiment is not a flaky CI gate.

This proves the admin native-compilation collision on the recorded environment,
not a lifecycle collision, concurrent VM behavior, historical source identity,
SBF equivalence or security acceptance. The unchanged captured-program tests in
both fixtures must still pass separately after the output-lifetime change.
