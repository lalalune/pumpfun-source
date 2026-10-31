# Bind native comparison receipts to the executed host

Base: `90300f9d2efe3ef014b116172251a41bfb104d78`.

Four native validators hashed `--host` only after its process exited. Replacing
or recompiling that path during a comparison therefore produced a successful
receipt naming bytes that had never supplied the recorded results.

`native_host_receipt.run_host` resolves the path and captures its digest before
execution, checks that digest after execution, and returns it with the process
result. The four writers publish that initial digest. An observed change fails
before report publication, preserving an existing report. This leaves their
comparison corpora and report schemas intact.

## Actual before/after workflow

Use Python 3.12, `requirements.txt`, and `rustc` on PATH:

```sh
python -B scripts/test_native_host_receipt.py
python -B scripts/test_fee_host_validation.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The regression builds the repository's real constant-product, sell-accounting,
fee-selection and quote-fee Rust hosts, then invokes all four full validators
against the retained captured programs. Positive controls check the receipt's
host digest. Each negative control uses a disposable executable wrapper that
forwards all input to the genuine compiled host and replaces only itself after
the calculation; its answers still match the captures.

Running the new regression against the four base validator scripts gives four
failures: all return success and replace the retained report with one that
names the replacement. The fixed scripts pass both methods and preserve the
prior report in all four replacement cases. The initial constant-product
reproduction completed 160 comparisons with zero mismatches while binding the
replacement's digest, demonstrating that result equality does not prove host
identity.

Required checks: 9 captures and 242 tooling tests pass. Existing validation
boundary, optimization, source-binding, constant-product receipt and native fee
suites pass. The source-binding-only fee test still uses its documented stub;
the new regression and native fee suite execute real Rust hosts and captured
programs. The regression is included in the host-fragments CI job.

Limits: endpoint digest checks detect a host that remains changed at the
post-run check. They do not prevent a replace-and-restore race between checks,
prove how a host was compiled, or establish full SBF reconstruction identity.
No capture or historical report is modified by the fix or tests.
