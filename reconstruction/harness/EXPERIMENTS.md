# Resumable, bounded experiments

`python reconstruction/harness/experiment_runner.py matrix.json --out /tmp/trials --max-trials 20`

A matrix is a JSON array of objects with unique simple `name`, absolute `source` directory, `command` argv array, optional `inputs` file paths and `timeout` seconds (default 300, maximum 86400). Use `{source}`, `{work}` and `{out}` in arguments. Commands run sequentially in an isolated working directory, without a shell. Source is copied; `.git`, `target` and `__pycache__` are omitted. Source symlinks and special files are refused. The output tree must be separate from the source.

The command contract is exit 0 = predicate holds, 1 = valid experiment but predicate does not hold, other status/timeout = infrastructure error. A compiler failure must not be converted into exit 1. `match_oracle.py` implements this contract for one official raw/normalized Pump window, including stack-warning rejection and isolated original-window cache. Example command array:

```
["/absolute/python3.12", "/absolute/repo/reconstruction/harness/match_oracle.py",
 "--source", "{source}", "--work", "{work}", "--out", "{out}",
 "--sdk", "/absolute/platform-tools", "--hybrid", "/absolute/hybrid144",
 "--window", "0x14f4e0", "--kind", "normalized"]
```

For this example `source` is the Pump crate directory, not the repository root. The existing Cargo dependency cache must be provisioned; builds are offline. Set timeouts appropriate for cold builds. No warm template is seeded by this oracle.

Declare every relevant external input in `inputs`: oracle/harness scripts, original ELF, window inventory, toolchain executables/libraries and any configuration consumed by your command. Resume identity includes source file bytes/executable bits, argv, declared input bytes, command executable, timeout, environment hash and runner implementation. Environment values are not recorded. Undeclared files, network responses and changing external services are not authenticated: this is not hermetic execution or a sandbox. The source snapshot and declared inputs are checked again after execution.

Each attempt retains stdout/stderr and all output files, with hashes in latest.json. Resume reuses only pass/fail results whose identity and retained artifacts still match. Errors retry in a new attempt directory; prior attempts remain. A per-trial file lock serializes concurrent users of the same destination. Timeouts kill the process group. Result hashes are integrity checks, not signatures or tamper-proof provenance. A matrix exits 2 on infrastructure error; valid failing predicates remain useful results and do not fail the matrix driver.
