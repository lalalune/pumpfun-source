# Revalidation invocation errors

The maintained `scripts/revalidate_all.py` distinguishes an observed missing-
argument usage error from other verifier failures. It requires exit code 2,
an argparse-style `usage:` line, and a matching exact missing-argument diagnostic
on stderr. Plain mentions of the diagnostic, or matching text on stdout, remain
failures.

The category is `invocation_error`. The process was invoked and may have read
inputs, written files, or performed checks before parsing arguments. This result
therefore does **not** mean that no verifier code executed. The packet remains
unverified. A failed manifest check takes precedence, and other nonzero exits
remain failures.

The aggregate summary includes `invocation_error` and
`invocation_error_packets`; `invocation-errors.json` lists the affected packets.
`passed.json`, `failed.json`, and `skipped.json` remain disjoint. Existing atomic
publication and no-replacement behavior is preserved. The old positional
`write_reports` call shape remains supported.

## Evidence and limits

`results.json` preserves the submitter's historical before/after observation at
`5889e795eba64e85e613b4409921323bfecec414`: 112 passes, 49 failures and 48 skips,
with 48 of those failures reporting missing arguments. Its `not_invoked` labels
belong to the original implementation and are not the current classification or
proof that no code executed. Those whole-repository counts have not been
independently regenerated for current main.

The maintained regression runs real child processes for required options,
required positional arguments, successful verification, evidence disagreement,
and misleading diagnostics. A verifier that writes a marker before calling
`parse_args()` demonstrates why the classification makes no non-execution
claim. A complete temporary audit checks manifest-failure precedence, the report
partition, publication, and the generated receipt verifier.

```sh
python -B tests/test_revalidate_all_invocation.py -v
python -B scripts/test_tooling.py
```

The two pinned consumers are updated together with the reviewed revalidator.
No missing image is supplied or inferred, and no historical packet is changed.
This improves failure reporting only; it does not establish packet correctness,
source reconstruction, or binary identity.
