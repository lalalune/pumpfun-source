# Bounded serial Pump aggregate

Problem: `scripts/pump_validate_all.py` launched all 44 suites through
`subprocess.run(..., check=True)` with no timeout and no process group. A hung
suite blocks the corpus run forever, and stopping the driver leaves the suite's
descendants alive.

Fix: route each serial suite through the already-merged bounded runner that
`pump_validate_parallel.py` uses (`reconstruction/harness/build_process.py`):
`start_new_session` plus `killpg` on expiry, `--suite-timeout` defaulting to
1800s, and `suite_timeout_seconds` recorded in the receipt.

Reproduction:

```
python -B scripts/pump_validate_all.py --candidate <candidate> --output <dir>/report.json.gz --suite-timeout 0.001
# exit 1, stderr: suite volume exceeded 0.001s, no report written
```

Base revision `8cf3c5f8a7912b36ced352e49ac8538ff864a4c2` rejects the option
(exit 2, `unrecognized arguments`) and never bounds a suite.

Limits: the 0.001s run proves the bound and the kill path, not SBF execution of
the corpus. No full 44-suite run is repeated here; the retained-suite tests
cover publication. macOS arm64, Python 3.14.3.

## Review qualification

The aggregate shares `serial_suite_process.py` with the Fees driver. POSIX uses
process-group termination; Windows retains inherited streams and a
`subprocess.run` timeout, with no Windows process-tree guarantee. Both adapter
and process-runner source paths are protected and hashed in the report, and a
changed helper aborts before a child receipt is consumed. Existing source-input
admission and atomic report/staging behavior are preserved.

The focused subprocess controls execute a real descendant timeout and verify
that neither a report nor a delayed marker is published. Existing retention and
Windows-publication branch tests still cover completed aggregate publication.
Their small child receipts test orchestration only, not contract equivalence.
