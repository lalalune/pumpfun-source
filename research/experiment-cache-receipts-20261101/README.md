# Consistent receipts before experiment reuse

At base `60a42309a4908577f0a386513eeaee6cd6f84f42`, the documented experiment
contract maps exit 0 to `pass` and exit 1 to `fail`. Resume checked the cache
key and pass/fail label, plus retained artifact and live-input checks, but not
whether the stored result metadata described that key or completed command.
An owned result with `returncode: 1` relabeled `pass` was returned as a reused
success. Saved schema, error reason and input provenance could likewise
contradict the accepted result.

The runner now checks the schema, exact integer exit/status pair, absent error
reason, current input object and its existing canonical key before reuse.
The second key check distinguishes JSON booleans from integers (Python dict
equality alone considers `false` and `0` equal). An inconsistent receipt takes
the existing new-attempt path. Valid pass and fail records remain reusable;
old attempt contents and source bytes remain intact. The changed runner
fingerprint naturally invalidates earlier cache keys.

## Reproduce

From the repository root with Python 3.12:

```sh
python research/experiment-cache-receipts-20261101/probe.py --repo . --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 --expect base --output /tmp/receipt-before.json
python research/experiment-cache-receipts-20261101/probe.py --repo . --expect fixed --output /tmp/receipt-after.json
python -m unittest discover -s reconstruction/harness -p 'test_experiment_receipt_integrity.py'
```

The probe runs four actual matrix CLIs per revision: create 13 results, reuse
them, edit only owned `latest.json` metadata and resume, then resume again.
Every child is a real Python command that copies a generic source file and
returns an explicit 0 or 1. The edited records come from actual completed
commands; no runner or subprocess result is mocked. Eleven inconsistent
records were all reused before and all rerun after. Two untouched pass/fail
controls remain reused. All old attempts, source bytes and output hashes are
preserved, and every resulting receipt is reused on the fourth invocation.
Exact portable summaries are in `results.json` (owned absolute paths and
content-derived keys are checked during execution, not published).

The existing receipt-integrity CI module invokes this public probe. Validation
on macOS arm64 / CPython 3.12.13: experiment family 72 passed, one optional SDK
probe skipped; receipt-integrity five passed after the final 13-case expansion;
bisection 12 passed; minimizer 18 passed, one platform case skipped; mandatory
`scripts/test_tooling.py` 255 passed; nine saved captures passed. The production
change was unchanged between these checks. The mandatory tooling suite includes
its existing VM fixtures; this new proof itself executes only generic Python
commands, with no compiler, model, program image or VM.

This extends the retained-input contract from #2730 and bounded launch behavior
from #2865. It is consistency admission, not signed or tamper-proof provenance;
coordinated forged metadata is outside the claim. Parsing malformed JSON and
other unsupported receipt shapes is unchanged. No historical evidence is edited.
