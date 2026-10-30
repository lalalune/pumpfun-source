# Bounded serial Fees suite execution

`scripts/fees_validate_all.py` launched each of its 18 suites with
`subprocess.run(..., check=True)` and no timeout or process group. A suite that
hangs blocks the aggregate forever, and killing the driver leaves its children
running; the base script contains no `timeout` anywhere. The parallel sibling
`pump_validate_parallel.py` already bounds the same corpus through
`build_process.run_compiler` with `--suite-timeout` (default 1800s,
`start_new_session` plus `killpg`).

`results.json` records the change and the runs. The aggregate now:

- accepts `--suite-timeout` (float, default 1800.0), validated by the same
  `validate_timeout` the parallel driver uses;
- runs each suite through `run_compiler(..., timeout=a.suite_timeout)`;
- stops with `suite <name> exceeded <seconds>s` when the bound expires, before
  any receipt is written, and records `suite_timeout_seconds` in the report.

Observed: `--suite-timeout 0.001` exits 1 with `suite queries exceeded 0.001s`
in 0.1s and writes no report; `--suite-timeout 0` is rejected by
`validate_timeout`. `tests/test_fees_aggregate_output.py` still passes (6 tests)
after its isolated CLI fixture copies `reconstruction/harness/build_process.py`,
the same way it already copies the reporter modules.

`tests/test_fees_suite_timeout.py` covers the expiry and the non-positive values;
all three subcases fail on the base script, which has no such option.

Required checks on the proposed tree: `python3 -E -X utf8 scripts/test_tooling.py`
(217 pass) and `python3 -E -X utf8 scripts/verify_evidence.py` (nine captures
verified). macOS arm64, Python 3.14.3. Suites, fixtures, corpora and captured
ELFs are unchanged; no full 18-suite run is claimed in this packet.

## Review qualification

The shared serial-suite adapter uses the existing process-group runner on
POSIX. Windows keeps inherited child streams and uses `subprocess.run` with a
timeout; it does not gain a process-tree termination guarantee. Both adapter
and process-runner source files are protected inputs and their hashes are
retained in the aggregate report. Captured child diagnostics remain visible.

Real subprocess controls cover a child that spawns a descendant, timeout
termination without a delayed marker, prior-report preservation, invalid finite
timeouts, and protected helper output aliases. Small child receipts in the
publication tests exercise aggregate plumbing only and are not VM evidence.
